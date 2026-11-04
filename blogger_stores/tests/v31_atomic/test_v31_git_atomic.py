"""Offline Git atomicity/fail-closed race tests, no GitHub access."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from v31_lab_atomic_finalize import check_destinations, ReconcileError

def git(*args,cwd):
    return subprocess.run(['git',*args],cwd=cwd,capture_output=True,text=True)

def check(*args,cwd):
    p=git(*args,cwd=cwd)
    if p.returncode:raise AssertionError(f"git command failed ({args[0]}): {p.stderr[-300:]}")
    return p.stdout.strip()

class GitAtomicTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.remote=self.root/'remote.git'
        check('init','--bare',str(self.remote),cwd=self.root)
        self.a=self.root/'agentA'
        check('clone',str(self.remote),str(self.a),cwd=self.root)
        check('config','user.name','V31 LAB TEST',cwd=self.a)
        check('config','user.email','test@example.invalid',cwd=self.a)
        (self.a/'base').write_text('base')
        check('add','base',cwd=self.a)
        check('commit','-m','base',cwd=self.a)
        check('branch','-M','lab',cwd=self.a)
        check('push','-u','origin','lab',cwd=self.a)
        self.b=self.root/'agentB'
        check('clone','--branch','lab',str(self.remote),str(self.b),cwd=self.root)
        check('config','user.name','V31 OTHER TEST',cwd=self.b)
        check('config','user.email','other@example.invalid',cwd=self.b)
    def test_atomic_pair_same_commit(self):
        (self.a/'ledger.json').write_text('{"status":"PERSISTED"}')
        (self.a/'history.json').write_text('{"runs":2}')
        check('add','ledger.json','history.json',cwd=self.a)
        self.assertEqual(check('diff','--cached','--name-only',cwd=self.a).splitlines(),['history.json','ledger.json'])
        check('commit','-m','atomic ledger+history',cwd=self.a)
        check('push','origin','HEAD:refs/heads/lab',cwd=self.a)
        files=check('--git-dir',str(self.remote),'ls-tree','-r','--name-only','lab',cwd=self.root).splitlines()
        self.assertIn('ledger.json',files);self.assertIn('history.json',files)
        paths=check('--git-dir',str(self.remote),'show','--format=','--name-only','lab',cwd=self.root).splitlines()
        self.assertEqual(paths,['history.json','ledger.json'])
    def test_concurrent_update_blocks_non_ff(self):
        (self.a/'ledger.json').write_text('{"status":"PERSISTED"}')
        (self.a/'history.json').write_text('{"runs":2}')
        check('add','ledger.json','history.json',cwd=self.a)
        check('commit','-m','one transaction',cwd=self.a)
        (self.b/'other.txt').write_text('parallel change')
        check('add','other.txt',cwd=self.b)
        check('commit','-m','parallel user',cwd=self.b)
        check('push','origin','HEAD:refs/heads/lab',cwd=self.b)
        denied=git('push','origin','HEAD:refs/heads/lab',cwd=self.a)
        self.assertNotEqual(denied.returncode,0)
        files=check('--git-dir',str(self.remote),'ls-tree','-r','--name-only','lab',cwd=self.root).splitlines()
        self.assertNotIn('ledger.json',files);self.assertNotIn('history.json',files)
        self.assertIn('other.txt',files)
    def test_preexisting_canonical_pair_blocks(self):
        a=self.a/'ledger.json';b=self.a/'history.json'
        a.write_text('{}');b.write_text('{}')
        with self.assertRaises(ReconcileError):check_destinations(a,b)
    def test_single_existing_canonical_file_blocks(self):
        a=self.a/'ledger.json';b=self.a/'history.json'
        a.write_text('{}')
        with self.assertRaises(ReconcileError):check_destinations(a,b)

if __name__=='__main__':unittest.main()