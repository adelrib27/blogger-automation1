"""V31 LAB: atomic pre-PUT attempt claim + durable backup, Git SANDBOX ONLY.

No Blogger imports, HTTP clients, GitHub remote, deploy flags or cron.
A real GitHub integration needs a separately authorized implementation and a
verified server-side If-Match rejection test before ANY Blogger PUT.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import re
import secrets
import subprocess

BLOG = '4739187376492839837'
PAGE = '2446067640331732447'
OP = '2ab915f6079855824374fd9577411783bf6d8e5c2bca7eb36a4aa8e1d08d5a93'
SELECTION = 'aea7191e1e4ea77581b33591e0e940f6bd582114c90ea2e457a7173faf3664b7'
ORIGINAL = '6f3810a364fe2114865b96fa5f118c10495bfe39943406624710ac9aaf25f450'
CANDIDATE = 'd33070c001281ed795489a032a504accfcab2b593010c1a9e8cf5bb86b8109b8'
LEDGER = 'blogger_stores/v31_lab/state/v31_rotation_ledger.json'
HISTORY = 'blogger_stores/v31_lab/state/v31_rotation_history.json'
BACKUP = f'blogger_stores/v31_lab/prewrite_backup/{OP}/LOJA_ANTES_SEGUNDA_ROTACAO.html'
BRANCH_SANDBOX = 'sandbox-v31-prewrite-claim'

class ClaimBlocked(ValueError): pass

def require(ok: bool, reason: str):
    if not ok: raise ClaimBlocked(reason)

def canonical_json(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')

def strong_etag(etag: str) -> bool:
    return isinstance(etag, str) and re.fullmatch(r'"[\x21\x23-\x7e]+"', etag) is not None

def plan_claim(*, ledger: dict, history: dict, html: bytes, etag: str,
               updated_at: str, expected_head: str, attempt_nonce: str) -> tuple[bytes, str]:
    """Pure PLAN claim; NEVER means that Blogger PUT is authorized."""
    require(type(html) is bytes and sha256(html).hexdigest() == ORIGINAL, 'HTML backup divergiu')
    require(strong_etag(etag), 'ETag must be strong, quoted, never wildcard')
    require(type(updated_at) is str and len(updated_at) > 18, 'Blogger updated missing')
    require(type(attempt_nonce) is str and re.fullmatch('[0-9a-f]{32}', attempt_nonce) is not None, 'Unique 128-bit attempt nonce required')
    require(type(expected_head) is str and re.fullmatch('[0-9a-f]{40}', expected_head) is not None, 'HEAD invalid')
    require(type(ledger) is dict and ledger.get('schema') == 1
            and ledger.get('blogId') == BLOG and ledger.get('pageId') == PAGE, 'Ledger identity')
    ops = ledger.get('operations')
    require(type(ops) is list and len(ops) == 2, 'Exactly first PERSISTED and second PLAN required')
    first, second = ops
    require(first.get('status') == 'PERSISTED' and second.get('status') == 'PLAN', 'PLAN not active')
    require(second.get('operationId') == OP and second.get('selectionSha') == SELECTION
            and second.get('originalSha') == ORIGINAL and second.get('candidateSha') == CANDIDATE,
            'PLAN contents differ from approved selection')
    require('prewriteClaim' not in second, 'A PUT attempt is already claimed; never retry')
    require(type(history) is dict and history.get('version') == 1
            and history.get('blogId') == BLOG and type(history.get('runs')) is list
            and len(history['runs']) == 2, 'History mismatch')
    require(history['runs'][0].get('source') == 'seed_from_current_blogger_store'
            and history['runs'][1].get('operationId') == first.get('operationId')
            and history['runs'][1].get('selectionSha') == first.get('selectionSha')
            and history['runs'][1].get('source') == 'blogger_published', 'History lineage mismatch')
    require(not any(x.get('operationId') == OP for x in history['runs']), 'History prematurely contains PLAN')
    claim_id = sha256('|'.join((BLOG, PAGE, OP, expected_head, ORIGINAL, CANDIDATE,
                                 etag, updated_at, attempt_nonce)).encode('utf-8')).hexdigest()
    out = deepcopy(ledger)
    out['operations'][1]['prewriteClaim'] = {
        'state': 'ATTEMPT_CLAIMED_BEFORE_PUT', 'claimId': claim_id, 'nonce': attempt_nonce,
        'expectedHead': expected_head, 'etagSha256': sha256(etag.encode()).hexdigest(),
        'updatedAt': updated_at, 'backupSha256': ORIGINAL, 'backupPath': BACKUP,
        'note': 'Claim does not certify Blogger PUT, If-Match support, or public proof.'}
    return canonical_json(out), claim_id

def git(cwd: Path, *args: str, check=True):
    p = subprocess.run(['git', *args], cwd=cwd, text=True, capture_output=True,
                       timeout=25, check=False, env=None)
    if check and p.returncode != 0: raise ClaimBlocked('git failure: '+p.stderr[-160:])
    return p

@dataclass(frozen=True)
class SandboxReceipt:
    claim_id: str
    parent: str
    remote_commit: str
    ledger_sha256: str
    backup_sha256: str
    unique: bool
    blogger_put_allowed: bool = False


def commit_sandbox_claim(*, checkout: Path, sandbox_remote: Path,
                         original_html: bytes, etag: str, updated_at: str,
                         before_push=None) -> SandboxReceipt:
    """Non-force one-shot Git race in an explicitly marked LOCAL sandbox.

    All Git pushes go to a local bare repository with a specific marker.
    Not usable with real GitHub remote or any production repo.
    """
    checkout = checkout.resolve(strict=True)
    sandbox_remote = sandbox_remote.resolve(strict=True)
    require(sandbox_remote.is_dir() and (sandbox_remote/'V31_SANDBOX_ONLY').is_file()
            and (sandbox_remote/'V31_SANDBOX_ONLY').read_text().strip() == 'NO_GITHUB_REMOTE',
            'Sandbox marker required')
    require((sandbox_remote/'HEAD').is_file() and (sandbox_remote/'objects').is_dir(),
            'Remote must be local bare Git repo')
    remote_url = git(checkout, 'remote', 'get-url', 'origin').stdout.strip()
    require(remote_url == str(sandbox_remote), 'Remote MUST be pinned local bare sandbox')
    require(git(checkout, 'branch', '--show-current').stdout.strip() == BRANCH_SANDBOX,
            'Wrong sandbox branch')
    require(not git(checkout, 'status', '--porcelain').stdout.strip(), 'Sandbox checkout dirty')
    head = git(checkout, 'rev-parse', 'HEAD').stdout.strip()
    remote_head = git(checkout, 'ls-remote', 'origin', f'refs/heads/{BRANCH_SANDBOX}').stdout.strip()
    require(remote_head == f'{head}\trefs/heads/{BRANCH_SANDBOX}', 'Stale remote HEAD')
    led_path, hist_path = checkout/LEDGER, checkout/HISTORY
    current_led = led_path.read_bytes()
    current_hist = hist_path.read_bytes()
    led = json.loads(current_led)
    hist = json.loads(current_hist)
    new_led, claim_id = plan_claim(ledger=led, history=hist, html=original_html,
                                   etag=etag, updated_at=updated_at, expected_head=head,
                                   attempt_nonce=secrets.token_hex(16))
    require(not (checkout/BACKUP).exists(), 'Backup path already exists')
    (checkout/BACKUP).parent.mkdir(parents=True, exist_ok=False)
    (checkout/BACKUP).write_bytes(original_html)
    led_path.write_bytes(new_led)
    git(checkout, 'add', '--', LEDGER, BACKUP)
    names=git(checkout,'diff','--cached','--name-only').stdout.splitlines()
    require(sorted(names)==sorted([LEDGER,BACKUP]),'Changes outside pinned ledger+backup')
    git(checkout,'-c','user.name=V31 SAFE Sandbox','-c','user.email=v31-sandbox@example.invalid',
        'commit','-m','SANDBOX ONLY: V31 prewrite claim + original HTML backup')
    commit=git(checkout,'rev-parse','HEAD').stdout.strip()
    parent=git(checkout,'rev-parse','HEAD^').stdout.strip()
    require(parent==head, 'Unexpected commit ancestry')
    # Test-only barrier demonstrates a real concurrent non-forced push race.
    if before_push is not None:
        require(callable(before_push), 'Test barrier invalid')
        before_push()
    # The two clones race for the same remote ref. No force or retries.
    push=git(checkout,'push','origin',f'{BRANCH_SANDBOX}:{BRANCH_SANDBOX}',check=False)
    require(push.returncode==0, 'Claim lost Git CAS race; refuse retry')
    after=git(checkout,'ls-remote','origin',f'refs/heads/{BRANCH_SANDBOX}').stdout.strip()
    require(after==f'{commit}\trefs/heads/{BRANCH_SANDBOX}', 'Remote claim not confirmed')
    # Durable backup and ledger are now reachable at a non-forced remote commit.
    def remote_blob(path):
        result = subprocess.run(['git', '--git-dir', str(sandbox_remote), 'show',
                                 f'{commit}:{path}'], capture_output=True, timeout=25)
        require(result.returncode == 0, 'Remote blob unavailable')
        return result.stdout
    remote_backup = remote_blob(BACKUP)
    remote_ledger = remote_blob(LEDGER)
    remote_history = remote_blob(HISTORY)
    require(remote_backup == original_html and remote_ledger == new_led and
            remote_history == current_hist, 'Remote backup/history/ledger diverged')
    return SandboxReceipt(claim_id,head,commit,sha256(new_led).hexdigest(),ORIGINAL,True)
