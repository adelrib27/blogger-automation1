"""The proposed LIVE policy and its atomic attempt ledger."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31 import autonomous_live as live
from affiliate_hub_v31.d1_universal_ready import UniversalD1ReadyState
from affiliate_hub_v31.tests.test_c71_d1_universal_ready import SqliteQuery


class LivePolicyTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.query = SqliteQuery(self.root / "state.sqlite3")
        self.addCleanup(self.query.close)
        for migration in ("c71_universal_ready_d1.sql", "c81_live_ledger.sql"):
            root = live.POLICY_PATH.parent / "migrations"
            self.query.db.executescript((root / migration).read_text(encoding="utf-8"))
        self.state = UniversalD1ReadyState(self.query)
        self.tenant = {"site_key": "blogger_example", "campaign": "example_campaign"}
        self.now = 1800000000
        self.rules = {"max_attempts_per_utc_day": 1, "minimum_interval_seconds": 86400,
                      "minimum_article_words": 350}

    def test_unapproved_and_changed_policy_are_blocked(self):
        path = self.root / "policy.json"
        proposal = {"version": 1, "activation": "pending_policy_approval",
                    "sites": {self.tenant["site_key"]: self.rules}}
        path.write_text(json.dumps(proposal))
        env = {"V31_AUTO_LIVE_APPROVED_POLICY_SHA256": hashlib.sha256(path.read_bytes()).hexdigest()}
        with self.assertRaisesRegex(live.LivePolicyError, "not_approved"):
            live.approved_policy(self.tenant["site_key"], policy_path=path, env=env)
        proposal["activation"] = "approved"
        path.write_text(json.dumps(proposal))
        with self.assertRaisesRegex(live.LivePolicyError, "not_approved"):
            live.approved_policy(self.tenant["site_key"], policy_path=path, env=env)
        env["V31_AUTO_LIVE_APPROVED_POLICY_SHA256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(live.approved_policy(self.tenant["site_key"], policy_path=path, env=env)[1],
                         self.rules)

    def seed(self, fingerprint, sku, expires):
        site, campaign = self.tenant.values()
        row = (site, campaign, sku)
        self.query("INSERT INTO v31_verified_evidence VALUES(?,?,?,?,?,?,?,?)",
                   (*row, "test", self.now-10, expires, "source", "{}"))
        self.query("INSERT INTO v31_ready_jobs VALUES(?,?,?,?,?,?,?,?,?)",
                   (site, campaign, fingerprint, sku, "html", "source", "USED", self.now-10, self.now-5))

    def attempt(self, fingerprint, post, now):
        return live.claim_attempt(self.state, tenant=self.tenant, fingerprint=fingerprint, post_id=post,
                                  digest="policy", limits=self.rules, now=now)

    def test_only_fresh_evidence_and_one_attempt_per_interval(self):
        self.seed("one", "test-one", self.now+10)
        self.seed("two", "test-two", self.now+999999)
        self.assertFalse(self.attempt("one", "1", self.now+15))
        self.assertTrue(self.attempt("two", "2", self.now+15))
        self.assertFalse(self.attempt("two", "2", self.now+16))
        live.record_outcome(self.state, tenant=self.tenant, fingerprint="two", status="PUBLISHED")
        self.seed("three", "test-three", self.now+999999)
        self.assertFalse(self.attempt("three", "3", self.now+16))
        self.assertTrue(self.attempt("three", "3", self.now+86420))

    def test_uncertain_attempt_pauses_tenant_even_on_later_days(self):
        self.seed("one", "test-one", self.now+999999)
        self.seed("two", "test-two", self.now+999999)
        self.assertTrue(self.attempt("one", "1", self.now))
        self.assertFalse(self.attempt("two", "2", self.now+86420))
        live.record_outcome(self.state, tenant=self.tenant, fingerprint="one", status="FAILED")
        self.assertFalse(self.attempt("two", "2", self.now+172840))
