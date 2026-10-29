from __future__ import annotations

import unittest

import configure_core_settings as cfg
import settings_dialog_guard as sdg
import local_service_v04  # noqa: F401 - importing applies v0.4 patches


class SettingsDialogGuardTests(unittest.TestCase):
    def test_v04_patches_description_dialog_handler(self):
        self.assertIs(cfg.set_dialog_text, sdg.set_dialog_text)

    def test_v04_patches_timezone_dialog_handler(self):
        self.assertIs(cfg.set_timezone, sdg.set_timezone)


if __name__ == "__main__":
    unittest.main()
