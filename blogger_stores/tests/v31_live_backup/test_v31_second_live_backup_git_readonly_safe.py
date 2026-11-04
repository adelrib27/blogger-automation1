"""Small isolated checks for LIVE GET/immutable backup/Git preflight. No network."""
import copy
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import v31_second_live_backup_git_readonly_safe as target

class FakeGateway:
    repository=target.REPO
    branch=target.BRANCH
    def __init__(self, ledger, history):
        self.commit='a'*40
        self.blobs={target.LEDGER:ledger,target.HISTORY:history}
    def head(self):return self.commit
    def read_blob(self,commit,path):
        assert commit==self.commit
        if path not in self.blobs:raise FileNotFoundError(path)
        return self.blobs[path]

class TestReadOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d=Path(os.environ.get('V31_TEST_REAL_HTML_DIR',str(ROOT/'../../')))
        cls.original=(d/'LOJA_ORIGINAL_BACKUP.html').read_bytes()
        cls.candidate=(d/'LOJA_CANDIDATA_NAO_PUBLICAR.html').read_bytes()
        assert sha256(cls.original).hexdigest()==target.ORIGINAL
        assert sha256(cls.candidate).hexdigest()==target.CANDIDATE
    def setUp(self):
        first={'operationId':'f'*64,'selectionSha':'e'*64,'status':'PERSISTED'}
        second={'status':'PLAN','operationId':target.OP,'selectionSha':target.SELECTION,
                'originalSha':target.ORIGINAL,'candidateSha':target.CANDIDATE}
        led={'schema':1,'blogId':target.BLOG,'pageId':target.PAGE,'operations':[first,second]}
        his={'version':1,'blogId':target.BLOG,'runs':[{'source':'seed_from_current_blogger_store'},
                {'source':'blogger_published','operationId':first['operationId'],'selectionSha':first['selectionSha']}]}
        self.git=FakeGateway(json.dumps(led).encode(),json.dumps(his).encode())
        self.p1=patch.object(target,'BASE_LEDGER_BLOB',target.git_blob(self.git.blobs[target.LEDGER]));self.p1.start()
        self.p2=patch.object(target,'BASE_HISTORY_BLOB',target.git_blob(self.git.blobs[target.HISTORY]));self.p2.start()
        self.addCleanup(self.p1.stop);self.addCleanup(self.p2.stop)
        self.page={'id':target.PAGE,'blog':{'id':target.BLOG},'title':'LOJA','url':target.URL,
                   'content':self.original.decode('utf-8'),'updated':target.UPDATED,
                   'etag':'"valid-strong-etag"'}
    def go(self,**kwargs):
        args=dict(page=self.page,authenticated_live_page_ids=frozenset({target.PAGE}),
                  archived_original=self.original,
                  archived_candidate=self.candidate,gateway=self.git,
                  expected_head=self.git.head(),reservation_is_ancestor=True)
        args.update(kwargs)
        return target.attest(**args)
    def test_original_live_and_remote_git_readonly_pass(self):
        r=self.go();self.assertTrue(r['live_get_authenticated']);self.assertFalse(r['publication_authorized']);self.assertFalse(r['durable_remote_claim_committed'])
    def test_archive_byte_mismatch_blocks(self):
        with self.assertRaises(target.PreflightBlocked):self.go(archived_original=self.original+b'\n')
    def test_candidate_corruption_blocks(self):
        with self.assertRaises(target.PreflightBlocked):self.go(archived_candidate=self.candidate[:-1])
    def test_blogger_change_blocks(self):
        self.page['content']+=' ';self.assertRaises(target.PreflightBlocked,self.go)
    def test_missing_from_authenticated_live_inventory_blocks(self):
        self.assertRaises(target.PreflightBlocked,self.go,authenticated_live_page_ids=frozenset())
    def test_draft_status_if_present_blocks(self):
        self.page['status']='DRAFT';self.assertRaises(target.PreflightBlocked,self.go)
    def test_weak_etag_blocks(self):
        self.page['etag']='W/"weak"';self.assertRaises(target.PreflightBlocked,self.go)
    def test_stale_remote_head_blocks(self):
        self.assertRaises(target.PreflightBlocked,self.go,expected_head='b'*40)
    def test_claimed_plan_blocks(self):
        ledger=json.loads(self.git.blobs[target.LEDGER]);ledger['operations'][1]['prewriteClaim']={'state':'ATTEMPT_CLAIMED_BEFORE_PUT'}
        self.git.blobs[target.LEDGER]=json.dumps(ledger).encode()
        with patch.object(target,'BASE_LEDGER_BLOB',target.git_blob(self.git.blobs[target.LEDGER])):
            self.assertRaises(target.PreflightBlocked,self.go)
    def test_existing_git_backup_blocks(self):
        self.git.blobs[target.BACKUP]=self.original
        self.assertRaises(target.PreflightBlocked,self.go)
    def test_history_tampering_blocks(self):
        self.git.blobs[target.HISTORY]+=b' '
        self.assertRaises(target.PreflightBlocked,self.go)
    def test_unverified_reservation_ancestry_blocks(self):
        self.assertRaises(target.PreflightBlocked,self.go,reservation_is_ancestor=False)

if __name__=='__main__':unittest.main()
