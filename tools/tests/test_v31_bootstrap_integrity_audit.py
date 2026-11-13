"""Hermetic tests for R28 integrity readback; no Windows/Chrome/token needed."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE_FILE = Path(__file__).parents[1] / "v31_bootstrap_integrity_audit.py"
spec = importlib.util.spec_from_file_location("integrity_audit", MODULE_FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture(root):
    tools = root / mod.REL_TOOLS
    tools.mkdir(parents=True, exist_ok=True)
    lines = []
    for index, (var, hashvar, filename) in enumerate(mod.MODULES):
        content = (f"sample-{index}").encode()
        (tools / filename).write_bytes(content)
        lines.append(f"\${var} = Join-Path $Tools '{filename}'")
        lines.append(f"\${hashvar} = '{hashlib.sha256(content).hexdigest()}'")
    boot = root / mod.BOOTSTRAP
    boot.parent.mkdir(parents=True, exist_ok=True)
    boot.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tools, boot


class IntegrityAuditTests(unittest.TestCase):
    def test_original_healthy(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture(root)
            result = mod.audit(root)
            self.assertEqual(result["status"], "BOOTSTRAP_INTEGRITY_OK")
            self.assertTrue(all(x["status"] == "OK" for x in result["files"]))
            self.assertFalse(result["local_files_modified"])

    def test_one_divergent_file_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tools, _ = fixture(root)
            (tools / "v31_master_policy.py").write_text("modified")
            result = mod.audit(root)
            self.assertEqual(result["status"], "BOOTSTRAP_INTEGRITY_BLOCKED")
            self.assertEqual([r["file"] for r in result["files"] if r["status"] == "DIVERGENT"],
                             ["v31_master_policy.py"])

    def test_missing_file_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tools, _ = fixture(root)
            (tools / "local_service_v08.py").unlink()
            result = mod.audit(root)
            self.assertEqual(result["files"][0]["status"], "MISSING")

    def test_altered_bootstrap_target_blocks_not_guesses(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, boot = fixture(root)
            boot.write_text(boot.read_text().replace("'local_service_v08.py'", "'other.py'"))
            with self.assertRaisesRegex(mod.AuditBlocked, "UNRECOGNIZED_TARGET_Runner"):
                mod.audit(root)

    def test_absent_bootstrap_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaisesRegex(mod.AuditBlocked, "BOOTSTRAP_MISSING_OR_SYMLINK"):
                mod.audit(root)

    def test_no_arbitrary_bootstrap_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture(root)
            with self.assertRaisesRegex(mod.AuditBlocked, "BOOTSTRAP_PATH_NOT_APPROVED"):
                mod.audit(root, root / "fake.ps1")

    def test_hash_assignment_tampering_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, boot = fixture(root)
            boot.write_text(boot.read_text().replace("$RunnerHash", "$UnknownHash"))
            with self.assertRaisesRegex(mod.AuditBlocked, "UNRECOGNIZED_HASH_RunnerHash"):
                mod.audit(root)

    def test_symlink_bootstrap_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, boot = fixture(root)
            replacement = boot.with_suffix(".txt")
            boot.rename(replacement)
            try:
                boot.symlink_to(replacement)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(mod.AuditBlocked, "BOOTSTRAP_MISSING_OR_SYMLINK"):
                mod.audit(root)

    def test_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tools, _ = fixture(root)
            p = tools / "local_service_v08.py"
            p.unlink()
            try:
                p.symlink_to(tools / "apply_universal_v31.py")
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            result = mod.audit(root)
            self.assertEqual(result["files"][0]["status"], "SYMLINK_DENIED")


if __name__ == "__main__":
    unittest.main()
