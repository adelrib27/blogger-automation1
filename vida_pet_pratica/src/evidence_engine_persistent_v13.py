import copy
import json
import time
from datetime import datetime
from pathlib import Path

import evidence_engine as live

LAB_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = LAB_ROOT / "config" / "evidence_reuse_policy.json"
CACHE_PATH = LAB_ROOT / "state" / "evidence_cache.json"
REPORT_PATH = LAB_ROOT / "data" / "architecture_lab" / "evidence_reuse_report.json"


def _load(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def _parse_time(value):
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


def _events():
    data = _load(REPORT_PATH, [])
    return data if isinstance(data, list) else []


def _audit(item_id, action, reasons=None, checked_at=None):
    events = _events()
    events.append({
        "itemId": str(item_id or ""),
        "action": action,
        "reasons": list(reasons or []),
        "evidence_checked_at": checked_at,
    })
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _validated_persisted_package(item, policy):
    item_id = str(item.get("itemId") or "").strip()
    product_name = str(item.get("productName") or "").strip()
    cache = _load(CACHE_PATH, {})
    row = cache.get(item_id) if isinstance(cache, dict) else None
    reasons = []
    if not isinstance(row, dict):
        return None, ["persisted_evidence_missing"]
    if policy.get("require_verified_product_status", True) and row.get("status") != "VERIFIED":
        reasons.append("persisted_product_not_verified")
    cached_product = row.get("product") or {}
    if str(cached_product.get("itemId") or "") != item_id:
        reasons.append("persisted_item_identity_mismatch")
    if policy.get("require_same_normalized_product_name", True):
        if live.normalize(cached_product.get("productName") or "") != live.normalize(product_name):
            reasons.append("persisted_product_name_changed")
    checked_at = row.get("evidence_checked_at")
    checked_ts = _parse_time(checked_at)
    ttl_days = int(policy.get("ttl_days", 7))
    age = time.time() - checked_ts if checked_ts else None
    if not checked_ts:
        reasons.append("persisted_evidence_timestamp_missing")
    elif age < 0:
        reasons.append("persisted_evidence_timestamp_in_future")
    elif age > ttl_days * 86400:
        reasons.append("persisted_evidence_stale")
    sources = row.get("sources") or []
    if not isinstance(sources, list):
        sources = []
    authorized = [s for s in sources if s.get("allowed_in_article") and s.get("support_text") and s.get("evidence_id")]
    exact = [s for s in authorized if s.get("identity_level") == "EXACT_PRODUCT"]
    external = [s for s in authorized if s.get("source_domain") != "open-api.affiliate.shopee.com.br"]
    if len(external) < int(policy.get("min_external_authorized_sources", 1)):
        reasons.append("persisted_external_authorized_insufficient")
    if len(exact) < int(policy.get("require_exact_evidence_count", 2)):
        reasons.append("persisted_exact_authorized_insufficient")
    if reasons:
        return None, reasons
    package = {
        "status": "VERIFIED",
        "version": "EVIDENCE_ENGINE_V1_3_PERSISTED_REUSE",
        "verified_at": checked_at,
        "product": {
            "itemId": item_id,
            "productName": product_name,
            "shopName": item.get("shopName"),
            "productLink": item.get("productLink"),
            "offerLink": item.get("offerLink"),
            "intentMatchedKeywords": item.get("intentMatchedKeywords") or item.get("keywords") or [],
            "categories": item.get("categories") or [],
            "modelTokens": live.model_tokens(product_name),
        },
        "search_runs": [],
        "rules": {
            "similar_product_specs_authorized": False,
            "exact_product_authorized": True,
            "persisted_evidence_reuse": True,
            "ttl_days": ttl_days,
            "refresh_does_not_extend_ttl": True,
            "firecrawl_fallback_preserved": True,
        },
        "authorized_evidence_ids": [s.get("evidence_id") for s in authorized],
        "external_authorized_evidence_ids": [s.get("evidence_id") for s in external],
        "conflicts": [],
        "reasons": [],
        "sources": copy.deepcopy(sources),
    }
    return package, []


def build_evidence_package(item, max_results=8, min_external_authorized_sources=1):
    policy = _load(POLICY_PATH, {})
    item_id = str(item.get("itemId") or "").strip()
    if not isinstance(policy, dict) or policy.get("enabled") is not True or policy.get("lab_only") is not True:
        raise RuntimeError("EVIDENCE_REUSE_POLICY_INVALID_OR_NOT_LAB_ONLY")
    if policy.get("fallback") != "FIRECRAWL" or policy.get("fail_closed_when_fallback_unavailable") is not True:
        raise RuntimeError("EVIDENCE_REUSE_FALLBACK_NOT_FAIL_CLOSED")
    package, reasons = _validated_persisted_package(item, policy)
    if package is not None:
        _audit(item_id, "PERSISTED_REUSE", checked_at=package.get("verified_at"))
        return package
    _audit(item_id, "FIRECRAWL_FALLBACK_REQUIRED", reasons=reasons)
    try:
        package = live.build_evidence_package(
            item,
            max_results=max_results,
            min_external_authorized_sources=max(
                int(policy.get("min_external_authorized_sources", 1)),
                int(min_external_authorized_sources),
            ),
        )
    except Exception as exc:
        _audit(item_id, "FALLBACK_FAILED_CLOSED", reasons=reasons + [str(exc)[:400]])
        raise RuntimeError("EVIDENCE_FALLBACK_REQUIRED_BUT_UNAVAILABLE: " + ";".join(reasons)) from exc
    _audit(item_id, "LIVE_FIRECRAWL", reasons=reasons, checked_at=package.get("verified_at"))
    return package
