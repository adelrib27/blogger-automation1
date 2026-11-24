"""C143: 24 deleted Blogger identities are denylisted, never PENDING.

Offline, no network, no external publication or deletion.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31 import editorial_scope_validation as gate, routing
from src import blogger_policy_repo_audit as old_audit

POLICY=gate.load_policy()
TOMBSTONES=gate.load_tombstones(POLICY)


class DeletedTwentyFourBloggerSafetyTests(unittest.TestCase):
    def test_count_and_unique_ids_are_24(self):
        rows=TOMBSTONES["deleted_blogs"]
        self.assertEqual(len(rows),24)
        self.assertEqual(len({x["blog_id"] for x in rows}),24)
        self.assertTrue(all(x["deleted_by_owner"] and not x["eligible_for_editorial"]
                            and not x["allow_reenroll"] for x in rows))

    def test_the_24_are_not_pending_candidates(self):
        self.assertEqual(POLICY["blogger"]["deleted_by_owner_count"],24)
        self.assertEqual(POLICY["snapshot_counts"]["deleted_blogger_pending_authentication"],0)
        self.assertEqual(POLICY["snapshot_counts"]["blogger_targets"],4)
        self.assertNotIn("historical_candidates_pending_authentication", POLICY["blogger"])

    def test_current_scope_four_blogger_three_wordpress(self):
        self.assertEqual(len(POLICY["blogger"]["current_targets"]),4)
        self.assertEqual(len(POLICY["wordpress"]["current_targets"]),3)
        self.assertEqual(POLICY["snapshot_counts"]["total_current_targets"],7)
        self.assertTrue(POLICY["snapshot_counts"]["future_blogs_allowed_after_verification"])

    def test_all_24_blogger_ids_fully_blocked(self):
        for tomb in TOMBSTONES["deleted_blogs"]:
            with self.subTest(key=tomb["legacy_site_key"]):
                route={"site_key":tomb["old_route_key"] or tomb["legacy_site_key"],
                       "platform":"blogger","identifier":tomb["blog_id"],
                       "campaign":"legacy","publish_enabled":False}
                self.assertEqual(gate.scope_status(POLICY,route),"DELETED_BY_OWNER")
                self.assertEqual(gate.scope_status(POLICY,None,
                                 site_key=tomb["legacy_site_key"]),"DELETED_BY_OWNER")

    def test_deleted_id_cannot_spoof_active_site_key(self):
        valid=POLICY["blogger"]["current_targets"][0]
        dead=TOMBSTONES["deleted_blogs"][0]
        route={"site_key":valid["site_key"],"platform":"blogger",
               "identifier":dead["blog_id"],"campaign":"valid","publish_enabled":False}
        self.assertEqual(gate.scope_status(POLICY,route),"DELETED_BY_OWNER")

    def test_deleted_key_cannot_spoof_active_identifier(self):
        valid=POLICY["blogger"]["current_targets"][0]
        dead=TOMBSTONES["deleted_blogs"][0]
        route={"site_key":dead["old_route_key"] or dead["legacy_site_key"],
               "platform":"blogger","identifier":valid["id"],
               "campaign":"valid","publish_enabled":False}
        self.assertEqual(gate.scope_status(POLICY,route),"DELETED_BY_OWNER")

    def test_deleted_registry_keys_not_in_active_routes(self):
        routes=routing.sites()
        deadids={t["blog_id"] for t in TOMBSTONES["deleted_blogs"]}
        oldkeys={t[k] for t in TOMBSTONES["deleted_blogs"]
                 for k in ("legacy_site_key","old_route_key") if t[k]}
        self.assertFalse(deadids & {x["identifier"] for x in routes.values()})
        self.assertFalse(oldkeys & set(routes))
        self.assertEqual(sum(x["platform"]=="blogger" for x in routes.values()),5)  # 4+Ar excluded
        self.assertEqual(sum(x["platform"]=="wordpress" for x in routes.values()),3)

    def test_new_deleted_route_reintroduction_fails_closed_at_registry(self):
        original=json.loads(routing.ROUTES_PATH.read_text(encoding="utf-8"))
        dead=TOMBSTONES["deleted_blogs"][0]
        original["sites"].append({"site_key":"blogger_fake_future",
                                  "platform":"blogger","identifier":dead["blog_id"],
                                  "campaign":"fake","allowed_niches":["cozinha/air_fryers"],
                                  "publish_enabled":False})
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"routes.json"
            path.write_text(json.dumps(original),encoding="utf-8")
            with patch.object(routing,"ROUTES_PATH",path):
                routing.sites.cache_clear()
                with self.assertRaisesRegex(ValueError,"blogger_deleted_by_owner_route_forbidden"):
                    routing.sites()
        routing.sites.cache_clear()

    def test_new_future_non_deleted_blog_may_be_registered_but_not_published(self):
        new={"site_key":"blogger_new_genuine_blog",
             "platform":"blogger","identifier":"999999999999111111",
             "campaign":"newgenuine","allowed_niches":["cozinha/air_fryers"],
             "publish_enabled":False}
        original=json.loads(routing.ROUTES_PATH.read_text(encoding="utf-8"))
        original["sites"].append(new)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"routes.json"
            path.write_text(json.dumps(original),encoding="utf-8")
            with patch.object(routing,"ROUTES_PATH",path):
                routing.sites.cache_clear()
                self.assertIn(new["site_key"],routing.sites())
                self.assertEqual(gate.scope_status(POLICY,new),
                                 "NOT_IN_CURRENT_VERIFIED_ACTIVE_INVENTORY")
        routing.sites.cache_clear()

    def test_50_simulations_include_all_24_deleted_without_remote_calls(self):
        cases=gate.simulation_cases(POLICY)
        self.assertEqual(len(cases),50)
        dead={z["blog_id"] for z in TOMBSTONES["deleted_blogs"]}
        checked={x["route"]["identifier"] for x in cases
                 if x["expected"]=="DELETED_BY_OWNER"}
        self.assertEqual(checked,dead)
        report=gate.run_simulations(count=50)
        self.assertEqual(report["passed"],50)
        self.assertEqual(report["outcomes"]["DELETED_BY_OWNER"],24)
        self.assertEqual(report["global_coverage_audit"]["cross_account_pending"],0)
        self.assertEqual(report["current_active_sites"],7)
        self.assertFalse(report["live_authorized"])
        self.assertEqual(report["cms_writes"],0)

    def test_two_simulation_cycles_keep_dead_all_blocked(self):
        for idx in (0,1,99):
            with self.subTest(cycle=idx):
                r=gate.run_simulations(count=50,cycle_index=idx)
                self.assertEqual(r["passed"],50)
                self.assertEqual(r["deleted_blogger_blocked"],24)
                self.assertEqual(r["outcomes"]["DELETED_BY_OWNER"],24)

    def test_tampering_with_tombstones_or_allow_reenroll_is_rejected(self):
        mutated=copy.deepcopy(TOMBSTONES)
        mutated["deleted_blogs"][0]["allow_reenroll"]=True
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"bad.json"
            path.write_text(json.dumps(mutated),encoding="utf-8")
            with patch.object(gate,"TOMBSTONES_PATH",path):
                with self.assertRaises(gate.EditorialScopeError):
                    gate.load_tombstones(POLICY)

    def test_c141_manifest_explicitly_deprecated(self):
        path=gate.POLICY_PATH.with_name("EDITORIAL_GLOBAL_PORTFOLIO_C141.json")
        doc=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(doc["status"],"SUPERSEDED_DO_NOT_USE_FOR_ROUTES_OR_EDITORIAL")
        self.assertNotIn("sites",doc)
        self.assertNotIn("articles",doc)

    def test_minimal_tombstones_do_not_reexpose_old_post_and_affiliate_details(self):
        for row in TOMBSTONES["deleted_blogs"]:
            self.assertEqual(set(row),{"blog_id","legacy_site_key","old_route_key",
                                       "deleted_by_owner","eligible_for_editorial","allow_reenroll"})
        self.assertNotIn("c102_verified_live_url",json.dumps(TOMBSTONES))
        self.assertNotIn("affiliate",json.dumps(TOMBSTONES).lower())

    def test_all_retired_store_workflows_have_no_schedule_and_job_disabled(self):
        self.assertEqual(len(old_audit.DELETED_BLOGGER_WRITER_WORKFLOWS),19)
        old_audit.audit_deleted_blogger_writers()

    def test_active_wordpress_and_blogger_writers_are_not_blocked(self):
        for p in ("cozinha_sem_complicacao_store_autonomous.yml",
                  "estilo_dia_a_dia_store_autonomous.yml",
                  "limpeza_inteligente_store_autonomous.yml"):
            text=(old_audit.ROOT/".github/workflows"/p).read_text(encoding="utf-8")
            self.assertNotIn("V31_C143_OWNER_DELETED_JOB_DISABLED",text)
        policy=json.loads((gate.POLICY_PATH.with_name("autonomous_live_policy.json"))
                          .read_text(encoding="utf-8"))
        self.assertEqual(policy["activation"],"pending_policy_approval")

    def test_retired_c141_run_cannot_be_reused_as_authorization(self):
        self.assertNotIn("historical_inventory_manifest",POLICY["blogger"])
        self.assertNotIn("C141",gate.POLICY_PATH.read_text(encoding="utf-8")[:250])
        self.assertFalse(POLICY["rollout"]["global_third_party_writes_now_authorized"])


if __name__=="__main__":
    unittest.main()
