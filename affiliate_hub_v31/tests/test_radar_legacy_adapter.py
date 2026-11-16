"""C9: regressão sem rede do construtor de 5 categorias Radar."""
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.radar_legacy_adapter import (
    RadarQueueError, build_from_ranking, validate_ranking,
)


class RadarAdapterTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.source=self.root/"ranking.json"
        self.target=self.root/"fila_dia.json"
        definitions=[
            ("Tecnologia","caixa de som bluetooth","Caixa de Som Bluetooth Portátil C9"),
            ("Casa & Decoracao","luminaria","Luminária LED para Casa C9"),
            ("Cozinha & Utilidades","air fryer","Air Fryer Elétrica C9"),
            ("Ferramentas & Auto","furadeira","Furadeira de Impacto C9"),
            ("Moda & Beleza","escova secadora","Escova Secadora Profissional C9"),
        ]
        self.rows=[]
        for n,(category,keyword,title) in enumerate(definitions,1):
            self.rows.append({
                "itemId":str(830000+n),"shopId":str(840000+n),
                "productName":title,
                "productLink":f"https://shopee.com.br/product/{840000+n}/{830000+n}",
                "offerLink":f"https://s.shopee.com.br/c9-{n}",
                "imageUrl":f"https://cf.shopee.com.br/file/c9-{n}",
                "categories":[category],
                "keywords":[keyword],
                "intentMatchedKeywords":[keyword],
                "priorityTier":"CSV_R2_CACHE",
                "ratingStar":None,"sales":None,"sellerCommissionRate":None,
            })
        self.write_ranking()

    def write_ranking(self):
        self.source.write_text(json.dumps({"ranking":self.rows}),
                               encoding="utf-8")

    def test_five_categories_distinct_shops_and_keywords_builds_original_queue(self):
        summary=build_from_ranking(self.source,self.target)
        self.assertEqual(summary["slots"],5)
        self.assertEqual(summary["publication_calls"],0)
        result=json.loads(self.target.read_text(encoding="utf-8"))
        self.assertTrue(result["complete"])
        self.assertEqual(len(result["slots"]),5)
        self.assertEqual(len({s["category"] for s in result["slots"]}),5)
        self.assertTrue(all(s["status"]=="AGENDADO" for s in result["slots"]))

    def test_missing_category_blocks_and_does_not_clobber_existing(self):
        # Quinta oferta é da mesma categoria da primeira.
        self.rows[4]["categories"]=["Tecnologia"]
        self.rows[4]["intentMatchedKeywords"]=["caixa de som bluetooth"]
        self.write_ranking()
        self.target.write_text('{"previous":"untouched"}',encoding="utf-8")
        with self.assertRaises(RadarQueueError):
            build_from_ranking(self.source,self.target)
        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8")),
                         {"previous":"untouched"})

    def test_wrong_affiliate_host_rejected_before_builder(self):
        self.rows[0]["offerLink"]="https://attacker.example.test/link"
        self.write_ranking()
        with self.assertRaises(RadarQueueError):
            validate_ranking(self.source)
        self.assertFalse(self.target.exists())

    def test_missing_shop_id_rejected_before_builder(self):
        self.rows[0].pop("shopId")
        self.write_ranking()
        with self.assertRaises(RadarQueueError):
            validate_ranking(self.source)


if __name__=="__main__":
    unittest.main()
