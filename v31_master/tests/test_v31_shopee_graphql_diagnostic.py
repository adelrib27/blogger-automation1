#!/usr/bin/env python3
"""Contrato offline do diagnostico diferencial da API Shopee, sem secrets reais."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab_shopee_graphql_diagnostic as diag


class TestDifferentialShopeeDiagnostic(unittest.TestCase):
    def test_http_200_graphql_10000_is_error(self):
        r = diag.sanitize_reply(200, b'{"errors":[{"message":"not-for-log","extensions":{"code":10000}}]}', "offers_shape")
        self.assertEqual(r["status"], "GRAPHQL_ERROR")
        self.assertEqual(r["graphql_error_codes"], [10000])
        self.assertNotIn("not-for-log", json.dumps(r))

    def test_invalid_signature_code_visible_only(self):
        r = diag.sanitize_reply(200, b'{"errors":[{"extensions":{"code":10020}}]}', "graphql_root")
        self.assertEqual(r["graphql_error_codes"], [10020])

    def test_rate_limit_code(self):
        r = diag.sanitize_reply(200, b'{"errors":[{"extensions":{"code":"10030"}}]}', "offers_shape")
        self.assertEqual(r["graphql_error_codes"], [10030])

    def test_shape_success(self):
        r = diag.sanitize_reply(200, b'{"data":{"productOfferV2":{"nodes":[{"itemId":"900","productName":"test"}]}}}', "offers_fields")
        self.assertEqual(r["status"], "GRAPHQL_OK")
        self.assertEqual(r["offers_count"], 1)
        self.assertNotIn("productName", json.dumps(r))
        self.assertNotIn("900", json.dumps(r))

    def test_root_success(self):
        r = diag.sanitize_reply(200, b'{"data":{"__typename":"Query"}}', "graphql_root")
        self.assertEqual(r["status"], "GRAPHQL_OK")
        self.assertTrue(r["api_data"])

    def test_nonjson_no_raw_logging(self):
        r = diag.sanitize_reply(502, b'<error>secret-value</error>', "graphql_root")
        self.assertEqual(r["status"], "NON_JSON")
        self.assertNotIn("secret-value", json.dumps(r))

    def test_summary_operations_specific_failure(self):
        rs = [
            {"probe":"graphql_root","status":"GRAPHQL_OK"},
            {"probe":"offers_shape","status":"GRAPHQL_ERROR"},
            {"probe":"offers_fields","status":"GRAPHQL_ERROR"},
            {"probe":"offers_filters","status":"GRAPHQL_ERROR"},
        ]
        self.assertEqual(diag.summarize(rs), "ROOT_OK_OFFERS_ERROR")

    def test_summary_one_query_ok(self):
        rs = [
            {"probe":"graphql_root","status":"GRAPHQL_OK"},
            {"probe":"offers_shape","status":"GRAPHQL_OK"},
        ]
        self.assertEqual(diag.summarize(rs), "OFFERS_AT_LEAST_ONE_QUERY_OK")

    def test_signs_same_utf8_body_sent_and_no_blogger(self):
        response = MagicMock()
        response.status = 200
        response.read.return_value = b'{"data":{"__typename":"Query"}}'
        context = MagicMock()
        context.__enter__.return_value = response
        with patch.object(diag.urllib.request, "urlopen", return_value=context) as urlopen:
            with patch.object(diag.time, "time", return_value=1730000000):
                r = diag.send_query("graphql_root", "query V31Probe { __typename }", "1234", "fake-offline-secret")
        self.assertEqual(r["status"], "GRAPHQL_OK")
        request = urlopen.call_args[0][0]
        self.assertEqual(request.get_method(), "POST")
        self.assertIn(b'"operationName":"V31Probe"', request.data)
        self.assertTrue(request.get_header("Authorization").startswith("SHA256 Credential=1234"))
        self.assertEqual(request.full_url, diag.ENDPOINT)
        self.assertEqual(diag.MAX_CALLS, 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
