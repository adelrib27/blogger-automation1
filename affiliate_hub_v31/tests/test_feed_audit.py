"""C2.1: regressão com dados artificiais para auditoria read-only de CSV."""
import csv
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.feed_audit import FeedAuditError, inspect_csv
from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.feed_download import redirect_allowed


class FeedAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def csv_file(self, name, rows):
        path=self.root/name
        with path.open("w",encoding="utf-8",newline="") as handle:
            writer=csv.DictWriter(handle,fieldnames=["shopId","itemId","productName","productLink","imageUrl"])
            writer.writeheader()
            for identifier,title in rows:
                writer.writerow({
                    "shopId":"100", "itemId":str(identifier), "productName":title,
                    "productLink":f"https://shopee.com.br/item-i.100.{identifier}",
                    "imageUrl":"https://img.example.invalid/photo.jpg",
                })
        return path

    def test_realistic_two_feeds_dedup_and_niches(self):
        seen=set()
        first=inspect_csv(self.csv_file("first.csv",[(1,"Air Fryer digital"),(2,"Liquidificador 1000W")]),seen,"feed_1")
        second=inspect_csv(self.csv_file("second.csv",[(2,"Liquidificador 1000W"),(3,"Produto Generico")]),seen,"feed_2")
        self.assertEqual(first["rows"],2)
        self.assertEqual(second["rows"],2)
        self.assertEqual(second["duplicates_or_existing"],1)
        self.assertEqual(second["unclassified"],1)
        self.assertEqual(len(seen),3)
        self.assertEqual(first["niches"]["cozinha/air_fryers"],1)

    def test_malformed_csv_errors_without_values(self):
        invalid=self.root/"bad.csv"
        invalid.write_text("productName,productLink\nAir Fryer\n",encoding="utf-8")
        with self.assertRaises(FeedAuditError) as caught:
            inspect_csv(invalid,set(),"feed_1")
        self.assertTrue(str(caught.exception).startswith("CSV_COLUMN_COUNT_MISMATCH_feed_1_ROW_1"))

    def test_real_csv_quoting_multiline_descriptions(self):
        path = self.root / "multiline.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "shopId", "itemId", "productName", "productLink",
                "imageUrl", "productDescription"
            ])
            writer.writeheader()
            for index in range(1, 9):
                writer.writerow({
                    "shopId": "10", "itemId": str(index),
                    "productName": "Air Fryer Modelo " + str(index),
                    "productLink": f"https://shopee.com.br/item-i.10.{index}",
                    "imageUrl": "https://img.example.invalid/p.png",
                    "productDescription": ('Descrição com vírgulas, aspas "internas" '
                                           'e trechos em várias linhas.\\n'.replace('\\n', '\n')) * 40,
                })
        seen = set()
        report = inspect_csv(path, seen, "feed_1")
        self.assertEqual(report["rows"], 8)
        self.assertEqual(report["columns"], 6)
        with Catalog(self.root / "multiline.sqlite3") as catalog:
            imported = catalog.import_csv(path, "feed1")
            self.assertEqual(imported["rows"], 8)
            self.assertEqual(catalog.stats()["products"], 8)

    def test_redirect_allowed_only_inside_https_shopee(self):
        self.assertTrue(redirect_allowed("https://download.shopee.com.br/path?token=private"))
        self.assertTrue(redirect_allowed("https://affiliate.shopee.com.br/api/v1/datafeed/download?id=test"))
        for url in ("http://download.shopee.com.br/path",
                    "https://shopee.com.br.evil.test/path",
                    "https://user:pass@shopee.com.br/path",
                    "https://example.com/feed.csv",
                    "https://shopee.com.br:444/path"):
            self.assertFalse(redirect_allowed(url))

    def test_reject_compressed_content_without_exposing_it(self):
        data=self.root/"f.csv"
        data.write_bytes(b"PK\x03\x04secret")
        with self.assertRaisesRegex(FeedAuditError,"UNEXPECTED_ZIP"):
            inspect_csv(data,set(),"feed_1")


if __name__=="__main__":
    unittest.main()
