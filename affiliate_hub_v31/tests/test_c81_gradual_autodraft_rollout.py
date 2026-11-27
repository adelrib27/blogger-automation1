"""C81: phased DRAFT writer migration without widening LIVE permissions.

All tests are offline. They never access CMS, R2, D1, Firecrawl or Shopee.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31 import site_request_queue as queue


class PhasedAutoDraftRolloutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.profiles = Path(self.tmp.name) / "profiles.json"
        self.profiles.write_text(json.dumps({
            "blogger_registered": {"offers": {}},
            "wordpress_registered": {"offers": {}},
        }), encoding="utf-8")
        self.requests = [
            {"site_key": "blogger_registered", "platform": "blogger",
             "topic": "teste", "articles": None, "enabled": True},
            {"site_key": "wordpress_registered", "platform": "wordpress",
             "topic": "teste", "articles": None, "enabled": True},
            {"site_key": "without_review_profile", "platform": "wordpress",
             "topic": "teste", "articles": None, "enabled": True},
        ]
        p = patch.object(queue, "VERIFIER_PROFILES", self.profiles)
        p.start()
        self.addCleanup(p.stop)
        requests_patch = patch.object(queue, "load_requests",
                                      return_value=self.requests)
        requests_patch.start()
        self.addCleanup(requests_patch.stop)

    def migrated(self, **variables):
        with patch.dict(os.environ, variables, clear=True):
            return queue.autonomous_sites_for_writes()

    def test_default_is_never_migrated_or_live(self):
        self.assertEqual(self.migrated(), set())
        self.assertEqual(self.migrated(V31_AUTODRAFT_ACTIVE="false",
                                      V31_AUTODRAFT_ROLLOUT_SITE="all",
                                      V31_AUTODRAFT_FULL_ROLLOUT_APPROVED="true"), set())

    def test_global_arm_alone_does_not_transfer_all_sites(self):
        self.assertEqual(self.migrated(V31_AUTODRAFT_ACTIVE="true"), set())
        self.assertEqual(self.migrated(V31_AUTODRAFT_ACTIVE="true",
                                      V31_AUTODRAFT_ROLLOUT_SITE=""), set())

    def test_only_exact_registered_profile_can_migrate(self):
        self.assertEqual(self.migrated(
            V31_AUTODRAFT_ACTIVE="true",
            V31_AUTODRAFT_ROLLOUT_SITE="blogger_registered"),
            {"blogger_registered"})
        self.assertEqual(self.migrated(
            V31_AUTODRAFT_ACTIVE="true",
            V31_AUTODRAFT_ROLLOUT_SITE="wordpress_registered"),
            {"wordpress_registered"})
        for unsafe in ("without_review_profile", "fake_blog", "blogger_registered,wordpress_registered",
                       "BLOGGER_REGISTERED", "../site", " blogger_registered ", "true"):
            with self.subTest(unsafe=unsafe):
                self.assertEqual(self.migrated(
                    V31_AUTODRAFT_ACTIVE="true",
                    V31_AUTODRAFT_ROLLOUT_SITE=unsafe), set())

    def test_full_rollout_needs_a_second_explicit_approval(self):
        self.assertEqual(self.migrated(V31_AUTODRAFT_ACTIVE="true",
                                      V31_AUTODRAFT_ROLLOUT_SITE="all"), set())
        self.assertEqual(self.migrated(V31_AUTODRAFT_ACTIVE="true",
                                      V31_AUTODRAFT_ROLLOUT_SITE="all",
                                      V31_AUTODRAFT_FULL_ROLLOUT_APPROVED="false"), set())
        self.assertEqual(self.migrated(
            V31_AUTODRAFT_ACTIVE="true", V31_AUTODRAFT_ROLLOUT_SITE="all",
            V31_AUTODRAFT_FULL_ROLLOUT_APPROVED="true"),
            {"blogger_registered", "wordpress_registered"})

    def test_legacy_and_new_workflows_share_the_same_rollout_contract(self):
        root = Path(__file__).resolve().parents[2] / ".github" / "workflows"
        legacy = ["v31_universal_blogger_autodraft_daily.yml",
                  "v31_universal_wordpress_autodraft_daily.yml"]
        for filename in legacy:
            with self.subTest(workflow=filename):
                yml = (root / filename).read_text(encoding="utf-8")
                for var in ("V31_AUTODRAFT_ACTIVE", "V31_AUTODRAFT_ROLLOUT_SITE",
                            "V31_AUTODRAFT_FULL_ROLLOUT_APPROVED"):
                    self.assertIn(var + ": " + "$" + "{{ vars." + var + " }}", yml)
                self.assertIn("group: v31-editorial-catalog-single-writer", yml)
        scheduler = (root / "v31_autonomous_draft_scheduler.yml").read_text(encoding="utf-8")
        self.assertIn("autonomous_sites_for_writes", scheduler)
        self.assertIn("vars.V31_AUTODRAFT_ROLLOUT_SITE != ''", scheduler)
        self.assertIn("vars.V31_AUTODRAFT_FULL_ROLLOUT_APPROVED == 'true'", scheduler)
        self.assertIn("IS_SCHEDULE", scheduler)
        self.assertIn("observe-homologation:", scheduler)
        self.assertIn("vars.V31_AUTOLIVE_ACTIVE == 'true'", scheduler)
        self.assertIn("vars.V31_AUTODRAFT_ACTIVE == 'true'", scheduler)
        reusable = (root / "v31_independent_review_draft.yml").read_text(encoding="utf-8")
        self.assertIn("group: v31-editorial-catalog-single-writer", reusable)

    def test_pilot_fallback_uses_regular_schedule_and_cannot_release(self):
        root = Path(__file__).resolve().parents[2] / ".github" / "workflows"
        scheduler = (root / "v31_autonomous_draft_scheduler.yml").read_text(encoding="utf-8")
        fallback = scheduler.split("\n  choose-pilot-fallback:\n", 1)[1]
        self.assertIn("needs: audit", fallback)
        self.assertIn("github.event_name == 'schedule'", fallback)
        self.assertIn("github.event.schedule == '47 */4 * * *'", fallback)
        self.assertIn("scheduled_draft_pilot(profiles)", fallback)
        self.assertIn("from_environment(allow_mutations=False)", fallback)
        self.assertIn('if status == "DUE":', fallback)
        self.assertIn("uses: ./.github/workflows/v31_independent_review_draft.yml", fallback)
        release = scheduler.split("\n  release:\n", 1)[1].split("\n  audit:\n", 1)[0]
        self.assertIn("needs: draft", release)
        self.assertNotIn("pilot-fallback", release)


if __name__ == "__main__":
    unittest.main()
