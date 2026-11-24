"""C152: regressões SAFE da colisão legada Blogger + WordPress."""
import unittest

from affiliate_hub_v31.legacy_cms_collision import (
    CMSLegacyCollisionError, audit_candidate_history, normalized,
)

KEY = "shopee:123456:999888"
TITLE = "Pulseira Samsung Galaxy Fit 3 preta: compatibilidade e materiais"


def wp(id=101, title="Guia para caixa de som Bluetooth", body="<p>Sem produto</p>",
       slug="caixa-som-bluetooth", status="publish"):
    return {"id": id, "title": {"raw": title}, "content": {"raw": body},
            "status": status, "slug": slug}


def blog(id="998877", title="Guia para caixa de som Bluetooth",
         body="<p>Sem produto</p>", status="live"):
    return {"id": id, "title": title, "content": body, "status": status}


def check(platform, posts, title=TITLE, key=KEY, slug=None):
    return audit_candidate_history(platform=platform, posts=posts,
                                   product_key=key, article_title=title,
                                   slug=slug)


class LegacyCMSCollisionTests(unittest.TestCase):
    def test_unrelated_wp_clear(self):
        r = check("wordpress", [wp()])
        self.assertEqual(r["status"], "NO_DETECTED_COLLISION")
        self.assertEqual(r["posts_checked"], 1)
        self.assertFalse(r["draft_authorized"])
        self.assertFalse(r["live_authorized"])

    def test_unrelated_blogger_clear(self):
        self.assertEqual(check("blogger", [blog()])["status"], "NO_DETECTED_COLLISION")

    def test_empty_history_is_not_cms_permission(self):
        r = check("wordpress", [])
        self.assertEqual(r["posts_checked"], 0)
        self.assertFalse(r["draft_authorized"])

    def test_exact_wp_sku_published_blocks(self):
        r = check("wordpress", [wp(body="<div data-v31-product-key='"+KEY+"'></div>")])
        self.assertEqual(r["collisions"][0]["reason"], "IDENTICAL_PRODUCT_SKU_OR_URL")

    def test_exact_wp_sku_draft_blocks(self):
        r = check("wordpress", [wp(status="draft", body="<p>"+KEY+"</p>")])
        self.assertEqual(r["status"], "REVIEW_REQUIRED")

    def test_exact_blogger_sku_blocks(self):
        r = check("blogger", [blog(body="<div>"+KEY+"</div>", status="draft")])
        self.assertEqual(r["status"], "REVIEW_REQUIRED")

    def test_shopee_product_path_identity(self):
        body = '<a href="https://shopee.com.br/product/123456/999888">produto</a>'
        r = check("wordpress", [wp(body=body)])
        self.assertEqual(r["collisions"][0]["reason"], "IDENTICAL_PRODUCT_SKU_OR_URL")

    def test_shopee_legacy_i_path_identity(self):
        body = '<a href="https://shopee.com.br/xyz-i.123456.999888">produto</a>'
        r = check("wordpress", [wp(body=body)])
        self.assertEqual(r["status"], "REVIEW_REQUIRED")

    def test_shopee_query_identity(self):
        body = '<a href="https://shopee.com.br/a?shopid=123456&amp;itemid=999888">produto</a>'
        r = check("wordpress", [wp(body=body)])
        self.assertEqual(r["status"], "REVIEW_REQUIRED")

    def test_other_shop_same_item_is_not_sku_duplicate(self):
        body = "<p>shopee:888888:999888</p>"
        self.assertEqual(check("wordpress", [wp(body=body)])["status"], "NO_DETECTED_COLLISION")

    def test_exact_slug_blocks(self):
        r = check("wordpress", [wp(slug="v31-abc-1")], slug="v31-abc-1")
        self.assertEqual(r["collisions"][0]["reason"], "IDENTICAL_SLUG")

    def test_same_title_with_accents_blocks(self):
        r = check("wordpress", [wp(title="PULSEIRA SAMSUNG GALAXY FIT 3 PRETA: COMPATIBILIDADE E MATERIAIS")])
        self.assertEqual(r["collisions"][0]["reason"], "IDENTICAL_TITLE")

    def test_near_topic_model_overlap_requires_review(self):
        title = "Pulseira Samsung Galaxy Fit 3 preta e materiais"
        r = check("wordpress", [wp(title="Pulseira Samsung Galaxy Fit 3 metal e materiais")],
                  title=title)
        self.assertEqual(r["status"], "REVIEW_REQUIRED")

    def test_variant_redmi_active_vs_lite_not_conflated(self):
        title = "Pulseira Redmi Watch 5 Active compatibilidade"
        prior = wp(title="Pulseira Redmi Watch 5 Lite compatibilidade")
        self.assertEqual(check("wordpress", [prior], title=title)["status"],
                         "NO_DETECTED_COLLISION")

    def test_distinct_sku_and_category_not_collision(self):
        title = "Smartwatch W99+ Plus: conferir os recursos"
        r = check("wordpress", [wp(title="Smartwatch e frequência cardíaca: o que verificar")],
                  title=title)
        self.assertEqual(r["status"], "NO_DETECTED_COLLISION")

    def test_two_real_statuses_in_one_audit(self):
        r = check("wordpress", [wp(1, title=TITLE, status="publish"),
                                 wp(2, title="Nada a ver", status="draft")])
        self.assertEqual(r["posts_checked"], 2)
        self.assertEqual([x["cms_id"] for x in r["collisions"]], ["1"])

    def test_missing_content_fail_closed(self):
        with self.assertRaises(CMSLegacyCollisionError):
            check("wordpress", [{"id": 2, "title": {"raw": "titulo"},
                                 "status": "publish", "slug": "x"}])

    def test_rendered_only_wp_fail_closed(self):
        with self.assertRaises(CMSLegacyCollisionError):
            check("wordpress", [wp(body="").__class__(
                id=2, title={"rendered": "Titulo"}, content={"rendered": "Conteudo"},
                status="publish", slug="x")])

    def test_missing_slug_fail_closed(self):
        p = wp()
        p.pop("slug")
        with self.assertRaises(CMSLegacyCollisionError):
            check("wordpress", [p])

    def test_duplicate_ids_fail_closed(self):
        with self.assertRaises(CMSLegacyCollisionError):
            check("wordpress", [wp(), wp()])

    def test_untrusted_status_fail_closed(self):
        with self.assertRaises(CMSLegacyCollisionError):
            check("wordpress", [wp(status="trash")])

    def test_invalid_site_platform_fail_closed(self):
        with self.assertRaises(CMSLegacyCollisionError):
            check("pinterest", [wp()])

    def test_invalid_product_key_fail_closed(self):
        with self.assertRaises(CMSLegacyCollisionError):
            check("wordpress", [], key="123")

    def test_no_mixing_other_site_history(self):
        other_site = [wp(title=TITLE)]
        self.assertEqual(check("wordpress", [])["status"], "NO_DETECTED_COLLISION")
        self.assertEqual(check("wordpress", other_site)["status"], "REVIEW_REQUIRED")

    def test_normalization_does_not_erase_model_digits(self):
        self.assertIn("3", normalized("Samsung Galaxy Fit 3"))


if __name__ == "__main__":
    unittest.main()
