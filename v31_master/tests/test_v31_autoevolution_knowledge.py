#!/usr/bin/env python3
"""Regressao da memoria cumulativa V31 sem rede, tokens ou Blogger PUT."""
from __future__ import annotations
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "autoevolution"))
import engine
import knowledge
REPO=engine.ALLOWED_REPO
BRANCH=engine.ALLOWED_BRANCH


def raw(run_id, conclusion, name="Shopee Loja", status="completed"):
    return {
        "id": run_id, "name": name, "repository":{"full_name":REPO},
        "head_branch":"main", "event":"schedule",
        "status":status, "conclusion":conclusion,
    }


def report(*runs, generating=999999):
    return engine.collect_report(list(runs), repo=REPO, branch=BRANCH,
                                 generated_run_id=generating)


class TestCumulativeLearning(unittest.TestCase):
    def test_first_report_builds_memory(self):
        x=knowledge.update_knowledge(None, report(raw(100001,"failure"),raw(100002,"success")))
        self.assertEqual(x["total_distinct_completed_runs"],2)
        self.assertEqual(x["cumulative_failures_by_layer"]["SHOPEE_PIPELINE"],1)
        self.assertEqual(x["cumulative_successes_by_layer"]["SHOPEE_PIPELINE"],1)

    def test_second_report_only_adds_unseen_events(self):
        a=report(raw(100001,"failure"),raw(100002,"success"))
        first=knowledge.update_knowledge(None,a)
        second=knowledge.update_knowledge(first,report(raw(100001,"failure"),raw(100002,"success"),raw(100003,"failure")))
        self.assertEqual(second["total_distinct_completed_runs"],3)
        self.assertEqual(second["cumulative_failures_by_layer"]["SHOPEE_PIPELINE"],2)

    def test_replayed_report_does_not_double_count(self):
        a=report(raw(100001,"failure"))
        first=knowledge.update_knowledge(None,a)
        second=knowledge.update_knowledge(first,a)
        self.assertEqual(first["observed"],second["observed"])

    def test_conflicting_run_history_fails_closed(self):
        first=knowledge.update_knowledge(None,report(raw(100001,"failure")))
        with self.assertRaises(engine.SafetyStop):
            knowledge.update_knowledge(first,report(raw(100001,"success")))

    def test_queued_is_not_completed_evidence(self):
        x=knowledge.update_knowledge(None,report(raw(100001,None,status="queued")))
        self.assertEqual(x["total_distinct_completed_runs"],0)

    def test_no_auto_patch_promotion(self):
        x=knowledge.update_knowledge(None,report(raw(100001,"failure")))
        self.assertFalse(x["lessons"][0]["auto_patch"])
        self.assertTrue(x["lessons"][0]["production_approval_required"])
        self.assertTrue(x["security"]["no_production_code_writes"])

    def test_tampered_state_wrong_repo_rejected(self):
        first=knowledge.update_knowledge(None,report(raw(100001,"failure")))
        first["repository"]="other/repo"
        with self.assertRaises(engine.SafetyStop):
            knowledge.update_knowledge(first,report(raw(100002,"success")))

    def test_tampered_report_source_rejected(self):
        a=report(raw(100001,"failure"))
        a["source"]="RAW_LOG_WITH_SECRETS"
        with self.assertRaises(engine.SafetyStop):
            knowledge.update_knowledge(None,a)

    def test_tampered_report_production_writes_rejected(self):
        a=report(raw(100001,"failure"))
        a["safety"]["production_writes"]=True
        with self.assertRaises(engine.SafetyStop):
            knowledge.update_knowledge(None,a)

    def test_invalid_duplicate_history_rejected(self):
        x=knowledge.update_knowledge(None,report(raw(100001,"failure")))
        x["observed"].append(dict(x["observed"][0]))
        with self.assertRaises(engine.SafetyStop):
            knowledge.update_knowledge(x,report(raw(100002,"success")))

    def test_lesson_does_not_claim_root_cause(self):
        x=knowledge.update_knowledge(None,report(raw(100001,"failure"),raw(100002,"failure")))
        lesson=x["lessons"][0]
        self.assertEqual(lesson["action"],"OPEN_SAFE_EXPERIMENT_FOR_REVIEW")
        self.assertEqual(lesson["proposal"],"SAFE_DIAGNOSE_GRAPHQL_AND_CATALOG")

    def test_state_has_no_original_api_log_content(self):
        value=raw(100001,"failure")
        value["untrusted_log"]="SHOPEE_SECRET=private-value"
        x=knowledge.update_knowledge(None,report(value))
        self.assertNotIn("private-value",json.dumps(x))


if __name__=="__main__":
    unittest.main(verbosity=2)
