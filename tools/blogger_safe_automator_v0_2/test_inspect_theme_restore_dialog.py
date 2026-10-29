#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import browser_provision as bp
from inspect_theme_restore_dialog import validate_blog_id, validate_xml_file


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


if __name__ == "__main__":
    unittest.main()
