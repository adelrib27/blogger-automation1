"""C148 — Radar é piloto primário, nunca nicho/limite exclusivo do V31."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31 import pilot_homologation as m
from affiliate_hub_v31.routing import sites


class FakeR2:
    def __init__(self, original: bytes, *, fail=False):
        self.original=original
        self.fail=fail
        self.writes=0
        self.reads=0

    def restore_to(self, path):
        self.reads+=1
        if self.fail: return False
        Path(path).write_bytes(self.original)
        return True


class UniversalPilotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="v31-c148-")
        self.addCleanup(self.temp.cleanup)
        self.db_path=Path(self.temp.name)/"offline.sqlite3"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE synthetic_fixture(id INTEGER PRIMARY KEY)")
            conn.execute("CREATE TABLE affiliate_links(product_key TEXT, campaign TEXT)")
            conn.execute("INSERT INTO affiliate_links VALUES (?,?)", ("sku1","radarwp"))
        self.storage=FakeR2(self.db_path.read_bytes())
        self.routes=sites()
        self.request_modes={
            "blogger_moveis_para_cada_canto":"ENABLED",
            "wordpress_casa_decoracao":"ENABLED",
            "wordpress_radartechbr":"STAGED_DISABLED",
        }
        self.profiles={
            "blogger_moveis_para_cada_canto":{"home":"https://moveis.example/","offers":{"a":{}}},
            "wordpress_casa_decoracao":{"home":self.routes["wordpress_casa_decoracao"]["identifier"],
                                        "offers":{"b":{}}},
        }

    def plan(self, **kw):
        args=dict(primary="wordpress_radartechbr",routes=self.routes,
                  request_modes=self.request_modes,reviewer_profiles=self.profiles)
        args.update(kw)
        return m.plan(**args)

    def real(self, **kw):
        def query(sql,params):
            if "v31_ready_jobs" in sql:
                return [{"status":"USED","total":1}]
            return [{"total":0}]
        args=dict(primary="wordpress_radartechbr",routes=self.routes,
                  request_modes=self.request_modes,reviewer_profiles=self.profiles,
                  query=query,storage=self.storage,
                  history_reader=lambda site:{"site_key":site,"keys":[],"slugs":[],"prose":[],"count":5})
        inspector=kw.pop("sample_provider", None)
        args.update(kw)
        if inspector is None:
            inspector=lambda catalog,route,**kwargs:{"catalog_candidates":2,
                                           "cached_exact_campaign":1,
                                           "items":[]}
        with patch.object(m,"inspect_campaign_cache",side_effect=inspector), \
             patch.object(m,"verify_database",return_value=None):
            return m.live_readonly(**args)

    def test_primary_radar_first_and_seven_current_sites(self):
        p=self.plan()
        self.assertEqual(p["primary"],"wordpress_radartechbr")
        self.assertEqual(p["active_sites"],7)
        self.assertEqual(p["platforms"],{"blogger":4,"wordpress":3})
        self.assertEqual(p["reports"][0]["site_key"],"wordpress_radartechbr")
        self.assertTrue(p["reports"][0]["is_primary"])

    def test_radar_explicitly_disabled_before_safe_e2e(self):
        p=self.plan()
        radar=p["reports"][0]
        self.assertEqual(radar["request_state"],"STAGED_DISABLED")
        self.assertEqual(radar["blocker"],"PILOT_REQUEST_DISABLED")
        self.assertFalse(radar["can_write_draft"])
        self.assertFalse(radar["can_publish_live"])

    def test_every_registered_site_still_covered(self):
        p=self.plan()
        self.assertEqual({x["site_key"] for x in p["reports"]},
                         {"wordpress_radartechbr","wordpress_casa_decoracao",
                          "wordpress_oficina_garagem","blogger_moveis_para_cada_canto",
                          "blogger_limpeza","blogger_estilo","blogger_cozinha_sem_complicacao"})

    def test_bloggers_and_wordpress_have_same_safety_guards(self):
        for item in self.plan()["reports"]:
            self.assertFalse(item["can_write_draft"])
            self.assertFalse(item["can_publish_live"])

    def test_can_select_another_existing_blogger_primary(self):
        p=self.plan(primary="blogger_moveis_para_cada_canto")
        self.assertEqual(p["reports"][0]["site_key"],"blogger_moveis_para_cada_canto")
        self.assertEqual(p["active_sites"],7)

    def test_can_select_another_wordpress_primary(self):
        p=self.plan(primary="wordpress_oficina_garagem")
        self.assertEqual(p["reports"][0]["platform"],"wordpress")
        self.assertEqual(p["active_sites"],7)

    def test_missing_nonregistered_primary_fails_closed(self):
        with self.assertRaisesRegex(m.PilotAuditError,"pilot_primary_not_in_active_scope"):
            self.plan(primary="site_missing")

    def test_excluded_site_never_enters_homologation(self):
        p=self.plan()
        self.assertNotIn("blogger_ar_condicionado_sem_duvidas",
                         [x["site_key"] for x in p["reports"]])

    def test_zero_mutations_as_part_of_config_plan(self):
        p=self.plan()
        for name in ("cms_writes","d1_writes","r2_writes","affiliate_mutations"):
            self.assertEqual(p[name],0)
        self.assertFalse(p["automatic_live_authorized"])

    def test_ready_profile_not_equal_to_draft_homologation(self):
        p=self.plan()
        casa=next(x for x in p["reports"] if x["site_key"]=="wordpress_casa_decoracao")
        self.assertTrue(casa["configured_for_independent_review"])
        self.assertEqual(casa["blocker"],"E2E_DRAFT_NOT_PROVEN_BY_READONLY")
        self.assertFalse(casa["can_write_draft"])

    def test_enabling_request_without_evidence_still_blocks(self):
        modes=dict(self.request_modes,wordpress_radartechbr="ENABLED")
        radar=self.plan(request_modes=modes)["reports"][0]
        self.assertEqual(radar["blocker"],"VERIFIED_SOURCE_PROFILE_MISSING")

    def test_configured_profile_wrong_wp_identity_blocks(self):
        modes=dict(self.request_modes,wordpress_radartechbr="ENABLED")
        profiles=dict(self.profiles,wordpress_radartechbr={"offers":{"key":{}},"home":"https://wrong.example/"})
        radar=self.plan(request_modes=modes,reviewer_profiles=profiles)["reports"][0]
        self.assertEqual(radar["blocker"],"REVIEW_PROFILE_IDENTITY_MISMATCH")

    def test_future_blog_enrollment_is_dynamic(self):
        newkey="wordpress_blog_futuro"
        routes={k:v for k,v in self.routes.items() if m.is_route_in_active_scope(v)}
        routes[newkey]=dict(self.routes["wordpress_radartechbr"],
                            site_key=newkey,identifier="https://novo.example/",
                            campaign="novafiliacao")
        with patch.object(m,"is_route_in_active_scope",return_value=True):
            p=self.plan(routes=routes)
        self.assertEqual(p["active_sites"],8)
        self.assertIn(newkey,[x["site_key"] for x in p["reports"]])
        self.assertEqual(p["reports"][0]["site_key"],"wordpress_radartechbr")

    def test_future_blogger_enrollment_is_dynamic(self):
        newkey="blogger_blog_futuro"
        routes={k:v for k,v in self.routes.items() if m.is_route_in_active_scope(v)}
        routes[newkey]=dict(self.routes["blogger_moveis_para_cada_canto"],
                            site_key=newkey,identifier="919191919191919",
                            campaign="novoblogger")
        with patch.object(m,"is_route_in_active_scope",return_value=True):
            p=self.plan(routes=routes)
        self.assertIn(newkey,[x["site_key"] for x in p["reports"]])

    def test_invalid_primary_fails_before_any_network(self):
        with self.assertRaisesRegex(m.PilotAuditError,"pilot_inputs_invalid"):
            self.plan(primary="https://host/token?secret=abc")

    def test_real_readonly_d1_r2_cms_success_is_not_post_proof(self):
        result=self.real()
        self.assertEqual(result["status"],"READ_ONLY_SOURCES_CONFIRMED_NOT_DRAFT_AUTHORIZED")
        self.assertEqual(result["reports"][0]["cms_v31_prefixed_slugs_detected"],5)
        self.assertEqual(result["reports"][0]["d1_used_jobs"],1)
        self.assertEqual(result["reports"][0]["cached_links_exact_campaign_sample"],1)
        self.assertEqual(result["new_drafts_proven"],0)
        self.assertEqual(self.storage.writes,0)

    def test_c179_audit_accepts_expanded_budget_but_rejects_over_cap(self):
        from affiliate_hub_v31.site_request_queue import MAX_BUDGET
        for count, expected in ((MAX_BUDGET, "READ_ONLY_CONFIRMED"),
                                (MAX_BUDGET + 1, "BLOCKED_D1_SELECT")):
            def query(statement, params):
                if "v31_shopee_conversion_attempts" in statement:
                    return [{"total": count}]
                return [{"status": "USED", "total": 1}]
            self.assertEqual(self.real(query=query)["checks"]["d1"], expected)

    def test_real_d1_failure_still_zero_writes(self):
        result=self.real(query=lambda a,b: (_ for _ in ()).throw(RuntimeError("token")))
        self.assertEqual(result["checks"]["d1"],"BLOCKED_D1_SELECT")
        self.assertEqual(result["status"],"READ_ONLY_SOURCE_CHECK_INCOMPLETE")
        self.assertEqual(result["d1_writes"],0)

    def test_real_r2_failure_still_zero_writes(self):
        store=FakeR2(self.db_path.read_bytes(),fail=True)
        result=self.real(storage=store)
        self.assertEqual(result["checks"]["r2"],"BLOCKED_R2_READ")
        self.assertEqual(result["r2_writes"],0)

    def test_missing_github_site_credentials_diagnosed_without_exposing_secret(self):
        from affiliate_hub_v31 import automatic_wordpress_drafts as wp
        fake_cms={"site_key":"wordpress_radartechbr","keys":[],"slugs":[],
                  "prose":[],"count":1}
        with patch.object(wp,"credentials_for",
                          side_effect=ValueError("private credential secret")), \
             patch.object(m,"read_draft_history",return_value=fake_cms):
            result=self.real(history_reader=None)
        self.assertEqual(result["checks"]["cms"],"BLOCKED_CMS_SITE_CREDENTIALS_UNAVAILABLE")
        self.assertNotIn("private credential secret",json.dumps(result))
        self.assertEqual(result["cms_writes"],0)

    def test_present_github_site_credentials_allows_authenticated_read(self):
        from affiliate_hub_v31 import automatic_wordpress_drafts as wp
        fake_cms={"site_key":"wordpress_radartechbr","keys":[],"slugs":[],
                  "prose":[],"count":1}
        with patch.object(wp,"credentials_for",return_value=("masked","masked")), \
             patch.object(m,"read_draft_history",return_value=fake_cms):
            result=self.real(history_reader=None)
        self.assertEqual(result["checks"]["cms"],"AUTHENTICATED_GET_CONFIRMED")
        self.assertEqual(result["new_drafts_proven"],0)

    def test_real_cms_auth_failure_still_zero_writes(self):
        result=self.real(history_reader=lambda site:(_ for _ in ()).throw(ValueError("secret")))
        self.assertEqual(result["checks"]["cms"],"BLOCKED_AUTHENTICATED_CMS_GET")
        self.assertEqual(result["cms_writes"],0)

    def test_bogus_d1_status_rejected(self):
        with self.assertRaisesRegex(m.PilotAuditError,"pilot_d1_job_counts_untrusted"):
            m._valid_d1_counts([{"status":"LIVE","total":20}])

    def test_duplicate_status_rejected(self):
        with self.assertRaisesRegex(m.PilotAuditError,"pilot_d1_duplicate_job_status"):
            m._valid_d1_counts([{"status":"USED","total":1},{"status":"USED","total":1}])

    def test_c151_primary_sample_reports_exact_sku_not_draft_authorization(self):
        sku="shopee:822103155:58265302556"
        def sample(cat,route):
            return {"catalog_candidates":1,"cached_exact_campaign":0,
                    "items":[{"product_key":sku,"title":"Ar Condicionado LG Dual Inverter Compact 12000",
                              "cached_for_exact_campaign":False}]}
        result=self.real(sample_provider=sample)
        radar=result["reports"][0]
        self.assertEqual(radar["primary_candidate_sample"][0]["product_key"],sku)
        self.assertFalse(radar["primary_candidate_sample"][0]["cms_legacy_duplicate_checked"])
        self.assertFalse(radar["primary_candidate_sample"][0]["eligible_for_draft_write"])
        self.assertNotIn("cms_history_records_scanned",radar)
        self.assertEqual(radar["cms_legacy_duplicate_crosscheck"],"NOT_PERFORMED")
        self.assertFalse(result["automatic_live_authorized"])

    def test_c151_sample_invalid_sku_blocks_r2_without_leaking_content(self):
        bad=lambda cat,route:{"catalog_candidates":1,"cached_exact_campaign":0,
             "items":[{"product_key":"https://secret.example/abc",
                       "title":"Produto fake com URL", "cached_for_exact_campaign":False}]}
        result=self.real(sample_provider=bad)
        self.assertEqual(result["checks"]["r2"],"BLOCKED_R2_READ")
        self.assertNotIn("secret.example",json.dumps(result))
        self.assertEqual(result["cms_writes"],0)

    def test_c151_primary_title_control_chars_sanitized(self):
        provider=lambda cat,route:{"catalog_candidates":1,"cached_exact_campaign":0,
             "items":[{"product_key":"shopee:123:456",
                       "title":"Produto para teste\\ncom controle\\tde log",
                       "cached_for_exact_campaign":False}]}
        result=self.real(sample_provider=provider)
        item=result["reports"][0]["primary_candidate_sample"][0]
        self.assertNotIn("\\n",item["title"])
        self.assertNotIn("\\t",item["title"])
        self.assertFalse(item["manufacturer_facts_verified"])

    def test_c151_primary_sample_never_implies_legacy_duplicate_cleared(self):
        out=self.real()
        radar=out["reports"][0]
        self.assertEqual(radar["cms_v31_prefixed_slugs_detected"],5)
        self.assertEqual(radar["cms_legacy_duplicate_crosscheck"],"NOT_PERFORMED")
        self.assertFalse(radar["can_write_draft"])

    def test_untrusted_d1_count_rejected(self):
        with self.assertRaisesRegex(m.PilotAuditError,"pilot_d1_job_counts_untrusted"):
            m._valid_d1_counts([{"status":"USED","total":"1"}])

    def test_readonly_result_never_includes_affiliate_urls(self):
        output=json.dumps(self.real(),sort_keys=True)
        self.assertNotIn("https://s.shopee.com.br/",output)
        self.assertNotIn("app_secret",output)

    def test_c159_all_cms_reads_every_active_site_with_one_snapshot(self):
        seen=[]
        def history(site):
            seen.append(site)
            return {"site_key":site,"keys":[],"slugs":[],"prose":[],"count":5}
        result=self.real(all_cms=True,history_reader=history)
        self.assertEqual(len(seen),7)
        self.assertEqual(len(set(seen)),7)
        self.assertEqual(self.storage.reads,1)
        self.assertEqual(result["reports"][0]["cached_links_exact_campaign_total"],1)
        self.assertTrue(all(x["cms_check"]=="AUTHENTICATED_GET_CONFIRMED" for x in result["reports"]))
        self.assertFalse(result["automatic_live_authorized"])

    def test_c159_failure_for_one_site_does_not_hide_others(self):
        def history(site):
            if site=="blogger_estilo":
                raise ValueError("secret")
            return {"site_key":site,"keys":[],"slugs":[],"prose":[],"count":5}
        result=self.real(all_cms=True,history_reader=history)
        self.assertEqual(result["checks"]["cms"],"BLOCKED_ONE_OR_MORE_CMS_GET")
        self.assertEqual(result["status"],"READ_ONLY_SOURCE_CHECK_INCOMPLETE")
        self.assertEqual(sum(x["cms_check"]=="AUTHENTICATED_GET_CONFIRMED" for x in result["reports"]),6)
        self.assertNotIn("secret",json.dumps(result))
        self.assertEqual(result["cms_writes"],0)

    def test_sql_queries_are_select_only(self):
        used=[]
        def query(statement, params):
            used.append(statement.strip().upper())
            return [{"status":"USED","total":1}] if "v31_ready_jobs" in statement else [{"total":0}]
        self.real(query=query)
        self.assertEqual(len(used),14)
        self.assertTrue(all(x.startswith("SELECT ") for x in used))

    def test_no_active_scope_enrollment_by_dropping_disabled_request(self):
        modes={key:val for key,val in self.request_modes.items()
               if key!="wordpress_radartechbr"}
        radar=self.plan(request_modes=modes)["reports"][0]
        self.assertEqual(radar["blocker"],"NO_EDITORIAL_REQUEST")

    def test_all_modes_are_only_informational(self):
        for name in ("ENABLED","STAGED_DISABLED","MISSING"):
            with self.subTest(name=name):
                modes=dict(self.request_modes,wordpress_radartechbr=name)
                self.assertFalse(self.plan(request_modes=modes)["reports"][0]["can_write_draft"])


if __name__=="__main__":
    unittest.main()
