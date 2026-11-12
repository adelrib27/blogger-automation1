from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runner"))
import v31_handoff_safe as mod

BLOG_ID = "2228849984262880811"
TITLE = "Ar-Condicionado sem Dúvidas"
URL = "https://ar-condicionado-sem-duvidas.blogspot.com/"
ADDRESS = "ar-condicionado-sem-duvidas"


def state(**overrides):
    x = {
        "schema": "v31-new-blog-checkpoint/v1",
        "status": "PROVISION_V31_PARTIAL_STOP",
        "created": True, "settings_validated": False,
        "theme_install_started": False, "theme_validated": False,
        "resume_attempted": False, "blog_id": BLOG_ID, "title": TITLE,
        "blog_url": URL, "address": ADDRESS, "steps": ["CREATE_BLOG_VALIDATED"],
    }
    x.update(overrides)
    return x


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cp = self.root / "logs" / "provisioning" / "v31" / (ADDRESS + ".json")
        self.cp.parent.mkdir(parents=True)
        self.cp.write_text(json.dumps(state()), encoding="utf8")
        self.settings = Mock(return_value={"status": "SETTINGS_PROFILE_VALIDATED",
                                           "blog_id": BLOG_ID})
        self.theme = Mock(return_value={"status": "V31_R52_APPLIED_AND_PUBLICLY_VALIDATED",
                                        "blog_id": BLOG_ID})
        self.public = Mock(return_value=(200, "<html>" + TITLE + "x" * 900 + "</html>"))
        self.latch_root = self.root / "latches"
        self.latch_root.mkdir()
        self.paths = {name: self.latch_root / name
                      for name in ("latch", "result", "preflight")}
        self.saved = []

    def save(self, path, cp):
        self.saved.append(cp["status"])
        path.write_text(json.dumps(cp), encoding="utf8")

    def attempt(self, **kwargs):
        data = dict(blog_id=BLOG_ID, title=TITLE, url=URL,
                    description="Guia de climatização", search_description="Como escolher",
                    timezone_text="GMT-03:00", confirm=mod.CONFIRM,
                    root=self.root, save=self.save,
                    settings_apply=self.settings, theme_adopt=self.theme,
                    theme_paths=lambda _: self.paths, public_readback=self.public,
                    settings_confirmation="APPLY SETTINGS",
                    theme_confirmation="INSTALL MODEL V31")
        data.update(kwargs)
        return mod.resume_exact(**data)

    def setcp(self, **kwargs):
        self.cp.write_text(json.dumps(state(**kwargs)), encoding="utf8")

    def test_resume_once_with_valid_creation_checkpoint(self):
        result = self.attempt()
        self.assertTrue(result["theme_validated"])
        self.assertEqual(result["publication_status"], "NOT_PUBLISHED")
        self.assertEqual(self.saved, ["RESUME_SETTINGS_IN_PROGRESS",
                                     "SETTINGS_VALIDATED_AWAIT_THEME",
                                     "V31_THEME_VALIDATED_AWAIT_PAGES"])
        cp = json.loads(self.cp.read_text(encoding="utf8"))
        self.assertEqual(cp["theme_authorization"]["blog_id"], BLOG_ID)
        self.assertTrue(cp["resume_attempted"])
        self.settings.assert_called_once()
        self.theme.assert_called_once()

    def test_cannot_restart_successful_resume(self):
        self.attempt()
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()
        self.assertEqual(self.theme.call_count, 1)

    def test_wrong_id_never_calls_seo(self):
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt(blog_id="999999999999999999")
        self.settings.assert_not_called()

    def test_wrong_url_never_calls_seo(self):
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt(url="https://other-blog.blogspot.com/")
        self.settings.assert_not_called()

    def test_wrong_title_never_calls_seo(self):
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt(title="Wrong Blog")
        self.settings.assert_not_called()

    def test_confirmation_mandatory(self):
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt(confirm="PROVISION BLOG V31")
        self.settings.assert_not_called()

    def test_missing_checkpoint_blocks(self):
        self.cp.unlink()
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()

    def test_missing_creation_step_blocks(self):
        self.setcp(steps=[])
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()

    def test_invalid_checkpoint_status_blocks(self):
        self.setcp(status="SETTINGS_VALIDATED_AWAIT_THEME")
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()

    def test_theme_already_started_blocks(self):
        self.setcp(theme_install_started=True)
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()

    def test_existing_latch_blocks(self):
        self.paths["latch"].write_text("STARTED", encoding="utf8")
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()
        self.theme.assert_not_called()

    def test_existing_result_blocks(self):
        self.paths["result"].write_text("DONE", encoding="utf8")
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()

    def test_existing_preflight_blocks(self):
        self.paths["preflight"].write_text("REVIEW", encoding="utf8")
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()

    def test_public_404_blocks(self):
        self.public.return_value = (404, "")
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()
        self.settings.assert_not_called()

    def test_public_wrong_title_blocks(self):
        self.public.return_value = (200, "<html>OTHER" + "x" * 900)
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()

    def test_public_theme_marker_blocks(self):
        self.public.return_value = (200, "<html>" + TITLE + "x" * 900 + "V31_R52</html>")
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()
        self.theme.assert_not_called()

    def test_seo_failure_never_installs_theme(self):
        self.settings.return_value = {"status": "ERROR", "blog_id": BLOG_ID}
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()
        self.theme.assert_not_called()
        cp = json.loads(self.cp.read_text(encoding="utf8"))
        self.assertTrue(cp["resume_attempted"])
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()

    def test_theme_failure_never_retries(self):
        self.theme.side_effect = RuntimeError("UNSAFE")
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()
        self.assertEqual(self.theme.call_count, 1)

    def test_history_never_used_as_authorization(self):
        import inspect
        source = inspect.getsource(mod)
        self.assertNotIn("v31_authorized_targets.json", source)
        self.assertNotIn("create_blog(", source)

    def test_checkpoint_symlink_rejected(self):
        self.cp.unlink()
        target = self.root / "other.json"
        target.write_text(json.dumps(state()), encoding="utf8")
        try:
            self.cp.symlink_to(target)
        except (NotImplementedError, OSError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(mod.HandoffBlocked):
            self.attempt()


if __name__ == "__main__":
    unittest.main(verbosity=2)
