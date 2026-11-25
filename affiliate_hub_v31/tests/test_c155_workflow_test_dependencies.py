"""Prevent the C154 missing-signature-dependency regression in V31 jobs."""
import re
import unittest
from pathlib import Path


class WorkflowDependencyTests(unittest.TestCase):
    def test_full_suite_jobs_install_signature_dependency_before_tests(self):
        workflows = Path(__file__).resolve().parents[2] / ".github" / "workflows"
        self.assertTrue(workflows.is_dir())
        suite = re.compile(r"python\s+-m\s+unittest\s+discover\s+-s\s+affiliate_hub_v31/tests")
        install = re.compile(r"pip\s+install[^\n]*cryptography")
        job_start = re.compile(r"(?m)^  [a-zA-Z0-9_-]+:\s*$")
        checked = 0
        for path in sorted(workflows.glob("*v31*.yml")):
            doc = path.read_text(encoding="utf-8")
            if not suite.search(doc):
                continue
            self.assertIn("\njobs:", doc, path.name)
            jobs = doc.split("\njobs:", 1)[1]
            for block in job_start.split(jobs):
                for match in suite.finditer(block):
                    checked += 1
                    with self.subTest(workflow=path.name):
                        self.assertIsNotNone(
                            install.search(block[:match.start()]),
                            "install cryptography in the same job before full suite"
                        )
        self.assertGreater(checked, 0)
