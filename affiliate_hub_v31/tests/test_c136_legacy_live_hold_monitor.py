"""C136: assert cron antigo não executa writer e não reativa LIVE."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31 import legacy_live_hold_monitor as m


def run(*, id_=100, status="completed", conclusion="success",
        created="2026-11-23T22:20:00Z"):
    return {"id": id_, "event": "schedule", "created_at": created,
            "status": status, "conclusion": conclusion}


def skipped(source):
    return [{"name": n, "conclusion": "skipped"}
            for n in m.PATHS[source]["expected_jobs"]]


class C136LegacyHoldMonitorTests(unittest.TestCase):
    def test_static_hold_casa_oficina_and_policy(self):
        self.assertIsNone(m.assert_static_live_hold())

    def test_no_run_is_observation_pending(self):
        r = m.evaluate_hold_run(source="casa", run=None, jobs=None)
        self.assertEqual(r["status"], "PENDING_OBSERVATION")

    def test_incomplete_run_is_not_verified(self):
        r = m.evaluate_hold_run(source="oficina",
                                run=run(status="in_progress", conclusion=None),
                                jobs=None)
        self.assertEqual(r["status"], "PENDING_RUN_COMPLETION")

    def test_both_jobs_skipped_are_verified(self):
        for source in m.PATHS:
            with self.subTest(source=source):
                result = m.evaluate_hold_run(source=source, run=run(),
                                             jobs=skipped(source))
                self.assertEqual(result["status"], "SKIP_VERIFIED")

    def test_a_single_executed_job_is_security_exception(self):
        jobs = skipped("casa")
        jobs[1]["conclusion"] = "success"
        result = m.evaluate_hold_run(source="casa", run=run(), jobs=jobs)
        self.assertEqual(result["status"], "SECURITY_EXCEPTION_JOB_RAN")

    def test_successful_extra_job_is_security_exception(self):
        jobs = skipped("oficina") + [{"name": "extra", "conclusion": "success"}]
        result = m.evaluate_hold_run(source="oficina", run=run(), jobs=jobs)
        self.assertEqual(result["status"], "SECURITY_EXCEPTION_JOB_RAN")

    def test_missing_job_is_unverified(self):
        result = m.evaluate_hold_run(source="oficina", run=run(),
                                     jobs=skipped("oficina")[:1])
        self.assertEqual(result["status"], "UNVERIFIED_JOB_STATE")

    def test_premerge_schedule_is_not_accepted_as_proof(self):
        with self.assertRaisesRegex(m.LegacyHoldAuditError, "post_hold"):
            m.evaluate_hold_run(source="casa", run=run(created="2026-11-23T20:00:00Z"),
                                jobs=skipped("casa"))

    def test_manual_dispatch_run_is_not_accepted(self):
        candidate = {**run(), "event": "workflow_dispatch"}
        with self.assertRaisesRegex(m.LegacyHoldAuditError, "post_hold"):
            m.evaluate_hold_run(source="casa", run=candidate,
                                jobs=skipped("casa"))

    def test_latest_postmerge_schedule_selected(self):
        old = run(id_=1, created="2026-11-23T19:15:00Z")
        a = run(id_=2, created="2026-11-23T22:15:00Z")
        b = run(id_=3, created="2026-11-23T22:17:00Z")
        self.assertEqual(m.recent_post_hold_run([old,b,a])["id"], 3)

    def test_only_old_runs_is_pending(self):
        old = run(created="2026-11-23T20:57:59Z")
        self.assertIsNone(m.recent_post_hold_run([old]))

    def test_duplicate_job_names_fail_closed(self):
        with self.assertRaisesRegex(m.LegacyHoldAuditError, "duplicate_jobs"):
            m.evaluate_hold_run(source="casa", run=run(),
                                jobs=[skipped("casa")[0], skipped("casa")[0]])

    def test_github_get_disallows_paths_outside_actions(self):
        with self.assertRaisesRegex(m.LegacyHoldAuditError, "path_invalid"):
            m._get_json("/repos/other/repo/actions/runs", "read-token")

    def test_readonly_audit_reads_only_schedules_and_jobs(self):
        paths = []
        def fake_get(path, token):
            self.assertEqual(token, "token")
            paths.append(path)
            if "/runs?" in path:
                return {"workflow_runs": [run()]}
            self.assertIn("/jobs?", path)
            source = "casa" if "casa" in paths[-2] else "oficina"
            return {"jobs": skipped(source)}
        with (patch.object(m, "_get_json", side_effect=fake_get),
              patch.object(m, "assert_static_live_hold")):
            result = m.audit(token="token")
        self.assertTrue(result["all_holds_verified"])
        self.assertEqual(result["cms_writes"], 0)
        self.assertEqual(result["d1_writes"], 0)
        self.assertEqual(result["workflow_dispatches"], 0)
        self.assertFalse(result["automatic_live_authorized"])
        self.assertEqual(len(paths), 4)
        self.assertTrue(all("/actions/" in x for x in paths))

    def test_pending_does_not_imply_all_verified(self):
        def fake_get(path, token):
            return {"workflow_runs": []}
        with (patch.object(m, "_get_json", side_effect=fake_get),
              patch.object(m, "assert_static_live_hold")):
            result = m.audit(token="token")
        self.assertFalse(result["all_holds_verified"])
        self.assertEqual(
            [x["status"] for x in result["workflows"]],
            ["PENDING_OBSERVATION","PENDING_OBSERVATION"])


if __name__ == "__main__":
    unittest.main()
