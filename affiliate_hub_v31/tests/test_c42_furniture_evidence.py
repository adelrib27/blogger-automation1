"""C42: nova rota por título+faceta oficial, sem aprovação por categoria isolada."""
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.safe_reclassification import find_candidates,reclassify
from affiliate_hub_v31.source_category_index import create_source_category_schema
from affiliate_hub_v31.taxonomy import classify_title


class FurnitureEvidenceTests(unittest.TestCase):
    def test_specific_phrases_and_accessories(self):
        for title in ("Mesa de Jantar Madeira Macica 6 Lugares", "Sofá Retrátil 3 Lugares",
                      "Guarda Roupa Casal 6 Portas", "Cadeira de Escritório Ergonômica"):
            with self.subTest(title=title):
                route=classify_title(title)
                self.assertEqual((route.category,route.niche,route.status),
                                 ("casa","moveis","matched"))
        for title in ("Capa para Sofá Retrátil", "Puxador para Armário Multiuso",
                      "Miniatura Mesa de Jantar", "Sofá Qualquer"):
            with self.subTest(title=title):
                self.assertEqual(classify_title(title).status,"review")

    def test_furniture_only_promoted_with_two_independent_signals(self):
        rows=[
            ("Mesa de Jantar Madeira Macica 6 Lugares","home living","furniture",
             "taxonomy_unclassified","matched"),
            ("Mesa de Jantar Madeira Macica 6 Lugares","home living","kitchenware",
             "taxonomy_unclassified","matched"),
            ("Mesa de Jantar Madeira Macica 6 Lugares","health","vitamins",
             "taxonomy_unclassified","matched"),
            ("Mesa de Jantar Madeira Macica 6 Lugares","home living","furniture",
             "manual_review","matched"),
            ("Mesa de Jantar Madeira Macica 6 Lugares","home living","furniture",
             "taxonomy_unclassified","conflict"),
            ("Capa para Sofá Retrátil","home living","furniture",
             "taxonomy_unclassified","matched"),
        ]
        with tempfile.TemporaryDirectory() as td:
            with Catalog(Path(td)/"catalog.sqlite3") as cat:
                create_source_category_schema(cat)
                with cat.db:
                    for i,(title,l1,l2,reason,status) in enumerate(rows):
                        key=f"shopee:{100+i}:{200+i}"
                        cat.db.execute("""
                         INSERT INTO products
                         (product_key,shop_id,item_id,title,description,origin_url,
                         image_url,moderation,moderation_reason,first_source,last_seen_utc)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?)
                        """,(key,str(100+i),str(200+i),title,"",
                             f"https://shopee.com.br/product/{100+i}/{200+i}",
                             "https://cdn.shopee.com.br/test","review",reason,
                             "feed1","2026-11-18T00:00:00Z"))
                        cat.db.execute("""
                         INSERT INTO product_taxonomy
                         (product_key,category,niche,status,reason,version)
                         VALUES(?,?,?,?,?,?)
                        """,(key,"","","review","unclassified",
                             "v31-editorial-taxonomy-2"))
                        cat.db.execute("""
                         INSERT INTO product_source_categories
                         (product_key,source,level1,level2,level3,status)
                         VALUES(?,?,?,?,?,?)
                        """,(key,"feed1",l1,l2,"",status))
                before=cat.stats()
                candidates,counts=find_candidates(cat)
                self.assertEqual(counts["supported_review_candidates"],1)
                self.assertEqual(len(candidates),1)
                self.assertEqual(candidates[0]["new_niche"],"moveis")
                self.assertEqual(cat.stats(),before)
                first=reclassify(cat,execute=True,limit=10)
                self.assertEqual(first["approved_this_batch"],1)
                self.assertEqual(cat.stats()["eligible"],1)
                self.assertEqual(cat.stats()["review"],5)
                self.assertEqual(reclassify(cat,execute=True)["approved_this_batch"],0)
                self.assertEqual(cat.db.execute(
                    "SELECT COUNT(*) FROM v31_taxonomy_reclassification_audit"
                ).fetchone()[0],1)


if __name__=="__main__":
    unittest.main()
