"""C147: executor de artigo prioriza cache e pode converter um único SKU no ciclo.

Integração inteiramente simulada: nem Shopee, nem Cloudflare, nem CMS/Firecrawl.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from affiliate_hub_v31 import autonomous_review as review
from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.routing import sites

SITE = "wordpress_casa_decoracao"
CACHED = "shopee:111222:333444"
MISSING = "shopee:555666:777888"
THIRD = "shopee:888999:111000"
LINK = "https://s.shopee.com.br/1gKKtbXPHn"
PROFILE = {"query":"vaso decorativo comprovado"}


class DummyStorage:
    def __init__(self, data):
        self.data=data
        self.restores=0
    def restore_to(self, path):
        Path(path).write_bytes(self.data)
        self.restores+=1
        return True


class DummyState:
    def __init__(self, *, cap=0, previous=None):
        self.cap=cap
        self.previous=previous
        self.jobs=0
        self.fresh_ready=[]
    def count_draft_attempts_today(self, **kwargs):
        return self.cap
    def list_fresh_ready(self, **kwargs):
        return self.fresh_ready
    def get_job(self, **kwargs):
        self.jobs+=1
        return self.previous
    def ready_has_fresh_evidence(self, **kwargs):
        return False


class InCycleReviewTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory(prefix="v31-c147-integration-")
        self.addCleanup(self.folder.cleanup)
        filename=Path(self.folder.name)/"catalog.sqlite3"
        self.route=sites()[SITE]
        with Catalog(filename) as catalog:
            with catalog.db:
                for sku in (CACHED,MISSING,THIRD):
                    shop,item=sku.split(":")[1:]
                    catalog.db.execute("""
                        INSERT INTO products
                        (product_key,shop_id,item_id,title,description,origin_url,image_url,
                         moderation,moderation_reason,first_source,last_seen_utc)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """, (sku,shop,item,"Vaso decorativo seguro","",
                          f"https://shopee.com.br/product/{shop}/{item}",
                          "https://cf.shopee.com.br/file/v31-c147", "eligible","",
                          "test","2026-11-24T00:00:00Z"))
                    catalog.db.execute("""
                        INSERT INTO product_taxonomy
                        (product_key,category,niche,status,reason,version)
                        VALUES(?,?,?,?,?,?)
                    """, (sku,"casa","decoracao","matched","","test"))
            catalog.cache_link(CACHED,self.route["campaign"], LINK)
        self.storage=DummyStorage(filename.read_bytes())
        self.history={"site_key":SITE,"keys":[],"slugs":[],"prose":[],"count":0}
        self.state=DummyState()
        self.conversions=[]
        self.verified=[]
        self.offers=[(MISSING,dict(PROFILE)),(CACHED,dict(PROFILE))]
        self.conversion_outcome="CONVERTED"
        self.verify_fail_on=set()
        self.patches=[
            patch.object(review,"_official_storage",return_value=self.storage),
            patch.object(review.CloudflareD1HTTPRunner,"from_environment",return_value=lambda sql,params:[]),
            patch.object(review,"UniversalD1ReadyState",return_value=self.state),
            patch.object(review,"R2PrivateReadyBackend",return_value=object()),
            patch.object(review,"ImmutablePrivateReadyEnvelope",return_value=MagicMock()),
            patch.object(review,"configured_signing_keys",return_value=("private","hmac","aa")),
            patch.object(review,"_selection",side_effect=lambda *args,**kwargs:iter(self.offers)),
            patch.object(review,"convert_for_review",side_effect=self.fake_convert),
            patch.object(review,"verify_offer",side_effect=self.fake_verify),
            patch.object(review,"prose_hashes",return_value=set()),
            patch.object(review,"prepare_review_payload",return_value={"reviewed":True}),
            patch.object(review,"payload_digest",return_value="a"*64),
            patch.object(review,"approval_receipt",return_value={"signature":"a"*64}),
            patch.object(review,"sign_release",return_value="a"*64),
            patch.object(review,"stage_reviewed_ready",
                         return_value={"job_status":"READY","fingerprint":"b"*64}),
            patch.dict(os.environ,{
                "V31_ON_DEMAND_CONVERSION":"true",
                "V31_EDITORIAL_SHOPEE_APP_ID":"test-app-id",
                "V31_EDITORIAL_SHOPEE_APP_SECRET":"test-app-secret",
                "V31_REVIEW_RELEASE_PUBLIC_KEY_HEX":"aa",
            }),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def fake_convert(self, **kwargs):
        self.conversions.append(kwargs["product_key"])
        self.assertEqual(kwargs["route"]["campaign"],self.route["campaign"])
        self.assertEqual(kwargs["app_id"],"test-app-id")
        self.assertEqual(kwargs["app_secret"],"test-app-secret")
        self.assertTrue(callable(kwargs["reserve_attempt"]))
        return self.conversion_outcome

    def fake_verify(self, **kwargs):
        sku=kwargs["sku"]
        self.verified.append(sku)
        if sku in self.verify_fail_on:
            raise review.VerificationError("trusted_manufacturer_source_unavailable")
        return {"html_content":"<article>Conteúdo verificável.</article>",
                "used_evidence_ids":["test-fact"]}

    def test_prefers_cached_product_even_when_missing_listed_first(self):
        result=review.run(site_key=SITE,history=self.history)
        self.assertEqual(result["status"],"READY")
        self.assertEqual(self.verified,[CACHED])
        self.assertEqual(self.conversions,[])

    def test_converts_missing_sku_after_cached_product_fails_fact_review(self):
        self.verify_fail_on.add(CACHED)
        result=review.run(site_key=SITE,history=self.history)
        self.assertEqual(result["status"],"READY")
        self.assertEqual(self.verified,[CACHED,MISSING])
        self.assertEqual(self.conversions,[MISSING])

    def test_no_cms_duplicate_product_conversion(self):
        self.offers=[(MISSING,dict(PROFILE))]
        self.history["keys"]=[hashlib.sha256(MISSING.encode()).hexdigest()]
        result=review.run(site_key=SITE,history=self.history)
        self.assertEqual(result["status"],"NO_NEW_OFFER")
        self.assertEqual(self.conversions,[])

    def test_no_conversion_when_draft_daily_cap_reached(self):
        self.state.cap=1
        self.offers=[(MISSING,dict(PROFILE))]
        result=review.run(site_key=SITE,history=self.history)
        self.assertEqual(result["reason"],"draft_daily_cap_reached")
        self.assertEqual(self.conversions,[])

    def test_no_conversion_on_probe(self):
        self.offers=[(MISSING,dict(PROFILE))]
        result=review.run(site_key=SITE,history=self.history,probe=True)
        self.assertEqual(result["status"],"NO_NEW_OFFER")
        self.assertEqual(self.conversions,[])

    def test_no_conversion_when_opt_in_disabled(self):
        os.environ["V31_ON_DEMAND_CONVERSION"]="false"
        self.offers=[(MISSING,dict(PROFILE))]
        result=review.run(site_key=SITE,history=self.history)
        self.assertEqual(result["status"],"NO_NEW_OFFER")
        self.assertEqual(self.conversions,[])

    def test_one_conversion_per_cycle_even_after_factual_failure(self):
        self.offers=[(MISSING,dict(PROFILE)),(THIRD,dict(PROFILE))]
        self.verify_fail_on={MISSING,THIRD}
        result=review.run(site_key=SITE,history=self.history)
        self.assertEqual(result["status"],"NO_NEW_OFFER")
        self.assertEqual(self.conversions,[MISSING])
        self.assertEqual(self.verified,[MISSING])

    def test_conversion_budget_exhausted_has_no_article_or_retry(self):
        self.offers=[(MISSING,dict(PROFILE))]
        self.conversion_outcome="BUDGET_DENIED"
        result=review.run(site_key=SITE,history=self.history)
        self.assertEqual(result["status"],"NO_NEW_OFFER")
        self.assertEqual(result["reason"],"conversion_daily_budget_exhausted")
        self.assertEqual(self.conversions,[MISSING])
        self.assertEqual(self.verified,[])

    def test_prior_ready_job_without_cache_requires_reconciliation(self):
        self.offers=[(MISSING,dict(PROFILE))]
        self.state.previous={"status":"READY","html_sha256":"e"*64}
        with self.assertRaisesRegex(review.VerificationError,
                                    "on_demand_existing_job_missing_cache"):
            review.run(site_key=SITE,history=self.history)
        self.assertEqual(self.conversions,[])


if __name__=="__main__":
    unittest.main()
