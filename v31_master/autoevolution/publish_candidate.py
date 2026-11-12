#!/usr/bin/env python3
"""Publish verified files using Git data API; never run them or merge anything."""
from __future__ import annotations
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from candidate import digest, validate
from engine import ALLOWED_BRANCH, ALLOWED_REPO, SafetyStop
from propose import NoRedirect


def verification_guard(result: dict, raw: bytes, sha: str) -> None:
    expected = {'schema': 'v31-verification/v1', 'base_sha': sha,
                'candidate_sha256': digest(raw), 'baseline': 'PASS',
                'regression_before': 'FAIL_EXPECTED', 'candidate_suite': 'PASS',
                'production_writes': False, 'network_in_sandbox': False}
    if result != expected:
        raise SafetyStop('VERIFICATION_MISMATCH')


def api(method: str, path: str, data=None):
    req = urllib.request.Request('https://api.github.com/repos/' + ALLOWED_REPO + path,
        method=method, data=json.dumps(data).encode() if data is not None else None,
        headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
                 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json'})
    with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as response:
        return json.load(response)


def main():
    if (os.getenv('GITHUB_REPOSITORY') != ALLOWED_REPO or
        os.getenv('GITHUB_REF_NAME') != ALLOWED_BRANCH):
        raise SafetyStop('PUBLISH_TARGET_DENIED')
    root, out = Path.cwd(), Path('autoevolution-output')
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    raw = (out / 'candidate.json').read_bytes()
    candidate = validate(json.loads(raw), root, sha)
    verification_guard(json.loads((out / 'verification.json').read_text()), raw, sha)
    branch = 'lab/jarvis-candidate-' + digest(raw)[:20]
    # Deterministic branch makes retries idempotent. Existing branches are never overwritten.
    try:
        ref = api('GET', '/git/ref/heads/' + branch)
        commit_sha = ref['object']['sha']
        for entry in candidate['files']:
            import base64
            current = api('GET', '/contents/' + entry['path'] + '?ref=' + branch)
            if base64.b64decode(current['content']).decode() != entry['content']:
                raise SafetyStop('EXISTING_CANDIDATE_BRANCH_DIVERGED')
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        parent = api('GET', '/git/commits/' + sha)
        tree = api('POST', '/git/trees', {'base_tree': parent['tree']['sha'], 'tree': [
            {'path': f['path'], 'mode': '100644', 'type': 'blob', 'content': f['content']}
            for f in candidate['files']]})
        commit = api('POST', '/git/commits', {'message': 'JARVIS: verified LAB candidate [skip ci]',
                      'tree': tree['sha'], 'parents': [sha]})
        commit_sha = commit['sha']
        api('POST', '/git/refs', {'ref': 'refs/heads/' + branch, 'sha': commit_sha})
    result = {'branch': branch, 'commit_sha': commit_sha, 'production_writes': False}
    # PR description is generated from trusted fields; model prose remains only in artifact.
    try:
        existing = api('GET', '/pulls?state=all&head=' + ALLOWED_REPO.split('/')[0] + ':' + branch)
        if existing:
            result['pull_request'] = existing[0]['html_url']
        else:
            pr = api('POST', '/pulls', {
                'title': 'JARVIS: candidato LAB com regressao reproduzida',
                'head': branch, 'base': ALLOWED_BRANCH, 'draft': True,
                'body': ('Candidato gerado por IA, sem promocao automatica.\n\n'
                         'Baseline aprovada; novo teste falhou por assercao antes da alteracao; '
                         'suite completa aprovada depois. Execucao sem rede e sem credenciais.\n\n'
                         'Base: ' + sha + '\nCandidate SHA256: ' + digest(raw) + '\n\n'
                         'Revisar causa, qualidade e comportamento antes de integrar. '
                         'PASS nao comprova estoque, conversao nem qualidade visual em producao.')})
            result['pull_request'] = pr['html_url']
    except urllib.error.HTTPError as exc:
        if exc.code not in (403, 422):
            raise
        result['pr_status'] = 'BLOCKED_REPOSITORY_PERMISSION_OR_VALIDATION'
    (out / 'publication.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('PUBLISH_BLOCKED_' + type(exc).__name__)
        raise SystemExit(2)
