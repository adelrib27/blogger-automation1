"""C60 — WordPress REST fake, quota per real owner request, no LIVE."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31 import automatic_wordpress_drafts as m

SITE = "wordpress_oficina_garagem"
HOME = "https://oficina.radartechbr.com.br/"
ROUTE = {"site_key": SITE, "platform": "wordpress",
         "identifier": HOME, "campaign": "oficinawp",
         "publish_enabled": False, "allowed_niches": ["automotivo/acessorios"]}
PRODUCT = "shopee:123:456"
NAME = "Suporte para Celular Automotivo Universal"
LINK = "https://s.shopee.com.br/real-oficina"
REQUEST = {"site_key": SITE, "platform": "wordpress", "topic": "suporte celular",
           "articles": 2, "enabled": True}


def old_post(number):
    return {"id": number, "slug": "original-" + str(number),
            "status": "publish", "link": HOME + "original-" + str(number) + "/",
            "title": {"rendered": "Dicas de organização " + str(number)},
            "content": {"raw": "<p>Artigo existente, sem V31</p>"}}


def paragraphs(**_):
    sentence = ("Para escolher suporte celular, confira as medidas disponíveis, "
                "compatibilidade com o aparelho, forma de fixação e materiais. "
                "Consulte o anúncio para verificar especificações e compare "
                "alternativas conforme suas necessidades e uso diário. ")
    return [sentence * 4] * 7


class Reply:
    def __init__(self, status, data, pages=1):
        self.status_code = status
        self.data = data
        self.headers = {"X-WP-TotalPages": str(pages)}

    def json(self):
        return self.data


class FakeREST:
    def __init__(self, posts=None):
        self.posts = list(posts or [])
        self.calls = []
        self.root = HOME[:-1]
        self.user_id = 9
        self.redirect = False
        self.before_second_history = None
        self.history_reads = 0

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if self.redirect:
            return Reply(302, {})
        if url == HOME + "wp-json/":
            return Reply(200, {"url": self.root})
        if url == HOME + "wp-json/wp/v2/users/me":
            return Reply(200, {"id": self.user_id})
        if url == HOME + "wp-json/wp/v2/posts":
            self.history_reads += 1
            if self.before_second_history and self.history_reads == 2:
                self.posts.append(self.before_second_history)
            return Reply(200, list(self.posts))
        if url.startswith(HOME + "wp-json/wp/v2/posts/"):
            pid = int(url.rsplit("/", 1)[1])
            return Reply(200, next(x for x in self.posts if x["id"] == pid))
        raise AssertionError("unexpected REST url")

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        assert url == HOME + "wp-json/wp/v2/posts"
        body = kwargs["json"]
        assert body["status"] == "draft"
        post = {"id": 901 + len(self.posts), "slug": body["slug"],
                "status": "draft", "link": HOME + body["slug"] + "/",
                "title": {"rendered": body["title"]},
                "content": {"raw": body["content"]}}
        self.posts.append(post)
        return Reply(201, post)


class UniversalWordPressDraftTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dbpath = Path(tmp.name) / "catalog.sqlite3"
        with Catalog(self.dbpath) as cat:
            with cat.db:
                cat.db.execute("""
                INSERT INTO products(product_key,shop_id,item_id,title,
                  description,origin_url,image_url,moderation,
                  moderation_reason,first_source,last_seen_utc)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """, (PRODUCT, "123", "456", NAME, "",
                      "https://shopee.com.br/product/123/456",
                      "https://cf.shopee.com.br/file/real",
                      "eligible", "", "csv", "2026-11-18T00:00:00Z"))
                cat.db.execute("""
                INSERT INTO product_taxonomy
                  (product_key,category,niche,status,reason,version)
                VALUES(?,?,?,?,?,?)
                """, (PRODUCT, "automotivo", "acessorios",
                      "matched", "test", "v31"))
            cat.cache_link(PRODUCT, ROUTE["campaign"], LINK)
        self.registry = patch.object(m, "sites", return_value={SITE: ROUTE})
        self.discovery = patch.object(m, "preview_site_launch", return_value={
            "registered_site": True, "can_publish": False,
            "approved_catalog_candidates": [{
                "product_key": PRODUCT, "title": NAME,
                "affiliate_status": "verified_for_campaign",
                "affiliate_url": LINK}]})
        self.registry.start()
        self.discovery.start()
        self.addCleanup(self.registry.stop)
        self.addCleanup(self.discovery.stop)

    def make_client(self, fake):
        return m.WPClient(ROUTE, ("editor", "this-is-a-test-app-password"),
                          session=fake)

    def run_draft(self, fake, *, execute=False, request=None, writer=paragraphs):
        with Catalog(self.dbpath) as cat:
            return m.draft_next(site_key=SITE, execute=execute, catalog=cat,
                     wp_client=self.make_client(fake), workers_writer=writer,
                     requests=[request or dict(REQUEST)])

    def test_dry_run_uses_real_wp_history_but_does_not_generate_or_post(self):
        rest = FakeREST([old_post(1), old_post(2)])
        def no_ai(**_):
            raise AssertionError("AI called in dry-run")
        r = self.run_draft(rest, writer=no_ai)
        self.assertEqual(r["status"], "READY_FOR_ORIGINAL_DRAFT_REVIEW")
        self.assertEqual(r["draft_creation_calls"], 0)
        self.assertEqual(len([c for c in rest.calls if c[0] == "POST"]), 0)
        self.assertTrue(all(c[2].get("allow_redirects") is False
                            for c in rest.calls))
        self.assertTrue(all(c[2].get("auth") == ("editor", "this-is-a-test-app-password")
                            for c in rest.calls))

    def test_create_one_verified_draft_with_real_photo_campaign_cta_and_posts(self):
        rest = FakeREST([old_post(1), old_post(2)])
        r = self.run_draft(rest, execute=True)
        self.assertEqual(r["status"], "DRAFT_CREATED")
        self.assertEqual((r["draft_creation_calls"], r["publication_calls"]), (1, 0))
        draft = rest.posts[-1]
        self.assertEqual(draft["status"], "draft")
        self.assertTrue(draft["slug"].startswith("v31-"))
        body = draft["content"]["raw"]
        self.assertIn("https://cf.shopee.com.br/file/real", body)
        self.assertIn(LINK, body)
        self.assertIn("Ver produto na Shopee", body)
        self.assertIn('data-v31-request="', body)
        self.assertIn('data-v31-product-key="' + PRODUCT + '"', body)
        self.assertEqual(body.count("<li>"), 2)
        self.assertIn("original-1/", body)
        self.assertIn("original-2/", body)
        self.assertNotIn("<script", body)
        self.assertEqual(len([c for c in rest.calls if c[0] == "POST"]), 1)
        self.assertTrue(any("/posts/" + str(draft["id"]) in c[1]
                            for c in rest.calls if c[0] == "GET"))

    def test_quota_is_per_topic_v31_not_all_legacy_wp_posts(self):
        rest = FakeREST([old_post(i) for i in range(1, 40)])
        request = {**REQUEST, "articles": 1}
        r = self.run_draft(rest, execute=True, request=request)
        self.assertEqual(r["status"], "DRAFT_CREATED")
        r = self.run_draft(rest, execute=True, request=request)
        self.assertEqual(r["status"], "OWNER_QUOTA_REACHED")
        self.assertEqual(len([c for c in rest.calls if c[0] == "POST"]), 1)

    def test_other_post_with_same_product_blocks_repetition(self):
        p = old_post(1)
        p["content"]["raw"] = '<section data-v31-product-key="' + PRODUCT + '">'
        r = self.run_draft(FakeREST([p]))
        self.assertEqual(r["status"], "NO_VERIFIED_CAMPAIGN_PRODUCT_YET")

    def test_never_reuses_link_from_other_campaign(self):
        with Catalog(self.dbpath) as cat:
            with cat.db:
                cat.db.execute("DELETE FROM affiliate_links WHERE campaign=?",
                               (ROUTE["campaign"],))
            plan = m.select_next(cat, site_key=SITE,
                                 request=REQUEST, history=[old_post(1)])
        self.assertEqual(plan["status"], "NO_VERIFIED_CAMPAIGN_PRODUCT_YET")

    def test_remote_identity_and_user_are_verified_before_posts(self):
        rest = FakeREST()
        rest.root = "https://unrelated.example"
        with self.assertRaisesRegex(m.WordPressDraftError, "identity_mismatch"):
            self.run_draft(rest)
        self.assertFalse(any("posts" in call[1] for call in rest.calls))
        rest = FakeREST()
        rest.user_id = None
        with self.assertRaisesRegex(m.WordPressDraftError, "not_authenticated"):
            self.run_draft(rest)

    def test_rest_redirects_fail_closed_even_for_read_requests(self):
        rest = FakeREST()
        rest.redirect = True
        with self.assertRaisesRegex(m.WordPressDraftError, "http_failure"):
            self.run_draft(rest)
        self.assertFalse(any(c[0] == "POST" for c in rest.calls))

    def test_missing_raw_history_rejected_before_ai_or_post(self):
        p = old_post(2)
        p["content"] = {"rendered": "<p>no raw</p>"}
        rest = FakeREST([p])
        with self.assertRaisesRegex(m.WordPressDraftError, "history_incomplete"):
            self.run_draft(rest)
        self.assertFalse(any(c[0] == "POST" for c in rest.calls))

    def test_race_after_generation_blocks_mutation(self):
        rest = FakeREST([old_post(1)])
        tag = m._request_tag(SITE, REQUEST["topic"])
        p = old_post(900)
        p["slug"] = "v31-" + tag + "-someone-else"
        p["content"]["raw"] = '<article data-v31-request="' + tag + '">'
        rest.before_second_history = p
        with self.assertRaisesRegex(m.WordPressDraftError, "race_detected"):
            self.run_draft(rest, execute=True,
                           request={**REQUEST, "articles": 1})
        self.assertFalse(any(c[0] == "POST" for c in rest.calls))

    def test_invalid_ai_and_request_cannot_create_draft(self):
        rest = FakeREST([old_post(1)])
        with self.assertRaisesRegex(m.WordPressDraftError, "original_article_gate"):
            self.run_draft(rest, execute=True, writer=lambda **_: ["curto"] * 7)
        self.assertFalse(any(c[0] == "POST" for c in rest.calls))
        with self.assertRaisesRegex(m.WordPressDraftError, "enabled_owner_request"):
            self.run_draft(rest, execute=True,
                           request={**REQUEST, "enabled": False})

    def test_credentials_are_site_scoped_and_not_in_error(self):
        raw = json.dumps({SITE: {"username": "editor",
                                 "app_password": "valid-app-pass-xyz"}})
        self.assertEqual(m.load_site_credentials(SITE, raw)[0], "editor")
        with self.assertRaisesRegex(m.WordPressDraftError, "credentials_missing"):
            m.load_site_credentials("wordpress_outro", raw)
        with self.assertRaisesRegex(m.WordPressDraftError, "credentials_missing"):
            m.load_site_credentials(SITE, "not a json token valid-app-pass-xyz")

    def test_wordpress_route_cannot_point_to_local_or_other_path(self):
        for identifier in ("http://oficina.radartechbr.com.br/",
                           "https://localhost/", "https://127.0.0.1/",
                           "https://evil.example/not-root/",
                           "https://username:password@evil.example/"):
            with self.subTest(identifier=identifier):
                with self.assertRaises(m.WordPressDraftError):
                    m.home_url({**ROUTE, "identifier": identifier})

    def test_no_wordpress_request_is_safe_noop(self):
        with patch.object(m, "load_requests", return_value=[
             {"site_key": "blogger_real", "platform": "blogger",
              "topic": "abc", "articles": 3, "enabled": True}]):
            with patch("sys.argv", ["automatic_wordpress_drafts"]):
                self.assertEqual(m.main(), 0)


if __name__ == "__main__":
    unittest.main()
