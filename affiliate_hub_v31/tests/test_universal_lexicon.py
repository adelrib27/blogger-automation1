"""C35: categoria/nicho universal nasce dos próprios títulos e facetas."""
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.source_category_index import create_source_category_schema
from affiliate_hub_v31.universal_inventory import rebuild_universal_inventory
from affiliate_hub_v31.universal_lexicon import (
    LexiconError,build_lexicon,paths_for_topic,
)

ROWS=[
    ("Mesa de Jantar Madeira","home living","furniture"),
    ("Mesa de Cozinha Vidro","home living","furniture"),
    ("Mesa de Sala Redonda","home living","furniture"),
    ("Furadeira Eletrica Potente","home living","tools home improvement"),
    ("Furadeira Sem Fio","home living","tools home improvement"),
    ("Carabina Pressao Alta","sports outdoors","sports outdoor recreation equipments"),
    ("Carabina Pressao Forte","sports outdoors","sports outdoor recreation equipments"),
    ("Shampoo Cuidados Cabelo","health","vitamins"),
    ("Shampoo Capilar","health","vitamins"),
]


class UniversalLexiconTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.catalog=self.root/"catalog.sqlite3"
        self.sidecar=self.root/"lexicon.sqlite3"
        with Catalog(self.catalog) as cat:
            create_source_category_schema(cat)
            with cat.db:
                for i,(title,l1,l2) in enumerate(ROWS):
                    shop=str(110+i)
                    key=f"shopee:{shop}:{i+1}"
                    cat.db.execute("""
                      INSERT INTO products(product_key,shop_id,item_id,title,
                        description,origin_url,image_url,moderation,moderation_reason,
                        first_source,last_seen_utc)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,shop,str(i+1),title,"",
                         f"https://shopee.com.br/product/{shop}/{i+1}",
                         "https://cf.shopee.com.br/file/image",
                         "review","taxonomy_unclassified","sample",
                         "2026-11-18T00:00:00Z"))
                    cat.db.execute("""
                      INSERT INTO product_taxonomy
                      (product_key,category,niche,status,reason,version)
                      VALUES(?,?,?,?,?,?)
                    """,(key,"","","review","unclassified","fixture"))
                    cat.db.execute("""
                      INSERT INTO product_source_categories
                      (product_key,source,level1,level2,level3,status)
                      VALUES(?,?,?,?,?,?)
                    """,(key,"feed1",l1,l2,"","matched"))
        with Catalog(self.catalog) as cat, closing(sqlite3.connect(self.sidecar)) as index, index:
            rebuild_universal_inventory(cat,sidecar=index)

    def test_dynamic_paths_from_unanticipated_titles(self):
        before=self.catalog.read_bytes()
        with Catalog(self.catalog) as cat, closing(sqlite3.connect(self.sidecar)) as index, index:
            report=build_lexicon(cat.db,index,min_products=2,min_shops=2)
            furniture=paths_for_topic(index,"mesa")
            tools=paths_for_topic(index,"furadeira eletrica")
            blocked=paths_for_topic(index,"carabina pressao")
        self.assertEqual(self.catalog.read_bytes(),before)
        self.assertEqual(report["new_approvals"],0)
        self.assertEqual(report["affiliate_conversions"],0)
        self.assertEqual(report["publications"],0)
        self.assertTrue(furniture)
        self.assertEqual(furniture[0]["category_l2"],"furniture")
        self.assertEqual(tools[0]["category_l2"],"tools home improvement")
        self.assertFalse(blocked)
        self.assertFalse(furniture[0]["publication_approved"])
        self.assertTrue(furniture[0]["is_review_signal_only"])

    def test_rebuild_idempotent_and_source_policy_protected(self):
        with Catalog(self.catalog) as cat, closing(sqlite3.connect(self.sidecar)) as index, index:
            first=build_lexicon(cat.db,index,min_products=2,min_shops=2)
            previous=index.execute("""
              SELECT * FROM v31_universal_title_lexicon ORDER BY source_l1,source_l2,term
            """).fetchall()
            second=build_lexicon(cat.db,index,min_products=2,min_shops=2)
            after=index.execute("""
              SELECT * FROM v31_universal_title_lexicon ORDER BY source_l1,source_l2,term
            """).fetchall()
        self.assertEqual(previous,after)
        self.assertEqual(first,second)
        self.assertNotIn("health",str(previous))
        self.assertNotIn("carabina",str(previous))

    def test_thresholds_and_input_limits_fail_closed(self):
        with Catalog(self.catalog) as cat, closing(sqlite3.connect(self.sidecar)) as index, index:
            with self.assertRaises(LexiconError):
                build_lexicon(cat.db,index,min_products=1,min_shops=2)
            with self.assertRaises(LexiconError):
                paths_for_topic(index,topic="",limit=10)
            with self.assertRaises(LexiconError):
                paths_for_topic(index,topic="furadeira",limit=31)


if __name__=="__main__":
    unittest.main()
