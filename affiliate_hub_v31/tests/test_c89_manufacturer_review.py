"""C89: trusted manufacturer evidence is never equivalent to a search result."""
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.manufacturer_review import (
    ManufacturerEvidenceError, models_for_catalog_title,
    source_page_allowed, verify_manufacturer_markdown, trusted_brands,
)

SITE = "blogger_moveis_para_cada_canto"
TITLE = "Guarda-Roupa Casal 6 Portas 4 Gavetas Giardino Demóbile Roupeiro"
URL = "https://demobile.com.br/produtos/giardino-guarda-roupa-casal"
META = {"url": URL, "title": "Giardino Guarda-Roupa Casal da Demóbile Móveis"}
TEXT = ("## Giardino Guarda-Roupa Casal da Demóbile Móveis\n\n"
        "O Guarda-Roupa Casal Giardino possui 6 portas e 4 gavetas, "
        "estrutura em MDP e revestimento em pintura UV. "
        "Cabideiros metálicos e corrediças telescópicas.\n")


class ManufacturerTests(unittest.TestCase):
    def identity(self):
        return models_for_catalog_title(TITLE, site_key=SITE)[0]

    def review(self, title=TITLE, identity=None, metadata=None,
               markdown=TEXT, url=URL):
        return verify_manufacturer_markdown(
            identity=identity or self.identity(), catalog_title=title,
            source_url=url, source_metadata=metadata or META, markdown=markdown)

    def test_recognizes_real_manufacturer_model_without_gtin(self):
        identity=self.identity()
        self.assertEqual(identity["model"], "giardino")
        self.assertEqual(identity["kind"], "guarda-roupa")
        facts=self.review()
        self.assertEqual(len(facts), 2)
        self.assertEqual([x[0] for x in facts], ["model_identifier", "material"])
        self.assertIn("MDP", facts[1][1])

    def test_model_code_is_more_specific_than_generic_words(self):
        title="Guarda Roupa Casal 6 Portas 3 gavetas B23 Briz"
        candidates=models_for_catalog_title(title,site_key=SITE)
        self.assertEqual(candidates[0]["model"],"b23")
        self.assertFalse(models_for_catalog_title(
            "Guarda roupa sem marca e sem codigo",site_key=SITE))

    def test_fake_sources_and_untrusted_redirects_fail_closed(self):
        idn=self.identity()
        for url in ("http://demobile.com.br/produtos/giardino-guarda-roupa-casal",
                    "https://evil.example/produtos/giardino-guarda-roupa-casal",
                    "https://demobile.com.br/produtos/giardino-guarda-roupa-casal?ref=evil",
                    "https://demobile.com.br/produtos/guarda-roupa",
                    "https://demobile.com.br/colecoes/giardino"):
            with self.subTest(url=url):
                self.assertFalse(source_page_allowed(url,idn))
        with self.assertRaisesRegex(ManufacturerEvidenceError,"source_redirected"):
            self.review(metadata={"url":"https://evil.example/giardino",
                                  "title":META["title"]})

    def test_other_model_or_product_type_cannot_be_signed(self):
        with self.assertRaisesRegex(ManufacturerEvidenceError,"model_identity_mismatch"):
            self.review(metadata={"url":URL, "title":"Giardino Cômoda da Demóbile"})
        with self.assertRaisesRegex(ManufacturerEvidenceError,"model_identity_mismatch"):
            self.review(title=TITLE.replace("Giardino","Laredo"))
        with self.assertRaisesRegex(ManufacturerEvidenceError,"model_identity_mismatch"):
            self.review(title=TITLE.replace("Demóbile","Outra Marca"))

    def test_variant_conflicts_and_missing_measured_material_fail_closed(self):
        with self.assertRaisesRegex(ManufacturerEvidenceError,"variant_conflict"):
            self.review(markdown=TEXT+"Guarda-Roupa Giardino 8 portas e 2 gavetas.")
        with self.assertRaisesRegex(ManufacturerEvidenceError,"variant_conflict"):
            self.review(markdown=TEXT.replace("6 portas e 4 gavetas, ",""))
        with self.assertRaisesRegex(ManufacturerEvidenceError,"material_unverified"):
            self.review(markdown=TEXT.replace("estrutura em MDP","ótima qualidade"))
        with self.assertRaisesRegex(ManufacturerEvidenceError,"material_unverified"):
            self.review(markdown=TEXT.replace("estrutura em MDP","estrutura em chumbo"))
        with self.assertRaisesRegex(ManufacturerEvidenceError,"material_unverified"):
            self.review(markdown=TEXT.replace("estrutura em MDP","estrutura em MDF e MDP"))

    def test_scraped_footer_cannot_supply_fake_material(self):
        front="## Giardino Guarda-Roupa Casal da Demóbile\n"
        body=front+"Guarda-Roupa Giardino 6 portas e 4 gavetas.\n"+("texto geral "*130)
        with self.assertRaisesRegex(ManufacturerEvidenceError,"material_unverified"):
            self.review(markdown=body+"\nProduto diferente tem estrutura em MDP.")

    def test_registry_requires_exact_validated_schema(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"brands.json"
            path.write_text(json.dumps({"schema":"v31-trusted-manufacturer-registry-1",
                "sites":{SITE:[{"brand":"X","aliases":["Exemplo"],
                                "hosts":["evil..host"],
                                "product_path_prefix":"/produtos/"}]}}))
            with self.assertRaisesRegex(ManufacturerEvidenceError,"trust_invalid"):
                trusted_brands(SITE,registry_path=path)


if __name__=="__main__":
    unittest.main()
