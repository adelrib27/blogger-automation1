"""C39 — só altera histórico com duas evidências e política limpa."""
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.safe_reclassification import (
    ReclassificationError,reclassify,find_candidates,
)
from affiliate_hub_v31.source_category_index import create_source_category_schema

ROWS=[
  # name, src L1, L2, reason, src status, product status, tax status
  ("Air Fryer 5 Litros Digital","home appliances","kitchen appliances",
   "taxonomy_unclassified","matched","review","review"),
  ("Organizador de Cozinha Inox","home living","kitchenware",
   "taxonomy_ambiguous_niches","matched","review","review"),
  ("Air Fryer Health","health","vitamins",
   "taxonomy_unclassified","matched","review","review"),
  ("Air Fryer Medicamento","home appliances","kitchen appliances",
   "taxonomy_unclassified","matched","review","review"),
  ("Air Fryer Sem Fonte","","",
   "taxonomy_unclassified",None,"review","review"),
  ("Air Fryer Revisão Humana","home appliances","kitchen appliances",
   "manual_hold","matched","review","review"),
  ("Air Fryer Origem Conflito","home appliances","kitchen appliances",
   "taxonomy_unclassified","conflict","review","review"),
  ("Air Fryer Histórico Aprovado","home appliances","kitchen appliances",
   "","matched","eligible","matched"),
]


class SafeReclassificationTests(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.path=Path(td.name)/"db.sqlite3"
        with Catalog(self.path) as cat:
            create_source_category_schema(cat)
            with cat.db:
                for idx,(title,l1,l2,reason,status,mod,tax) in enumerate(ROWS):
                    shop=str(idx+101)
                    item=str(idx+201)
                    key=f"shopee:{shop}:{item}"
                    cat.db.execute("""
                      INSERT INTO products(product_key,shop_id,item_id,title,
                        description,origin_url,image_url,moderation,
                        moderation_reason,first_source,last_seen_utc)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,shop,item,title,"",
                        f"https://shopee.com.br/product/{shop}/{item}",
                        "https://cf.shopee.com.br/file/img",mod,reason,
                        "first","2026-11-18T00:00:00Z"))
                    cat.db.execute("""
                      INSERT INTO product_taxonomy(product_key,category,niche,
                        status,reason,version) VALUES(?,?,?,?,?,?)
                    """,(key,"","",tax,reason,"v31-test-old"))
                    if status:
                        cat.db.execute("""
                          INSERT INTO product_source_categories
                          (product_key,source,level1,level2,level3,status)
                          VALUES(?,?,?,?,?,?)
                        """,(key,"feed1",l1,l2,"",status))
            cat.cache_link("shopee:108:208","blogantigo",
                           "https://s.shopee.com.br/old-affiliate")
        self.legacylink="https://s.shopee.com.br/old-affiliate"

    def test_dry_run_does_not_promote_or_mutate_links(self):
        with Catalog(self.path) as cat:
            before=cat.stats()
            report=reclassify(cat,limit=20)
            after=cat.stats()
        self.assertEqual(before,after)
        self.assertEqual(report["supported_candidates_total"],2)
        self.assertEqual(report["approved_this_batch"],0)
        self.assertEqual(report["proposed_this_batch"],2)
        self.assertEqual(report["publication_calls"],0)
        self.assertTrue(report["old_affiliate_links_preserved"])

    def test_execute_is_idempotent_and_preserves_existing_links(self):
        with Catalog(self.path) as cat:
            report=reclassify(cat,execute=True,limit=10)
            self.assertEqual(report["approved_this_batch"],2)
            self.assertEqual(cat.stats()["eligible"],3)
            self.assertEqual(cat.cached_link("shopee:108:208","blogantigo"),
                             self.legacylink)
            approved=cat.db.execute("""
              SELECT COUNT(*) FROM v31_taxonomy_reclassification_audit
            """).fetchone()[0]
            self.assertEqual(approved,2)
            repeat=reclassify(cat,execute=True,limit=10)
            self.assertEqual(repeat["approved_this_batch"],0)
            self.assertEqual(cat.stats()["eligible"],3)
            for idx in (3,4,5,6,7):
                key=f"shopee:{100+idx}:{200+idx}"
                self.assertIsNone(cat.for_conversion(key))

    def test_only_explicit_source_to_title_route_promotes(self):
        with Catalog(self.path) as cat:
            selected,count=find_candidates(cat,limit=1)
            self.assertEqual(len(selected),1)
            self.assertEqual(count["supported_review_candidates"],2)
            self.assertEqual(selected[0]["new_category"],"cozinha")
            self.assertIn(selected[0]["new_niche"],
                          {"air_fryers","organizacao_utensilios"})

    def test_invalid_budget_and_missing_official_categories_fail_closed(self):
        with Catalog(self.path) as cat:
            for bad in (0,101,-1,True,"10"):
                with self.subTest(bad=bad),self.assertRaises(ReclassificationError):
                    reclassify(cat,limit=bad)
        with tempfile.TemporaryDirectory() as td:
            with Catalog(Path(td)/"legacy.sqlite3") as cat:
                with self.assertRaises(ReclassificationError):
                    reclassify(cat)


if __name__=="__main__":
    unittest.main()
