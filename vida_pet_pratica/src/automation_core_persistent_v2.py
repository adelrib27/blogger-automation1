import json
import os
import time
from datetime import datetime
from pathlib import Path

import automation_core_v1 as base
import evidence_engine as evidence

LAB_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = LAB_ROOT / "config" / "automation_policy.json"
STATE_DIR = LAB_ROOT / "state"
OUT_DIR = LAB_ROOT / "data" / "architecture_lab"


def parse_time(value):
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def cooldown_active(row):
    until = parse_time(row.get("cooldownUntil"))
    return bool(until and until > time.time())


def known_products(history):
    out = {}
    for row in history:
        item_id = str(row.get("itemId") or "")
        if not item_id or str(row.get("evidenceStatus") or "") != "VERIFIED":
            continue
        current = out.get(item_id)
        if current is None or parse_time(row.get("lastUsedAt")) >= parse_time(current.get("lastUsedAt")):
            out[item_id] = row
    return list(out.values())


def candidate_from_item(item, history, max_similarity, max_results, status, angle_status_prefix=""):
    item_id = str(item.get("itemId") or "")
    allowed, blocked = base.source_guard(item)
    if not allowed:
        return None, {"itemId": item_id, "stage": "SOURCE_GUARD", "reasons": blocked}
    try:
        package = evidence.build_evidence_package(item, max_results=max_results)
    except Exception as exc:
        return None, {"itemId": item_id, "stage": "EVIDENCE_ENGINE", "reasons": [str(exc)]}
    base.save_json(OUT_DIR / "evidence" / f"{item_id}.json", package)
    if package.get("status") != "VERIFIED":
        return None, {"itemId": item_id, "stage": "EVIDENCE_REJECTED", "reasons": package.get("reasons") or []}
    angle, angle_status = base.choose_angle(item, history, max_similarity)
    if not angle:
        return None, {"itemId": item_id, "stage": angle_status, "reasons": ["no_unique_angle_available"]}
    return {
        "status": status,
        "itemId": item_id,
        "productName": item.get("productName"),
        "category": (item.get("categories") or [None])[0],
        "keyword": (item.get("intentMatchedKeywords") or item.get("keywords") or [None])[0],
        "angle": angle,
        "angle_status": f"{angle_status_prefix}{angle_status}",
        "fingerprint": base.fingerprint(item_id, angle),
        "evidence_file": f"evidence/{item_id}.json",
        "authorized_evidence_ids": package.get("authorized_evidence_ids") or [],
    }, None


def main():
    policy = base.load_json(POLICY_PATH, {})
    min_ready = int(policy.get("min_ready", 3))
    attempt_limit = int(policy.get("candidate_attempt_limit", 20))
    max_similarity = float((policy.get("anti_duplicate") or {}).get("max_similarity", 0.72))
    max_results = int((policy.get("evidence") or {}).get("max_search_results", 8))
    new_products_first = bool((policy.get("rotation") or {}).get("new_products_first", True))
    force_evergreen = os.getenv("VIDAPET_FORCE_EVERGREEN", "").strip() == "1"
    target = max(min_ready, int(os.getenv("VIDAPET_CANDIDATE_BUFFER_TARGET", "5")))

    if (policy.get("wordpress") or {}).get("writes_enabled") is not False:
        raise SystemExit("SAFE bloqueado: WordPress precisa continuar desativado")

    history = base.load_json(STATE_DIR / "article_history.json", [])
    if not isinstance(history, list):
        raise SystemExit("article_history.json inválido")
    known = known_products(history)
    known_ids = {str(x.get("itemId") or "") for x in known}

    base.shopee.run_regression_checks = base.pet_regression_checks
    ranking = base.shopee.scan_v23()
    ready, rejected = [], []
    attempts = 0

    if not force_evergreen:
        for item in ranking:
            if attempts >= attempt_limit or len(ready) >= target:
                break
            attempts += 1
            item_id = str(item.get("itemId") or "")
            if not item_id:
                continue
            if new_products_first and item_id in known_ids:
                rejected.append({"itemId": item_id, "stage": "KNOWN_PRODUCT_DEFERRED", "reasons": ["new_products_first"]})
                continue
            candidate, rejection = candidate_from_item(
                item, history, max_similarity, max_results,
                status="VERIFIED_READY_CANDIDATE",
                angle_status_prefix="NEW_PRODUCT_",
            )
            if rejection:
                rejected.append(rejection)
                continue
            ready.append(candidate)

    mode = "NEW_PRODUCT_DISCOVERY"
    if force_evergreen or len(ready) < min_ready:
        mode = "EVERGREEN_ROTATION_FORCED" if force_evergreen else "EVERGREEN_ROTATION_FALLBACK"
        for row in known:
            if len(ready) >= target:
                break
            item_id = str(row.get("itemId") or "")
            if not item_id or any(str(x.get("itemId") or "") == item_id for x in ready):
                continue
            if cooldown_active(row):
                rejected.append({"itemId": item_id, "stage": "PRODUCT_COOLDOWN", "reasons": [str(row.get("cooldownUntil"))]})
                continue
            source = row.get("sourcePayload") or {}
            if not source or str(source.get("itemId") or "") != item_id:
                rejected.append({"itemId": item_id, "stage": "PERSISTENT_SOURCE_MISSING", "reasons": ["source_payload_unavailable"]})
                continue
            attempts += 1
            candidate, rejection = candidate_from_item(
                source, history, max_similarity, max_results,
                status="EVERGREEN_READY_CANDIDATE",
                angle_status_prefix="EVERGREEN_",
            )
            if rejection:
                rejected.append(rejection)
                continue
            ready.append(candidate)

    health = "HEALTHY" if len(ready) >= min_ready else ("ATTENTION" if ready else "EMERGENCY")
    report = {
        "status": "PERSISTENT_ARCHITECTURE_LAB_COMPLETE",
        "version": "VIDA_PET_AUTOMATION_CORE_PERSISTENT_V2",
        "wordpress_written": False,
        "publishing_enabled": False,
        "persistent_history_rows": len(history),
        "known_products": len(known_ids),
        "min_ready": min_ready,
        "candidate_buffer_target": target,
        "ready_count": len(ready),
        "buffer_health": health,
        "mode": mode,
        "force_evergreen": force_evergreen,
        "candidate_attempts": attempts,
        "candidate_rejections": len(rejected),
        "firecrawl_auth_mode": "API_KEY" if os.getenv("FIRECRAWL_API_KEY", "").strip() else "MISSING",
        "ready_buffer": ready,
        "rejections": rejected,
        "guards": {
            "candidate_failover": True,
            "candidate_reserve": True,
            "evidence_fail_closed": True,
            "new_products_first_strict": True,
            "persistent_history": True,
            "evergreen_rechecks_evidence": True,
            "anti_duplicate_angle_guard": True,
            "wordpress_write_blocked": True,
        },
    }
    base.save_json(OUT_DIR / "ready_buffer.json", ready)
    base.save_json(OUT_DIR / "candidate_rejections.json", rejected)
    base.save_json(OUT_DIR / "architecture_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if len(ready) < min_ready:
        raise SystemExit(f"Buffer insuficiente: {len(ready)}/{min_ready}")


if __name__ == "__main__":
    main()
