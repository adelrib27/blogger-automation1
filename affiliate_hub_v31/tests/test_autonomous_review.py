"""Regressions for the independent factual trust boundary."""

import unittest
from unittest.mock import patch

from affiliate_hub_v31.autonomous_review import (
    VerificationError, checked_claims, extract_text, prose_hashes, verify_affiliate_target,
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
