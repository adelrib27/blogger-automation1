"""Contrato C145: auditoria D1 USED -> CMS DRAFT, sem mutações externas."""
from __future__ import annotations

import hashlib
import unittest
from unittest.mock import MagicMock, patch

from affiliate_hub_v31.audit_draft_pilots import (
    MAX_USED_JOBS_PER_SITE, DraftPilotAuditError, _blogger_outcome,
    audit,
)
from affiliate_hub_v31 import automatic_wordpress_drafts as wordpress
from affiliate_hub_v31.routing import sites

WP = "wordpress_casa_decoracao"
BLOGGER = "blogger_moveis_para_cada_canto"
PRODUCT = "shopee:400124163:42079451217"
CONTENT = ('<article lang="pt-BR" data-v31-product-key="' + PRODUCT +
           '"><p>Orientação original comprovada.</p></article>')
FINGERPRINT = "a" * 64


def used(route, content=CONTENT, **overrides):
    value = {
        "site_key": route["site_key"],
        "campaign": route["campaign"],
        "fingerprint": FINGERPRINT,
        "product_key": PRODUCT,
        "html_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "status": "USED",
    }
    return {**value, **overrides}


class FakeWordPress:
    def __init__(self, route, content=CONTENT, status="draft",
                 missing=False, title="Artigo original"):
        self.route = route
        self.content = content
        self.status = status
        self.missing = missing
        self.title = title
        self.calls = []
        self.slug = wordpress._product_slug(route["site_key"], PRODUCT)

    def site_settings(self):
        self.calls.append("settings")
        return {"url": self.route["identifier"]}

    def list_posts(self, *, include_unpublished, slug):
        self.calls.append("list")
        assert include_unpublished and slug == self.slug
        return [] if self.missing else [{"id": 321, "slug": slug}]

    def get_post(self, post_id):
        self.calls.append("get")
        assert post_id == 321
        return {
            "id": 321, "slug": self.slug, "status": self.status,
            "title": {"raw": self.title}, "content": {"raw": self.content},
        }


