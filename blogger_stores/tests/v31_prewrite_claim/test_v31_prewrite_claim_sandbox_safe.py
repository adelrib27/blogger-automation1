"""No Blogger HTTP; all pushes go to a locally created, marked, bare repo."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from threading import Barrier
import json
import os
import subprocess
import sys
import tempfile
import unittest

CORE = Path(__file__).resolve().parents[2] / 'v31_core'
sys.path.insert(0, str(CORE))
import v31_prewrite_claim_sandbox_safe as m
import v31_blogger_etag_policy_safe as etags


def git(cwd, *args):
    v = subprocess.run(['git', *args], cwd=cwd, text=True, capture_output=True, timeout=25)
    if v.returncode: raise RuntimeError(v.stderr)
    return v.stdout.strip()


def fixtures():
    first={'status':'PERSISTED','operationId':'8babc29b6609e369d10f674ef5730719b66e8dd2ca51e56a76d6c1f750e0fcdc',
           'selectionSha':'46ef8a293875720f036d90430d1e57c862277b42bde966fbf34b15f9d2cb6c0c'}
    second={'status':'PLAN','operationId':m.OP,'selectionSha':m.SELECTION,
            'originalSha':m.ORIGINAL,'candidateSha':m.CANDIDATE}
    ledger={'schema':1,'blogId':m.BLOG,'pageId':m.PAGE,'operations':[first,second]}
    history={'version':1,'blogId':m.BLOG,'runs':[{'source':'seed_from_current_blogger_store'},
        {'source':'blogger_published','operationId':first['operationId'],
         'selectionSha':first['selectionSha']}]}
    return ledger,history

class ClaimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get('V31_REAL_ORIGINAL_HTML')
        if not path:
            raise RuntimeError('V31_REAL_ORIGINAL_HTML authentic archived file required')
        cls.original=Path(path).read_bytes()
        assert sha256(cls.original).hexdigest()==m.ORIGINAL
        # Also validate real repo ledger/history if provided by CI.
        if os.environ.get('V31_REAL_LEDGER') and os.environ.get('V31_REAL_HISTORY'):
            led=json.loads(Path(os.environ['V31_REAL_LEDGER']).read_text())
            his=json.loads(Path(os.environ['V31_REAL_HISTORY']).read_text())
            out, _=m.plan_claim(ledger=led,history=his,html=cls.original,
                                 etag='"valid-ETag"',updated_at='2026-11-04T18:10:00-03:00',
                                 expected_head='1'*40,attempt_nonce='0'*32)
            assert json.loads(out)['operations'][-1]['prewriteClaim']['state']=='ATTEMPT_CLAIMED_BEFORE_PUT'

    def setUp(self):
        self.ledger,self.history=fixtures()
        self.etag='"VALIDSTRONG"'
        self.updated='2026-11-04T18:10:00-03:00'
    def claim(self,**kw):
        args=dict(ledger=self.ledger,history=self.history,html=self.original,
                  etag=self.etag,updated_at=self.updated,expected_head='1'*40,
                  attempt_nonce='1'*32)
        args.update(kw)
        return m.plan_claim(**args)
    def reject(self,**kw):
        with self.assertRaises(m.ClaimBlocked): self.claim(**kw)
    def test_real_html_validated(self): self.assertEqual(sha256(self.original).hexdigest(),m.ORIGINAL)
    def test_good_claim_is_deterministic_for_fixed_nonce(self):
        a,id1=self.claim();b,id2=self.claim();self.assertEqual((a,id1),(b,id2))
        self.assertEqual(json.loads(a)['operations'][-1]['status'],'PLAN')
        self.assertNotIn(b'blogger_put_allowed', a)
    def test_claim_does_not_modify_inputs(self):
        before=deepcopy((self.ledger,self.history));self.claim();self.assertEqual((self.ledger,self.history),before)
    def test_new_nonce_produces_distinct_git_bytes(self):
        a,_=self.claim();b,_=self.claim(attempt_nonce='2'*32);self.assertNotEqual(a,b)
    def test_missing_128bit_nonce_blocked(self): self.reject(attempt_nonce='f')
    def test_html_tampering_blocked(self): self.reject(html=self.original+b' ')
    def test_weak_etag_blocked(self): self.reject(etag='W/"weak"')
    def test_wildcard_etag_blocked(self): self.reject(etag='*')
    def test_unquoted_etag_blocked(self): self.reject(etag='abc')
    def test_empty_etag_blocked(self): self.reject(etag='')
    def test_invalid_head_blocked(self): self.reject(expected_head='x')
    def test_invalid_updated_blocked(self): self.reject(updated_at='')
    def test_wrong_blog_blocked(self):
        x=deepcopy(self.ledger);x['blogId']='9';self.reject(ledger=x)
    def test_wrong_page_blocked(self):
        x=deepcopy(self.ledger);x['pageId']='9';self.reject(ledger=x)
    def test_operation_not_plan_blocked(self):
        x=deepcopy(self.ledger);x['operations'][1]['status']='PERSISTED';self.reject(ledger=x)
    def test_prematurely_published_history_blocked(self):
        x=deepcopy(self.history);x['runs'].append({'operationId':m.OP});self.reject(history=x)
    def test_missing_history_lineage_blocked(self):
        x=deepcopy(self.history);x['runs'][1]['operationId']='a'*64;self.reject(history=x)
    def test_replay_after_claim_blocked(self):
        raw,_=self.claim();self.reject(ledger=json.loads(raw))
    def test_other_selection_blocked(self):
        x=deepcopy(self.ledger);x['operations'][1]['selectionSha']='a'*64;self.reject(ledger=x)
    def test_unexpected_extra_operation_blocked(self):
        x=deepcopy(self.ledger);x['operations'].append({});self.reject(ledger=x)

class SandboxGitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get('V31_REAL_ORIGINAL_HTML');cls.original=Path(path).read_bytes()
        assert sha256(cls.original).hexdigest()==m.ORIGINAL
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name);self.remote=root/'remote.git'
        git(root,'init','--bare',f'--initial-branch={m.BRANCH_SANDBOX}',str(self.remote))
        (self.remote/'V31_SANDBOX_ONLY').write_text('NO_GITHUB_REMOTE\n')
        self.a=root/'a';self.b=root/'b'
        git(root,'clone',str(self.remote),str(self.a))
        git(self.a,'checkout','-b',m.BRANCH_SANDBOX)
        led,his=fixtures()
        for path,data in ((m.LEDGER,m.canonical_json(led)),(m.HISTORY,m.canonical_json(his))):
            f=self.a/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
        git(self.a,'add','.');git(self.a,'-c','user.name=seed','-c','user.email=seed@example.invalid','commit','-m','seed')
        git(self.a,'push','origin',m.BRANCH_SANDBOX)
        git(root,'clone','--branch',m.BRANCH_SANDBOX,str(self.remote),str(self.b))
    def run_claim(self,clone,**kw):
        args=dict(checkout=clone,sandbox_remote=self.remote,original_html=self.original,
                  etag='"strong-etag"',updated_at='2026-11-04T18:10:00-03:00')
        args.update(kw)
        return m.commit_sandbox_claim(**args)
    def test_exactly_ledger_and_backup_are_committed(self):
        old_history=(self.a/m.HISTORY).read_bytes();receipt=self.run_claim(self.a)
        self.assertFalse(receipt.blogger_put_allowed)
        self.assertTrue(receipt.unique)
        self.assertEqual((self.a/m.BACKUP).read_bytes(),self.original)
        self.assertEqual((self.a/m.HISTORY).read_bytes(),old_history)
        files=git(self.a,'diff','--name-only',f'{receipt.parent}..{receipt.remote_commit}').splitlines()
        self.assertEqual(sorted(files),sorted([m.BACKUP,m.LEDGER]))
        new=json.loads((self.a/m.LEDGER).read_text());self.assertEqual(new['operations'][1]['status'],'PLAN')
        self.assertEqual(new['operations'][1]['prewriteClaim']['state'],'ATTEMPT_CLAIMED_BEFORE_PUT')
    def test_one_shot_claim_rejects_repeat(self):
        self.run_claim(self.a)
        with self.assertRaises(m.ClaimBlocked):self.run_claim(self.a)
    def test_stale_clone_is_rejected(self):
        self.run_claim(self.a)
        with self.assertRaises(m.ClaimBlocked):self.run_claim(self.b)
        self.assertFalse((self.b/m.BACKUP).exists())
    def test_racing_clones_exactly_one_push_wins(self):
        barrier=Barrier(2)
        def f(clone):
            try:return self.run_claim(clone,before_push=lambda:barrier.wait(timeout=15))
            except m.ClaimBlocked:return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            future1=pool.submit(f,self.a);future2=pool.submit(f,self.b)
            values=[future1.result(timeout=45),future2.result(timeout=45)]
        self.assertEqual(sum(x is not None for x in values),1)
        winning=next(x for x in values if x is not None)
        self.assertEqual(git(self.a,'ls-remote','origin',f'refs/heads/{m.BRANCH_SANDBOX}').split()[0],winning.remote_commit)
    def test_unmarked_remote_rejected(self):
        (self.remote/'V31_SANDBOX_ONLY').unlink()
        with self.assertRaises(m.ClaimBlocked):self.run_claim(self.a)
    def test_invalid_marker_rejected(self):
        (self.remote/'V31_SANDBOX_ONLY').write_text('REAL')
        with self.assertRaises(m.ClaimBlocked):self.run_claim(self.a)
    def test_wrong_branch_rejected(self):
        git(self.a,'checkout','-b','main')
        with self.assertRaises(m.ClaimBlocked):self.run_claim(self.a)
    def test_dirty_checkout_rejected(self):
        (self.a/'untracked').write_text('x')
        with self.assertRaises(m.ClaimBlocked):self.run_claim(self.a)
    def test_remote_mismatch_rejected(self):
        git(self.a,'remote','set-url','origin','https://github.com/adelrib27/blogger-automation1.git')
        with self.assertRaises(m.ClaimBlocked):self.run_claim(self.a)
    def test_existing_backup_path_rejected(self):
        f=self.a/m.BACKUP;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('old')
        with self.assertRaises(m.ClaimBlocked):self.run_claim(self.a)
    def test_tampered_ledger_rejected(self):
        p=self.a/m.LEDGER;d=json.loads(p.read_text());d['operations'][1]['candidateSha']='a'*64
        p.write_bytes(m.canonical_json(d));git(self.a,'add','.');git(self.a,'-c','user.name=bad','-c','user.email=bad@example.invalid','commit','-m','bad');git(self.a,'push','origin',m.BRANCH_SANDBOX)
        with self.assertRaises(m.ClaimBlocked):self.run_claim(self.a)

class BloggerIfMatchProofTests(unittest.TestCase):
    def setUp(self):
        self.proof={ 'blogId':m.BLOG, 'pageId':m.PAGE,
            'apiMethod':'blogger.pages.update','httpMethod':'PUT',
            'originalEtag':'"strong-current"','staleEtag':'"strong-stale"',
            'sentIfMatch':'"strong-stale"','responseStatus':412,
            'readbackNoMutation':True,'authenticatedGet':True,
            'authorizedTest':True,'independentEvidenceRef':'OFFLINE_SYNTHETIC_ONLY'}
    def deny(self,**updates):
        p=deepcopy(self.proof);p.update(updates)
        with self.assertRaises(etags.EtagProofBlocked):etags.assess_if_match_proof(p)
    def test_no_real_proof_blocks(self):
        with self.assertRaises(etags.EtagProofBlocked):etags.assess_if_match_proof(None)
    def test_hypothetical_positive_is_not_publication_authorization(self):
        v=etags.assess_if_match_proof(self.proof)
        self.assertFalse(v['blogger_put_allowed']);self.assertFalse(v['publication_authorized'])
    def test_http_200_not_proof(self):self.deny(responseStatus=200)
    def test_http_409_not_proof(self):self.deny(responseStatus=409)
    def test_http_304_not_proof(self):self.deny(responseStatus=304)
    def test_weak_original_etag_not_allowed(self):self.deny(originalEtag='W/"weak"')
    def test_weak_stale_etag_not_allowed(self):self.deny(staleEtag='W/"weak"',sentIfMatch='W/"weak"')
    def test_if_match_wildcard_not_allowed(self):self.deny(staleEtag='*',sentIfMatch='*')
    def test_same_etag_not_proof(self):self.deny(staleEtag='"strong-current"',sentIfMatch='"strong-current"')
    def test_other_blog_not_proof(self):self.deny(blogId='9')
    def test_other_page_not_proof(self):self.deny(pageId='9')
    def test_no_authenticated_readback(self):self.deny(authenticatedGet=False)
    def test_mutated_page_not_proof(self):self.deny(readbackNoMutation=False)
    def test_not_authorized_test_not_proof(self):self.deny(authorizedTest=False)
    def test_no_evidence_ref_not_proof(self):self.deny(independentEvidenceRef='')
    def test_different_method_not_proof(self):self.deny(httpMethod='PATCH')
    def test_missing_header_not_proof(self):self.deny(sentIfMatch=None)

if __name__=='__main__': unittest.main()
