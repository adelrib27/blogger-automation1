"""Synthetic storage canary. Run only in the isolated V31 GitHub job."""

import hashlib
import json
import uuid
from contextlib import ExitStack
from datetime import timedelta
from unittest.mock import patch

from affiliate_hub_v31.d1_http_runner import CloudflareD1HTTPRunner
from affiliate_hub_v31.d1_universal_ready import UniversalD1ReadyState
from affiliate_hub_v31.private_ready_envelope import ImmutablePrivateReadyEnvelope, object_key
from affiliate_hub_v31.reviewed_ready_promotion import stage_reviewed_ready
from affiliate_hub_v31.r2_private_ready_backend import BUCKET, R2PrivateReadyBackend
from affiliate_hub_v31.tests import test_c77_reviewed_ready_promotion as fixture

TABLES = ("v31_ready_jobs", "v31_verified_evidence", "v31_search_budget", "v31_ready_leases")


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def exercise_expired_buffer(state, tenant, now):
    product = fixture.KEYS[1]
    owner = {"owner_nonce": uuid.uuid4().hex, "lease_name": "refill"}
    cached = {"product_key": product, "product_title": fixture.TITLES[1],
              "owner_nonce": owner["owner_nonce"]}
    before, after = "a" * 64, "b" * 64

    def reserve(when, fingerprint, expected_evidence):
        epoch = int(when.timestamp())
        proof = fixture.package(1, date=when.isoformat())
        require(state.acquire_lease(**tenant, **owner, now_epoch=epoch),
                "C81_REFILL_LEASE_FAILED")
        try:
            require(state.cache_verified_evidence(**tenant, **cached, package=proof,
                                                  now_epoch=epoch) == expected_evidence,
                    "C81_EVIDENCE_REFRESH_UNEXPECTED")
            digest = hashlib.sha256(json.dumps(
                proof, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
            return state.reserve_ready(
                **tenant, owner_nonce=owner["owner_nonce"], fingerprint=fingerprint,
                product_key=product, html_sha256="c" * 64, evidence_sha256=digest,
                min_ready=1, now_epoch=epoch,
            )
        finally:
            require(state.release_lease(**tenant, **owner), "C81_REFILL_RELEASE_FAILED")

    require(reserve(now, before, True), "C81_INITIAL_BUFFER_READY_FAILED")
    require(not reserve(now + timedelta(hours=1), after, False),
            "C81_ACTIVE_EVIDENCE_REPLACED")
    require(reserve(now + timedelta(days=8), after, True), "C81_EXPIRED_BUFFER_BLOCKED")
    print("C81_OFFICIAL_D1_STALE_BUFFER_RECOVERY=PASS")


def main():
    site = "c81_canary_" + uuid.uuid4().hex
    campaign = "c81_storage_canary"
    tenant = {"site_key": site, "campaign": campaign}
    routes = {site: {**fixture.ROUTES[fixture.SITE], **tenant}}
    runner = CloudflareD1HTTPRunner.from_environment(allow_mutations=True)
    state = UniversalD1ReadyState(runner)
    backend = R2PrivateReadyBackend.from_environment()
    envelope = ImmutablePrivateReadyEnvelope(backend=backend)
    test = fixture.ReviewedReadyIntegrationTests()
    with ExitStack() as stack:
        stack.callback(test.doCleanups)
        stack.enter_context(patch.object(fixture, "SITE", site))
        stack.enter_context(patch.object(fixture, "CAMPAIGN", campaign))
        stack.enter_context(patch.object(fixture, "ROUTES", routes))
        test.setUp()
        params = test.input(state=state, envelope=envelope)
        html_hash = hashlib.sha256(params["html_content"].encode("utf-8")).hexdigest()
        key = object_key(site, campaign, html_hash)
        owner = {"owner_nonce": uuid.uuid4().hex, "lease_name": "writer"}
        require(backend.get(key) is None, "C81_CANARY_OBJECT_ALREADY_EXISTS")
        try:
            staged = stage_reviewed_ready(**params)
            require(staged["status"] == "READY_RESERVED_FOR_DRAFT_REVIEW", "C81_READY_FAILED")
            require(stage_reviewed_ready(**params)["status"] == "READY_ALREADY_STAGED",
                    "C81_REPLAY_FAILED")
            fingerprint = staged["fingerprint"]
            job = state.get_job(**tenant, fingerprint=fingerprint)
            stored = envelope.load(**tenant, html_sha256=job["html_sha256"],
                                   independent_review_key=fixture.KEY)
            require(job["status"] == "READY" and stored["html_content"] == params["html_content"]
                    and stored["review"]["evidence_sha256"] == job["evidence_sha256"],
                    "C81_READBACK_BINDING_FAILED")
            epoch = int(params["now"].timestamp())
            require(state.acquire_lease(**tenant, **owner, now_epoch=epoch),
                    "C81_WRITER_LEASE_FAILED")
            consume = {"fingerprint": fingerprint, "now_epoch": epoch,
                       "owner_nonce": owner["owner_nonce"]}
            require(state.consume_one(**tenant, **consume), "C81_CONSUME_FAILED")
            require(not state.consume_one(**tenant, **consume), "C81_DUPLICATE_CONSUME")
            require(state.get_job(**tenant, fingerprint=fingerprint)["status"] == "USED",
                    "C81_USED_READBACK_FAILED")
            print("C81_OFFICIAL_R2_D1_EXACT_READBACK_READY_USED_REPLAY=PASS")
            exercise_expired_buffer(state, tenant, params["now"])
        finally:
            try:
                for table in TABLES:
                    runner(f"DELETE FROM {table} WHERE site_key=? AND campaign=?", (site, campaign))
                for table in TABLES:
                    counts = runner(f"SELECT count(*) AS n FROM {table} WHERE site_key=? AND campaign=?",
                                    (site, campaign))
                    require(counts == [{"n": 0}], "C81_D1_CLEANUP_FAILED")
                print("C81_D1_CANARY_CLEANUP_ZERO=PASS")
            finally:
                backend._s3.delete_object(Bucket=BUCKET, Key=key)
                require(backend.get(key) is None, "C81_R2_CLEANUP_FAILED")
                print("C81_R2_CANARY_CLEANUP_ZERO=PASS")


if __name__ == "__main__":
    main()
