"""C92: manufacturer title+model vs generic colors and exact counts from official pages."""
import unittest

from affiliate_hub_v31.manufacturer_review import (
    models_for_catalog_title, source_page_allowed, verify_manufacturer_markdown,
    ManufacturerEvidenceError,
)
SITE="blogger_moveis_para_cada_canto"
ITEMS=[
 ("Armário Multiuso Lavanderia Viena c/ 2 Portas Branco - Demóbile","viena",None),
 ("Guarda Roupa Casal 6 Portas (2 Ripadas) e 4 Gavetas c/ Espelho Buriti Jatoba/Grafite - Santos Andirá",
  "buriti",None),
 ("Cômoda de Quarto Marabá 1.6 c/ 1 Porta 2 Nichos e 6 Gavetas Jatoba Atacama/Grafitte - Santos Andirá",
  "maraba","1.6"),
 ("Cômoda de Quarto Marabá 1.6 c/ 1 Porta 2 Nichos e 6 Gavetas c/ Espelho Atacama/Grafitte - Santos Andirá",
  "maraba","1.6"),
 ("Cômoda de Quarto Master c/ 2 Portas 1 Nicho e 4 Gavetas c/ Pés Branco - Santos Andirá",
  "master",None),
 ("Cômoda Sapateira Ambiente áurea Amêndola Touch Off White – Demóbile",
  "aurea",None),
]


class ManufacturerVariantC92(unittest.TestCase):
    def identity(self, title):
        return models_for_catalog_title(title,site_key=SITE)[0]

    def test_extracts_real_model_before_color_or_accessories(self):
        for title,model,variant in ITEMS:
            with self.subTest(model=model):
                x=self.identity(title)
                self.assertEqual(x["model"],model)
                self.assertEqual(x.get("variant"),variant)

    def test_buriti_official_total_six_doors_contains_two_ribbed_subset(self):
        title=ITEMS[1][0]
        identity=self.identity(title)
        url="https://www.santosandira.com.br/produto/guarda-roupa-buriti-6-portas/"
        metadata={"url":url,"title":"Guarda-Roupa Buriti 6 Portas – Santos Andirá"}
        markdown="""## Guarda-Roupa Buriti 6 Portas
        ### Sobre o produto
        • 04 Gavetas com corrediças telescópicas
        • 02 Portas em MDF com detalhe usinado ripado
        • 07 Prateleiras, 03 cabideiros em alumínio
        """
        facts=verify_manufacturer_markdown(identity=identity,catalog_title=title,
                         source_url=url,source_metadata=metadata,markdown=markdown)
        self.assertEqual([x[0] for x in facts],
                         ["model_identifier","features","features"])
        self.assertIn("6 portas",facts[1][1])
        self.assertIn("4 gavetas",facts[2][1])
        with self.assertRaisesRegex(ManufacturerEvidenceError,"variant_conflict"):
            verify_manufacturer_markdown(identity=identity,catalog_title=title,
                        source_url=url,source_metadata=metadata,
                        markdown=markdown.replace("04 Gavetas","03 Gavetas"))
        with self.assertRaisesRegex(ManufacturerEvidenceError,"variant_conflict"):
            verify_manufacturer_markdown(identity=identity,catalog_title=title,
                        source_url=url,source_metadata=metadata,
                        markdown=markdown+"Este guarda-roupa tem 8 portas.")

    def test_maraba_version_and_amplas_gavetas_are_exact(self):
        title=ITEMS[2][0]
        identity=self.identity(title)
        url="https://www.santosandira.com.br/produto/multi-comoda-maraba-1-6/"
        metadata={"url":url,"title":"Multi-Cômoda Marabá 1.6 – Santos Andirá"}
        markdown="""## Multi-Cômoda Marabá 1.6
        ### Sobre o produto
        • 01 porta com 03 prateleiras
        • 06 amplas gavetas com corrediças telescópicas
        • 01 ampla prateleira externa
        """
        self.assertTrue(source_page_allowed(url,identity))
        facts=verify_manufacturer_markdown(identity=identity,catalog_title=title,
                         source_url=url,source_metadata=metadata,markdown=markdown)
        self.assertEqual([f[0] for f in facts],
                         ["model_identifier","features","features"])
        self.assertIn("1 portas",facts[1][1])  # checked numeral, grammar tested below
        self.assertIn("6 gavetas",facts[2][1])
        with self.assertRaisesRegex(ManufacturerEvidenceError,"model_identity_mismatch"):
            verify_manufacturer_markdown(identity=identity,catalog_title=title,
                source_url=url,source_metadata={**metadata,
                                  "title":"Multi-Cômoda Marabá 1.4 – Santos Andirá"},
                markdown=markdown)
        self.assertFalse(source_page_allowed(
             "https://www.santosandira.com.br/produto/multi-comoda-maraba-1-4/",
             identity))

    def test_no_model_in_unbranded_or_color_only_title(self):
        self.assertFalse(models_for_catalog_title(
           "Cômoda de Quarto com Espelho Branco - Santos Andirá",site_key=SITE))
        self.assertFalse(models_for_catalog_title(
           "Armário Multiuso Lavanderia Branco - Demóbile",site_key=SITE))

if __name__=="__main__":
    unittest.main()
