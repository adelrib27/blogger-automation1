"""C16: diagnóstico de razões sem ler links ou gerar posts."""
import csv
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.taxonomy_diagnostic import diagnose
from affiliate_hub_v31.feed_schema_probe import schema


class C16DiagnosticTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)

    def test_pending_taxonomy_has_static_reason_not_titles(self):
        file=self.root/"feed.csv"
        with file.open("w",newline="",encoding="utf-8") as stream:
            writer=csv.DictWriter(stream,fieldnames=[
                "shopId","itemId","productName","productLink","imageUrl"
            ])
            writer.writeheader()
            for i,title in enumerate(["Produto inovador sem nicho especificado",
                                       "Produto inovador sem nicho especificado",
                                       "Air Fryer 5 litros"],1):
                writer.writerow({
                    "shopId":"100","itemId":str(i),"productName":title,
                    "productLink":f"https://shopee.com.br/product/100/{i}",
                    "imageUrl":"https://cf.shopee.com.br/file/image"
                })
        with Catalog(self.root/"db.sqlite3") as catalog:
            catalog.import_csv(file,"feed1")
            result=diagnose(catalog,top=15)
        self.assertEqual(result["pending_products"],2)
        self.assertEqual(result["taxonomy_reasons"]["unclassified"],2)
        self.assertEqual(
            result["potentially_reclassifiable_without_prior_conflict"],2)
        self.assertEqual(result["r2_writes"],0)
        self.assertEqual(result["shopee_api_calls"],0)
        self.assertNotIn("inovador",str(result))

    def test_csv_category_column_detection_without_exposing_content(self):
        path=self.root/"feed.csv"
        with path.open("w",encoding="utf-8",newline="") as h:
            writer=csv.DictWriter(h,fieldnames=[
                "productName","productLink","categoryName","sellerId"
            ])
            writer.writeheader()
            writer.writerow({"productName":"Produto privado",
                             "productLink":"https://shopee.com.br/product/1/2",
                             "categoryName":"NomeSensivelDeTeste","sellerId":"100"})
        result=schema(path)
        self.assertTrue(result["has_csv_taxonomy_metadata"])
        self.assertEqual(result["taxonomy_metadata_columns"],1)
        self.assertEqual(result["taxonomy_metadata_nonempty_per_column_first_1000"],[1])
        self.assertNotIn("NomeSensivelDeTeste",str(result))
        self.assertNotIn("categoryName",str(result))

    def test_csv_without_any_category_field_fails_not_forced(self):
        file=self.root/"no_category.csv"
        file.write_text("productName,productLink\n"
                        "ABC,https://shopee.com.br/product/1/2\n")
        self.assertFalse(schema(file)["has_csv_taxonomy_metadata"])


if __name__=="__main__":
    unittest.main()
