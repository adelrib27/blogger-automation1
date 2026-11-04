#!/usr/bin/env python3
"""LAB V31: independently authenticate Blogger LIVE GET and immutable Git PLAN.

READ-ONLY PREFLIGHT ONLY: no Git commits, Blogger PUT, claims, publication or cron.
The prewrite backup/claim MUST later be written atomically by the R12 bridge
immediately before a separately approved one-shot publication.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v31_core"))

from v31_prewrite_claim_sandbox_safe import (
    BLOG, PAGE, OP, SELECTION, ORIGINAL, CANDIDATE, LEDGER, HISTORY,
    BACKUP, strong_etag,
)
from v31_atomic_git_claim_bridge_lab import (
    REPO, BRANCH, BASE_LEDGER_BLOB, BASE_HISTORY_BLOB,
    RESERVATION, PinnedGitRemoteGateway, git_blob,
)

URL = 'https://blog-teste-tema-worpress.blogspot.com/p/loja.html'
UPDATED = '2026-11-03T22:19:09-03:00'

class PreflightBlocked(RuntimeError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise PreflightBlocked(reason)


def attest(*, page: dict, archived_original: bytes, archived_candidate: bytes,
           gateway, expected_head: str, reservation_is_ancestor: bool) -> dict:
    """Verify external authenticated page representation and remote immutable Git.

    gateway must represent a separately authenticated source. Fake gateways are
    legitimate for unit tests ONLY. Return is not a publication authorization.
    """
    require(getattr(gateway, 'repository', None) == REPO
            and getattr(gateway, 'branch', None) == BRANCH, 'Git repository/branch mismatch')
    require(type(expected_head) is str
            and re.fullmatch('[0-9a-f]{40}', expected_head) is not None,
            'Invalid expected HEAD')
    require(gateway.head() == expected_head, 'Remote Git HEAD differs')
    require(reservation_is_ancestor is True, 'PLAN reservation missing from branch history')
    require(isinstance(page, dict) and str(page.get('id')) == PAGE
            and str(page.get('blog', {}).get('id')) == BLOG
            and page.get('title', '').strip().casefold() == 'loja'
            and page.get('url') == URL and page.get('status') == 'LIVE',
            'Authenticated Blogger LOJA identity/status mismatch')
    content = page.get('content')
    require(type(content) is str, 'Blogger HTML missing')
    actual = content.encode('utf-8')
    require(sha256(actual).hexdigest() == ORIGINAL, 'Blogger HTML not approved original')
    require(type(archived_original) is bytes and archived_original == actual
            and sha256(archived_original).hexdigest() == ORIGINAL,
            'Independent original backup differs from authenticated GET')
    require(type(archived_candidate) is bytes
            and sha256(archived_candidate).hexdigest() == CANDIDATE,
            'Approved candidate HTML archive mismatch')
    etag = page.get('etag')
    require(strong_etag(etag), 'Blogger ETag must be strong')
    require(page.get('updated') == UPDATED, 'Blogger updated timestamp diverged')
    led = gateway.read_blob(expected_head, LEDGER)
    his = gateway.read_blob(expected_head, HISTORY)
    require(git_blob(led) == BASE_LEDGER_BLOB
            and git_blob(his) == BASE_HISTORY_BLOB,
            'Canonical Git blob differs from reserved state')
    try:
        ledger, history = json.loads(led), json.loads(his)
    except (TypeError, ValueError) as exc:
        raise PreflightBlocked('Canonical Git JSON malformed') from exc
    require(ledger.get('schema') == 1 and ledger.get('blogId') == BLOG
            and ledger.get('pageId') == PAGE, 'Ledger identity mismatch')
    ops = ledger.get('operations')
    require(type(ops) is list and len(ops) == 2
            and [x.get('status') for x in ops] == ['PERSISTED', 'PLAN'],
            'Missing expected PERSISTED + PLAN sequence')
    reserved = ops[1]
    require(reserved.get('operationId') == OP
            and reserved.get('selectionSha') == SELECTION
            and reserved.get('originalSha') == ORIGINAL
            and reserved.get('candidateSha') == CANDIDATE
            and 'prewriteClaim' not in reserved,
            'PLAN changed or a claim was already consumed')
    require(history.get('version') == 1 and history.get('blogId') == BLOG
            and type(history.get('runs')) is list and len(history['runs']) == 2
            and history['runs'][1].get('operationId') == ops[0].get('operationId')
            and not any(run.get('operationId') == OP for run in history['runs']),
            'History diverged from first persisted cycle')
    try:
        gateway.read_blob(expected_head, BACKUP)
    except FileNotFoundError:
        pass
    else:
        raise PreflightBlocked('Remote claim backup already exists: do not retry')
    require(gateway.head() == expected_head, 'Remote HEAD moved during read-only check')
    return {
        'status': 'V31_SECOND_AUTHENTICATED_BACKUP_AND_GIT_READ_ONLY_PASS',
        'repository': REPO, 'branch': BRANCH, 'head': expected_head,
        'operation_id': OP, 'blog_id': BLOG, 'page_id': PAGE,
        'original_sha256': ORIGINAL, 'candidate_sha256': CANDIDATE,
        'etag_sha256': sha256(etag.encode()).hexdigest(),
        'ledger_git_blob': BASE_LEDGER_BLOB,
        'history_git_blob': BASE_HISTORY_BLOB,
        'page_updated': UPDATED,
        'archived_original_verified': True,
        'live_get_authenticated': True,
        'remote_git_head_read_back': True,
        'durable_remote_claim_committed': False,
        'blogger_put_performed': False,
        'publication_authorized': False,
        'daily_cron_enabled': False,
    }


def run_live_read_only() -> dict:
    """Only approved LAB push with existing GitHub OAuth secrets, GET requests only."""
    require(os.getenv('GITHUB_REPOSITORY') == REPO
            and os.getenv('GITHUB_REF') == 'refs/heads/' + BRANCH
            and os.getenv('GITHUB_EVENT_NAME') == 'push'
            and os.getenv('GITHUB_RUN_ATTEMPT') == '1', 'Not approved LAB CI invocation')
    expected_head = os.getenv('GITHUB_SHA', '')
    require(re.fullmatch('[0-9a-f]{40}', expected_head) is not None,
            'GitHub commit SHA absent')
    checkout = Path(os.getenv('GITHUB_WORKSPACE', '')).resolve(strict=True)
    original_path = Path(os.environ['V31_ARCHIVED_ORIGINAL']).resolve(strict=True)
    candidate_path = Path(os.environ['V31_ARCHIVED_CANDIDATE']).resolve(strict=True)
    require(original_path.parent == candidate_path.parent
            and not str(original_path).startswith(str(checkout) + '/')
            and not str(candidate_path).startswith(str(checkout) + '/'),
            'Archived files must be outside checkout')
    git = PinnedGitRemoteGateway(checkout, write_enabled=False)
    require(subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=checkout,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           timeout=15, check=True).stdout.decode().strip() == expected_head,
            'Checkout SHA differs from event')
    ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', RESERVATION, expected_head],
                             cwd=checkout, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, timeout=15, check=False)
    require(ancestor.returncode == 0, 'Reservation commit not ancestor')
    # Reuse previously audited OAuth code; call transport ONLY with method GET.
    from v31_etag_sacrificial_live_once import oauth_access_token, transport
    token = oauth_access_token()
    endpoint = 'https://www.googleapis.com/blogger/v3/blogs/' + BLOG + '/pages/' + PAGE
    code, page = transport(endpoint, 'GET', token=token)
    require(code == 200, 'Authenticated Blogger GET failed')
    report = attest(page=page,
                    archived_original=original_path.read_bytes(),
                    archived_candidate=candidate_path.read_bytes(),
                    gateway=git, expected_head=expected_head,
                    reservation_is_ancestor=True)
    print('V31_SECOND_AUTHENTICATED_BACKUP_GIT_READONLY_PASS=' + json.dumps(report, sort_keys=True), flush=True)
    return report


if __name__ == '__main__':
    try:
        run_live_read_only()
    except (PreflightBlocked, ValueError, KeyError, FileNotFoundError) as exc:
        print('V31_SECOND_READ_ONLY_PREFLIGHT_BLOCKED=' + type(exc).__name__, flush=True)
        raise SystemExit(2)
