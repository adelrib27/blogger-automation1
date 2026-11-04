#!/usr/bin/env python3
"""V31 LAB: single-attempt Blogger second rotation, guarded against re-PUT.

This is *code under test*, NOT permission to publish. There is deliberately no
CLI --apply, scheduling, or GitHub Actions writer. The external integration must
separately obtain user approval, authenticate/verify the current Git state,
upload/verify a durable prewrite backup, and atomically claim an attempt via a
remote compare-and-swap fence *before* any Blogger PUT. In the absence of all
of those independent authorities, this module cannot send a PUT.

The pure prewrite contract pins all bytes to the already reserved PLAN. Any
uncertain response from Blogger is terminal until a new authenticated readback
and manual recovery decision; this function never retries a PUT or rolls back.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Callable, Any
import json
import re
import sys

CORE = Path(__file__).resolve().parents[1] / 'v31_core'
sys.path.insert(0, str(CORE))
from v31_second_publish_gate_safe import (
    BLOG_ID, PAGE_ID, PAGE_URL, REPOSITORY, BRANCH, RESERVATION_COMMIT,
    CANDIDATE_SHA, ORIGINAL_SHA, OPERATION_ID, LEDGER_BLOB, HISTORY_BLOB,
    gate_second_publish_safe, GateBlocked,
)

class PublicationBlocked(RuntimeError):
    """Fail closed; may also represent an uncertain attempted PUT."""


@dataclass(frozen=True)
class ImmutableInputs:
    profile: bytes
    ledger: bytes
    history: bytes
    selection: bytes
    original: bytes
    candidate: bytes


@dataclass(frozen=True)
class GitWitness:
    """Authenticated remotely by a separate read-only component at call time."""
    repository: str
    branch: str
    head: str
    reservation_ancestor: bool
    ledger_blob: str
    history_blob: str


@dataclass(frozen=True)
class WriteApproval:
    """Must be supplied only by an external workflow after explicit user approval."""
    operation_id: str
    reservation_commit: str
    explicit_lab_put_authorized: bool


@dataclass(frozen=True)
class FenceReceipt:
    """Proof from external durable CAS fence, one claim per operation."""
    operation_id: str
    original_sha256: str
    candidate_sha256: str
    git_head: str
    etag: str
    unique_claim: bool
    durable: bool


def _need(ok: bool, reason: str) -> None:
    if not ok:
        raise PublicationBlocked(reason)


def _sha(content: bytes) -> str:
    _need(type(content) is bytes, 'Invalid HTML byte encoding')
    return sha256(content).hexdigest()


def _page_snapshot(page: dict) -> tuple[bytes, str, str, str]:
    _need(isinstance(page, dict), 'Blogger GET must return a page object')
    _need(str(page.get('id', '')) == PAGE_ID, 'Wrong Blogger page ID')
    blog = page.get('blog')
    _need(type(blog) is dict and str(blog.get('id')) == BLOG_ID,
          'Blogger blog identity not independently confirmed')
    _need(str(page.get('title', '')).strip().casefold() == 'loja',
          'Blogger page title unexpectedly changed')
    _need(page.get('url') == PAGE_URL, 'Blogger page URL mismatch')
    raw = page.get('content')
    _need(type(raw) is str and 5000 < len(raw) < 180000,
          'Blogger page content absent or size invalid')
    etag = page.get('etag')
    _need(type(etag) is str and bool(etag.strip()) and len(etag) < 512,
          'Blogger ETag required; refuse write without concurrency precondition')
    updated = page.get('updated')
    _need(type(updated) is str and bool(updated.strip()), 'Blogger updated field absent')
    return raw.encode('utf-8'), etag, updated, str(page['title'])


def _get(service) -> dict:
    return service.pages().get(blogId=BLOG_ID, pageId=PAGE_ID).execute()


def classify_read_only(*, service, inputs: ImmutableInputs,
                       witness: GitWitness) -> dict:
    """Authenticated GET + pure gate; NEVER publishes or modifies Git."""
    _need(witness.repository == REPOSITORY and witness.branch == BRANCH,
          'Git remote repository/branch mismatch')
    _need(re.fullmatch('[0-9a-f]{40}', witness.head or '') is not None,
          'Git head not pinned')
    _need(witness.reservation_ancestor is True, 'Reserved PLAN commit not ancestor')
    _need(witness.ledger_blob == LEDGER_BLOB and witness.history_blob == HISTORY_BLOB,
          'Git canonical blob witness diverged')
    page = _get(service)
    current, _, updated, _ = _page_snapshot(page)
    try:
        gate = gate_second_publish_safe(
            repository=witness.repository, branch=witness.branch,
            branch_head=witness.head,
            reservation_is_ancestor=witness.reservation_ancestor,
            profile_bytes=inputs.profile, ledger_bytes=inputs.ledger,
            history_bytes=inputs.history, selection_bytes=inputs.selection,
            original_html_bytes=inputs.original,
            candidate_html_bytes=inputs.candidate,
            observed_blogger_html_bytes=current,
            observed_blogger_is_authenticated_live=True,
        )
    except GateBlocked as exc:
        raise PublicationBlocked('PREWRITE_GATE_BLOCKED: '+str(exc)) from exc
    _need(gate['observed_blogger_live_authenticated'] is True,
          'Not an authenticated LIVE Blogger readback')
    return {'status': 'V31_SECOND_ONCE_READONLY_VALIDATED',
            'decision': gate['decision'],
            'git_head': witness.head, 'page_updated': updated,
            'observed_sha256': _sha(current),
            'operation_id': OPERATION_ID,
            'put_executed': False, 'publication_authorized': False,
            'cron_enabled': False}


def _write_exclusive(path: Path, content: bytes) -> None:
    _need(not path.is_symlink(), 'Symlink backup destination rejected')
    with path.open('xb') as handle:
        handle.write(content)
    _need(path.read_bytes() == content, 'Backup readback mismatch')


def _save_prewrite(directory: Path, page: bytes, witness: GitWitness,
                   etag: str, updated: str) -> dict:
    """Local proof only; a separate external system must attest durable upload."""
    _need(isinstance(directory, Path) and not directory.exists(),
          'Prewrite archive already exists or invalid')
    _need(not directory.parent.is_symlink(), 'Archive parent cannot be symlink')
    directory.mkdir(parents=True, exist_ok=False)
    backup = directory / 'LOJA_ANTES_SEGUNDA_ROTACAO.html'
    _write_exclusive(backup, page)
    manifest = {'schema': 1, 'blog_id': BLOG_ID, 'page_id': PAGE_ID,
                'operation_id': OPERATION_ID, 'reservation_commit': RESERVATION_COMMIT,
                'git_head': witness.head, 'ledger_blob': witness.ledger_blob,
                'history_blob': witness.history_blob, 'etag': etag,
                'updated': updated, 'original_sha256': _sha(page),
                'candidate_sha256': CANDIDATE_SHA,
                'external_backup_uploaded': False, 'blogger_put_performed': False}
    raw = (json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True)+'\n').encode('utf-8')
    _write_exclusive(directory/'MANIFESTO_PREWRITE.json', raw)
    return manifest


def publish_once_with_external_gates(*, service, inputs: ImmutableInputs,
                                     read_remote: Callable[[], GitWitness],
                                     approval: WriteApproval | None,
                                     archive_dir: Path,
                                     verify_durable_backup: Callable[[dict], bool] | None,
                                     claim_attempt: Callable[[dict], FenceReceipt] | None) -> dict:
    """Library-only lab PUT: never run from the SAFE CI workflow.

    Remote observer and durable atomic attempt claim are external dependencies.
    No caller can omit these and reach Blogger PUT. Callbacks must authenticate
    Git ref state and persist CAS claim independently of this process.
    """
    _need(approval is not None and type(approval) is WriteApproval,
          'Explicit second LAB publication approval missing')
    _need(approval.explicit_lab_put_authorized is True
          and approval.operation_id == OPERATION_ID
          and approval.reservation_commit == RESERVATION_COMMIT,
          'Approval does not cover this exact LAB operation')
    _need(callable(read_remote) and callable(verify_durable_backup)
          and callable(claim_attempt),
          'Trusted remote witness, durable backup or atomic attempt gate unavailable')
    witness = read_remote()
    _need(type(witness) is GitWitness, 'Remote witness invalid')
    before = classify_read_only(service=service, inputs=inputs, witness=witness)
    if before['decision'] == 'CANDIDATE_ALREADY_IN_BLOGGER_SKIP_PUT_VERIFY_PUBLIC_ONLY':
        return {'status': 'V31_SECOND_ALREADY_APPLIED_NO_PUT',
                'put_executed': False, 'next': 'PUBLIC_PROOF_AND_RECONCILIATION_ONLY'}
    _need(before['decision'] == 'EXISTING_PLAN_READBACK_ORIGINAL_SEPARATE_APPROVAL_REQUIRED',
          'Current Blogger HTML cannot be published from this state')
    page1 = _get(service)
    original, etag, updated, title = _page_snapshot(page1)
    _need(_sha(original) == ORIGINAL_SHA, 'Blogger changed before backup')
    manifest = _save_prewrite(archive_dir, original, witness, etag, updated)
    # No attempt or PUT unless an external durable pre-PUT artifact was verified.
    _need(verify_durable_backup(manifest) is True,
          'Immutable prewrite backup not verified as durably uploaded')
    witness2 = read_remote()
    _need(witness2 == witness, 'Git head/ledger/history changed before PUT')
    page2 = _get(service)
    current, etag2, updated2, title2 = _page_snapshot(page2)
    if _sha(current) == CANDIDATE_SHA:
        return {'status': 'V31_SECOND_ALREADY_APPLIED_NO_PUT',
                'put_executed': False, 'next': 'PUBLIC_PROOF_AND_RECONCILIATION_ONLY'}
    _need(_sha(current) == ORIGINAL_SHA and etag2 == etag
          and updated2 == updated and title2 == title,
          'Blogger changed or ETag rotated before PUT')
    request = {'operation_id': OPERATION_ID,
               'reservation_commit': RESERVATION_COMMIT,
               'git_head': witness.head, 'ledger_blob': LEDGER_BLOB,
               'history_blob': HISTORY_BLOB,
               'original_sha256': ORIGINAL_SHA,
               'candidate_sha256': CANDIDATE_SHA,
               'etag': etag,
               'backup_sha256': _sha(original)}
    # A true external CAS claim must be durable before Blogger can be touched.
    receipt = claim_attempt(request)
    _need(type(receipt) is FenceReceipt and receipt.unique_claim is True
          and receipt.durable is True
          and receipt.operation_id == OPERATION_ID
          and receipt.original_sha256 == ORIGINAL_SHA
          and receipt.candidate_sha256 == CANDIDATE_SHA
          and receipt.git_head == witness.head and receipt.etag == etag,
          'No durable unique attempt CAS receipt; cannot send PUT')
    # At this point one PUT attempt is permitted. Never retry, including HTTP429.
    req = service.pages().update(blogId=BLOG_ID, pageId=PAGE_ID,
                                 body={'title': title, 'content': inputs.candidate.decode('utf-8')})
    _need(hasattr(req, 'headers') and isinstance(req.headers, dict),
          'Blogger API does not expose If-Match request headers')
    req.headers['If-Match'] = etag
    try:
        req.execute()
    except Exception as exc:
        raise PublicationBlocked(
            'BLOGGER_PUT_RESULT_UNCERTAIN_DO_NOT_RETRY: '
            + type(exc).__name__ + '. Require authenticated readback and public proof.') from exc
    try:
        page3 = _get(service)
        final, _, _, _ = _page_snapshot(page3)
    except Exception as exc:
        raise PublicationBlocked('BLOGGER_POST_PUT_READBACK_UNCERTAIN_DO_NOT_RETRY: '
                                 + type(exc).__name__) from exc
    _need(_sha(final) == CANDIDATE_SHA,
          'BLOGGER_POST_PUT_HTML_MISMATCH_DO_NOT_RETRY')
    return {'status': 'V31_SECOND_PUT_READBACK_CONFIRMED_AWAIT_PUBLIC_PROOF',
            'put_executed': True, 'operation_id': OPERATION_ID,
            'candidate_sha256': CANDIDATE_SHA,
            'next': 'INDEPENDENT_CLOUDFLARE_PUBLIC_EXACT_PASS_THEN_ATOMIC_GIT_COMMIT',
            'history_updated': False, 'cron_enabled': False}


def load_immutable_inputs(*, profile: Path, ledger: Path, history: Path,
                          selection: Path, original: Path,
                          candidate: Path) -> ImmutableInputs:
    return ImmutableInputs(*(p.read_bytes() for p in
                             (profile, ledger, history, selection, original, candidate)))
