from __future__ import annotations

import unittest

import browser_provision as bp
from resilient_create import (
    build_address_candidates,
    execute_create_resilient,
    is_safe_pre_save_retry,
)


class ResilientCreateTests(unittest.TestCase):
    def test_candidates_keep_requested_first_and_are_valid(self):
        candidates = build_address_candidates(
            "meu-blog-teste",
            max_attempts=5,
            seed="1234567890",
        )
        self.assertEqual(candidates[0], "meu-blog-teste")
        self.assertEqual(len(candidates), 5)
        self.assertEqual(len(set(candidates)), 5)
        for candidate in candidates:
            self.assertLessEqual(len(candidate), 63)
            self.assertEqual(bp.CreateBlogRequest.build("x", candidate).address, candidate)

    def test_retries_only_before_save_then_succeeds(self):
        calls = []

        def fake_create(title, address, **kwargs):
            calls.append(address)
            if len(calls) < 3:
                raise bp.SafeAutomationError(
                    "O endereço solicitado foi rejeitado pelo Blogger. "
                    "Nenhum clique em SALVAR foi executado."
                )
            return {
                "status": "CREATE_BLOG_VALIDATED",
                "title": title,
                "address": address,
                "blog_id": "123",
                "expected_url": f"https://{address}.blogspot.com/",
                "public_validation": {"ok": True, "status": 200},
            }

        result = execute_create_resilient(
            "Teste",
            "meu-blog-teste",
            confirm=bp.CREATE_CONFIRMATION,
            max_address_attempts=5,
            create_fn=fake_create,
        )
        self.assertEqual(len(calls), 3)
        self.assertEqual(result["address_attempt_count"], 3)
        self.assertTrue(result["address_retry_enabled"])
        self.assertEqual(result["blog_id"], "123")

    def test_does_not_retry_error_that_may_be_after_save(self):
        calls = []

        def fake_create(title, address, **kwargs):
            calls.append(address)
            raise bp.SafeAutomationError(
                "O Blogger aparenta ter criado o blog, mas a URL pública não foi validada com HTTP 200."
            )

        with self.assertRaises(bp.SafeAutomationError):
            execute_create_resilient(
                "Teste",
                "meu-blog-teste",
                confirm=bp.CREATE_CONFIRMATION,
                max_address_attempts=5,
                create_fn=fake_create,
            )
        self.assertEqual(len(calls), 1)

    def test_retry_classifier_requires_explicit_no_save_marker(self):
        self.assertTrue(
            is_safe_pre_save_retry(
                bp.SafeAutomationError("Nenhum clique em SALVAR foi executado.")
            )
        )
        self.assertFalse(
            is_safe_pre_save_retry(
                bp.SafeAutomationError("Falha após salvar.")
            )
        )


if __name__ == "__main__":
    unittest.main()
