from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import browser_provision as bp
import validate_blog_structure as vbs


class ValidateBlogStructureTests(unittest.TestCase):
    def test_target_url_is_bound_to_expected_blog(self):
        self.assertEqual(
            vbs.target_url("themes", "1453188702831337099"),
            "https://draft.blogger.com/blog/themes/1453188702831337099",
        )

    def test_target_url_rejects_unknown_route(self):
        with self.assertRaises(bp.SafeAutomationError):
            vbs.target_url("settings", "1453188702831337099")

    def test_assert_expected_blog_blocks_mismatch(self):
        page = MagicMock()
        with patch.object(bp, "extract_current_blog_id", return_value="999"):
            with self.assertRaises(bp.SafeAutomationError):
                vbs.assert_expected_blog(page, "1453188702831337099")

    def test_assert_expected_blog_accepts_exact_match(self):
        page = MagicMock()
        with patch.object(bp, "extract_current_blog_id", return_value="1453188702831337099"):
            vbs.assert_expected_blog(page, "1453188702831337099")


if __name__ == "__main__":
    unittest.main()
