#!/usr/bin/env python3
"""Regressao do gateway mínimo de ofertas no LAB: sem credenciais reais."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shopee_r2_safe as gateway
from replication_safe import GateError


def mocked_request(data, status=200):
    res = MagicMock()
    res.status = status
    res.read.return_value = json.dumps(data).encode("utf-8")
    context = MagicMock()
    context.__enter__.return_value = res
    return context


class TestMinimalShopeeQuery(unittest.TestCase):
    def test_minimal_fields_no_list_type_or_sort_type(self):
        with patch.object(gateway.urllib.request, "urlopen",
                          return_value=mocked_request({"data": {"productOfferV2": {"nodes": [
                              {"itemId": "1000000", "productName": "Mouse USB"}
                          ]}}})) as urlopen:
            products = gateway.signed_query("mouse", "1234", "fake-secret-for-offline-test")
        self.assertEqual(len(products), 1)
        request = urlopen.call_args[0][0]
        body = json.loads(request.data)
        query = body["query"]
        self.assertIn("productOfferV2(keyword:", query)
        self.assertIn("itemId productName offerLink imageUrl priceMin shopId ratingStar sales", query)
        self.assertNotIn("listType:", query)
        self.assertNotIn("sortType:", query)
        self.assertNotIn("generateShortLink", query)
        self.assertEqual(request.get_method(), "POST")

    def test_graphql_10000_rejects_without_partial_results(self):
        data = {"data": {"productOfferV2": {"nodes": [{"itemId": "1000000"}]}},
                "errors": [{"extensions": {"code": 10000}, "message": "System Error"}]}
        with patch.object(gateway.urllib.request, "urlopen", return_value=mocked_request(data)):
            with self.assertRaises(GateError):
                gateway.signed_query("mouse", "1234", "fake-secret-for-offline-test")

    def test_invalid_nodes_rejects(self):
        data = {"data": {"productOfferV2": {"nodes": "not-list"}}}
        with patch.object(gateway.urllib.request, "urlopen", return_value=mocked_request(data)):
            with self.assertRaises(GateError):
                gateway.signed_query("mouse", "1234", "fake-secret-for-offline-test")

    def test_network_failure_rejects(self):
        with patch.object(gateway.urllib.request, "urlopen", side_effect=TimeoutError()):
            with self.assertRaises(GateError):
                gateway.signed_query("mouse", "1234", "fake-secret-for-offline-test")

    def test_no_blogger_dependency_in_gateway(self):
        import inspect
        source = inspect.getsource(gateway)
        self.assertNotIn("blogger.pages().update", source)
        self.assertNotIn("blogger.posts().update", source)
        self.assertEqual(gateway.REQUIRED, 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
