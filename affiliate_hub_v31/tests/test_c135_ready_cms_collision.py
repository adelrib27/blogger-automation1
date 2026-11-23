"""C135: colisões READY e CMS devem falhar fechadas e jamais gerar permissão."""
from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from affiliate_hub_v31 import ready_cms_collision_audit as audit


WP = {"site_key": "wordpress_casa_decoracao", "platform": "wordpress",
      "identifier": "https://casaedecoracao.radartechbr.com.br/",
      "campaign": "casaedecoracaowp", "publish_enabled": False}
BLOGGER = {"site_key": "blogger_moveis_para_cada_canto", "platform": "blogger",
           "identifier": "1439741542627895062",
           "campaign": "moveisparacadacanto", "publish_enabled": False}
PRODUCT = "shopee:306698991:8503898928"
HTML = f'<article data-v31-product-key="{PRODUCT}">Conteúdo verificado</article>'
FINGERPRINT = "f" * 64


def job(route=WP, content=HTML):
    return {"site_key": route["site_key"], "campaign": route["campaign"],
            "fingerprint": FINGERPRINT, "product_key": PRODUCT,
            "html_sha256": hashlib.sha256(content.encode()).hexdigest(),
            "status": "READY"}


def post(html=HTML, *, status="draft", route=WP, id_=314, slug=None):
    result = {"id": id_, "status": status, "title": {"raw": "Produto exemplo"}}
    if route["platform"] == "wordpress":
        result["content"] = {"raw": html}
        result["slug"] = (slug if slug is not None
                          else "v31-31856a8a43a1-8503898928")
    else:
        result["content"] = html
        result["labels"] = ["v31-" + FINGERPRINT[:32]]
    return result


class ReadOnlyReadyCMSAuditTests(unittest.TestCase):
    def audit(self, route=WP, ready=None, posts=None):
        return audit.audit_ready_jobs(
            route=route,
            ready_jobs=[job(route)] if ready is None else ready,
            cms_posts=[post(route=route)] if posts is None else posts)

    def test_wordpress_exact_html_already_present_is_not_authorization(self):
        result = self.audit()
        self.assertEqual(result["outcomes"], {"IDENTICAL_DRAFT_ALREADY_PRESENT": 1})
        self.assertFalse(result["ready_delivery_authorized"])
        self.assertFalse(result["automatic_live_authorized"])
        self.assertEqual(result["cms_writes"], 0)

    def test_different_html_for_same_sku_is_rejected(self):
        result = self.audit(posts=[post(HTML + "<p>Outro guia</p>")])
        self.assertEqual(result["outcomes"], {"CONFLICTING_DRAFT_HTML": 1})
        self.assertEqual(result["jobs"][0]["cms_ids"], ["314"])

    def test_live_same_sku_is_blocked(self):
        self.assertEqual(self.audit(posts=[post(status="publish")])["outcomes"],
                         {"EXISTING_NON_DRAFT_POST": 1})

    def test_duplicate_cms_posts_are_blocked(self):
        rows = [post(id_=314), post(id_=316)]
        result = self.audit(posts=rows)
        self.assertEqual(result["outcomes"], {"MULTIPLE_CMS_MATCHES": 1})

    def test_conflicting_product_marker_and_slug_is_blocked(self):
        bad = post('<article data-v31-product-key="shopee:1:2"></article>')
        self.assertEqual(self.audit(posts=[bad])["outcomes"],
                         {"CONFLICTING_PRODUCT_IDENTITY": 1})

    def test_conflicting_slug_with_same_product_is_blocked(self):
        bad = post(slug="diferente")
        self.assertEqual(self.audit(posts=[bad])["outcomes"],
                         {"CONFLICTING_SLUG": 1})

    def test_no_match_never_implies_delivery_authorization(self):
        result = self.audit(posts=[post(
            '<article data-v31-product-key="shopee:1:2"></article>',
            slug="outro-artigo")])
        self.assertEqual(result["outcomes"], {"NOT_PRESENT_IN_ACTIVE_HISTORY": 1})
        self.assertFalse(result["ready_delivery_authorized"])

    def test_missing_raw_content_fails_closed(self):
        bad = post()
        bad["content"] = {"rendered": HTML}
        with self.assertRaisesRegex(audit.ReadyCMSAuditError, "cms_raw_history"):
            self.audit(posts=[bad])

    def test_blogger_exact_html_already_present_is_not_authorization(self):
        result = self.audit(route=BLOGGER)
        self.assertEqual(result["outcomes"], {"IDENTICAL_DRAFT_ALREADY_PRESENT": 1})

    def test_blogger_live_marker_detects_status(self):
        result = self.audit(route=BLOGGER, posts=[post(route=BLOGGER,status="live")])
        self.assertEqual(result["outcomes"], {"EXISTING_NON_DRAFT_POST": 1})

    def test_wrong_campaign_fails_closed(self):
        candidate = job()
        candidate["campaign"] = "othercampaign"
        with self.assertRaisesRegex(audit.ReadyCMSAuditError, "ready_job_untrusted"):
            self.audit(ready=[candidate])

    def test_unsafe_route_fails_closed(self):
        with self.assertRaisesRegex(audit.ReadyCMSAuditError, "audit_input_invalid"):
            self.audit(route={**WP, "publish_enabled": True})

    def test_over_limit_fails_closed(self):
        with self.assertRaisesRegex(audit.ReadyCMSAuditError, "audit_input_invalid"):
            self.audit(ready=[job()] * 101)

    def test_duplicate_history_ids_fail_closed(self):
        with self.assertRaisesRegex(audit.ReadyCMSAuditError, "cms_history_duplicate_ids"):
            self.audit(posts=[post(), post()])

    def test_d1_select_only_and_no_cms_mutation(self):
        captured = []
        class FakeD1:
            @classmethod
            def from_environment(cls, *, allow_mutations=False):
                captured.append(allow_mutations)
                return lambda sql, params: [job()]
        with (patch.object(audit, "CloudflareD1HTTPRunner", FakeD1),
              patch.object(audit, "sites", return_value={WP["site_key"]: WP}),
              patch.object(audit, "authenticated_posts", return_value=[post()])):
            report = audit.audit_site(site_key=WP["site_key"])
        self.assertEqual(captured, [False])
        self.assertEqual(report["ready_jobs_checked"], 1)
        self.assertFalse(report["ready_delivery_authorized"])


if __name__ == "__main__":
    unittest.main()
