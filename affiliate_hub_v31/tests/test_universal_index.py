"""C15 — catálogo global por categoria/nicho, inclusive revisão, sem blog."""
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.universal_index import (
    IndexErrorV31, grouped_inventory, lookup,
)


class GlobalIndexTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db=Path(tmp.name)/"catalog.sqlite3"
        with Catalog(self.db) as c:
            with c.db:
                records=[
                    ("shopee:100:200","Cafeteira Espresso de Bancada",
                     "cozinha","eletroportateis","eligible","matched"),
                    ("shopee:101:201","Escova Secadora de Cabelo",
                     "beleza","cabelos","eligible","matched"),
                    ("shopee:102:202","Produto de Nicho Futuro Desconhecido",
                     "","","review","review")
                ]
                for n,(key,title,category,niche,moderation,status) in enumerate(records):
                    c.db.execute("""
                        INSERT INTO products
                         (product_key,shop_id,item_id,title,description,
                          origin_url,image_url,moderation,moderation_reason,
                          first_source,last_seen_utc)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,str(100+n),str(200+n),title,"",
                         f"https://shopee.com.br/product/{100+n}/{200+n}",
                         "https://cf.shopee.com.br/file/photo",moderation,"",
                         "csv_110k","2026-11-17T00:00:00Z"))
                    c.db.execute("""
                        INSERT INTO product_taxonomy
                          (product_key,category,niche,status,reason,version)
                        VALUES(?,?,?,?,?,?)
                    """,(key,category,niche,status,"fixture","v31-test"))

    def test_all_products_grouped_even_when_topic_not_known(self):
        with Catalog(self.db) as c:
            result=grouped_inventory(c)
        self.assertEqual(sum(x["products"] for x in result),3)
        self.assertEqual(len(result),3)
        self.assertEqual(next(x["state"] for x in result
                         if x["category"]=="revisao_pendente"),"review")
        self.assertEqual(next(x["niche"] for x in result
                         if x["category"]=="beleza"),"cabelos")

    def test_reviewed_and_conflicting_taxonomies_share_one_review_bucket(self):
        with Catalog(self.db) as c:
            with c.db:
                c.db.execute("""
                    UPDATE product_taxonomy SET category='moda',niche='roupas'
                    WHERE product_key='shopee:102:202'
                """)
                c.db.execute("""
                    INSERT INTO products
                    (product_key,shop_id,item_id,title,description,origin_url,
                     image_url,moderation,moderation_reason,first_source,last_seen_utc)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,("shopee:103:203","103","203","Outra classificação pendente","",
                     "https://shopee.com.br/product/103/203",
                     "https://cf.shopee.com.br/file/photo","review","",
                     "csv_110k","2026-11-17T00:00:00Z"))
                c.db.execute("""
                    INSERT INTO product_taxonomy
                    (product_key,category,niche,status,reason,version)
                    VALUES(?,?,?,?,?,?)
                """,("shopee:103:203","tecnologia","gadgets","review",
                     "ambiguous","v31-test"))
            rows=grouped_inventory(c)
        self.assertEqual(sum(x["products"] for x in rows),4)
        pending=[x for x in rows if x["state"]=="review"]
        self.assertEqual(len(pending),1)
        self.assertEqual(pending[0]["products"],2)

    def test_blog_that_does_not_exist_can_choose_category_and_query(self):
        with Catalog(self.db) as c:
            result=lookup(c,category="cozinha",query="cafeteira espresso")
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["title"],"Cafeteira Espresso de Bancada")
        self.assertNotIn("affiliate_url",result[0])
        self.assertNotIn("affiliate_ready",result[0])

    def test_category_lookup_does_not_infer_other_blog_campaign(self):
        with Catalog(self.db) as c:
            c.cache_link("shopee:100:200","campaignold",
                         "https://s.shopee.com.br/real-old-link")
            a=lookup(c,category="cozinha",campaign="campaignold")
            b=lookup(c,category="cozinha",campaign="campaignnew")
            self.assertTrue(a[0]["affiliate_ready"])
            self.assertEqual(a[0]["affiliate_url"],
                             "https://s.shopee.com.br/real-old-link")
            self.assertFalse(b[0]["affiliate_ready"])
            self.assertNotIn("affiliate_url",b[0])

    def test_products_pending_review_never_returned_to_blog(self):
        with Catalog(self.db) as c:
            self.assertEqual(lookup(c,query="nicho futuro desconhecido"),[])
            self.assertEqual(len(lookup(c,niche="cabelos")),1)

    def test_requires_explicit_topic_not_guesswork(self):
        with Catalog(self.db) as c:
            with self.assertRaisesRegex(IndexErrorV31,"search_constraint_required"):
                lookup(c)
            with self.assertRaisesRegex(IndexErrorV31,"limit_invalid"):
                lookup(c,category="cozinha",limit=101)


if __name__=="__main__":
    unittest.main()
