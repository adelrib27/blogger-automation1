"""C151: durable sanitized read-only pilot receipt, no network or mutation."""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31 import pilot_homologation as m

FILE="v31_pilot_readonly_report.json"
ROOT=Path(__file__).resolve().parents[2]

class DurablePilotReceiptTests(unittest.TestCase):
    def fixture(self, status="READ_ONLY_SOURCES_CONFIRMED_NOT_DRAFT_AUTHORIZED"):
        return {"mode":"UNIVERSAL_REAL_READONLY_CHECK","status":status,
                "reports":[{"site_key":"wordpress_radartechbr","campaign":"radarwp",
                            "primary_candidate_sample":[{"product_key":"shopee:123:456",
                                                         "title":"Produto de teste",
                                                         "cached_for_exact_campaign":False,
                                                         "eligible_for_draft_write":False}]}],
                "cms_writes":0,"d1_writes":0,"r2_writes":0,
                "affiliate_mutations":0,"automatic_live_authorized":False}

    def test_receipt_fixed_filename_contains_no_tokens(self):
        output=io.StringIO()
        report=self.fixture()
        with patch.object(m,"plan",return_value=report), \
             patch.object(sys,"argv",["pilot","--report-json",FILE]), \
             patch.object(Path,"write_text",return_value=100) as write, \
             contextlib.redirect_stdout(output):
            code=m.main()
        self.assertEqual(code,0)
        self.assertEqual(write.call_count,1)
        obj=json.loads(write.call_args.args[0].name and write.call_args.args[1])
        self.assertEqual(obj["reports"][0]["primary_candidate_sample"][0]["product_key"],"shopee:123:456")
        self.assertFalse(obj["automatic_live_authorized"])
        self.assertEqual(obj["cms_writes"],0)
        self.assertNotIn("password",output.getvalue())

    def test_rejects_arbitrary_path_traversal(self):
        with patch.object(sys,"argv",["pilot","--report-json","../../private"]):
            with contextlib.redirect_stderr(io.StringIO()), \
                 self.assertRaises(SystemExit) as exc:
                m.main()
        self.assertEqual(exc.exception.code,2)

    def test_artifact_persistence_failure_is_non_success(self):
        with patch.object(m,"plan",return_value=self.fixture()), \
             patch.object(sys,"argv",["pilot","--report-json",FILE]), \
             patch.object(Path,"write_text",side_effect=OSError("do not expose path")), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            code=m.main()
        self.assertEqual(code,4)
        self.assertIn("V31_PILOT_REPORT_PERSISTENCE_FAILED_CLOSED",output.getvalue())
        self.assertNotIn("do not expose path",output.getvalue())

    def test_remote_fail_closed_report_is_still_durable(self):
        with patch.object(m,"live_readonly",
                          return_value=self.fixture("READ_ONLY_SOURCE_CHECK_INCOMPLETE")), \
             patch.object(sys,"argv",["pilot","--real-readonly","--report-json",FILE]), \
             patch.object(Path,"write_text",return_value=100) as write, \
             contextlib.redirect_stdout(io.StringIO()):
            code=m.main()
        self.assertEqual(code,3)
        self.assertEqual(write.call_count,1)

    def test_workflow_uploads_only_sanitized_static_report(self):
        text=(ROOT/".github/workflows/v31_c148_universal_pilot_readonly.yml").read_text()
        self.assertIn("--report-json "+FILE,text)
        self.assertIn("uses: actions/upload-artifact@v4",text)
        self.assertIn("path: "+FILE,text)
        self.assertIn("retention-days: 14",text)
        self.assertIn("if: always()",text)
        self.assertNotIn("RADAR_LIVE_PUBLISH_ENABLED: \"true\"",text)

if __name__=="__main__":
    unittest.main()
