"""C136: verificação operacional dos crons editoriais LEGADOS após LIVE HOLD.

Somente GET GitHub Actions + leitura de arquivos da main. Não aciona workflows,
não modifica posts/cotas/credenciais, não substitui autorização LIVE.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

REPO = "adelrib27/blogger-automation1"
HOLD_MERGED_AT = "2026-11-23T20:57:59Z"
PATHS = {
    "casa": {
        "workflow": "casa_editorial_generate_schedule.yml",
        "expected_jobs": ("v31_casa_discovery", "autonomo"),
        "live_flag": 'CASA_LIVE_PUBLISH_ENABLED: "false"',
        "status_flag": "CASA_WORDPRESS_STATUS: draft",
    },
    "oficina": {
        "workflow": "oficina_editorial_autonomous.yml",
        "expected_jobs": ("v31_oficina_discovery", "publicar-um-slot"),
        "live_flag": 'OFICINA_LIVE_PUBLISH_ENABLED: "false"',
        "status_flag": 'OFICINA_WORDPRESS_STATUS: "draft"',
    },
}
ROOT = Path(__file__).resolve().parent.parent
MAX_RUNS = 60
MAX_JOBS = 100


class LegacyHoldAuditError(ValueError):
    pass


def _when(v: str) -> datetime:
    if not isinstance(v, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", v):
        raise LegacyHoldAuditError("invalid_action_date")
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


def assert_static_live_hold(root: Path = ROOT) -> None:
    if not isinstance(root, Path):
        raise LegacyHoldAuditError("invalid_repository_root")
    policy = json.loads((root / "affiliate_hub_v31" /
                         "autonomous_live_policy.json").read_text(encoding="utf-8"))
    if policy.get("activation") != "pending_policy_approval":
        raise LegacyHoldAuditError("live_policy_not_pending")
    for c in PATHS.values():
        body = (root / ".github/workflows" / c["workflow"]).read_text(encoding="utf-8")
        for name in c["expected_jobs"]:
            # Job starts with hard false guard, no later expression can override.
            block = re.search(
                rf"(?ms)^  {re.escape(name)}:\n(?P<body>.*?)(?=^  [A-Za-z][\w-]*:|\Z)",
                body)
            if block is None or not re.search(
                    r"(?m)^    if: >-\n      false &&\s*$", block.group("body")):
                raise LegacyHoldAuditError("legacy_schedule_guard_missing")
        if c["live_flag"] not in body or c["status_flag"] not in body:
            raise LegacyHoldAuditError("legacy_schedule_live_flags_unsafe")


def evaluate_hold_run(*, source: str, run: dict | None,
                      jobs: list[dict] | None) -> dict:
    if source not in PATHS:
        raise LegacyHoldAuditError("unknown_workflow")
    if run is None:
        return {"source": source, "status": "PENDING_OBSERVATION",
                "run_id": None, "jobs_checked": 0}
    if not isinstance(run, dict) or not isinstance(run.get("id"), int):
        raise LegacyHoldAuditError("run_untrusted")
    if run.get("event") != "schedule" or _when(run.get("created_at")) <= _when(HOLD_MERGED_AT):
        raise LegacyHoldAuditError("schedule_post_hold_identity_invalid")
    if run.get("status") != "completed":
        return {"source": source, "status": "PENDING_RUN_COMPLETION",
                "run_id": run["id"], "jobs_checked": 0}
    if not isinstance(jobs, list) or len(jobs) > MAX_JOBS or any(
            not isinstance(x, dict) or not isinstance(x.get("name"), str)
            for x in jobs):
        raise LegacyHoldAuditError("jobs_untrusted")
    names = [x["name"] for x in jobs]
    if len(names) != len(set(names)):
        raise LegacyHoldAuditError("duplicate_jobs_untrusted")
    required = PATHS[source]["expected_jobs"]
    by_name = {x["name"]: x.get("conclusion") for x in jobs}
    # Qualquer job executado inesperadamente num workflow legado é violação.
    if any(result == "success" for result in by_name.values()):
        status = "SECURITY_EXCEPTION_JOB_RAN"
    elif all(by_name.get(name) == "skipped" for name in required) and (
            run.get("conclusion") in {"success", "skipped"}):
        status = "SKIP_VERIFIED"
    else:
        status = "UNVERIFIED_JOB_STATE"
    return {"source": source, "status": status,
            "run_id": run["id"], "jobs_checked": len(jobs)}


def recent_post_hold_run(runs: list[dict]) -> dict | None:
    if not isinstance(runs, list) or len(runs) > MAX_RUNS:
        raise LegacyHoldAuditError("runs_untrusted")
    valid = []
    for r in runs:
        if not isinstance(r, dict):
            raise LegacyHoldAuditError("run_untrusted")
        if r.get("event") != "schedule":
            continue
        if _when(r.get("created_at")) > _when(HOLD_MERGED_AT):
            valid.append(r)
    valid.sort(key=lambda r: _when(r["created_at"]), reverse=True)
    return valid[0] if valid else None


def _get_json(path: str, token: str) -> dict:
    if not isinstance(path, str) or not path.startswith(
            "/repos/adelrib27/blogger-automation1/actions/"):
        raise LegacyHoldAuditError("github_path_invalid")
    if not isinstance(token, str) or not token:
        raise LegacyHoldAuditError("github_read_token_missing")
    request = Request("https://api.github.com" + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "V31-C136-ReadOnly-Audit"})
    try:
        with urlopen(request, timeout=20) as response:
            data = response.read(512_001)
    except (HTTPError, URLError, TimeoutError, OSError):
        raise LegacyHoldAuditError("github_read_failed_closed") from None
    if len(data) > 512_000:
        raise LegacyHoldAuditError("github_response_too_large")
    try:
        result = json.loads(data)
    except (ValueError, UnicodeDecodeError):
        raise LegacyHoldAuditError("github_json_invalid") from None
    if not isinstance(result, dict):
        raise LegacyHoldAuditError("github_response_invalid")
    return result


def audit(*, token: str) -> dict:
    assert_static_live_hold()
    reports = []
    for key, cfg in PATHS.items():
        # A query NÃO chama rerun nem dispatch e verifica o evento schedule.
        response = _get_json(
            "/repos/" + REPO + "/actions/workflows/"
            + quote(cfg["workflow"], safe="") + "/runs?event=schedule&per_page=60",
            token)
        runs = response.get("workflow_runs")
        if not isinstance(runs, list):
            raise LegacyHoldAuditError("runs_schema_invalid")
        latest = recent_post_hold_run(runs)
        jobs = None
        if latest is not None and latest.get("status") == "completed":
            response = _get_json(
                "/repos/" + REPO + f"/actions/runs/{latest['id']}/jobs?per_page=100",
                token)
            jobs = response.get("jobs")
        reports.append(evaluate_hold_run(source=key, run=latest, jobs=jobs))
    return {
        "mode": "READ_ONLY_SCHEDULE_VERIFICATION",
        "base_merge": HOLD_MERGED_AT,
        "workflows": reports,
        "all_holds_verified": all(r["status"] == "SKIP_VERIFIED" for r in reports),
        "cms_writes": 0,
        "d1_writes": 0,
        "workflow_dispatches": 0,
        "automatic_live_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="C136 observação SAFE crons legados")
    parser.add_argument("--offline-static", action="store_true")
    args = parser.parse_args()
    try:
        if args.offline_static:
            assert_static_live_hold()
            result = {"mode": "STATIC_SAFE_HOLD_VERIFIED", "all_holds_verified": False}
        else:
            result = audit(token=os.getenv("GITHUB_TOKEN", ""))
    except LegacyHoldAuditError as exc:
        # Código de erro controlado (sem URL, headers, tokens ou resposta HTTP).
        print("C136_LEGACY_HOLD_FAILED_CLOSED:" + str(exc))
        return 1
    except Exception:
        print("C136_LEGACY_HOLD_FAILED_CLOSED:internal_error")
        return 1
    print("C136_LEGACY_HOLD=" + json.dumps(result, sort_keys=True))
    if any(x.get("status") == "SECURITY_EXCEPTION_JOB_RAN"
           for x in result.get("workflows", [])):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
