#!/usr/bin/env python3
"""Recompute downloaded evidence before staging it; no artifact code execution."""
import json
import os
import subprocess
from pathlib import Path
from engine import ALLOWED_BRANCH, ALLOWED_REPO, SafetyStop, collect_report
from knowledge import update_knowledge


def main():
    if os.environ.get('GITHUB_REPOSITORY') != ALLOWED_REPO or os.environ.get('GITHUB_REF_NAME') != ALLOWED_BRANCH:
        raise SafetyStop('EVIDENCE_TARGET_DENIED')
    run_id = int(os.environ['GITHUB_RUN_ID'])
    root = Path('v31_master/autoevolution')
    incoming = Path('evidence-input')
    report_path = incoming / 'reports' / f'{run_id}.json'
    report = json.loads(report_path.read_text())
    if report.get('generated_by_run_id') != run_id:
        raise SafetyStop('EVIDENCE_RUN_MISMATCH')
    # Validate every API-derived field again using the trusted collector.
    raw = [{'id': x['run_id'], 'run_attempt': x.get('run_attempt', 1),
            'name': x['workflow'], 'head_branch': x['branch'],
            'repository': {'full_name': ALLOWED_REPO}, 'event': x['event'],
            'status': x['status'], 'conclusion': x['conclusion']}
           for x in report['run_summaries']]
    canonical = collect_report(raw, repo=ALLOWED_REPO, branch=ALLOWED_BRANCH,
                               generated_run_id=run_id)
    # Coverage describes the raw window before invalid/self runs were excluded.
    if any(report.get(k) != canonical[k] for k in ('repository', 'branch', 'run_summaries',
           'lessons', 'totals', 'failures_by_layer', 'observed_runs', 'safety', 'schema', 'source', 'stage')):
        raise SafetyStop('EVIDENCE_NOT_CANONICAL')
    state_path = root / 'knowledge/state.json'
    previous = json.loads(state_path.read_text()) if state_path.exists() else None
    baseline = json.loads(subprocess.check_output([
        'git', 'show', os.environ['GITHUB_SHA'] + ':v31_master/autoevolution/knowledge/state.json'
    ], text=True))
    expected = update_knowledge(baseline, report)
    received = json.loads((incoming / 'knowledge/state.json').read_text())
    if expected != received:
        raise SafetyStop('EVIDENCE_STATE_MISMATCH')
    # Merge against current LAB state after checking artifact provenance at trigger SHA.
    expected = update_knowledge(previous, report)
    report_destination = root / 'reports' / f'{run_id}.json'
    if report_destination.exists() and json.loads(report_destination.read_text()) != report:
        raise SafetyStop('IMMUTABLE_REPORT_CONFLICT')
    for destination, data in [(root / 'reports' / f'{run_id}.json', report), (state_path, expected)]:
        if destination.is_symlink() or not destination.resolve().is_relative_to(Path.cwd().resolve()):
            raise SafetyStop('EVIDENCE_SYMLINK_DENIED')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
