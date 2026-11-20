"""C79 — S3 CAS backend contract and C78 integration, 0 external I/O."""
import hashlib
import io
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from affiliate_hub_v31.r2_state import R2State
from affiliate_hub_v31.r2_private_ready_backend import (
    R2PrivateReadyBackend, R2PrivateReadyError, ACCOUNT_ID, BUCKET,
    ENDPOINT, MAX_BYTES,
)
from affiliate_hub_v31.private_ready_envelope import (
    ImmutablePrivateReadyEnvelope, PrivateEnvelopeError, object_key,
)
from affiliate_hub_v31.tests.test_c78_private_ready_envelope import (
    SITE, CAMPAIGN, KEYS, KEY, ROUTES, make_html, fixture_review,
)


class S3Error(Exception):
    def __init__(self, code, status):
        self.response = {"Error": {"Code": code},
                         "ResponseMetadata": {"HTTPStatusCode": status}}


class FakeS3:
    def __init__(self, endpoint=ENDPOINT):
        self.meta = SimpleNamespace(endpoint_url=endpoint)
        self.objects = {}
        self.put_calls = []
        self.get_calls = []
        self.fail_put = None
        self.fail_get = None

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)
        if self.fail_put:
            raise self.fail_put
        key = kwargs["Key"]
        if key in self.objects:
            raise S3Error("PreconditionFailed", 412)
        self.objects[key] = {
            "body": kwargs["Body"], "metadata": kwargs["Metadata"]}
        return {"ETag": '"testing"'}

    def get_object(self, **kwargs):
        self.get_calls.append(kwargs)
        if self.fail_get:
            raise self.fail_get
        obj = self.objects.get(kwargs["Key"])
        if obj is None:
            raise S3Error("NoSuchKey", 404)
        return {
            "ContentLength": len(obj["body"]),
            "Metadata": obj["metadata"],
            "Body": io.BytesIO(obj["body"]),
        }


