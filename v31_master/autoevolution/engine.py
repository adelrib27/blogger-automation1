#!/usr/bin/env python3
"""V31 Autoevolucao SAFE v1: aprender com evidencias, nunca autoeditar producao.

Faz inferencia DETERMINISTICA sobre resultados CI da PROPRIA conta/repo.
Nao treina modelo ChatGPT/LLM, nao baixa logs, nao executa codigo gerado,
nao acessa Blogger/Shopee, e so grava arquivo de relatorio na branch LAB.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_REPO = "adelrib27/blogger-automation1"
ALLOWED_BRANCH = "lab/v31-autoevolucao-safe-20261112"
ALLOWED_OUTPUT_PREFIX = "v31_master/autoevolution/reports/"
ENGINE_VERSION = "v31-autoevolution-safe/v1"
MAX_RUNS = 1000
MAX_PAGES = 10
MAX_RESPONSE = 2_000_000
KIND = ("SHOPEE_PIPELINE", "VISUAL_QA", "BLOGGER_PIPELINE",
        "CI_GENERAL", "UNKNOWN")
SUGGESTIONS = {
    "SHOPEE_PIPELINE": {
        "proposal": "SAFE_DIAGNOSE_GRAPHQL_AND_CATALOG",
        "required_gates": ["GRAPHQL_ERRORS_NEVER_OOS", "STOCK_UNKNOWN", "NO_BLOGGER_PUT"],
    },
    "VISUAL_QA": {
        "proposal": "SAFE_RECHECK_VISUAL_CONTRACT",
        "required_gates": ["PRESERVE_THEME", "RECHECK_MOBILE", "PUBLIC_READBACK"],
    },
    "BLOGGER_PIPELINE": {
        "proposal": "SAFE_RECHECK_TARGET_AND_IDEMPOTENCY",
        "required_gates": ["BLOG_ID_PAGE_ID_ALLOWLIST", "NO_UNREVIEWED_PUT"],
    },
    "CI_GENERAL": {
        "proposal": "SAFE_REVIEW_FAILURE_WITHOUT_INFERRED_CAUSE",
        "required_gates": ["MANUAL_DIAGNOSIS"],
    },
}
SECRET_PATTERN = re.compile(r"(?i)(bearer |token=|api_key=|password=|secret=|ghp_[a-z0-9]+)")
SLUG = re.compile(r"^[A-Za-z0-9_.\-/]{1,128}$")


class SafetyStop(RuntimeError):
    pass


def output_path_guard(path: str, repo_root: Path) -> Path:
    """Protege contra path traversal e qualquer escrita fora de reports."""
    root = repo_root.resolve()
    dest = (root / path).resolve()
    allowed = (root / ALLOWED_OUTPUT_PREFIX).resolve()
    if not allowed.is_relative_to(root) or not dest.is_relative_to(allowed) or dest.suffix != ".json":
        raise SafetyStop("OUTPUT_PATH_NOT_ALLOWLISTED")
    if dest.name.startswith(".") or not re.fullmatch(r"[0-9]{5,20}\.json", dest.name):
        raise SafetyStop("OUTPUT_FILENAME_NOT_RUN_ID")
    return dest


def changed_paths_guard(changed: list[str]) -> None:
    if not changed or len(changed) > 3:
        raise SafetyStop("TOO_MANY_CHANGED_FILES")
    for path in changed:
        if not isinstance(path, str) or not path.startswith(ALLOWED_OUTPUT_PREFIX):
            raise SafetyStop("PROTECTED_PATH_CHANGED")
        if not re.fullmatch(r"v31_master/autoevolution/reports/[0-9]{5,20}\.json", path):
            raise SafetyStop("UNTRUSTED_OUTPUT_PATH")


def classify_workflow(name: str) -> str:
    """Nome indica CAMADA possivelmente afetada; nao infere causa raiz."""
    lowered = name.lower()
    if any(w in lowered for w in ("shopee", "loja", "store", "affiliate")):
        return "SHOPEE_PIPELINE"
    if any(w in lowered for w in ("visual", "theme", "tema", "imagem", "mobile")):
        return "VISUAL_QA"
    if any(w in lowered for w in ("blogger", "editorial", "publica", "contato")):
        return "BLOGGER_PIPELINE"
    return "CI_GENERAL"


def valid_run(r: object, repo: str) -> dict | None:
    if not isinstance(r, dict):
        return None
    run_id, name = r.get("id"), r.get("name")
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        return None
    if not isinstance(name, str) or not (1 <= len(name) <= 160):
        return None
    if SECRET_PATTERN.search(name):
        return None
    repository = (r.get("repository") or {})
    if not isinstance(repository, dict) or repository.get("full_name") != repo:
        return None
    branch = r.get("head_branch")
    if not isinstance(branch, str) or not SLUG.fullmatch(branch):
        return None
    event = r.get("event")
    if event not in ("schedule", "push", "workflow_dispatch", "pull_request",
                     "workflow_run", "repository_dispatch"):
        event = "other"
    status = r.get("status")
    conclusion = r.get("conclusion")
    if status not in ("completed", "queued", "in_progress"):
        return None
    if conclusion not in (None, "success", "failure", "cancelled", "timed_out",
                          "action_required", "neutral", "skipped", "stale"):
        return None
    if status != "completed":
        conclusion = None
    attempt = r.get("run_attempt", 1)
    if type(attempt) is not int or attempt < 1:
        return None
    if SECRET_PATTERN.search(branch):
        return None
    return {
        "run_attempt": attempt,
        "run_id": run_id,
        "workflow": name,
        "branch": branch,
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "category": classify_workflow(name),
        "run_url": "https://github.com/" + repo + "/actions/runs/" + str(run_id),
    }


def collect_report(raw_runs: list, *, repo: str, branch: str, generated_run_id: int) -> dict:
    if repo != ALLOWED_REPO or branch != ALLOWED_BRANCH:
        raise SafetyStop("CROSS_REPO_OR_BRANCH_DENIED")
    if not isinstance(raw_runs, list) or len(raw_runs) > MAX_RUNS:
        raise SafetyStop("INVALID_OR_TOO_MANY_RUNS")
    unique = {}
    for raw in raw_runs:
        entry = valid_run(raw, repo)
        if entry is None or entry["run_id"] == generated_run_id:
            continue
        if any(word in entry["workflow"].casefold() for word in ("autoevolucao", "autoevolution", "jarvis")):
            continue
        key = (entry["run_id"], entry["run_attempt"])
        if key in unique and unique[key] != entry:
            raise SafetyStop("CONFLICTING_RUN_SNAPSHOT")
        unique[key] = entry
    selected = list(unique.values())[:MAX_RUNS]
    totals = Counter(e["conclusion"] or e["status"] for e in selected)
    failures = Counter(
        e["category"] for e in selected
        if e["status"] == "completed" and e["conclusion"] in ("failure", "timed_out")
    )
    lessons = []
    for category, n in sorted(failures.items(), key=lambda x: (-x[1], x[0])):
        hints = SUGGESTIONS[category]
        lessons.append({
            "category": category,
            "failure_count_observed": n,
            "maturity": "REPEATED_NEEDS_SAFE_DIAGNOSTIC" if n >= 2 else "SINGLE_EVENT_MONITOR",
            "proposal": hints["proposal"],
            "required_gates": hints["required_gates"],
            "auto_code_edit_authorized": False,
            "root_cause_known": False,
        })
    return {
        "schema": ENGINE_VERSION,
        "repository": repo,
        "branch": branch,
        "generated_by_run_id": generated_run_id,
        "stage": "OBSERVE_ANALYZE_REPORT",
        "observed_runs": len(selected),
        "coverage": {"kind": "BOUNDED_RECENT_WINDOW", "limit": MAX_RUNS,
                     "at_limit": len(raw_runs) >= MAX_RUNS,
                     "complete_history_claimed": False},
        "totals": dict(totals),
        "failures_by_layer": dict(failures),
        "lessons": lessons,
        "source": "GITHUB_ACTIONS_RUN_METADATA_ONLY",
        "run_summaries": selected,
        "safety": {
            "model_retraining": False,
            "exposed_run_logs": False,
            "auto_code_edit": False,
            "production_writes": False,
            "cross_repository_writes": False,
            "stock_from_missing_offer": "UNKNOWN",
            "graphql_error_10000": "API_FAILURE_NOT_STOCK",
            "auto_write_scope": ALLOWED_OUTPUT_PREFIX,
            "code_changes_require_review": True,
        },
    }


def github_runs(repo: str, *, token: str, max_runs: int = MAX_RUNS) -> list:
    if repo != ALLOWED_REPO or not token:
        raise SafetyStop("REPOSITORY_OR_TOKEN_NOT_AVAILABLE")
    if type(max_runs) is not int or not 1 <= max_runs <= MAX_RUNS:
        raise SafetyStop("INVALID_COLLECTION_LIMIT")
    collected = []
    per_page = min(max_runs, 100)
    for page in range(1, MAX_PAGES + 1):
        url = ("https://api.github.com/repos/" + repo + "/actions/runs?per_page="
               + str(per_page) + "&page=" + str(page))
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "V31-LAB-AutoEvolution-SAFE",
        })
        try:
            with urllib.request.urlopen(req, timeout=22) as resp:
                if resp.status != 200:
                    raise SafetyStop("GITHUB_RUNS_NOT_200")
                raw = resp.read(MAX_RESPONSE + 1)
        except (urllib.error.URLError, TimeoutError, OSError):
            raise SafetyStop("GITHUB_READ_FAILED") from None
        if len(raw) > MAX_RESPONSE:
            raise SafetyStop("GITHUB_RESPONSE_TOO_LARGE")
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeError):
            raise SafetyStop("INVALID_GITHUB_JSON") from None
        if not isinstance(data, dict) or not isinstance(data.get("workflow_runs"), list):
            raise SafetyStop("INVALID_GITHUB_RUNS_SHAPE")
        runs = data["workflow_runs"]
        collected.extend(runs[:max_runs - len(collected)])
        if len(runs) < per_page or len(collected) >= max_runs:
            break
    return collected


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--branch", required=True)
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--fixture", help="Apenas testes offline. Nenhuma conexao externa.")
    args = p.parse_args(argv)
    try:
        if args.repo != ALLOWED_REPO or args.branch != ALLOWED_BRANCH:
            raise SafetyStop("TARGET_NOT_ALLOWLISTED")
        out = output_path_guard(args.out, Path.cwd())
        if out.name != str(args.run_id) + ".json":
            raise SafetyStop("RUN_ID_OUTPUT_MISMATCH")
        if out.exists():
            existing = json.loads(out.read_text(encoding="utf-8"))
            if (existing.get("repository") != args.repo or existing.get("branch") != args.branch
                    or existing.get("generated_by_run_id") != args.run_id):
                raise SafetyStop("EXISTING_REPORT_PROVENANCE_MISMATCH")
            print(json.dumps({"status": "EXISTING_REPORT_REUSED", "production_writes": False}))
            return 0
        if args.fixture:
            runs = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        else:
            runs = github_runs(args.repo, token=os.getenv("GITHUB_TOKEN", ""))
        report = collect_report(runs, repo=args.repo, branch=args.branch,
                                generated_run_id=args.run_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            raise SafetyStop("REPORT_ALREADY_EXISTS")
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
        print(json.dumps({"status": "LAB_EVIDENCE_WRITTEN", "run_id": args.run_id,
                          "observed_runs": report["observed_runs"],
                          "lesson_count": len(report["lessons"]),
                          "production_writes": False, "auto_code_edits": False}))
        return 0
    except (SafetyStop, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "AUTOEVOLUTION_FAIL_CLOSED",
                          "reason_type": type(exc).__name__,
                          "production_writes": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
