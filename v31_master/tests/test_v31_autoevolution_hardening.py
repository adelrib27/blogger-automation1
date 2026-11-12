"""Security and lifecycle regression cases, all offline and credential-free."""
import io
import json
import os
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autoevolution'))
import engine
import knowledge
import candidate
import propose
import publish_candidate
import verify_candidate
from test_v31_autoevolution_knowledge import raw, report


class TestHistory(unittest.TestCase):
    def test_rerun_retains_failed_attempt_and_latest_success(self):
        first = knowledge.update_knowledge(None, report(raw(100001, 'failure')))
        rerun = raw(100001, 'success'); rerun['run_attempt'] = 2
        updated = knowledge.update_knowledge(first, report(rerun))
        self.assertEqual(updated['total_distinct_completed_runs'], 1)
        self.assertEqual(len(updated['observed']), 2)
        self.assertEqual(updated['cumulative_failures_by_layer'], {})
        self.assertEqual(updated['cumulative_successes_by_layer']['SHOPEE_PIPELINE'], 1)

    def test_legacy_unknown_attempt_is_not_fabricated(self):
        prior = knowledge.update_knowledge(None, report(raw(100001, 'failure')))
        prior['schema'] = knowledge.LEGACY_SCHEMA
        del prior['observed'][0]['run_attempt']
        rerun = raw(100001, 'success'); rerun['run_attempt'] = 2
        updated = knowledge.update_knowledge(prior, report(rerun))
        self.assertEqual(updated['legacy_attempt_unknown_count'], 1)
        self.assertEqual(updated['total_distinct_completed_runs'], 1)

    def test_old_snapshot_never_overwrites_later_attempt(self):
        rerun = raw(100001, 'success'); rerun['run_attempt'] = 2
        prior = knowledge.update_knowledge(None, report(rerun))
        result = knowledge.update_knowledge(prior, report(raw(100001, 'failure')))
        self.assertEqual(result['cumulative_failures_by_layer'], {})

    def test_invalid_attempt_rejected(self):
        for value in (True, 0, -1, '2'):
            item = raw(100001, 'failure'); item['run_attempt'] = value
            self.assertIsNone(engine.valid_run(item, engine.ALLOWED_REPO))

    def test_lowercase_self_events_excluded(self):
        result = report(raw(100001, 'failure', name='V31 jarvis candidato'))
        self.assertEqual(result['observed_runs'], 0)

    def test_same_snapshot_conflict_rejected(self):
        with self.assertRaises(engine.SafetyStop):
            report(raw(100001, 'success'), raw(100001, 'failure'))

    def test_pagination_collects_more_than_first_page(self):
        pages = [[raw(100000+i, 'failure') for i in range(100)], [raw(200000, 'success')]]
        responses = []
        for page in pages:
            response = MagicMock()
            response.__enter__.return_value = response
            response.status = 200
            response.read.return_value = json.dumps({'workflow_runs': page}).encode()
            responses.append(response)
        with patch.object(engine.urllib.request, 'urlopen', side_effect=responses) as request:
            self.assertEqual(len(engine.github_runs(engine.ALLOWED_REPO, token='test-only')), 101)
            self.assertEqual(request.call_count, 2)
            self.assertIn('page=2', request.call_args[0][0].full_url)

    def test_collection_does_not_claim_complete_history(self):
        self.assertFalse(report(raw(100001, 'success'))['coverage']['complete_history_claimed'])

    def test_report_symlink_escape_denied(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            root = Path(first)
            (root / 'v31_master/autoevolution').mkdir(parents=True)
            (root / 'v31_master/autoevolution/reports').symlink_to(second, target_is_directory=True)
            with self.assertRaises(engine.SafetyStop):
                engine.output_path_guard('v31_master/autoevolution/reports/123456.json', root)


class TestCandidates(unittest.TestCase):
    def setUp(self):
        self.sha = 'a' * 40
        self.original = b'VALUE = 1\n'
        self.value = {'schema': 'v31-candidate/v1', 'base_sha': self.sha,
                      'hypothesis': 'Evidence-backed bug', 'expected_improvement': 'Regression fixed',
                      'files': [{'path': sorted(candidate.SOURCE_PATHS)[0],
                                 'before_sha256': candidate.digest(self.original), 'content': 'VALUE = 2\n'},
                                {'path': candidate.regression_path(self.sha), 'before_sha256': None,
                                 'content': 'import unittest\n'}]}

    def validate(self, value):
        with patch.object(candidate, 'git_blob', return_value=self.original), \
             patch.object(candidate.subprocess, 'run') as check:
            check.return_value.returncode = 1
            return candidate.validate(value, Path('.'), self.sha)

    def test_valid_source_with_new_regression(self):
        self.assertEqual(self.validate(self.value), self.value)

    def test_protected_paths_never_accepted(self):
        for path in ['AGENTS.md', '.github/workflows/live.yml', '../escape.py',
                     'v31_master/autoevolution/candidate.py', 'v31_master/tests/test_r57_store_policy.py']:
            value = deepcopy(self.value); value['files'][0]['path'] = path
            with self.assertRaises(engine.SafetyStop): self.validate(value)

    def test_stale_base_denied(self):
        self.value['base_sha'] = 'b' * 40
        with self.assertRaises(engine.SafetyStop): self.validate(self.value)

    def test_source_hash_mismatch_denied(self):
        self.value['files'][0]['before_sha256'] = 'b' * 64
        with self.assertRaises(engine.SafetyStop): self.validate(self.value)

    def test_noop_denied(self):
        self.value['files'][0]['content'] = self.original.decode()
        with self.assertRaises(engine.SafetyStop): self.validate(self.value)

    def test_without_regression_denied(self):
        self.value['files'].pop()
        with self.assertRaises(engine.SafetyStop): self.validate(self.value)

    def test_existing_tests_cannot_be_overwritten(self):
        with patch.object(candidate, 'git_blob', return_value=self.original), \
             patch.object(candidate.subprocess, 'run') as check:
            check.return_value.returncode = 0
            with self.assertRaises(engine.SafetyStop):
                candidate.validate(self.value, Path('.'), self.sha)

    def test_duplicate_paths_denied(self):
        self.value['files'].append(self.value['files'][0])
        with self.assertRaises(engine.SafetyStop): self.validate(self.value)

    def test_oversized_proposal_denied(self):
        self.value['files'][0]['content'] = 'x' * 200_000
        with self.assertRaises(engine.SafetyStop): self.validate(self.value)

    def test_materialization_symlink_denied(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            root = Path(first)
            (root / 'v31_master').symlink_to(second, target_is_directory=True)
            with self.assertRaises(engine.SafetyStop): candidate.materialize(self.value, root)

    def test_failed_or_swapped_verification_denied(self):
        with self.assertRaises(engine.SafetyStop):
            publish_candidate.verification_guard({'baseline': 'PASS'}, b'{}', self.sha)

    def test_no_api_call_without_dedicated_configuration(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True), \
             patch.object(propose, 'request_candidate') as call:
            with patch.object(propose, 'Path', side_effect=lambda p: Path(folder) / p):
                self.assertEqual(propose.main(), 0)
            call.assert_not_called()
            self.assertIn('BLOCKED_MODEL_CONFIGURATION', (Path(folder)/'autoevolution-output/status.json').read_text())

    def test_sandbox_command_has_no_network_or_secrets(self):
        captured = []
        def run(args, **kwargs):
            captured.extend(args)
            kwargs['stdout'].write(b'Ran 1 test\nOK\n')
            return MagicMock(returncode=0)
        with patch.object(verify_candidate.subprocess, 'run', side_effect=run):
            self.assertEqual(verify_candidate.container_test(Path('/fixture'), 'test_*.py'), 0)
        self.assertIn('--network=none', captured)
        self.assertIn('--read-only', captured)
        self.assertIn('--cap-drop=ALL', captured)
        self.assertFalse(any('TOKEN' in x or 'SECRET' in x or '.git' in x for x in captured))

    def test_import_error_is_not_a_reproduced_bug(self):
        def run(args, **kwargs):
            kwargs['stdout'].write(b'Ran 1 test\nERROR: failed import\nFAILED\n')
            return MagicMock(returncode=1)
        with patch.object(verify_candidate.subprocess, 'run', side_effect=run):
            with self.assertRaises(engine.SafetyStop):
                verify_candidate.container_test(Path('/fixture'), Path(candidate.regression_path(self.sha)).name)

    def test_publish_main_denied_before_network(self):
        with patch.dict(os.environ, {'GITHUB_REPOSITORY':engine.ALLOWED_REPO, 'GITHUB_REF_NAME':'main'}), \
             patch.object(publish_candidate, 'api') as call:
            with self.assertRaises(engine.SafetyStop): publish_candidate.main()
            call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
