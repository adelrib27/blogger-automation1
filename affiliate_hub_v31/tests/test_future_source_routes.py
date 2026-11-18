"""Blogs futuros podem declarar L1/L2 official no cadastro, sem novo Python."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import affiliate_hub_v31.routing as routing
from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.source_category_index import import_source_categories
from affiliate_hub_v31.site_launch_plan import preview_site_launch
from affiliate_hub_v31.fallback_v23 import candidates_from_catalog


class FutureSourceRouteTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.sites_dir=self.root/"new_routes"
        self.sites_dir.mkdir()
        self.route={
            "site_key":"blogger_cozinha_futura",
            "platform":"blogger","identifier":"1234567890123456789",
            "campaign":"futurocozinhareal",
            "allowed_niches":[],
            "allowed_source_paths":["home living/kitchenware"],
            "publish_enabled":False,
        }
        (self.sites_dir/"new.json").write_text(
            json.dumps(self.route),encoding="utf-8")
        self.db=self.root/"catalog.sqlite3"
        feed=self.root/"feed.csv"
        with feed.open("w",newline="",encoding="utf-8") as output:
            writer=csv.DictWriter(output,fieldnames=[
                "shopId","itemId","productName","productLink",
                "imageUrl","globalCategory1","globalCategory2"])
            writer.writeheader()
            for shop,item,title,l1,l2 in (
                ("100","101","Organizador de Cozinha com Tampa",
                 "Home & Living","Kitchenware"),
                ("200","202","Air Fryer Digital 5 Litros",
                 "Home Appliances","Kitchen Appliances"),
            ):
                writer.writerow({
                    "shopId":shop,"itemId":item,"productName":title,
                    "productLink":f"https://shopee.com.br/product/{shop}/{item}",
                    "imageUrl":"https://cf.shopee.com.br/file/img",
                    "globalCategory1":l1,"globalCategory2":l2})
        with Catalog(self.db) as cat:
            cat.import_csv(feed,"feed1")
            import_source_categories(cat,feed,"feed1")
            cat.cache_link("shopee:100:101","futurocozinhareal",
                "https://s.shopee.com.br/offer-for-future-site")
            cat.cache_link("shopee:200:202","outra_campanha",
                "https://s.shopee.com.br/other-site-affiliate")

    def _using_dynamic_route(self):
        routing.sites.cache_clear()
        p=patch.object(routing,"SITES_DIRECTORY",self.sites_dir)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(routing.sites.cache_clear)

    def test_new_route_without_legacy_niches_is_accepted_and_selects_source(self):
        self._using_dynamic_route()
        route=routing.sites()["blogger_cozinha_futura"]
        self.assertEqual(route["allowed_niches"],[])
        self.assertEqual(route["allowed_source_paths"],
                         ["home living/kitchenware"])
        with Catalog(self.db) as cat:
            plan=routing.plan_site(cat,"blogger_cozinha_futura")
        self.assertEqual(plan["product_keys"],["shopee:100:101"])
        self.assertEqual(plan["cached_affiliate_links"],1)
        self.assertEqual(plan["requiring_conversion"],0)

    def test_future_site_launch_uses_exact_campaign_and_review_only_brief(self):
        self._using_dynamic_route()
        with Catalog(self.db) as cat:
            plan=preview_site_launch(cat,topic="Organizador de Cozinha",
                 platform="blogger",site_key="blogger_cozinha_futura")
        self.assertEqual(len(plan["approved_catalog_candidates"]),1)
        item=plan["approved_catalog_candidates"][0]
        self.assertEqual(item["affiliate_url"],
                         "https://s.shopee.com.br/offer-for-future-site")
        self.assertEqual(item["editorial_brief"]["status"],"REVIEW_REQUIRED")
        self.assertFalse(item["can_publish"])
        self.assertEqual(plan["publication_calls"],0)

    def test_future_site_fallback_reads_only_cached_verified_and_source_safe(self):
        self._using_dynamic_route()
        cfg={"categories":{"Cozinha":["organizador de cozinha"]}}
        with patch("affiliate_hub_v31.fallback_v23.sites",
                   side_effect=routing.sites):
            rows=candidates_from_catalog(self.db,
                "blogger_cozinha_futura",cfg,{"rules":{}},limit=5)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["offerLink"],
                         "https://s.shopee.com.br/offer-for-future-site")

    def test_source_route_rejects_protected_root_without_creating_blog(self):
        self.route["allowed_source_paths"]=["health/vitamins"]
        (self.sites_dir/"new.json").write_text(
            json.dumps(self.route),encoding="utf-8")
        self._using_dynamic_route()
        with self.assertRaises(ValueError):
            routing.sites()

    def test_source_route_rejects_wildcards_and_wrong_case(self):
        for invalid in (["*/*"],["Home & Living/Kitchenware"],
                        ["home living"],["home living/kitchenware"]*2):
            with self.subTest(invalid=invalid):
                self.route["allowed_source_paths"]=invalid
                (self.sites_dir/"new.json").write_text(
                    json.dumps(self.route),encoding="utf-8")
                routing.sites.cache_clear()
                with patch.object(routing,"SITES_DIRECTORY",self.sites_dir):
                    with self.assertRaises(ValueError):
                        routing.sites()
        routing.sites.cache_clear()


if __name__=="__main__":
    unittest.main()