class R2PrivateBackendTests(unittest.TestCase):
    def setUp(self):
        patcher = patch("affiliate_hub_v31.private_ready_envelope.sites",
                        return_value=ROUTES)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.s3 = FakeS3()
        self.backend = R2PrivateReadyBackend(R2State(self.s3, BUCKET))
        self.key = object_key(SITE, CAMPAIGN, "a" * 64)
        self.body = b'{"schema":"synthetic"}'

    def test_atomic_if_none_match_and_correct_bucket_metadata(self):
        self.assertTrue(self.backend.put_if_absent(self.key, self.body))
        self.assertFalse(self.backend.put_if_absent(self.key, self.body))
        self.assertEqual(self.backend.get(self.key), self.body)
        self.assertEqual(len(self.s3.objects), 1)
        first = self.s3.put_calls[0]
        self.assertEqual(first["Bucket"], BUCKET)
        self.assertEqual(first["IfNoneMatch"], "*")
        self.assertEqual(first["Key"], self.key)
        self.assertEqual(first["Metadata"]["v31sha256"],
                         hashlib.sha256(self.body).hexdigest())
        self.assertRegex(first["Metadata"]["writeid"], r"^[a-f0-9]{32}$")
        self.assertEqual(first["CacheControl"], "private, no-store")
        self.assertEqual(self.s3.get_calls[0], {"Bucket": BUCKET, "Key": self.key})

    def test_endpoint_account_and_bucket_cannot_be_swapped(self):
        for storage in (R2State(FakeS3(
                "https://b1515400afe32581994c4d3f038f835f.r2.cloudflarestorage.com"
                ), BUCKET),
                R2State(self.s3, "outro-bucket")):
            with self.subTest(bucket=storage.bucket), self.assertRaises(
                R2PrivateReadyError
            ):
                R2PrivateReadyBackend(storage)
        with self.assertRaises(R2PrivateReadyError):
            R2PrivateReadyBackend(object())

    def test_from_environment_rejects_wrong_account_before_client_created(self):
        with patch("affiliate_hub_v31.r2_private_ready_backend.R2State.from_env") as mk:
            for env in (
                {}, {"V31_EDITORIAL_R2_ACCOUNT_ID": "b1515400afe32581994c4d3f038f835f",
                     "V31_EDITORIAL_R2_BUCKET": BUCKET},
                {"V31_EDITORIAL_R2_ACCOUNT_ID": ACCOUNT_ID,
                 "V31_EDITORIAL_R2_BUCKET": "vida-pet"},
            ):
                with self.subTest(env_keys=list(env)), self.assertRaises(
                    R2PrivateReadyError
                ):
                    R2PrivateReadyBackend.from_environment(env)
            mk.assert_not_called()
            mk.return_value = R2State(self.s3, BUCKET)
            r = R2PrivateReadyBackend.from_environment({
                "V31_EDITORIAL_R2_ACCOUNT_ID": ACCOUNT_ID,
                "V31_EDITORIAL_R2_BUCKET": BUCKET,
            })
            self.assertIsInstance(r, R2PrivateReadyBackend)
            self.assertEqual(mk.call_count, 1)

    def test_no_get_before_put_no_delete_and_no_list(self):
        self.backend.put_if_absent(self.key, self.body)
        self.assertEqual(len(self.s3.get_calls), 0)
        self.assertFalse(hasattr(self.backend, "delete"))
        self.assertFalse(hasattr(self.backend, "list"))

    def test_412_only_valid_conflict_code_409_403_timeout_fail_closed(self):
        for exception in (
            S3Error("ObjectLockedByBucketPolicy", 409),
            S3Error("AccessDenied", 403),
            S3Error("PreconditionFailed", 400),
            TimeoutError("private data in error"),
        ):
            self.s3.fail_put = exception
            with self.subTest(type=type(exception).__name__), self.assertRaisesRegex(
                R2PrivateReadyError, "conditional_write_failed"
            ) as ctx:
                self.backend.put_if_absent(self.key, self.body)
            self.assertNotIn("private data", str(ctx.exception))
        self.assertEqual(len(self.s3.objects), 0)

    def test_no_silent_get_403_timeout_and_bogus_404(self):
        for exception in (
            S3Error("AccessDenied", 403),
            TimeoutError("timeout"),
            S3Error("AccessDenied", 404),
        ):
            self.s3.fail_get = exception
            with self.subTest(error=type(exception).__name__), self.assertRaisesRegex(
                R2PrivateReadyError, "get_failed_closed"
            ):
                self.backend.get(self.key)
        self.s3.fail_get = S3Error("NoSuchKey", 404)
        self.assertIsNone(self.backend.get(self.key))

    def test_unregistered_or_malformed_key_denied_before_any_sdk_request(self):
        bad = [
            "v31-editorial/CURRENT.json",
            "v31/private-ready/v1/../" + "a"*64,
            self.key.replace("/aa/", "/ff/"),
            self.key.replace("/" + CAMPAIGN + "/", "/exemplowp/"),
            self.key.replace("/" + SITE + "/", "/outro_blog/"),
            self.key.replace(".json", ".txt"),
        ]
        for key in bad:
            with self.subTest(key=key[:40]), self.assertRaises(R2PrivateReadyError):
                self.backend.put_if_absent(key, self.body)
            with self.assertRaises(R2PrivateReadyError):
                self.backend.get(key)
        self.assertEqual(len(self.s3.put_calls), 0)
        self.assertEqual(len(self.s3.get_calls), 0)

    def test_get_readback_metadata_mismatch_invalid_or_large_rejected(self):
        self.backend.put_if_absent(self.key, self.body)
        obj = self.s3.objects[self.key]
        obj["body"] += b"tamper"
        with self.assertRaisesRegex(R2PrivateReadyError, "hash_readback_mismatch"):
            self.backend.get(self.key)
        obj["body"] = b"x" * (MAX_BYTES + 1)
        with self.assertRaisesRegex(R2PrivateReadyError, "untrusted_response"):
            self.backend.get(self.key)
        obj["body"] = self.body
        obj["metadata"] = {}
        with self.assertRaisesRegex(R2PrivateReadyError, "untrusted_response"):
            self.backend.get(self.key)

    def test_c78_complete_envelope_r2_sdk_mocked_idempotent(self):
        wrapper = ImmutablePrivateReadyEnvelope(backend=self.backend)
        args = {
            "site_key": SITE, "campaign": CAMPAIGN,
            "product_key": KEYS[0], "content_html": make_html(),
            "attestation": fixture_review(), "independent_review_key": KEY,
        }
        first = wrapper.save(**args)
        self.assertEqual(first["status"], "PRIVATE_ENVELOPE_CREATED")
        self.assertEqual(wrapper.save(**args)["status"],
                         "PRIVATE_ENVELOPE_ALREADY_VALID")
        loaded = wrapper.load(
            site_key=SITE, campaign=CAMPAIGN,
            html_sha256=first["html_sha256"],
            independent_review_key=KEY,
        )
        self.assertEqual(loaded["html_content"], make_html())
        self.assertFalse(loaded["live_publication_authorized"])
        self.assertEqual(len(self.s3.objects), 1)

    def test_r2_same_key_different_review_manifest_fails_closed(self):
        wrapper = ImmutablePrivateReadyEnvelope(backend=self.backend)
        args = dict(
            site_key=SITE, campaign=CAMPAIGN,
            product_key=KEYS[0], content_html=make_html(),
            attestation=fixture_review(), independent_review_key=KEY,
        )
        wrapper.save(**args)
        changed = fixture_review()
        changed["signature"] = "a" * 64
        with self.assertRaises(PrivateEnvelopeError):
            wrapper.save(**{**args, "attestation": changed})
        self.assertEqual(len(self.s3.objects), 1)


if __name__ == "__main__":
    unittest.main()
