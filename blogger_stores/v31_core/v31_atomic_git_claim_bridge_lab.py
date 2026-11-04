"""V31 R1 LAB: atomic backup + one-attempt Git claim adapter (NOT a publisher).

No network library, Git credential handling, CLI, scheduled job or Blogger PUT.
The caller must supply a trusted authenticated Git gateway, an independently
verified durable backup reader and a separate explicit publication approval.
This module is unarmed by default. It must never be invoked by a push workflow.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1, sha256
import re
import secrets
from typing import Callable, Protocol

from v31_prewrite_claim_sandbox_safe import (
    BLOG, PAGE, OP, SELECTION, ORIGINAL, CANDIDATE,
    LEDGER, HISTORY, BACKUP, plan_claim,
)

REPO = 'adelrib27/blogger-automation1'
BRANCH = 'lab/v31r1-shopee-safe-20261103'
BASE_LEDGER_BLOB = '8331d025d77fc752230eec71f6c7d8ba86ece5a5'
BASE_HISTORY_BLOB = 'de0f022994ca47f0b8316169815afe25722fdfff'
RESERVATION = '801381b4e0d2d23fa60f478da67b6dca6ec3df32'


class BridgeBlocked(RuntimeError):
    """No trust or consistency: fail closed, never retry a PUT."""


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise BridgeBlocked(reason)


def git_blob(raw: bytes) -> str:
    need(type(raw) is bytes, 'Invalid Git blob bytes')
    return sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


class AuthenticatedGitGateway(Protocol):
    """Must be implemented separately with authenticated, non-force CAS writes.

    commit_nonforce must reject a stale ref. Never use force, retry or reset.
    read_blob reads bytes from an exact immutable commit, not a moving branch.
    """
    repository: str
    branch: str

    def head(self) -> str: ...
    def read_blob(self, commit: str, path: str) -> bytes: ...
    def commit_nonforce(self, expected_head: str, changes: dict[str, bytes]) -> str: ...
    def parent(self, commit: str) -> str: ...
    def changed_paths(self, commit: str) -> frozenset[str]: ...


@dataclass(frozen=True)
class ClaimAudit:
    previous_head: str
    claim_commit: str
    claim_id: str
    ledger_blob: str
    history_blob: str
    backup_blob: str
    exact_remote_readback: bool
    blogger_put_performed: bool = False


class LabAtomicClaimBridge:
    """Two callbacks for the *unchanged* one-shot publisher.

    verify_durable_backup verifies a separately retained immutable copy of
    the approved original HTML, without touching Git. claim_attempt then
    atomically writes the current HTML and unique attempt claim in ONE commit.

    The caller must explicitly arm this bridge in a *future approved* manual
    publication workflow. No current SAFE workflow arms it or supplies a
    remote writer. A receipt is not, by itself, permission to Blogger PUT.
    """

    def __init__(self, *, gateway: AuthenticatedGitGateway,
                 archived_backup_reader: Callable[[], bytes],
                 original_html: bytes, armed: bool = False,
                 pins: dict[str, str] | None = None) -> None:
        self.git = gateway
        self.reader = archived_backup_reader
        self.original = original_html
        self.armed = armed
        self.backup_verified = False
        self.last_audit: ClaimAudit | None = None
        self._archived_etag: str | None = None
        self._archived_updated: str | None = None
        self._archived_head: str | None = None
        # Test fixture pins are permissible ONLY for an explicitly marked
        # in-memory sandbox. Production always uses the actual canonical blobs.
        self.pins = {'ledger': BASE_LEDGER_BLOB, 'history': BASE_HISTORY_BLOB}
        if pins is not None:
            need(getattr(gateway, 'sandbox_only', False) is True,
                 'Custom blob pins require sandbox-only gateway')
            self.pins = pins
        need(getattr(gateway, 'repository', None) == REPO
             and getattr(gateway, 'branch', None) == BRANCH,
             'Git gateway identity mismatch')
        need(type(original_html) is bytes and sha256(original_html).hexdigest() == ORIGINAL,
             'Approved original HTML digest mismatch')
        need(callable(archived_backup_reader), 'Independent durable backup reader missing')
        need(type(armed) is bool, 'Invalid write gate')

    def verify_durable_backup(self, manifest: dict) -> bool:
        """Read-only: caller needs an independently authenticated retained archive.

        A fake reader cannot establish production durability. The real runtime
        must validate the archive's repository/storage identity separately.
        """
        need(type(manifest) is dict
             and manifest.get('blog_id') == BLOG
             and manifest.get('page_id') == PAGE
             and manifest.get('operation_id') == OP
             and manifest.get('reservation_commit') == RESERVATION
             and manifest.get('original_sha256') == ORIGINAL
             and manifest.get('candidate_sha256') == CANDIDATE
             and manifest.get('ledger_blob') == self.pins['ledger']
             and manifest.get('history_blob') == self.pins['history']
             and manifest.get('external_backup_uploaded') is False
             and isinstance(manifest.get('etag'), str)
             and isinstance(manifest.get('updated'), str),
             'Prewrite manifest identity/hash mismatch')
        head = manifest.get('git_head')
        need(isinstance(head, str) and re.fullmatch('[0-9a-f]{40}', head) is not None
             and head == self.git.head(), 'Git HEAD changed before archived backup proof')
        retained = self.reader()
        need(type(retained) is bytes and retained == self.original,
             'Retained backup unavailable or differs from live original')
        self._archived_etag = manifest['etag']
        self._archived_updated = manifest['updated']
        self._archived_head = head
        self.backup_verified = True
        return True

    def claim_attempt(self, request: dict):
        """At most one non-force CAS claim; no retries and no Blogger calls.

        Returns the existing publisher FenceReceipt only after remote readback.
        Actual remote writer must be injected by a separately authorized run.
        """
        need(self.armed is True, 'Operational claim is NOT authorized')
        need(self.backup_verified is True, 'Verified durable backup missing')
        self.backup_verified = False  # consume the attestation, even on failure
        need(type(request) is dict, 'Invalid claim request')
        head = request.get('git_head')
        need(isinstance(head, str) and re.fullmatch('[0-9a-f]{40}', head) is not None,
             'Claim Git parent SHA invalid')
        need(request.get('operation_id') == OP
             and request.get('reservation_commit') == RESERVATION
             and request.get('original_sha256') == ORIGINAL
             and request.get('candidate_sha256') == CANDIDATE
             and request.get('backup_sha256') == ORIGINAL
             and request.get('ledger_blob') == self.pins['ledger']
             and request.get('history_blob') == self.pins['history'],
             'Claim request differs from fixed PLAN')
        etag = request.get('etag')
        need(isinstance(etag, str) and re.fullmatch(r'"[\x21\x23-\x7e]+"', etag) is not None,
             'Strong If-Match ETag required')
        need(head == self._archived_head and etag == self._archived_etag,
             'Claim differs from independently backed-up snapshot')
        need(self.git.head() == head, 'Remote Git HEAD diverged before claim')
        ledger = self.git.read_blob(head, LEDGER)
        history = self.git.read_blob(head, HISTORY)
        need(git_blob(ledger) == self.pins['ledger']
             and git_blob(history) == self.pins['history'],
             'Canonical ledger/history Git blobs changed')
        try:
            self.git.read_blob(head, BACKUP)
        except FileNotFoundError:
            pass
        else:
            raise BridgeBlocked('Remote backup already exists; duplicate claim blocked')
        import json
        try:
            ledger_doc, history_doc = json.loads(ledger), json.loads(history)
            new_ledger, claim_id = plan_claim(
                ledger=ledger_doc, history=history_doc, html=self.original,
                etag=etag, updated_at=self._archived_updated,
                expected_head=head, attempt_nonce=secrets.token_hex(16))
        except (TypeError, ValueError) as exc:
            raise BridgeBlocked('Canonical PLAN/claim validation failed') from exc
        need(git_blob(new_ledger) != self.pins['ledger'], 'Claim ledger must change')
        # Gateway's non-force CAS is the only allowed remote write operation.
        commit = self.git.commit_nonforce(head, {LEDGER: new_ledger, BACKUP: self.original})
        need(isinstance(commit, str) and re.fullmatch('[0-9a-f]{40}', commit) is not None
             and commit != head, 'Claim commit not confirmed')
        # Read back immutable commit objects AND the currently selected ref.
        need(self.git.head() == commit, 'Remote ref changed after claim: stop')
        need(self.git.parent(commit) == head, 'Claim parent differs')
        need(self.git.changed_paths(commit) == frozenset({LEDGER, BACKUP}),
             'Unexpected paths in claim commit')
        need(self.git.read_blob(commit, LEDGER) == new_ledger
             and self.git.read_blob(commit, BACKUP) == self.original
             and self.git.read_blob(commit, HISTORY) == history,
             'Atomic ledger/backup/history remote readback mismatch')
        self.last_audit = ClaimAudit(head, commit, claim_id,
                                     git_blob(new_ledger), git_blob(history),
                                     git_blob(self.original), True)
        # Preserve the publisher's exact receipt type; do not change its logic.
        from v31_second_publish_once_lab import FenceReceipt
        return FenceReceipt(OP, ORIGINAL, CANDIDATE, head, etag, True, True)

class PinnedGitRemoteGateway:
    """Git CLI transport for a future manually authorized GitHub LAB workflow.

    Constructor is read-only. The ONLY write is commit_nonforce, which is
    disabled unless explicitly constructed with write_enabled=True. There is
    intentionally no CLI entrypoint, cron, token loading or Blogger operation.
    """

    repository = REPO
    branch = BRANCH
    sandbox_only = False

    def __init__(self, checkout, *, write_enabled: bool = False):
        from pathlib import Path
        self.checkout = Path(checkout).resolve(strict=True)
        self.write_enabled = write_enabled
        need(type(write_enabled) is bool, 'Invalid remote writer gate')
        need(self.checkout.is_dir(), 'Missing checkout')
        need(self._git('rev-parse', '--show-toplevel').decode().strip() == str(self.checkout),
             'Must be repository root')
        need(self._git('branch', '--show-current').decode().strip() == BRANCH,
             'Not on exact V31 LAB branch')
        url = self._git('remote', 'get-url', 'origin').decode().strip()
        need(url in ('https://github.com/' + REPO, 'https://github.com/' + REPO + '.git'),
             'Remote repository identity mismatch or embedded credentials')
        need(self._git('status', '--porcelain').strip() == b'', 'Checkout is dirty')

    def _git(self, *args, check=True) -> bytes:
        import subprocess
        proc = subprocess.run(['git', *args], cwd=self.checkout,
                              capture_output=True, timeout=45, check=False)
        if check:
            # Never leak stderr from git because remote/credential helpers may
            # include URL credentials in diagnostic output.
            need(proc.returncode == 0, 'Git subprocess did not succeed')
        return proc.stdout if check else bytes([proc.returncode]) + proc.stdout

    def head(self) -> str:
        raw = self._git('ls-remote', '--heads', 'origin',
                        'refs/heads/' + BRANCH).decode().strip()
        match = re.fullmatch(r'([0-9a-f]{40})\trefs/heads/' + re.escape(BRANCH), raw)
        need(match is not None, 'Remote Git ref unavailable')
        return match.group(1)

    def read_blob(self, commit: str, path: str) -> bytes:
        need(re.fullmatch(r'[0-9a-f]{40}', commit) is not None,
             'Invalid immutable revision')
        need(path in {LEDGER, HISTORY, BACKUP}, 'Unexpected Git file read')
        import subprocess
        p = subprocess.run(['git', 'show', commit + ':' + path], cwd=self.checkout,
                           capture_output=True, timeout=45, check=False)
        if p.returncode != 0 and path == BACKUP:
            raise FileNotFoundError(path)
        need(p.returncode == 0, 'Immutable Git file read failed')
        return p.stdout

    def parent(self, commit: str) -> str:
        need(re.fullmatch(r'[0-9a-f]{40}', commit) is not None, 'Invalid commit SHA')
        raw = self._git('rev-list', '--parents', '-n', '1', commit).decode().strip().split()
        need(len(raw) == 2 and raw[0] == commit, 'Claim must have one parent')
        return raw[1]

    def changed_paths(self, commit: str) -> frozenset[str]:
        need(re.fullmatch(r'[0-9a-f]{40}', commit) is not None, 'Invalid commit SHA')
        return frozenset(self._git('diff-tree', '--no-commit-id', '--name-only',
                                   '-r', commit).decode().splitlines())

    def commit_nonforce(self, expected_head: str, changes: dict[str, bytes]) -> str:
        """Explicitly armed non-force push; on uncertainty: no retries."""
        need(self.write_enabled is True, 'Remote Git writing not enabled')
        need(type(changes) is dict and set(changes) == {LEDGER, BACKUP}
             and all(type(x) is bytes for x in changes.values()),
             'Only atomic ledger+backup changes permitted')
        need(re.fullmatch(r'[0-9a-f]{40}', expected_head) is not None,
             'Expected ref SHA invalid')
        need(self._git('rev-parse', 'HEAD').decode().strip() == expected_head
             and self.head() == expected_head, 'Stale checkout or remote ref')
        need(self._git('status', '--porcelain').strip() == b'', 'Checkout dirty before claim')
        target = self.checkout / BACKUP
        need(not target.exists() and not target.is_symlink(),
             'Backup target exists or is a symlink')
        # Disallow path substitutions via symlinks in the checkout.
        for path in (LEDGER, BACKUP):
            target_path = self.checkout / path
            for part in [target_path, *target_path.parents]:
                if part == self.checkout.parent:
                    break
                need(not part.is_symlink(), 'Symlink ancestor blocked')
        target.parent.mkdir(parents=True, exist_ok=True)
        (self.checkout / LEDGER).write_bytes(changes[LEDGER])
        target.write_bytes(changes[BACKUP])
        self._git('add', '--', LEDGER, BACKUP)
        names = self._git('diff', '--cached', '--name-only').decode().splitlines()
        need(set(names) == {LEDGER, BACKUP}, 'Unexpected staged files')
        self._git('-c', 'user.name=V31 LAB Claim',
                  '-c', 'user.email=v31-lab-claim@users.noreply.github.com',
                  'commit', '-m', 'LAB V31: one-time prewrite claim + HTML backup')
        result = self._git('rev-parse', 'HEAD').decode().strip()
        need(self.parent(result) == expected_head
             and self.changed_paths(result) == frozenset({LEDGER, BACKUP}),
             'Unexpected Git commit tree or parent')
        # Non-forced push only; never use --force, --mirror, --atomic fallback
        # or retry. A changed remote ref rejects a non-fast-forward update.
        import subprocess
        pushed = subprocess.run(['git', 'push', 'origin',
                                 'HEAD:refs/heads/' + BRANCH],
                                cwd=self.checkout, capture_output=True,
                                timeout=50, check=False)
        need(pushed.returncode == 0,
             'Remote claim push rejected or uncertain: NEVER RETRY')
        need(self.head() == result, 'Remote head readback uncertain: NEVER RETRY')
        return result
