"""C22: contrato contextual para blogs existentes e ainda não criados."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.site_launch_plan import (
    SiteLaunchError,preview_site_launch,summarize_site_launch,
)
from affiliate_hub_v31.source_category_index import import_source_categories


class LaunchPlanTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root=Path(tmp.name)
        self.db=root/"catalog.sqlite3"
        feed=root/"feed.csv"
        products=[
            ("11","100","Air Fryer Digital 5 litros","Home Appliances","Kitchen Appliances"),
            ("12","200","Air Fryer Digital 4 litros","Home Appliances","Kitchen Appliances"),
            ("13","300","Organizador de Cozinha com Tampa","Home & Living","Kitchenware"),
            ("14","400","Air Fryer Proibida Antigo","Health","Nutrition"),
            ("15","500","Produto Vitrine Sem Nicho","Home & Living","Furniture"),
        ]
        with feed.open("w",newline="",encoding="utf-8") as stream:
            w=csv.DictWriter(stream,fieldnames=[
                "shopId","itemId","productName","productLink","imageUrl",
                "globalCategory1","globalCategory2"])
            w.writeheader()
            for shop,item,title,l1,l2 in products:
                w.writerow({
                    "shopId":shop,"itemId":item,"productName":title,
                    "productLink":f"https://shopee.com.br/product/{shop}/{item}",
                    "imageUrl":"https://cf.shopee.com.br/file/image",
                    "globalCategory1":l1,"globalCategory2":l2})
        with Catalog(self.db) as cat:
            cat.import_csv(feed,"first")
            import_source_categories(cat,feed,"first")
            cat.cache_link("shopee:11:100","airfryers",
                           "https://s.shopee.com.br/old-airfryers-link")
            cat.cache_link("shopee:12:200","radarwp",
                           "https://s.shopee.com.br/radarwp-link")

    def test_blogger_existing_site_uses_only_its_campaign_and_creates_brief(self):
        with Catalog(self.db) as cat:
            first=cat.stats()
            plan=preview_site_launch(cat,topic="Air Fryer",platform="blogger",
                                     site_key="blogger_air_fryers")
            after=cat.stats()
        self.assertEqual(first,after)
        self.assertTrue(plan["registered_site"])
        self.assertEqual(plan["campaign"],"airfryers")
        self.assertEqual(len(plan["approved_catalog_candidates"]),2)
        by_id={x["product_key"]:x for x in plan["approved_catalog_candidates"]}
        self.assertEqual(by_id["shopee:11:100"]["affiliate_status"],
                         "verified_for_campaign")
        self.assertEqual(by_id["shopee:11:100"]["affiliate_url"],
                         "https://s.shopee.com.br/old-airfryers-link")
        self.assertEqual(by_id["shopee:12:200"]["affiliate_status"],
                         "requires_conversion")
        self.assertIsNone(by_id["shopee:12:200"]["affiliate_url"])
        self.assertTrue(all(x["editorial_brief"]["status"]=="REVIEW_REQUIRED"
                            for x in plan["approved_catalog_candidates"]))
        self.assertTrue(all("air fryer" in x["editorial_brief"]["keyword"]
                            for x in plan["approved_catalog_candidates"]))
        self.assertEqual(plan["publication_calls"],0)
        self.assertEqual(plan["r2_writes"],0)

    def test_future_blogger_is_not_assigned_another_blog_affiliate_link(self):
        with Catalog(self.db) as cat:
            p=preview_site_launch(cat,topic="Air Fryer",platform="blogger")
        self.assertTrue(p["future_site_needs_registration"])
        self.assertIsNone(p["campaign"])
        self.assertTrue(p["approved_catalog_candidates"])
        self.assertTrue(all(x["affiliate_url"] is None and
                            x["editorial_brief"] is None
                            for x in p["approved_catalog_candidates"]))
        self.assertEqual(p["cached_for_campaign"],0)
        self.assertEqual(p["requires_conversion"],0)

    def test_wordpress_isolation_and_cross_site_flags(self):
        with Catalog(self.db) as cat:
            plan=preview_site_launch(cat,topic="Air Fryer",platform="wordpress",
                                     site_key="wordpress_radartechbr")
        self.assertEqual(plan["campaign"],"radarwp")
        self.assertEqual(plan["platform"],"wordpress")
        by_id={x["product_key"]:x for x in plan["approved_catalog_candidates"]}
        self.assertEqual(by_id["shopee:12:200"]["affiliate_url"],
                         "https://s.shopee.com.br/radarwp-link")
        self.assertIsNone(by_id["shopee:11:100"]["affiliate_url"])
        self.assertTrue(all(x["editorial_brief"] is not None
                            for x in plan["approved_catalog_candidates"]))

    def test_mismatched_niche_is_filtered_and_root_protected_stays_out(self):
        with Catalog(self.db) as cat:
            wrong=preview_site_launch(cat,topic="Air Fryer",platform="wordpress",
                                      site_key="wordpress_casa_decoracao")
            correct=preview_site_launch(cat,topic="Organizador de Cozinha",
                                        platform="wordpress",
                                        site_key="wordpress_casa_decoracao")
        self.assertEqual(wrong["approved_catalog_candidates"],[])
        self.assertEqual(len(correct["approved_catalog_candidates"]),1)
        self.assertEqual(correct["approved_catalog_candidates"][0]
                         ["editorial_category"],"cozinha")
        self.assertTrue(all(x["source_category_l1"]!="health"
                            for x in wrong["approved_catalog_candidates"]))
        self.assertEqual(correct["requires_conversion"],1)
        self.assertFalse(correct["can_publish"])

    def test_registration_campaign_mismatch_and_invalid_platform_fail_closed(self):
        with Catalog(self.db) as cat:
            cases=[
                dict(platform="pinterest"),
                dict(platform="blogger",campaign="outra"),
                dict(platform="wordpress",site_key="blogger_air_fryers"),
                dict(platform="blogger",site_key="ghost"),
                dict(platform="blogger",site_key="blogger_air_fryers",
                     campaign="wrongcampaign"),
                dict(platform="blogger",site_key="blogger_air_fryers",
                     max_items=0),
                dict(platform="blogger",site_key="blogger_air_fryers",
                     max_per_shop=0),
            ]
            for case in cases:
                with self.subTest(case=case),self.assertRaises((SiteLaunchError,ValueError)):
                    preview_site_launch(cat,topic="Air Fryer",**case)

    def test_sanitized_site_summary_does_not_leak_site_campaign_or_products(self):
        with Catalog(self.db) as cat:
            plan=preview_site_launch(cat,topic="Air Fryer",platform="blogger",
                                     site_key="blogger_air_fryers")
        report=summarize_site_launch(plan)
        raw=json.dumps(report,ensure_ascii=False)
        for forbidden in ("Air Fryer","blogger_air_fryers","airfryers",
                          "shopee:","s.shopee.com.br","old-airfryers",
                          "Digital 5 litros"):
            self.assertNotIn(forbidden,raw)
        self.assertTrue(report["registered_site"])
        self.assertEqual(report["selected_catalog_candidates"],2)
        self.assertEqual(report["cached_links_for_exact_campaign"],1)
        self.assertEqual(report["items_requiring_conversion_for_exact_campaign"],1)
        self.assertEqual(report["proposed_editorial_briefs"],2)
        self.assertEqual(report["r2_writes"],0)
        self.assertFalse(report["can_publish"])


if __name__=="__main__":
    unittest.main()
