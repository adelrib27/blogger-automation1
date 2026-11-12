#!/usr/bin/env python3
"""Provas offline do motor de evolucao: nenhuma rede e nenhuma escrita em producao."""
from __future__ import annotations
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "autoevolution"))
import engine as e

REPO = e.ALLOWED_REPO
BRANCH = e.ALLOWED_BRANCH


def run(run_id, name, conclusion, *, repo=REPO, branch="main", event="schedule",
        status="completed"):
    return {
        "id": run_id, "name": name, "head_branch": branch,
        "repository": {"full_name": repo}, "event": event, "status": status,
        "conclusion": conclusion,
        "html_url": "https://evil.example/not-used",
        "some_untrusted_log": "Authorization: Bearer should-never-persist",
    }


class TestEngine(unittest.TestCase):
    def test_failures_aggregated_without_diagnosing_root_cause(self):
        samples = [
            run(100001, "V31 Shopee Loja", "failure"),
            run(100002, "V31 Shopee Loja", "failure"),
            run(100003, "V31 Contato", "success"),
            run(100004, "Visual theme", "timed_out"),
        ]
        report = e.collect_report(samples, repo=REPO, branch=BRANCH,
                                  generated_run_id=999999)
        self.assertEqual(report["observed_runs"], 4)
        self.assertEqual(report["failures_by_layer"]["SHOPEE_PIPELINE"], 2)
        item = next(x for x in report["lessons"] if x["category"] == "SHOPEE_PIPELINE")
        self.assertEqual(item["maturity"], "REPEATED_NEEDS_SAFE_DIAGNOSTIC")
        self.assertFalse(item["root_cause_known"])
        self.assertFalse(item["auto_code_edit_authorized"])
        self.assertEqual(report["stage"], "OBSERVE_ANALYZE_REPORT")
        self.assertFalse(report["safety"]["production_writes"])

    def test_cross_repository_input_excluded(self):
        d = e.collect_report([run(100001, "Shopee Loja", "failure",
                                  repo="another-owner/other")],
                             repo=REPO, branch=BRANCH, generated_run_id=999999)
        self.assertEqual(d["observed_runs"], 0)

    def test_cross_repository_target_denied(self):
        with self.assertRaises(e.SafetyStop):
            e.collect_report([], repo="another-owner/other",
                             branch=BRANCH, generated_run_id=999999)

    def test_protected_branch_denied(self):
        with self.assertRaises(e.SafetyStop):
            e.collect_report([], repo=REPO, branch="main", generated_run_id=999999)

    def test_current_run_excluded(self):
        report = e.collect_report([run(999999, "V31 Shopee", "failure")],
                                  repo=REPO, branch=BRANCH, generated_run_id=999999)
        self.assertEqual(report["observed_runs"], 0)

    def test_rejects_invalid_or_bearer_workflow_name(self):
        d = e.collect_report([run(111111, "token=XXX", "failure"),
                              run(222222, "", "failure"),
                              run(333333, "Normal Shopee", "failure")],
                             repo=REPO, branch=BRANCH, generated_run_id=999999)
        self.assertEqual(d["observed_runs"], 1)
        self.assertNotIn("XXX", json.dumps(d))

    def test_never_copy_untrusted_urls_or_logs(self):
        d = e.collect_report([run(111111, "Loja SAFE", "failure")],
                             repo=REPO, branch=BRANCH, generated_run_id=999999)
        s = json.dumps(d)
        self.assertNotIn("evil.example", s)
        self.assertNotIn("should-never-persist", s)
        self.assertIn("https://github.com/" + REPO + "/actions/runs/111111", s)

    def test_api_failures_are_not_inventory_events(self):
        d = e.collect_report([run(111111, "Loja Shopee", "failure")],
                             repo=REPO, branch=BRANCH, generated_run_id=999999)
        self.assertEqual(d["safety"]["stock_from_missing_offer"], "UNKNOWN")
        self.assertEqual(d["safety"]["graphql_error_10000"], "API_FAILURE_NOT_STOCK")

    def test_success_does_not_generate_repair_proposal(self):
        d = e.collect_report([run(111111, "Loja Shopee", "success")],
                             repo=REPO, branch=BRANCH, generated_run_id=999999)
        self.assertEqual(d["lessons"], [])

    def test_duplicate_run_id_dedup(self):
        sample=run(111111, "Loja Shopee", "failure")
        d = e.collect_report([sample,sample], repo=REPO, branch=BRANCH,
                             generated_run_id=999999)
        self.assertEqual(d["observed_runs"], 1)

    def test_workflow_in_progress_not_false_failure(self):
        d = e.collect_report([run(111111, "Loja Shopee", "failure",
                                  status="in_progress")],
                             repo=REPO, branch=BRANCH, generated_run_id=999999)
        self.assertEqual(d["lessons"], [])

    def test_self_workflow_excluded(self):
        d = e.collect_report([run(111111, "V31 LAB Autoevolucao SAFE", "failure")],
                             repo=REPO, branch=BRANCH, generated_run_id=999999)
        self.assertEqual(d["observed_runs"], 0)

    def test_output_guard_accepts_exact_folder_and_id(self):
        with tempfile.TemporaryDirectory() as d:
            p=e.output_path_guard("v31_master/autoevolution/reports/123456.json",Path(d))
            self.assertTrue(str(p).endswith("/v31_master/autoevolution/reports/123456.json"))

    def test_output_guard_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(e.SafetyStop):
                e.output_path_guard("v31_master/autoevolution/reports/../../../../AGENTS.md", Path(d))

    def test_output_guard_rejects_code_edits(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(e.SafetyStop):
                e.output_path_guard("v31_master/shopee_r2_safe.py", Path(d))

    def test_commit_guard_rejects_main_source_file(self):
        with self.assertRaises(e.SafetyStop):
            e.changed_paths_guard(["achados_da_rotina/rotation_v31.py"])

    def test_commit_guard_rejects_theme(self):
        with self.assertRaises(e.SafetyStop):
            e.changed_paths_guard(["blogger_themes/modelo.xml"])

    def test_commit_guard_accepts_one_report(self):
        e.changed_paths_guard(["v31_master/autoevolution/reports/123456.json"])

    def test_commit_guard_rejects_arbitrary_json(self):
        with self.assertRaises(e.SafetyStop):
            e.changed_paths_guard(["v31_master/autoevolution/reports/config.json"])

    def test_github_api_not_called_when_fixture(self):
        sample=[run(111111,"Shopee Loja","failure")]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            fixture=root/"sample.json"
            fixture.write_text(json.dumps(sample),encoding="utf-8")
            with patch.object(e,"github_runs",side_effect=AssertionError("NO_NETWORK")):
                with patch.object(e.Path,"cwd",return_value=root):
                    output=io.StringIO()
                    with redirect_stdout(output):
                        rc=e.main(["--repo",REPO,"--branch",BRANCH,"--run-id","999999",
                                  "--out","v31_master/autoevolution/reports/999999.json",
                                  "--fixture",str(fixture)])
            self.assertEqual(rc,0)
            report=json.loads((root/"v31_master/autoevolution/reports/999999.json").read_text(encoding="utf-8"))
            self.assertEqual(report["observed_runs"],1)
            self.assertFalse(report["safety"]["auto_code_edit"])

    def test_invalid_repo_cli_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch.object(e.Path,"cwd",return_value=root):
                with redirect_stdout(io.StringIO()):
                    rc=e.main(["--repo","other/repo","--branch",BRANCH,"--run-id","999999",
                               "--out","v31_master/autoevolution/reports/999999.json"])
            self.assertEqual(rc,2)
            self.assertFalse((root/"v31_master").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
