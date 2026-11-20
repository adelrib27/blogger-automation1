"""C71 — D1-compatible contract test using REAL SQLite file, no APIs/CMS."""
import hashlib
import sqlite3
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31 import d1_universal_ready as d1
from affiliate_hub_v31.tests.test_c69_universal_evidence_ready import (
    KEYS, TITLES, NOW, package,
)

ROUTES = {
    "blogger_novo_exemplo": {
        "site_key":"blogger_novo_exemplo","campaign":"exemploblogger",
        "platform":"blogger","publish_enabled":False,
    },
    "wordpress_novo_exemplo": {
        "site_key":"wordpress_novo_exemplo","campaign":"exemplowp",
        "platform":"wordpress","publish_enabled":False,
    },
}
B = "blogger_novo_exemplo"
C = "exemploblogger"
W = "wordpress_novo_exemplo"
WC = "exemplowp"
NA = "a" * 22
NB = "b" * 22
T = int(NOW.timestamp())
ONE = "1" * 64
TWO = "2" * 64
THREE = "3" * 64
FOUR = "4" * 64


class SqliteQuery:
    """Duas conexões ao MESMO arquivo simulam dois runners independentes."""
    def __init__(self, path):
        self.db = sqlite3.connect(str(path), timeout=2, isolation_level=None)
        self.db.row_factory = sqlite3.Row

    def __call__(self, sql, params):
        c = self.db.execute(sql, params)
        return [dict(row) for row in c.fetchall()] if c.description else []

    def close(self):
        self.db.close()


