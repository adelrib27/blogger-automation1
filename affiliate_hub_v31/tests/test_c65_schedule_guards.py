"""C65 — canários cron não podem criar novos DRAFTs por acidente."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]/".github"/"workflows"

class ScheduleSafeModeTests(unittest.TestCase):
    def test_blogger_only_normal_daily_schedule_can_create_draft(self):
        y=(ROOT/"v31_universal_blogger_autodraft_daily.yml").read_text()
        self.assertIn("github.event.schedule == '18 12 * * *'",y)
        self.assertIn("github.event_name == 'workflow_dispatch'",y)
        self.assertIn("V31_DRAFT_EXECUTE:",y)
        self.assertEqual(y.count("    - cron:"),1)
        self.assertIn("'false'",y)
        self.assertIn("publish_enabled", (Path(__file__).resolve().parents[1]/"routing.py").read_text())

    def test_wordpress_only_normal_daily_schedule_may_request_draft(self):
        y=(ROOT/"v31_universal_wordpress_autodraft_daily.yml").read_text()
        self.assertIn("github.event.schedule == '41 12 * * *'",y)
        self.assertIn("V31_UNIVERSAL_WORDPRESS_AUTODRAFT_ENABLED",y)
        self.assertEqual(y.count("    - cron:"),1)
        self.assertIn("github.event_name == 'workflow_dispatch'",y)
        self.assertIn("'false'",y)
        self.assertIn("DRAFT_ONLY", (Path(__file__).resolve().parents[1]/"automatic_wordpress_drafts.py").read_text())

if __name__=="__main__":
    unittest.main()