class V31DraftPilotAuditTests(unittest.TestCase):
    def setUp(self):
        self.route = sites()[WP]
        self.sites = sites()
        self.request = [{"site_key": WP}]

    def perform(self, jobs, client=None, query=None):
        calls = []
        def read_only(sql, params):
            self.assertTrue(sql.strip().upper().startswith("SELECT"))
            self.assertNotIn("INSERT", sql.upper())
            self.assertEqual(params[0:2], (WP, self.route["campaign"]))
            calls.append("select")
            return jobs
        client = client or FakeWordPress(self.route)
        result = audit(
            routes=self.sites, requests=self.request,
            query=query or read_only,
            wordpress_client_factory=lambda site_key: client,
        )
        return result, client, calls

    def test_empty_d1_history_does_not_claim_any_verified_draft(self):
        report, client, calls = self.perform([])
        self.assertEqual(report["status"], "NO_USED_JOBS_TO_VERIFY")
        self.assertEqual(report["drafts_verified"], 0)
        self.assertFalse(report["all_used_jobs_verified"])
        self.assertEqual(client.calls, [])
        self.assertEqual(calls, ["select"])
        self.assertEqual(report["cms_writes"], 0)

    def test_d1_used_wordpress_exact_same_sku_hash_and_draft_passes(self):
        report, client, _ = self.perform([used(self.route)])
        self.assertEqual(report["status"], "ALL_USED_DRAFTS_VERIFIED")
        self.assertEqual(report["drafts_verified"], 1)
        self.assertTrue(report["all_used_jobs_verified"])
        self.assertEqual(client.calls, ["settings", "list", "get"])
        self.assertFalse(report["automatic_live_authorized"])

    def test_d1_used_does_not_approve_changed_html(self):
        report, _, _ = self.perform(
            [used(self.route)], FakeWordPress(self.route, content=CONTENT+"altered"))
        self.assertEqual(report["status"], "BLOCKED_RECONCILIATION")
        self.assertEqual(report["reports"][0]["outcomes"],
                         {"CMS_HTML_OR_SKU_CONFLICT": 1})

    def test_d1_used_without_cms_post_requires_operator(self):
        report, _, _ = self.perform(
            [used(self.route)], FakeWordPress(self.route, missing=True))
        self.assertEqual(report["status"], "BLOCKED_RECONCILIATION")
        self.assertEqual(report["drafts_verified"], 0)
        self.assertEqual(report["reports"][0]["outcomes"],
                         {"USED_WITHOUT_CMS_MATCH": 1})

    def test_non_draft_cms_does_not_count_as_verified(self):
        report, _, _ = self.perform(
            [used(self.route)], FakeWordPress(self.route, status="publish"))
        self.assertEqual(report["reports"][0]["outcomes"],
                         {"EXISTING_NON_DRAFT_POST": 1})
        self.assertFalse(report["automatic_live_authorized"])

    def test_missing_title_cannot_be_verified(self):
        report, _, _ = self.perform(
            [used(self.route)], FakeWordPress(self.route, title=""))
        self.assertEqual(report["status"], "BLOCKED_RECONCILIATION")
        self.assertEqual(report["drafts_verified"], 0)

    def test_ready_job_is_not_delivery_evidence(self):
        with self.assertRaisesRegex(DraftPilotAuditError,
                                    "d1_used_job_untrusted"):
            self.perform([used(self.route, status="READY")])

    def test_foreign_campaign_or_site_rejected_before_cms(self):
        for field, value in (("site_key", BLOGGER),
                             ("campaign", "wrongcampaign")):
            with self.subTest(field=field):
                with self.assertRaisesRegex(DraftPilotAuditError,
                                            "d1_used_job_untrusted"):
                    self.perform([used(self.route, **{field:value})])

    def test_incomplete_used_job_history_is_fail_closed(self):
        with self.assertRaisesRegex(DraftPilotAuditError,
                                    "d1_used_inventory_incomplete"):
            self.perform([used(self.route)] * (MAX_USED_JOBS_PER_SITE+1))

    def test_duplicate_fingerprint_is_fail_closed(self):
        with self.assertRaisesRegex(DraftPilotAuditError,
                                    "d1_duplicate_used_fingerprint"):
            self.perform([used(self.route), used(self.route)])

    def test_rejected_blogger_route_cannot_be_audited(self):
        excluded = self.sites["blogger_ar_condicionado_sem_duvidas"]
        with self.assertRaisesRegex(DraftPilotAuditError,
                                    "audit_site_scope_invalid"):
            audit(routes=self.sites,
                  requests=[{"site_key":"blogger_ar_condicionado_sem_duvidas"}],
                  query=lambda sql, params: [])

    def test_no_requests_is_not_a_verified_draft(self):
        report = audit(routes=self.sites, requests=[],
                       query=lambda sql, params: self.fail("unexpected SELECT"))
        self.assertEqual(report["status"], "NO_USED_JOBS_TO_VERIFY")
        self.assertEqual(report["sites_checked"], 0)
        self.assertEqual(report["drafts_verified"], 0)

    def test_blogger_exact_marker_slug_and_hash(self):
        route = self.sites[BLOGGER]
        job = used(route)
        marker = "v31-" + job["fingerprint"][:32]
        service = MagicMock()
        service.blogs.return_value.get.return_value.execute.return_value = {
            "id":route["identifier"]}
        service.posts.return_value.get.return_value.execute.return_value = {
            "id":"4106024906916105222",
            "blog":{"id":route["identifier"]},
            "status":"DRAFT", "labels":[marker],
            "title":"Artigo factual original", "content":CONTENT,
        }
        with patch("affiliate_hub_v31.audit_draft_pilots.blogger.validate_remote_identity",
                   return_value="https://moveisparacadacanto.blogspot.com/"), \
             patch("affiliate_hub_v31.audit_draft_pilots.blogger._list_posts",
                   return_value=[{"id":"4106024906916105222", "labels":[marker]}]):
            self.assertEqual(_blogger_outcome(job, route, service), "DRAFT_VERIFIED")
            report = audit(
                routes=self.sites,
                requests=[{"site_key":BLOGGER}],
                query=lambda sql, params: [job],
                blogger_service_factory=lambda site_key: service,
            )
        self.assertEqual(report["status"], "ALL_USED_DRAFTS_VERIFIED")

    def test_missing_blogger_cms_marker_does_not_retry_post(self):
        route = self.sites[BLOGGER]
        job = used(route)
        service = MagicMock()
        service.blogs.return_value.get.return_value.execute.return_value = {
            "id":route["identifier"]}
        with patch("affiliate_hub_v31.audit_draft_pilots.blogger.validate_remote_identity"), \
             patch("affiliate_hub_v31.audit_draft_pilots.blogger._list_posts",
                   return_value=[]):
            report = audit(
                routes=self.sites,
                requests=[{"site_key":BLOGGER}],
                query=lambda sql, params: [job],
                blogger_service_factory=lambda site_key: service,
            )
        self.assertEqual(report["status"], "BLOCKED_RECONCILIATION")
        self.assertEqual(report["reports"][0]["outcomes"],
                         {"USED_WITHOUT_CMS_MATCH":1})
        self.assertFalse(service.posts.return_value.insert.called)


if __name__ == "__main__":
    unittest.main()
