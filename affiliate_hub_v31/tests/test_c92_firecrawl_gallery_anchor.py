"""C92 regression using the observed Firecrawl structure of Buriti's official page.

URLs and image-gallery filenames are not product feature evidence.
"""
import unittest

from affiliate_hub_v31.manufacturer_review import (
    ManufacturerEvidenceError, models_for_catalog_title,
    verify_manufacturer_markdown,
)

SITE="blogger_moveis_para_cada_canto"
PRODUCT="Guarda Roupa Casal 6 Portas (2 Ripadas) e 4 Gavetas c/ Espelho Buriti Jatoba/Grafite - Santos Andirá"
URL="https://www.santosandira.com.br/produto/guarda-roupa-buriti-6-portas/"
META={"sourceURL":URL,
      "title":"Guarda-Roupa Buriti 6 Portas – Santos Andirá"}
GALLERY="\n".join("- ![](https://www.santosandira.com.br/wp-content/uploads/2023/12/"
                  f"GR_Buriti_6P_JatobaGrafite_{i}-150x150.jpg)"
                  for i in range(11))
MAIN="""## Guarda-Roupa Buriti 6 Portas

### Sobre o produto

Características:

• 04  Gavetas com corrediças telescópicas
• Cofre embutido
• 07 Prateleiras
• 03 Cabideiros em alumínio
• Amplo Maleiro
• Puxadores em MDF revestido
• 02 Portas em MDF com detalhe usinado ripado

### Acabamento das cores
Jatobá/Grafite: 162348

### Medidas
Altura - 2190 mm
Largura - 2320 mm

[Manual de Montagem](https://www.santosandira.com.br/wp-content/uploads/G.R.-BURITI-06-PTS-1.pdf)

## Newsletter.
Conteúdo de rodapé de outro produto: 12 portas e 9 gavetas
"""

class ObservedFirecrawlGalleryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.identity=models_for_catalog_title(PRODUCT,site_key=SITE)[0]
    def verify(self, markdown):
        return verify_manufacturer_markdown(
            identity=self.identity, catalog_title=PRODUCT,
            source_url=URL, source_metadata=META, markdown=markdown)

    def test_gallery_before_real_heading_does_not_hide_valid_counts(self):
        raw="×\n\n## O que você está procurando?\n\nBuscar\n\n"+GALLERY+"\n\n"+MAIN
        facts=self.verify(raw)
        self.assertEqual([f[0] for f in facts],
                         ["model_identifier","features","features"])
        self.assertIn("6 portas",facts[1][1])
        self.assertIn("4 gavetas",facts[2][1])
        self.assertTrue(all("12 portas" not in f[1] for f in facts))

    def test_image_link_or_related_footer_not_substitute_for_article_heading(self):
        bad="×\n\n"+GALLERY.replace("6P","06-portas")+"\n\n## Newsletter\n" + \
            "Guarda Roupa Buriti 6 portas e 4 gavetas"
        with self.assertRaisesRegex(ManufacturerEvidenceError,
                                    "manufacturer_product_heading_missing"):
            self.verify(bad)

    def test_no_variant_claim_from_footer_or_gallery(self):
        wrong=("## Guarda-Roupa Buriti 6 Portas\n"
               "\n### Sobre o produto\n• 01 Gaveta\n\n## Newsletter\n"
               "04 Gavetas com corrediças telescópicas")
        with self.assertRaisesRegex(ManufacturerEvidenceError,
                                    "manufacturer_variant_conflict"):
            self.verify(wrong)

if __name__=="__main__":
    unittest.main()
