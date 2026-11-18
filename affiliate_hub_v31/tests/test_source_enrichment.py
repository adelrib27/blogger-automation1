"""C16: migração de categorias é aditiva; produtos e links são intocáveis."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.source_enrichment import (
    EnrichmentError,enrich,protected_fingerprint
)


class LocalStorage:
    def __init__(self, data: bytes):
        self.snapshot=data
        self.saves=0

    def restore_to(self, destination):
        Path(destination).write_bytes(self.snapshot)
        return True

    def save_from(self, source):
        self.snapshot=Path(source).read_bytes()
        self.saves+=1
        return {"state_saved":True,"retention_pending":False}


class SourceEnrichmentTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.database=self.root/"base.sqlite3"
        self.feed1=self.root/"feed1.csv"
        self.feed2=self.root/"feed2.csv"
        self.make_feed(self.feed1,["globalCategory1","globalCategory2","globalCategory3"],[
            ("1","Air Fryer Elétrica",["Home Appliances","Kitchen Appliances","Air Fryers"]),
            ("2","Calça Jeans",["Women Clothes","Bottoms","Pants"]),
        ])
        self.make_feed(self.feed2,["globalCategory1","globalCategory2"],[
            ("3","Armário para Quarto",["Home & Living","Furniture"])
        ])
        with Catalog(self.database) as c:
            c.import_csv(self.feed1,"feed1")
            c.import_csv(self.feed2,"feed2")
            c.cache_link("shopee:123:1","oldblog",
                         "https://s.shopee.com.br/verified-old")
            self.original_stats=c.stats()
            self.original_hash=protected_fingerprint(c)
        self.storage=LocalStorage(self.database.read_bytes())

    def make_feed(self,path,levels,rows):
        with path.open("w",newline="",encoding="utf-8") as f:
            columns=["shopId","itemId","productName","productLink","imageUrl"]+levels
            w=csv.DictWriter(f,fieldnames=columns)
            w.writeheader()
            for num,title,categories in rows:
                row={"shopId":"123","itemId":num,"productName":title,
                     "productLink":f"https://shopee.com.br/product/123/{num}",
                     "imageUrl":"https://cf.shopee.com.br/file/p"}
                row.update(zip(levels,categories))
                w.writerow(row)

    def test_dry_run_never_saves_and_protected_data_remain_original(self):
        report=enrich(self.storage,(self.feed1,self.feed2))
        self.assertEqual(report["category_index"]
                         ["products_with_official_source_categories"],3)
        self.assertEqual(report["original_affiliate_links_preserved"],1)
        self.assertFalse(report["snapshot_saved_and_restored"])
        self.assertEqual(self.storage.saves,0)
        with Catalog(self.database) as c:
            self.assertEqual(c.stats(),self.original_stats)
            self.assertEqual(protected_fingerprint(c),self.original_hash)
            self.assertIsNone(c.db.execute("""
                SELECT name FROM sqlite_master WHERE name='product_source_categories'
            """).fetchone())

    def test_save_once_restores_and_retains_all_prior_affiliate_urls(self):
        report=enrich(self.storage,(self.feed1,self.feed2),execute=True)
        self.assertTrue(report["snapshot_saved_and_restored"])
        self.assertEqual(self.storage.saves,1)
        with tempfile.TemporaryDirectory() as temp:
            db=Path(temp)/"verified.sqlite3"
            self.storage.restore_to(db)
            with Catalog(db) as c:
                self.assertEqual(protected_fingerprint(c),self.original_hash)
                self.assertEqual(c.cached_link("shopee:123:1","oldblog"),
                                 "https://s.shopee.com.br/verified-old")
                self.assertEqual(c.db.execute(
                    "SELECT COUNT(*) FROM product_source_categories"
                ).fetchone()[0],3)

    def test_new_feed_products_block_real_save_but_report_dry_run(self):
        extra=self.root/"new.csv"
        self.make_feed(extra,["globalCategory1","globalCategory2"],[
            ("999","Smartphone não registrado",["Mobile Gadgets","Phones"])
        ])
        report=enrich(self.storage,(self.feed1,extra),execute=False)
        self.assertEqual(report["feeds"][1]["not_in_current_catalog"],1)
        with self.assertRaisesRegex(EnrichmentError,"resynchronize_first"):
            enrich(self.storage,(self.feed1,extra),execute=True)
        self.assertEqual(self.storage.saves,0)


if __name__=="__main__":
    unittest.main()
