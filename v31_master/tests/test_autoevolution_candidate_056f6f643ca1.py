import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shopee_r2_safe import GateError, signed_query


class TestShopeeOfferEnvelope(unittest.TestCase):
    def query(self, payload):
        with patch('shopee_r2_safe.urllib.request.urlopen') as request:
            response = request.return_value.__enter__.return_value
            response.status = 200
            response.read.return_value = json.dumps(payload).encode()
            return signed_query('teste', 'local-id', 'local-secret')

    def test_incomplete_envelopes_raise_controlled_error(self):
        for payload in (
            {},
            {'data': []},
            {'data': {'productOfferV2': 'invalid'}},
            {'data': {'productOfferV2': {}}},
            {'data': {'productOfferV2': {'nodes': None}}},
            {'data': {'productOfferV2': {'nodes': {}}}},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(Exception) as caught:
                    self.query(payload)
                self.assertIsInstance(caught.exception, GateError)
                self.assertEqual(str(caught.exception), 'Nodes da Shopee ausentes')

    def test_explicit_list_remains_valid(self):
        for nodes in ([], [{'itemId': '123'}]):
            with self.subTest(nodes=nodes):
                self.assertEqual(self.query({'data': {'productOfferV2': {'nodes': nodes}}}), nodes)
