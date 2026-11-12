#!/usr/bin/env python3
"""Synthetic sandbox healthcheck. Never published as a real improvement."""
import json
import subprocess
from pathlib import Path
from candidate import digest, git_blob, regression_path
from verify_candidate import verify


def main():
    root = Path.cwd()
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    path = 'v31_master/store_stock_commission_safe.py'
    source = git_blob(root, sha, path)
    candidate = {'schema': 'v31-candidate/v1', 'base_sha': sha,
        'hypothesis': 'SYNTHETIC_SMOKE_ONLY: test the isolated red/green pipeline.',
        'expected_improvement': 'Infrastructure verification only; never publish this candidate.',
        'files': [
            {'path': path, 'before_sha256': digest(source),
             'content': source.decode() + '\nJARVIS_SANDBOX_SMOKE_ONLY = True\n'},
            {'path': regression_path(sha), 'before_sha256': None, 'content': '''import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import store_stock_commission_safe as target
class TestSandboxSmoke(unittest.TestCase):
    def test_synthetic_marker(self):
        self.assertTrue(getattr(target, 'JARVIS_SANDBOX_SMOKE_ONLY', False))
'''}]}
    out = Path('sandbox-smoke-output')
    out.mkdir(exist_ok=True)
    (out / 'candidate.json').write_text(json.dumps(candidate))
    verify(root, out / 'candidate.json', out / 'verification.json')
    print('SYNTHETIC_SANDBOX_SMOKE_PASS_NO_PUBLICATION')


if __name__ == '__main__':
    main()
