import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'v31_core'))
from v31_rotation_ledger import *
BLOG_ID='4739187376492839837';PAGE_ID='2446067640331732447'
A='a'*64;B='b'*64;C='c'*64;D='d'*64

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.state=stage(initial_state(BLOG_ID,PAGE_ID),A,B,C)
        self.history={'version':1,'blogId':BLOG_ID,'runs':[]}
        self.items=[{'itemId':str(20042293295+i),'category':'Quarto'} for i in range(16)]
        self.proof={'status':'PUBLIC_EXACT_PASS','selection_sha256':A,'cards':16,'images':16,'links':16,'public_http':200}
    def test_stages_once(self):self.assertEqual(len(stage(self.state,A,B,C)['operations']),1)
    def test_cannot_stage_when_other_pending(self):
        with self.assertRaises(LedgerError):stage(self.state,D,B,C)
    def test_disallow_inconsistent_same_id(self):
        with self.assertRaises(LedgerError):stage(self.state,A,B,D)
    def test_cannot_mark_before_readback(self):
        with self.assertRaises(LedgerError):mark_public_verified(self.state,A,proof=self.proof)
    def test_readback_wrong_hash(self):
        with self.assertRaises(LedgerError):mark_readback(self.state,A,observed_candidate_sha=D)
    def test_readback_idempotent(self):
        s=mark_readback(self.state,A,observed_candidate_sha=C)
        self.assertEqual(s,mark_readback(s,A,observed_candidate_sha=C))
    def test_public_wrong_selection(self):
        s=mark_readback(self.state,A,observed_candidate_sha=C)
        with self.assertRaises(LedgerError):mark_public_verified(s,A,proof={**self.proof,'selection_sha256':D})
    def test_public_throttled_not_valid(self):
        s=mark_readback(self.state,A,observed_candidate_sha=C)
        with self.assertRaises(LedgerError):mark_public_verified(s,A,proof={'status':'PUBLIC_PENDING_THROTTLED'})
    def test_cannot_commit_before_public(self):
        with self.assertRaises(LedgerError):history_commit(self.state,A,self.history,published_items=self.items,published_at='2026-11-03T22:19:09-03:00')
    def test_commit_only_once(self):
        s=mark_public_verified(mark_readback(self.state,A,observed_candidate_sha=C),A,proof=self.proof)
        h1,s1= None,None
        s1,h1=history_commit(s,A,self.history,published_items=self.items,published_at='2026-11-03T22:19:09-03:00')
        s2,h2=history_commit(s1,A,h1,published_items=self.items,published_at='2026-11-03T22:19:09-03:00')
        self.assertEqual(len(h2['runs']),1)
        self.assertEqual(s2,s1)
    def test_can_stage_next_after_persist(self):
        s=mark_public_verified(mark_readback(self.state,A,observed_candidate_sha=C),A,proof=self.proof)
        s,_=history_commit(s,A,self.history,published_items=self.items,published_at='2026-11-03T22:19:09-03:00')
        n=stage(s,D,C,B)
        self.assertEqual(len(n['operations']),2)
    def test_one_active_guard(self):
        s=stage(self.state,A,B,C);s['operations'].append({**s['operations'][0],'operationId':operation_id(D,BLOG_ID,PAGE_ID),'selectionSha':D})
        with self.assertRaises(LedgerError):validate_state(s)
    def test_cross_blog_history(self):
        s=mark_public_verified(mark_readback(self.state,A,observed_candidate_sha=C),A,proof=self.proof)
        with self.assertRaises(LedgerError):history_commit(s,A,{**self.history,'blogId':'42'},published_items=self.items,published_at='2026-11-03T22:19:09-03:00')
    def test_bad_product_duplicates(self):
        s=mark_public_verified(mark_readback(self.state,A,observed_candidate_sha=C),A,proof=self.proof)
        items=self.items[:-1]+self.items[:1]
        with self.assertRaises(LedgerError):history_commit(s,A,self.history,published_items=items,published_at='2026-11-03T22:19:09-03:00')

if __name__=='__main__':unittest.main()