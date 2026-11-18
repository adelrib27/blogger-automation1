"""C51 verifies dynamic Blogger ownership without a hardcoded ID list.

These are purely offline contract tests. They do NOT claim the Windows
Runner version 0.9-v31-r52-candidate has been updated.
"""
import unittest
from lab_v31_runner_target_auth.authorization_v31 import (
    TargetAuthorizationError, authorize_theme_target,
)

BLOG = {
    "id": "1439741542627895062",
    "name": "Móveis para Cada Canto",
    "url": "https://moveisparacadacanto.blogspot.com/",
}
DASHBOARD = "https://draft.blogger.com/blog/posts/1439741542627895062"


class DynamicBloggerTargetTests(unittest.TestCase):
    def authorize(self, **changes):
        args = {
            "expected_blog_id": BLOG["id"],
            "expected_title": BLOG["name"],
            "expected_url": BLOG["url"],
            "authenticated_account_inventory": [BLOG],
            "observed_active_panel_url": DASHBOARD,
        }
        args.update(changes)
        return authorize_theme_target(**args)

    def test_new_furniture_blog_accepted_without_static_allowlist(self):
        approved = self.authorize()
        self.assertEqual(approved.blog_id, BLOG["id"])
        self.assertEqual(approved.title, BLOG["name"])
        self.assertEqual(approved.url, BLOG["url"])
        self.assertEqual(
            approved.source, "VERIFIED_AUTHENTICATED_BLOGGER_INVENTORY")

    def test_other_future_owned_blog_with_unforeseen_id(self):
        new_blog = {
            "id": "98765432101234567",
            "name": "O Blog Que Ainda Não Existia",
            "url": "https://novo-assunto-futuro.blogspot.com/",
        }
        approved=self.authorize(
            expected_blog_id=new_blog["id"],
            expected_title=new_blog["name"],
            expected_url=new_blog["url"],
            observed_active_panel_url=(
                "https://www.blogger.com/blog/themes/" + new_blog["id"]),
            authenticated_account_inventory=[BLOG, new_blog],
        )
        self.assertEqual(approved.blog_id, new_blog["id"])

    def test_unowned_blog_fails_closed(self):
        with self.assertRaisesRegex(TargetAuthorizationError,
                                    "blog_not_uniquely_owned"):
            self.authorize(authenticated_account_inventory=[])

    def test_duplicate_inventory_identity_fails_closed(self):
        with self.assertRaisesRegex(TargetAuthorizationError,
                                    "blog_not_uniquely_owned"):
            self.authorize(authenticated_account_inventory=[BLOG, BLOG])

    def test_current_tab_must_match_target(self):
        with self.assertRaisesRegex(TargetAuthorizationError,
                                    "active_panel_blog_mismatch"):
            self.authorize(
                observed_active_panel_url=(
                    "https://draft.blogger.com/blog/posts/4739187376492839837"))

    def test_expected_url_must_match_verified_account(self):
        with self.assertRaisesRegex(TargetAuthorizationError,
                                    "owned_blog_identity_mismatch"):
            self.authorize(
                expected_url="https://outro-blog.blogspot.com/")

    def test_expected_title_must_match_verified_account(self):
        with self.assertRaisesRegex(TargetAuthorizationError,
                                    "owned_blog_identity_mismatch"):
            self.authorize(expected_title="Outro blog")

    def test_session_inventory_cannot_be_accepted_if_missing(self):
        for data in (None, {}, "fake"):
            with self.subTest(data=data):
                with self.assertRaisesRegex(TargetAuthorizationError,
                                            "authenticated_inventory_unavailable"):
                    self.authorize(authenticated_account_inventory=data)

    def test_login_panel_hostname_cannot_be_spoofed(self):
        for url in (
            "http://draft.blogger.com/blog/posts/" + BLOG["id"],
            "https://draft.blogger.com.evil.test/blog/posts/" + BLOG["id"],
            "https://not-blogger.com/blog/posts/" + BLOG["id"],
        ):
            with self.subTest(url=url):
                with self.assertRaisesRegex(TargetAuthorizationError,
                                            "invalid_active_blogger_page"):
                    self.authorize(observed_active_panel_url=url)

    def test_protection_against_bad_request_id_and_url(self):
        with self.assertRaisesRegex(TargetAuthorizationError, "invalid_blog_id"):
            self.authorize(expected_blog_id="https://blogger.com/blog")
        with self.assertRaisesRegex(TargetAuthorizationError, "invalid_blog_host"):
            self.authorize(expected_url="https://localhost/")
        with self.assertRaisesRegex(TargetAuthorizationError, "invalid_blog_url"):
            self.authorize(expected_url="http://moveisparacadacanto.blogspot.com/")

    def test_verified_blog_identity_mismatch_fails_closed(self):
        bad = {**BLOG, "url": "https://outra-loja.blogspot.com/"}
        with self.assertRaisesRegex(TargetAuthorizationError,
                                    "owned_blog_identity_mismatch"):
            self.authorize(authenticated_account_inventory=[bad])

    def test_unknown_custom_domain_can_work_with_ownership_evidence(self):
        custom = {
            "id": BLOG["id"], "name": BLOG["name"],
            "url": "https://www.moveisparacadacanto.example/"
        }
        a = self.authorize(
            expected_url=custom["url"],
            authenticated_account_inventory=[custom],
        )
        self.assertEqual(a.url, custom["url"])


if __name__ == "__main__":
    unittest.main()
