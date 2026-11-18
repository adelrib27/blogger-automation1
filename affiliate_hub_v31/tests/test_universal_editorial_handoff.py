"""C36: e2e de handoff sem publicar nem cruzar campanhas."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.universal_editorial_handoff import (
    HandoffError,plan_editorial_handoff,safe_summary,
)

ROUTE={"site_key":"blog_novo_real","platform":"blogger",
       "identifier":"1234567890123456","campaign":"campanha_nova",
       "allowed_niches":["cozinha/air_fryers"],"publish_enabled":False}


class HandoffTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/"catalog.sqlite3"
        with Catalog(self.path) as cat:
            with cat.db:
                for i,mod,tax in ((1,"eligible","matched"),
                                  (2,"eligible","matched"),
                                  (3,"review","review")):
                    key=f"shopee:{100+i}:{200+i}"
                    cat.db.execute("""
                      INSERT INTO products(product_key,shop_id,item_id,
                        title,description,origin_url,image_url,moderation,
                        moderation_reason,first_source,last_seen_utc)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,str(100+i),str(200+i),
                         f"Air Fryer Digital {i} litros","",
                         f"https://shopee.com.br/product/{100+i}/{200+i}",
                         "https://cf.shopee.com.br/file/test",mod,"",
                         "test","2026-11-18T00:00:00Z"))
                    cat.db.execute("""
                      INSERT INTO product_taxonomy
                      (product_key,category,niche,status,reason,version)
                      VALUES(?,?,?,?,?,?)
                    """,(key,"cozinha","air_fryers",tax,"test","test"))
            cat.cache_link("shopee:101:201","campanha_antiga",
                           "https://s.shopee.com.br/oldcampaign")
            cat.cache_link("shopee:101:201","campanha_nova",
                           "https://s.shopee.com.br/newcampaign")

    def test_future_blog_without_campaign_prepares_discovery_only(self):
        with Catalog(self.path) as cat:
            before=cat.stats()
            result=plan_editorial_handoff(cat,topic="Air Fryer",
                platform="blogger",articles=3)
            after=cat.stats()
        self.assertEqual(before,after)
        self.assertTrue(result["requires_registration"])
        self.assertEqual(result["ready_review_jobs"],[])
        self.assertEqual(result["conversion_required_keys"],[])
        self.assertEqual(result["discovered_approved"],2)
        self.assertEqual(result["publication_calls"],0)

    def test_registered_site_gets_only_exact_campaign_link_and_conversion_queue(self):
        with patch("affiliate_hub_v31.universal_editorial_handoff.sites",
                   return_value={"blog_novo_real":ROUTE}), \
             patch("affiliate_hub_v31.site_launch_plan.sites",
                   return_value={"blog_novo_real":ROUTE}):
            with Catalog(self.path) as cat:
                result=plan_editorial_handoff(cat,topic="Air Fryer",
                   platform="blogger",articles=3,site_key="blog_novo_real")
        self.assertEqual(len(result["ready_review_jobs"]),1)
        self.assertEqual(len(result["conversion_required_keys"]),1)
        self.assertEqual(result["review_candidates"],1)
        job=result["ready_review_jobs"][0]
        self.assertEqual(job["product"]["offerLink"],
                         "https://s.shopee.com.br/newcampaign")
        self.assertEqual(job["campaign"],"campanha_nova")
        self.assertEqual(job["status"],"REVIEW_REQUIRED")
        self.assertFalse(job["publication_allowed"])
        self.assertEqual(result["r2_writes"],0)
        self.assertEqual(result["publication_calls"],0)

    def test_summary_omits_identifiers_urls_topics_and_campaigns(self):
        with patch("affiliate_hub_v31.universal_editorial_handoff.sites",
                   return_value={"blog_novo_real":ROUTE}), \
             patch("affiliate_hub_v31.site_launch_plan.sites",
                   return_value={"blog_novo_real":ROUTE}):
            with Catalog(self.path) as cat:
                result=plan_editorial_handoff(cat,topic="Air Fryer",
                   platform="blogger",articles=2,site_key="blog_novo_real")
        s=json.dumps(safe_summary(result))
        for value in ("blog_novo_real","campanha_nova","Air Fryer",
                      "shopee:101","newcampaign","productName","offerLink"):
            self.assertNotIn(value,s)
        self.assertEqual(safe_summary(result)["ready_review_jobs"],1)

    def test_unregistered_key_wrong_platform_and_limits_block(self):
        with Catalog(self.path) as cat:
            for opts in (
                dict(site_key="missing"),
                dict(articles=0),
                dict(articles=25),
                dict(articles=True),
                dict(platform="pinterest"),
                dict(topic=" "),
            ):
                with self.subTest(opts=opts), self.assertRaises(HandoffError):
                    plan_editorial_handoff(cat,topic="Air Fryer",
                        platform="blogger",articles=3,**opts)
        with patch("affiliate_hub_v31.universal_editorial_handoff.sites",
                   return_value={"blog_novo_real":ROUTE}):
            with Catalog(self.path) as cat:
                with self.assertRaises(HandoffError):
                    plan_editorial_handoff(cat,topic="Air Fryer",
                        platform="wordpress",articles=2,
                        site_key="blog_novo_real")

    def test_no_cross_campaign_when_only_other_link_exists(self):
        with patch("affiliate_hub_v31.universal_editorial_handoff.sites",
                   return_value={"blog_novo_real":ROUTE}), \
             patch("affiliate_hub_v31.site_launch_plan.sites",
                   return_value={"blog_novo_real":ROUTE}):
            with Catalog(self.path) as cat:
                with cat.db:
                    cat.db.execute("DELETE FROM affiliate_links WHERE campaign='campanha_nova'")
                result=plan_editorial_handoff(cat,topic="Air Fryer",
                    platform="blogger",articles=2,site_key="blog_novo_real")
        self.assertEqual(result["ready_review_jobs"],[])
        self.assertEqual(len(result["conversion_required_keys"]),2)
        self.assertEqual(result["publication_calls"],0)


if __name__=="__main__":
    unittest.main()
