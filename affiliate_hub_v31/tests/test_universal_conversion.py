"""Conversão Shopee universal por tema: somente rota real, campanha correta."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.universal_conversion import (
    UniversalConversionError,convert_for_registered_blog,
)

ROUTE={"site_key":"novo_site_real","platform":"blogger",
       "identifier":"1234567890123456","campaign":"nova_campanha",
       "allowed_niches":["cozinha/air_fryers"],"publish_enabled":False}


class FakeStorage:
    def __init__(self,data):
        self.data=data
        self.writes=0
    def restore_to(self,path):
        Path(path).write_bytes(self.data)
        return True
    def save_from(self,path):
        self.data=Path(path).read_bytes()
        self.writes+=1
        return {"state_saved":True,"retention_pending":False}


class UniversalConverterTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        db=Path(temp.name)/"catalog.sqlite3"
        with Catalog(db) as cat:
            with cat.db:
                for shop,item,mod,tax in (
                    ("11","101","eligible","matched"),
                    ("12","102","review","review"),
                ):
                    key=f"shopee:{shop}:{item}"
                    cat.db.execute("""
                      INSERT INTO products(product_key,shop_id,item_id,
                       title,description,origin_url,image_url,moderation,
                       moderation_reason,first_source,last_seen_utc)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,shop,item,"Air Fryer 5 litros","",
                         f"https://shopee.com.br/product/{shop}/{item}",
                         "https://cf.shopee.com.br/file/p",mod,"",
                         "test","2026-11-18T00:00:00Z"))
                    cat.db.execute("""
                      INSERT INTO product_taxonomy
                      (product_key,category,niche,status,reason,version)
                      VALUES(?,?,?,?,?,?)
                    """,(key,"cozinha","air_fryers",tax,"test","test"))
            cat.cache_link("shopee:11:101","campanha_antiga",
                           "https://s.shopee.com.br/old-campaign-only")
        self.storage=FakeStorage(db.read_bytes())

    def _plan(self,*args,**kwargs):
        return {"approved_catalog_candidates":[
            {"product_key":"shopee:11:101",
             "affiliate_status":"requires_conversion"},
            {"product_key":"shopee:12:102",
             "affiliate_status":"requires_conversion"}]}

    def test_dry_run_requires_real_route_and_never_copies_other_campaign(self):
        with patch("affiliate_hub_v31.universal_conversion.sites",
                   return_value={"novo_site_real":ROUTE}), \
             patch("affiliate_hub_v31.universal_conversion.preview_site_launch",
                   side_effect=self._plan):
            result=convert_for_registered_blog(
                self.storage,site_key="novo_site_real",
                topic="air fryer 5 litros",budget=2)
        self.assertEqual(result["candidate_count"],1)
        self.assertEqual(result["converted"],0)
        self.assertEqual(result["shopee_mutation_attempts"],0)
        self.assertEqual(self.storage.writes,0)
        self.assertTrue(result["no_cross_campaign_links"])

    def test_execute_converts_only_approved_into_correct_real_campaign(self):
        called=[]
        def fake_convert(cat,key,campaign,app_id,app_secret):
            called.append((key,campaign))
            cat.cache_link(key,campaign,
                           "https://s.shopee.com.br/new-campaign-real")
            return "https://s.shopee.com.br/new-campaign-real",True
        with patch("affiliate_hub_v31.universal_conversion.sites",
                   return_value={"novo_site_real":ROUTE}), \
             patch("affiliate_hub_v31.universal_conversion.preview_site_launch",
                   side_effect=self._plan), \
             patch("affiliate_hub_v31.universal_conversion.convert_one",
                   side_effect=fake_convert):
            result=convert_for_registered_blog(
                self.storage,site_key="novo_site_real",
                topic="air fryer",budget=3,execute=True,
                app_id="123",app_secret="new-secret",reserve_conversion=lambda *_: True)
        self.assertEqual(called,[("shopee:11:101","nova_campanha")])
        self.assertEqual(result["converted"],1)
        self.assertTrue(result["r2_snapshot_saved_and_verified"])
        self.assertEqual(self.storage.writes,1)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"verified.sqlite3"
            self.storage.restore_to(path)
            with Catalog(path) as cat:
                self.assertEqual(cat.cached_link("shopee:11:101",
                    "nova_campanha"),"https://s.shopee.com.br/new-campaign-real")
                self.assertEqual(cat.cached_link("shopee:11:101",
                    "campanha_antiga"),
                    "https://s.shopee.com.br/old-campaign-only")
                self.assertIsNone(cat.cached_link("shopee:12:102",
                    "nova_campanha"))

    def test_unknown_site_cannot_invent_campaign(self):
        with patch("affiliate_hub_v31.universal_conversion.sites",
                   return_value={}):
            with self.assertRaises(UniversalConversionError):
                convert_for_registered_blog(self.storage,
                    site_key="futuro_nao_registrado",topic="air fryer")
        self.assertEqual(self.storage.writes,0)

    def test_mutation_budget_rejects_more_than_ten_and_no_topic(self):
        with patch("affiliate_hub_v31.universal_conversion.sites",
                   return_value={"novo_site_real":ROUTE}):
            for bad in (0,11,-1,True,"3"):
                with self.subTest(bad=bad),self.assertRaises(UniversalConversionError):
                    convert_for_registered_blog(self.storage,
                        site_key="novo_site_real",topic="air fryer",budget=bad)
            with self.assertRaises(UniversalConversionError):
                convert_for_registered_blog(self.storage,
                    site_key="novo_site_real",topic="  ")
        self.assertEqual(self.storage.writes,0)

    def test_shared_reservation_denial_never_calls_shopee(self):
        with patch("affiliate_hub_v31.universal_conversion.sites", return_value={"novo_site_real":ROUTE}), \
             patch("affiliate_hub_v31.universal_conversion.preview_site_launch", side_effect=self._plan), \
             patch("affiliate_hub_v31.universal_conversion.convert_one") as call:
            result=convert_for_registered_blog(self.storage,site_key="novo_site_real",topic="air fryer",
                execute=True,app_id="fixture",app_secret="fixture",reserve_conversion=lambda *_:False)
            call.assert_not_called()
            self.assertEqual(result["conversion_reservations_denied"],1)
            self.assertEqual(result["shopee_mutation_attempts"],0)
            self.assertEqual(self.storage.writes,0)

    def test_execute_without_shopee_key_fails_without_R2_write(self):
        with self.assertRaises(UniversalConversionError):
            convert_for_registered_blog(
                self.storage,site_key="novo_site_real",topic="air fryer",
                execute=True)
        self.assertEqual(self.storage.writes,0)


if __name__=="__main__":
    unittest.main()
