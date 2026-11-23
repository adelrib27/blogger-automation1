"""C133: auditor de cadastros não concede licença de publicação."""
import unittest

from affiliate_hub_v31.autodraft_rollout_readiness import build_readiness


def blogger(id_, campaign="cozinha"):
    return {
        "site_key": "blogger_cozinha", "platform": "blogger",
        "identifier": id_, "campaign": campaign,
        "allowed_niches": ["cozinha/air_fryers"], "publish_enabled": False,
    }


def wordpress():
    return {
        "site_key": "wordpress_casa", "platform": "wordpress",
        "identifier": "https://casa.example.test/", "campaign": "casawp",
        "allowed_niches": ["casa/decoracao"], "publish_enabled": False,
    }


class RolloutReadinessTests(unittest.TestCase):
    def setUp(self):
        self.portfolio = {"kept": [
            {"id": "1234567890123456789", "name": "Cozinha"},
            {"id": "9876543210987654321", "name": "Pet"},
        ]}
        self.routes = {
            "blogger_cozinha": blogger("1234567890123456789"),
            "wordpress_casa": wordpress(),
        }

    def test_missing_blogger_route_fails_closed_without_inventing_campaign(self):
        report = build_readiness(
            self.portfolio, self.routes,
            {"blogger_cozinha", "wordpress_casa"},
            {"blogger_cozinha", "wordpress_casa"})
        self.assertEqual(report["priority_sites"], 3)
        self.assertEqual(report["configured_for_draft_preflight"], 2)
        self.assertFalse(report["all_configured_for_draft_preflight"])
        missing = next(r for r in report["sites"] if r["name"] == "Pet")
        self.assertEqual(missing["status"], "ROUTE_MISSING")
        self.assertIsNone(missing["campaign_from_registry"])
        self.assertFalse(missing["configured_for_draft_preflight"])

    def test_route_alone_is_not_approval_for_autonomous_draft(self):
        report = build_readiness(self.portfolio, self.routes, set(), set())
        original = next(r for r in report["sites"] if r["name"] == "Cozinha")
        self.assertEqual(original["status"], "PROFILE_AND_REQUEST_MISSING")
        self.assertFalse(original["configured_for_draft_preflight"])

    def test_publish_enabled_true_blocks_preflight_even_with_profile(self):
        self.routes["blogger_cozinha"]["publish_enabled"] = True
        report = build_readiness(
            self.portfolio, self.routes,
            {"blogger_cozinha", "wordpress_casa"},
            {"blogger_cozinha", "wordpress_casa"})
        target = next(r for r in report["sites"] if r["name"] == "Cozinha")
        self.assertEqual(target["status"], "ROUTE_UNSAFE")
        self.assertFalse(target["configured_for_draft_preflight"])

    def test_registration_is_declarative_for_future_blogs(self):
        self.routes["blogger_pet"] = {
            "site_key": "blogger_pet", "platform": "blogger",
            "identifier": "9876543210987654321", "campaign": "petverified",
            "allowed_niches": ["pets/cuidados_acessorios"], "publish_enabled": False}
        report = build_readiness(
            self.portfolio, self.routes,
            {"blogger_cozinha", "wordpress_casa", "blogger_pet"},
            {"blogger_cozinha", "wordpress_casa", "blogger_pet"})
        self.assertEqual(report["configured_for_draft_preflight"], 3)
        self.assertTrue(report["all_configured_for_draft_preflight"])
        self.assertTrue(all(x["status"] == "CONFIGURED_NOT_REMOTE_HOMOLOGATED"
                            for x in report["sites"]))
        self.assertTrue(all(x["status"] != "LIVE_APPROVED"
                            for x in report["sites"]))

    def test_duplicate_portfolio_ids_are_an_error(self):
        with self.assertRaisesRegex(ValueError, "portfolio_blog_id_invalid"):
            build_readiness(
                {"kept": [{"id": "1234567890123456789"},
                          {"id": "1234567890123456789"}]},
                self.routes, set(), set())


if __name__ == "__main__":
    unittest.main()
