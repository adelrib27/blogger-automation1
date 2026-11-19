"""C65: LIVE só com owner approval exato, payload imutável e readback."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31 import manual_live_release as live

PRODUCT = "shopee:12345678:87654321"
LINK = "https://s.shopee.com.br/Validated_Casa123"
IMAGE = "https://cf.shopee.com.br/file/sku-casa-real"
WP_KEY = "wordpress_casa_decoracao"
WP_URL = "https://casaedecoracao.radartechbr.com.br/"
WP_ROUTE = {
    "site_key": WP_KEY, "platform": "wordpress", "identifier": WP_URL,
    "campaign": "casaedecoracaowp", "allowed_niches": ["casa/decoracao"],
    "publish_enabled": False,
}
BLOG_KEY = "blogger_moveis_para_cada_canto"
BLOG_URL = "https://moveisparacadacanto.blogspot.com/"
BLOG_ROUTE = {
    "site_key": BLOG_KEY, "platform": "blogger",
    "identifier": "1439741542627895062",
    "campaign": "moveisparacadacanto",
    "allowed_niches": ["casa/decoracao"], "publish_enabled": False,
}


def article():
    para = (
        "Para escolher um vaso decorativo, observe as medidas da sala, "
        "o local disponível e a facilidade de limpeza. Antes de decidir, "
        "compare as especificações verificadas na página do vendedor e "
        "não confunda imagens ilustrativas com medidas confirmadas. "
        "Verifique o material e a estabilidade descritos no anúncio. "
    )
    body = "".join(
        f"<h2>Critério de escolha {i}</h2><p>"
        + para + f"Considere o espaço do ambiente na etapa {i}.</p>"
        for i in range(1, 9)
    )
    return (
        '<article lang="pt-BR">' + body +
        '<section data-v31-product-key="' + PRODUCT + '">'
        '<img src="' + IMAGE + '" alt="Foto do produto">'
        '<a href="' + LINK + '" rel="nofollow sponsored noopener">'
        'Ver produto na Shopee</a>'
        '<p>Transparência: este artigo contém link de afiliado. '
        'Podemos receber comissão por compras elegíveis.</p></section>'
        '</article>'
    )


class FakeWP:
    def __init__(self, content=None):
        self.post = {
            "id": 303, "status": "draft",
            "title": {"raw": "Guia de compra: vaso decorativo para sua sala"},
            "slug": "v31-test", "content": {"raw": content or article()},
        }
        self.writes = []
        self.url = WP_URL
    def site_settings(self):
        return {"url": self.url}
    def get_post(self, post_id):
        assert post_id == 303
        return {**self.post, "content": dict(self.post["content"])}
    def _call(self, method, path, body):
        self.writes.append((method, path, body))
        if method == "POST" and body == {"status": "publish"}:
            self.post["status"] = "publish"
        return dict(self.post)


class LiveGateTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        db = self.root / "catalog.sqlite3"
        with Catalog(db) as cat:
            with cat.db:
                cat.db.execute("""
                    INSERT INTO products
                    (product_key,shop_id,item_id,title,description,origin_url,
                    image_url,moderation,moderation_reason,first_source,last_seen_utc)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """, (PRODUCT, "12345678", "87654321",
                       "Vaso Decorativo para Sala em Cerâmica", "",
                       "https://shopee.com.br/product/12345678/87654321",
                       IMAGE, "eligible", "", "feed", "2026-11-18T00:00:00Z"))
                cat.db.execute("""
                    INSERT INTO product_taxonomy
                    (product_key,category,niche,status,reason,version)
                    VALUES(?,?,?,?,?,?)
                """, (PRODUCT, "casa", "decoracao", "matched", "fixture", "v31"))
            cat.cache_link(PRODUCT, WP_ROUTE["campaign"], LINK)
            cat.cache_link(PRODUCT, BLOG_ROUTE["campaign"], LINK)
        self.catalog = Catalog(db)
        self.addCleanup(self.catalog.close)
        guard = patch.object(live, "sites", return_value={
            WP_KEY: WP_ROUTE, BLOG_KEY: BLOG_ROUTE,
        })
        guard.start()
        self.addCleanup(guard.stop)
        self.approvals = self.root / "approvals"
        self.approvals.mkdir()

    def approve(self, site=WP_KEY, post_id="303", content=None,
                sha_override=None, **changes):
        route = WP_ROUTE if site == WP_KEY else BLOG_ROUTE
        a = {
            "site_key": site, "platform": route["platform"],
            "post_id": post_id,
            "content_sha256": sha_override or hashlib.sha256(
                ("Guia de compra: vaso decorativo para sua sala" + "\n" +
                 (content or article())).encode()).hexdigest(),
            "approved_utc": "2026-11-18T12:00:00Z",
            "owner_authorized": True, "editorial_reviewed": True,
            "commercial_reviewed": True,
        } | changes
        live.approval_path(site, post_id, self.approvals).write_text(
            json.dumps(a), encoding="utf-8"
        )

    def test_readonly_wp_preview_no_approval_no_post(self):
        wp = FakeWP()
        result = live.preview_or_publish(
            site_key=WP_KEY, post_id="303", catalog=self.catalog,
            wp_client=wp, approval_directory=self.approvals)
        self.assertEqual(result["status"], "AWAITING_OWNER_APPROVAL")
        self.assertEqual(result["publication_calls"], 0)
        self.assertEqual(result["content_sha256"],
                         hashlib.sha256((
                             "Guia de compra: vaso decorativo para sua sala" +
                             "\n" + article()).encode()).hexdigest())
        self.assertEqual(wp.writes, [])

    def test_missing_owner_approval_fails_before_wp_post(self):
        wp = FakeWP()
        with self.assertRaisesRegex(live.LiveReleaseError, "approval_missing"):
            live.preview_or_publish(
                site_key=WP_KEY, post_id="303", catalog=self.catalog,
                wp_client=wp, approval_directory=self.approvals,
                execute=True, confirm="PUBLISH:" + WP_KEY + ":303")
        self.assertEqual(wp.writes, [])

    def test_mismatched_wordpress_site_identity_blocks_before_post(self):
        self.approve()
        wp=FakeWP()
        wp.url="https://wrong-wordpress.example/"
        with self.assertRaisesRegex(live.LiveReleaseError,
                                    "release_wordpress_site_identity_mismatch"):
            live.preview_or_publish(
                site_key=WP_KEY, post_id="303", catalog=self.catalog,
                wp_client=wp, approval_directory=self.approvals,
                execute=True, confirm="PUBLISH:" + WP_KEY + ":303")
        self.assertEqual(wp.writes, [])

    def test_title_change_invalidates_content_approval_even_if_body_same(self):
        self.approve()
        wp=FakeWP()
        wp.post["title"]["raw"]="Guia revisado para vaso decorativo em casa"
        with self.assertRaisesRegex(live.LiveReleaseError,
                                    "content_changed_after_approval"):
            live.preview_or_publish(
                site_key=WP_KEY, post_id="303", catalog=self.catalog,
                wp_client=wp, approval_directory=self.approvals,
                execute=True, confirm="PUBLISH:" + WP_KEY + ":303")
        self.assertEqual(wp.writes, [])

    def test_no_exact_confirmation_never_publishes(self):
        self.approve()
        wp = FakeWP()
        with self.assertRaisesRegex(live.LiveReleaseError, "confirmation_required"):
            live.preview_or_publish(
                site_key=WP_KEY, post_id="303", catalog=self.catalog,
                wp_client=wp, approval_directory=self.approvals,
                execute=True)
        self.assertEqual(wp.writes, [])

    def test_changed_body_after_review_never_publishes(self):
        self.approve(sha_override="0"*64)
        wp = FakeWP()
        with self.assertRaisesRegex(live.LiveReleaseError,
                                    "content_changed_after_approval"):
            live.preview_or_publish(
                site_key=WP_KEY, post_id="303", catalog=self.catalog,
                wp_client=wp, approval_directory=self.approvals,
                execute=True, confirm="PUBLISH:" + WP_KEY + ":303")
        self.assertEqual(wp.writes, [])

    def test_exact_approval_and_confirmation_publish_only_one_post(self):
        self.approve()
        wp = FakeWP()
        result = live.preview_or_publish(
            site_key=WP_KEY, post_id="303", catalog=self.catalog,
            wp_client=wp, approval_directory=self.approvals,
            execute=True, confirm="PUBLISH:" + WP_KEY + ":303")
        self.assertEqual(result["status"], "LIVE_CONFIRMED")
        self.assertEqual(result["publication_calls"], 1)
        self.assertEqual(wp.writes, [
            ("POST", "/wp-json/wp/v2/posts/303", {"status": "publish"})
        ])
        with self.assertRaisesRegex(live.LiveReleaseError, "not_draft"):
            live.preview_or_publish(
                site_key=WP_KEY, post_id="303", catalog=self.catalog,
                wp_client=wp, approval_directory=self.approvals,
                execute=True, confirm="PUBLISH:" + WP_KEY + ":303")
        self.assertEqual(len(wp.writes), 1)

    def test_quality_gate_blocks_unverified_claim_before_live(self):
        corrupted = article().replace(
            "Verifique o material", "Materiais resistentes a bactérias. Verifique o material"
        )
        self.approve(content=corrupted)
        wp = FakeWP(content=corrupted)
        with self.assertRaisesRegex(live.LiveReleaseError,
                                    "editorial_quality_not_approved"):
            live.preview_or_publish(
                site_key=WP_KEY, post_id="303", catalog=self.catalog,
                wp_client=wp, approval_directory=self.approvals,
                execute=True, confirm="PUBLISH:" + WP_KEY + ":303")
        self.assertEqual(wp.writes, [])

    def test_wrong_product_photo_or_affiliate_blocks(self):
        for changed in (
            article().replace(IMAGE, "https://cf.shopee.com.br/file/other"),
            article().replace(LINK, "https://s.shopee.com.br/othercampaign"),
        ):
            with self.subTest(changed=changed[-80:]):
                wp = FakeWP(content=changed)
                with self.assertRaises(live.LiveReleaseError):
                    live.preview_or_publish(
                        site_key=WP_KEY, post_id="303",
                        catalog=self.catalog, wp_client=wp,
                        approval_directory=self.approvals)
                self.assertEqual(wp.writes, [])

    def test_blogger_one_post_live_after_matching_approval(self):
        self.approve(site=BLOG_KEY, post_id="9871")
        b = Mock()
        data = {
            "id": "9871", "status": "draft",
            "title": "Guia de compra: vaso decorativo para sua sala",
            "content": article(),
        }
        b.blogs.return_value.get.return_value.execute.return_value = {
            "id": BLOG_ROUTE["identifier"], "url": BLOG_URL,
        }
        b.posts.return_value.get.return_value.execute.side_effect = lambda: dict(data)
        def publish_once():
            data["status"] = "live"
            return dict(data)
        b.posts.return_value.publish.return_value.execute.side_effect = publish_once
        result = live.preview_or_publish(
            site_key=BLOG_KEY, post_id="9871", catalog=self.catalog,
            blogger_service=b, approval_directory=self.approvals,
            execute=True, confirm="PUBLISH:" + BLOG_KEY + ":9871")
        self.assertEqual(result["status"], "LIVE_CONFIRMED")
        self.assertEqual(b.posts.return_value.publish.call_count, 1)
        args = b.posts.return_value.publish.call_args.kwargs
        self.assertEqual(args["blogId"], BLOG_ROUTE["identifier"])
        self.assertEqual(args["postId"], "9871")

    def test_cross_route_id_and_invalid_manifest_block(self):
        self.approve(site=BLOG_KEY, post_id="9871")
        wp = FakeWP()
        with self.assertRaisesRegex(live.LiveReleaseError, "approval_missing"):
            live.preview_or_publish(
                site_key=WP_KEY, post_id="303", catalog=self.catalog,
                wp_client=wp, approval_directory=self.approvals,
                execute=True, confirm="PUBLISH:" + WP_KEY + ":303")
        self.approve(owner_authorized=False)
        with self.assertRaisesRegex(live.LiveReleaseError, "approval_invalid"):
            live.preview_or_publish(
                site_key=WP_KEY, post_id="303", catalog=self.catalog,
                wp_client=wp, approval_directory=self.approvals,
                execute=True, confirm="PUBLISH:" + WP_KEY + ":303")
        self.assertEqual(wp.writes, [])

if __name__ == "__main__":
    unittest.main()
