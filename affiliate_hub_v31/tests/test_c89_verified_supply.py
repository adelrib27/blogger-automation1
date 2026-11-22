"""C89: approved source supply is not a claim of publication authorization."""
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.verified_supply import (
    conversion_priority_keys, dynamic_profile, route_allows_sku,
    route_supply_keys, supply_profiles,
)

SITE="blogger_moveis_para_cada_canto"
ROUTE={"site_key":SITE, "platform":"blogger",
       "identifier":"1439741542627895062",
       "campaign":"moveisparacadacanto",
       "allowed_niches":["casa/decoracao"],
       "allowed_source_paths":[], "publish_enabled":False}
POLICY={"offers":{}, "trusted_structured_hosts":[],
        "structured_template":{"name":"Móvel com código",
                               "cluster":"guarda-roupa",
                               "advice":[["Medidas","Compare as medidas"]] }}


class SupplySelectionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.catalog=Catalog(Path(tmp.name)/"c.sqlite")
        self.addCleanup(self.catalog.close)
        rows=[
            (1,"Guarda-Roupa Casal 6 Portas 4 Gavetas Giardino Demóbile",
             "Sem GTIN", "casa","decoracao","eligible","matched"),
            (2,"Guarda Roupa Casal 6 Portas 3 Gavetas B23 Briz",
             "Sem EAN", "casa","decoracao","eligible","matched"),
            (3,"Guarda roupa sem marca", "Sem EAN",
             "casa","decoracao","eligible","matched"),
            (4,"Guarda-Roupa Giardino Demóbile", "Sem EAN",
             "limpeza","produtos","eligible","matched"),
            (5,"Guarda-Roupa Giardino Demóbile", "Sem EAN",
             "casa","decoracao","review","review"),
        ]
        for num,title,desc,cat,niche,moderation,status in rows:
            key=f"shopee:100:{num}"
            self.catalog.db.execute("""
              INSERT INTO products(product_key,shop_id,item_id,title,description,
                  origin_url,image_url,moderation,moderation_reason,first_source,
                  last_seen_utc) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,(key,"100",str(num),title,desc,
                 f"https://shopee.com.br/product/100/{num}",
                 "https://cf.shopee.com.br/file/image",
                 moderation,"","feed1","2026-11-22T00:00:00Z"))
            self.catalog.db.execute("""
              INSERT INTO product_taxonomy(product_key,category,niche,status,reason,version)
              VALUES(?,?,?,?,?,?)
            """,(key,cat,niche,status,"unit","v31"))
        self.catalog.db.execute("""
          INSERT INTO affiliate_links(product_key,campaign,affiliate_url,
          verified_origin,updated_utc) VALUES(?,?,?,?,?)
        """,("shopee:100:1",ROUTE["campaign"],
             "https://s.shopee.com.br/test123","shopee_api","2026-11-22"))
        self.catalog.db.commit()

    def test_model_supply_beyond_top24_without_ean(self):
        profiles=dict(supply_profiles(self.catalog,ROUTE,POLICY))
        self.assertIn("shopee:100:1",profiles)
        self.assertIn("shopee:100:2",profiles)
        self.assertNotIn("shopee:100:3",profiles)
        self.assertNotIn("shopee:100:4",profiles)
        self.assertNotIn("shopee:100:5",profiles)
        self.assertEqual(profiles["shopee:100:1"]["manufacturer_identity"]["model"],
                         "giardino")
        self.assertEqual(profiles["shopee:100:2"]["manufacturer_identity"]["model"],
                         "b23")
        self.assertFalse("gtin" in profiles["shopee:100:1"])

    def test_conversion_priority_only_for_validated_catalog_profiles(self):
        self.assertEqual(list(conversion_priority_keys(self.catalog,ROUTE,POLICY)),
                         ["shopee:100:2"])
        self.assertTrue(route_allows_sku(self.catalog,ROUTE,"shopee:100:1"))
        self.assertFalse(route_allows_sku(self.catalog,ROUTE,"shopee:100:4"))
        self.assertFalse(route_allows_sku(self.catalog,ROUTE,"shopee:100:5"))

    def test_specific_candidate_does_not_fall_back_to_unrelated_item(self):
        self.assertEqual(list(supply_profiles(self.catalog,ROUTE,POLICY,
                                              only_key="shopee:100:4")),[])
        only=list(supply_profiles(self.catalog,ROUTE,POLICY,only_key="shopee:100:1"))
        self.assertEqual([key for key,_ in only],["shopee:100:1"])
        self.assertTrue("shopee:100:1" in set(route_supply_keys(
            self.catalog,ROUTE,limit_per_path=100)))
        unsafe={**ROUTE,"publish_enabled":True}
        self.assertFalse(route_allows_sku(self.catalog,unsafe,"shopee:100:1"))


if __name__=="__main__":
    unittest.main()
