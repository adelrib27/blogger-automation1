"""C141: cobertura global (28 Blogger) sem autorizar outras contas sem autenticação.

Tudo sintético/local: lê apenas os manifests históricos versionados no GitHub.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31 import editorial_scope_validation as g

POLICY = g.load_policy()
HISTORY = g.load_global_inventory(POLICY)


class HistoricalPortfolioReconciliationTests(unittest.TestCase):
    def test_historical_source_has_30_distinct_blogger_ids(self):
        entries = HISTORY["sites"]
        self.assertEqual(len(entries),30)
        self.assertEqual(len({r["blog_id"] for r in entries}),30)
        self.assertEqual(len({r["legacy_site_key"] for r in entries}),30)

    def test_global_blogger_candidates_are_28_not_four(self):
        self.assertEqual(HISTORY["summary"]["global_candidates"],28)
        self.assertEqual(POLICY["snapshot_counts"]["blogger_targets"],28)
        self.assertEqual(POLICY["snapshot_counts"]["total_current_targets"],31)
        self.assertFalse(POLICY["snapshot_counts"]["global_total_is_currently_active_confirmed"])

    def test_connected_blogger_is_only_four_of_28(self):
        self.assertEqual(HISTORY["summary"]["currently_authenticated_candidates"],4)
        self.assertEqual(HISTORY["summary"]["cross_account_pending"],24)
        self.assertEqual(len(POLICY["blogger"]["current_targets"]),4)
        self.assertIn("SUBSET_ONLY",POLICY["blogger"]["current_targets_connection_scope"])

    def test_all_historical_pending_are_not_labeled_inactive(self):
        pending = [r for r in HISTORY["sites"] if r["current_access_class"]==
                   "HISTORICALLY_VERIFIED_PENDING_CROSS_ACCOUNT_AUTH"]
        self.assertEqual(len(pending),24)
        self.assertFalse(any("INACTIVE" in r["current_access_class"] for r in pending))
        self.assertTrue(all(r["editorial_candidate"] for r in pending))

    def test_twenty_registered_and_eight_need_real_route(self):
        self.assertEqual(HISTORY["summary"]["routed_candidates"],20)
        self.assertEqual(HISTORY["summary"]["without_route"],8)

    def test_c102_evidence_has_real_article_readback_per_identity(self):
        for record in HISTORY["sites"]:
            with self.subTest(record=record["legacy_site_key"]):
                self.assertTrue(record["c102_verified_live_post_id"].isdigit())
                self.assertIn(".blogspot.com/2026/11/",record["c102_verified_live_url"])
                self.assertFalse(record["cms_writes_now_authorized"])

    def test_old_registered_blog_is_pending_other_account_not_inactive(self):
        x = next(r for r in HISTORY["sites"] if r["legacy_site_key"] == "ventiladores")
        route = {"site_key":x["existing_universal_route"],"platform":"blogger",
                 "identifier":x["blog_id"],"publish_enabled":False,
                 "campaign":x["route_campaign_from_repo"]}
        self.assertEqual(g.scope_status(POLICY,route),
                         "PENDING_ACCOUNT_AUTHENTICATION")
        self.assertFalse(g.is_route_in_active_scope(route))

    def test_unrouted_real_history_is_pending_route_without_inventing(self):
        x = next(r for r in HISTORY["sites"] if r["legacy_site_key"] == "cafe")
        self.assertIsNone(x["existing_universal_route"])
        self.assertEqual(g.scope_status(POLICY,None,site_key=x["legacy_site_key"]),
                         "ROUTE_NOT_REGISTERED")

    def test_owner_excluded_air_conditioner_never_enters_editorial_rollout(self):
        x = next(r for r in HISTORY["sites"] if r["legacy_site_key"] == "ar_cond")
        self.assertFalse(x["editorial_candidate"])
        route={"site_key":x["existing_universal_route"],"platform":"blogger",
               "identifier":x["blog_id"],"campaign":"historical",
               "publish_enabled":False}
        self.assertEqual(g.scope_status(POLICY,route),"EXCLUDED_BY_OWNER")

    def test_vida_pet_is_engineering_reference_only_not_blog_target(self):
        x = next(r for r in HISTORY["sites"] if r["legacy_site_key"] == "vida")
        self.assertEqual(x["current_access_class"],
                         "REFERENCE_ONLY_NOT_V31_EDITORIAL_DESTINATION")
        self.assertFalse(x["editorial_candidate"])
        route={"site_key":"blogger_reference_only_not_a_destination",
               "platform":"blogger","identifier":x["blog_id"],
               "campaign":"historical","publish_enabled":False}
        self.assertEqual(g.scope_status(POLICY,route),
                         "REFERENCE_ONLY_NOT_V31_DESTINATION")
        self.assertFalse(g.is_route_in_active_scope(route))

    def test_unknown_blog_is_not_automatically_approved(self):
        route={"site_key":"unknown_blog","platform":"blogger",
               "identifier":"1234567890123456789","campaign":"unknown",
               "publish_enabled":False}
        self.assertEqual(g.scope_status(POLICY,route),"NOT_IN_VERIFIED_ACTIVE_INVENTORY")

    def test_historical_id_cannot_be_spoofed_by_another_site_key(self):
        x = next(r for r in HISTORY["sites"] if r["legacy_site_key"] == "ventiladores")
        route={"site_key":"blogger_wrong_key","platform":"blogger",
               "identifier":x["blog_id"],"campaign":"pretend",
               "publish_enabled":False}
        self.assertEqual(g.scope_status(POLICY,route),"ROUTE_IDENTITY_MISMATCH")

    def test_all_28_blogger_plus_3_wordpress_covered_by_fifty_sims(self):
        cases = g.simulation_cases(POLICY)
        self.assertEqual(len(cases),50)
        seen={x["site_key"] for x in cases}
        for x in HISTORY["sites"]:
            if x["editorial_candidate"]:
                self.assertIn(x["existing_universal_route"] or x["legacy_site_key"],seen)
        for x in POLICY["wordpress"]["current_targets"]:
            self.assertIn(x["site_key"],seen)
        self.assertTrue(all(not x["quality"].get("allow_live",False) for x in cases))

    def test_fifty_simulations_fail_closed_with_all_ids_audited(self):
        report=g.run_simulations(count=50)
        self.assertEqual(report["executed"],50)
        self.assertEqual(report["passed"],50)
        self.assertEqual(report["failed"],0)
        self.assertEqual(report["global_coverage_audit"]["global_candidates"],28)
        self.assertFalse(report["live_authorized"])
        self.assertEqual(report["cms_writes"],0)
        self.assertEqual(report["affiliate_mutations"],0)

    def test_tampered_duplicate_blog_id_denied(self):
        altered=copy.deepcopy(HISTORY)
        altered["sites"][0]["blog_id"]=altered["sites"][1]["blog_id"]
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/"fake.json"
            file.write_text(json.dumps(altered),encoding="utf-8")
            with patch.object(g,"HISTORICAL_PATH",file), self.assertRaises(g.EditorialScopeError):
                g.load_global_inventory(POLICY)

    def test_tampered_global_count_denied(self):
        altered=copy.deepcopy(POLICY)
        altered["snapshot_counts"]["blogger_targets"]=4
        with self.assertRaisesRegex(g.EditorialScopeError,
                                    "global_portfolio_policy_counts_mismatch"):
            g.validate_policy(altered)

    def test_policy_can_enroll_another_verified_route_without_fixed_four_cap(self):
        # Um novo acesso verificável pode promover um candidato sem liberar LIVE.
        candidate=next(r for r in HISTORY["sites"] if r["legacy_site_key"]=="ventiladores")
        pol=copy.deepcopy(POLICY)
        data=copy.deepcopy(HISTORY)
        target=next(r for r in data["sites"] if r["blog_id"]==candidate["blog_id"])
        target["current_access_class"]="AUTHENTICATED_CONNECTED_ACCOUNT_SUBSET"
        data["summary"]["currently_authenticated_candidates"]+=1
        data["summary"]["cross_account_pending"]-=1
        pol["snapshot_counts"]["blogger_connected_verified_subset"]+=1
        pol["snapshot_counts"]["blogger_candidates_pending_current_account_auth"]-=1
        pol["blogger"]["current_targets"].append({
            "site_key":target["existing_universal_route"],
            "id":target["blog_id"],
            "route_registered":True,
            "name":"Scenario: additional verified Blogger"
        })
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/"future_verified.json"
            file.write_text(json.dumps(data),encoding="utf-8")
            with patch.object(g,"HISTORICAL_PATH",file):
                self.assertEqual(
                    g.scope_status(pol,{
                        "site_key":target["existing_universal_route"],
                        "platform":"blogger","identifier":target["blog_id"],
                        "campaign":target["route_campaign_from_repo"],
                        "publish_enabled":False
                    }),"IN_SCOPE")
                self.assertEqual(g.run_simulations(count=50,policy=pol)["passed"],50)

    def test_future_more_than_31_candidates_rotate_without_fake_four_limit(self):
        # Valida rotação real das identidades amostradas, mesmo com dados atuais
        # distintos. A contagem das 50 simulações permanece fixa.
        first=g.run_simulations(count=50,cycle_index=0)
        second=g.run_simulations(count=50,cycle_index=1)
        self.assertEqual(first["passed"],50)
        self.assertEqual(second["passed"],50)
        self.assertEqual(first["distinct_candidate_sites_simulated"],31)
        self.assertEqual(second["distinct_candidate_sites_simulated"],31)
        self.assertNotEqual(first["cycle_index"],second["cycle_index"])
        self.assertEqual(first["global_coverage_audit"]["global_candidates"],28)
        self.assertFalse(second["live_authorized"])

    def test_invalid_simulation_cycle_fails_closed(self):
        for item in (-1,True,"1",1_000_000_001):
            with self.subTest(item=item), self.assertRaises(g.EditorialScopeError):
                g.run_simulations(count=50,cycle_index=item)

    def test_historical_c103_freeze_was_recommendation_not_access_rule(self):
        self.assertIn("C103",POLICY["blogger"]["legacy_inventory_note"])
        self.assertIn("NEVER executed",POLICY["blogger"]["legacy_inventory_note"].replace("NEVER","NEVER"))
        self.assertNotIn("FROZEN",g.run_simulations(count=50)["outcomes"])


if __name__=="__main__":
    unittest.main()
