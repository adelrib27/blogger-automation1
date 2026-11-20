"""C78 immutable private envelope: synthetic atomic object backend, no R2/CMS."""
import hashlib
import hmac
import json
import unittest
from unittest.mock import patch

from affiliate_hub_v31 import private_ready_envelope as private
from affiliate_hub_v31 import reviewed_ready_promotion as review
from affiliate_hub_v31.tests.test_c77_reviewed_ready_promotion import (
    SITE, CAMPAIGN, ARTICLE_URL, TITLE, QUERY, ANGLE, HASHES,
    HOME, KEY, make_html,
)
from affiliate_hub_v31.tests.test_c69_universal_evidence_ready import (
    KEYS, ROUTES,
)


class FakeConditionalStore:
    """True atomic CAS in fixture; production MUST use R2 conditional PUT."""
    def __init__(self):
        self.objects = {}
        self.put_calls = 0
        self.get_calls = 0

    def put_if_absent(self, key, blob):
        self.put_calls += 1
        if key in self.objects:
            return False
        self.objects[key] = blob
        return True

    def get(self, key):
        self.get_calls += 1
        return self.objects.get(key)


def fixture_review(html=None):
    html = make_html() if html is None else html
    material = review.review_payload(
        site_key=SITE, campaign=CAMPAIGN,
        product_key=KEYS[0], site_url=HOME,
        article_url=ARTICLE_URL, article_title=TITLE,
        primary_query=QUERY, angle=ANGLE,
        html_sha256=hashlib.sha256(html.encode("utf-8")).hexdigest(),
        evidence_sha256="a"*64,
        seo_context_sha256="b"*64,
        reviewed_text_hashes=HASHES,
    )
    raw = json.dumps(material, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    signature = hmac.new(KEY, raw, hashlib.sha256).hexdigest()
    return {"payload": material, "signature": signature}


class PrivateReadyEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeConditionalStore()
        self.store = private.ImmutablePrivateReadyEnvelope(backend=self.backend)
        pt = patch("affiliate_hub_v31.private_ready_envelope.sites",
                   return_value=ROUTES)
        pt.start()
        self.addCleanup(pt.stop)

    def save(self, **overrides):
        data = {
            "site_key": SITE, "campaign": CAMPAIGN, "product_key": KEYS[0],
            "content_html": make_html(), "attestation": fixture_review(),
            "independent_review_key": KEY,
        }
        data.update(overrides)
        return self.store.save(**data)

    def test_exact_bytes_atomic_write_readback_and_idempotent_replay(self):
        first = self.save()
        self.assertEqual(first["status"], "PRIVATE_ENVELOPE_CREATED")
        self.assertFalse(first["live_publication_authorized"])
        self.assertEqual(first["publication_calls"], 0)
        self.assertEqual(self.backend.put_calls, 1)
        self.assertEqual(self.backend.get_calls, 1)
        self.assertTrue(first["object_key"].startswith(
            "v31/private-ready/v1/" + SITE + "/" + CAMPAIGN + "/"))
        again = self.save()
        self.assertEqual(again["status"], "PRIVATE_ENVELOPE_ALREADY_VALID")
        self.assertEqual(len(self.backend.objects), 1)
        loaded = self.store.load(
            site_key=SITE, campaign=CAMPAIGN,
            html_sha256=first["html_sha256"],
            independent_review_key=KEY,
        )
        self.assertEqual(loaded["html_content"], make_html())
        self.assertFalse(loaded["live_publication_authorized"])

    def test_wrong_tenant_and_path_traversal_denied_before_storage(self):
        for site, campaign in (
            ("../malicious", CAMPAIGN),
            (SITE, "exemplowp"),
            ("wordpress_novo_exemplo", CAMPAIGN),
            ("unknown_unregistered_site", CAMPAIGN),
        ):
            with self.subTest(site=site), self.assertRaises(
                private.PrivateEnvelopeError
            ):
                self.save(site_key=site, campaign=campaign)
        self.assertEqual(self.backend.put_calls, 0)

    def test_crossblog_review_replay_never_creates_envelope(self):
        with self.assertRaisesRegex(
            private.PrivateEnvelopeError, "review_binding_mismatch"
        ):
            self.save(
                site_key="wordpress_novo_exemplo",
                campaign="exemplowp",
            )
        self.assertEqual(self.backend.put_calls, 0)

    def test_changed_html_without_new_signature_denied(self):
        html = make_html().replace("compra planejada", "anúncio imperdível")
        with self.assertRaises(private.PrivateEnvelopeError):
            self.save(content_html=html)
        self.assertEqual(self.backend.put_calls, 0)

    def test_bad_key_bad_signature_fails_without_storage(self):
        for key in (b"", b"wrong-key-material-with-more-than-32-bytes"):
            with self.subTest(key_len=len(key)), self.assertRaises(
                private.PrivateEnvelopeError
            ):
                self.save(independent_review_key=key)
        self.assertEqual(self.backend.put_calls, 0)

    def test_existing_key_cannot_be_overwritten_with_other_manifest(self):
        first = self.save()
        alt = fixture_review()
        alt["payload"]["article_title"] = "Outro título do mesmo artigo"
        raw = json.dumps(alt["payload"], ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
        alt["signature"] = hmac.new(KEY, raw, hashlib.sha256).hexdigest()
        with self.assertRaisesRegex(
            private.PrivateEnvelopeError, "readback_mismatch"
        ):
            self.save(attestation=alt)
        self.assertEqual(len(self.backend.objects), 1)
        old = self.store.load(
            site_key=SITE, campaign=CAMPAIGN,
            html_sha256=first["html_sha256"], independent_review_key=KEY)
        self.assertEqual(old["html_content"], make_html())

    def test_corrupted_body_or_noncanonical_json_rejected_on_load(self):
        saved = self.save()
        key = saved["object_key"]
        valid = self.backend.objects[key]
        for tampered in (valid + b" ", valid.replace(
                b'"html_sha256"', b'"tampered_hash"'), b'{"invalid":true}'):
            with self.subTest(length=len(tampered)):
                self.backend.objects[key] = tampered
                with self.assertRaisesRegex(private.PrivateEnvelopeError,
                                            "integrity_failed_closed"):
                    self.store.load(
                        site_key=SITE, campaign=CAMPAIGN,
                        html_sha256=saved["html_sha256"],
                        independent_review_key=KEY)
        self.backend.objects[key] = valid
        self.assertEqual(self.store.load(
            site_key=SITE, campaign=CAMPAIGN,
            html_sha256=saved["html_sha256"], independent_review_key=KEY
        )["html_content"], make_html())

    def test_wrong_or_missing_backend_contract_fails_closed(self):
        with self.assertRaisesRegex(private.PrivateEnvelopeError, "backend_required"):
            private.ImmutablePrivateReadyEnvelope(backend=object())

        class BadCAS(FakeConditionalStore):
            def put_if_absent(self, key, blob):
                return 1

        with self.assertRaisesRegex(private.PrivateEnvelopeError, "cas_invalid"):
            private.ImmutablePrivateReadyEnvelope(backend=BadCAS()).save(
                site_key=SITE, campaign=CAMPAIGN, product_key=KEYS[0],
                content_html=make_html(), attestation=fixture_review(),
                independent_review_key=KEY)

    def test_no_cms_or_firecrawl_api_methods_or_live_approval(self):
        self.assertFalse(hasattr(self.store, "publish"))
        self.assertFalse(hasattr(self.store, "create_post"))
        self.assertFalse(hasattr(self.store, "firecrawl"))
        self.assertFalse(hasattr(self.store, "convert_shopee_link"))


if __name__ == "__main__":
    unittest.main()
