"""Regressão SAFE — python -m unittest discover -s affiliate_hub_v31/tests -v."""
import csv
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog, classify, fields, host_allowed, ids_from_url


class CatalogSafeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dbpath = self.root / "catalog.sqlite3"

    def feed(self, name, records):
        path = self.root / name
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["itemId", "shopId", "productName", "productLink", "imageUrl", "productDescription"])
            writer.writeheader()
            writer.writerows(records)
        return path

    def product(self, iid="101", shop="202", title="Organizador de Cozinha"):
        return dict(itemId=iid, shopId=shop, productName=title,
                    productLink=f"https://shopee.com.br/produto-i.{shop}.{iid}",
                    imageUrl="https://cf.shopee.com.br/imagem.jpg", productDescription="Uso doméstico")

    def test_import_dedup_across_feeds_and_reruns(self):
        path1 = self.feed("feed1.csv", [self.product(), self.product("102")])
        path2 = self.feed("feed2.csv", [self.product("102"), self.product("103")])
        with Catalog(self.dbpath) as cat:
            one = cat.import_csv(path1, "feed1")
            two = cat.import_csv(path2, "feed2")
            again = cat.import_csv(path1, "feed1")
            self.assertEqual((one["added"], two["added"], two["duplicates"], again["added"]), (2, 1, 1, 0))
            self.assertEqual(cat.stats()["products"], 3)
            self.assertEqual(cat.stats()["eligible"], 3)
            self.assertTrue(cat.integrity())

    def test_sensitive_product_must_be_reviewed(self):
        path = self.feed("sensitive.csv", [self.product(title="Creatina em pó"), self.product("102")])
        with Catalog(self.dbpath) as cat:
            result = cat.import_csv(path, "sensitive")
            self.assertEqual(result["review"], 1)
            self.assertEqual(cat.stats()["eligible"], 1)
            self.assertEqual(len(cat.candidates("blogger")), 1)

    def test_malformed_feed_rolls_back_all_rows(self):
        path = self.root / "bad.csv"
        path.write_text("productName,productLink,imageUrl\n"
                        "Válido,https://shopee.com.br/item-i.202.101,https://cdn.test/image.jpg\n"
                        "Falta coluna,https://shopee.com.br/item-i.202.102\n", encoding="utf-8")
        with Catalog(self.dbpath) as cat:
            with self.assertRaises(ValueError):
                cat.import_csv(path, "feed_bad")
            self.assertEqual(cat.stats()["products"], 0)

    def test_limit_exceeded_rolls_back(self):
        path = self.feed("limit.csv", [self.product(), self.product("102")])
        with Catalog(self.dbpath) as cat:
            with self.assertRaises(ValueError):
                cat.import_csv(path, "feed", max_rows=1)
            self.assertEqual(cat.stats()["products"], 0)

    def test_missing_header_rejected(self):
        path = self.root / "missing.csv"
        path.write_text("title,price\nFoo,10\n", encoding="utf-8")
        with Catalog(self.dbpath) as cat:
            with self.assertRaises(ValueError):
                cat.import_csv(path, "feed")

    def test_cache_per_campaign_cannot_be_overwritten(self):
        path = self.feed("cache.csv", [self.product()])
        with Catalog(self.dbpath) as cat:
            cat.import_csv(path, "feed")
            key = "shopee:202:101"
            self.assertTrue(cat.cache_link(key, "blogger", "https://s.shopee.com.br/A1"))
            self.assertFalse(cat.cache_link(key, "blogger", "https://s.shopee.com.br/B2"))
            self.assertTrue(cat.cache_link(key, "wordpress", "https://s.shopee.com.br/W3"))
            self.assertEqual(cat.cached_link(key, "blogger"), "https://s.shopee.com.br/A1")
            self.assertEqual(cat.cached_link(key, "wordpress"), "https://s.shopee.com.br/W3")
            self.assertEqual(cat.stats()["cached_affiliate_links"], 2)
            self.assertEqual(cat.candidates("blogger"), [])

    def test_unauthorized_link_rejected(self):
        path = self.feed("cache.csv", [self.product()])
        with Catalog(self.dbpath) as cat:
            cat.import_csv(path, "feed")
            with self.assertRaises(ValueError):
                cat.cache_link("shopee:202:101", "blogger", "https://shopee.com.br.evil.test/x")
            with self.assertRaises(ValueError):
                cat.cache_link("shopee:202:101", "blogger", "http://s.shopee.com.br/X")
            with self.assertRaises(ValueError):
                cat.cache_link("shopee:202:101", "blogger", "https://s.shopee.com.br/X", origin="unverified")

    def test_host_allowlist(self):
        self.assertTrue(host_allowed("https://shopee.com.br/product/12"))
        self.assertTrue(host_allowed("https://affiliate.shopee.com.br/offer"))
        self.assertFalse(host_allowed("https://shopee.com.br.evil.test/x"))
        self.assertFalse(host_allowed("https://user:pass@shopee.com.br/x"))
        self.assertFalse(host_allowed("http://shopee.com.br/x"))
        self.assertFalse(host_allowed("https://s.shopee.com.br/x"))
        self.assertTrue(host_allowed("https://s.shopee.com.br/x", allow_short=True))

    def test_url_id_parsing(self):
        self.assertEqual(ids_from_url("https://shopee.com.br/item-i.202.101"), ("202", "101"))
        self.assertEqual(ids_from_url("https://shopee.com.br/foo?shopId=202&itemId=101"), ("202", "101"))

    def test_snapshot_backup_has_integrity(self):
        path = self.feed("feed.csv", [self.product(), self.product("102")])
        with Catalog(self.dbpath) as cat:
            cat.import_csv(path, "feed")
            snapshot = self.root / "copy.sqlite3"
            with closing(sqlite3.connect(snapshot)) as destination:
                cat.db.backup(destination)
        with Catalog(snapshot) as restored:
            self.assertTrue(restored.integrity())
            self.assertEqual(restored.stats()["products"], 2)


if __name__ == "__main__":
    unittest.main()
