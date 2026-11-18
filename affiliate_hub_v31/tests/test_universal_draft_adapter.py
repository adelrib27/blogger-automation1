"""C41: draft Blogger/WordPress somente após aprovação, corpo original e campanha."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.universal_draft_adapter import (
    UniversalDraftError,prepare_universal_draft,
)

ROUTES={
  "blog_real":{"site_key":"blog_real","platform":"blogger",
               "identifier":"1234567890123456","campaign":"campanha_blog",
               "allowed_niches":["cozinha/air_fryers"],
               "publish_enabled":False},
  "wp_real":{"site_key":"wp_real","platform":"wordpress",
             "identifier":"https://wp.example/","campaign":"campanha_wp",
             "allowed_niches":["cozinha/air_fryers"],
             "publish_enabled":False},
}


def envelope(site,offer,product="shopee:11:22"):
    route=ROUTES[site]
    return {"site_key":site,"campaign":route["campaign"],
            "platform":route["platform"],"status":"REVIEW_REQUIRED",
            "publication_allowed":False,
            "jobs":[{
                "site_key":site,"platform":route["platform"],
                "campaign":route["campaign"],"status":"REVIEW_REQUIRED",
                "publication_allowed":False,"product_key":product,
                "editorial_brief":{"proposed_title":"Guia: air fryer — critérios",
                    "keyword":"air fryer","slug":"guia-air-fryer-criterios",
                    "editorial_status":"REVIEW_REQUIRED"},
                "product":{"shopId":"11","itemId":"22",
                    "productLink":"https://shopee.com.br/product/11/22",
                    "offerLink":offer,
                    "sourceModes":["csv_r2_verified_affiliate_cache"]},
            }]}


def paragraphs():
    single=("Para escolher uma air fryer, avalie o tamanho da cozinha, "
            "as necessidades práticas da rotina e as características "
            "confirmadas pelo fabricante antes de comparar alternativas "
            "sem assumir avaliações, comissões ou experiências não verificadas. ")
    return [single*3 for _ in range(4)]


class UniversalDraftTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.path=Path(t.name)/"catalog.sqlite3"
        with Catalog(self.path) as cat:
            with cat.db:
                cat.db.execute("""
                    INSERT INTO products(product_key,shop_id,item_id,title,
                      description,origin_url,image_url,moderation,
                      moderation_reason,first_source,last_seen_utc)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,("shopee:11:22","11","22","Air Fryer Digital","",
                    "https://shopee.com.br/product/11/22",
                    "https://cf.shopee.com.br/file/x",
                    "eligible","","fixture","2026-11-18T00:00:00Z"))
                cat.db.execute("""
                    INSERT INTO product_taxonomy(product_key,category,niche,
                       status,reason,version) VALUES(?,?,?,?,?,?)
                """,("shopee:11:22","cozinha","air_fryers",
                     "matched","test","test"))
            cat.cache_link("shopee:11:22","campanha_blog",
                           "https://s.shopee.com.br/blog-real")
            cat.cache_link("shopee:11:22","campanha_wp",
                           "https://s.shopee.com.br/wp-real")
            cat.cache_link("shopee:11:22","outra",
                           "https://s.shopee.com.br/other")
        self.patch=patch("affiliate_hub_v31.universal_draft_adapter.sites",
                         return_value=ROUTES)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_blogger_draft_is_not_published_and_uses_only_correct_campaign(self):
        with Catalog(self.path) as cat:
            before=cat.stats()
            result=prepare_universal_draft(cat,site_key="blog_real",
                envelope=envelope("blog_real","https://s.shopee.com.br/blog-real"),
                product_key="shopee:11:22",paragraphs=paragraphs(),approved=True)
            self.assertEqual(before,cat.stats())
        self.assertEqual(result.platform,"blogger")
        self.assertEqual(result.status,"draft")
        self.assertTrue(result.meta["isDraft"])
        self.assertIn("blog-real",result.content_html)
        self.assertNotIn("/other",result.content_html)
        self.assertNotIn("<script>",result.content_html)

    def test_wordpress_draft_has_status_draft(self):
        with Catalog(self.path) as cat:
            result=prepare_universal_draft(cat,site_key="wp_real",
                envelope=envelope("wp_real","https://s.shopee.com.br/wp-real"),
                product_key="shopee:11:22",paragraphs=paragraphs(),approved=True)
        self.assertEqual(result.platform,"wordpress")
        self.assertEqual(result.meta["status"],"draft")
        self.assertIn("wp-real",result.content_html)

    def test_requires_explicit_approval_and_original_body(self):
        with Catalog(self.path) as cat:
            for approved,body in ((False,paragraphs()),(True,["curto"]*4),
                                  (True,paragraphs()[:2])):
                with self.subTest(approved=approved),self.assertRaises(UniversalDraftError):
                    prepare_universal_draft(cat,site_key="blog_real",
                        envelope=envelope("blog_real","https://s.shopee.com.br/blog-real"),
                        product_key="shopee:11:22",paragraphs=body,approved=approved)

    def test_cross_campaign_cache_leak_is_refused(self):
        with Catalog(self.path) as cat:
            with self.assertRaises(UniversalDraftError):
                prepare_universal_draft(cat,site_key="blog_real",
                    envelope=envelope("blog_real","https://s.shopee.com.br/other"),
                    product_key="shopee:11:22",paragraphs=paragraphs(),approved=True)
            with self.assertRaises(UniversalDraftError):
                prepare_universal_draft(cat,site_key="blog_real",
                    envelope=envelope("wp_real","https://s.shopee.com.br/wp-real"),
                    product_key="shopee:11:22",paragraphs=paragraphs(),approved=True)

    def test_banned_product_cannot_be_prepared_even_with_cached_link(self):
        with Catalog(self.path) as cat:
            with cat.db:
                cat.db.execute("UPDATE products SET moderation='review' WHERE product_key=?",
                               ("shopee:11:22",))
            with self.assertRaises(UniversalDraftError):
                prepare_universal_draft(cat,site_key="blog_real",
                    envelope=envelope("blog_real","https://s.shopee.com.br/blog-real"),
                    product_key="shopee:11:22",paragraphs=paragraphs(),approved=True)

    def test_html_is_escaped_and_not_interpreted(self):
        body=paragraphs()
        body[0]+="<script>alert('x')</script>"
        with Catalog(self.path) as cat:
            result=prepare_universal_draft(cat,site_key="blog_real",
                envelope=envelope("blog_real","https://s.shopee.com.br/blog-real"),
                product_key="shopee:11:22",paragraphs=body,approved=True)
        self.assertNotIn("<script>",result.content_html)
        self.assertIn("&lt;script&gt;",result.content_html)


if __name__=="__main__":
    unittest.main()
