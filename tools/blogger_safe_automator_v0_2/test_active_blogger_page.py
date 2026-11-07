from __future__ import annotations

import unittest

from active_blogger_page import select_active_blogger_page


class FakePage:
    def __init__(self, url: str, visibility: str = "hidden"):
        self.url = url
        self.visibility = visibility

    def evaluate(self, expression: str):
        if expression == "() => document.visibilityState":
            return self.visibility
        raise AssertionError(expression)


class FakeContext:
    def __init__(self, pages):
        self.pages = pages


class ActiveBloggerPageTests(unittest.TestCase):
    def test_prefers_visible_blogger_page(self):
        stale = FakePage("https://draft.blogger.com/blog/settings/111", "hidden")
        active = FakePage("https://draft.blogger.com/blog/settings/222", "visible")
        context = FakeContext([stale, active])
        selected = select_active_blogger_page(context, lambda ctx: ctx.pages[0])
        self.assertIs(selected, active)

    def test_falls_back_to_latest_blogger_page_when_none_visible(self):
        first = FakePage("https://draft.blogger.com/blog/settings/111", "hidden")
        latest = FakePage("https://draft.blogger.com/blog/settings/222", "hidden")
        context = FakeContext([first, latest])
        selected = select_active_blogger_page(context, lambda ctx: ctx.pages[0])
        self.assertIs(selected, latest)

    def test_uses_original_fallback_when_no_blogger_page_exists(self):
        other = FakePage("https://example.com/")
        context = FakeContext([other])
        selected = select_active_blogger_page(context, lambda ctx: ctx.pages[0])
        self.assertIs(selected, other)


if __name__ == "__main__":
    unittest.main()
