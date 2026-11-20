"""C71 — fact gate do HTML final. Fixtures sintéticas; 0 APIs/POST."""
import unittest
from datetime import timedelta

from affiliate_hub_v31.final_fact_gate import (
    FinalFactGateError, reviewed_text_digest, verify_final_html_facts,
)
from affiliate_hub_v31.tests.test_c69_universal_evidence_ready import (
    KEYS, TITLES, NOW, package,
)

HEADING = "Como comparar produtos"
BOILERPLATE = "Verifique o anúncio oficial antes de comprar."
FACT = "As dimensões são verificadas na ficha externa atual."
HTML = (
    "<article><h2>" + HEADING + "</h2>"
    '<p><span data-v31-fact-id="EVID_0_0">' + FACT + "</span></p>"
    "<p>" + BOILERPLATE + "</p></article>"
)
HASHES = [reviewed_text_digest(HEADING), reviewed_text_digest(BOILERPLATE)]


class FinalFactGateTests(unittest.TestCase):
    def run_gate(self, html=HTML, **kwargs):
        args = {
            "html_content": html,
            "evidence_package": package(0),
            "product_key": KEYS[0],
            "product_title": TITLES[0],
            "used_evidence_ids": ["EVID_0_0"],
            "trusted_reviewed_text_hashes": HASHES,
            "now": NOW,
        }
        args.update(kwargs)
        return verify_final_html_facts(**args)

    def test_exact_fact_and_independently_reviewed_prose_pass_not_live(self):
        result = self.run_gate()
        self.assertEqual(result["verified_facts"], 1)
        self.assertEqual(result["editorial_blocks_independently_reviewed"], 2)
        self.assertEqual(result["status"],
                         "EXACT_FACT_BINDINGS_VERIFIED_REVIEW_STILL_REQUIRED")
        self.assertTrue(result["requires_human_live_approval"])
        self.assertFalse(result["ready_publication_authorized"])
        self.assertEqual(result["publication_calls"], 0)
        self.assertEqual(result["network_calls"], 0)

    def test_unreviewed_prose_is_fail_closed_even_if_model_claims_verified(self):
        for trusted in ([], [reviewed_text_digest(HEADING)]):
            with self.subTest(trusted=trusted), self.assertRaisesRegex(
                    FinalFactGateError, "unreviewed_editorial_text"):
                self.run_gate(trusted_reviewed_text_hashes=trusted)

    def test_substitution_or_added_fake_source_claim_blocks(self):
        for other in (
            FACT.replace("verificadas", "garantidas"),
            "O produto é comprovadamente melhor e tem 50% desconto.",
        ):
            html = HTML.replace(FACT, other)
            with self.subTest(other=other), self.assertRaisesRegex(
                    FinalFactGateError, "html_fact_changed_or_unsupported"):
                self.run_gate(html)

    def test_unknown_or_missing_fact_id_blocks(self):
        for html in (
            HTML.replace("EVID_0_0", "EVID_0_1"),
            HTML.replace(' data-v31-fact-id="EVID_0_0"', ""),
        ):
            with self.subTest(html=html[:60]), self.assertRaisesRegex(
                    FinalFactGateError, "fact_ids_not_exactly_bound"):
                self.run_gate(html)

    def test_duplicate_id_blocks_even_when_text_exact(self):
        html = HTML.replace("</article>",
                            '<p><span data-v31-fact-id="EVID_0_0">'
                            + FACT + "</span></p></article>")
        with self.assertRaisesRegex(FinalFactGateError, "duplicate"):
            self.run_gate(html)

    def test_wrong_sku_and_expired_external_proof_fail(self):
        with self.assertRaisesRegex(FinalFactGateError, "package_not_verified"):
            self.run_gate(product_key=KEYS[1])
        with self.assertRaisesRegex(FinalFactGateError, "package_not_verified"):
            self.run_gate(now=NOW + timedelta(days=9))
        with self.assertRaisesRegex(FinalFactGateError, "package_not_verified"):
            self.run_gate(evidence_package=package(0, authorized=False))

    def test_html_and_script_injections_block(self):
        for extra, message in (
            ("<script>alert(1)</script>", "html_tag"),
            ('<p onclick="alert(1)">Clique</p>', "html_untrusted_attribute"),
            ('<p style="display:none">Texto</p>', "html_untrusted_attribute"),
            ('<a href="javascript:alert(1)">X</a>', "html_unsafe_url"),
            ('<p><span data-v31-fact-id="EVID_0_1"><img src="https://x.test/a"></span></p>',
             "fact_span_nested_markup_unsafe"),
        ):
            html = HTML.replace("</article>", extra + "</article>")
            with self.subTest(extra=extra), self.assertRaisesRegex(
                    FinalFactGateError, message):
                self.run_gate(html)

    def test_fact_marker_on_other_tag_rejected(self):
        html = HTML.replace('span data-v31-fact-id', 'div data-v31-fact-id')
        with self.assertRaisesRegex(FinalFactGateError,
                                    "fact_marker_wrong_element"):
            self.run_gate(html)

    def test_unbalanced_or_nested_markup_rejected(self):
        html = HTML.replace("</article>", "")
        with self.assertRaisesRegex(FinalFactGateError, "html_structure_invalid"):
            self.run_gate(html)

    def test_source_similar_model_never_promoted_to_fact(self):
        with self.assertRaisesRegex(FinalFactGateError, "package_not_verified"):
            self.run_gate(evidence_package=package(0, identity="SIMILAR_PRODUCT"))

    def test_used_ids_must_be_exact_and_cannot_be_duplicated(self):
        for ids in ([], ["EVID_0_0", "EVID_0_0"], ["EVID_0_0", "FAKE_1"]):
            with self.subTest(ids=ids), self.assertRaises(FinalFactGateError):
                self.run_gate(used_evidence_ids=ids)

    def test_literal_fact_is_not_made_true_by_bogus_editorial_hash(self):
        html = HTML.replace(FACT, "O material é garantido por 100 anos.")
        with self.assertRaisesRegex(FinalFactGateError,
                                    "html_fact_changed_or_unsupported"):
            self.run_gate(html, trusted_reviewed_text_hashes=HASHES + [
                reviewed_text_digest("O material é garantido por 100 anos.")
            ])


if __name__ == "__main__":
    unittest.main()
