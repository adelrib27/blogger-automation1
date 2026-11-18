"""C34 universal inventory: 100% SKUs separados de elegibilidade comercial."""
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.source_category_index import create_source_category_schema
from affiliate_hub_v31.universal_inventory import (
    UniversalInventoryError, NO_OFFICIAL_CATEGORY, rebuild_universal_inventory,
)

class UniversalInventoryTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/"state.sqlite3"
        with Catalog(self.path) as cat:
            create_source_category_schema(cat)
            with cat.db:
                for i,(name,mod,tax,root,branch,source_status,reason) in enumerate((
                    ("Air Fryer Digital 5 litros","eligible","matched",
                     "home appliances","kitchen appliances","matched",""),
                    ("Guarda Roupa Casal","review","review",
                     "home living","furniture","matched","taxonomy_unclassified"),
                    ("Produto Antigo Sem Faceta","review","review",
                     "", "", None,"taxonomy_unclassified"),
                    ("Suplemento Vitamina","review","review",
                     "health","vitamins","matched","categoria_sensivel"),
                    ("Air Fryer Historico Protegido","eligible","matched",
                     "health","vitamins","matched",""),
                    ("Air Fryer Conflito de Fonte","eligible","matched",
                     "home appliances","kitchen appliances","conflict",""),
                    ("Air Fryer Dados Ruins","review","review",
                     "home appliances","kitchen appliances","matched",""),
                )):
                    key=f"shopee:{100+i}:{i+1}"
                    url=(f"https://shopee.com.br/product/{100+i}/{i+1}"
                        if i!=6 else "https://invalid.invalid/1")
                    cat.db.execute("""
                      INSERT INTO products(product_key,shop_id,item_id,title,
                        description,origin_url,image_url,moderation,moderation_reason,
                        first_source,last_seen_utc)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,str(100+i),str(i+1),name,"",url,
                         "https://cf.shopee.com.br/file/img",mod,reason,
                         "fixture","2026-11-18T00:00:00Z"))
                    cat.db.execute("""
                      INSERT INTO product_taxonomy
                      (product_key,category,niche,status,reason,version)
                      VALUES(?,?,?,?,?,?)
                    """,(key,"cozinha","air_fryers",tax,"fixture","test"))
                    if source_status:
                        cat.db.execute("""
                          INSERT INTO product_source_categories
                          (product_key,source,level1,level2,level3,status)
                          VALUES(?,?,?,?,?,?)
                        """,(key,"feed1",root,branch,"",source_status))
            cat.cache_link("shopee:100:1","campaign_original",
                           "https://s.shopee.com.br/verified-legacy")

    def test_every_product_is_indexed_and_original_rows_and_links_unchanged(self):
        with Catalog(self.path) as cat:
            before={table:cat.db.execute(
                f"SELECT * FROM {table} ORDER BY product_key").fetchall()
                for table in ("products","product_taxonomy","affiliate_links")}
            result=rebuild_universal_inventory(cat)
            after={table:cat.db.execute(
                f"SELECT * FROM {table} ORDER BY product_key").fetchall()
                for table in before}
            self.assertEqual(before,after)
            self.assertEqual(result["products_indexed"],7)
            self.assertEqual(result["inventory_approved_preexisting"],1)
            self.assertEqual(result["inventory_review_required"],4)
            self.assertEqual(result["inventory_legacy_blocked"],2)
            self.assertEqual(result["new_approvals"],0)
            self.assertEqual(result["converted"],0)
            self.assertEqual(result["publication_calls"],0)
            self.assertEqual(result["no_official_category"],2)
            self.assertTrue(result["source_classification_is_not_approval"])
            entries=cat.db.execute("""
              SELECT product_key,source_l1,source_l2,decision,can_convert
              FROM v31_universal_inventory ORDER BY product_key
            """).fetchall()
        self.assertEqual(entries[0][-2:],("approved",1))
        self.assertEqual(entries[1][-2:],("review_required",0))
        self.assertEqual(entries[2][1],NO_OFFICIAL_CATEGORY)
        self.assertEqual(entries[4][-2:],("legacy_source_blocked",0))
        self.assertEqual(entries[5][-2:],("legacy_source_blocked",0))
        self.assertEqual(entries[6][-2:],("review_required",0))

    def test_second_rebuild_is_idempotent_and_preserves_affiliate_links(self):
        with Catalog(self.path) as cat:
            first=rebuild_universal_inventory(cat)
            prior=cat.db.execute(
                "SELECT * FROM v31_universal_inventory ORDER BY product_key"
            ).fetchall()
            second=rebuild_universal_inventory(cat)
            after=cat.db.execute(
                "SELECT * FROM v31_universal_inventory ORDER BY product_key"
            ).fetchall()
            link=cat.db.execute(
                "SELECT affiliate_url FROM affiliate_links").fetchone()[0]
        self.assertEqual(prior,after)
        self.assertEqual(first,second)
        self.assertIn("verified-legacy",link)

    def test_no_origin_facets_fails_closed_without_created_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            with Catalog(Path(temp)/"legacy.sqlite3") as cat:
                with self.assertRaises(UniversalInventoryError):
                    rebuild_universal_inventory(cat)
                self.assertEqual(cat.db.execute("""
                    SELECT count(*) FROM sqlite_master
                    WHERE name='v31_universal_inventory'
                """).fetchone()[0],0)

    def test_official_category_is_not_editorial_approval(self):
        with Catalog(self.path) as cat:
            rebuild_universal_inventory(cat)
            result=cat.db.execute("""
              SELECT decision,can_convert,source_l1,source_l2
              FROM v31_universal_inventory WHERE product_key=?
            """,("shopee:101:2",)).fetchone()
        self.assertEqual(result,("review_required",0,"home living","furniture"))


if __name__=="__main__":
    unittest.main()
