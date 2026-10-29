from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import configure_core_settings as cfg
import settings_dialog_guard as sdg
import local_service_v04  # noqa: F401 - importing applies v0.4 patches


class SettingsDialogGuardTests(unittest.TestCase):
    def test_v04_patches_description_dialog_handler(self):
        self.assertIs(cfg.set_dialog_text, sdg.set_dialog_text)

    def test_v04_patches_timezone_dialog_handler(self):
        self.assertIs(cfg.set_timezone, sdg.set_timezone)

    def test_wait_for_field_by_aria_retries_until_visible(self):
        page = MagicMock()
        field = MagicMock()
        with patch.object(sdg, "_field_by_aria", side_effect=[None, None, field]) as lookup:
            result = sdg._wait_for_field_by_aria(page, ("Descrição",), timeout_ms=500)
        self.assertIs(result, field)
        self.assertEqual(lookup.call_count, 3)
        self.assertEqual(page.wait_for_timeout.call_count, 2)
        page.wait_for_timeout.assert_called_with(100)

    def test_text_setting_is_idempotent_when_page_already_shows_value(self):
        page = MagicMock()
        value = "Blog de teste para validação da automação Blogger."
        with patch.object(sdg, "_field_by_aria", return_value=None), patch.object(
            sdg, "_current_text_setting_matches", return_value=True
        ), patch.object(sdg.cfg.core, "click_row_prefix") as click_row:
            result = sdg.set_dialog_text(page, "Descrição", value, ("Descrição",))
        self.assertFalse(result["changed"])
        self.assertEqual(result["dialog_guard"], "already_selected")
        click_row.assert_not_called()

    def test_open_text_field_with_same_value_uses_cancel_no_write(self):
        page = MagicMock()
        field = MagicMock()
        dialog = MagicMock()
        value = "Ambiente de teste para validar automação segura."
        with patch.object(sdg, "_field_by_aria", return_value=field), patch.object(
            sdg, "_dialog_for_field", return_value=dialog
        ), patch.object(sdg, "_field_value_matches", return_value=True), patch.object(
            sdg, "_click_action_in_dialog"
        ) as click_action:
            result = sdg.set_dialog_text(
                page,
                "Descrição da pesquisa",
                value,
                ("Descrição da pesquisa",),
            )
        click_action.assert_called_once_with(page, dialog, "CANCELAR")
        field.fill.assert_not_called()
        self.assertFalse(result["changed"])
        self.assertEqual(result["dialog_guard"], "open_field_noop")

    def test_text_normalization_handles_nbsp_and_repeated_spacing(self):
        left = "Texto\u00a0de   teste"
        right = "Texto de teste"
        self.assertEqual(sdg._norm_setting_text(left), sdg._norm_setting_text(right))

    def test_timezone_is_idempotent_when_target_already_selected(self):
        target = "(GMT-03:00) Horário Padrão de Brasília – São Paulo"
        page = MagicMock()
        page.get_by_text.return_value.count.return_value = 0
        with patch.object(sdg.cfg.core, "row_text", return_value=f"Fuso horário {target}"), patch.object(
            sdg.cfg.core, "click_row_prefix"
        ) as click_row, patch.object(sdg, "_timezone_dialog", return_value=None):
            result = sdg.set_timezone(page, target)
        self.assertTrue(result["selected_and_saved"])
        self.assertFalse(result["changed"])
        self.assertEqual(result["dialog_guard"], "already_selected")
        click_row.assert_not_called()

    def test_timezone_idempotency_normalizes_spacing_and_dash_variants(self):
        target = "(GMT-03:00) Horário Padrão de Brasília – São Paulo"
        current = "Fuso horário\u00a0 (GMT-03:00) Horário Padrão de Brasília — São   Paulo"
        page = MagicMock()
        page.get_by_text.return_value.count.return_value = 0
        with patch.object(sdg.cfg.core, "row_text", return_value=current):
            self.assertTrue(sdg._current_timezone_matches(page, target))

    def test_dialog_box_key_collapses_same_visual_modal(self):
        dialog_a = MagicMock()
        dialog_b = MagicMock()
        box = {"x": 100.04, "y": 200.06, "width": 400.01, "height": 500.02}
        dialog_a.bounding_box.return_value = box
        dialog_b.bounding_box.return_value = dict(box)
        self.assertEqual(sdg._dialog_box_key(dialog_a), sdg._dialog_box_key(dialog_b))

    def test_selected_timezone_radio_uses_cancel_no_write(self):
        target = "(GMT-03:00) Horário Padrão de Brasília – São Paulo"
        page = MagicMock()
        dialog = MagicMock()
        chosen = MagicMock()
        chosen.get_attribute.return_value = "true"

        with patch.object(sdg, "_timezone_dialog", return_value=dialog), patch.object(
            sdg, "_target_control_in_dialog", return_value=chosen
        ), patch.object(sdg, "_click_action_in_dialog") as click_action, patch.object(
            sdg, "_current_timezone_matches", return_value=True
        ):
            result = sdg.set_timezone(page, target)

        click_action.assert_called_once_with(page, dialog, "CANCELAR")
        chosen.click.assert_not_called()
        self.assertFalse(result["changed"])
        self.assertEqual(result["dialog_guard"], "selected_radio_noop")


if __name__ == "__main__":
    unittest.main()
