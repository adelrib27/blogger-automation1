"""Targeted R12 tests: no Blogger API, no GitHub writes, no network, no cron.

These tests use a fake authenticated gateway and real approved original HTML.
The actual Git remote/If-Match was tested separately; do not repeat it here.
"""
from __future__ import annotations
from hashlib import sha1, sha256
import copy
import json
import secrets
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
# In GitHub CI: blogger_stores/tests/v31_atomic_claim_bridge -> blogger_stores
ROOT = HERE.parents[1] if HERE.name == 'v31_atomic_claim_bridge' else HERE
for source in (ROOT / 'v31_core', ROOT / 'src', HERE):
    sys.path.insert(0, str(source))
import v31_atomic_git_claim_bridge_lab as v


class FakeGit:
    sandbox_only = True
    repository = v.REPO
    branch = v.BRANCH
    def __init__(self, ledger, history):
        self._head = 'a' * 40
        self.objects = {self._head: {v.LEDGER: ledger, v.HISTORY: history}}
        self.parents = {}
        self.changes = {}
        self.write_count = 0
        self.fail_cas = False
    def head(self): return self._head
    def read_blob(self, commit, path):
        if path not in self.objects[commit]: raise FileNotFoundError(path)
        return self.objects[commit][path]
    def commit_nonforce(self, expected_head, changes):
        if self.fail_cas or expected_head != self._head:
            raise v.BridgeBlocked('CAS failed: no retry')
        self.write_count += 1
        new = copy.deepcopy(self.objects[expected_head]);new.update(changes)
        key = sha1(secrets.token_bytes(16)).hexdigest()
        self.objects[key] = new; self.parents[key] = expected_head
        self.changes[key] = frozenset(changes)
        self._head = key
        return key
    def parent(self, commit): return self.parents[commit]
    def changed_paths(self, commit): return self.changes[commit]


class ClaimAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Inside CI these two HTML inputs may be read from the archived artifacts;
        # locally they reside next to this test. No synthetic HTML is accepted.
        path = Path(__file__).resolve().parent / 'LOJA_ORIGINAL_BACKUP.html'
        if not path.exists():
            import os
            archived = os.environ.get('V31_TEST_REAL_HTML_DIR')
            if not archived: raise RuntimeError('Approved original HTML required')
            path = Path(archived)/path.name
        cls.html = path.read_bytes()
        assert sha256(cls.html).hexdigest() == v.ORIGINAL

    def setUp(self):
        led = {'schema':1,'blogId':v.BLOG,'pageId':v.PAGE,'operations':[
            {'status':'PERSISTED','operationId':'f'*64,'selectionSha':'e'*64,
             'candidateSha':v.ORIGINAL},
            {'status':'PLAN','operationId':v.OP,'selectionSha':v.SELECTION,
             'originalSha':v.ORIGINAL,'candidateSha':v.CANDIDATE}]}
        hist = {'version':1,'blogId':v.BLOG,'runs':[
            {'source':'seed_from_current_blogger_store'},
            {'source':'blogger_published','operationId':'f'*64,
             'selectionSha':'e'*64}]}
        ledger=json.dumps(led,sort_keys=True).encode()
        history=json.dumps(hist,sort_keys=True).encode()
        self.g=FakeGit(ledger,history)
        self.pins={'ledger':v.git_blob(ledger),'history':v.git_blob(history)}
        self.archive_reads=0
        def reader():
            self.archive_reads+=1
            return self.html
        self.bridge=v.LabAtomicClaimBridge(gateway=self.g,
            archived_backup_reader=reader,original_html=self.html,
            armed=True,pins=self.pins)
        self.etag='"etag-before"'
        self.manifest={'blog_id':v.BLOG,'page_id':v.PAGE,
            'operation_id':v.OP,'reservation_commit':v.RESERVATION,
            'original_sha256':v.ORIGINAL,'candidate_sha256':v.CANDIDATE,
            'ledger_blob':self.pins['ledger'],'history_blob':self.pins['history'],
            'git_head':self.g.head(),'etag':self.etag,
            'updated':'2026-11-03T22:19:09-03:00',
            'external_backup_uploaded':False}
        self.req={'operation_id':v.OP,'reservation_commit':v.RESERVATION,
            'original_sha256':v.ORIGINAL,'candidate_sha256':v.CANDIDATE,
            'backup_sha256':v.ORIGINAL,'ledger_blob':self.pins['ledger'],
            'history_blob':self.pins['history'],
            'git_head':self.g.head(),'etag':self.etag}

    def test_backup_and_claim_atomic_and_readback(self):
        self.assertTrue(self.bridge.verify_durable_backup(self.manifest))
        receipt=self.bridge.claim_attempt(self.req)
        self.assertEqual(receipt.operation_id,v.OP)
        self.assertTrue(receipt.unique_claim and receipt.durable)
        self.assertEqual(self.g.write_count,1)
        self.assertEqual(self.g.read_blob(self.g.head(),v.BACKUP),self.html)
        self.assertEqual(self.g.read_blob(self.g.head(),v.HISTORY),
                         self.g.read_blob('a'*40,v.HISTORY))
        self.assertEqual(json.loads(self.g.read_blob(self.g.head(),v.LEDGER))['operations'][-1]
                         ['prewriteClaim']['state'],'ATTEMPT_CLAIMED_BEFORE_PUT')
        self.assertTrue(self.bridge.last_audit.exact_remote_readback)
        self.assertFalse(self.bridge.last_audit.blogger_put_performed)

    def test_default_is_disarmed(self):
        a=v.LabAtomicClaimBridge(gateway=self.g,archived_backup_reader=lambda:self.html,
             original_html=self.html,pins=self.pins)
        a.verify_durable_backup(self.manifest)
        with self.assertRaisesRegex(v.BridgeBlocked,'NOT authorized'):
            a.claim_attempt(self.req)
        self.assertEqual(self.g.write_count,0)

    def test_unattested_claim_blocked(self):
        with self.assertRaisesRegex(v.BridgeBlocked,'backup missing'):
            self.bridge.claim_attempt(self.req)
        self.assertEqual(self.g.write_count,0)

    def test_retained_archive_bytes_must_match(self):
        self.bridge.reader=lambda:b'wrong archived html'
        with self.assertRaises(v.BridgeBlocked):
            self.bridge.verify_durable_backup(self.manifest)
        self.assertEqual(self.g.write_count,0)

    def test_manifest_identity_mismatch_rejected(self):
        m={**self.manifest,'page_id':'1'}
        with self.assertRaises(v.BridgeBlocked):self.bridge.verify_durable_backup(m)

    def test_etag_changed_after_backup_blocks(self):
        self.bridge.verify_durable_backup(self.manifest)
        with self.assertRaises(v.BridgeBlocked):
            self.bridge.claim_attempt({**self.req,'etag':'"different"'})
        self.assertEqual(self.g.write_count,0)

    def test_stale_git_head_rejected(self):
        self.bridge.verify_durable_backup(self.manifest)
        self.g._head='b'*40
        with self.assertRaises(v.BridgeBlocked):self.bridge.claim_attempt(self.req)
        self.assertEqual(self.g.write_count,0)

    def test_competing_claim_rejected_without_retry(self):
        self.bridge.verify_durable_backup(self.manifest)
        self.g.fail_cas=True
        with self.assertRaises(v.BridgeBlocked):self.bridge.claim_attempt(self.req)
        self.assertEqual(self.g.write_count,0)
        self.assertFalse(self.bridge.backup_verified)

    def test_existing_remote_backup_blocks(self):
        self.bridge.verify_durable_backup(self.manifest)
        self.g.objects[self.g.head()][v.BACKUP]=self.html
        with self.assertRaisesRegex(v.BridgeBlocked,'already exists'):
            self.bridge.claim_attempt(self.req)
        self.assertEqual(self.g.write_count,0)

    def test_history_or_ledger_blob_changed_blocks(self):
        self.bridge.verify_durable_backup(self.manifest)
        self.g.objects[self.g.head()][v.HISTORY]+=b'\n'
        with self.assertRaises(v.BridgeBlocked):self.bridge.claim_attempt(self.req)
        self.assertEqual(self.g.write_count,0)

    def test_readback_incomplete_blocks_even_after_claim(self):
        self.bridge.verify_durable_backup(self.manifest)
        good=self.g.commit_nonforce
        def corrupt(head,changes):
            commit=good(head,changes)
            self.g.objects[commit][v.BACKUP]=b'missing backup bytes'
            return commit
        self.g.commit_nonforce=corrupt
        with self.assertRaises(v.BridgeBlocked):self.bridge.claim_attempt(self.req)
        self.assertEqual(self.g.write_count,1)
        self.assertIsNone(self.bridge.last_audit)

    def test_custom_pins_must_be_sandbox_only(self):
        self.g.sandbox_only=False
        with self.assertRaises(v.BridgeBlocked):
            v.LabAtomicClaimBridge(gateway=self.g,
              archived_backup_reader=lambda:self.html,
              original_html=self.html,pins=self.pins)

    def test_wrong_repo_gateway_is_blocked(self):
        self.g.repository='another/repo'
        with self.assertRaises(v.BridgeBlocked):
            v.LabAtomicClaimBridge(gateway=self.g,
              archived_backup_reader=lambda:self.html, original_html=self.html)

    def test_no_publication_implementation(self):
        self.assertFalse(hasattr(self.bridge,'blogger_put'))
        self.assertFalse(hasattr(self.bridge,'enable_cron'))


if __name__=='__main__': unittest.main()
