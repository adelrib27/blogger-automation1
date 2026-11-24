"""C146: apenas rótulos estáticos de etapa, nunca rede, payloads ou segredos."""
import contextlib
import io
import sys
import unittest
from unittest.mock import patch

from affiliate_hub_v31 import autonomous_review as review


class ReviewFailureStagesTests(unittest.TestCase):
    def tearDown(self):
        review._mark_stage("boot")

    def test_all_stages_are_fixed_identifiers(self):
        self.assertGreaterEqual(len(review.SAFE_STAGES), 12)
        for stage in review.SAFE_STAGES:
            self.assertRegex(stage, r"^[a-z0-9_]+$")
            self.assertEqual(len(stage), len(stage.encode("ascii")))

    def test_rejects_dynamic_sensitive_error_message_as_stage(self):
        review._mark_stage("d1_connect")
        with self.assertRaisesRegex(review.VerificationError, "diagnostic_stage_untrusted"):
            review._mark_stage("https://secret.example/token?key=private")
        self.assertEqual(review._safe_failure_stage(), "d1_connect")

    def test_failure_stage_is_allowed_constant(self):
        review._mark_stage("offer_image")
        self.assertEqual(review._safe_failure_stage(), "offer_image")

    def test_failed_exception_never_prints_data_from_exception(self):
        secret = "SECRET_NOT_FOR_LOGS"
        def fail(**kwargs):
            review._mark_stage("external_research")
            raise AttributeError(secret)
        output = io.StringIO()
        with patch.object(review, "run", side_effect=fail), \
             patch.object(sys, "argv", ["review", "--site-key", "blogger_moveis_para_cada_canto",
                                      "--history", "/dev/null"]), \
             patch("pathlib.Path.read_text", return_value='{"site_key":"blogger_moveis_para_cada_canto","keys":[],"slugs":[],"prose":[],"count":0}'), \
             contextlib.redirect_stdout(output):
            exit_code = review.main()
        self.assertEqual(exit_code, 1)
        self.assertEqual(output.getvalue().strip(),
                         "autonomous_verification_failed_closed:external_research")
        self.assertNotIn(secret, output.getvalue())

    def test_main_resets_stage_between_invocations(self):
        def fail(**kwargs):
            raise KeyError("private-user-data")
        review._mark_stage("ready_promotion")
        output = io.StringIO()
        with patch.object(review, "run", side_effect=fail), \
             patch.object(sys, "argv", ["review", "--site-key", "blogger_moveis_para_cada_canto",
                                      "--history", "/dev/null"]), \
             patch("pathlib.Path.read_text", return_value='{"site_key":"blogger_moveis_para_cada_canto","keys":[],"slugs":[],"prose":[],"count":0}'), \
             contextlib.redirect_stdout(output):
            code = review.main()
        self.assertEqual(code, 1)
        self.assertEqual(output.getvalue().strip(),
                         "autonomous_verification_failed_closed:boot")

    def test_expected_verification_errors_keep_existing_fail_closed_contract(self):
        def fail(**kwargs):
            review._mark_stage("external_research")
            raise review.VerificationError("research_budget_exhausted")
        output = io.StringIO()
        with patch.object(review, "run", side_effect=fail), \
             patch.object(sys, "argv", ["review", "--site-key", "blogger_moveis_para_cada_canto",
                                      "--history", "/dev/null"]), \
             patch("pathlib.Path.read_text", return_value='{"site_key":"blogger_moveis_para_cada_canto","keys":[],"slugs":[],"prose":[],"count":0}'), \
             contextlib.redirect_stdout(output):
            code = review.main()
        self.assertEqual(code, 1)
        self.assertEqual(output.getvalue().strip(), "research_budget_exhausted")

    def test_live_publish_not_referenced_by_diagnostic_stages(self):
        self.assertNotIn("live", review.SAFE_STAGES)
        self.assertNotIn("publish", review.SAFE_STAGES)

    def test_no_dynamic_or_unknown_stages(self):
        with self.assertRaises(review.VerificationError):
            review._mark_stage("exception:500")
        with self.assertRaises(review.VerificationError):
            review._mark_stage("web_request?authorization=123")


if __name__ == "__main__":
    unittest.main()
