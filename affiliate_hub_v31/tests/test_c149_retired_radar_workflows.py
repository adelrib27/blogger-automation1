"""C149: old Radar-only scheduled writers are gone; the V31 universal core stays."""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.routing import sites
from affiliate_hub_v31.site_request_queue import (
    autonomous_sites_for_writes, load_requests, scheduled_draft_pilot,
)
from affiliate_hub_v31 import autonomous_review

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "affiliate_hub_v31/EDITORIAL_LEGACY_RADAR_RETIREMENT_C149.json"
DATA = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


class RetiredRadarWorkflowTests(unittest.TestCase):
    def test_manifest_has_exact_ten_retired_workflows(self):
        self.assertEqual(len(DATA["retired_workflows"]), 10)
        self.assertEqual(len({e["path"] for e in DATA["retired_workflows"]}), 10)

    def test_retired_workflows_absent_from_current_main_tree(self):
        for entry in DATA["retired_workflows"]:
            with self.subTest(path=entry["path"]):
                self.assertFalse((ROOT / entry["path"]).exists())

    def test_retirement_includes_all_three_scheduled_old_radar_workflows(self):
        retired={e["path"] for e in DATA["retired_workflows"]}
        for name in ("radar_editorial_vnext_autonomous.yml",
                     "radar_fase3_fila_diaria.yml",
                     "radar_store_autonomous.yml"):
            self.assertIn(".github/workflows/"+name,retired)

    def test_retirement_includes_lg24_one_shot_that_consumed_d1(self):
        retired={e["path"] for e in DATA["retired_workflows"]}
        self.assertIn(".github/workflows/v31_radarwp_lg12_20261124_once.yml",
                      retired)
        self.assertEqual(DATA["historical_attempts_radarwp"][-1]["source_run"],
                         45372082046)

    def test_history_preserved_without_source_shortlink(self):
        self.assertTrue(DATA["historical_d1_records_preserved"])
        self.assertTrue(DATA["historical_r2_records_preserved"])
        self.assertTrue(DATA["legacy_restoration_requires_new_review"])
        self.assertNotIn("https://s.shopee.com.br/",
                         json.dumps(DATA,sort_keys=True))

    def test_all_three_historical_campaign_skus_unique(self):
        attempts=DATA["historical_attempts_radarwp"]
        self.assertEqual(len(attempts),3)
        self.assertEqual(len({a["sku"] for a in attempts}),3)
        self.assertEqual({a["day_utc"] for a in attempts},
                         {"2026-11-23","2026-11-24"})

    def test_old_monolithic_wordpress_publishing_not_reachable_by_workflows(self):
        for legacy in DATA["retired_workflows"]:
            if legacy["path"].endswith(".yml"):
                self.assertFalse((ROOT / legacy["path"]).is_file())

    def test_universal_wordpress_and_blogger_automation_remain(self):
        for path in (".github/workflows/v31_universal_wordpress_autodraft_daily.yml",
                     ".github/workflows/v31_universal_blogger_autodraft_daily.yml",
                     ".github/workflows/v31_autonomous_draft_scheduler.yml",
                     ".github/workflows/v31_independent_review_draft.yml",
                     ".github/workflows/v31_c148_universal_pilot_readonly.yml"):
            self.assertTrue((ROOT / path).is_file(),path)

    def test_wordpress_radar_route_stays_registered_unmodified(self):
        route=sites()["wordpress_radartechbr"]
        self.assertEqual(route["campaign"],"radarwp")
        self.assertEqual(route["identifier"],"https://radartechbr.com.br/")
        self.assertIs(route["publish_enabled"],False)

    def test_scheduled_pilot_requires_its_own_target_and_keeps_regular_rollout(self):
        radar = "wordpress_radartechbr"
        regular = "blogger_moveis_para_cada_canto"
        profiles = json.loads(autonomous_review.PROFILE.read_text(encoding="utf-8"))
        self.assertIn(radar, [request["site_key"] for request in load_requests()])
        with patch.dict(os.environ, {"V31_AUTODRAFT_ACTIVE": "true",
                                     "V31_AUTODRAFT_ROLLOUT_SITE": regular}, clear=True):
            self.assertEqual(scheduled_draft_pilot(profiles), "")
            os.environ["V31_AUTODRAFT_PILOT_SITE"] = radar
            self.assertEqual(scheduled_draft_pilot(profiles), radar)
            self.assertEqual(autonomous_sites_for_writes(), {regular})
            for overlapping in ("all", radar):
                os.environ["V31_AUTODRAFT_ROLLOUT_SITE"] = overlapping
                self.assertEqual(scheduled_draft_pilot(profiles), "")

    def test_universal_reviewer_still_shares_single_budget(self):
        from affiliate_hub_v31.site_request_queue import MAX_BUDGET
        self.assertEqual(MAX_BUDGET,3)
        self.assertIn("claim_conversion_attempt",
                      (ROOT/"affiliate_hub_v31/autonomous_review.py").read_text(encoding="utf-8"))

    def test_legacy_wp_store_rotation_not_falsely_claimed_migrated(self):
        self.assertIn("NOT claimed",DATA["retired_store_writer_note"])

    def test_radar_shared_src_selftest_preserved(self):
        self.assertTrue((ROOT/"radar_tech_br/src/self_test.py").exists())
        self.assertTrue((ROOT/"radar_tech_br/src/generate_articles.py").exists())

    def test_other_blogger_retirement_scope_not_affected(self):
        self.assertTrue((ROOT/".github/workflows/radar_tech_blogger_store_autonomous.yml").exists())

    def test_universal_live_policy_still_requires_approval(self):
        policy=json.loads((ROOT/"affiliate_hub_v31/autonomous_live_policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["activation"],"pending_policy_approval")


if __name__=="__main__":
    unittest.main()
