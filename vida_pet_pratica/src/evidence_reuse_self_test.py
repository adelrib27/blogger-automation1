import json
import tempfile
import time
from pathlib import Path

import evidence_engine_persistent_v13 as reuse


def source(eid, identity="EXACT_PRODUCT", domain="shopee.com.br"):
    return {
        "evidence_id": eid,
        "identity_level": identity,
        "source_url": "https://example.invalid/" + eid,
        "source_domain": domain,
        "source_title": "Produto Teste",
        "support_text": "Produto Teste",
        "allowed_in_article": True,
        "confidence": 1.0,
        "reason": "test fixture",
    }


def run():
    original_policy, original_cache, original_report = reuse.POLICY_PATH, reuse.CACHE_PATH, reuse.REPORT_PATH
    original_live = reuse.live.build_evidence_package
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        reuse.POLICY_PATH = root / "policy.json"
        reuse.CACHE_PATH = root / "cache.json"
        reuse.REPORT_PATH = root / "report.json"
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
        item = {"itemId": "123", "productName": "Produto Teste"}
        fresh = int(time.time()) - 60
        cache = {
            "123": {
                "status": "VERIFIED",
                "evidence_checked_at": fresh,
                "product": {"itemId": "123", "productName": "Produto Teste"},
                "sources": [
                    source("EV-SHOPEE-API-123", domain="open-api.affiliate.shopee.com.br"),
                    source("EV-WEB-EXACT-123", domain="shopee.com.br"),
                ],
            }
        }
        reuse.CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
        package = reuse.build_evidence_package(item)
        assert package["status"] == "VERIFIED"
        assert package["version"] == "EVIDENCE_ENGINE_V1_3_PERSISTED_REUSE"
        assert package["verified_at"] == fresh
        assert len([s for s in package["sources"] if s["identity_level"] == "EXACT_PRODUCT"]) >= 2

        def fail_live(*args, **kwargs):
            raise RuntimeError("simulated fallback unavailable")

        reuse.live.build_evidence_package = fail_live
        stale = json.loads(json.dumps(cache))
        stale["123"]["evidence_checked_at"] = int(time.time()) - 8 * 86400
        reuse.CACHE_PATH.write_text(json.dumps(stale), encoding="utf-8")
        try:
            reuse.build_evidence_package(item)
            raise AssertionError("stale evidence should fail closed when fallback unavailable")
        except RuntimeError as exc:
            assert "EVIDENCE_FALLBACK_REQUIRED_BUT_UNAVAILABLE" in str(exc)

        renamed = json.loads(json.dumps(cache))
        renamed["123"]["product"]["productName"] = "Outro Produto"
        reuse.CACHE_PATH.write_text(json.dumps(renamed), encoding="utf-8")
        try:
            reuse.build_evidence_package(item)
            raise AssertionError("renamed product should require fallback")
        except RuntimeError as exc:
            assert "EVIDENCE_FALLBACK_REQUIRED_BUT_UNAVAILABLE" in str(exc)

        insufficient = json.loads(json.dumps(cache))
        insufficient["123"]["sources"] = [source("EV-SHOPEE-API-123", domain="open-api.affiliate.shopee.com.br")]
        reuse.CACHE_PATH.write_text(json.dumps(insufficient), encoding="utf-8")
        try:
            reuse.build_evidence_package(item)
            raise AssertionError("insufficient exact/external evidence should require fallback")
        except RuntimeError as exc:
            assert "EVIDENCE_FALLBACK_REQUIRED_BUT_UNAVAILABLE" in str(exc)

    reuse.POLICY_PATH, reuse.CACHE_PATH, reuse.REPORT_PATH = original_policy, original_cache, original_report
    reuse.live.build_evidence_package = original_live
    print(json.dumps({
        "status": "EVIDENCE_REUSE_SELF_TEST_PASS",
        "fresh_reuse": True,
        "ttl_preserved": True,
        "stale_fail_closed": True,
        "identity_change_fail_closed": True,
        "insufficient_evidence_fail_closed": True,
        "wordpress_written": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    run()
