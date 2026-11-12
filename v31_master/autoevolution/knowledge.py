#!/usr/bin/env python3
"""Memoria operacional cumulativa V31 — apenas observacoes verificaveis.

Deduplica GitHub run IDs. Nao modifica codigo, nao altera configuracoes
produtivas, nao infere causa raiz, nao baixa logs nem retreina LLM.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path

from engine import (ALLOWED_REPO, ALLOWED_BRANCH, ENGINE_VERSION,
                    SafetyStop, SUGGESTIONS)

SCHEMA = "v31-autoevolution-knowledge/v1"
STATE_PATH = "v31_master/autoevolution/knowledge/state.json"
MAX_KNOWN_RUNS = 1000
TERMINAL = {"success", "failure", "timed_out", "cancelled", "neutral", "skipped", "action_required", "stale"}


def verified_report(report: object) -> dict:
    if not isinstance(report, dict):
        raise SafetyStop("REPORT_INVALID")
    if (report.get("schema") != ENGINE_VERSION or
        report.get("repository") != ALLOWED_REPO or
        report.get("branch") != ALLOWED_BRANCH or
        report.get("source") != "GITHUB_ACTIONS_RUN_METADATA_ONLY" or
        report.get("stage") != "OBSERVE_ANALYZE_REPORT"):
        raise SafetyStop("REPORT_PROVENANCE_INVALID")
    if report.get("safety", {}).get("production_writes") is not False:
        raise SafetyStop("REPORT_UNSAFE")
    if not isinstance(report.get("run_summaries"), list):
        raise SafetyStop("REPORT_RUNS_MISSING")
    return report


def _event(item: object) -> dict | None:
    if not isinstance(item, dict) or item.get("status") != "completed":
        return None
    run_id = item.get("run_id")
    category = item.get("category")
    conclusion = item.get("conclusion")
    if (not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0 or
        category not in SUGGESTIONS or conclusion not in TERMINAL):
        return None
    return {"run_id": run_id, "category": category, "conclusion": conclusion}


def update_knowledge(previous: object, report: object) -> dict:
    report = verified_report(report)
    if previous is None:
        stored = []
    else:
        if (not isinstance(previous, dict) or previous.get("schema") != SCHEMA or
            previous.get("repository") != ALLOWED_REPO or
            previous.get("branch") != ALLOWED_BRANCH or
            not isinstance(previous.get("observed"), list)):
            raise SafetyStop("KNOWLEDGE_STATE_INVALID")
        stored = previous["observed"]
    all_events: dict[int, dict] = {}
    for value in stored:
        event = _event({**value, "status": "completed"}) if isinstance(value, dict) else None
        if event is None or event["run_id"] in all_events:
            raise SafetyStop("KNOWLEDGE_STATE_CORRUPTED")
        all_events[event["run_id"]] = event
    for value in report["run_summaries"]:
        event = _event(value)
        if event is None:
            continue
        # Mantenha o registro original; nao permita que snapshots posteriores
        # reescrevam um resultado historico.
        old = all_events.get(event["run_id"])
        if old is not None and old != event:
            raise SafetyStop("CONFLICTING_RUN_HISTORY")
        all_events[event["run_id"]] = event
    if len(all_events) > MAX_KNOWN_RUNS:
        raise SafetyStop("HISTORY_LIMIT_REVIEW_REQUIRED")
    ordered = [all_events[k] for k in sorted(all_events)]
    failures = Counter(
        e["category"] for e in ordered
        if e["conclusion"] in ("failure", "timed_out"))
    successes = Counter(e["category"] for e in ordered if e["conclusion"] == "success")
    lessons = []
    for category, n in sorted(failures.items(), key=lambda v: (-v[1],v[0])):
        lessons.append({
            "category": category, "observed_failures": n,
            "observed_successes": successes.get(category, 0),
            "proposal": SUGGESTIONS[category]["proposal"],
            "required_gates": SUGGESTIONS[category]["required_gates"],
            "action": "OPEN_SAFE_EXPERIMENT_FOR_REVIEW",
            "auto_patch": False,
            "production_approval_required": True,
        })
    return {
        "schema": SCHEMA, "repository": ALLOWED_REPO, "branch": ALLOWED_BRANCH,
        "observed": ordered, "total_distinct_completed_runs": len(ordered),
        "cumulative_failures_by_layer": dict(failures),
        "cumulative_successes_by_layer": dict(successes),
        "lessons": lessons,
        "last_report_run_id": report["generated_by_run_id"],
        "security": {
            "no_model_weight_updates": True,
            "no_production_code_writes": True,
            "no_blogger_mutations": True,
            "human_review_required_for_promotion": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--report", required=True)
    p.add_argument("--state", required=True)
    args=p.parse_args(argv)
    try:
        root=Path.cwd().resolve()
        report_path=(root / args.report).resolve()
        state_path=(root / args.state).resolve()
        if (state_path != (root / STATE_PATH).resolve() or
            not report_path.is_relative_to((root / "v31_master/autoevolution/reports").resolve()) or
            not report_path.name.endswith(".json")):
            raise SafetyStop("KNOWLEDGE_PATH_DENIED")
        report=json.loads(report_path.read_text(encoding="utf-8"))
        previous=json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
        state=update_knowledge(previous, report)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps({
            "status": "LAB_KNOWLEDGE_UPDATED",
            "distinct_runs": state["total_distinct_completed_runs"],
            "learned_categories": len(state["lessons"]),
            "production_writes": False,
        }))
        return 0
    except (SafetyStop, OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"status":"KNOWLEDGE_FAIL_CLOSED", "production_writes": False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
