#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import browser_provision as bp
from inspect_theme_restore_dialog import (
    CANCEL_RE,
    MORE_ACTIONS_RE,
    RESTORE_RE,
    select_expected_theme_page,
    validate_blog_id,
    validate_restore_evidence,
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

    def test_select_expected_theme_page_prefers_visible_candidate(self):
        expected = "99449222854490000"
        hidden = FakePage(f"https://draft.blogger.com/blog/themes/{expected}", visible=False)
        visible = FakePage(f"https://draft.blogger.com/blog/themes/{expected}?hl=pt-BR", visible=True)
        selected = select_expected_theme_page(FakeContext([visible, hidden]), expected)
        self.assertIs(selected, visible)

    def test_select_expected_theme_page_fails_closed_without_theme_tab(self):
        expected = "99449222854490000"
        context = FakeContext([
            FakePage(f"https://draft.blogger.com/blog/settings/{expected}"),
            FakePage("https://example.com/"),
        ])
        with self.assertRaises(bp.SafeAutomationError):
            select_expected_theme_page(context, expected)

    def test_restore_evidence_does_not_require_role_dialog(self):
        dom = {
            "dialogs": [],
            "restore_evidence": {
                "title_visible": True,
                "explanation_visible": True,
                "cancel_action_visible": True,
                "upload_action_visible": True,
            },
        }
        result = validate_restore_evidence(dom)
        self.assertTrue(all(result.values()))

    def test_restore_evidence_fails_closed_when_upload_action_missing(self):
        dom = {
            "restore_evidence": {
                "title_visible": True,
                "explanation_visible": True,
                "cancel_action_visible": True,
                "upload_action_visible": False,
            },
        }
        with self.assertRaises(bp.SafeAutomationError):
            validate_restore_evidence(dom)

    def test_theme_action_labels_are_strict(self):
        self.assertIsNotNone(MORE_ACTIONS_RE.fullmatch("Mais ações"))
        self.assertIsNotNone(RESTORE_RE.fullmatch("Restaurar"))
        self.assertIsNotNone(CANCEL_RE.fullmatch("CANCELAR"))
        self.assertIsNone(MORE_ACTIONS_RE.fullmatch("Mais ações do tema agora"))
        self.assertIsNone(RESTORE_RE.fullmatch("Restaurar tema agora"))
        self.assertIsNone(CANCEL_RE.fullmatch("Cancelar upload"))


if __name__ == "__main__":
    unittest.main()
