"""Regressão de taxonomia C2; nenhum acesso à rede ou secrets."""
import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.taxonomy import classify_title, normalize, rules


class TaxonomyTests(unittest.TestCase):
    def test_coverage_version_and_clean_terms(self):
        version, items = rules()
        self.assertTrue(version.startswith("v31-editorial-taxonomy-"))
        self.assertGreaterEqual(len(items), 15)
        self.assertEqual(normalize("Cafeteira Elétrica"), "cafeteira eletrica")

    def test_example_routes(self):
        cases = {
            "Organizador de Cozinha Inox": ("cozinha", "organizacao_utensilios"),
            "Air Fryer Digital 5 litros": ("cozinha", "eletroportateis"),
            "Aspirador de Pó Vertical 2 em 1": ("limpeza", "equipamentos"),
            "Escova Secadora Bivolt": ("beleza", "cabelos"),
            "Scanner OBD2 Bluetooth": ("automotivo", "acessorios"),
            "Projetor Portátil 4K": ("tecnologia", "gadgets"),
            "Cama para Cachorro Grande": ("pets", "cuidados_acessorios"),
            "Parafusadeira Recarregável": ("ferramentas", "eletricas_manuais"),
            "Mala de Viagem Grande": ("viagem", "malas_acessorios"),
            "Violão Acústico": ("musica", "violao_instrumentos"),
            "Capacete Ciclismo": ("ciclismo", "equipamentos"),
            "Moedor de Café Manual": ("cafe", "preparo"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                got = classify_title(title)
                self.assertEqual((got.category, got.niche, got.status), (*expected, "matched"))

    def test_ambiguous_unknown_and_accessories_quarantined(self):
        for title, reason in [
            ("Produto Premium Importado", "unclassified"),
            ("Air Fryer e Liquidificador", "ambiguous_niches") if False else ("Air Fryer e Parafusadeira", "ambiguous_niches"),
            ("Motor para Ventilador Original", "excluded_accessory_or_semantics"),
            ("Capa para Liquidificador", "excluded_accessory_or_semantics"),
            ("Pulseira para Smartwatch", "excluded_accessory_or_semantics"),
        ]:
            with self.subTest(title=title):
                got = classify_title(title)
                self.assertEqual(got.status, "review")
                self.assertEqual(got.reason, reason)

    def test_word_boundaries_not_substring(self):
        self.assertEqual(classify_title("Cortador de batomera").status, "review")
        self.assertEqual(classify_title("Amop decorativo").status, "review")

    def test_catalog_only_provides_niche_approved_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            feed = p / "feed.csv"
            with feed.open("w", encoding="utf-8", newline="") as f:
                out = csv.DictWriter(f, fieldnames=["productName","shopId","itemId","productLink","imageUrl"])
                out.writeheader()
                for idx, title in enumerate(["Organizador de Cozinha", "Produto Importado", "Air Fryer", "Capa para Liquidificador"], 1):
                    out.writerow({"productName": title,"shopId":"200","itemId":str(idx),
                                  "productLink":f"https://shopee.com.br/produto-i.200.{idx}",
                                  "imageUrl":"https://cdn.example/image.jpg"})
            with Catalog(p / "state.sqlite3") as cat:
                result=cat.import_csv(feed,"feed")
                self.assertEqual(result["rows"], 4)
                self.assertEqual(result["taxonomy_matched"], 2)
                self.assertEqual(cat.stats()["eligible"], 2)
                self.assertEqual(cat.stats()["review"], 2)
                self.assertEqual(len(cat.candidates("blogger", category="cozinha", niche="eletroportateis")), 1)
                self.assertEqual(cat.for_conversion("shopee:200:2"), None)
                with self.assertRaises(ValueError):
                    cat.cache_link("shopee:200:2","blogger","https://s.shopee.com.br/abc")
                self.assertEqual(sum(x["products"] for x in cat.categories()), 2)

    def test_product_with_conflicting_reimport_is_quarantined(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            def emit(title):
                path=p/"update.csv"
                with path.open("w",encoding="utf-8",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=["shopId","itemId","productName","productLink","imageUrl"])
                    w.writeheader()
                    w.writerow({"shopId":"22","itemId":"33","productName":title,
                                "productLink":"https://shopee.com.br/item-i.22.33",
                                "imageUrl":"https://cdn.example/33.jpg"})
                return path
            with Catalog(p/"state.db") as cat:
                cat.import_csv(emit("Liquidificador 1000W"),"feed")
                self.assertIsNotNone(cat.for_conversion("shopee:22:33"))
                cat.import_csv(emit("Parafusadeira 12V"),"feed2")
                self.assertIsNone(cat.for_conversion("shopee:22:33"))
                self.assertEqual(cat.stats()["review"], 1)

    def test_legacy_rows_are_not_eligible_until_reclassification(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"state.sqlite3"
            with Catalog(p) as cat:
                with cat.db:
                    cat.db.execute("""INSERT INTO products
                      (product_key,shop_id,item_id,title,description,origin_url,image_url,moderation,moderation_reason,first_source,last_seen_utc)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                      ("shopee:11:12","11","12","Air Fryer","",
                       "https://shopee.com.br/item-i.11.12","https://cdn.example/p.jpg",
                       "eligible","","legacy","2026-11-15"))
                self.assertEqual(cat.stats()["eligible"],0)
                self.assertIsNone(cat.for_conversion("shopee:11:12"))
                self.assertEqual(cat.reclassify_missing(),1)
                self.assertIsNotNone(cat.for_conversion("shopee:11:12"))
                self.assertEqual(cat.reclassify_missing(),0)


if __name__=="__main__":
    unittest.main()