class D1ReadyLeaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        path = Path(self.temp.name) / "c71-d1-fixture.sqlite3"
        first = SqliteQuery(path)
        self.addCleanup(first.close)
        migration = (Path(__file__).resolve().parents[1] /
                     "migrations" / "c71_universal_ready_d1.sql")
        first.db.executescript(migration.read_text(encoding="utf-8"))
        second = SqliteQuery(path)
        self.addCleanup(second.close)
        self.store = d1.UniversalD1ReadyState(first)
        self.other = d1.UniversalD1ReadyState(second)
        patcher = patch("affiliate_hub_v31.d1_universal_ready.sites",
                        return_value=ROUTES)
        patcher.start()
        self.addCleanup(patcher.stop)

    def acquire(self, who=NA, *, kind="refill", now=T):
        return self.store.acquire_lease(
            site_key=B,campaign=C,lease_name=kind,
            owner_nonce=who,now_epoch=now,ttl_seconds=60)

    def test_atomic_lease_contention_and_owner_compare_and_swap(self):
        self.assertTrue(self.acquire())
        self.assertFalse(self.other.acquire_lease(
            site_key=B,campaign=C,lease_name="refill",
            owner_nonce=NB,now_epoch=T+1,ttl_seconds=60))
        self.assertFalse(self.other.release_lease(
            site_key=B,campaign=C,lease_name="refill",owner_nonce=NB))
        self.assertTrue(self.other.acquire_lease(
            site_key=B,campaign=C,lease_name="refill",
            owner_nonce=NB,now_epoch=T+61,ttl_seconds=60))
        self.assertFalse(self.store.release_lease(
            site_key=B,campaign=C,lease_name="refill",owner_nonce=NA))
        self.assertTrue(self.other.release_lease(
            site_key=B,campaign=C,lease_name="refill",owner_nonce=NB))

    def test_missing_lease_does_not_create_ready(self):
        self.assertFalse(self.store.reserve_ready(
            site_key=B,campaign=C,owner_nonce=NA,fingerprint=ONE,
            product_key=KEYS[0],html_sha256=TWO,
            evidence_sha256=THREE,now_epoch=T,min_ready=2))
        self.assertEqual(self.store.count_ready(site_key=B,campaign=C),0)

    def test_min_ready_is_simultaneous_buffer_not_total_quota(self):
        self.assertTrue(self.acquire())
        def create(fp, sku, now=T):
            return self.store.reserve_ready(
                site_key=B,campaign=C,owner_nonce=NA,fingerprint=fp,
                product_key=sku,html_sha256=TWO,
                evidence_sha256=THREE,now_epoch=now,min_ready=2)
        self.assertTrue(create(ONE,KEYS[0]))
        self.assertFalse(create(ONE,KEYS[0]))  # idempotency
        self.assertTrue(create(TWO,KEYS[1]))
        self.assertFalse(create(THREE,KEYS[2]))  # buffer already full
        self.assertEqual(self.other.count_ready(site_key=B,campaign=C),2)
        self.assertFalse(self.store.consume_one(
            site_key=B,campaign=C,owner_nonce=NB,fingerprint=ONE,now_epoch=T))
        self.assertTrue(self.acquire(kind="writer"))
        self.assertTrue(self.store.consume_one(
            site_key=B,campaign=C,owner_nonce=NA,fingerprint=ONE,now_epoch=T))
        self.assertFalse(self.store.consume_one(
            site_key=B,campaign=C,owner_nonce=NA,fingerprint=ONE,now_epoch=T))
        self.assertTrue(create(THREE,KEYS[2]))
        self.assertEqual(self.store.count_ready(site_key=B,campaign=C),2)
        self.assertFalse(create(ONE,KEYS[0]))  # already USED, no reinsert

    def test_same_sku_different_angle_blocked_for_cooldown_then_reusable(self):
        self.assertTrue(self.acquire())
        self.assertTrue(self.store.reserve_ready(
            site_key=B,campaign=C,owner_nonce=NA,fingerprint=ONE,
            product_key=KEYS[0],html_sha256=TWO,
            evidence_sha256=THREE,now_epoch=T))
        # A different fingerprint is NOT enough to evade same-SKU cooldown.
        self.assertFalse(self.other.reserve_ready(
            site_key=B,campaign=C,owner_nonce=NA,fingerprint=FOUR,
            product_key=KEYS[0],html_sha256=TWO,
            evidence_sha256=THREE,now_epoch=T))
        self.assertTrue(self.acquire(kind="writer"))
        self.assertTrue(self.store.consume_one(
            site_key=B,campaign=C,owner_nonce=NA,fingerprint=ONE,now_epoch=T))
        self.assertFalse(self.other.reserve_ready(
            site_key=B,campaign=C,owner_nonce=NA,fingerprint=FOUR,
            product_key=KEYS[0],html_sha256=TWO,
            evidence_sha256=THREE,now_epoch=T+30))
        # Only after cooldown and a new valid lease can a NEW angle enter.
        future=T+31*86400
        self.assertTrue(self.store.acquire_lease(
            site_key=B,campaign=C,lease_name="refill",
            owner_nonce=NA,now_epoch=future,ttl_seconds=60))
        self.assertTrue(self.store.reserve_ready(
            site_key=B,campaign=C,owner_nonce=NA,fingerprint=FOUR,
            product_key=KEYS[0],html_sha256=TWO,
            evidence_sha256=THREE,now_epoch=future))

    def test_site_campaign_isolation_and_wrong_tenant_fail_closed(self):
        self.assertTrue(self.acquire())
        self.assertTrue(self.store.reserve_ready(
            site_key=B,campaign=C,owner_nonce=NA,fingerprint=ONE,
            product_key=KEYS[0],html_sha256=TWO,
            evidence_sha256=THREE,now_epoch=T))
        self.assertEqual(self.other.count_ready(site_key=W,campaign=WC),0)
        with self.assertRaisesRegex(d1.D1SafeError, "tenant_registry"):
            self.other.count_ready(site_key=W,campaign=C)
        with self.assertRaisesRegex(d1.D1SafeError, "tenant_registry"):
            self.other.count_ready(site_key="vida_pet_pratica",campaign=C)
        self.assertTrue(self.other.acquire_lease(
            site_key=W,campaign=WC,lease_name="refill",
            owner_nonce=NB,now_epoch=T))
        self.assertTrue(self.other.reserve_ready(
            site_key=W,campaign=WC,owner_nonce=NB,fingerprint=ONE,
            product_key=KEYS[0],html_sha256=TWO,
            evidence_sha256=THREE,now_epoch=T))
        self.assertEqual(self.other.count_ready(site_key=W,campaign=WC),1)

    def test_expired_lease_cannot_mutate_jobs(self):
        self.assertTrue(self.acquire())
        self.assertFalse(self.store.reserve_ready(
            site_key=B,campaign=C,owner_nonce=NA,fingerprint=ONE,
            product_key=KEYS[0],html_sha256=TWO,
            evidence_sha256=THREE,now_epoch=T+61))
        self.assertEqual(self.store.count_ready(site_key=B,campaign=C),0)

    def test_verified_evidence_is_tenant_isolated_ttl_immutable(self):
        self.assertTrue(self.acquire())
        self.assertTrue(self.store.cache_verified_evidence(
            site_key=B,campaign=C,owner_nonce=NA,
            product_key=KEYS[0],product_title=TITLES[0],
            package=package(0),now_epoch=T))
        restored=self.other.get_verified_evidence(
            site_key=B,campaign=C,product_key=KEYS[0],
            product_title=TITLES[0],now_epoch=T)
        self.assertEqual(restored["verified_utc"],package(0)["verified_utc"])
        self.assertIsNone(self.other.get_verified_evidence(
            site_key=W,campaign=WC,product_key=KEYS[0],
            product_title=TITLES[0],now_epoch=T))
        self.assertIsNone(self.other.get_verified_evidence(
            site_key=B,campaign=C,product_key=KEYS[0],
            product_title=TITLES[0],now_epoch=T+9*86400))
        # Reusing exactly the same package does NOT extend freshness.
        self.assertFalse(self.store.cache_verified_evidence(
            site_key=B,campaign=C,owner_nonce=NA,
            product_key=KEYS[0],product_title=TITLES[0],
            package=package(0),now_epoch=T))

    def test_invalid_sources_do_not_enter_shared_cache(self):
        self.assertTrue(self.acquire())
        with self.assertRaisesRegex(d1.D1SafeError, "evidence_not_verified"):
            self.store.cache_verified_evidence(
                site_key=B,campaign=C,owner_nonce=NA,
                product_key=KEYS[0],product_title=TITLES[0],
                package=package(0,authorized=False),now_epoch=T)
        self.assertIsNone(self.store.get_verified_evidence(
            site_key=B,campaign=C,product_key=KEYS[0],
            product_title=TITLES[0],now_epoch=T))

    def test_daily_budget_is_atomic_and_circuit_breaker_durable(self):
        self.assertTrue(self.store.acquire_lease(
            site_key=B,campaign=C,lease_name="firecrawl",
            owner_nonce=NA,now_epoch=T,ttl_seconds=300))
        def attempt(at, store=None):
            return (store or self.store).claim_search_budget(
                site_key=B,campaign=C,owner_nonce=NA,now_epoch=at,
                kind="SEARCH",daily_cap=3)
        self.assertTrue(attempt(T))
        self.assertTrue(attempt(T+1,self.other))
        self.assertFalse(self.other.claim_search_budget(
            site_key=B,campaign=C,owner_nonce=NB,now_epoch=T+1,
            kind="SEARCH",daily_cap=3))
        self.assertEqual(self.store.block_search_on_429(
            site_key=B,campaign=C,owner_nonce=NA,now_epoch=T+2,
            block_seconds=60),1)
        self.assertFalse(attempt(T+30,self.other))
        self.assertTrue(attempt(T+63,self.other))
        self.assertFalse(attempt(T+64,self.other))

    def test_query_error_or_invalid_return_fails_closed(self):
        def broken(_sql,_params):
            raise RuntimeError("connection closed")
        with self.assertRaisesRegex(d1.D1SafeError, "d1_query_failed_closed"):
            d1.UniversalD1ReadyState(broken).count_ready(
                site_key=B,campaign=C)
        with self.assertRaisesRegex(d1.D1SafeError, "d1_query_result_untrusted"):
            d1.UniversalD1ReadyState(lambda *_: None).count_ready(
                site_key=B,campaign=C)

    def test_no_read_only_claim_can_publish_or_change_blog_content(self):
        self.assertFalse(hasattr(self.store, "publish"))
        self.assertFalse(hasattr(self.store, "create_post"))
        self.assertFalse(hasattr(self.store, "convert_shopee_link"))
        self.assertFalse(hasattr(self.store, "write_wordpress"))
        self.assertEqual(self.store.count_ready(site_key=B,campaign=C),0)


if __name__ == "__main__":
    unittest.main()
