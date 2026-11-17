"""C20: contrato futuro blog SAFE e separação da fila pendente por campanha."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.future_site_intake import (
    IntakeError, preview_future_site, summarize_preview,
)
from affiliate_hub_v31.product_discovery import discover, DiscoveryError
from affiliate_hub_v31.source_category_index import import_source_categories
from affiliate_hub_v31.title_index import rebuild_index


class FutureSiteIntakeTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / "catalog.sqlite3"
        self.feed = Path(folder.name) / "feed.csv"
        rows = [
            ("101", "1", "Air Fryer Digital 5 litros", "Home Appliances", "Kitchen Appliances"),
            ("202", "3", "Air Fryer Digital 4 litros", "Home Appliances", "Kitchen Appliances"),
            ("404", "5", "Guarda Roupa Casal 4 Portas", "Home & Living", "Furniture"),
            ("505", "6", "Air Fryer Digital Saúde", "Health", "Nutritional"),
        ]
        with self.feed.open("w", encoding="utf-8", newline="") as stream:
            w = csv.DictWriter(stream, fieldnames=[
                "shopId", "itemId", "productName", "productLink", "imageUrl",
                "globalCategory1", "globalCategory2",
            ])
            w.writeheader()
            for shop, item, title, l1, l2 in rows:
                w.writerow({
                    "shopId": shop, "itemId": item, "productName": title,
                    "productLink": f"https://shopee.com.br/product/{shop}/{item}",
                    "imageUrl": "https://cf.shopee.com.br/file/image",
                    "globalCategory1": l1, "globalCategory2": l2,
                })
        with Catalog(self.db) as cat:
            cat.import_csv(self.feed, "first")
            import_source_categories(cat, self.feed, "first")
            cat.cache_link("shopee:101:1", "blogantigo",
                           "https://s.shopee.com.br/link-real-antigo")
            cat.cache_link("shopee:202:3", "novoblog",
                           "https://s.shopee.com.br/link-real-novoblog")

    def test_unassigned_future_site_uses_user_topic_and_no_campaign_link(self):
        with Catalog(self.db) as cat:
            result = preview_future_site(cat, topic="Air Fryer")
        self.assertEqual(result["platform"], "unspecified")
        self.assertFalse(result["campaign_explicitly_selected"])
        self.assertTrue(result["category_paths"])
        self.assertEqual(result["category_paths"][0]["category"], "home appliances")
        self.assertTrue(result["approved_candidates"])
        self.assertTrue(all(x["affiliate_url"] is None
                            for x in result["approved_candidates"]))
        self.assertEqual(result["site_creation_calls"], 0)
        self.assertEqual(result["affiliate_conversion_calls"], 0)
        self.assertEqual(result["publication_calls"], 0)
        self.assertEqual(result["r2_writes"], 0)
        self.assertFalse(result["can_publish"])

    def test_only_explicit_campaign_link_can_be_reused(self):
        with Catalog(self.db) as cat:
            result = preview_future_site(cat, topic="Air Fryer Digital",
                                         platform="wordpress",
                                         campaign="novoblog")
        by_key = {p["product_key"]: p for p in result["approved_candidates"]}
        self.assertIsNone(by_key["shopee:101:1"]["affiliate_url"])
        self.assertEqual(by_key["shopee:101:1"]["affiliate_status"],
                         "requires_conversion")
        self.assertEqual(by_key["shopee:202:3"]["affiliate_url"],
                         "https://s.shopee.com.br/link-real-novoblog")
        self.assertTrue(all(p["affiliate_url"] is None for p in result["review_queue"]))
        self.assertTrue(all(not p["can_publish"]
                            for p in result["approved_candidates"] + result["review_queue"]))

    def test_review_queue_is_disjoint_and_protected_products_not_approved(self):
        with Catalog(self.db) as cat:
            result = preview_future_site(cat, topic="Air Fryer",
                                         platform="blogger", review_limit=12)
            wardrobe = preview_future_site(cat, topic="Guarda Roupa")
        approved_keys = {x["product_key"] for x in result["approved_candidates"]}
        pending_keys = {x["product_key"] for x in result["review_queue"]}
        self.assertFalse(approved_keys & pending_keys)
        self.assertIn("shopee:505:6", pending_keys)
        protected = next(x for x in result["review_queue"]
                         if x["product_key"] == "shopee:505:6")
        self.assertIn("PROTECTED_SOURCE_ROOT", protected["review_reasons"])
        self.assertEqual(protected["curation"], "review_required")
        self.assertEqual(wardrobe["approved_candidates"], [])
        self.assertEqual(wardrobe["review_queue"][0]["curation"], "review_required")
        self.assertIn("EDITORIAL_TAXONOMY_UNMATCHED",
                      wardrobe["review_queue"][0]["review_reasons"])

    def test_review_only_requires_explicit_review_opt_in(self):
        with Catalog(self.db) as cat:
            with self.assertRaisesRegex(DiscoveryError,
                                        "review_only_requires_review_mode"):
                discover(cat, topic="Air Fryer", review_only=True)
            queue = discover(cat, topic="Air Fryer", include_review=True,
                             review_only=True, campaign="blogantigo")
        self.assertTrue(queue)
        self.assertTrue(all(x["curation"] == "review_required" and
                            x["affiliate_url"] is None for x in queue))

    def test_snapshot_unchanged_and_fts_before_after_same_result(self):
        with Catalog(self.db) as cat:
            initial = cat.stats()
            before = preview_future_site(cat, topic="Air Fryer",
                                         campaign="novoblog")
            self.assertEqual(cat.stats(), initial)
            rebuild_index(cat)
            indexed = preview_future_site(cat, topic="Air Fryer",
                                          campaign="novoblog")
            self.assertEqual(cat.stats(), initial)
        self.assertEqual(before, indexed)

    def test_safe_summary_never_logs_urls_titles_keys_or_topic(self):
        with Catalog(self.db) as cat:
            full = preview_future_site(cat, topic="Air Fryer",
                                       campaign="novoblog")
            raw = json.dumps(summarize_preview(full), ensure_ascii=False)
        self.assertNotIn("Air Fryer", raw)
        self.assertNotIn("shopee:", raw)
        self.assertNotIn("s.shopee.com.br", raw)
        self.assertNotIn("novoblog", raw)
        self.assertNotIn("link-real", raw)
        self.assertIn("approved_candidate_count", raw)
        self.assertIn('"can_publish": false', raw)

    def test_invalid_topic_platform_limits_and_campaign_fail_closed(self):
        with Catalog(self.db) as cat:
            for bad in ("", "de para com", " "):
                with self.subTest(topic=bad), self.assertRaises(DiscoveryError):
                    preview_future_site(cat, topic=bad)
            for bad in ("pinterest", "blogger+wordpress", "", None):
                with self.subTest(platform=bad), self.assertRaises(IntakeError):
                    preview_future_site(cat, topic="Air Fryer", platform=bad)
            with self.assertRaises(IntakeError):
                preview_future_site(cat, topic="Air Fryer", review_limit=1000)
            with self.assertRaises(IntakeError):
                preview_future_site(cat, topic="Air Fryer", approved_limit=0)
            with self.assertRaises(ValueError):
                preview_future_site(cat, topic="Air Fryer", campaign="???")


if __name__ == "__main__":
    unittest.main()
