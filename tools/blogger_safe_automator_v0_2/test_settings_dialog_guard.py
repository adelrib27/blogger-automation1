from __future__ import annotations

import unittest
from unittest.mock import patch

import configure_core_settings as cfg
import settings_dialog_guard as sdg
import local_service_v04  # noqa: F401 - importing applies v0.4 patches


class SettingsDialogGuardTests(unittest.TestCase):
    def test_v04_patches_description_dialog_handler(self):
        self.assertIs(cfg.set_dialog_text, sdg.set_dialog_text)

    def test_v04_patches_timezone_dialog_handler(self):
        self.assertIs(cfg.set_timezone, sdg.set_timezone)

    def test_timezone_is_idempotent_when_target_already_selected(self):
        target = "(GMT-03:00) Horário Padrão de Brasília – São Paulo"
        page = object()
        with patch.object(sdg.cfg.core, "row_text", return_value=f"Fuso horário {target}"), patch.object(
            sdg.cfg.core, "click_row_prefix"
        ) as click_row:
            result = sdg.set_timezone(page, target)
        self.assertTrue(result["selected_and_saved"])
        self.assertFalse(result["changed"])
        self.assertEqual(result["dialog_guard"], "already_selected")
        click_row.assert_not_called()


if __name__ == "__main__":
    unittest.main()
