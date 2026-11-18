"""C57 — state-of-work checkpoints survive chat interruption, no secrets."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.continuity_guard import (
    ContinuityGuardError, check_repository,
)


class V31ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        actual=Path(__file__).resolve().parents[2]
        for name in ("V31_CONTINUAR_AQUI.md", "AGENTS.md"):
            shutil.copy2(actual/name, self.root/name)
        folder=self.root/"affiliate_hub_v31"
        folder.mkdir()
        state=json.loads((actual/"affiliate_hub_v31"/
                          "CONTINUIDADE_ESTADO.json").read_text(encoding="utf-8"))
        checkpoint=Path(state["checkpoint_detail"]).name
        for name in ("CONTINUIDADE_ESTADO.json",
                     "CONTINUIDADE_PROTOCOLO.md", checkpoint):
            shutil.copy2(actual/"affiliate_hub_v31"/name,folder/name)
        self.state_path=folder/"CONTINUIDADE_ESTADO.json"

    def _edit(self, operation):
        state=json.loads(self.state_path.read_text(encoding="utf-8"))
        operation(state)
        self.state_path.write_text(
            json.dumps(state,ensure_ascii=False,indent=2),
            encoding="utf-8")

    def test_checkpoint_entrypoint_is_valid_and_can_resume(self):
        result=check_repository(self.root)
        state=json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(result["status"],state["continuity_status"])
        self.assertEqual(result["phase"],state["continuity_protocol_phase"])
        self.assertEqual(result["latest_checkpoint"],state["last_checkpoint_phase"])
        self.assertEqual(result["gate_check"],"PASS")
        self.assertEqual(result["external_mutations"],0)
        self.assertTrue(result["next_safe_step"])

    def test_active_work_and_status_must_match(self):
        self._edit(lambda s:s["active_work"].update(status="BLOQUEADO"))
        with self.assertRaisesRegex(ContinuityGuardError,
                                    "continuity_status_mismatch"):
            check_repository(self.root)

    def test_pointer_must_exist_inside_project(self):
        self._edit(lambda s:s.update(checkpoint_detail="../secret.env"))
        with self.assertRaisesRegex(ContinuityGuardError,
                                    "continuity_checkpoint_not_found"):
            check_repository(self.root)

    def test_previews_need_last_verified_step_and_next_step(self):
        self._edit(lambda s:s["active_work"].update(next_safe_step=""))
        with self.assertRaisesRegex(ContinuityGuardError,
                                    "continuity_active_work_incomplete"):
            check_repository(self.root)

    def test_empty_next_priorities_fail_closed(self):
        self._edit(lambda s:s.update(next_priorities=[]))
        with self.assertRaisesRegex(ContinuityGuardError,
                                    "continuity_missing_next_steps"):
            check_repository(self.root)

    def test_private_token_key_disallowed_in_checkpoint(self):
        self._edit(lambda s:s.update(api_token="FAKE-DO-NOT-USE"))
        with self.assertRaisesRegex(ContinuityGuardError,
                                    "continuity_secret_field_prohibited"):
            check_repository(self.root)

    def test_no_external_writes_on_validation(self):
        before=self.state_path.read_bytes()
        check_repository(self.root)
        after=self.state_path.read_bytes()
        self.assertEqual(before,after)

    def test_legacy_checkpoint_kept_separate(self):
        doc=(self.root/"V31_CONTINUAR_AQUI.md").read_text(encoding="utf-8")
        self.assertIn("CHECKPOINT_ATUAL.md",doc)
        self.assertIn("CONTINUIDADE_ESTADO.json",doc)


if __name__=="__main__":
    unittest.main()
