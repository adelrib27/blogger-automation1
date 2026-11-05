import importlib.util
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CODE = Path(__file__).resolve().parents[2] / "src" / "v31_daily_cycle_gate_safe.py"
SPEC = importlib.util.spec_from_file_location("v31_daily_cycle_gate_safe", CODE)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)
R = ZoneInfo("America/Recife")
SHA = "a" * 64
OLD = "b" * 64
NEW = "c" * 64


def fixtures():
    profile = {"mode":"SAFE","blog_id":GATE.BLOG,"page_id":GATE.PAGE,
               "page_url":f"https://{GATE.HOST}/p/loja.html", "blog_host":GATE.HOST,
               "categories":["Decoração","Organização","Cozinha","Quarto"],
               "expected_products":16,"per_category":{
                   "Decoração":4,"Organização":4,"Cozinha":4,"Quarto":4}}
    def fixed_items(offset):
        return [{"itemId":str(100000 + offset + cat_i*4+i),"category":cat}
                for cat_i,cat in enumerate(profile["categories"]) for i in range(4)]
    times=["2026-11-03T21:27:35-03:00","2026-11-03T22:19:09-03:00","2026-11-04T21:06:56-03:00"]
    ledger = {"schema":1,"blogId":GATE.BLOG,"pageId":GATE.PAGE,"operations":[
        {"operationId":SHA,"status":"PERSISTED","originalSha":OLD,
         "candidateSha":SHA,"selectionSha":SHA,"pageUpdatedAt":times[1],
         "publicProof":{"transport":GATE.PROOF_TRANSPORT,"htmlSha256":SHA,
                        "sourceRun":41769090187,"verifiedAt":"2026-11-04T05:19:00+00:00"}},
        {"operationId":NEW,"status":"PERSISTED","originalSha":SHA,
         "candidateSha":NEW,"selectionSha":NEW,"pageUpdatedAt":times[2],
         "prewriteClaim":{"state":"ATTEMPT_CLAIMED_BEFORE_PUT","backupSha256":SHA},
         "publicProof":{"transport":GATE.PROOF_TRANSPORT,"htmlSha256":NEW,
                        "sourceRun":41938854284,"verifiedAt":"2026-11-05T00:07:00+00:00",
                        "cards":16,"images":16,"links":16,"categories":4,"publicHttp":200}}
    ]}
    hist = {"version":1,"blogId":GATE.BLOG,"runs":[
        {"source":"seed_from_current_blogger_store","pageId":GATE.PAGE,
         "timestamp":times[0],"items":fixed_items(0)},
        {"source":"blogger_published","pageId":GATE.PAGE,"timestamp":times[1],
         "selectionSha":SHA,"operationId":SHA,"items":fixed_items(16)},
        {"source":"blogger_published","pageId":GATE.PAGE,"timestamp":times[2],
         "selectionSha":NEW,"operationId":NEW,"items":fixed_items(32)}]}
    return profile,ledger,hist


class TestDailyGate(unittest.TestCase):
    def eval(self, date="2026-11-04T22:11:00-03:00", data=None):
        return GATE.gate(*(data or fixtures()), now=datetime.fromisoformat(date))

    def test_today_skip(self):
        result=self.eval()
        self.assertEqual(result["status"], "SKIP_ALREADY_UPDATED_TODAY")
        self.assertFalse(result["safeScanAllowed"])
        self.assertFalse(result["bloggerPutAllowed"])
        self.assertFalse(result["remoteGitWriteAllowed"])
        self.assertFalse(result["cronEnabled"])

    def test_next_day_safe_only(self):
        p=self.eval("2026-11-05T08:47:00-03:00")
        self.assertEqual(p["status"], "READY_FOR_SAFE_SHOPEE_SCAN")
        self.assertTrue(p["safeScanAllowed"])
        self.assertFalse(p["bloggerPutAllowed"])

    def test_active_plan_rejected(self):
        p,l,h=fixtures();l["operations"][1]["status"]="PLAN"
        with self.assertRaises(GATE.DailyGateBlocked): self.eval(data=(p,l,h))

    def test_wrong_target_rejected(self):
        p,l,h=fixtures();p["page_id"]="900"
        with self.assertRaises(GATE.DailyGateBlocked): self.eval(data=(p,l,h))

    def test_history_out_of_sync_rejected(self):
        p,l,h=fixtures();h["runs"][2]["operationId"]="f"*64
        with self.assertRaises(GATE.DailyGateBlocked): self.eval(data=(p,l,h))

    def test_missing_public_proof_rejected(self):
        p,l,h=fixtures();del l["operations"][1]["publicProof"]
        with self.assertRaises(GATE.DailyGateBlocked): self.eval(data=(p,l,h))

    def test_duplicate_items_in_one_run_rejected(self):
        p,l,h=fixtures();h["runs"][2]["items"][0]["itemId"]=h["runs"][2]["items"][1]["itemId"]
        with self.assertRaises(GATE.DailyGateBlocked): self.eval(data=(p,l,h))

    def test_historical_reuse_allowed_when_policy_says_so(self):
        p,l,h=fixtures();h["runs"][2]["items"][0]["itemId"]=h["runs"][0]["items"][0]["itemId"]
        self.assertTrue(self.eval(data=(p,l,h))["status"].startswith("SKIP"))

    def test_future_publication_rejected(self):
        with self.assertRaises(GATE.DailyGateBlocked): self.eval("2026-11-03T00:00:00-03:00")

    def test_no_branch_crossover(self):
        with self.assertRaises(GATE.DailyGateBlocked):
            GATE.gate(*fixtures(), now=datetime.now(R), branch="main")

    def test_previous_candidate_chain_rejected(self):
        p,l,h=fixtures();l["operations"][1]["originalSha"]="d"*64
        with self.assertRaises(GATE.DailyGateBlocked): self.eval(data=(p,l,h))

    def test_no_naive_time(self):
        with self.assertRaises(GATE.DailyGateBlocked):
            GATE.gate(*fixtures(), now=datetime(2026,11,5,8,47))


if __name__ == "__main__":
    unittest.main()
