"""C18: categorias protegidas e divergências entre fontes são auditáveis."""
import csv
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.curation_audit import audit
from affiliate_hub_v31.source_category_index import import_source_categories


class CurationAuditTests(unittest.TestCase):
    def test_cross_feed_conflicts_are_counted_not_auto_approved(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            db=root/"catalog.sqlite3"
            def emit(name,records):
                file=root/name
                with file.open("w",encoding="utf-8",newline="") as stream:
                    w=csv.DictWriter(stream,fieldnames=[
                        "shopId","itemId","productName","productLink","imageUrl",
                        "globalCategory1","globalCategory2"
                    ])
                    w.writeheader()
                    for num,title,a,b in records:
                        w.writerow({"shopId":"100","itemId":num,
                            "productName":title,
                            "productLink":f"https://shopee.com.br/product/100/{num}",
                            "imageUrl":"https://cf.shopee.com.br/file/test",
                            "globalCategory1":a,"globalCategory2":b})
                return file
            f1=emit("one.csv",[
                ("1","Air Fryer Digital","Home Appliances","Kitchen Appliances"),
                ("2","Produto saúde","Health","Vitamins"),
                ("3","Organizador de Cozinha","Home & Living","Storage"),
            ])
            f2=emit("two.csv",[
                ("1","Air Fryer Digital","Food & Beverages","Other"),
                ("3","Organizador de Cozinha","Home & Living","Furniture"),
            ])
            with Catalog(db) as cat:
                cat.import_csv(f1,"feed1")
                cat.import_csv(f2,"feed2")
                import_source_categories(cat,f1,"feed1")
                import_source_categories(cat,f2,"feed2")
                result=audit(cat)
            self.assertEqual(result["conflicting_root_categories_across_sources"],1)
            self.assertEqual(result["conflicting_l1_l2_branches_across_sources"],2)
            self.assertEqual(result["products_with_multiple_source_records"],2)
            protected={x["category"] for x in result["protected_roots_not_automatically_promotable"]}
            self.assertIn("health",protected)
            self.assertIn("food beverages",protected)
            self.assertEqual(result["publication_calls"],0)
            self.assertEqual(result["existing_affiliate_links_preserved"],0)
            self.assertEqual(result["product_identifiers_reported"],0)


if __name__=="__main__":
    unittest.main()
