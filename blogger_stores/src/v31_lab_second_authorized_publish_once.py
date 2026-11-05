#!/usr/bin/env python3
"""One explicitly approved LAB V31 second-rotation attempt; NEVER schedule/retry.

Git is fenced and durably backs up HTML in the same non-forced commit before PUT.
Any uncertain result after claim is terminal; manual readback/reconciliation only.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib import request, error

SRC = Path(__file__).resolve().parent
CORE = SRC.parent / 'v31_core'
sys.path.insert(0, str(CORE))
sys.path.insert(0, str(SRC))

from v31_prewrite_claim_sandbox_safe import BLOG, PAGE, OP, ORIGINAL, CANDIDATE, LEDGER, HISTORY, BACKUP
from v31_atomic_git_claim_bridge_lab import (
    LabAtomicClaimBridge, PinnedGitRemoteGateway, BASE_LEDGER_BLOB,
    BASE_HISTORY_BLOB, REPO, BRANCH, RESERVATION, git_blob,
)
from v31_second_publish_once_lab import (
    ImmutableInputs, GitWitness, WriteApproval, publish_once_with_external_gates,
    PublicationBlocked, PAGE_URL,
)
from v31_second_live_backup_git_readonly_safe import run_live_read_only
from v31_etag_sacrificial_live_once import oauth_access_token
from hashlib import sha256

LAUNCH = 'blogger_stores/v31_lab/SECOND_ROTATION_USER_APPROVED_LIVE_ONCE.trigger'
APPROVAL = 'USER_AUTHORIZED_V31_SECOND_ROTATION_LAB_ONLY_20261104_PREFLIGHT_CORRECTED1'
TARGET = 'https://www.googleapis.com/blogger/v3/blogs/' + BLOG + '/pages/' + PAGE

class Stop(RuntimeError): pass

def ensure(value, reason):
    if not value: raise Stop(reason)

def sha(raw): return sha256(raw).hexdigest()

def git(*args):
    p = subprocess.run(['git', *args], capture_output=True, timeout=45, check=False)
    ensure(p.returncode == 0, 'Git metadata check failed')
    return p.stdout.decode('utf-8').strip()

def validate_launch_env():
    ensure(os.environ.get('GITHUB_REPOSITORY') == REPO, 'Wrong repository')
    ensure(os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'Wrong LAB branch')
    ensure(os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Only a single, explicit launch push')
    ensure(os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'Reruns are forbidden')
    ensure(os.environ.get('V31_LAB_ONCE_APPROVAL') == APPROVAL, 'Explicit authorization flag absent')
    ensure(re.fullmatch(r'[0-9a-f]{40}', os.environ.get('GITHUB_SHA', '')) is not None,
           'GitHub HEAD SHA invalid')
    ensure(git('rev-parse', 'HEAD') == os.environ['GITHUB_SHA'], 'Checkout revision mismatch')
    ensure(git('branch','--show-current') == BRANCH, 'Checkout branch mismatch')
    ensure(git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines() == [LAUNCH],
           'Launch commit must alter exactly the one-time trigger')
    ensure(Path(LAUNCH).read_text(encoding='utf-8').strip() == APPROVAL,
           'Launch trigger not the exact approved operation')
    ensure(subprocess.run(['git', 'merge-base', '--is-ancestor', RESERVATION,
                           os.environ['GITHUB_SHA']], capture_output=True, timeout=20).returncode == 0,
           'Missing real PLAN reservation ancestry')
    ensure(os.environ.get('GITHUB_ACTOR') not in ('dependabot[bot]',), 'Automated actor forbidden')

class OneRequest:
    def __init__(self, service, method, data=None):
        self.s = service
        self.method = method
        self.data = data
        self.headers = {}

    def execute(self):
        if self.method == 'PUT':
            ensure(self.s.put_count == 0, 'Second Blogger PUT forbidden, including retries')
            self.s.put_count += 1  # count BEFORE network, including timeout
            etag = self.headers.get('If-Match')
            ensure(isinstance(etag, str) and re.fullmatch(r'"[\x21\x23-\x7e]+"', etag),
                   'Missing strong If-Match header')
        headers = {'Accept':'application/json', 'Authorization': 'Bearer '+self.s.token,
                   'User-Agent': 'V31-LAB-SECOND-LIVE-ONCE/1'}
        if self.method == 'PUT':
            headers['Content-Type'] = 'application/json; charset=utf-8'
            headers['If-Match'] = self.headers['If-Match']
            data = json.dumps(self.data, ensure_ascii=False, separators=(',',':')).encode('utf-8')
        else:
            data = None
        q = request.Request(TARGET, method=self.method, data=data, headers=headers)
        try:
            with request.urlopen(q, timeout=35) as resp:
                ensure(resp.status in (200, 201), 'Blogger HTTP response not 200/201')
                raw = resp.read(250000)
                ensure(len(raw) < 250000, 'Blogger response oversized')
                return json.loads(raw)
        except error.HTTPError as exc:
            # Never print response body or headers (OAuth secrets).
            raise Stop('Blogger HTTP '+str(exc.code)) from None
        except (error.URLError, TimeoutError, OSError) as exc:
            raise Stop('Blogger network result uncertain: '+type(exc).__name__) from None

class OneBloggerService:
    def __init__(self, token):
        ensure(type(token) is str and len(token) > 30, 'OAuth token absent')
        self.token=token
        self.put_count=0
    def pages(self): return self
    def get(self, *, blogId, pageId):
        ensure((str(blogId),str(pageId)) == (BLOG,PAGE), 'Protected Blogger GET target mismatch')
        return OneRequest(self, 'GET')
    def update(self, *, blogId, pageId, body):
        ensure((str(blogId),str(pageId)) == (BLOG,PAGE), 'Protected Blogger PUT target mismatch')
        ensure(self.put_count == 0, 'Already attempted Blogger PUT')
        ensure(type(body) is dict and set(body) == {'title','content'} and body['title'].strip().casefold()=='loja',
               'Unexpected Blogger update body')
        ensure(type(body['content']) is str and sha(body['content'].encode('utf-8'))==CANDIDATE,
               'Candidate HTML not pinned to approved SHA')
        # Mirrors the previously validated Google Blogger Pages.update request envelope.
        data={'kind':'blogger#page','blog':{'id':BLOG},'id':PAGE,
              'title':body['title'], 'content':body['content']}
        return OneRequest(self, 'PUT', data)


def run_once():
    validate_launch_env()  # strictly before OAuth or any Git writing
    checkout=Path(os.environ['GITHUB_WORKSPACE']).resolve(strict=True)
    ensure(checkout == Path.cwd().resolve(), 'Not in expected repository root')
    base=Path(os.environ['RUNNER_TEMP']).resolve(strict=True)
    a=base/'v31_approved'
    ensure(a.is_dir() and not a.is_symlink(), 'Approved artifact directory missing')
    profile=(checkout/'blogger_stores/v31_lab/perfil_v31_lab.json').read_bytes()
    original=(a/'LOJA_ORIGINAL_BACKUP.html').read_bytes()
    candidate=(a/'LOJA_CANDIDATA_NAO_PUBLICAR.html').read_bytes()
    selection=(a/'selecao_shopee_v23_SECOND_REAL_SAFE.json').read_bytes()
    ensure(sha(original)==ORIGINAL and sha(candidate)==CANDIDATE and
           sha(selection)=='aea7191e1e4ea77581b33591e0e940f6bd582114c90ea2e457a7173faf3664b7',
           'Archived Shopee selection or HTML changed')
    gateway= PinnedGitRemoteGateway(checkout, write_enabled=True)
    head = os.environ['GITHUB_SHA']
    ensure(gateway.head()==head, 'Remote HEAD moved since approved launch')
    ledger=gateway.read_blob(head,LEDGER);history=gateway.read_blob(head,HISTORY)
    ensure(git_blob(ledger)==BASE_LEDGER_BLOB and git_blob(history)==BASE_HISTORY_BLOB,
           'Ledger/history no longer at approved PLAN')
    def witness():
        current=gateway.head()
        ensure(current==head, 'Remote Git head changed during prewrite')
        led=gateway.read_blob(head,LEDGER)
        his=gateway.read_blob(head,HISTORY)
        ensure(git_blob(led)==BASE_LEDGER_BLOB and git_blob(his)==BASE_HISTORY_BLOB,
               'Git state changed before claim')
        return GitWitness(REPO,BRANCH,head,True,BASE_LEDGER_BLOB,BASE_HISTORY_BLOB)
    # R13 independent GET and authenticated live inventory: no Blogger writes.
    os.environ['V31_ARCHIVED_ORIGINAL']=str(a/'LOJA_ORIGINAL_BACKUP.html')
    os.environ['V31_ARCHIVED_CANDIDATE']=str(a/'LOJA_CANDIDATA_NAO_PUBLICAR.html')
    proof = run_live_read_only()
    ensure(proof['status']=='V31_SECOND_AUTHENTICATED_BACKUP_AND_GIT_READ_ONLY_PASS',
           'Prewrite attestation incomplete')
    svc=OneBloggerService(oauth_access_token())
    bridge=LabAtomicClaimBridge(gateway=gateway,
        archived_backup_reader=lambda: (a/'LOJA_ORIGINAL_BACKUP.html').read_bytes(),
        original_html=original, armed=True)
    inputs=ImmutableInputs(profile,ledger,history,selection,original,candidate)
    approval=WriteApproval(OP, RESERVATION, True)
    try:
        result=publish_once_with_external_gates(
            service=svc,inputs=inputs,read_remote=witness,approval=approval,
            archive_dir=base/'v31_second_prewrite_original_unique',
            verify_durable_backup=bridge.verify_durable_backup,
            claim_attempt=bridge.claim_attempt)
        ensure(result.get('status') in ('V31_SECOND_PUT_READBACK_CONFIRMED_AWAIT_PUBLIC_PROOF',
                                       'V31_SECOND_ALREADY_APPLIED_NO_PUT'),
               'Unexpected publisher status')
        audit=bridge.last_audit
        if result['status']=='V31_SECOND_PUT_READBACK_CONFIRMED_AWAIT_PUBLIC_PROOF':
            ensure(svc.put_count==1 and audit is not None and audit.exact_remote_readback,
                   'Git claim/one Blogger PUT not evidenced')
        else:
            ensure(svc.put_count==0, 'Already-applied handling attempted PUT')
        report={'status':result['status'],'operation_id':OP,'blog_id':BLOG,
                'page_id':PAGE,'put_attempts':svc.put_count,
                'git_claim_commit':audit.claim_commit if audit else None,
                'git_backup_verified':bool(audit and audit.exact_remote_readback),
                'candidate_sha256':CANDIDATE,'public_proof_pending':True,
                'cron_enabled':False}
        print('V31_LAB_SECOND_ONE_SHOT_RESULT='+json.dumps(report,sort_keys=True),flush=True)
        return result
    except Exception as exc:
        # Cannot know whether a PUT succeeded after a network error.
        audit=bridge.last_audit
        print('V31_LAB_SECOND_ONE_SHOT_STOP='+json.dumps({
            'error_type':type(exc).__name__, 'put_attempts':svc.put_count,
            'claim_commit': audit.claim_commit if audit else None,
            'requires_authenticated_readback':bool(audit),
            'never_retry_put':True},sort_keys=True),flush=True)
        raise SystemExit(2) from None

if __name__=='__main__':
    try: run_once()
    except (Stop, KeyError, ValueError, FileNotFoundError) as exc:
        print('V31_LAB_SECOND_BLOCKED='+type(exc).__name__,flush=True)
        raise SystemExit(2) from None
