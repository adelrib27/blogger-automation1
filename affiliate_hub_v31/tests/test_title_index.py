"""C19: o FTS reduz a varredura sem alterar a seleção editorial ou links."""
import unittest

from affiliate_hub_v31.title_index import (
    rebuild_index,has_index,fts_condition,safe_match_expression,
)
from affiliate_hub_v31.product_discovery import discover,suggest_category_paths
from affiliate_hub_v31.tests.test_product_discovery import DiscoveryTests
from affiliate_hub_v31.catalog import Catalog


class SearchIndexTests(DiscoveryTests):
    def test_index_rebuild_preserves_campaigns_and_same_search_results(self):
        with Catalog(self.db) as cat:
            old=cat.stats()
            normal=discover(cat,topic="Air Fryer",category="Home Appliances",
                            campaign="novoblog",include_review=True,limit=12)
            before_paths=suggest_category_paths(cat,topic="Guarda Roupa")
            self.assertFalse(has_index(cat))
            report=rebuild_index(cat)
            self.assertTrue(has_index(cat))
            self.assertEqual(report["index_rows"],old["products"])
            indexed=discover(cat,topic="Air Fryer",category="Home Appliances",
                             campaign="novoblog",include_review=True,limit=12)
            after_paths=suggest_category_paths(cat,topic="Guarda Roupa")
            self.assertEqual(indexed,normal)
            self.assertEqual(after_paths,before_paths)
            self.assertEqual(cat.stats(),old)
            self.assertEqual(cat.cached_link("shopee:101:1","blogantigo"),
                             "https://s.shopee.com.br/link-real-antigo")

    def test_repeated_build_is_idempotent_and_does_not_duplicate_products(self):
        with Catalog(self.db) as cat:
            first=rebuild_index(cat)
            second=rebuild_index(cat)
            self.assertEqual(first["index_rows"],second["index_rows"])
            self.assertEqual(second["index_rows"],7)

    def test_invalid_fts_query_fails_to_nonindexed_fallback(self):
        with Catalog(self.db) as cat:
            self.assertIsNone(safe_match_expression(('x" OR 1=1 --',)))
            self.assertIsNone(safe_match_expression(('a',)*9))
            self.assertEqual(fts_condition(cat,("air","fryer")),("",[]))
            rebuild_index(cat)
            expression,params=fts_condition(cat,("air","fryer"))
            self.assertIn("v31_catalog_fts MATCH",expression)
            self.assertEqual(params,['"air" OR "fryer"'])
            self.assertEqual(fts_condition(cat,('x" OR 1=1 --',)),("",[]))


if __name__=="__main__":
    unittest.main()
