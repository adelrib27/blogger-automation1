import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import d1_persistence as base

LAB_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = LAB_ROOT / "config" / "automation_policy.json"
OUT_DIR = LAB_ROOT / "data" / "architecture_lab"
EVERGREEN_VERSION = "SAFE_V11_EVERGREEN_EDITORIAL_INCREMENTAL_REPAIR"


def iso(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def count_ready():
    rows = base.rows("SELECT COUNT(*) AS c FROM ready_queue WHERE status='READY'")
    return int((rows or [{"c": 0}])[0].get("c") or 0)


def persist_v2():
    ready_before = count_ready()
    base.persist()

    policy = base.load_json(POLICY_PATH, {}) or {}
    cooldown_days = int((policy.get("rotation") or {}).get("product_cooldown_days", 30))
    now = datetime.now(timezone.utc)
    now_s = iso(now)
    cooldown_s = iso(now + timedelta(days=cooldown_days))
    evergreen = os.getenv("VIDAPET_FORCE_EVERGREEN", "").strip() == "1"
    updated = []

    post_dir = OUT_DIR / "posts"
    for path in sorted(post_dir.glob("*.json")) if post_dir.exists() else []:
        post = base.load_json(path, {}) or {}
        if post.get("status") != "VERIFIED_READY":
            continue
        item_id = str(post.get("itemId") or "")
        angle = str(post.get("angle") or "")
        if not item_id or not angle:
            continue
        gate = post.get("gate") or {}
        if evergreen:
            version = EVERGREEN_VERSION
        else:
            version = str(gate.get("editorial_sanitizer") or "SAFE_V5_CATEGORY_AWARE")
        a_fp = base.angle_fp(angle)
        base.execute(
            "UPDATE editorial_articles SET gate_version=?,builder_version=?,last_used_at=? WHERE item_id=? AND angle_fingerprint=?",
            [version, version, now_s, item_id, a_fp],
        )
        base.execute(
            "UPDATE editorial_products SET last_used_at=?,cooldown_until=?,status='COOLDOWN' WHERE item_id=?",
            [now_s, cooldown_s, item_id],
        )
        updated.append(item_id)

    ready_after = count_ready()
    architecture = base.load_json(OUT_DIR / "architecture_report.json", {}) or {}
    run_id = f"github-{os.getenv('GITHUB_RUN_ID', 'local')}-{os.getenv('GITHUB_RUN_ATTEMPT', '1')}"
    mode = str(architecture.get("mode") or ("EVERGREEN_ROTATION_FORCED" if evergreen else "NEW_PRODUCT_DISCOVERY"))
    notes = {
        "builder": EVERGREEN_VERSION if evergreen else "SAFE_V5_CATEGORY_AWARE",
        "wordpress_written": False,
        "cooldown_days": cooldown_days,
        "items": updated,
    }
    base.execute(
        """
        INSERT INTO automation_runs(run_id,started_at,completed_at,status,mode,ready_before,ready_after,candidate_attempts,candidate_rejections,notes)
        VALUES(?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(run_id) DO UPDATE SET completed_at=excluded.completed_at,status=excluded.status,mode=excluded.mode,
        ready_before=excluded.ready_before,ready_after=excluded.ready_after,candidate_attempts=excluded.candidate_attempts,
        candidate_rejections=excluded.candidate_rejections,notes=excluded.notes
        """,
        [run_id, now_s, now_s, "COMPLETE", mode, ready_before, ready_after,
         int(architecture.get("candidate_attempts") or 0), int(architecture.get("candidate_rejections") or 0),
         json.dumps(notes, ensure_ascii=False, separators=(",", ":"))],
    )
    print(json.dumps({
        "status": "PERSISTENCE_V2_COMPLETE",
        "items": updated,
        "cooldown_until": cooldown_s,
        "builder_version": notes["builder"],
        "ready_before": ready_before,
        "ready_after": ready_after,
        "run_id": run_id,
        "wordpress_written": False,
    }, ensure_ascii=False))


def main():
    if len(sys.argv) != 2:
        raise SystemExit("uso: d1_persistence_v2.py hydrate|persist|consume-ready-lab|verify")
    command = sys.argv[1]
    if command == "persist":
        persist_v2()
    elif command == "hydrate":
        base.hydrate()
    elif command == "consume-ready-lab":
        base.consume_ready_lab()
    elif command == "verify":
        base.verify()
    else:
        raise SystemExit("comando inválido")


if __name__ == "__main__":
    main()
