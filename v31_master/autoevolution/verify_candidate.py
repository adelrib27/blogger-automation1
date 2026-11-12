#!/usr/bin/env python3
"""Run baseline, red regression and green suite in credential-free containers."""
from __future__ import annotations
import io
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path
from candidate import digest, materialize, validate, regression_path
from engine import SafetyStop

IMAGE = 'python:3.12-slim'


def container_test(root: Path, pattern: str) -> int:
    command = [
        'docker', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=ALL',
        '--security-opt=no-new-privileges', '--pids-limit=128', '--memory=512m',
        '--cpus=1', '--user=65534:65534', '--tmpfs=/tmp:rw,noexec,nosuid,size=64m',
        '-e', 'PYTHONDONTWRITEBYTECODE=1', '-v', str(root) + ':/repo:ro', '-w', '/repo',
        IMAGE, 'python', '-m', 'unittest', 'discover', '-s', 'v31_master/tests', '-p', pattern,
    ]
    # No output from untrusted code is interpreted as commands or published as evidence.
    with tempfile.TemporaryFile() as output:
        try:
            result = subprocess.run(command, stdout=output, stderr=output, timeout=180)
        except subprocess.TimeoutExpired:
            raise SafetyStop('SANDBOX_TIMEOUT') from None
        output.seek(0)
        text = output.read(1_000_000).decode(errors='replace')
    if 'Ran 0 tests' in text or 'Ran ' not in text:
        raise SafetyStop('TESTS_DID_NOT_RUN')
    if result.returncode not in (0, 1):
        raise SafetyStop('SANDBOX_INFRASTRUCTURE_FAILURE')
    # An import/syntax error must not be accepted as the required red regression.
    if pattern.startswith('test_autoevolution_candidate_') and result.returncode == 1:
        if 'FAIL:' not in text or 'ERROR:' in text:
            raise SafetyStop('REGRESSION_NOT_AN_ASSERTION_FAILURE')
    return result.returncode


def verify(root: Path, candidate_path: Path, output: Path) -> dict:
    raw = candidate_path.read_bytes()
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    candidate = validate(json.loads(raw), root, sha)
    subprocess.run(['docker', 'pull', IMAGE], check=True, stdout=subprocess.DEVNULL)
    archive = subprocess.check_output(['git', 'archive', sha], cwd=root)
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        temp_root.chmod(0o755)
        baseline, changed = temp_root / 'baseline', temp_root / 'candidate'
        for target in (baseline, changed):
            target.mkdir(mode=0o755)
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(target, filter='data')
        if container_test(baseline, 'test_*.py') != 0:
            raise SafetyStop('BASELINE_FAILED')
        materialize(candidate, baseline, tests_only=True)
        if container_test(baseline, Path(regression_path(sha)).name) != 1:
            raise SafetyStop('NO_REPRODUCED_REGRESSION')
        materialize(candidate, changed)
        if container_test(changed, 'test_*.py') != 0:
            raise SafetyStop('CANDIDATE_FAILED')
    result = {'schema': 'v31-verification/v1', 'base_sha': sha,
              'candidate_sha256': digest(raw), 'baseline': 'PASS',
              'regression_before': 'FAIL_EXPECTED', 'candidate_suite': 'PASS',
              'production_writes': False, 'network_in_sandbox': False}
    output.write_text(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    out = Path('autoevolution-output')
    try:
        verify(Path.cwd(), out / 'candidate.json', out / 'verification.json')
        print('CANDIDATE_VERIFIED_IN_NETWORKLESS_SANDBOX')
    except Exception as exc:
        (out / 'verification-failure.json').write_text(json.dumps({
            'status': 'BLOCKED', 'reason_type': type(exc).__name__, 'production_writes': False}))
        print('CANDIDATE_BLOCKED_' + type(exc).__name__)
        raise SystemExit(2)
