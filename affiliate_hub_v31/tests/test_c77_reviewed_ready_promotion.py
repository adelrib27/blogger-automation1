"""C77 end-to-end SAFE gates: real Catalog SQLite fixture + SEO + exact facts
+ independently signed reviewer + D1 SQL, NO Cloudflare/CMS/network calls."""
import hashlib
import hmac
import json
import sqlite3
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.final_fact_gate import reviewed_text_digest
from affiliate_hub_v31 import reviewed_ready_promotion as promo
from affiliate_hub_v31.d1_universal_ready import UniversalD1ReadyState
from affiliate_hub_v31.tests.test_c71_d1_universal_ready import SqliteQuery
from affiliate_hub_v31.tests.test_c69_universal_evidence_ready import (
    KEYS, TITLES, NOW, HOME, OTHER, ROUTES, package,
)


SITE = "blogger_novo_exemplo"
CAMPAIGN = "exemploblogger"
ARTICLE_URL = HOME + "guia-cadeira-ergonomica/"
TITLE = "Como escolher cadeira ergonômica para seu escritório"
META = ("Entenda como comparar cadeiras ergonômicas para trabalho "
        "considerando dimensões, ajustes, conforto e condições de compra.")
QUERY = "como escolher cadeira ergonomica para trabalhar"
ANGLE = "Comparação das medidas e ajustes do modelo zero"
KEY = b"v31-only-a-synthetic-independent-review-test-key-1234567890"
NONCE = "c77_synthetic_nonce_12345"
IMAGE = "https://cf.shopee.com.br/file/foto-real"
LINK = "https://s.shopee.com.br/CampanhaBlog456"
FACT = "As dimensões são verificadas na ficha externa atual."
BOILER = ("Este artigo contém link de afiliado. Consulte as condições "
          "no anúncio. Ver produto na Shopee")
HEADINGS = (
    "Compare as medidas antes de escolher",
    "Informações de origem para comparar",
    "Conclusão para uma compra planejada",
)


def make_html(image=IMAGE, affiliate=LINK, fact=FACT):
    return (
        "<article>"
        "<h2>" + HEADINGS[0] + "</h2>"
        '<p><span data-v31-fact-id="EVID_0_0">' + fact + "</span></p>"
        "<h2>" + HEADINGS[1] + "</h2>"
        "<p>Este artigo contém link de afiliado. Consulte as condições "
        'no anúncio. <a href="' + affiliate
        + '" rel="nofollow sponsored noopener">Ver produto na Shopee</a></p>'
        '<figure><img src="' + image
        + '" alt="Foto real do produto cadeira ergonômica"></figure>'
        "<h2>" + HEADINGS[2] + "</h2></article>"
    )


HASHES = [reviewed_text_digest(x) for x in (*HEADINGS, BOILER)]


def sign_material(payload):
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")
    return hmac.new(KEY, canonical, hashlib.sha256).hexdigest()


class ReviewedReadyIntegrationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        catalog_path = Path(tmp.name) / "catalog.sqlite3"
        ready_path = Path(tmp.name) / "ready.sqlite3"
        self.catalog = Catalog(catalog_path)
        self.addCleanup(self.catalog.close)
        with self.catalog.db:
            self.catalog.db.execute(
                """INSERT INTO products(
                 product_key,shop_id,item_id,title,description,origin_url,
                 image_url,moderation,moderation_reason,first_source,last_seen_utc
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (KEYS[0], "111", "456", TITLES[0], "",
                 "https://shopee.com.br/product/111/456", IMAGE,
                 "eligible", "", "csv_real", "2026-11-19T12:00:00Z")
            )
            self.catalog.db.execute(
                """INSERT INTO product_taxonomy(
                   product_key,category,niche,status,reason,version
                ) VALUES (?,?,?,?,?,?)""",
                (KEYS[0], "casa", "moveis", "matched", "evidence", "v31")
            )
        self.catalog.cache_link(KEYS[0], CAMPAIGN, LINK)
        self.catalog.cache_link(KEYS[0], "exemplowp",
                                "https://s.shopee.com.br/CampanhaWP456")
        query = SqliteQuery(ready_path)
        self.addCleanup(query.close)
        migration = (Path(__file__).resolve().parents[1]
                     / "migrations" / "c71_universal_ready_d1.sql")
        query.db.executescript(migration.read_text(encoding="utf-8"))
        self.state = UniversalD1ReadyState(query)
        for target in (
            "affiliate_hub_v31.reviewed_ready_promotion.sites",
            "affiliate_hub_v31.d1_universal_ready.sites",
        ):
            pt = patch(target, return_value=ROUTES)
            pt.start()
            self.addCleanup(pt.stop)

    def input(self, **overrides):
        params = {
            "catalog": self.catalog,
            "state": self.state,
            "site_key": SITE, "product_key": KEYS[0],
            "html_content": make_html(),
            "site_url": HOME, "article_url": ARTICLE_URL,
            "article_title": TITLE, "meta_description": META,
            "primary_query": QUERY, "angle": ANGLE,
            "intent": "buying_guide",
            "keyword_evidence": {
                "source": "serp_research", "query": QUERY,
                "observed_utc": "2026-11-19T10:00:00Z",
            },
            "published_posts": [], "cluster_id": "cadeiras-ergonomicas",
            "evidence_package": package(0),
            "used_evidence_ids": ["EVID_0_0"],
            "owner_nonce": NONCE, "now": NOW,
            "independent_review_key": KEY,
        }
        params.update(overrides)
        seo_context = {
            "site_url": params["site_url"],
            "article_url": params["article_url"],
            "title": params["article_title"],
            "meta_description": params["meta_description"],
            "primary_query": params["primary_query"],
            "intent": params["intent"],
            "html_content": params["html_content"],
            "published_posts": params["published_posts"],
            "keyword_evidence": params["keyword_evidence"],
            "cluster_id": params["cluster_id"],
        }
        # A synthetic independent-review service, not model output.
        material = promo.review_payload(
            site_key=SITE, campaign=CAMPAIGN,
            product_key=KEYS[0], site_url=HOME, article_url=ARTICLE_URL,
            article_title=TITLE, primary_query=QUERY, angle=ANGLE,
            html_sha256=hashlib.sha256(make_html().encode()).hexdigest(),
            evidence_sha256=promo._json_sha(package(0)),
            seo_context_sha256=promo._json_sha({
                **seo_context, "html_content": make_html(),
            }),
            reviewed_text_hashes=HASHES,
        )
        params["attestation"] = overrides.get("attestation", {
            "payload": material, "signature": sign_material(material)
        })
        return params

    def test_signed_exact_product_to_ready_once_with_all_gates(self):
        before = self.catalog.stats()
        result = promo.stage_reviewed_ready(**self.input())
        self.assertEqual(result["status"], "READY_RESERVED_FOR_DRAFT_REVIEW")
        self.assertEqual(result["cms_draft_calls"], 0)
        self.assertEqual(result["publication_calls"], 0)
        self.assertFalse(result["live_publication_authorized"])
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 1)
        self.assertEqual(self.catalog.stats(), before)
        # Repeat does not create a duplicate or refresh source timestamp.
        again = promo.stage_reviewed_ready(**self.input())
        self.assertEqual(again["status"], "READY_NOT_RESERVED")
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 1)

    def test_changed_html_without_new_signed_review_fails_closed(self):
        changed = make_html().replace("compra planejada", "oferta imperdível")
        with self.assertRaisesRegex(promo.ReviewedReadyError, "review_attestation"):
            promo.stage_reviewed_ready(**self.input(html_content=changed))
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 0)

    def test_fake_and_cross_campaign_offer_rejected(self):
        for html in (
            make_html(affiliate="https://s.shopee.com.br/CampanhaWP456"),
            make_html(image="https://cf.shopee.com.br/file/outra-foto"),
            make_html().replace("nofollow sponsored", "nofollow"),
        ):
            with self.subTest(html=html[:30]), self.assertRaises(
                promo.ReviewedReadyError
            ):
                promo.stage_reviewed_ready(**self.input(html_content=html))
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 0)

    def test_reviewed_content_cannot_steal_other_site_signature(self):
        other = self.input(site_key="wordpress_novo_exemplo", site_url=OTHER,
                           article_url=OTHER + "guia-cadeira/")
        with self.assertRaises(promo.ReviewedReadyError):
            promo.stage_reviewed_ready(**other)
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 0)

    def test_no_signed_key_bad_signature_or_unreviewed_paragraph_blocks(self):
        for overrides in (
            {"independent_review_key": b"short"},
            {"independent_review_key": b"totally-different-key-material-xyz-123456"},
            {"attestation": {"payload": {}, "signature": "0" * 64}},
        ):
            with self.subTest(overrides=str(list(overrides))), self.assertRaises(
                promo.ReviewedReadyError
            ):
                promo.stage_reviewed_ready(**self.input(**overrides))
        extra = make_html().replace(
            "</article>", "<p>Afirmação adicional não revisada.</p></article>"
        )
        # Even freshly signed HTML is rejected when independent block hash
        # approval is absent, regardless of a model's own quality flag.
        p = self.input(html_content=extra)
        p["attestation"]["payload"]["html_sha256"] = hashlib.sha256(extra.encode()).hexdigest()
        p["attestation"]["payload"]["seo_context_sha256"] = promo._json_sha({
            "site_url": p["site_url"], "article_url": p["article_url"],
            "title": p["article_title"], "meta_description": p["meta_description"],
            "primary_query": p["primary_query"], "intent": p["intent"],
            "html_content": extra, "published_posts": [],
            "keyword_evidence": p["keyword_evidence"],
            "cluster_id": p["cluster_id"],
        })
        p["attestation"]["signature"] = sign_material(p["attestation"]["payload"])
        with self.assertRaisesRegex(promo.ReviewedReadyError, "gate_failed_closed"):
            promo.stage_reviewed_ready(**p)
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 0)

    def test_no_ready_for_expired_source_or_unapproved_sku(self):
        with self.assertRaises(promo.ReviewedReadyError):
            promo.stage_reviewed_ready(**self.input(now=NOW + timedelta(days=9)))
        with self.catalog.db:
            self.catalog.db.execute(
                "UPDATE products SET moderation='review' WHERE product_key=?",
                (KEYS[0],)
            )
        with self.assertRaises(promo.ReviewedReadyError):
            promo.stage_reviewed_ready(**self.input())
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 0)

    def test_no_ready_if_keyword_research_missing(self):
        p = self.input()
        p["keyword_evidence"] = {}
        with self.assertRaises(promo.ReviewedReadyError):
            promo.stage_reviewed_ready(**p)
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 0)

    def test_bad_source_claim_cannot_pass_independent_review(self):
        altered = package(0, authorized=False)
        p = self.input(evidence_package=altered)
        with self.assertRaises(promo.ReviewedReadyError):
            promo.stage_reviewed_ready(**p)
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 0)

    def test_no_writer_live_or_network_invoked_by_module(self):
        from inspect import getsource
        source = getsource(promo)
        self.assertNotIn("create_post(", source)
        self.assertNotIn("publish_post(", source)
        self.assertNotIn("firecrawl.request(", source)


if __name__ == "__main__":
    unittest.main()
