"""C137 — nenhum cache sem campanha exata vira autorização DRAFT ou LIVE."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31 import campaign_cache_readiness as m


SKU = "shopee:123456:987654"
TITLE = "Forma de silicone retangular para uso doméstico na cozinha"
CAMPAIGN = "cozinhasemcomp"
ROUTE = {"site_key": "blogger_cozinha_sem_complicacao",
         "platform": "blogger", "identifier": "3552757910439359679",
         "campaign": CAMPAIGN, "allowed_niches": ["cozinha/utensilios"],
         "publish_enabled": False}
IMAGE = "https://cf.shopee.com.br/file/test-image"
ORIGIN = "https://shopee.com.br/product/123456/987654"
LINK = "https://s.shopee.com.br/safeTestCache"


class C137CampaignCacheReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.path = Path(self.t.name) / "r2_catalog.sqlite3"
        with Catalog(self.path) as cat:
            with cat.db:
                cat.db.execute("""
                    INSERT INTO products(product_key, shop_id, item_id, title,
                    description, origin_url, image_url, moderation, moderation_reason,
                    first_source, last_seen_utc)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """, (SKU,"123456","987654",TITLE,"",ORIGIN,IMAGE,
                       "eligible","","feed","2026-11-23T20:00:00Z"))
                cat.db.execute("""
                    INSERT INTO product_taxonomy(product_key,category,niche,status,reason,version)
                    VALUES(?,?,?,?,?,?)
                """, (SKU,"cozinha","utensilios","matched","fixture","v31"))

    def inspect(self, route=ROUTE, *, cached=False):
        with Catalog(self.path) as c:
            if cached:
                c.cache_link(SKU, CAMPAIGN, LINK)
            with patch.object(m, "source_safe_for_use", return_value=True):
                return m.inspect_campaign_cache(c, route)

    def test_unconverted_is_not_eligible_for_draft(self):
        x = self.inspect()
        self.assertEqual(x["catalog_candidates"], 1)
        self.assertEqual(x["cached_exact_campaign"], 0)
        self.assertFalse(x["items"][0]["eligible_for_draft_write"])
        self.assertFalse(x["automatic_live_authorized"])

    def test_exact_campaign_cached_is_not_full_verification(self):
        x = self.inspect(cached=True)
        self.assertEqual(x["cached_exact_campaign"], 1)
        item = x["items"][0]
        self.assertTrue(item["cached_for_exact_campaign"])
        self.assertEqual(item["cache_origin"], "shopee_api")
        self.assertFalse(item["manufacturer_facts_verified"])
        self.assertFalse(item["redirect_target_currently_verified"])
        self.assertFalse(item["cms_duplicate_checked"])
        self.assertFalse(item["eligible_for_draft_write"])

    def test_other_campaign_cache_must_not_match(self):
        with Catalog(self.path) as c:
            c.cache_link(SKU, "outrocamp", LINK)
        x = self.inspect()
        self.assertEqual(x["cached_exact_campaign"], 0)

    def test_invalid_link_in_database_fails_closed(self):
        with Catalog(self.path) as c:
            c.cache_link(SKU, CAMPAIGN, LINK)
            c.db.execute("UPDATE affiliate_links SET affiliate_url='http://bad.test/'")
            c.db.commit()
        with self.assertRaisesRegex(m.CampaignCacheAuditError, "cached_link_untrusted"):
            self.inspect()

    def test_untrusted_affiliate_provenance_fails_closed(self):
        with Catalog(self.path) as c:
            c.cache_link(SKU, CAMPAIGN, LINK)
            c.db.execute("UPDATE affiliate_links SET verified_origin='unknown'")
            c.db.commit()
        with self.assertRaisesRegex(m.CampaignCacheAuditError, "cached_link_untrusted"):
            self.inspect()

    def test_same_affiliate_cache_guard_accepts_wordpress(self):
        wp = {**ROUTE, "platform": "wordpress",
              "site_key": "wordpress_test_scoped",
              "identifier": "https://editorial.example/"}
        x = self.inspect(route=wp, cached=True)
        self.assertEqual(x["cached_exact_campaign"], 1)
        self.assertFalse(x["items"][0]["eligible_for_draft_write"])
        self.assertEqual(x["site_key"], "wordpress_test_scoped")

    def test_wordpress_wrong_campaign_not_reused(self):
        wp = {**ROUTE, "platform": "wordpress",
              "site_key": "wordpress_test_scoped",
              "identifier": "https://editorial.example/",
              "campaign": "anotherwp"}
        x = self.inspect(route=wp, cached=True)
        self.assertEqual(x["cached_exact_campaign"], 0)
        self.assertFalse(x["automatic_live_authorized"])

    def test_publisher_route_not_allowed(self):
        with self.assertRaisesRegex(m.CampaignCacheAuditError, "safe_editorial_route"):
            self.inspect(route={**ROUTE,"publish_enabled":True})

    def test_cross_campaign_isolation(self):
        x = self.inspect(route={**ROUTE,"campaign":"outrocamp"})
        self.assertEqual(x["site_key"], ROUTE["site_key"])
        self.assertEqual(x["campaign"], "outrocamp")
        self.assertEqual(x["cached_exact_campaign"], 0)

    def test_policy_rejects_catalog_candidate(self):
        with Catalog(self.path) as c:
            with patch.object(m, "source_safe_for_use", return_value=False):
                x = m.inspect_campaign_cache(c,ROUTE)
        self.assertEqual(x["catalog_candidates"], 0)

    def test_moderation_rejected_product_excluded(self):
        with Catalog(self.path) as c:
            c.db.execute("UPDATE products SET moderation='review'")
            c.db.commit()
        x = self.inspect()
        self.assertEqual(x["catalog_candidates"],0)

    def test_wrong_taxonomy_excluded(self):
        with Catalog(self.path) as c:
            c.db.execute("UPDATE product_taxonomy SET niche='outra'")
            c.db.commit()
        self.assertEqual(self.inspect()["catalog_candidates"], 0)

    def test_strict_max_four(self):
        with self.assertRaisesRegex(m.CampaignCacheAuditError, "safe_editorial_route"):
            with Catalog(self.path) as c:
                m.inspect_campaign_cache(c, ROUTE, limit=5)

    def test_site_keys_duplicate_denied_before_network(self):
        with self.assertRaisesRegex(m.CampaignCacheAuditError, "sites_invalid"):
            m.audit(site_keys=(ROUTE["site_key"], ROUTE["site_key"]))

    def test_count_only_and_no_direct_affiliate_url_leak(self):
        x = self.inspect(cached=True)
        self.assertEqual(x["affiliate_conversions"],0)
        self.assertEqual(x["cms_writes"],0)
        self.assertEqual(x["d1_writes"],0)
        self.assertEqual(x["r2_writes"],0)
        self.assertNotIn(LINK,str(x))


if __name__ == "__main__":
    unittest.main()
