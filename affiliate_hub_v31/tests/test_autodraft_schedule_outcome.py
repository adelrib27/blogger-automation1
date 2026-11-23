"""C134: bloqueios por cota e provas reais não podem ser confundidos."""
import json
import unittest

from affiliate_hub_v31.autodraft_schedule_outcome import summarize_draft_cycle


def classify(status, reason="", proof=None, draft_job="success", site="blogger_moveis"):
    receipt = {"site_key": site, "status": status, "reason": reason,
               "fingerprint": "f" * 64}
    return summarize_draft_cycle(
        site_key=site, verification_receipt=json.dumps(receipt),
        verified_draft=json.dumps(proof) if proof is not None else "",
        draft_job=draft_job, live_job="skipped")


def good_proof():
    return {"status": "DRAFT_VERIFIED", "site_key": "blogger_moveis",
            "fingerprint": "f" * 64, "draft_id": "4106024906916105222",
            "html_sha256": "a" * 64}


class DraftCycleOutcomeTests(unittest.TestCase):
    def test_budget_exhaustion_does_not_count_as_draft(self):
        value = classify("NO_NEW_OFFER", "research_budget_exhausted")
        self.assertEqual(value["draft_outcome"], "BLOCKED_RESEARCH_BUDGET")
        self.assertFalse(value["draft_verified_or_reconciled"])

    def test_source_rejection_is_not_operational_delivery(self):
        value = classify("NO_NEW_OFFER", "no_new_offer_with_trusted_source")
        self.assertEqual(value["draft_outcome"], "NO_APPROVED_NEW_OFFER")

    def test_site_cap_is_not_successful_delivery(self):
        value = classify("NO_NEW_OFFER", "site_quota_reached")
        self.assertEqual(value["draft_outcome"], "BLOCKED_SITE_ARTICLE_LIMIT")

    def test_ready_with_complete_matching_proof_confirms_draft(self):
        value = classify("READY", proof=good_proof())
        self.assertEqual(value["draft_outcome"], "DRAFT_VERIFIED")
        self.assertTrue(value["draft_verified_or_reconciled"])
        self.assertFalse(value["automatic_live_confirmation"])

    def test_success_without_proof_fails_closed(self):
        value = classify("READY")
        self.assertEqual(value["draft_outcome"], "UNVERIFIED")

    def test_proof_from_another_site_is_rejected(self):
        proof = good_proof()
        proof["site_key"] = "wordpress_casa"
        value = classify("READY", proof=proof)
        self.assertEqual(value["draft_outcome"], "UNVERIFIED")

    def test_own_valid_proof_does_not_override_failed_job(self):
        value = classify("USED", proof=good_proof(), draft_job="failure")
        self.assertEqual(value["draft_outcome"], "UNVERIFIED")

    def test_no_new_offer_cannot_include_delivery_proof(self):
        value = classify("NO_NEW_OFFER", "research_budget_exhausted", proof=good_proof())
        self.assertEqual(value["draft_outcome"], "UNVERIFIED")

    def test_malformed_json_never_confirms_draft(self):
        value = summarize_draft_cycle(
            site_key="blogger_moveis", verification_receipt="{",
            verified_draft="{", draft_job="success", live_job="success")
        self.assertEqual(value["draft_outcome"], "UNVERIFIED")
        self.assertFalse(value["automatic_live_confirmation"])


if __name__ == "__main__":
    unittest.main()
