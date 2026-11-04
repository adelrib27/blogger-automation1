"""Fake authenticated Blogger API + pure gate: no network and no Git writes.

Real pinned HTML artifacts are supplied by the SAFE CI in V31_TEST_REAL_HTML_DIR.
This suite tests the one-attempt orchestration, not public Cloudflare proof.
"""
import copy
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

MOD = Path(__file__).resolve().parents[2] / 'src'
sys.path.insert(0, str(MOD))
import v31_second_publish_once_lab as once

GIT_HEAD = '1f31897758a116f7bd66fe76ef6f7f92eff0e52c'


class FakeGet:
    def __init__(self, service): self.s = service
    def execute(self):
        self.s.get_count += 1
        if self.s.get_count in self.s.on_get:
            self.s.current = self.s.on_get[self.s.get_count]
        return copy.deepcopy(self.s.current)


class FakeUpdate:
    def __init__(self, service, body):
        self.s = service
        self.body = body
        self.headers = {}
    def execute(self):
        self.s.put_count += 1
        self.s.headers_seen.append(dict(self.headers))
        if self.s.error_on_put:
            raise TimeoutError('simulated: Blogger PUT accepted, response lost')
        if not self.s.fail_to_apply:
            self.s.current['content'] = self.body['content']
            self.s.current['etag'] = '"after-ETag"'
            self.s.current['updated'] = '2026-11-04T18:50:00-03:00'
        return {'id': once.PAGE_ID}


class FakePages:
    def __init__(self, service): self.s = service
    def get(self, *, blogId, pageId):
        if (blogId, pageId) != (once.BLOG_ID, once.PAGE_ID): raise AssertionError('Wrong Blogger target')
        return FakeGet(self.s)
    def update(self, *, blogId, pageId, body):
        if (blogId, pageId) != (once.BLOG_ID, once.PAGE_ID): raise AssertionError('Wrong PUT target')
        return FakeUpdate(self.s, body)


class FakeService:
    def __init__(self, html):
        self.current = {'id': once.PAGE_ID, 'blog': {'id': once.BLOG_ID}, 'title': 'LOJA',
                        'url': once.PAGE_URL, 'etag': '"ETag-before"',
                        'updated': '2026-11-03T22:19:09-03:00',
                        'content': html.decode('utf-8')}
        self.get_count = self.put_count = 0
        self.headers_seen = []
        self.error_on_put = self.fail_to_apply = False
        self.on_get = {}
    def pages(self): return FakePages(self)


class OnceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = os.environ.get('V31_TEST_REAL_HTML_DIR')
        if not directory:
            raise RuntimeError('V31_TEST_REAL_HTML_DIR required: provide authentic archived original/candidate HTML')
        p = Path(directory)
        cls.original = (p/'LOJA_ORIGINAL_BACKUP.html').read_bytes()
        cls.candidate = (p/'LOJA_CANDIDATA_NAO_PUBLICAR.html').read_bytes()
        assert sha256(cls.original).hexdigest() == once.ORIGINAL_SHA
        assert sha256(cls.candidate).hexdigest() == once.CANDIDATE_SHA

    def setUp(self):
        self.s = FakeService(self.original)
        self.inputs = once.ImmutableInputs(
            profile=b'{}', ledger=b'{}', history=b'{}', selection=b'{}',
            original=self.original, candidate=self.candidate)
        self.w = once.GitWitness(once.REPOSITORY, once.BRANCH, GIT_HEAD, True,
                                 once.LEDGER_BLOB, once.HISTORY_BLOB)
        self.ap = once.WriteApproval(once.OPERATION_ID, once.RESERVATION_COMMIT, True)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'prewrite-unique'
        self.uploads = []
        self.claims = []
        self.n_remote = 0
        self.gate_mock = patch.object(once, 'gate_second_publish_safe', side_effect=self.fake_gate)
        self.gate_mock.start()
        self.addCleanup(self.gate_mock.stop)

    def fake_gate(self, **kwargs):
        if not kwargs.get('observed_blogger_is_authenticated_live'):
            raise once.GateBlocked('No authenticated GET')
        obs = sha256(kwargs['observed_blogger_html_bytes']).hexdigest()
        if obs == once.ORIGINAL_SHA:
            decision = 'EXISTING_PLAN_READBACK_ORIGINAL_SEPARATE_APPROVAL_REQUIRED'
        elif obs == once.CANDIDATE_SHA:
            decision = 'CANDIDATE_ALREADY_IN_BLOGGER_SKIP_PUT_VERIFY_PUBLIC_ONLY'
        else:
            raise once.GateBlocked('Unexpected HTML')
        return {'observed_blogger_live_authenticated':True, 'decision': decision}

    def witness(self):
        self.n_remote += 1
        return self.w

    def attest(self, manifest):
        self.uploads.append(manifest)
        return True

    def claim(self, request):
        self.claims.append(request)
        return once.FenceReceipt(once.OPERATION_ID, once.ORIGINAL_SHA, once.CANDIDATE_SHA,
                                 self.w.head, '"ETag-before"', True, True)

    def go(self, **extra):
        kw=dict(service=self.s, inputs=self.inputs, read_remote=self.witness,
                approval=self.ap, archive_dir=self.path,
                verify_durable_backup=self.attest, claim_attempt=self.claim)
        kw.update(extra)
        return once.publish_once_with_external_gates(**kw)

    def blocked(self, **kwargs):
        with self.assertRaises(once.PublicationBlocked): self.go(**kwargs)
        self.assertEqual(self.s.put_count, 0)

    def test_readonly_is_not_an_authorization(self):
        result=once.classify_read_only(service=self.s, inputs=self.inputs, witness=self.w)
        self.assertEqual(result['status'], 'V31_SECOND_ONCE_READONLY_VALIDATED')
        self.assertFalse(result['put_executed'])
        self.assertFalse(result['publication_authorized'])
        self.assertEqual(self.s.put_count, 0)

    def test_missing_user_approval_blocks(self): self.blocked(approval=None)
    def test_wrong_operation_approval_blocks(self):
        self.blocked(approval=once.WriteApproval('f'*64, once.RESERVATION_COMMIT, True))
    def test_approval_flag_false_blocks(self):
        self.blocked(approval=once.WriteApproval(once.OPERATION_ID, once.RESERVATION_COMMIT, False))
    def test_wrong_reservation_commit_blocks(self):
        self.blocked(approval=once.WriteApproval(once.OPERATION_ID, 'a'*40, True))
    def test_missing_backup_attestor_blocks(self): self.blocked(verify_durable_backup=None)
    def test_missing_atomic_claim_service_blocks(self): self.blocked(claim_attempt=None)
    def test_wrong_git_branch_blocks(self):
        self.w = once.GitWitness(once.REPOSITORY, 'main', GIT_HEAD, True,
                                  once.LEDGER_BLOB, once.HISTORY_BLOB)
        self.blocked()
    def test_wrong_git_ledger_blob_blocks(self):
        self.w = once.GitWitness(once.REPOSITORY, once.BRANCH, GIT_HEAD, True,
                                  'f'*40, once.HISTORY_BLOB)
        self.blocked()
    def test_reservation_not_ancestor_blocks(self):
        self.w = once.GitWitness(once.REPOSITORY, once.BRANCH, GIT_HEAD, False,
                                  once.LEDGER_BLOB, once.HISTORY_BLOB)
        self.blocked()
    def test_wrong_page_identity_blocks(self):
        self.s.current['blog']['id'] = 'wrong'
        self.blocked()
    def test_missing_etag_blocks(self):
        self.s.current.pop('etag')
        self.blocked()
    def test_wrong_page_url_blocks(self):
        self.s.current['url'] = 'https://somewhere.invalid/loja.html'
        self.blocked()
    def test_html_not_original_nor_candidate_blocks(self):
        self.s.current['content'] += ' '  # changes the exact SHA
        self.blocked()
    def test_candidate_already_applied_is_no_put(self):
        self.s.current['content'] = self.candidate.decode('utf-8')
        result=self.go()
        self.assertEqual(result['status'], 'V31_SECOND_ALREADY_APPLIED_NO_PUT')
        self.assertEqual(self.s.put_count, 0)
        self.assertFalse(self.path.exists())
    def test_no_external_durable_backup_blocks_after_local_archive(self):
        self.blocked(verify_durable_backup=lambda m: False)
        self.assertTrue((self.path/'LOJA_ANTES_SEGUNDA_ROTACAO.html').exists())
        self.assertFalse(self.claims)
    def test_remote_head_changes_before_put_blocks(self):
        def changes():
            current=getattr(self,'called',0)+1;self.called=current
            if current==1:return self.w
            return once.GitWitness(once.REPOSITORY,once.BRANCH,'f'*40,True,once.LEDGER_BLOB,once.HISTORY_BLOB)
        self.blocked(read_remote=changes)
        self.assertFalse(self.claims)
    def test_blogger_etag_rotates_before_put_blocks(self):
        altered=copy.deepcopy(self.s.current);altered['etag']='"parallel-edit"'
        self.s.on_get[3] = altered
        self.blocked()
        self.assertFalse(self.claims)
    def test_blogger_html_candidate_appears_before_put_skips(self):
        altered=copy.deepcopy(self.s.current);altered['content']=self.candidate.decode('utf-8')
        self.s.on_get[3]=altered
        result=self.go()
        self.assertEqual(result['status'],'V31_SECOND_ALREADY_APPLIED_NO_PUT')
        self.assertEqual(self.s.put_count,0)
        self.assertFalse(self.claims)
    def test_claim_rejected_blocks(self):
        def nope(x):
            return once.FenceReceipt(once.OPERATION_ID,once.ORIGINAL_SHA,once.CANDIDATE_SHA,
                                     self.w.head,'"ETag-before"',False,True)
        self.blocked(claim_attempt=nope)
    def test_claim_not_durable_blocks(self):
        def nope(x):
            return once.FenceReceipt(once.OPERATION_ID,once.ORIGINAL_SHA,once.CANDIDATE_SHA,
                                     self.w.head,'"ETag-before"',True,False)
        self.blocked(claim_attempt=nope)
    def test_claim_wrong_operation_blocks(self):
        def nope(x):
            return once.FenceReceipt('a'*64,once.ORIGINAL_SHA,once.CANDIDATE_SHA,
                                     self.w.head,'"ETag-before"',True,True)
        self.blocked(claim_attempt=nope)
    def test_backup_target_already_exists_blocks(self):
        self.path.mkdir()
        self.blocked()
    def test_unique_put_uses_if_match_and_preserves_backup(self):
        result=self.go()
        self.assertEqual(result['status'], 'V31_SECOND_PUT_READBACK_CONFIRMED_AWAIT_PUBLIC_PROOF')
        self.assertEqual(self.s.put_count, 1)
        self.assertEqual(self.s.headers_seen[0]['If-Match'], '"ETag-before"')
        self.assertEqual((self.path/'LOJA_ANTES_SEGUNDA_ROTACAO.html').read_bytes(), self.original)
        self.assertEqual(len(self.uploads), 1)
        self.assertEqual(len(self.claims), 1)
        self.assertFalse(result['history_updated'])
        self.assertFalse(result['cron_enabled'])
    def test_timeout_after_put_must_never_retry(self):
        self.s.error_on_put=True
        with self.assertRaisesRegex(once.PublicationBlocked, 'DO_NOT_RETRY'):
            self.go()
        self.assertEqual(self.s.put_count, 1)
        self.assertEqual(len(self.claims), 1)
    def test_post_put_unknown_result_must_never_retry(self):
        self.s.fail_to_apply=True
        with self.assertRaisesRegex(once.PublicationBlocked, 'DO_NOT_RETRY'):
            self.go()
        self.assertEqual(self.s.put_count, 1)
    def test_after_readback_failed_must_never_retry(self):
        after=copy.deepcopy(self.s.current)
        after['content']='unexpected response after successful update'
        self.s.on_get[4]=after
        with self.assertRaisesRegex(once.PublicationBlocked, 'DO_NOT_RETRY'):
            self.go()
        self.assertEqual(self.s.put_count, 1)
    def test_second_call_after_success_classifies_already_applied(self):
        self.go()
        second=self.go(archive_dir=self.path.parent/'new-archive')
        self.assertEqual(second['status'],'V31_SECOND_ALREADY_APPLIED_NO_PUT')
        self.assertEqual(self.s.put_count,1)
    def test_local_backup_manifest_explicitly_marks_no_put(self):
        self.go()
        manifest=json.loads((self.path/'MANIFESTO_PREWRITE.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['operation_id'],once.OPERATION_ID)
        self.assertFalse(manifest['blogger_put_performed'])
        self.assertFalse(manifest['external_backup_uploaded'])
    def test_fake_authorization_not_sufficient_for_actual_network(self):
        self.blocked(read_remote=None)

if __name__=='__main__':unittest.main()
