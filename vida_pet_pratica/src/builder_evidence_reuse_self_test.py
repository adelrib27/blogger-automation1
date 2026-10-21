import json
import tempfile
import time
from pathlib import Path

import article_builder_persistent_v3 as builder_v3


def source(eid, domain):
    return {
        "evidence_id": eid,
        "identity_level": "EXACT_PRODUCT",
        "source_url": "https://example.invalid/" + eid,
        "source_domain": domain,
        "source_title": "Organizador Pet Teste",
        "support_text": "Organizador Pet Teste com divisórias removíveis e fechamento simples.",
        "allowed_in_article": True,
        "confidence": 1.0,
        "reason": "builder reuse self-test fixture",
    }


def run():
    reuse = builder_v3.persisted_evidence
    core = builder_v3.persistent_core
    original_policy = reuse.POLICY_PATH
    original_cache = reuse.CACHE_PATH
    original_report = reuse.REPORT_PATH
    original_live = reuse.live.build_evidence_package
    original_out = core.OUT_DIR

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        reuse.POLICY_PATH = root / "policy.json"
        reuse.CACHE_PATH = root / "cache.json"
        reuse.REPORT_PATH = root / "report.json"
        core.OUT_DIR = root / "architecture_lab"

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
        checked_at = int(time.time()) - 60
        item = {
            "itemId": "987654",
            "productName": "Organizador Pet Teste",
            "categories": ["Organizacao"],
            "keywords": ["organizador pet"],
        }
        cache = {
            "987654": {
                "status": "VERIFIED",
                "evidence_checked_at": checked_at,
                "product": {"itemId": "987654", "productName": "Organizador Pet Teste"},
                "sources": [
                    source("EV-SHOPEE-API-987654", "open-api.affiliate.shopee.com.br"),
                    source("EV-WEB-EXACT-987654", "shopee.com.br"),
                ],
            }
        }
        reuse.CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")

        def live_must_not_run(*args, **kwargs):
            raise AssertionError("live Firecrawl fallback must not run for valid persisted evidence")

        reuse.live.build_evidence_package = live_must_not_run
        assert core.evidence is reuse
        candidate, rejection = core.candidate_from_item(
            item,
            history=[],
            max_similarity=0.72,
            max_results=8,
            status="VERIFIED_READY_CANDIDATE",
            angle_status_prefix="NEW_PRODUCT_FAILOVER_",
        )
        assert rejection is None
        assert candidate is not None
        assert candidate["itemId"] == "987654"
        assert candidate["status"] == "VERIFIED_READY_CANDIDATE"
        package = json.loads((core.OUT_DIR / "evidence" / "987654.json").read_text(encoding="utf-8"))
        assert package["version"] == "EVIDENCE_ENGINE_V1_3_PERSISTED_REUSE"
        assert package["verified_at"] == checked_at

    reuse.POLICY_PATH = original_policy
    reuse.CACHE_PATH = original_cache
    reuse.REPORT_PATH = original_report
    reuse.live.build_evidence_package = original_live
    core.OUT_DIR = original_out

    print(json.dumps({
        "status": "BUILDER_EVIDENCE_REUSE_SELF_TEST_PASS",
        "builder_failover_uses_persisted_reuse": True,
        "live_fallback_not_called_when_cache_valid": True,
        "ttl_timestamp_preserved": True,
        "wordpress_written": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    run()
