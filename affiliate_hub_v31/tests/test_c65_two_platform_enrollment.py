"""C65 — fila multi-site real: Blogger e WordPress, campanhas nunca copiadas."""
import unittest
from pathlib import Path

from affiliate_hub_v31.routing import sites
from affiliate_hub_v31.site_request_queue import load_requests

ROOT=Path(__file__).resolve().parents[2]


class MultiPlatformEnrollmentTests(unittest.TestCase):
    def test_real_blogger_and_wordpress_requests_are_continuous_and_isolated(self):
        requests={entry["site_key"]:entry for entry in load_requests()}
        blogger=requests["blogger_moveis_para_cada_canto"]
        wordpress=requests["wordpress_casa_decoracao"]
        routes=sites()
        self.assertEqual(blogger["platform"],"blogger")
        self.assertEqual(wordpress["platform"],"wordpress")
        self.assertIsNone(blogger["articles"])
        self.assertIsNone(wordpress["articles"])
        self.assertTrue(blogger["enabled"] and wordpress["enabled"])
        self.assertNotEqual(routes[blogger["site_key"]]["campaign"],
                            routes[wordpress["site_key"]]["campaign"])
        self.assertTrue(routes[wordpress["site_key"]]["identifier"].startswith("https://"))
        self.assertFalse(routes[wordpress["site_key"]]["publish_enabled"])
        self.assertEqual(wordpress["topic"],"vaso decorativo")

    def test_schedule_is_draft_only_and_can_be_paused(self):
        wf=(ROOT/".github/workflows/v31_universal_wordpress_autodraft_daily.yml").read_text()
        self.assertIn("V31_UNIVERSAL_WORDPRESS_AUTODRAFT_ENABLED != 'false'",wf)
        self.assertIn("github.event.schedule == '41 12 * * *'",wf)
        self.assertIn("CASA_WORDPRESS_APP_PASSWORD",wf)
        self.assertIn("python -m affiliate_hub_v31.automatic_wordpress_drafts",wf)
        self.assertNotIn(' --publish',wf)

if __name__=="__main__":
    unittest.main()
