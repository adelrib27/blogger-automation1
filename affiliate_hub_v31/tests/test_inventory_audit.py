"""Inventário C9: reconhecer categorias Shopee sem depender de links cacheados."""
import csv
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.inventory_audit import eligible_inventory,InventoryError


class InventoryCoverageTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root=Path(self.directory.name)
        file=root/"products.csv"
        with file.open("w",newline="",encoding="utf-8") as h:
            w=csv.DictWriter(h,fieldnames=["shopId","itemId","productName",
                                            "productLink","imageUrl"])
            w.writeheader()
            for i,title in enumerate(["Air Fryer de Bancada",
                                      "Furadeira de Impacto",
                                      "Escova Secadora Profissional",
                                      "Smartwatch Bluetooth com Tela",
                                      "Ar Condicionado Split Inverter 12000 BTU"],1):
                w.writerow({"shopId":"987","itemId":str(i),"productName":title,
                            "productLink":f"https://shopee.com.br/product/987/{i}",
                            "imageUrl":"https://cf.shopee.com.br/file/abcd"})
        self.db=root/"state.sqlite3"
        with Catalog(self.db) as cat:
            cat.import_csv(file,"f")

    def test_radar_inventory_by_keyword_not_campaign(self):
        cfg={"categories":{
            "Cozinha & Utilidades":["air fryer"],
            "Ferramentas & Auto":["furadeira"],
            "Moda & Beleza":["escova secadora"],
            "Tecnologia":["smartwatch"],
            "Climatização":["ar condicionado split"],
        }}
        rules={"rules":{}}
        report=eligible_inventory(self.db,"wordpress_radartechbr",cfg,rules)
        # Biblioteca completa; cada site enxerga apenas o nicho permitido.
        self.assertEqual(report["category_supply"]["Cozinha & Utilidades"],0)
        self.assertEqual(report["category_supply"]["Ferramentas & Auto"],0)
        self.assertEqual(report["category_supply"]["Moda & Beleza"],0)
        self.assertEqual(report["category_supply"]["Tecnologia"],1)
        self.assertEqual(report["category_supply"]["Climatização"],1)
        self.assertEqual(set(report["zero_supply_categories"]),
                         {"Cozinha & Utilidades","Ferramentas & Auto",
                          "Moda & Beleza"})
        self.assertNotIn("offerLink",str(report))

    def test_absent_category_is_visible(self):
        cfg={"categories":{"Tecnologia":["webcam"]}}
        result=eligible_inventory(self.db,"wordpress_radartechbr",cfg,{"rules":{}})
        self.assertEqual(result["zero_supply_categories"],["Tecnologia"])

    def test_unknown_site_fails(self):
        with self.assertRaisesRegex(InventoryError,"site_unknown"):
            eligible_inventory(self.db,"wordpress_not_configured",{"categories":{}},{})


if __name__=="__main__":
    unittest.main()
