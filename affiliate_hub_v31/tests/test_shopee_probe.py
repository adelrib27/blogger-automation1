"""Regressões offline do único probe autorizado para o Hub Editorial."""
import hashlib
import json
import urllib.error
import unittest
from unittest.mock import patch

from affiliate_hub_v31 import shopee_probe as api


class FakeResponse:
    status = 200

    def __init__(self, document):
        self.document = json.dumps(document).encode("utf-8") if isinstance(document, dict) else document

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, *_):
        return self.document


class ShopeeProbeTests(unittest.TestCase):
    def test_signature_matches_preexisting_contract(self):
        body = api.payload()
        expected = hashlib.sha256(("123" + "1770000000" + body + "TEST_SECRET").encode()).hexdigest()
        value = api.authorization("123", "TEST_SECRET", body, 1770000000)
        self.assertEqual(value, f"SHA256 Credential=123, Timestamp=1770000000, Signature={expected}")

    def test_missing_credentials_fail_closed(self):
        with self.assertRaises(ValueError):
            api.authorization("", "x", "{}", 1)

    def test_success_reads_only_one_product_and_no_export(self):
        response = FakeResponse({"data": {"productOfferV2": {
            "nodes": [{"itemId": "123"}], "pageInfo": {"page": 1, "limit": 1, "hasNextPage": True}
        }}})
        with patch.object(api.urllib.request, "urlopen", return_value=response) as mocked:
            result = api.probe("APP_TEST", "SECRET_TEST")
        self.assertEqual(result, "V31_SHOPEE_API_PASS")
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, api.ENDPOINT)
        self.assertEqual(request.method, "POST")
        self.assertEqual(json.loads(request.data)["operationName"], "V31EditorialSafeProbe")
        self.assertIn("limit: 1", request.data.decode())
        self.assertNotIn("SECRET_TEST", request.data.decode())

    def test_graphql_errors_are_not_logged(self):
        with patch.object(api.urllib.request, "urlopen", return_value=FakeResponse({
            "errors": [{"message": "SECRET_TEST credentials rejected"}]
        })):
            self.assertEqual(api.probe("APP_TEST", "SECRET_TEST"), "V31_SHOPEE_API_GRAPHQL_ERROR")

    def test_http_errors_are_sanitized(self):
        exception = urllib.error.HTTPError(api.ENDPOINT, 401, "SECRET_TEST", {}, None)
        with patch.object(api.urllib.request, "urlopen", side_effect=exception):
            self.assertEqual(api.probe("APP_TEST", "SECRET_TEST"), "V31_SHOPEE_API_HTTP_ERROR_401")

    def test_invalid_response_is_rejected(self):
        with patch.object(api.urllib.request, "urlopen", return_value=FakeResponse(b"<html>SECRET_TEST</html>")):
            self.assertEqual(api.probe("APP_TEST", "SECRET_TEST"), "V31_SHOPEE_API_INVALID_JSON")


if __name__ == "__main__":
    unittest.main()
