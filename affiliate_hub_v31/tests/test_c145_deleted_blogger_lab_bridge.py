"""C145: nenhum workflow principal agenda um Blogger explicitamente excluido."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / ".github/workflows/v31_lab_daily_autonomous_dispatch.yml"
DENY = ROOT / "affiliate_hub_v31/EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json"
BLOCKED_ID = "4739187376492839837"


class DeletedBloggerLabBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(DENY.read_text(encoding="utf-8"))
        cls.workflow = BRIDGE.read_text(encoding="utf-8")

    def test_target_id_is_in_official_tombstones(self):
        ids = {str(item["blog_id"]) for item in self.policy["deleted_blogs"]}
        self.assertIn(BLOCKED_ID, ids)
        self.assertEqual(len(ids), 24)

    def test_workflow_name_and_job_id_are_unchanged(self):
        self.assertIn(
            "name: V31 LAB - Ponte diaria Shopee (main agenda, LAB executa)",
            self.workflow)
        self.assertRegex(
            self.workflow,
            r"(?m)^  chamar-somente-workflow-v31-na-branch-lab:$")

    def test_no_scheduled_or_push_trigger(self):
        section = self.workflow.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertIn("  workflow_dispatch:", section)
        self.assertNotRegex(section, r"(?m)^\s*(schedule|push):")

    def test_dispatch_job_is_static_skipped(self):
        self.assertRegex(self.workflow, r"(?m)^    if: false$")
        self.assertNotIn("if: github.", self.workflow)

    def test_no_external_dispatch_or_write_permission(self):
        actions = [line.strip() for line in self.workflow.splitlines()
                   if not line.lstrip().startswith("#")]
        operational = "\n".join(actions).lower()
        self.assertNotIn("curl ", operational)
        self.assertNotIn("api.github.com", operational)
        self.assertNotIn("actions: write", operational)
        self.assertNotIn("contents: write", operational)
        self.assertNotIn("v31_target_ref", operational)

    def test_no_commercial_or_cms_secrets_are_passed(self):
        for token in ("SHOPEE_APP", "BLOGGER_REFRESH_TOKEN", "CF_LAB_BROWSER_TOKEN"):
            self.assertNotIn(token, self.workflow)

    def test_preserves_zero_mutation_footprint(self):
        self.assertNotIn("run: python ", self.workflow)
        self.assertIn("if: false", self.workflow)


if __name__ == "__main__":
    unittest.main()
