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
    def __init__(self, doc):
        self.doc = doc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.doc, ensure_ascii=False).encode("utf-8")


def source(eid, domain):
    return {
        "evidence_id": eid,
        "identity_level": "EXACT_PRODUCT",
        "source_url": "https://example.invalid/evidence",
        "source_domain": domain,
        "source_title": "Produto Sensível Teste",
        "support_text": "Produto Sensível Teste",
        "allowed_in_article": True,
        "confidence": 1.0,
        "reason": "test fixture",
    }


def run():
    original_path = os.environ.get("VIDAPET_FIRECRAWL_TELEMETRY_PATH")
    original_key = os.environ.get("FIRECRAWL_API_KEY")
    original_urlopen = engine.urllib.request.urlopen
    original_sleep = engine.time.sleep
    original_policy, original_cache, original_report = reuse.POLICY_PATH, reuse.CACHE_PATH, reuse.REPORT_PATH
    original_live = reuse.live.build_evidence_package

    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            telemetry_path = root / "telemetry.json"
            os.environ["VIDAPET_FIRECRAWL_TELEMETRY_PATH"] = str(telemetry_path)
            os.environ["FIRECRAWL_API_KEY"] = "SENSITIVE_SELF_TEST_KEY"
            telemetry.reset()

            calls = {"count": 0, "rate_limit_once": True}

            def fake_urlopen(request, timeout=90):
                calls["count"] += 1
                payload = json.loads(request.data.decode("utf-8"))
                query = payload.get("query")
                if query == "RATE_LIMIT_QUERY" and calls["rate_limit_once"]:
                    calls["rate_limit_once"] = False
                    raise urllib.error.HTTPError(
                        request.full_url,
                        429,
                        "Too Many Requests",
                        {"Retry-After": "0"},
                        io.BytesIO(b'{"retry_after_seconds": 0}'),
                    )
                return FakeResponse({
                    "id": "SENSITIVE_SEARCH_ID",
                    "creditsUsed": 2,
                    "data": {"web": []},
                })

            engine.urllib.request.urlopen = fake_urlopen
            engine.time.sleep = lambda *_args, **_kwargs: None

            engine.firecrawl_search("SENSITIVE_QUERY_SENTINEL", limit=1)
            engine.firecrawl_search("RATE_LIMIT_QUERY", limit=1)

            snap = telemetry.snapshot()
            assert snap["counters"]["search_calls"] == 2
            assert snap["counters"]["http_attempts"] == 3
            assert snap["counters"]["rate_limit_429"] == 1
            assert snap["counters"]["search_successes"] == 2
            assert snap["credits_reported_total"] == 4.0

            reuse.POLICY_PATH = root / "policy.json"
            reuse.CACHE_PATH = root / "cache.json"
            reuse.REPORT_PATH = root / "reuse_report.json"
            policy = {
                "enabled": True,
                "lab_only": True,
                "ttl_days": 7,
                "require_verified_product_status": True,
                "require_same_normalized_product_name": True,
                "min_external_authorized_sources": 1,
                "require_exact_evidence_count": 2,
                "refresh_does_not_extend_ttl": True,
                "fallback": "FIRECRAWL",
                "fail_closed_when_fallback_unavailable": True,
            }
            reuse.POLICY_PATH.write_text(json.dumps(policy), encoding="utf-8")
            item = {"itemId": "SENSITIVE-ITEM-123", "productName": "Produto Sensível Teste"}
            fresh = int(time.time()) - 30
            cache = {
                "SENSITIVE-ITEM-123": {
                    "status": "VERIFIED",
                    "evidence_checked_at": fresh,
                    "product": {
                        "itemId": "SENSITIVE-ITEM-123",
                        "productName": "Produto Sensível Teste",
                    },
                    "sources": [
                        source("EV-API", "open-api.affiliate.shopee.com.br"),
                        source("EV-WEB", "shopee.com.br"),
                    ],
                }
            }
            reuse.CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
            package = reuse.build_evidence_package(item)
            assert package["version"] == "EVIDENCE_ENGINE_V1_3_PERSISTED_REUSE"

            stale = json.loads(json.dumps(cache))
            stale["SENSITIVE-ITEM-123"]["evidence_checked_at"] = int(time.time()) - 8 * 86400
            reuse.CACHE_PATH.write_text(json.dumps(stale), encoding="utf-8")

            def fake_live(*_args, **_kwargs):
                return {"status": "VERIFIED", "verified_at": int(time.time()), "sources": []}

            reuse.live.build_evidence_package = fake_live
            fallback = reuse.build_evidence_package(item)
            assert fallback["status"] == "VERIFIED"

            snap = telemetry.snapshot()
            assert snap["counters"]["cache_hits"] == 1
            assert snap["counters"]["cache_misses"] == 1
            assert snap["counters"]["fallback_required"] == 1
            assert snap["counters"]["fallback_successes"] == 1

            raw = telemetry_path.read_text(encoding="utf-8")
            for forbidden in (
                "SENSITIVE_QUERY_SENTINEL",
                "RATE_LIMIT_QUERY",
                "SENSITIVE_SELF_TEST_KEY",
                "SENSITIVE_SEARCH_ID",
                "SENSITIVE-ITEM-123",
                "Produto Sensível Teste",
                "example.invalid",
            ):
                assert forbidden not in raw
    finally:
        engine.urllib.request.urlopen = original_urlopen
        engine.time.sleep = original_sleep
        reuse.POLICY_PATH, reuse.CACHE_PATH, reuse.REPORT_PATH = original_policy, original_cache, original_report
        reuse.live.build_evidence_package = original_live
        if original_path is None:
            os.environ.pop("VIDAPET_FIRECRAWL_TELEMETRY_PATH", None)
        else:
            os.environ["VIDAPET_FIRECRAWL_TELEMETRY_PATH"] = original_path
        if original_key is None:
            os.environ.pop("FIRECRAWL_API_KEY", None)
        else:
            os.environ["FIRECRAWL_API_KEY"] = original_key

    print(json.dumps({
        "status": "FIRECRAWL_TELEMETRY_SELF_TEST_PASS",
        "aggregate_only": True,
        "cache_hit_miss_accounting": True,
        "fallback_accounting": True,
        "http_attempt_accounting": True,
        "rate_limit_429_accounting": True,
        "credits_used_accounting": True,
        "sensitive_fields_absent": True,
        "wordpress_written": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    run()
