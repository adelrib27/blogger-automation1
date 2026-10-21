import json
from pathlib import Path

import automation_core_persistent_v2 as core
import evidence_engine_persistent_v13 as persisted_evidence

LAB_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = LAB_ROOT / "data" / "architecture_lab" / "architecture_report.json"


def main():
    core.evidence = persisted_evidence
    core.main()
    report = core.base.load_json(REPORT_PATH, {}) or {}
    report["version"] = "VIDA_PET_AUTOMATION_CORE_PERSISTENT_V3_EVIDENCE_REUSE"
    guards = report.setdefault("guards", {})
    guards.update({
        "persisted_evidence_ttl_guard": True,
        "evidence_reuse_does_not_extend_ttl": True,
        "firecrawl_fallback_preserved": True,
        "evidence_reuse_fail_closed": True,
    })
    core.base.save_json(REPORT_PATH, report)
    print(json.dumps({
        "status": "PERSISTENT_CORE_V3_EVIDENCE_REUSE_COMPLETE",
        "ready_count": report.get("ready_count"),
        "wordpress_written": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
