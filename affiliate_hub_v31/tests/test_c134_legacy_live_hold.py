"""C134 SAFE: regressões do bloqueio LIVE de dois writers legados.

Mantém intactos os workflows de DRAFT do V31 e os acionamentos manuais
independentes; zero I/O remoto e nenhuma operação de CMS.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2] / ".github" / "workflows"


class LegacyLiveHoldTests(unittest.TestCase):
    def _content(self, filename):
        return (ROOT / filename).read_text(encoding="utf-8")

    def _assert_job_guard(self, contents, job):
        expr = rf"(?m)^  {re.escape(job)}:\n(?:    (?!if:)[^\n]*\n)*    if: >-\n      false &&\n"
        self.assertRegex(contents, expr)

    def test_casa_scheduled_writer_and_discovery_both_fail_closed(self):
        s = self._content("casa_editorial_generate_schedule.yml")
        self._assert_job_guard(s, "v31_casa_discovery")
        self._assert_job_guard(s, "autonomo")
        self.assertIn('CASA_LIVE_PUBLISH_ENABLED: "false"', s)
        self.assertIn("CASA_WORDPRESS_STATUS: draft", s)

    def test_oficina_scheduled_writer_and_discovery_both_fail_closed(self):
        s = self._content("oficina_editorial_autonomous.yml")
        self._assert_job_guard(s, "v31_oficina_discovery")
        self._assert_job_guard(s, "publicar-um-slot")
        self.assertIn('OFICINA_LIVE_PUBLISH_ENABLED: "false"', s)
        self.assertIn('OFICINA_WORDPRESS_STATUS: "draft"', s)

    def test_universal_live_still_gated_by_explicit_policy(self):
        s = self._content("v31_autonomous_draft_scheduler.yml")
        self.assertIn("vars.V31_AUTOLIVE_ACTIVE == 'true'", s)
        self.assertIn("environment: v31-autonomous-live", s)
        self.assertIn("V31_AUTO_LIVE_APPROVED_POLICY_SHA256", s)

    def test_radar_legacy_writer_remains_disabled(self):
        s = self._content("radar_editorial_vnext_autonomous.yml")
        self.assertRegex(s, r"(?m)^  autonomo:\n(?:    [^\n]*\n)*    if: \$\{\{ false \}\}")
        self.assertIn('RADAR_LIVE_PUBLISH_ENABLED: "false"', s)


if __name__ == "__main__":
    unittest.main()
