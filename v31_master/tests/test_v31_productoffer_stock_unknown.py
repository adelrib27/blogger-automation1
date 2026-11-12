#!/usr/bin/env python3
"""LAB SAFE: productOfferV2 nao tem evidencia homologada de estoque."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import store_stock_commission_safe as policy
from replication_safe import GateError

ITEM = "1000000001"

def response(nodes, errors=None):
    d = {"data": {"productOfferV2": {"nodes": nodes}}}
    if errors is not None:
        d["errors"] = errors
    return d

class TestProductOfferDoesNotMeanInventory(unittest.TestCase):
    def test_item_absent_is_unknown_not_out_of_stock(self):
        x = policy.classify_product_offer_visibility(ITEM, response([]))
        self.assertEqual(x["discovery_status"], "NOT_LISTED")
        self.assertEqual(x["stock_status"], policy.UNKNOWN)

    def test_item_present_still_no_stock_confirmation(self):
        x = policy.classify_product_offer_visibility(
            ITEM, response([{"itemId": ITEM, "productName": "Mouse sem fio"}]))
        self.assertEqual(x["discovery_status"], "LISTED")
        self.assertEqual(x["stock_status"], policy.UNKNOWN)

    def test_fake_stock_zero_on_offer_is_not_authority(self):
        x = policy.classify_product_offer_visibility(ITEM,
            response([{"itemId": ITEM, "stock": 0, "stock_units": 0, "soldOut": True}]))
        self.assertEqual(x["stock_status"], policy.UNKNOWN)

    def test_graphql_10000_is_unknown(self):
        d = {"errors": [{"extensions": {"code": 10000}, "message": "System Error"}]}
        x = policy.classify_product_offer_visibility(ITEM, d)
        self.assertEqual(x["discovery_status"], "API_GRAPHQL_ERROR")
        self.assertEqual(x["stock_status"], policy.UNKNOWN)

    def test_http_200_with_partial_errors_still_unknown(self):
        d = response([{"itemId": ITEM}], errors=[{"extensions": {"code": 10000}}])
        x = policy.classify_product_offer_visibility(ITEM, d)
        self.assertEqual(x["discovery_status"], "API_GRAPHQL_ERROR")
        self.assertEqual(x["stock_status"], policy.UNKNOWN)

    def test_http_error_is_unknown(self):
        x = policy.classify_product_offer_visibility(ITEM, response([]), http_status=503)
        self.assertEqual(x["discovery_status"], "API_UNAVAILABLE")
        self.assertEqual(x["stock_status"], policy.UNKNOWN)

    def test_no_api_response_is_unknown(self):
        x = policy.classify_product_offer_visibility(ITEM, None)
        self.assertEqual(x["discovery_status"], "API_UNAVAILABLE")
        self.assertEqual(x["stock_status"], policy.UNKNOWN)

    def test_null_nodes_is_unknown(self):
        x = policy.classify_product_offer_visibility(
            ITEM, {"data": {"productOfferV2": {"nodes": None}}})
        self.assertEqual(x["discovery_status"], "INVALID_DISCOVERY")
        self.assertEqual(x["stock_status"], policy.UNKNOWN)

    def test_other_item_in_search_is_not_proof(self):
        x = policy.classify_product_offer_visibility(ITEM, response([{"itemId": "222222222"}]))
        self.assertEqual(x["discovery_status"], "NOT_LISTED")
        self.assertEqual(x["stock_status"], policy.UNKNOWN)

    def test_invalid_id_is_blocked(self):
        with self.assertRaises(GateError):
            policy.classify_product_offer_visibility("?", response([]))

    def test_stock_inference_requires_independent_observations(self):
        from datetime import datetime, timezone
        when = datetime(2026,11,12,15,0,tzinfo=timezone.utc)
        x = policy.classify_product_offer_visibility(ITEM, response([]))
        y = policy.stock_status(ITEM, [], now=when)
        self.assertEqual(x["stock_status"], policy.UNKNOWN)
        self.assertEqual(y, policy.UNKNOWN)

    def test_discovery_clean_only_on_ok_envelope(self):
        policy.require_clean_discovery_metadata({
            "operation": "productOfferV2", "http_status": 200,
            "query_status": "OK", "graphql_error_codes": []})

    def test_discovery_error_code_blocks_even_http200(self):
        with self.assertRaises(GateError):
            policy.require_clean_discovery_metadata({
                "operation": "productOfferV2", "http_status": 200,
                "query_status": "OK", "graphql_error_codes": [10000]})

    def test_missing_discovery_envelope_blocked(self):
        with self.assertRaises(GateError):
            policy.require_clean_discovery_metadata(None)

if __name__ == "__main__":
    unittest.main(verbosity=2)
