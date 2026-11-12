"""Recipe boundaries and credential-free cross-job transport."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autoevolution'))
import offline
import transfer
from engine import SafetyStop


class TestOfflineRecipes(unittest.TestCase):
    def build(self, source):
        with patch.object(offline, 'git_blob', return_value=source.encode()), \
             patch.object(offline, 'validate', side_effect=lambda value, root, sha: value):
            return offline.build_candidate(Path('.'), 'a' * 40)

    def test_known_guard_gets_one_line_correction_and_regression(self):
        source = 'def example():\n' + offline.BEFORE + '\n        return False\n'
        result = self.build(source)
        self.assertEqual(result['files'][0]['content'], source.replace(offline.BEFORE, offline.AFTER))
        self.assertEqual(len(result['files']), 2)
        self.assertEqual(result['generator'], 'DETERMINISTIC_REVIEWED_RECIPE')

    def test_already_fixed_is_noop(self):
        self.assertIsNone(self.build(offline.AFTER))

    def test_unknown_source_is_noop(self):
        self.assertIsNone(self.build('different implementation'))

    def test_ambiguous_target_denied(self):
        with self.assertRaises(SafetyStop):
            self.build(offline.BEFORE + '\n' + offline.BEFORE)

    def test_foreign_target_denied_before_git_or_network(self):
        with patch.dict('os.environ', {'GITHUB_REPOSITORY': 'other/repo'}), \
             patch.object(offline.subprocess, 'check_output') as call:
            with self.assertRaises(SafetyStop): offline.main()
            call.assert_not_called()


class TestJobTransport(unittest.TestCase):
    def test_preserves_exact_verified_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = root / 'first', root / 'second'
            first.mkdir()
            raw = '{"content":"acentuação \\n literal"}\n'.encode()
            (first / 'candidate.json').write_bytes(raw)
            (first / 'verification.json').write_bytes(b'{"baseline":"PASS"}\n')
            package = transfer.encode_package(first)
            transfer.decode_package(package, second)
            self.assertEqual((second / 'candidate.json').read_bytes(), raw)
            self.assertEqual((second / 'verification.json').read_bytes(), b'{"baseline":"PASS"}\n')

    def test_extra_paths_rejected(self):
        import base64
        value = base64.b64encode(json.dumps({'../../code.py': 'bad'}).encode()).decode()
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(SafetyStop):
            transfer.decode_package(value, Path(directory))

    def test_size_limit_rejected_before_decoding(self):
        with self.assertRaises(SafetyStop):
            transfer.decode_package('x' * (transfer.MAX_PACKAGE_BYTES * 2 + 1), Path('.'))


if __name__ == '__main__':
    unittest.main()
