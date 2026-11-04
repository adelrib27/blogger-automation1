"""Provas offline de retomada de um segundo ciclo; sem rede nem PUT."""
import copy
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v31_rotation_ledger import (stage, mark_readback, mark_public_verified,
                                 history_commit, LedgerError, operation_id)
from v31_second_resume_safe import (decide_resume, validate_persisted_pair,
                                    ResumeBlocked)

BID='4739187376492839837'
PID='2446067640331732447'
FIRST='46ef8a293875720f036d90430d1e57c862277b42bde966fbf34b15f9d2cb6c0c'
SECOND='aea7191e1e4ea77581b33591e0e940f6bd582114c90ea2e457a7173faf3664b7'
ORIGINAL='6f3810a364fe2114865b96fa5f118c10495bfe39943406624710ac9aaf25f450'
CANDIDATE='d33070c001281ed795489a032a504accfcab2b593010c1a9e8cf5bb86b8109b8'

# Simula os metadados operacionais da primeira rotacao real, ja persistida.
# Nao se trata de prova publica de segunda publicacao.
def fixture():
    firstitems=[{'itemId':str(20000000001+i),'category':['Decoração','Organização','Cozinha','Quarto'][i//4]} for i in range(16)]
    led={'schema':1,'blogId':BID,'pageId':PID,'operations':[{'operationId':operation_id(FIRST,BID,PID),
        'selectionSha':FIRST,'originalSha':'a'*64,'candidateSha':ORIGINAL,'status':'PERSISTED'}]}
    history={'version':1,'blogId':BID,'runs':[
        {'source':'seed_from_current_blogger_store','pageId':PID,'items':[]},
        {'source':'blogger_published','pageId':PID,'operationId':operation_id(FIRST,BID,PID),
         'selectionSha':FIRST,'items':firstitems}]}
    return led,history

class SecondRecoverySafe(unittest.TestCase):
    def setUp(self):
        self.baseline,self.history=fixture()
        self.plan=stage(self.baseline,SECOND,ORIGINAL,CANDIDATE)
    def decide(self,state=None,history=None,sha=SECOND,observed=ORIGINAL,blog=BID,page=PID):
        return decide_resume(state=self.plan if state is None else state,
            history=self.history if history is None else history,
            blog_id=blog,page_id=page,selection_sha=sha,observed_html_sha=observed)
    def blocked(self,**kwargs):
        with self.assertRaises((ResumeBlocked,LedgerError)):
            self.decide(**kwargs)
    def test_first_persisted_pair_is_valid(self):
        validate_persisted_pair(self.baseline,self.history)
    def test_second_plan_is_a_separate_operation(self):
        self.assertEqual(len(self.plan['operations']),2)
        self.assertEqual(self.plan['operations'][0]['status'],'PERSISTED')
        self.assertEqual(self.plan['operations'][1]['status'],'PLAN')
    def test_crash_before_put_is_not_automatic_publish(self):
        x=self.decide();self.assertEqual(x['decision'],'PLAN_ONLY_REQUIRES_EXPLICIT_WRITE_GATE')
        self.assertFalse(x['blogger_put_allowed']);self.assertFalse(x['git_state_write_allowed'])
    def test_crash_after_put_before_ledger_update_skips_reput(self):
        x=self.decide(observed=CANDIDATE)
        self.assertEqual(x['decision'],'PUT_MAY_HAVE_SUCCEEDED_SKIP_RETRY')
        self.assertFalse(x['blogger_put_allowed'])
    def test_unknown_page_checksum_blocks(self):self.blocked(observed='9'*64)
    def test_bad_or_foreign_blog_blocks(self):self.blocked(blog='1234')
    def test_bad_or_foreign_page_blocks(self):self.blocked(page='1234')
    def test_unregistered_selection_blocks(self):self.blocked(sha='f'*64)
    def test_malformed_hash_blocks(self):self.blocked(observed='invalid')
    def test_replay_stage_is_idempotent(self):
        plan_copy=copy.deepcopy(self.plan)
        self.assertEqual(stage(self.plan,SECOND,ORIGINAL,CANDIDATE),self.plan)
        self.assertEqual(self.plan,plan_copy)
    def test_third_selection_while_second_is_pending_blocks(self):
        with self.assertRaises(LedgerError):stage(self.plan,'f'*64,ORIGINAL,'e'*64)
    def test_no_commit_before_exact_public_proof(self):
        with self.assertRaises(LedgerError):
            history_commit(self.plan,SECOND,self.history,
                published_items=self.new_items(),published_at='2026-11-04T12:00:00-03:00')
    def test_readback_wrong_checksum_blocks(self):
        with self.assertRaises(LedgerError):mark_readback(self.plan,SECOND,observed_candidate_sha='d'*64)
    def test_readback_recovers_without_another_put(self):
        state=mark_readback(self.plan,SECOND,observed_candidate_sha=CANDIDATE)
        self.assertEqual(self.decide(state=state,observed=CANDIDATE)['decision'],'VERIFY_PUBLIC_ONLY_NO_PUT')
    def test_pending_with_original_page_blocks(self):
        state=mark_readback(self.plan,SECOND,observed_candidate_sha=CANDIDATE)
        self.blocked(state=state,observed=ORIGINAL)
    def test_429_or_throttled_public_proof_blocks(self):
        state=mark_readback(self.plan,SECOND,observed_candidate_sha=CANDIDATE)
        with self.assertRaises(LedgerError):
            mark_public_verified(state,SECOND,proof={'status':'PUBLIC_PENDING_THROTTLED'})
    @staticmethod
    def new_items():
        cats=['Decoração','Organização','Cozinha','Quarto']
        return [{'itemId':str(99000000001+i),'category':cats[i//4]} for i in range(16)]
    def proven(self):
        state=mark_readback(self.plan,SECOND,observed_candidate_sha=CANDIDATE)
        proof={'status':'PUBLIC_EXACT_PASS','selection_sha256':SECOND,
               'cards':16,'images':16,'links':16,'public_http':200}
        return mark_public_verified(state,SECOND,proof=proof)
    def test_exact_proof_leads_only_to_atomic_pair_gate(self):
        x=self.decide(state=self.proven(),observed=CANDIDATE)
        self.assertEqual(x['decision'],'PREPARE_ATOMIC_PAIR_AWAIT_CAS')
        self.assertFalse(x['git_state_write_allowed'])
    def test_history_commit_second_is_idempotent(self):
        items=self.new_items()
        s,h=history_commit(self.proven(),SECOND,self.history,
            published_items=items,published_at='2026-11-04T12:00:00-03:00')
        self.assertEqual(len(s['operations']),2)
        self.assertEqual(len(h['runs']),3)
        s2,h2=history_commit(s,SECOND,h,published_items=items,
                             published_at='2026-11-04T12:00:00-03:00')
        self.assertEqual((s,h),(s2,h2))
        self.assertEqual(self.decide(state=s,history=h,observed=CANDIDATE)['decision'],
                         'ALREADY_PERSISTED_NO_ACTION')
    def test_persisted_page_rollback_blocks(self):
        s,h=history_commit(self.proven(),SECOND,self.history,
            published_items=self.new_items(),published_at='2026-11-04T12:00:00-03:00')
        self.blocked(state=s,history=h,observed=ORIGINAL)
    def test_different_candidate_same_operation_blocks(self):
        with self.assertRaises(LedgerError):stage(self.plan,SECOND,ORIGINAL,'e'*64)
    def test_inconsistent_history_item_blocks(self):
        bad=copy.deepcopy(self.history);bad['runs'][1]['items'][0]['itemId']='bad'
        self.blocked(history=bad)
    def test_tampered_history_identity_blocks(self):
        bad=copy.deepcopy(self.history);bad['runs'][1]['selectionSha']='f'*64
        self.blocked(history=bad)
    def test_history_written_before_public_proof_blocks(self):
        bad=copy.deepcopy(self.history)
        bad['runs'].append({'source':'blogger_published','pageId':PID,
                           'operationId':operation_id(SECOND,BID,PID),'selectionSha':SECOND,'items':self.new_items()})
        self.blocked(history=bad)
    def test_duplicate_history_after_second_commit_blocks(self):
        s,h=history_commit(self.proven(),SECOND,self.history,
            published_items=self.new_items(),published_at='2026-11-04T12:00:00-03:00')
        bad=copy.deepcopy(h);bad['runs'].append(copy.deepcopy(h['runs'][-1]))
        self.blocked(state=s,history=bad,observed=CANDIDATE)
    def test_persisted_history_mismatch_blocks(self):
        s,h=history_commit(self.proven(),SECOND,self.history,
            published_items=self.new_items(),published_at='2026-11-04T12:00:00-03:00')
        bad=copy.deepcopy(h);bad['runs'][-1]['operationId']='a'*64
        self.blocked(state=s,history=bad,observed=CANDIDATE)
    def test_no_plan_means_no_new_put(self):
        self.blocked(state=self.baseline)

if __name__=='__main__':unittest.main()