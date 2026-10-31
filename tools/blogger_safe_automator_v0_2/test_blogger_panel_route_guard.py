#!/usr/bin/env python3
from __future__ import annotations

import unittest

from blogger_panel_route_guard import extract_panel_blog_id


class BloggerPanelRouteGuardTests(unittest.TestCase):
    def test_supported_panel_routes_extract_same_blog_id(self):
        blog_id = "99449222854490000"
        for route in ("themes", "theme", "layout", "pages", "posts", "settings"):
            with self.subTest(route=route):
                self.assertEqual(
                    extract_panel_blog_id(f"https://draft.blogger.com/blog/{route}/{blog_id}?hl=pt-BR"),
                    blog_id,
                )

    def test_unrelated_url_returns_none(self):
        self.assertIsNone(extract_panel_blog_id("https://draft.blogger.com/"))


if __name__ == "__main__":
    unittest.main()
