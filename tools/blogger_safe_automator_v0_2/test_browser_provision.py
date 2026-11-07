from __future__ import annotations

import unittest

from browser_provision import (
    SafeAutomationError,
    extract_blog_id_from_url,
    normalize_address,
    sanitize_url,
    validate_cdp_url,
)


class BrowserProvisionTests(unittest.TestCase):
    def test_normalize_blogspot_address(self):
        self.assertEqual(normalize_address("https://Meu-Blog.blogspot.com/"), "meu-blog")

    def test_sanitize_url_removes_query_and_fragment(self):
        self.assertEqual(
            sanitize_url("https://draft.blogger.com/blog/posts/123?x=secret#frag"),
            "https://draft.blogger.com/blog/posts/123",
        )

    def test_local_cdp_is_allowed(self):
        self.assertEqual(
            validate_cdp_url("http://127.0.0.1:9222/"),
            "http://127.0.0.1:9222",
        )

    def test_extract_blog_id_from_panel_url(self):
        self.assertEqual(
            extract_blog_id_from_url("https://draft.blogger.com/blog/posts/1426630233929943394"),
            "1426630233929943394",
        )

    def test_remote_cdp_is_blocked_by_default(self):
        with self.assertRaises(SafeAutomationError):
            validate_cdp_url("http://10.0.0.5:9222")

    def test_cdp_credentials_are_blocked(self):
        with self.assertRaises(SafeAutomationError):
            validate_cdp_url("http://user:pass@127.0.0.1:9222")


if __name__ == "__main__":
    unittest.main()
