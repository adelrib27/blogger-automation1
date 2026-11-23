"""C9: fallback preserva alternativas de loja para a mesma keyword."""
import csv
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.fallback_v23 import candidates_from_catalog


class CachedAlternativeTests(unittest.TestCase):
    def test_three_alternative_shops_for_one_keyword_and_campaign_isolation(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            csvfile=path/"feed.csv"
            with csvfile.open("w",newline="",encoding="utf-8") as stream:
                w=csv.DictWriter(stream,fieldnames=[
                    "shopId","itemId","productName","productLink","imageUrl"
                ])
                w.writeheader()
                for n in range(5):
                    w.writerow({
                        "shopId":str(9100+n),"itemId":str(9300+n),
                        "productName":f"Smartwatch Bluetooth Modelo {n}",
                        "productLink":f"https://shopee.com.br/product/{9100+n}/{9300+n}",
                        "imageUrl":"https://cf.shopee.com.br/file/photo"
                    })
            db=path/"catalog.sqlite3"
            with Catalog(db) as catalog:
                catalog.import_csv(csvfile,"feed")
                for n in range(5):
                    catalog.cache_link(
                        f"shopee:{9100+n}:{9300+n}","radarwp",
                        f"https://s.shopee.com.br/cache-{n}"
                    )
            cfg={"categories":{"Tecnologia":["smartwatch"]}}
            rules={"rules":{}}
            rows=candidates_from_catalog(db,"wordpress_radartechbr",cfg,rules,limit=20)
            self.assertEqual(len(rows),3)
            self.assertEqual(len({r["shopId"] for r in rows}),3)
            self.assertTrue(all(r["productLink"].startswith(
                "https://shopee.com.br/") for r in rows))
            self.assertEqual(len(rows[0]["intentMatchedKeywords"]),1)
            self.assertTrue(all(r["offerLink"].startswith(
                "https://s.shopee.com.br/") for r in rows))
            self.assertEqual(candidates_from_catalog(
                db,"wordpress_casa_decoracao",cfg,rules,20),[])
            self.assertEqual(candidates_from_catalog(
                db,"wordpress_radartechbr",
                {"categories":{"Cozinha":["air fryer"]}},rules,20),[])


if __name__ == "__main__":
    unittest.main()
