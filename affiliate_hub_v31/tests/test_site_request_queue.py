"""C37 — cron universal sem temas pré-previstos, orçamento global e zero posts."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.site_request_queue import (
    RequestQueueError,claim_conversion_attempt,load_requests,process_requests,
)

ROUTES={
  "novo_blog_a":{"site_key":"novo_blog_a","platform":"blogger",
    "identifier":"1234567890123456","campaign":"campanha_a",
    "allowed_niches":["cozinha/air_fryers"],"publish_enabled":False},
  "novo_blog_b":{"site_key":"novo_blog_b","platform":"wordpress",
    "identifier":"https://example.test/","campaign":"campanha_b",
    "allowed_niches":["cozinha/air_fryers"],"publish_enabled":False},
}


class FakeStorage:
    def __init__(self,data):
        self.data=data
        self.saved=0
        self.restored=0
    def restore_to(self,path):
        Path(path).write_bytes(self.data)
        self.restored+=1
        return True
    def save_from(self,path):
        self.data=Path(path).read_bytes()
        self.saved+=1
        return {"state_saved":True}


class RequestQueueTests(unittest.TestCase):
    def setUp(self):
        # Fixtures sintéticas do C37 são blogs hipotéticos (não o inventário
        # CMS atual). Mockar apenas escopo ativo aqui; testes C140 validam
        # separadamente o guard real e a exclusão do proprietário.
        check=patch("affiliate_hub_v31.site_request_queue.is_route_in_active_scope",
                    return_value=True)
        check.start()
        self.addCleanup(check.stop)
        td=tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root=Path(td.name)
        self.folder=self.root/"site_requests.d"
        self.folder.mkdir()
        self.db=self.root/"catalog.sqlite3"
        with Catalog(self.db) as cat:
            with cat.db:
                for n in (1,2,3):
                    cat.db.execute("""
                      INSERT INTO products(product_key,shop_id,item_id,title,
                        description,origin_url,image_url,moderation,
                        moderation_reason,first_source,last_seen_utc)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(f"shopee:100:{n}","100",str(n),
                         f"Air Fryer modelo {n}","",
                         f"https://shopee.com.br/product/100/{n}",
                         "https://cf.shopee.com.br/file/image",
                         "eligible","","fixture","2026-11-18T00:00:00Z"))
                    cat.db.execute("""
                      INSERT INTO product_taxonomy(product_key,category,niche,
                        status,reason,version) VALUES(?,?,?,?,?,?)
                    """,(f"shopee:100:{n}","cozinha","air_fryers",
                         "matched","test","test"))
        self.storage=FakeStorage(self.db.read_bytes())

    def _request(self,key,topic="assunto pedido",enabled=True):
        return {
            "site_key":key,"platform":ROUTES[key]["platform"],
            "topic":topic,"articles":3,"enabled":enabled,
        }
    def _write(self,key,**change):
        d=self._request(key)|change
        (self.folder/(key+".json")).write_text(json.dumps(d),encoding="utf-8")

    def test_empty_directory_no_mutations_no_storage(self):
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES):
            r=process_requests(self.storage,directory=self.folder,execute=True)
        self.assertEqual(r["requests_active"],0)
        self.assertEqual(r["shopee_mutation_attempts"],0)
        self.assertEqual(self.storage.restored,0)

    def test_registered_requests_validated_and_disabled_skipped(self):
        self._write("novo_blog_a")
        self._write("novo_blog_b",enabled=False)
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES):
            self.assertEqual(len(load_requests(self.folder)),1)
        self._write("novo_blog_b",platform="pinterest",enabled=True)
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES):
            with self.assertRaises(RequestQueueError):
                load_requests(self.folder)

    def test_invalid_json_and_unknown_site_fail_closed(self):
        (self.folder/"desconhecido.json").write_text(json.dumps({
           "site_key":"desconhecido","platform":"blogger","topic":"mesa",
           "articles":2,"enabled":True}),encoding="utf-8")
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES):
            with self.assertRaises(RequestQueueError):
                load_requests(self.folder)
        (self.folder/"desconhecido.json").unlink()
        self._write("novo_blog_a",articles=25)
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES):
            with self.assertRaises(RequestQueueError):
                load_requests(self.folder)

    def test_c160_independent_commercial_enrollment(self):
        self._write("novo_blog_a",enabled=False,commercial_enabled=True)
        self._write("novo_blog_b",enabled=True,commercial_enabled=False)
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES):
            self.assertEqual([r["site_key"] for r in load_requests(self.folder)],["novo_blog_b"])
            self.assertEqual([r["site_key"] for r in load_requests(self.folder,commercial=True)],["novo_blog_a"])
            self._write("novo_blog_a",enabled=False,commercial_enabled="true")
            with self.assertRaises(RequestQueueError):
                load_requests(self.folder,commercial=True)

    def test_c160_cache_only_route_still_needs_verified_active_scope(self):
        self._write("novo_blog_a",enabled=False,commercial_enabled=True)
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.is_route_in_active_scope",return_value=False):
            with self.assertRaisesRegex(RequestQueueError,"site_outside_verified_active_scope"):
                load_requests(self.folder,commercial=True)

    def test_c160_commercial_only_no_editorial_profile_and_history_skip(self):
        self._write("novo_blog_a",enabled=False,commercial_enabled=True)
        self._write("novo_blog_b",enabled=False,commercial_enabled=True)
        report={"registered_site":True,"can_publish":False,"cached_for_campaign":0,
                "review_queue_count":0,"approved_catalog_candidates":[]}
        calls=[]
        def convert(cat,sku,campaign,app_id,app_secret):
            calls.append((campaign,sku))
            url="https://s.shopee.com.br/"+campaign
            cat.cache_link(sku,campaign,url)
            return url,True
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.preview_site_launch",side_effect=lambda *a,**k: dict(report,approved_catalog_candidates=[])), \
             patch("affiliate_hub_v31.site_request_queue.route_supply_keys",side_effect=lambda *a,**k: iter(["shopee:100:1","shopee:100:2"])), \
             patch("affiliate_hub_v31.site_request_queue.convert_one",side_effect=convert):
            result=process_requests(self.storage,directory=self.folder,budget=2,execute=True,
                app_id="app",app_secret="secret",ordinal=0,
                reserve_conversion=lambda *_:True,
                previously_attempted={("campanha_a","shopee:100:1")})
            self.assertEqual(load_requests(self.folder),[])
        self.assertEqual(calls,[("campanha_a","shopee:100:2"),("campanha_b","shopee:100:1")])
        self.assertEqual(result["commercial_only_requests"],2)
        self.assertEqual(result["converted"],2)
        self.assertEqual(result["publication_calls"],0)
        self.assertTrue(result["r2_snapshot_saved_and_verified"])

    def test_articles_null_is_continuous_but_r2_batch_is_24(self):
        self._write("novo_blog_a", articles=None)
        amounts=[]
        def preview(cat, **kwargs):
            amounts.append(kwargs["max_items"])
            return {"registered_site":True,"can_publish":False,
                    "cached_for_campaign":0,"review_queue_count":0,
                    "approved_catalog_candidates":[]}
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.preview_site_launch",
                   side_effect=preview):
            self.assertIsNone(load_requests(self.folder)[0]["articles"])
            report=process_requests(self.storage,directory=self.folder,
                                    budget=1,execute=False)
        self.assertEqual(amounts,[24])
        self.assertEqual(report["publication_calls"],0)
        self.assertEqual(report["shopee_mutation_attempts"],0)

    def test_invalid_types_do_not_mean_unlimited(self):
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES):
            for bad in (False,True,0,25,"unlimited",-1):
                with self.subTest(bad=bad):
                    self._write("novo_blog_a",articles=bad)
                    with self.assertRaises(RequestQueueError):
                        load_requests(self.folder)

    def test_budget_and_campaign_isolation_in_one_snapshot(self):
        self._write("novo_blog_a")
        self._write("novo_blog_b")
        calls=[]
        def fake_preview(cat,*,site_key,**kwargs):
            key="shopee:100:1" if site_key=="novo_blog_a" else "shopee:100:2"
            return {"registered_site":True,"can_publish":False,
                    "cached_for_campaign":0,"review_queue_count":0,
                    "approved_catalog_candidates":[{
                        "product_key":key,"affiliate_status":"requires_conversion"}]}
        def fake_convert(cat,key,campaign,app_id,app_secret):
            calls.append((key,campaign))
            url="https://s.shopee.com.br/"+campaign
            cat.cache_link(key,campaign,url)
            return url,True
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.preview_site_launch",
                   side_effect=fake_preview), \
             patch("affiliate_hub_v31.site_request_queue.convert_one",
                   side_effect=fake_convert):
            r=process_requests(self.storage,directory=self.folder,budget=2,
                execute=True,app_id="app",app_secret="secret",ordinal=0)
        self.assertEqual(r["converted"],2)
        self.assertEqual(r["shopee_mutation_attempts"],2)
        self.assertEqual(r["publication_calls"],0)
        self.assertEqual(self.storage.saved,1)
        self.assertEqual(set(calls),{
            ("shopee:100:1","campanha_a"),("shopee:100:2","campanha_b")})
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"verified.sqlite3"
            self.storage.restore_to(path)
            with Catalog(path) as cat:
                self.assertIsNone(cat.cached_link("shopee:100:1","campanha_b"))
                self.assertIsNone(cat.cached_link("shopee:100:2","campanha_a"))

    def test_dry_run_and_invalid_budget_never_mutate(self):
        self._write("novo_blog_a")
        def fake_preview(cat,**kwargs):
            return {"registered_site":True,"can_publish":False,
                "cached_for_campaign":0,"review_queue_count":1,
                "approved_catalog_candidates":[{
                    "product_key":"shopee:100:1",
                    "affiliate_status":"requires_conversion"}]}
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.preview_site_launch",
                   side_effect=fake_preview):
            r=process_requests(self.storage,directory=self.folder,budget=1)
            self.assertEqual(r["conversion_candidates"],1)
            self.assertEqual(r["converted"],0)
            self.assertEqual(self.storage.saved,0)
            for bad in (0,4,True,"3"):
                with self.subTest(bad=bad),self.assertRaises(RequestQueueError):
                    process_requests(self.storage,directory=self.folder,budget=bad)

    def test_daily_reservations_share_cap_and_deduplicate_exact_campaign(self):
        schema = Path(__file__).resolve().parents[1] / "migrations" / "c81_shopee_conversion_budget.sql"
        state = sqlite3.connect(self.root / "budget.sqlite3", isolation_level=None)
        self.addCleanup(state.close)
        state.executescript(schema.read_text(encoding="utf-8"))

        def query(statement, args):
            return state.execute(statement, args).fetchall()

        def claim(campaign, sku, day="2026-11-21"):
            return claim_conversion_attempt(query, day_utc=day, campaign=campaign, product_key=sku)

        self.assertTrue(claim("campanha_a", "shopee:100:1"))
        self.assertFalse(claim("campanha_a", "shopee:100:1"))
        self.assertTrue(claim("campanha_b", "shopee:100:1"))
        self.assertTrue(claim("campanha_b", "shopee:100:2"))
        self.assertFalse(claim("campanha_a", "shopee:100:3"))
        # C149: a reserva antiga existe mesmo se o shortlink nao foi
        # persistido no R2. Nunca repetir automaticamente em outro dia.
        self.assertFalse(claim("campanha_a", "shopee:100:1", day="2026-11-22"))
        # Outro SKU e outra campanha continuam independentes.
        self.assertTrue(claim("campanha_a", "shopee:100:3", day="2026-11-22"))
        self.assertTrue(claim("campanha_c", "shopee:100:1", day="2026-11-22"))

    def test_historical_radarwp_conversion_cannot_be_retried_across_days(self):
        schema = Path(__file__).resolve().parents[1] / "migrations" / "c81_shopee_conversion_budget.sql"
        state = sqlite3.connect(self.root / "radarwp-historical.sqlite3", isolation_level=None)
        self.addCleanup(state.close)
        state.executescript(schema.read_text(encoding="utf-8"))
        history = [
            ("2026-11-23", 2, "radarwp", "shopee:1736335904:58267891881"),
            ("2026-11-23", 3, "radarwp", "shopee:889973435:18398298625"),
            ("2026-11-24", 1, "radarwp", "shopee:822103155:58265302556"),
        ]
        state.executemany(
            "INSERT INTO v31_shopee_conversion_attempts(day_utc,slot,campaign,product_key) VALUES(?,?,?,?)",
            history)
        query = lambda sql, args: state.execute(sql, args).fetchall()
        for _, _, campaign, sku in history:
            with self.subTest(product_key=sku):
                self.assertFalse(claim_conversion_attempt(
                    query, day_utc="2026-11-25", campaign=campaign, product_key=sku))
        self.assertEqual(state.execute(
            "SELECT COUNT(*) FROM v31_shopee_conversion_attempts").fetchone()[0], 3)
        self.assertTrue(claim_conversion_attempt(
            query, day_utc="2026-11-25", campaign="outra", product_key=history[0][3]))

    def test_pilot_selects_only_registered_sku_and_honors_denied_reservation(self):
        self._write("novo_blog_a")
        self._write("novo_blog_b")
        report = {"registered_site":True,"can_publish":False,"cached_for_campaign":0,
                  "review_queue_count":0,"approved_catalog_candidates":[
                      {"product_key":f"shopee:100:{n}","affiliate_status":"requires_conversion"}
                      for n in (1,2)]}
        reservations = []

        def deny(campaign, sku):
            reservations.append((campaign, sku))
            return False

        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.preview_site_launch",return_value=report), \
             patch("affiliate_hub_v31.site_request_queue.reserved_pilot_sku",return_value="shopee:100:2"), \
             patch("affiliate_hub_v31.site_request_queue.convert_one") as convert:
            actual = process_requests(self.storage,directory=self.folder,budget=1,execute=True,
                                      app_id="fixture",app_secret="fixture",
                                      pilot_site_key="novo_blog_b",reserve_conversion=deny)
        self.assertEqual(reservations,[("campanha_b","shopee:100:2")])
        self.assertEqual(actual["conversion_reservations_denied"],1)
        self.assertEqual(actual["shopee_mutation_attempts"],0)
        convert.assert_not_called()


    def test_migrated_autodraft_cache_independent_of_fact_source(self):
        self._write("novo_blog_a")
        report = {"registered_site":True,"can_publish":False,
                  "cached_for_campaign":0,"review_queue_count":0,
                  "approved_catalog_candidates":[
                      {"product_key":f"shopee:100:{n}",
                       "affiliate_status":"requires_conversion"}
                      for n in (1,2,3)]}
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.preview_site_launch",
                   return_value=report), \
             patch("affiliate_hub_v31.site_request_queue.autonomous_sites_for_writes",
                   return_value={"novo_blog_a"}), \
             patch("affiliate_hub_v31.site_request_queue.conversion_priority_keys",
                   return_value=iter([])):
            empty=process_requests(self.storage,directory=self.folder,budget=3)
        self.assertEqual(empty["conversion_candidates"],3)
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.preview_site_launch",
                   return_value=report), \
             patch("affiliate_hub_v31.site_request_queue.autonomous_sites_for_writes",
                   return_value={"novo_blog_a"}), \
             patch("affiliate_hub_v31.site_request_queue.conversion_priority_keys",
                   return_value=iter(["shopee:100:2"])):
            one=process_requests(self.storage,directory=self.folder,budget=3)
        self.assertEqual(one["conversion_candidates"],3)
        self.assertEqual(one["shopee_mutation_attempts"],0)
        self.assertEqual(one["publication_calls"],0)
        self.assertEqual(self.storage.saved,0)


    def test_exact_migrated_conversion_needs_cms_auth_and_one_sku(self):
        import hashlib
        self._write("novo_blog_a")
        target="shopee:100:2"
        plan={"registered_site":True,"can_publish":False,
              "cached_for_campaign":0,"review_queue_count":0,
              "approved_catalog_candidates":[]}
        calls=[]
        def convert(cat, sku, campaign, app_id, app_secret):
            calls.append((sku,campaign))
            url="https://s.shopee.com.br/one-verified-link"
            cat.cache_link(sku,campaign,url)
            return url,True
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.preview_site_launch",
                   return_value=plan), \
             patch("affiliate_hub_v31.site_request_queue.autonomous_sites_for_writes",
                   return_value={"novo_blog_a"}), \
             patch("affiliate_hub_v31.site_request_queue.conversion_priority_keys",
                   side_effect=lambda *args: iter([target])), \
             patch("affiliate_hub_v31.site_request_queue.convert_one",
                   side_effect=convert):
            for bad in (
                {"authenticated_cms_keys":None},
                {"authenticated_cms_keys":[hashlib.sha256(target.encode()).hexdigest()]},
                {"authenticated_cms_keys":[],"execute":False},
                {"authenticated_cms_keys":[],"budget":3},
                {"authenticated_cms_keys":[],"target_product_key":"shopee:999:999"},
            ):
                with self.subTest(bad=bad), self.assertRaises(RequestQueueError):
                    args=dict(directory=self.folder, budget=1, execute=True,
                              app_id="app",app_secret="secret",
                              target_site_key="novo_blog_a",
                              target_product_key=target,
                              authenticated_cms_keys=[],
                              reserve_conversion=lambda *_: True)
                    args.update(bad)
                    process_requests(self.storage,**args)
            self.assertEqual(calls,[])
            out=process_requests(self.storage,directory=self.folder,budget=1,
                execute=True,app_id="app",app_secret="secret",
                target_site_key="novo_blog_a",target_product_key=target,
                authenticated_cms_keys=[], reserve_conversion=lambda *_: True)
        self.assertEqual(out["converted"],1)
        self.assertEqual(out["shopee_mutation_attempts"],1)
        self.assertEqual(calls,[(target,"campanha_a")])
        self.assertEqual(self.storage.saved,1)

    def test_exact_target_fails_on_wrong_supplier_or_disabled_migration(self):
        self._write("novo_blog_a")
        plan={"registered_site":True,"can_publish":False,
              "cached_for_campaign":0,"review_queue_count":0,
              "approved_catalog_candidates":[]}
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.preview_site_launch",
                   return_value=plan), \
             patch("affiliate_hub_v31.site_request_queue.autonomous_sites_for_writes",
                   return_value=set()):
            with self.assertRaisesRegex(RequestQueueError,"migration_guard_failed"):
                process_requests(self.storage,directory=self.folder,budget=1,
                   execute=True,target_site_key="novo_blog_a",
                   target_product_key="shopee:100:2",authenticated_cms_keys=[])
        with patch("affiliate_hub_v31.site_request_queue.sites",return_value=ROUTES), \
             patch("affiliate_hub_v31.site_request_queue.preview_site_launch",
                   return_value=plan), \
             patch("affiliate_hub_v31.site_request_queue.autonomous_sites_for_writes",
                   return_value={"novo_blog_a"}), \
             patch("affiliate_hub_v31.site_request_queue.conversion_priority_keys",
                   return_value=iter([])):
            with self.assertRaisesRegex(RequestQueueError,"target_offer_not_in_verified_supply"):
                process_requests(self.storage,directory=self.folder,budget=1,
                   execute=True,target_site_key="novo_blog_a",
                   target_product_key="shopee:100:2",authenticated_cms_keys=[])


if __name__=="__main__":
    unittest.main()
