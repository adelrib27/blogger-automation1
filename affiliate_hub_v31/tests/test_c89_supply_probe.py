"""C89 SAFE supply audit: synthetic database only, no network or credentials."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31 import supply_probe as probe


class SupplyProbeTests(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.dbfile = Path(td.name) / "test.sqlite3"
        self.profiles = Path(td.name) / "profiles.json"
        self.profiles.write_text(json.dumps({
            "blogger_example": {
                "offers": {"shopee:100:1": {"name": "Brand A"}},
                "trusted_structured_hosts": ["example.org"],
            }
        }))
        self.cat = Catalog(self.dbfile)
        self.addCleanup(self.cat.close)
        items = [
            ("1", "Mesa com EAN: 4006381333931", "EAN: 4006381333931",
             "eligible", "matched"),
            ("2", "Guarda-roupa", "Sem EAN no texto", "eligible", "matched"),
            ("3", "Amostra rejeitada", "EAN: 4006381333931", "review", "review"),
        ]
        for sku,title,description,mod,tax in items:
            key = "shopee:100:" + sku
            self.cat.db.execute(
                """INSERT INTO products(product_key,shop_id,item_id,title,
                  description,origin_url,image_url,moderation,moderation_reason,
                  first_source,last_seen_utc) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (key, "100", sku, title, description,
                 "https://shopee.com.br/product/100/"+sku,
                 "https://cf.shopee.com.br/file/image", mod, "", "test",
                 "2026-11-22T00:00:00Z"))
            self.cat.db.execute(
                """INSERT INTO product_taxonomy
                  (product_key,category,niche,status,reason,version)
                  VALUES(?,?,?,?,?,?)""",
                (key,"casa","decoracao",tax,"test","v1"))
        self.cat.db.execute(
            """INSERT INTO affiliate_links(product_key,campaign,affiliate_url,
                  verified_origin,updated_utc) VALUES(?,?,?,?,?)""",
            ("shopee:100:1","examplecampaign",
             "https://s.shopee.com.br/test", "shopee_api", "2026-11-22"))
        self.cat.db.commit()
        route={"site_key":"blogger_example","platform":"blogger",
               "identifier":"1234567890123456","campaign":"examplecampaign",
               "allowed_niches":["casa/decoracao"],"allowed_source_paths":[],
               "publish_enabled":False}
        self.patchers=[
            patch.object(probe, "sites",return_value={"blogger_example":route}),
            patch.object(probe, "load_requests",return_value=[{
                "site_key":"blogger_example","platform":"blogger","topic":"mesa",
                "articles":None,"enabled":True}]),
            patch.object(probe, "VERIFIER_PROFILES",self.profiles),
            patch.object(probe, "preview_site_launch",return_value={
                "approved_catalog_candidates":[
                    {"product_key":"shopee:100:1",
                     "affiliate_status":"verified_for_campaign"},
                    {"product_key":"shopee:100:2",
                     "affiliate_status":"requires_conversion"}]})
        ]
        for p in self.patchers:
            p.start()
            self.addCleanup(p.stop)

    def test_counts_cached_gtin_and_missing_conversion_without_leaking_products(self):
        result=probe.audit_catalog(self.cat,"blogger_example")
        self.assertEqual(result["profiled_offer_count"],1)
        self.assertEqual(result["profiled_approved_with_campaign_link"],1)
        self.assertEqual(result["top24_gtin_with_campaign_link"],1)
        self.assertEqual(result["authorized_pool_scanned"],2)
        self.assertEqual(result["authorized_pool_valid_gtin"],1)
        self.assertEqual(result["authorized_pool_gtin_with_campaign_link"],1)
        self.assertEqual(result["paid_research_calls"],0)
        self.assertEqual(result["r2_mutations"],0)
        self.assertEqual(result["cms_posts_created"],0)
        self.assertNotIn("https",json.dumps(result))
        self.assertNotIn("shopee:100:",json.dumps(result))

    def test_invalid_route_fails_closed_without_network(self):
        with self.assertRaisesRegex(ValueError,"registered_draft_only_request_required"):
            probe.audit_catalog(self.cat,"unregistered_site")

    def test_gtin_rejects_missing_and_invalid_check_digit(self):
        self.assertFalse(probe._has_valid_gtin(self.cat,"shopee:100:2"))
        self.cat.db.execute("UPDATE products SET description='EAN: 4006381333932' "
                            "WHERE product_key='shopee:100:1'")
        self.assertFalse(probe._has_valid_gtin(self.cat,"shopee:100:1"))


if __name__=="__main__":
    unittest.main()
