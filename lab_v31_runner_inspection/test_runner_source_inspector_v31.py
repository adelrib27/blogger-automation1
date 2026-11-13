import hashlib
import tempfile
import unittest
from pathlib import Path

from runner_source_inspector_v31 import InspectionDenied, READ_CONFIRMATION, manifest, read_source


class InspectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.content = "def test():\n    return 1\n"
        (self.root / "browser_provision.py").write_text(self.content, encoding="utf-8")
        self.digest = hashlib.sha256(self.content.encode()).hexdigest()

    def read(self, **kwargs):
        args = dict(name="browser_provision.py", expected_sha256=self.digest,
                    confirm=READ_CONFIRMATION)
        args.update(kwargs)
        return read_source(self.root, **args)

    def test_manifest_contains_metadata_only(self):
        doc = manifest(self.root)
        entry = next(x for x in doc["files"] if x["name"] == "browser_provision.py")
        self.assertEqual(entry["sha256"], self.digest)
        self.assertNotIn("content", entry)
        self.assertEqual(doc["mode"], "READ_ONLY")

    def test_read_specific_sha(self):
        self.assertEqual(self.read()["content"], self.content)

    def test_reject_wrong_confirmation(self):
        with self.assertRaisesRegex(InspectionDenied, "READ_CONFIRMATION_REQUIRED"):
            self.read(confirm="NO")

    def test_reject_stale_sha(self):
        with self.assertRaisesRegex(InspectionDenied, "SOURCE_CHANGED_RECHECK_MANIFEST"):
            self.read(expected_sha256="0" * 64)

    def test_reject_path_traversal(self):
        with self.assertRaisesRegex(InspectionDenied, "SOURCE_NOT_ALLOWLISTED"):
            self.read(name="../.env")

    def test_reject_sensitive_file(self):
        with self.assertRaisesRegex(InspectionDenied, "SOURCE_NOT_ALLOWLISTED"):
            self.read(name="settings.json")

    def test_reject_symlink(self):
        other = self.root / "anything.txt"
        other.write_text(self.content)
        (self.root / "browser_provision.py").unlink()
        try:
            (self.root / "browser_provision.py").symlink_to(other)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unsupported")
        with self.assertRaisesRegex(InspectionDenied, "SYMLINK_NOT_ALLOWED"):
            self.read()

    def test_reject_large_file(self):
        (self.root / "browser_provision.py").write_bytes(b"x" * (128 * 1024 + 1))
        with self.assertRaisesRegex(InspectionDenied, "SOURCE_TOO_LARGE"):
            self.read()

    def test_reject_hardcoded_secret(self):
        source = 'client_secret = "should-not-leak-these-credentials"\n'
        (self.root / "browser_provision.py").write_text(source, encoding="utf-8")
        sha = hashlib.sha256(source.encode()).hexdigest()
        with self.assertRaisesRegex(InspectionDenied, "POSSIBLE_HARDCODED_CREDENTIAL"):
            self.read(expected_sha256=sha)

    def test_reject_email(self):
        source = 'contact_email = "someone@example.net"\n'
        (self.root / "browser_provision.py").write_text(source, encoding="utf-8")
        sha = hashlib.sha256(source.encode()).hexdigest()
        with self.assertRaisesRegex(InspectionDenied, "PERSONAL_DATA_POSSIBLE"):
            self.read(expected_sha256=sha)

    def test_credential_env_name_allowed(self):
        source = 'token_env = "BLOGGER_RUNNER_TOKEN"\n'
        (self.root / "browser_provision.py").write_text(source, encoding="utf-8")
        sha = hashlib.sha256(source.encode()).hexdigest()
        self.assertEqual(self.read(expected_sha256=sha)["content"], source)

    def test_no_created_files_from_read(self):
        before = sorted(p.name for p in self.root.iterdir())
        self.read()
        manifest(self.root)
        self.assertEqual(before, sorted(p.name for p in self.root.iterdir()))


if __name__ == "__main__":
    unittest.main()
