"""C37 — cron universal sem temas pré-previstos, orçamento global e zero posts."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.site_request_queue import (
    RequestQueueError,load_requests,process_requests,
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


if __name__=="__main__":
    unittest.main()
