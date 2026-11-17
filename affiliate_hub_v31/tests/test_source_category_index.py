"""C16: 2 CSV Shopee com categoria L1/L2/L3 e links por campanha intactos."""
import csv
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.source_category_index import (
    browse_source,import_source_categories,source_inventory,
    SourceCategoryError
)


class OfficialCategoryIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.db=self.root/"catalog.sqlite3"
        self.feed1=self.root/"100k.csv"
        self.feed2=self.root/"10k.csv"
        self.write_csv(self.feed1,["globalCategory3","globalCategory1","globalCategory2"],[
            ("1","Air Fryer Digital 5 litros",
             ("Air Fryers","Home Appliances","Kitchen Appliances")),
            ("2","Armário Estante Modular Sala de Jantar",
             ("Cupboards Cabinets","Home & Living","Furniture")),
            ("3","Calça Jeans Feminina",
             ("Pants","Women Clothes","Bottoms")),
        ])
        self.write_csv(self.feed2,["globalCategory1","globalCategory2"],[
            ("1","Air Fryer Digital 5 litros",("Home Appliances","Kitchen Appliances")),
            ("4","Notebook de Estudo",
             ("Computers & Accessories","Laptops")),
        ])
        with Catalog(self.db) as catalog:
            catalog.import_csv(self.feed1,"feed1")
            catalog.import_csv(self.feed2,"feed2")
            catalog.cache_link("shopee:100:1","blogold",
                               "https://s.shopee.com.br/old-verified")

    def write_csv(self,path,category_columns,records):
        names=["shopId","itemId","productName","productLink","imageUrl"]+category_columns
        with path.open("w",newline="",encoding="utf-8") as file:
            writer=csv.DictWriter(file,fieldnames=names)
            writer.writeheader()
            for item,title,cat in records:
                fields={
                    "shopId":"100","itemId":item,"productName":title,
                    "productLink":f"https://shopee.com.br/product/100/{item}",
                    "imageUrl":"https://cf.shopee.com.br/file/product",
                }
                fields.update(zip(category_columns,cat))
                writer.writerow(fields)

    def test_official_hierarchy_not_only_current_blog_categories(self):
        with Catalog(self.db) as cat:
            one=import_source_categories(cat,self.feed1,"feed1")
            two=import_source_categories(cat,self.feed2,"feed2")
            report=source_inventory(cat)
            self.assertEqual((one["new_category_records"],
                              two["new_category_records"]),(3,2))
            self.assertEqual(report["products_with_official_source_categories"],4)
            self.assertEqual(report["source_category_rows"],5)
            categories={d["label"] for d in report["level1_facets"]}
            self.assertIn("home living",categories)
            self.assertIn("computers accessories",categories)
            self.assertIn("home appliances",categories)
            self.assertTrue(cat.integrity())

    def test_unclassified_product_browsable_but_not_publishable(self):
        with Catalog(self.db) as cat:
            import_source_categories(cat,self.feed1,"feed1")
            rows=browse_source(cat,level1="Home & Living",level2="Furniture",
                               campaign="blogold")
            self.assertEqual(len(rows),1)
            self.assertFalse(rows[0]["editorial_approved"])
            self.assertFalse(rows[0]["affiliate_ready"])
            self.assertNotIn("affiliate_url",rows[0])

    def test_different_campaign_never_receives_previous_affiliate_url(self):
        with Catalog(self.db) as cat:
            import_source_categories(cat,self.feed1,"feed1")
            import_source_categories(cat,self.feed2,"feed2")
            previous=browse_source(cat,level1="Home Appliances",
                                   campaign="blogold")
            new=browse_source(cat,level1="Home Appliances",
                              campaign="newblogcampaign")
            self.assertEqual(len(previous),1)
            self.assertEqual(previous[0]["affiliate_url"],
                             "https://s.shopee.com.br/old-verified")
            self.assertFalse(new[0]["affiliate_ready"])
            self.assertNotIn("affiliate_url",new[0])
            self.assertEqual(cat.stats()["cached_affiliate_links"],1)

    def test_reimport_idempotent_and_never_changes_editorial_decisions(self):
        with Catalog(self.db) as cat:
            before=cat.stats()
            import_source_categories(cat,self.feed1,"feed1")
            again=import_source_categories(cat,self.feed1,"feed1")
            self.assertEqual(again["new_category_records"],0)
            self.assertEqual(again["duplicates_same_category"],3)
            self.assertEqual(cat.stats(),before)
            self.assertIsNone(cat.for_conversion("shopee:100:2"))

    def test_conflict_in_same_source_quarantines_source_facet(self):
        conflicting=self.root/"conflict.csv"
        self.write_csv(conflicting,
                       ["globalCategory3","globalCategory1","globalCategory2"],
                       [("1","Air Fryer Digital 5 litros",
                         ("Air Fryers","Unknown Category","Kitchen Appliances"))])
        with Catalog(self.db) as cat:
            import_source_categories(cat,self.feed1,"feed1")
            changed=import_source_categories(cat,conflicting,"feed1")
            self.assertEqual(changed["category_conflicts"],1)
            self.assertEqual(browse_source(cat,level1="Home Appliances"),[])
            self.assertEqual(cat.cached_link("shopee:100:1","blogold"),
                             "https://s.shopee.com.br/old-verified")

    def test_source_categories_cannot_create_phantom_products(self):
        ghost=self.root/"ghost.csv"
        self.write_csv(ghost,["globalCategory1","globalCategory2"],[
            ("999","Smartphone Inexistente",("Mobile Gadgets","Smartphones"))])
        with Catalog(self.db) as cat:
            old=cat.stats()
            data=import_source_categories(cat,ghost,"feed1")
            self.assertEqual(data["not_in_current_catalog"],1)
            self.assertEqual(cat.stats(),old)

    def test_missing_official_category_headers_fail_closed(self):
        file=self.root/"missing.csv"
        file.write_text("shopId,itemId,productName,productLink,imageUrl\n"
                        "100,4,Notebook,https://shopee.com.br/product/100/4,"
                        "https://cf.shopee.com.br/file/p\n",encoding="utf-8")
        with Catalog(self.db) as cat:
            with self.assertRaisesRegex(SourceCategoryError,
                                        "official_level1_missing"):
                import_source_categories(cat,file,"feed3")


if __name__=="__main__":
    unittest.main()
