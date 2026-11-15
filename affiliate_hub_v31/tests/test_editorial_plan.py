"""C2.3: planejador editorial privado, sem API e com reuso do produto."""
import csv
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.editorial_plan import plan


class PlannerTests(unittest.TestCase):
    def test_reserves_unique_briefs_and_reuses_products(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            feed=base/"catalog.csv"
            with feed.open("w", encoding="utf-8", newline="") as io:
                writer=csv.DictWriter(io,fieldnames=["productName","shopId","itemId","productLink","imageUrl"])
                writer.writeheader()
                writer.writerow({"productName":"Air Fryer 5 Litros","shopId":"10","itemId":"44",
                                 "productLink":"https://shopee.com.br/item-i.10.44",
                                 "imageUrl":"https://img.example.invalid/a.jpg"})
            with Catalog(base/"state.db") as cat:
                cat.import_csv(feed,"feed1")
                first=plan(cat,"blogger_air_fryers",1)
                second=plan(cat,"blogger_air_fryers",1)
                self.assertEqual(first["reserved_for_review"],1)
                self.assertEqual(second["reserved_for_review"],1)
                result=cat.db.execute("SELECT COUNT(DISTINCT product_key),COUNT(DISTINCT title),COUNT(DISTINCT angle) FROM editorial_briefs").fetchone()
                self.assertEqual(result,(1,2,2))
                self.assertEqual(cat.db.execute("SELECT COUNT(*) FROM editorial_briefs WHERE status='REVIEW_REQUIRED'").fetchone()[0],2)
                self.assertTrue(cat.integrity())

    def test_missing_site_rejected(self):
        with tempfile.TemporaryDirectory() as d, Catalog(Path(d)/"state.db") as c:
            with self.assertRaises(ValueError):
                plan(c,"pinterest",1)
            with self.assertRaises(ValueError):
                plan(c,"blogger_air_fryers",0)


if __name__ == "__main__":
    unittest.main()
