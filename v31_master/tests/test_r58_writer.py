#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import r58_store_policy as gate
import r58_rotate_store as writer
from test_r58_store_policy import make_html, state_for

def page(content):
    return {"id":writer.PAGE_ID, "blog":{"id":writer.BLOG_ID},
            "url":writer.PAGE_URL,"title":"LOJA",
            "status":None,"published":"2026-11-06T17:54:00-03:00",
            "updated":"2026-11-06T17:54:00-03:00", "content":content}

class TestWriter(unittest.TestCase):
    def fixture(self,old,new):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d=Path(tmp.name)
        candidate=d/"candidate.html";candidate.write_text(new,encoding="utf-8")
        state=d/"state.json";state.write_text(json.dumps(state_for(old)),encoding="utf-8")
        out=d/"output";out.mkdir()
        return candidate,state,out
    def test_no_change_never_put(self):
        old=make_html()
        candidate,state,out=self.fixture(old,old)
        with patch.object(writer,"oauth_token",return_value="test-only"),patch.object(writer,"api_page",return_value=page(old)) as api:
            self.assertEqual(writer.run(candidate_path=candidate,state_path=state,dry_run=True,out_dir=out),0)
            self.assertEqual(api.call_count,1)
            self.assertEqual(api.call_args.args,("test-only",))
    def test_dryrun_rotation_never_put(self):
        old,new=make_html(),make_html(20)
        candidate,state,out=self.fixture(old,new)
        with patch.object(writer,"oauth_token",return_value="test-only"),patch.object(writer,"api_page",return_value=page(old)) as api:
            self.assertEqual(writer.run(candidate_path=candidate,state_path=state,dry_run=True,out_dir=out),0)
            self.assertEqual(api.call_count,1)
            self.assertFalse(any(out.iterdir()))
    def test_live_denied_by_state_no_put(self):
        old,new=make_html(),make_html(20)
        candidate,state,out=self.fixture(old,new)
        with patch.object(writer,"oauth_token",return_value="test-only"),patch.object(writer,"api_page",return_value=page(old)) as api:
            with self.assertRaises(writer.WriterError):
                writer.run(candidate_path=candidate,state_path=state,dry_run=False,out_dir=out)
            self.assertEqual(api.call_count,1)
    def test_expected_page_no_status_but_published(self):
        self.assertEqual(writer.validate_page(page(make_html())),make_html())
    def test_no_status_and_no_published_is_rejected(self):
        p=page(make_html());p.pop("published")
        with self.assertRaises(writer.WriterError):writer.validate_page(p)
    def test_other_blog_id_rejected(self):
        p=page(make_html());p["blog"]["id"]="8476663092477971560"
        with self.assertRaises(writer.WriterError):writer.validate_page(p)
    def test_live_marks_started_before_put_and_does_not_retry(self):
        old,new=make_html(),make_html(20)
        candidate,state,out=self.fixture(old,new)
        s=json.loads(state.read_text(encoding="utf8"))
        s["allow_auto_write"]=True;s["rotation_enabled"]=True
        state.write_text(json.dumps(s),encoding="utf8")
        def api(token,method="GET",content=None):
            if method=="PUT":
                raise writer.WriterError("SIMULATED_TIMEOUT_UNCERTAIN")
            return page(old)
        with patch.object(writer,"oauth_token",return_value="test-only"),patch.object(writer,"api_page",side_effect=api),patch.dict(os.environ,{"R58_LIVE_CONFIRM":writer.CONFIRM}):
            with self.assertRaises(writer.WriterError):
                writer.run(candidate_path=candidate,state_path=state,dry_run=False,out_dir=out)
        self.assertTrue((out/"R58_WRITE_STARTED_NO_RETRY").exists())
        self.assertTrue((out/"BACKUP_LOJA_R58_PRE_WRITE.json").exists())
        self.assertFalse((out/"R58_ROTATION_STATE_NEXT.json").exists())

if __name__=="__main__":
    unittest.main(verbosity=2)
