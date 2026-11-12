#!/usr/bin/env python3
"""Trusted candidate envelope validation. Never imports candidate source."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from pathlib import Path
from engine import SafetyStop

SOURCE_PATHS = frozenset({
    'v31_master/store_stock_commission_safe.py',
    'v31_master/shopee_r2_safe.py',
})
def regression_path(base_sha: str) -> str:
    return 'v31_master/tests/test_autoevolution_candidate_' + base_sha[:12] + '.py'
MAX_BYTES = 160_000


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(root: Path, sha: str, path: str) -> bytes:
    return subprocess.check_output(['git', 'show', f'{sha}:{path}'], cwd=root)


def validate(candidate: object, root: Path, base_sha: str) -> dict:
    if not isinstance(candidate, dict) or not re.fullmatch(r'[0-9a-f]{40}', base_sha):
        raise SafetyStop('INVALID_CANDIDATE')
    if candidate.get('schema') != 'v31-candidate/v1' or candidate.get('base_sha') != base_sha:
        raise SafetyStop('STALE_OR_INVALID_CANDIDATE')
    if len(json.dumps(candidate).encode()) > MAX_BYTES:
        raise SafetyStop('CANDIDATE_TOO_LARGE')
    for key in ('hypothesis', 'expected_improvement'):
        if not isinstance(candidate.get(key), str) or not 1 <= len(candidate[key]) <= 2000:
            raise SafetyStop('MISSING_EXPERIMENT_RATIONALE')
    test_path = regression_path(base_sha)
    files = candidate.get('files')
    if not isinstance(files, list) or not 2 <= len(files) <= 3:
        raise SafetyStop('INVALID_FILE_COUNT')
    seen = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise SafetyStop('INVALID_FILE')
        path, content = entry.get('path'), entry.get('content')
        if not isinstance(path, str) or path not in SOURCE_PATHS | {test_path} or path in seen:
            raise SafetyStop('PROTECTED_OR_DUPLICATE_PATH')
        seen.add(path)
        if not isinstance(content, str) or not content.strip() or len(content.encode()) > 60_000:
            raise SafetyStop('INVALID_SOURCE_SIZE')
        if path == test_path:
            if entry.get('before_sha256') is not None:
                raise SafetyStop('TEST_MUST_BE_NEW')
            exists = subprocess.run(['git', 'cat-file', '-e', f'{base_sha}:{path}'],
                                    cwd=root, capture_output=True).returncode == 0
            if exists:
                raise SafetyStop('REGRESSION_PATH_ALREADY_EXISTS')
        else:
            before = git_blob(root, base_sha, path)
            if entry.get('before_sha256') != digest(before):
                raise SafetyStop('SOURCE_BASE_MISMATCH')
            if before == content.encode():
                raise SafetyStop('NO_OP_SOURCE_CHANGE')
        # Parsing happens in the networkless sandbox, never execute/import here.
    if test_path not in seen or not seen & SOURCE_PATHS:
        raise SafetyStop('SOURCE_AND_REGRESSION_REQUIRED')
    return candidate


def materialize(candidate: dict, destination: Path, *, tests_only=False) -> None:
    """Use only after validate; destination is a fresh git archive, without .git."""
    root = destination.resolve()
    for entry in candidate['files']:
        if tests_only and entry['path'] != regression_path(candidate['base_sha']):
            continue
        target = root / entry['path']
        if target.is_symlink() or not target.resolve().is_relative_to(root):
            raise SafetyStop('SYMLINK_OR_PATH_ESCAPE')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(entry['content'], encoding='utf-8')
