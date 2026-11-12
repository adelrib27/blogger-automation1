#!/usr/bin/env python3
"""Persist bounded, sanitized experiment outcomes in the LAB only."""
import base64
import json
import os
import re
import urllib.error
from engine import ALLOWED_REPO, ALLOWED_BRANCH, SafetyStop
from publish_candidate import api


def main():
    if (os.getenv('GITHUB_REPOSITORY') != ALLOWED_REPO or
        os.getenv('GITHUB_REF_NAME') != ALLOWED_BRANCH):
        raise SafetyStop('FEEDBACK_TARGET_DENIED')
    run, attempt = os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_RUN_ATTEMPT']
    if not re.fullmatch(r'[0-9]{5,20}', run) or not re.fullmatch(r'[0-9]{1,5}', attempt):
        raise SafetyStop('INVALID_FEEDBACK_ID')
    result = {'schema': 'v31-experiment-outcome/v1', 'run_id': int(run),
              'attempt': int(attempt), 'production_writes': False}
    for key in ('propose', 'verify', 'publish', 'sandbox'):
        value = os.environ.get('RESULT_' + key.upper(), 'skipped')
        if value not in ('success', 'failure', 'cancelled', 'skipped'):
            raise SafetyStop('INVALID_JOB_RESULT')
        result[key] = value
    fingerprint = os.getenv('CONTEXT_KEY', '')
    if fingerprint and not re.fullmatch(r'[a-f0-9]{64}', fingerprint):
        raise SafetyStop('INVALID_CONTEXT_KEY')
    result['context_key'] = fingerprint
    result['proposal_status'] = os.getenv('PROPOSAL_STATUS', 'UNAVAILABLE')
    if not re.fullmatch(r'[A-Z_a-z]{1,80}', result['proposal_status']):
        raise SafetyStop('INVALID_PROPOSAL_STATUS')
    path = f'/contents/v31_master/autoevolution/experiments/{run}-{attempt}.json'
    raw = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
    try:
        previous = api('GET', path + '?ref=' + ALLOWED_BRANCH)
        if base64.b64decode(previous['content']) != raw:
            raise SafetyStop('IMMUTABLE_OUTCOME_CONFLICT')
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        api('PUT', path, {'message': f'LAB experiment outcome {run}-{attempt} [skip ci]',
                          'branch': ALLOWED_BRANCH, 'content': base64.b64encode(raw).decode()})
    print('LAB_EXPERIMENT_OUTCOME_RECORDED')


if __name__ == '__main__':
    main()
