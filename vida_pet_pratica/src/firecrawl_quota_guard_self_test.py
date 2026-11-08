"""R28 LAB budget guard regression: all Firecrawl I/O is mocked."""
import io
import json
import os
import tempfile
import time
import urllib.error
from pathlib import Path

import evidence_engine as engine
import evidence_engine_persistent_v13 as reuse
import firecrawl_telemetry as telemetry


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps({"creditsUsed": 1, "data": {"web": []}}).encode("utf-8")


def fixture_source(domain):
    return {
        "evidence_id": "test-evidence",
        "identity_level": "EXACT_PRODUCT",
        "source_domain": domain,
        "support_text": "Evidencia de teste suficiente",
        "allowed_in_article": True,
    }


def run():
    names = (
        "VIDAPET_FIRECRAWL_TELEMETRY_PATH",
        "VIDAPET_FIRECRAWL_BUDGET_GUARD",
        "VIDAPET_FIRECRAWL_MAX_SEARCH_CALLS",
        "VIDAPET_FIRECRAWL_MAX_HTTP_ATTEMPTS",
        "FIRECRAWL_API_KEY",
    )
    original_env = {k: os.environ.get(k) for k in names}
    original_urlopen = engine.urllib.request.urlopen
    original_paths = reuse.POLICY_PATH, reuse.CACHE_PATH, reuse.REPORT_PATH
    calls = {"n": 0}
    try:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            os.environ["VIDAPET_FIRECRAWL_TELEMETRY_PATH"] = str(root / "metrics.json")
            os.environ["VIDAPET_FIRECRAWL_BUDGET_GUARD"] = "1"
            os.environ["VIDAPET_FIRECRAWL_MAX_SEARCH_CALLS"] = "2"
            os.environ["VIDAPET_FIRECRAWL_MAX_HTTP_ATTEMPTS"] = "3"
            os.environ["FIRECRAWL_API_KEY"] = "SENTINEL_GUARD_SECRET"
            reuse.POLICY_PATH = root / "policy.json"
            reuse.CACHE_PATH = root / "cache.json"
            reuse.REPORT_PATH = root / "reuse_report.json"
            reuse.POLICY_PATH.write_text(json.dumps({
                "enabled": True, "lab_only": True, "ttl_days": 7,
                "require_verified_product_status": True,
                "require_same_normalized_product_name": True,
                "min_external_authorized_sources": 1,
                "require_exact_evidence_count": 2,
                "refresh_does_not_extend_ttl": True,
                "fallback": "FIRECRAWL",
                "fail_closed_when_fallback_unavailable": True,
            }), encoding="utf-8")
            item = {"itemId": "SENTINEL_ITEM", "productName": "Produto Teste Pet"}
            reuse.CACHE_PATH.write_text(json.dumps({"SENTINEL_ITEM": {
                "status": "VERIFIED", "evidence_checked_at": int(time.time()) - 30,
                "product": item,
                "sources": [
                    fixture_source("open-api.affiliate.shopee.com.br"),
                    fixture_source("shopee.com.br"),
                ],
            }}), encoding="utf-8")
            telemetry.reset()

            def successful_open(_request, timeout=90):
                calls["n"] += 1
                return FakeResponse()

            engine.urllib.request.urlopen = successful_open
            engine.firecrawl_search("SENTINEL_GUARD_QUERY_A", limit=1)
            engine.firecrawl_search("SENTINEL_GUARD_QUERY_B", limit=1)
            try:
                engine.firecrawl_search("SENTINEL_GUARD_QUERY_C", limit=1)
                raise AssertionError("third search should be refused")
            except RuntimeError as exc:
                assert "FIRECRAWL_LAB_CALL_BUDGET_EXHAUSTED" in str(exc)
            assert calls["n"] == 2
            metrics = telemetry.snapshot()
            assert metrics["counters"]["search_calls"] == 2
            assert metrics["counters"]["http_attempts"] == 2
            assert metrics["credits_reported_total"] == 2.0

            # A valid cached package still works when live budget is exhausted.
            cached = reuse.build_evidence_package(item)
            assert cached["version"] == "EVIDENCE_ENGINE_V1_3_PERSISTED_REUSE"
            assert calls["n"] == 2

            # A cache miss must not bypass the budget: fail closed, no new I/O.
            reuse.CACHE_PATH.write_text("{}", encoding="utf-8")
            try:
                reuse.build_evidence_package(item)
                raise AssertionError("cache miss cannot bypass live quota")
            except RuntimeError as exc:
                assert "EVIDENCE_FALLBACK_REQUIRED_BUT_UNAVAILABLE" in str(exc)
            assert calls["n"] == 2

            telemetry.reset()
            calls["n"] = 0

            def rate_limited(request, timeout=90):
                calls["n"] += 1
                raise urllib.error.HTTPError(request.full_url, 429, "Quota", {}, io.BytesIO(b"quota"))

            engine.urllib.request.urlopen = rate_limited
            try:
                engine.firecrawl_search("SENTINEL_429_QUERY", limit=1)
                raise AssertionError("429 must open circuit")
            except RuntimeError as exc:
                assert "FIRECRAWL_LAB_429_CIRCUIT_OPEN" in str(exc)
            assert calls["n"] == 1
            try:
                engine.firecrawl_search("SENTINEL_SECOND_QUERY", limit=1)
                raise AssertionError("subsequent calls after 429 must be refused")
            except RuntimeError as exc:
                assert "FIRECRAWL_LAB_429_CIRCUIT_OPEN" in str(exc)
            assert calls["n"] == 1
            assert telemetry.snapshot()["counters"]["rate_limit_429"] == 1

            # A missing or corrupted shared telemetry state cannot reset the budget.
            (root / "metrics.json").write_text("{broken", encoding="utf-8")
            try:
                engine.firecrawl_search("SENTINEL_CORRUPT_QUERY", limit=1)
                raise AssertionError("corrupt budget state should fail closed")
            except RuntimeError as exc:
                assert "FIRECRAWL_LAB_BUDGET_STATE_UNAVAILABLE" in str(exc)
            assert calls["n"] == 1

            raw = (root / "metrics.json").read_text(encoding="utf-8")
            for secret in ("SENTINEL_GUARD_SECRET", "SENTINEL_ITEM",
                           "SENTINEL_GUARD_QUERY_A", "SENTINEL_429_QUERY"):
                assert secret not in raw
    finally:
        engine.urllib.request.urlopen = original_urlopen
        reuse.POLICY_PATH, reuse.CACHE_PATH, reuse.REPORT_PATH = original_paths
        for name, value in original_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    print(json.dumps({
        "status": "FIRECRAWL_LAB_BUDGET_GUARD_SELF_TEST_PASS",
        "hard_search_budget": True,
        "http_attempt_budget": True,
        "cache_hit_allowed": True,
        "cache_miss_fail_closed": True,
        "429_single_attempt_circuit": True,
        "corrupt_counter_fail_closed": True,
        "real_firecrawl_requests": 0,
        "wordpress_written": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    run()
