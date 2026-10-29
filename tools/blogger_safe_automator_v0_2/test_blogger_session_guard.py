from __future__ import annotations

import unittest

from blogger_session_guard import is_blogger_url


class BloggerSessionGuardTests(unittest.TestCase):
    def test_draft_blogger_panel_is_preserved(self):
        self.assertTrue(
            is_blogger_url("https://draft.blogger.com/blog/settings/1963445282243783455")
        )

    def test_blogger_home_is_recognized(self):
        self.assertTrue(is_blogger_url("https://www.blogger.com/"))

    def test_google_accounts_is_not_blogger(self):
        self.assertFalse(is_blogger_url("https://accounts.google.com/"))

    def test_lookalike_domain_is_not_blogger(self):
        self.assertFalse(is_blogger_url("https://evilblogger.com/"))


if __name__ == "__main__":
    unittest.main()
