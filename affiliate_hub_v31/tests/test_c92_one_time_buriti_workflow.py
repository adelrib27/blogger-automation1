"""C92 one-time E2E route must never expand scope or turn LIVE on."""
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "v31_c92_buriti_one_time_e2e.yml"

class BuritiOneTimeWorkflowTests(unittest.TestCase):
    def test_single_utc_day_and_one_exact_sku(self):
        text=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("cron: '23 0 23 11 *'",text)
        self.assertIn('date -u +%F',text)
        self.assertIn('"2026-11-23"',text)
        self.assertIn("v31-editorial-catalog-single-writer",text)
        self.assertIn("shopee:1235923910:19299550912",text)
        self.assertIn("--target-site-key blogger_moveis_para_cada_canto",text)
        self.assertIn("--budget 1",text)
        self.assertIn("--execute",text)
        self.assertNotIn("workflow_dispatch:",text)
        self.assertNotIn("cancel-in-progress: true",text)

    def test_strict_repo_rollout_and_no_live_writer(self):
        text=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("vars.V31_AUTODRAFT_ACTIVE == 'true'",text)
        self.assertIn("vars.V31_AUTODRAFT_ROLLOUT_SITE == 'blogger_moveis_para_cada_canto'",text)
        self.assertIn("vars.V31_AUTOLIVE_ACTIVE != 'true'",text)
        self.assertIn("vars.V31_AUTODRAFT_FULL_ROLLOUT_APPROVED != 'true'",text)
        self.assertIn("environment: v31-editorial-safe",text)
        self.assertIn("uses: ./.github/workflows/v31_independent_review_draft.yml",text)
        self.assertIn("needs.exact-buriti-conversion.outputs.conversion_ready == 'true'",text)
        self.assertNotIn("uses: ./.github/workflows/v31_autonomous_live",text)
        self.assertNotIn("publish_post",text)
        self.assertNotIn("AUTOLIVE_ACTIVE: true",text)

    def test_conversion_gate_requires_persisted_exact_link(self):
        text=WORKFLOW.read_text(encoding="utf-8")
        for s in (
            'result.get("converted")==1',
            'result.get("shopee_mutation_attempts")==1',
            'result.get("r2_snapshot_saved_and_verified") is True',
            'result.get("publication_calls")==0',
            'result.get("api_interrupted") is False',
            'print("conversion_ready=true")',
            "V31_D1_SAFE_SQL_ONLY",
        ):
            self.assertIn(s,text)
        self.assertEqual(text.count('print("conversion_ready=true")'),1)
        self.assertIn("secrets: inherit",text)

if __name__ == "__main__":
    unittest.main()
