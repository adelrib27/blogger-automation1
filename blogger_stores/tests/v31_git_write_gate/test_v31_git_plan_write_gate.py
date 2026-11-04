"""Local isolated bare-Git integration tests. NEVER push to user GitHub."""
from __future__ import annotations
import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'v31_core'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v31_transaction'))
from test_v31_multicycle_cas_contract import objects,selection,html,encoded
from v31_multicycle_cas_contract import prepare_reservation,git_blob_sha,REPO,BRANCH
from v31_git_plan_write_gate import (LEDGER,HISTORY,LAB_URL,SANDBOX_BRANCH,
    ReservationWriteBlocked,validate_plan_bytes,commit_plan_on_checkout,
    reserve_from_isolated_clone)


def run(root,*args,success=True):
    r=subprocess.run(['git',*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if success and r.returncode:
        raise AssertionError('Git command failed: '+str(args))
    return r.stdout.strip().decode('utf-8','replace')

class TestPlanWriteGate(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(prefix='v31-safe-write-test-')
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.bare=self.root/'sandbox-remote.git'
        run(self.root,'init','--bare',str(self.bare))
        self.seed=self.root/'seed';self.seed.mkdir()
        run(self.seed,'init','-b',SANDBOX_BRANCH)
        run(self.seed,'config','user.name','Safe')
        run(self.seed,'config','user.email','safe@example.invalid')
        old_state,old_hist,profile=objects()
        self.before=html([str(60000+i) for i in range(16)])
        self.after=html([str(70000+i) for i in range(16)])
        old_state['operations'][-1]['candidateSha']=sha256(self.before).hexdigest()
        self.old=encoded(old_state);self.history=encoded(old_hist)
        for name,data in ((LEDGER,self.old),(HISTORY,self.history)):
            file=self.seed/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
        run(self.seed,'add','--',LEDGER,HISTORY)
        run(self.seed,'commit','-m','Seed SAFE')
        run(self.seed,'remote','add','origin',str(self.bare))
        run(self.seed,'push','origin','HEAD:refs/heads/'+SANDBOX_BRANCH)
        self.parent=run(self.seed,'rev-parse','HEAD')
        proposal=prepare_reservation(repository=REPO,branch=BRANCH,profile=profile,
            ledger_bytes=self.old,history_bytes=self.history,selection_bytes=encoded(selection()),
            blogger_html_bytes=self.before,candidate_html_bytes=self.after,
            expected_head=self.parent,observed_head=self.parent,
            expected_ledger_blob=git_blob_sha(self.old),
            expected_history_blob=git_blob_sha(self.history))
        self.proposed=proposal['proposed_ledger_bytes'];self.oid=proposal['operation_id']
        self.args=dict(remote=str(self.bare),branch=SANDBOX_BRANCH,expected_head=self.parent,
            expected_ledger_blob=git_blob_sha(self.old),expected_history_blob=git_blob_sha(self.history),
            proposed_ledger_bytes=self.proposed,operation_id=self.oid,
            expected_plan_sha256=sha256(self.proposed).hexdigest(),
            expected_selection_sha=proposal['selection_sha256'],
            expected_original_sha=proposal['original_html_sha256'],
            expected_candidate_sha=proposal['candidate_html_sha256'],
            mode='SANDBOX',sandbox_bare=self.bare)

    def clone(self,folder):
        dest=self.root/folder
        run(self.root,'clone','-b',SANDBOX_BRANCH,str(self.bare),str(dest))
        return dest
    def submitted(self,**kwargs):
        p=dict(self.args);p.update(kwargs)
        return reserve_from_isolated_clone(**p)
    def blocked(self,**kwargs):
        with self.assertRaises((ReservationWriteBlocked,ValueError,KeyError)):
            self.submitted(**kwargs)
    def remote_sha(self):
        return run(self.bare,'rev-parse','refs/heads/'+SANDBOX_BRANCH)
    def test_valid_plan_reserves_single_ledger_commit(self):
        output=self.submitted()
        self.assertEqual(output['status'],'V31_LAB_GIT_PLAN_RESERVATION_COMMITTED')
        self.assertEqual(output['expected_parent_head'],self.parent)
        self.assertNotEqual(self.remote_sha(),self.parent)
        self.assertEqual(self.remote_sha(),output['reserved_commit_head'])
        self.assertTrue(output['history_unchanged'])
        self.assertFalse(output['live_git_write'])
        self.assertFalse(output['blogger_put_allowed'])
        self.assertFalse(output['cron_allowed'])
        self.assertEqual(run(self.bare,'show','refs/heads/'+SANDBOX_BRANCH+':'+LEDGER),self.proposed.decode().strip())
        self.assertEqual(run(self.bare,'show','refs/heads/'+SANDBOX_BRANCH+':'+HISTORY),self.history.decode().strip())
        files=run(self.bare,'diff-tree','--no-commit-id','--name-only','-r',self.remote_sha())
        self.assertEqual(files,LEDGER)
        self.assertEqual(run(self.bare,'rev-parse',self.remote_sha()+'^'),self.parent)
    def test_old_checkout_stale_blocks(self): self.blocked(expected_head='f'*40)
    def test_blob_mismatch_ledger_blocks(self): self.blocked(expected_ledger_blob='a'*40)
    def test_blob_mismatch_history_blocks(self): self.blocked(expected_history_blob='a'*40)
    def test_wrong_pinned_proposal_blocks(self):self.blocked(expected_plan_sha256='f'*64)
    def test_wrong_pinned_selection_blocks(self):self.blocked(expected_selection_sha='f'*64)
    def test_wrong_pinned_candidate_blocks(self):self.blocked(expected_candidate_sha='f'*64)
    def test_branch_mismatch_blocks(self): self.blocked(branch='main')
    def test_nonbare_remote_blocks(self): self.blocked(sandbox_bare=self.seed,remote=str(self.seed))
    def test_wrong_sandbox_root_blocks(self): self.blocked(sandbox_bare=self.seed)
    def test_live_gate_forbidden_without_explicit_authorization(self):
        with self.assertRaises(ReservationWriteBlocked):
            self.submitted(mode='LAB_REAL',remote=LAB_URL,branch=BRANCH)
    def test_lab_approval_text_does_not_bypass_github_environment(self):
        with self.assertRaises(ReservationWriteBlocked):
            self.submitted(mode='LAB_REAL',remote=LAB_URL,branch=BRANCH,
                 approval='RESERVAR_SOMENTE_GIT_LAB:'+self.oid)
    def test_no_auto_replay_second_attempt(self):
        self.submitted()
        self.blocked()
    def test_duplicate_writers_from_same_head_only_one_wins(self):
        a=self.clone('writer_a');b=self.clone('writer_b')
        first=commit_plan_on_checkout(checkout=a,**self.args)
        self.assertNotEqual(self.parent,first['reserved_commit_head'])
        with self.assertRaises(ReservationWriteBlocked):
            commit_plan_on_checkout(checkout=b,**self.args)
        self.assertEqual(first['reserved_commit_head'],self.remote_sha())
    def test_dirty_clone_refuses_before_any_commit(self):
        c=self.clone('dirty');(c/'other.txt').write_text('dirty')
        with self.assertRaises(ReservationWriteBlocked):commit_plan_on_checkout(checkout=c,**self.args)
        self.assertEqual(self.parent,self.remote_sha())
    def test_origin_drift_refuses(self):
        c=self.clone('wrong_origin');run(c,'remote','set-url','origin',str(self.seed))
        with self.assertRaises(ReservationWriteBlocked):commit_plan_on_checkout(checkout=c,**self.args)
        self.assertEqual(self.parent,self.remote_sha())
    def test_missing_ledger_refuses(self):
        c=self.clone('missing_ledger');(c/LEDGER).unlink()
        with self.assertRaises(ReservationWriteBlocked):commit_plan_on_checkout(checkout=c,**self.args)
        self.assertEqual(self.parent,self.remote_sha())
    def test_history_file_modified_refuses(self):
        c=self.clone('history_dirty');(c/HISTORY).write_text('{}')
        with self.assertRaises(ReservationWriteBlocked):commit_plan_on_checkout(checkout=c,**self.args)
        self.assertEqual(self.parent,self.remote_sha())
    def test_plan_tampering_before_list_refused(self):
        data=json.loads(self.proposed);data['operations'][0]['candidateSha']='e'*64
        self.blocked(proposed_ledger_bytes=encoded(data))
    def test_plan_tampering_operation_refused(self):
        data=json.loads(self.proposed);data['operations'][-1]['operationId']='a'*64
        self.blocked(proposed_ledger_bytes=encoded(data))
    def test_plan_tampering_status_refused(self):
        data=json.loads(self.proposed);data['operations'][-1]['status']='PERSISTED'
        self.blocked(proposed_ledger_bytes=encoded(data))
    def test_plan_tampering_original_sha_refused(self):
        data=json.loads(self.proposed);data['operations'][-1]['originalSha']='e'*64
        self.blocked(proposed_ledger_bytes=encoded(data))
    def test_plan_tampering_blog_refused(self):
        data=json.loads(self.proposed);data['blogId']='123'
        self.blocked(proposed_ledger_bytes=encoded(data))
    def test_empty_plan_refused(self): self.blocked(proposed_ledger_bytes=self.old)
    def test_invalid_expected_parent_refused(self):self.blocked(expected_head='invalid')
    def test_invalid_operation_id_refused(self):self.blocked(operation_id='e'*64)
    def test_second_concurrent_plan_refused(self):
        data=json.loads(self.proposed)
        data['operations'].append(copy.deepcopy(data['operations'][-1]))
        self.blocked(proposed_ledger_bytes=encoded(data))
    def test_result_not_allowing_blogger_write(self):
        report=self.submitted()
        self.assertFalse(report['blogger_put_allowed'])
        self.assertFalse(report['cron_allowed'])

if __name__=='__main__': unittest.main()
