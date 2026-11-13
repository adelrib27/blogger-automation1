#!/usr/bin/env python3
"""Deterministic reviewed recipes. No LLM, API key, HTTP, or generated commands."""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path
from candidate import digest, git_blob, regression_path, validate
from engine import ALLOWED_REPO, ALLOWED_BRANCH, SafetyStop

SOURCE = 'v31_master/store_stock_commission_safe.py'
RECIPE = 'strict-affiliate-verification-v1'
BEFORE = '    if not verified_affiliate_response or not isinstance(raw, dict):'
AFTER = '    if verified_affiliate_response is not True or not isinstance(raw, dict):'
REGRESSION = '''import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from store_stock_commission_safe import commission_eligible

class TestStrictAffiliateVerification(unittest.TestCase):
    def test_only_boolean_true_confirms_origin(self):
        for unverified in ('false', 'true', 1, [True], {'verified': True}, False, None):
            with self.subTest(value=unverified):
                self.assertFalse(commission_eligible({'commissionRate': '0.015'},
                                                    verified_affiliate_response=unverified))

    def test_confirmed_positive_commission_stays_eligible(self):
        self.assertTrue(commission_eligible({'commissionRate': '0.0001'},
                                           verified_affiliate_response=True))

    def test_zero_commission_stays_ineligible(self):
        self.assertFalse(commission_eligible({'commissionRate': '0'},
                                            verified_affiliate_response=True))
'''


DISCOVERY_SOURCE = 'v31_master/shopee_r2_safe.py'
DISCOVERY_RECIPE = 'require-shopee-offer-nodes-v1'
DISCOVERY_BEFORE = '''    nodes = (((data.get("data") or {}).get("productOfferV2") or {}).get("nodes") or [])
    if not isinstance(nodes, list):
        raise GateError("Nodes da Shopee ausentes")'''
DISCOVERY_AFTER = '''    payload = data.get("data")
    offers = payload.get("productOfferV2") if isinstance(payload, dict) else None
    nodes = offers.get("nodes") if isinstance(offers, dict) else None
    if not isinstance(nodes, list):
        raise GateError("Nodes da Shopee ausentes")'''
DISCOVERY_REGRESSION = '''import json
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
                with self.assertRaisesRegex(GateError, 'Nodes da Shopee ausentes'):
                    self.query(payload)

    def test_explicit_list_remains_valid(self):
        for nodes in ([], [{'itemId': '123'}]):
            with self.subTest(nodes=nodes):
                self.assertEqual(self.query({'data': {'productOfferV2': {'nodes': nodes}}}), nodes)
'''

RECIPES = (
    (RECIPE, SOURCE, BEFORE, AFTER, REGRESSION,
     'Truthy non-boolean values currently bypass the affiliate-origin boolean guard.',
     'Require exactly True for verified origin, retaining all positive commissions.'),
    (DISCOVERY_RECIPE, DISCOVERY_SOURCE, DISCOVERY_BEFORE, DISCOVERY_AFTER,
     DISCOVERY_REGRESSION,
     'Missing or malformed Shopee offer nodes can look like an empty result or raise an unexpected exception.',
     'Require an explicit list of offers and preserve successful empty results.'),
)


def build_candidate(root: Path, sha: str, recipe=RECIPES[0]):
    name, path, before, after, regression, hypothesis, improvement = recipe
    source = git_blob(root, sha, path)
    text = source.decode('utf-8')
    if before not in text:
        return None
    if text.count(before) != 1:
        raise SafetyStop('AMBIGUOUS_RECIPE_TARGET')
    candidate = {
        'schema': 'v31-candidate/v1', 'base_sha': sha,
        'generator': 'DETERMINISTIC_REVIEWED_RECIPE', 'recipe': name,
        'hypothesis': hypothesis, 'expected_improvement': improvement,
        'files': [
            {'path': path, 'before_sha256': digest(source),
             'content': text.replace(before, after, 1)},
            {'path': regression_path(sha), 'before_sha256': None, 'content': regression},
        ],
    }
    validate(candidate, root, sha)
    return candidate


def main():
    if (os.environ.get('GITHUB_REPOSITORY', ALLOWED_REPO) != ALLOWED_REPO or
        os.environ.get('GITHUB_REF_NAME', ALLOWED_BRANCH) != ALLOWED_BRANCH):
        raise SafetyStop('OFFLINE_TARGET_DENIED')
    root = Path.cwd()
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    fingerprint = ''
    status = 'OFFLINE_NO_APPLICABLE_RECIPE'
    out = Path('autoevolution-output')
    out.mkdir(exist_ok=True)
    candidate_path = out / 'candidate.json'
    candidate_path.unlink(missing_ok=True)
    published_contexts = set()
    for path in (root / 'v31_master/autoevolution/experiments').glob('*.json'):
        item = json.loads(path.read_text())
        if item.get('publish') == 'success':
            published_contexts.add(item.get('context_key'))
    for recipe in RECIPES:
        name, path, *_ = recipe
        candidate = build_candidate(root, sha, recipe)
        if candidate is None:
            continue
        fingerprint = digest(name.encode() + git_blob(root, sha, path))
        if fingerprint in published_contexts:
            status = 'OFFLINE_ALREADY_PROPOSED'
            continue
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False))
        status = 'OFFLINE_CANDIDATE_READY'
        break
    result = {'status': status, 'mode': 'OFFLINE_RULES', 'context_key': fingerprint,
              'paid_api_calls': 0, 'production_writes': False}
    (out / 'status.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
            stream.write('ready=' + str(status == 'OFFLINE_CANDIDATE_READY').lower() + '\n')
            stream.write('status=' + status + '\ncontext_key=' + fingerprint + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
