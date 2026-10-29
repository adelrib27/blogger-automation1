#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import browser_provision as bp
from inspect_theme_restore_dialog import (
    select_expected_theme_page,
    validate_blog_id,
    validate_xml_file,
)


class FakePage:
    def __init__(self, url: str, visible: bool = True):
        self.url = url
        self.visible = visible

    def evaluate(self, script: str):
        if "document.visibilityState" in script:
            return "visible" if self.visible else "hidden"
        raise AssertionError(f"Unexpected evaluate call: {script}")


class FakeContext:
    def __init__(self, pages):
        self.pages = pages


class ThemeRestoreInspectorTests(unittest.TestCase):
    def test_validate_blog_id_accepts_digits(self):
        self.assertEqual(validate_blog_id("99449222854490000"), "99449222854490000")

    def test_validate_blog_id_rejects_non_digits(self):
        with self.assertRaises(bp.SafeAutomationError):
            validate_blog_id("99449x")

    def test_validate_xml_file_returns_hash_and_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "theme.xml"
            path.write_text("<?xml version='1.0'?><html></html>", encoding="utf-8")
            result = validate_xml_file(str(path), label="Teste")
            self.assertTrue(result["xml_valid"])
            self.assertGreater(result["size_bytes"], 0)
            self.assertEqual(len(result["sha256"]), 64)

    def test_validate_xml_file_rejects_invalid_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.xml"
            path.write_text("<html>", encoding="utf-8")
            with self.assertRaises(bp.SafeAutomationError):
                validate_xml_file(str(path), label="Teste")

    def test_select_expected_theme_page_accepts_plural_themes_route(self):
        expected = "99449222854490000"
        settings = FakePage(f"https://draft.blogger.com/blog/settings/{expected}")
        theme = FakePage(f"https://draft.blogger.com/blog/themes/{expected}?hl=pt-BR")
        other = FakePage("https://draft.blogger.com/blog/themes/1453188702831337099")
        selected = select_expected_theme_page(FakeContext([settings, other, theme]), expected)
        self.assertIs(selected, theme)

    def test_select_expected_theme_page_fails_closed_without_theme_tab(self):
        expected = "99449222854490000"
        context = FakeContext([
            FakePage(f"https://draft.blogger.com/blog/settings/{expected}"),
            FakePage("https://example.com/"),
        ])
        with self.assertRaises(bp.SafeAutomationError):
            select_expected_theme_page(context, expected)


if __name__ == "__main__":
    unittest.main()
