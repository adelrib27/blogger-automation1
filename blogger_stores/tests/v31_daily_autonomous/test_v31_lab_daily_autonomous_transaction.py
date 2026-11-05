"""Directed offline security tests for the V31 LAB daily autonomous transaction."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[2] / "src" / "v31_lab_daily_autonomous_transaction.py"
SPEC = importlib.util.spec_from_file_location("v31_lab_daily_autonomous_transaction", SRC)
TX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TX)


def call_git(*args):
    cp = subprocess.run(["git", *map(str, args)], stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, timeout=12, check=False)
    if cp.returncode:
        raise RuntimeError("Fixture Git command failed")
    return cp.stdout.decode().strip()


class DummyResponse:
    status = 200
    def __init__(self, content):
        self.content = json.dumps(content).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def read(self, n):
        return self.content[:n]


class TestDailyGuards(unittest.TestCase):
    def test_strong_etag_only(self):
        self.assertTrue(TX.strong_etag('"sTr0ng:12"'))
        for tag in (None, "", "W/\"weak\"", "unquoted", '"', '"sp ace"', '""'):
            self.assertFalse(TX.strong_etag(tag))

    def test_canonical_preserves_final_newline(self):
        value = TX.canonical({"c": "é", "b": [1, 2]})
        self.assertTrue(value.endswith(b"\n"))
        self.assertEqual(json.loads(value), {"c": "é", "b": [1, 2]})

    def test_wrong_repository_blocks(self):
        with patch.dict(os.environ, {"GITHUB_REPOSITORY":"other/repo"}, clear=True):
            with self.assertRaises(TX.Blocked): TX.check_environment()

    def test_rerun_blocks(self):
        base = {"GITHUB_REPOSITORY":TX.REPO, "GITHUB_REF":TX.REF,
                "GITHUB_EVENT_NAME":"workflow_dispatch", "GITHUB_RUN_ATTEMPT":"2"}
        with patch.dict(os.environ, base, clear=True):
            with self.assertRaises(TX.Blocked): TX.check_environment()

    def test_push_event_not_allowed(self):
        base = {"GITHUB_REPOSITORY":TX.REPO,"GITHUB_REF":TX.REF,
                "GITHUB_EVENT_NAME":"push","GITHUB_RUN_ATTEMPT":"1"}
        with patch.dict(os.environ, base, clear=True):
            with self.assertRaises(TX.Blocked): TX.check_environment()

    def test_wrong_origin_blocks(self):
        base = {"GITHUB_REPOSITORY":TX.REPO,"GITHUB_REF":TX.REF,
                "GITHUB_EVENT_NAME":"workflow_dispatch","GITHUB_RUN_ATTEMPT":"1",
                "V31_DAILY_ORIGIN":"UNKNOWN","V31_DAILY_APPROVAL":TX.APPROVAL}
        with patch.dict(os.environ, base, clear=True):
            with self.assertRaises(TX.Blocked): TX.check_environment()

    def test_right_env_passes(self):
        base = {"GITHUB_REPOSITORY":TX.REPO,"GITHUB_REF":TX.REF,
                "GITHUB_EVENT_NAME":"workflow_dispatch","GITHUB_RUN_ATTEMPT":"1",
                "V31_DAILY_ORIGIN":"MAIN_SCHEDULE_LAB_ONLY",
                "V31_DAILY_APPROVAL":TX.APPROVAL,"GITHUB_RUN_ID":"900",
                "GITHUB_WORKFLOW_REF":TX.REPO+"/.github/workflows/"
                   "v31_lab_daily_autonomous_dispatch.yml@"+TX.REF,
                "GITHUB_WORKSPACE":str(Path.cwd()),"GITHUB_ACTOR":"github-actions[bot]"}
        with patch.dict(os.environ, base, clear=True):
            TX.check_environment()

    def test_put_without_if_match_blocked_before_network(self):
        with self.assertRaises(TX.Blocked):
            TX.blogger_call("token", "PUT", payload={
                "kind":"blogger#page","blog":{"id":TX.BLOG},"id":TX.PAGE,
                "title":"LOJA","content":"HTML"}, etag="W/\"weak\"")

    def test_put_to_wrong_page_blocked(self):
        with self.assertRaises(TX.Blocked):
            TX.blogger_call("token", "PUT", payload={
                "kind":"blogger#page","blog":{"id":TX.BLOG},"id":"888",
                "title":"LOJA","content":"HTML"}, etag='"strong"')

    def test_get_uses_only_pinned_url(self):
        calls = []
        def fake_open(req, timeout):
            calls.append((req.full_url, req.get_method()))
            return DummyResponse({"id": TX.PAGE})
        with patch.object(TX.OPENER, "open", fake_open):
            value = TX.blogger_call("fake-token", "GET")
        self.assertEqual(value["id"], TX.PAGE)
        self.assertEqual(calls, [(TX.PAGE_API,"GET")])

    def test_live_inventory_required(self):
        page = {"id":TX.PAGE,"blog":{"id":TX.BLOG},"title":"LOJA",
                "url":TX.PAGE_URL,"etag":'"yes"',"content":"content",
                "updated":"2026-11-04T21:06:56-03:00"}
        with patch.object(TX, "list_pages", return_value=[]):
            with self.assertRaises(TX.Blocked): TX.require_live_page("fake",page)

    def test_live_inventory_pass(self):
        page = {"id":TX.PAGE,"blog":{"id":TX.BLOG},"title":"LOJA",
                "url":TX.PAGE_URL,"etag":'"yes"',"content":"content",
                "updated":"2026-11-04T21:06:56-03:00"}
        with patch.object(TX, "list_pages",return_value=[{"id":TX.PAGE}]):
            self.assertEqual(TX.require_live_page("fake",page), b"content")

    def test_wrong_blog_live_page_rejected(self):
        page = {"id":TX.PAGE,"blog":{"id":"111"},"title":"LOJA",
                "url":TX.PAGE_URL,"etag":'"yes"',"content":"content",
                "updated":"2026-11-04T21:06:56-03:00"}
        with patch.object(TX, "list_pages",return_value=[{"id":TX.PAGE}]):
            with self.assertRaises(TX.Blocked): TX.require_live_page("fake",page)


class TestGitCAS(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.original = Path.cwd()
        base = Path(self.root.name)
        self.remote = base / "remote.git"
        self.local = base / "local"
        call_git("init", "--bare", self.remote)
        call_git("clone", self.remote, self.local)
        call_git("-C",self.local,"checkout","-b",TX.BRANCH)
        for path, raw in ((TX.LEDGER,b'{"schema":1}\n'),
                          (TX.HISTORY,b'{"version":1}\n')):
            file = self.local/path
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_bytes(raw)
        call_git("-C",self.local,"add","--",TX.LEDGER,TX.HISTORY)
        call_git("-C",self.local,"-c","user.name=Lab Test",
                 "-c","user.email=lab-test@users.noreply.github.com",
                 "commit","-m","seed")
        call_git("-C",self.local,"push","origin","HEAD:"+TX.REF)
        self.head = call_git("-C",self.local,"rev-parse","HEAD")
        os.chdir(self.local)
        self.env = patch.dict(os.environ, {"GITHUB_SHA":self.head})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        os.chdir(self.original)
        self.root.cleanup()

    def test_exact_read_preserves_whitespace(self):
        l=TX.GitLease()
        self.assertEqual(l.read(TX.LEDGER), b'{"schema":1}\n')

    def test_one_file_git_plan_nonforced(self):
        l=TX.GitLease()
        candidate=b'{"schema":2}\n'
        after=l.commit_exact({TX.LEDGER:candidate},"V31 LAB sandbox plan")
        self.assertEqual(l.remote_head(),after)
        self.assertEqual(l.read(TX.LEDGER),candidate)
        self.assertEqual(l.read(TX.HISTORY),b'{"version":1}\n')

    def test_two_file_backup_claim_atomic(self):
        l=TX.GitLease()
        backup=f"blogger_stores/v31_lab/prewrite_backup/{'f'*64}/LOJA_ANTES_ROTACAO_DIARIA.html"
        html=b'  <article>approved original</article>\n'
        after=l.commit_exact({TX.LEDGER:b'{"schema":2}\n',backup:html},
                             "V31 LAB sandbox atomic claim backup")
        self.assertEqual(l.remote_head(),after)
        self.assertEqual(l.read(backup),html)
        self.assertEqual(l.read(TX.HISTORY),b'{"version":1}\n')

    def test_two_file_finalization_atomic(self):
        l=TX.GitLease()
        after=l.commit_exact({TX.LEDGER:b'{"schema":2}\n',
                              TX.HISTORY:b'{"version":2}\n'},
                             "V31 LAB sandbox atomic persistence")
        self.assertEqual(l.remote_head(),after)
        self.assertEqual(l.read(TX.HISTORY),b'{"version":2}\n')

    def test_unexpected_path_fails_closed(self):
        l=TX.GitLease()
        with self.assertRaises(TX.Blocked):
            l.commit_exact({"README.md":b"wrong"}, "forbidden")
        self.assertEqual(l.remote_head(),self.head)

    def test_backup_path_traversal_fails_closed(self):
        l=TX.GitLease()
        with self.assertRaises(TX.Blocked):
            l.commit_exact({
                TX.LEDGER:b'{"schema":2}\n',
                "blogger_stores/v31_lab/prewrite_backup/../wrong.html":b"wrong"
            },"forbidden")
        self.assertEqual(l.remote_head(),self.head)

    def test_concurrent_head_change_blocks_without_commit(self):
        l=TX.GitLease()
        # Simulate another writer by advancing the same branch through a temp clone.
        other=Path(self.root.name)/"other"
        call_git("clone","--branch",TX.BRANCH,self.remote,other)
        (other/"x.txt").write_text("parallel",encoding="utf-8")
        call_git("-C",other,"add","x.txt")
        call_git("-C",other,"-c","user.name=Lab Test",
                 "-c","user.email=lab-test@users.noreply.github.com",
                 "commit","-m","parallel")
        call_git("-C",other,"push","origin","HEAD:"+TX.REF)
        with self.assertRaises(TX.Blocked):
            l.commit_exact({TX.LEDGER:b'{"schema":2}\n'},"forbidden stale")
        self.assertEqual(call_git("rev-parse","HEAD"),self.head)


if __name__=="__main__":
    unittest.main()
