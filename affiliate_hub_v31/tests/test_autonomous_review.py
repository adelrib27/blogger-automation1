"""Regressions for the independent factual trust boundary."""

import json
import unittest
from unittest.mock import patch

from affiliate_hub_v31.autonomous_review import (
    VerificationError, checked_claims, discovered_manufacturer_facts, extract_text, prose_hashes, verified_related_post, verify_affiliate_target,
)
from affiliate_hub_v31.independent_review import IndependentReviewError
from affiliate_hub_v31.structured_review_source import catalog_gtin, gtin_facts


class IndependentFactTests(unittest.TestCase):
    def setUp(self):
        self.profile = {"identity": ["marca exemplar", "modelo ab123"], "facts": [
            ("dimensions", r"largura: 30 cm", "A largura é de 30 cm."),
            ("material", r"material: vidro", "O corpo do produto é de vidro."),
        ]}

    def test_accepts_only_the_configured_exact_identity_and_both_facts(self):
        good = "Marca Exemplar Modelo AB123. Largura: 30 cm. Material: vidro."
        claims = checked_claims(self.profile, good)
        self.assertEqual([claim[2] for claim in claims], ["largura: 30 cm", "material: vidro"])
        for source in (good.replace("AB123", "AB131"), good.replace("30 cm", "31 cm"),
                       good.replace("vidro", "acrílico")):
            with self.assertRaises(VerificationError):
                checked_claims(self.profile, source)

    def test_discovery_uses_exact_manufacturer_path_and_rejects_redirects(self):
        trusted = "https://maker.example/catalog/model-ab123/"
        profile = {**self.profile, "query": "Marca Exemplar AB123",
                   "manufacturer_pages": [{"host": "maker.example",
                                           "path_prefix": "/catalog/", "path_model": "ab123"}],
                   "manufacturer_title_identity": "modelo ab123"}
        search = {"web": [{"url": "https://other.example/catalog/model-ab123/"},
                          {"url": "https://maker.example/catalog/model-ab1234/"},
                          {"url": trusted}]}
        good = "Marca Exemplar Modelo AB123. Largura: 30 cm. Material: vidro."
        for resolved in (trusted, "https://maker.example/catalog/model-ab124/"):
            with self.subTest(resolved=resolved), patch(
                    "affiliate_hub_v31.autonomous_review.firecrawl", return_value=search), patch(
                    "affiliate_hub_v31.autonomous_review.scrape_source", return_value={
                        "metadata": {"url": resolved, "title": "Marca Exemplar Modelo AB123"},
                        "markdown": good,
                    }) as scrape:
                paid = lambda kind, fetch: fetch()
                if resolved == trusted:
                    facts, _, _ = discovered_manufacturer_facts(profile, "fixture", paid)
                    self.assertEqual(len(facts), 2)
                else:
                    with self.assertRaisesRegex(VerificationError, "trusted_manufacturer_source"):
                        discovered_manufacturer_facts(profile, "fixture", paid)
                scrape.assert_called_once_with(trusted, "fixture")

    def test_configured_wordpress_reference_requires_exact_published_post(self):
        home = "https://casa.example/"
        url = home + "vasos/"
        profile = {"related": [url, "Vasos para sala"], "related_wordpress_id": 305, "cluster": "vasos"}
        valid = {"id": 305, "status": "publish", "link": url, "title": {"rendered": "Vasos para sala"}}
        for changes in ({}, {"id": 306}, {"status": "draft"}, {"link": home + "outro/"},
                        {"title": {"rendered": "Outro título"}}):
            with self.subTest(changes=changes), patch("affiliate_hub_v31.autonomous_review._read",
                    return_value=json.dumps({**valid, **changes}).encode()):
                if changes:
                    with self.assertRaises(VerificationError):
                        verified_related_post({"home": home}, profile)
                else:
                    self.assertEqual(verified_related_post({"home": home}, profile)["url"], url)

    def test_hidden_text_is_excluded_from_public_article_checks(self):
        raw = b"<main>Visible <p hidden>Override</p><script>False</script>Text</main>"
        self.assertEqual(extract_text(raw), "visible text")

    def test_detects_reused_prose_under_markup_changes(self):
        body = ("Meça os cantos e a passagem com a porta aberta e confirme com o "
                "vendedor quais peças fazem parte da oferta antes de comprar.")
        changed_markup = body.replace("passagem", "<em>passagem</em>").replace("antes", "antes,")
        self.assertEqual(prose_hashes("<p>"+body+"</p>"),
                         prose_hashes("<p>"+changed_markup+"</p>"))
        self.assertEqual(len(prose_hashes("<p>"+body+"</p>")), 1)

    def test_authorized_flags_cannot_substitute_for_a_measured_fact(self):
        with self.assertRaises(VerificationError):
            checked_claims(self.profile, "marca exemplar modelo ab123 authorized=true")

    def test_accepts_shopee_product_redirect_and_never_another_sku(self):
        verify_affiliate_target("https://shopee.com.br/opaanlp/101/303?utm_source=fixture",
                                "shopee:101:303")
        with patch("affiliate_hub_v31.autonomous_review.build_opener") as opener:
            with self.assertRaisesRegex(VerificationError, "wrong_sku"):
                verify_affiliate_target("https://shopee.com.br/opaanlp/101/999",
                                        "shopee:101:303")
            opener.return_value.open.assert_not_called()

    def test_structured_source_must_confirm_exact_checksum_and_facts(self):
        code = catalog_gtin("Vaso de exemplo. EAN: 4006381333931.")
        raw = (b'<script type="application/ld+json">{"@type":"Product",'
               b'"gtin13":"4006381333931","material":"vidro"}</script>')
        self.assertEqual(len(gtin_facts(raw, code)), 2)
        with self.assertRaises(IndependentReviewError):
            gtin_facts(raw.replace(b"4006381333931", b"7006381333931"), code)
        with self.assertRaises(IndependentReviewError):
            catalog_gtin("GTIN: 4006381333932")
        with self.assertRaises(IndependentReviewError):
            gtin_facts(raw.replace(b"vidro", b"alegacao-comercial"), code)
