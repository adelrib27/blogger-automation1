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
from unittest.mock import Mock, patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.final_fact_gate import reviewed_text_digest
from affiliate_hub_v31 import reviewed_ready_promotion as promo
from affiliate_hub_v31 import reviewed_draft_delivery as delivery
from affiliate_hub_v31 import independent_review
from affiliate_hub_v31.review_signatures import approval_receipt, payload_digest, sign_release
from affiliate_hub_v31.d1_universal_ready import UniversalD1ReadyState
from affiliate_hub_v31.private_ready_envelope import ImmutablePrivateReadyEnvelope
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


class ConditionalMemoryBackend:
    def __init__(self):
        self.objects = {}

    def put_if_absent(self, key, body):
        if key in self.objects:
            return False
        self.objects[key] = body
        return True

    def get(self, key):
        return self.objects.get(key)


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
            "affiliate_hub_v31.private_ready_envelope.sites",
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

    def test_envelope_then_ready_with_exact_html_and_idempotent_replay(self):
        backend = ConditionalMemoryBackend()
        envelope = ImmutablePrivateReadyEnvelope(backend=backend)
        params = self.input(envelope=envelope)
        result = promo.stage_reviewed_ready(**params)
        self.assertEqual(result["status"], "READY_RESERVED_FOR_DRAFT_REVIEW")
        stored = envelope.load(site_key=SITE, campaign=CAMPAIGN,
                               html_sha256=result["html_sha256"],
                               independent_review_key=KEY)
        self.assertEqual(stored["html_content"], params["html_content"])
        replay = promo.stage_reviewed_ready(**params)
        self.assertEqual(replay["status"], "READY_ALREADY_STAGED")
        self.assertEqual(replay["fingerprint"], result["fingerprint"])
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 1)
        self.assertEqual(len(backend.objects), 1)

    def test_envelope_failure_and_signed_gate_failure_create_no_ready(self):
        backend = ConditionalMemoryBackend()
        envelope = ImmutablePrivateReadyEnvelope(backend=backend)
        with self.assertRaises(promo.ReviewedReadyError):
            promo.stage_reviewed_ready(**self.input(envelope=envelope,
                                                    html_content=make_html() + " "))
        self.assertEqual(backend.objects, {})
        with patch.object(backend, "get", return_value=b"untrusted"):
            with self.assertRaises(promo.ReviewedReadyError):
                promo.stage_reviewed_ready(**self.input(envelope=envelope))
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 0)

    def test_recovery_after_envelope_created_and_d1_response_lost(self):
        backend = ConditionalMemoryBackend()
        params = self.input(envelope=ImmutablePrivateReadyEnvelope(backend=backend))
        reserve = self.state.reserve_ready

        def lose_response(**kwargs):
            reserve(**kwargs)
            raise promo.D1SafeError("synthetic_response_loss")

        with patch.object(self.state, "reserve_ready", side_effect=lose_response):
            with self.assertRaises(promo.ReviewedReadyError):
                promo.stage_reviewed_ready(**params)
        result = promo.stage_reviewed_ready(**params)
        self.assertEqual(result["status"], "READY_ALREADY_STAGED")
        self.assertEqual(len(backend.objects), 1)
        self.assertEqual(self.state.count_ready(site_key=SITE, campaign=CAMPAIGN), 1)

    def test_blogger_timeout_after_post_reconciles_exact_draft_without_repost(self):
        service = Mock()
        routes = {SITE: {**ROUTES[SITE], "identifier": "123456789012"}}
        service.blogs().get().execute.return_value = {
            "id": "123456789012", "url": HOME,
        }
        posts = service.posts()
        envelope = ImmutablePrivateReadyEnvelope(backend=ConditionalMemoryBackend())
        params = self.input(envelope=envelope)
        ready = promo.stage_reviewed_ready(**params)
        marker = "v31-" + ready["fingerprint"][:32]
        draft = {"id": "2026", "blog": {"id": "123456789012"},
                 "status": "DRAFT", "labels": [marker], "title": TITLE,
                 "content": params["html_content"]}
        posts.get().execute.return_value = draft
        posts.list().execute.return_value = {"items": []}
        posts.insert().execute.side_effect = TimeoutError()
        posts.insert.reset_mock()

        with patch.object(delivery, "sites", return_value=routes), patch.object(
            delivery.time, "time", return_value=NOW.timestamp(),
        ):
            kwargs = {"site_key": SITE, "fingerprint": ready["fingerprint"],
                      "state": self.state, "envelope": envelope,
                      "independent_review_key": KEY, "blogger_service": service}
            with self.assertRaisesRegex(delivery.ReviewedDraftError, "unverified"):
                delivery.deliver_reviewed_draft(**kwargs)
            self.assertEqual(delivery.deliver_reviewed_draft(**kwargs)["status"],
                             "DRAFT_RECONCILIATION_REQUIRED")
            posts.list.side_effect = lambda **q: Mock(**{
                "execute.return_value": {"items": [draft] if q["status"] == ["DRAFT"] else []},
            })
            result = delivery.deliver_reviewed_draft(**kwargs)
            self.assertEqual(result["status"], "DRAFT_VERIFIED")
            self.assertEqual(result["draft_id"], "2026")
            self.assertEqual(posts.insert.call_count, 1)
            self.assertTrue(posts.insert.call_args.kwargs["isDraft"])
            self.assertEqual(posts.insert.call_args.kwargs["body"]["content"],
                             params["html_content"])

    def test_wordpress_checks_raw_html_and_never_reposts_a_used_job(self):
        wp_site = "wordpress_novo_exemplo"
        wp_campaign = "exemplowp"
        content = make_html(affiliate="https://s.shopee.com.br/CampanhaWP456").replace(
            "<article>", f'<article data-v31-product-key="{KEYS[0]}">')
        params = self.input(site_key=wp_site, site_url=OTHER,
                            article_url=OTHER + "guia-cadeira/", html_content=content)
        payload = params["attestation"]["payload"]
        seo = {k: params[k] for k in ("site_url", "article_url", "meta_description",
               "primary_query", "intent", "html_content", "published_posts",
               "keyword_evidence", "cluster_id")}
        payload.update(site_key=wp_site, campaign=wp_campaign, site_url=OTHER,
                       article_url=params["article_url"],
                       html_sha256=hashlib.sha256(content.encode()).hexdigest(),
                       seo_context_sha256=promo._json_sha({**seo, "title": TITLE}))
        params["attestation"]["signature"] = sign_material(payload)
        envelope = ImmutablePrivateReadyEnvelope(backend=ConditionalMemoryBackend())
        ready = promo.stage_reviewed_ready(**params, envelope=envelope)
        client = Mock()
        client.site_settings.return_value = {"url": OTHER}
        client.list_posts.return_value = []
        slug = delivery.wordpress._product_slug(wp_site, KEYS[0])
        draft = {"id": 303, "slug": slug, "status": "draft",
                 "title": {"raw": TITLE}, "content": {"raw": content + " "}}
        client.create_draft.return_value = {"id": 303, "status": "draft"}
        client.get_post.return_value = draft
        kwargs = {"site_key": wp_site, "fingerprint": ready["fingerprint"],
                  "state": self.state, "envelope": envelope,
                  "independent_review_key": KEY, "wordpress_client": client}
        with patch.object(delivery, "sites", return_value=ROUTES), patch.object(
            delivery.time, "time", return_value=NOW.timestamp(),
        ):
            with self.assertRaisesRegex(delivery.ReviewedDraftError, "readback_mismatch"):
                delivery.deliver_reviewed_draft(**kwargs)
            draft["content"]["raw"] = content
            client.list_posts.return_value = [draft]
            self.assertEqual(delivery.deliver_reviewed_draft(**kwargs)["status"],
                             "DRAFT_VERIFIED")
            client.create_draft.assert_called_once_with(title=TITLE, slug=slug,
                                                        content=content)

    def test_review_signs_exact_approved_candidate_and_writer_uses_only_public_key(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        params = self.input()
        article = {field: params[field] for field in independent_review.ARTICLE_FIELDS}
        private = Ed25519PrivateKey.generate()
        public_key = private.public_key().public_bytes_raw().hex()
        raw = json.dumps(article, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual(independent_review.decode_candidate(raw, digest=digest), article)
        with self.assertRaises(independent_review.IndependentReviewError):
            independent_review.decode_candidate(raw + b" ", digest=digest)
        with patch.object(independent_review, "sites", return_value=ROUTES):
            payload = independent_review.prepare_review_payload(
                article=article, catalog=self.catalog, now=NOW)
        receipt = approval_receipt(candidate_sha256=digest, payload_sha256=payload_digest(payload),
                                   key=KEY)
        signature = sign_release(receipt, private_key=private.private_bytes_raw().hex())
        attestation = {"payload": payload, "signature": receipt["signature"],
                       "candidate_sha256": digest}
        backend = ConditionalMemoryBackend()
        envelope = ImmutablePrivateReadyEnvelope(backend=backend)
        ready = promo.stage_reviewed_ready(
            **{**params, "attestation": attestation, "independent_review_key": None},
            envelope=envelope,
            release_signature=signature, release_public_key=public_key,
        )
        saved = envelope.load(site_key=SITE, campaign=CAMPAIGN,
                              html_sha256=ready["html_sha256"], release_public_key=public_key)
        self.assertEqual(saved["html_content"], article["html_content"])
        data = json.loads(backend.objects[saved["object_key"]])
        data["attestation"]["signature"] = "0" * 64
        backend.objects[saved["object_key"]] = json.dumps(
            data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "private_envelope_integrity"):
            envelope.load(site_key=SITE, campaign=CAMPAIGN,
                          html_sha256=ready["html_sha256"], release_public_key=public_key)

    def test_protected_review_requires_actual_approval_and_exact_workflow_inputs(self):
        from io import BytesIO

        digest = "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            event.write_text(json.dumps({"inputs": {"site_key": SITE, "candidate_digest": digest}}))
            env = {"GITHUB_REPOSITORY": independent_review.REPOSITORY,
                   "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "workflow_dispatch",
                   "GITHUB_RUN_ID": "123", "V31_ACTIONS_READ_TOKEN": "synthetic-test",
                   "V31_PROTECTED_REVIEWER": "approved-user", "GITHUB_EVENT_PATH": str(event)}
            with patch.object(independent_review, "build_opener") as opener:
                endpoint = opener.return_value
                endpoint.open.return_value = BytesIO(b"[]")
                with self.assertRaisesRegex(ValueError, "approval_missing"):
                    independent_review.require_independent_approval(env, site_key=SITE, digest=digest)
                endpoint.open.side_effect = lambda *a, **kw: BytesIO(json.dumps([{
                    "environments": [{"name": independent_review.REVIEW_ENVIRONMENT}],
                    "state": "approved", "user": {"login": "approved-user"},
                }]).encode())
                with self.assertRaises(ValueError):
                    independent_review.require_independent_approval(env, site_key=SITE, digest="b"*64)
                self.assertEqual(independent_review.require_independent_approval(
                    env, site_key=SITE, digest=digest), "approved-user")

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

    def test_wordpress_cannot_use_a_foreign_seo_home_even_when_signed(self):
        foreign = self.input(site_key="wordpress_novo_exemplo",
                             site_url=HOME, article_url=ARTICLE_URL)
        with self.assertRaisesRegex(
            promo.ReviewedReadyError, "wordpress_site_origin_mismatch"
        ):
            promo.stage_reviewed_ready(**foreign)
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
