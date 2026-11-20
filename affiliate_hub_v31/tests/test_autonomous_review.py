"""Regressions for the independent factual trust boundary."""

import unittest
from unittest.mock import patch

from affiliate_hub_v31.autonomous_review import (
    VerificationError, checked_claims, extract_text, verify_affiliate_target,
)


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
