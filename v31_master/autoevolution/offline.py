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


def build_candidate(root: Path, sha: str):
    source = git_blob(root, sha, SOURCE)
    text = source.decode('utf-8')
    if BEFORE not in text:
        return None  # Fixed or unknown source: never guess a replacement.
    if text.count(BEFORE) != 1:
        raise SafetyStop('AMBIGUOUS_RECIPE_TARGET')
    candidate = {
        'schema': 'v31-candidate/v1', 'base_sha': sha,
        'generator': 'DETERMINISTIC_REVIEWED_RECIPE', 'recipe': RECIPE,
        'hypothesis': 'Truthy non-boolean values currently bypass the affiliate-origin boolean guard.',
        'expected_improvement': 'Require exactly True for verified origin, retaining all positive commissions.',
        'files': [
            {'path': SOURCE, 'before_sha256': digest(source),
             'content': text.replace(BEFORE, AFTER, 1)},
            {'path': regression_path(sha), 'before_sha256': None, 'content': REGRESSION},
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
    fingerprint = digest(RECIPE.encode() + git_blob(root, sha, SOURCE))
    status = 'OFFLINE_NO_APPLICABLE_RECIPE'
    out = Path('autoevolution-output')
    out.mkdir(exist_ok=True)
    candidate_path = out / 'candidate.json'
    candidate_path.unlink(missing_ok=True)
    past = []
    for path in (root / 'v31_master/autoevolution/experiments').glob('*.json'):
        item = json.loads(path.read_text())
        if item.get('context_key') == fingerprint and item.get('publish') == 'success':
            past.append(item)
    if past:
        status = 'OFFLINE_ALREADY_PROPOSED'
    else:
        candidate = build_candidate(root, sha)
        if candidate is not None:
            candidate_path.write_text(json.dumps(candidate, ensure_ascii=False))
            status = 'OFFLINE_CANDIDATE_READY'
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
