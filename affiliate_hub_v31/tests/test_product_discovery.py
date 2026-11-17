"""C18: seleção temática independente de blogs, sem publicar nem cruzar campanhas."""
import csv
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.product_discovery import discover,DiscoveryError
from affiliate_hub_v31.source_category_index import import_source_categories


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.db=self.root/"catalog.sqlite3"
        self.feed1=self.write("feed1.csv",[
            ("101","1","Air Fryer Digital 5 litros","Home Appliances","Kitchen Appliances"),
            ("101","2","Air Fryer Digital 6 litros","Home Appliances","Kitchen Appliances"),
            ("202","3","Air Fryer Digital 4 litros","Home Appliances","Kitchen Appliances"),
            ("303","4","Air Fryer 3 litros","Home Appliances","Kitchen Appliances"),
            ("404","5","Guarda Roupa Casal 4 Portas","Home & Living","Furniture"),
            ("505","6","Air Fryer Digital Saúde","Health","Nutritional"),
            ("606","7","Air Fryer Compacta","Home Appliances","Kitchen Appliances"),
        ])
        self.feed2=self.write("feed2.csv",[
            ("101","1","Air Fryer Digital 5 litros","Home Appliances","Kitchen Appliances"),
        ])
        with Catalog(self.db) as cat:
            cat.import_csv(self.feed1,"feed1")
            cat.import_csv(self.feed2,"feed2")
            import_source_categories(cat,self.feed1,"feed1")
            import_source_categories(cat,self.feed2,"feed2")
            cat.cache_link("shopee:101:1","blogantigo",
                           "https://s.shopee.com.br/link-real-antigo")
            cat.cache_link("shopee:202:3","novoblog",
                           "https://s.shopee.com.br/link-real-novoblog")

    def write(self,name,records):
        f=self.root/name
        with f.open("w",encoding="utf-8",newline="") as handle:
            w=csv.DictWriter(handle,fieldnames=[
                "shopId","itemId","productName","productLink","imageUrl",
                "globalCategory1","globalCategory2"
            ])
            w.writeheader()
            for shop,item,title,l1,l2 in records:
                w.writerow({
                    "shopId":shop,"itemId":item,
                    "productName":title,
                    "productLink":f"https://shopee.com.br/product/{shop}/{item}",
                    "imageUrl":"https://cf.shopee.com.br/file/photo",
                    "globalCategory1":l1,"globalCategory2":l2,
                })
        return f

    def test_new_blog_cannot_receive_old_campaign_link(self):
        with Catalog(self.db) as c:
            results=discover(c,topic="Air Fryer Digital",
                             category="Home Appliances",campaign="novoblog",
                             limit=6)
        self.assertTrue(results)
        self.assertTrue(all(x["curation"]=="approved" for x in results))
        self.assertTrue(all(x["can_publish"] is False for x in results))
        self.assertTrue(all(not x["commercial_metrics_available"] for x in results))
        self.assertTrue(all(x["affiliate_url"]!="https://s.shopee.com.br/link-real-antigo"
                            for x in results))
        selected=next(x for x in results if x["product_key"]=="shopee:202:3")
        self.assertEqual(selected["affiliate_status"],"verified_for_campaign")
        noncached=next(x for x in results if x["product_key"]=="shopee:101:1")
        self.assertIsNone(noncached["affiliate_url"])
        self.assertEqual(noncached["affiliate_status"],"requires_conversion")

    def test_no_campaign_never_creates_a_link_and_preserves_shop_diversity(self):
        with Catalog(self.db) as c:
            found=discover(c,topic="Air Fryer",limit=10,max_per_shop=1)
        self.assertEqual(len(set(x["shop_id"] for x in found)),len(found))
        self.assertEqual(sum(bool(x["affiliate_url"]) for x in found),0)
        self.assertTrue(all(x["affiliate_status"]=="campaign_not_selected"
                            for x in found))
        self.assertNotIn("shopee:505:6",[x["product_key"] for x in found])

    def test_unclassified_products_available_for_review_not_auto_publishing(self):
        with Catalog(self.db) as c:
            self.assertEqual(discover(c,topic="Guarda Roupa",category="Home & Living"),[])
            reviewed=discover(c,topic="Guarda Roupa",
                              category="Home & Living",
                              campaign="novoblog",include_review=True)
        self.assertEqual(len(reviewed),1)
        self.assertEqual(reviewed[0]["curation"],"review_required")
        self.assertEqual(reviewed[0]["affiliate_status"],"review_required")
        self.assertIsNone(reviewed[0]["affiliate_url"])
        self.assertFalse(reviewed[0]["can_publish"])

    def test_protected_category_blocks_even_legacy_approved_title(self):
        with Catalog(self.db) as c:
            blocked=discover(c,topic="Air Fryer",category="Health")
            review=discover(c,topic="Air Fryer",category="Health",
                            include_review=True)
        self.assertEqual(blocked,[])
        self.assertEqual(len(review),1)
        self.assertEqual(review[0]["curation"],"review_required")

    def test_conflicting_source_categories_fail_closed(self):
        different=self.write("conflict.csv",[
            ("101","1","Air Fryer Digital 5 litros","Home Appliances","Other"),
        ])
        with Catalog(self.db) as cat:
            import_source_categories(cat,different,"feed_other")
            found=discover(cat,topic="Air Fryer",category="Home Appliances",
                           include_review=True)
        self.assertNotIn("shopee:101:1",[x["product_key"] for x in found])

    def test_no_meaningful_topic_raises(self):
        with Catalog(self.db) as c:
            for q in ("", "de para com", "  "):
                with self.subTest(q=q),self.assertRaises(DiscoveryError):
                    discover(c,topic=q)
            with self.assertRaisesRegex(DiscoveryError,"subcategory_requires_parent"):
                discover(c,topic="Air Fryer",subcategory="Kitchen Appliances")


if __name__=="__main__":
    unittest.main()
