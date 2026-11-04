"""SAFE: Git read-only executor tests, sandbox bare race, no Blogger/GitHub writes."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'v31_core'))
sys.path.insert(0,str(ROOT/'tests/v31_transaction'))
from test_v31_multicycle_cas_contract import objects, selection, html, encoded
from v31_multicycle_cas_contract import prepare_reservation, REPO, BRANCH, git_blob_sha
from v31_git_reservation_executor_safe import (
    LEDGER,HISTORY,PROFILE,SafeExecutionBlocked,
    read_only_reservation_preflight,sandbox_race,git_read,write_report,
)
from hashlib import sha256

def git(cwd,*cmd):
    r=subprocess.run(['git',*cmd],cwd=cwd,capture_output=True,check=False)
    if r.returncode:raise AssertionError((cmd,r.stderr.decode(errors='replace')))
    return r.stdout.decode().strip()

class TestRealGitReadOnly(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name)/'checkout'
        self.repo.mkdir()
        git(self.repo,'init','-b','test')
        git(self.repo,'config','user.name','Safe')
        git(self.repo,'config','user.email','safe@example.invalid')
        git(self.repo,'remote','add','origin','https://github.com/adelrib27/blogger-automation1.git')
        ledger,history,profile=objects()
        self.state=encoded(ledger)
        self.history=encoded(history)
        for name,data in ((LEDGER,self.state),(HISTORY,self.history),(PROFILE,encoded(profile))):
            path=self.repo/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
        git(self.repo,'add','.')
        git(self.repo,'commit','-m','fake pinned baseline')
        self.head=git(self.repo,'rev-parse','HEAD')
        self.selection=encoded(selection())
        self.before=html([str(60000+i) for i in range(16)])
        self.after=html([str(70000+i) for i in range(16)])
        for name,contents in (('selection.json',self.selection),('original.html',self.before),('candidate.html',self.after)):
            (Path(self.temp.name)/name).write_bytes(contents)
        self.args=dict(repo_root=self.repo,selection=Path(self.temp.name)/'selection.json',
            original=Path(self.temp.name)/'original.html',candidate=Path(self.temp.name)/'candidate.html',
            expected_selection_sha=sha256(self.selection).hexdigest(),
            expected_original_sha=sha256(self.before).hexdigest(),
            expected_candidate_sha=sha256(self.after).hexdigest(),
            remote_reader=lambda _: self.head)
    def test_read_only_pinned_git_baseline(self):
        report=read_only_reservation_preflight(**self.args)
        self.assertEqual(report['status'],'V31_LAB_GIT_REMOTE_READ_ONLY_PREFLIGHT_PASS')
        self.assertEqual(report['head'],self.head)
        self.assertEqual(report['product_count'],16)
        self.assertEqual(report['baseline_ledger_blob'],git_blob_sha(self.state))
        self.assertEqual(report['baseline_history_blob'],git_blob_sha(self.history))
        self.assertFalse(report['blogger_put_allowed'])
        self.assertFalse(report['git_remote_write_allowed'])
        self.assertFalse(report['blogger_readback_live'])
        self.assertEqual(json.loads(self.state)['operations'][0]['status'],'PERSISTED')
    def test_remote_moved_blocks(self):
        a=dict(self.args,remote_reader=lambda _: 'f'*40)
        with self.assertRaises(SafeExecutionBlocked):read_only_reservation_preflight(**a)
    def test_remote_moved_during_computation_blocks(self):
        calls=iter([self.head, 'f'*40])
        with self.assertRaises(SafeExecutionBlocked):
            read_only_reservation_preflight(**dict(self.args,remote_reader=lambda _: next(calls)))
    def test_origin_not_github_blocks(self):
        git(self.repo,'remote','set-url','origin','https://github.com/other/repo.git')
        with self.assertRaises(SafeExecutionBlocked):read_only_reservation_preflight(**self.args)
    def test_origin_embedded_token_blocks(self):
        git(self.repo,'remote','set-url','origin','https://token@github.com/adelrib27/blogger-automation1.git')
        with self.assertRaises(SafeExecutionBlocked):read_only_reservation_preflight(**self.args)
    def test_dirty_canonical_file_blocks(self):
        with (self.repo/HISTORY).open('ab') as f:f.write(b' ')
        with self.assertRaises(SafeExecutionBlocked):read_only_reservation_preflight(**self.args)
    def test_wrong_hash_blocks(self):
        with self.assertRaises(SafeExecutionBlocked):
            read_only_reservation_preflight(**dict(self.args,expected_candidate_sha='a'*64))
    def test_selection_change_blocks(self):
        self.args['selection'].write_bytes(self.selection+b' ')
        with self.assertRaises(SafeExecutionBlocked):read_only_reservation_preflight(**self.args)
    def test_missing_candidate_blocks(self):
        self.args['candidate'].unlink()
        with self.assertRaises(SafeExecutionBlocked):read_only_reservation_preflight(**self.args)
    def test_report_outside_root_only_exclusive_create(self):
        data=read_only_reservation_preflight(**self.args)
        dest=Path(self.temp.name)/'report.json'
        write_report(data,dest,self.repo)
        self.assertFalse(json.loads(dest.read_text())['git_remote_write_allowed'])
        with self.assertRaises(FileExistsError):write_report(data,dest,self.repo)
        with self.assertRaises(SafeExecutionBlocked):write_report(data,self.repo/'report.json',self.repo)
    def test_git_read_only_guard_blocks_git_push(self):
        with self.assertRaises(SafeExecutionBlocked):git_read(self.repo,'push','origin','main')
    def test_git_read_only_guard_blocks_git_commit(self):
        with self.assertRaises(SafeExecutionBlocked):git_read(self.repo,'commit','--allow-empty')
    def test_isolated_sandbox_race_allows_only_one_writer(self):
        ledger,history,profile=objects()
        proposal=prepare_reservation(repository=REPO,branch=BRANCH,profile=profile,
            ledger_bytes=encoded(ledger),history_bytes=encoded(history),
            selection_bytes=self.selection,blogger_html_bytes=self.before,
            candidate_html_bytes=self.after,expected_head=self.head,observed_head=self.head,
            expected_ledger_blob=git_blob_sha(encoded(ledger)),
            expected_history_blob=git_blob_sha(encoded(history)))
        result=sandbox_race(parent_ledger=encoded(ledger),parent_history=encoded(history),
                            proposed_ledger=proposal['proposed_ledger_bytes'])
        self.assertEqual(result['status'],'V31_SANDBOX_GIT_NONFORCE_RACE_PASS')
        self.assertTrue(result['writer_a_push_accepted'])
        self.assertTrue(result['writer_b_conflict_rejected'])
        self.assertFalse(result['github_write'])
        self.assertFalse(result['blogger_write'])
    def test_sandbox_rejects_non_plan(self):
        with self.assertRaises(SafeExecutionBlocked):
            sandbox_race(parent_ledger=self.state,parent_history=self.history,proposed_ledger=self.state)

if __name__=='__main__':unittest.main()
