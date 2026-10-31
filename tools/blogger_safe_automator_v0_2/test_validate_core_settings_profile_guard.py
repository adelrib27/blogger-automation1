from __future__ import annotations

import unittest
from unittest.mock import MagicMock

import browser_provision as bp
import validate_core_settings_profile as diag


class ValidateCoreSettingsProfileGuardTests(unittest.TestCase):
    def _page(self, url: str, visible: bool = False):
        page = MagicMock()
        page.url = url
        page.evaluate.return_value = "visible" if visible else "hidden"
        return page

    def test_select_expected_blog_page_ignores_stale_other_blog(self):
        stale = self._page(
            "https://draft.blogger.com/blog/settings/1426630233929943394",
            visible=False,
        )
        expected = self._page(
            "https://draft.blogger.com/blog/settings/99449222854490000?hl=pt-BR",
            visible=True,
        )
        context = MagicMock()
        context.pages = [stale, expected]

        chosen = diag.select_expected_blog_page(context, "99449222854490000")
        self.assertIs(chosen, expected)

    def test_missing_expected_blog_fails_closed(self):
        context = MagicMock()
        context.pages = [
            self._page("https://draft.blogger.com/blog/settings/1426630233929943394")
        ]

        with self.assertRaises(bp.SafeAutomationError):
            diag.select_expected_blog_page(context, "99449222854490000")

    def test_invalid_expected_blog_id_is_rejected(self):
        with self.assertRaises(bp.SafeAutomationError):
            diag.validate_expected_blog_id("99449oops")


if __name__ == "__main__":
    unittest.main()
