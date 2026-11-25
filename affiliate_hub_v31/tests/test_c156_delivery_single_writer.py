"""The reusable DRAFT workflow must own its global writer lock exactly once."""
import unittest
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
LOCK = "group: v31-editorial-catalog-single-writer"


class DeliveryConcurrencyTests(unittest.TestCase):
    def test_global_lock_once_no_nested_job_acquisition(self):
        workflow = (WORKFLOWS / "v31_independent_review_draft.yml").read_text(encoding="utf-8")
        header, jobs = workflow.split("\njobs:", 1)
        self.assertIn("\nconcurrency:", header)
        self.assertEqual(header.count(LOCK), 1)
        self.assertIn("cancel-in-progress: false", header)
        self.assertNotIn(LOCK, jobs)
        self.assertIn("deliver-draft:", jobs)
        self.assertIn("needs: independent-verifier", jobs)
        self.assertIn("affiliate_hub_v31.reviewed_draft_delivery", jobs)
        self.assertIn("V31_D1_SAFE_SQL_ONLY", jobs)
        self.assertIn("--execute-draft", jobs)

    def test_scheduler_does_not_hold_global_lock_around_reusable_call(self):
        scheduler = (WORKFLOWS / "v31_autonomous_draft_scheduler.yml").read_text(encoding="utf-8")
        header, jobs = scheduler.split("\njobs:", 1)
        self.assertNotIn(LOCK, header)
        draft = jobs.split("\n  draft:", 1)[1].split("\n  release:", 1)[0]
        self.assertIn("uses: ./.github/workflows/v31_independent_review_draft.yml", draft)
        self.assertNotIn(LOCK, draft)
