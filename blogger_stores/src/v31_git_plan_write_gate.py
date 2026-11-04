#!/usr/bin/env python3
"""V31 R1 LAB -- one-operation Git PLAN reservation, fail closed.

This module is inert on import. The only mutating Git operation is an explicit
non-force push of ONE updated canonical ledger file, preceded by a CAS check.
The history file remains byte-identical. Blogger writes, cron and promotion are
not implemented here. CI uses a new local bare remote, never real GitHub.

The LAB_REAL mode requires independent manual approval AND GitHub workflow
environment gates; it is intentionally NOT called by the SAFE workflow.
"""
from __future__ import annotations
import json
from hashlib import sha256
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / 'v31_core'))
from v31_rotation_ledger import validate_state
from v31_second_resume_safe import validate_persisted_pair
from v31_multicycle_cas_contract import (REPO, BRANCH, BLOG_ID, PAGE_ID,
    is_git_sha, git_blob_sha)

LEDGER = 'blogger_stores/v31_lab/state/v31_rotation_ledger.json'
HISTORY = 'blogger_stores/v31_lab/state/v31_rotation_history.json'
LAB_URL = f'https://github.com/{REPO}.git'
SANDBOX_BRANCH = 'sandbox-v31'
MAX_SIZE = 1024 * 1024

class ReservationWriteBlocked(ValueError):
    pass

def require(condition: bool, why: str) -> None:
    if not condition:
        raise ReservationWriteBlocked(why)

def _git(worktree: Path, *args: str, allowed_failure: bool=False, timeout: int=30):
    # No shell, custom credential/helper/hooks, or untrusted Git messages.
    env=os.environ.copy()
    env.update(GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1',
        GIT_AUTHOR_NAME='V31 Lab Reservation', GIT_AUTHOR_EMAIL='v31-lab@users.noreply.github.com',
        GIT_COMMITTER_NAME='V31 Lab Reservation', GIT_COMMITTER_EMAIL='v31-lab@users.noreply.github.com')
    cmd=['git','-c','core.hooksPath=/dev/null',*args]
    try:
        run=subprocess.run(cmd,cwd=worktree,env=env,capture_output=True,
                           timeout=timeout,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ReservationWriteBlocked('Git indisponivel ou sem resposta') from exc
    if run.returncode and not allowed_failure:
        # Never surface stderr: the remote or credential helper may leak secrets.
        raise ReservationWriteBlocked('Git operacao recusada: '+args[0])
    return run

def _output(worktree:Path,*args:str)->bytes:
    return _git(worktree,*args).stdout.strip()

def _remote_head(worktree:Path,branch:str)->str:
    data=_output(worktree,'ls-remote','--exit-code','origin','refs/heads/'+branch)
    fields=data.decode('ascii','replace').split('\t')
    require(len(fields)==2 and fields[1]=='refs/heads/'+branch
            and is_git_sha(fields[0]),'Branch remota ausente ou invalida')
    return fields[0]

def _git_file(worktree:Path,relative:str)->bytes:
    # HEAD points to the checked-out commit; never read arbitrary remote files.
    return _git(worktree,'show','HEAD:'+relative).stdout

def _json(raw:bytes,label:str)->dict:
    require(type(raw) is bytes and 0<len(raw)<MAX_SIZE,label+' invalido')
    try: value=json.loads(raw.decode('utf-8'))
    except (ValueError,UnicodeError) as exc:
        raise ReservationWriteBlocked(label+' nao e JSON UTF-8') from exc
    require(type(value) is dict,label+' nao e objeto JSON')
    return value

def validate_plan_bytes(*,ledger_before:bytes,history_before:bytes,
                        ledger_plan:bytes,expected_ledger_blob:str,
                        expected_history_blob:str,operation_id:str,
                        expected_plan_sha256:str,expected_selection_sha:str,
                        expected_original_sha:str,expected_candidate_sha:str)->dict:
    """Validate the entire state transition independently of the producer."""
    require(isinstance(expected_plan_sha256,str) and
            re.fullmatch(r'[0-9a-f]{64}',expected_plan_sha256)
            and sha256(ledger_plan).hexdigest()==expected_plan_sha256,
            'Plano de escrita nao corresponde ao digest autorizado')
    require(git_blob_sha(ledger_before)==expected_ledger_blob
            and git_blob_sha(history_before)==expected_history_blob,
            'Blobs basais alterados')
    before=_json(ledger_before,'Ledger original')
    history=_json(history_before,'Historico')
    proposed=_json(ledger_plan,'Ledger PLAN')
    validate_persisted_pair(before,history)
    validate_state(proposed)
    require(before['blogId']==proposed['blogId']==BLOG_ID
            and before['pageId']==proposed['pageId']==PAGE_ID,'Blog/Page LAB divergente')
    old=before['operations']; new=proposed['operations']
    require(len(old)>=1 and all(x['status']=='PERSISTED' for x in old),
            'Ledger nao esta totalmente persistido')
    require(len(new)==len(old)+1 and new[:-1]==old
            and new[-1].get('status')=='PLAN',
            'Reserva nao e adicao imutavel de um PLAN')
    op=new[-1]
    require((op.get('selectionSha'),op.get('originalSha'),op.get('candidateSha')) ==
            (expected_selection_sha,expected_original_sha,expected_candidate_sha),
            'Selecao ou HTML nao coincide com hashes aprovados')
    require(isinstance(operation_id,str) and re.fullmatch(r'[0-9a-f]{64}',operation_id),
            'ID operacao invalido')
    require(op['operationId']==operation_id and
            op['originalSha']==old[-1]['candidateSha'],
            'Operacao/HTML anterior nao correspondem')
    require(isinstance(op.get('candidateSha'),str) and op['candidateSha']!=op['originalSha'],
            'Candidato igual ao anterior')
    require(all(x['operationId']!=operation_id for x in old), 'Replay de operacao')
    return op

def _gate(*,mode:str,remote:str,branch:str,operation_id:str,
          expected_plan_sha256:str,approval:str|None,sandbox_bare:Path|None)->None:
    require(mode in ('SANDBOX','LAB_REAL'),'Modo Git nao permitido')
    if mode=='SANDBOX':
        require(branch==SANDBOX_BRANCH and sandbox_bare is not None,
                'Branch isolada invalida')
        bare=sandbox_bare.resolve(strict=True)
        require(bare.is_dir() and not bare.is_symlink()
                and remote==str(bare),'Remote SANDBOX invalido')
        require(_output(bare,'rev-parse','--is-bare-repository')==b'true',
                'Remote SANDBOX nao e bare')
        return
    # These conditions cannot be set by the read-only CI. Live permission must
    # be granted in a DIFFERENT explicitly approved manual workflow, if any.
    require(remote==LAB_URL and branch==BRANCH,'Remote LAB nao autorizado')
    require(os.getenv('GITHUB_ACTIONS')=='true'
        and os.getenv('GITHUB_EVENT_NAME')=='workflow_dispatch'
        and os.getenv('GITHUB_REPOSITORY')==REPO
        and os.getenv('GITHUB_REF')=='refs/heads/'+BRANCH,
        'Nao e workflow manual da branch LAB')
    require(approval=='RESERVAR_SOMENTE_GIT_LAB:'+operation_id
        and os.getenv('V31_LAB_RESERVATION_APPROVED_OPERATION')==operation_id
        and os.getenv('V31_LAB_RESERVATION_APPROVED_PLAN_SHA256')==expected_plan_sha256,
        'Autorizacao LAB especifica nao apresentada')

def commit_plan_on_checkout(*,checkout:Path,remote:str,branch:str,
    expected_head:str,expected_ledger_blob:str,expected_history_blob:str,
    proposed_ledger_bytes:bytes,operation_id:str,
    expected_plan_sha256:str,expected_selection_sha:str,
    expected_original_sha:str,expected_candidate_sha:str,mode:str='SANDBOX',
    approval:str|None=None,sandbox_bare:Path|None=None)->dict:
    """Persist ONE ledger PLAN by a non-force push, then read back HEAD/blobs.

    Checkout must be an isolated clone, not the user's original worktree.
    Preconditions are checked BEFORE modifying the clone. A stale expected_head
    fails closed, whether detected before or during the push.
    """
    require(is_git_sha(expected_head),'SHA do HEAD esperado invalido')
    _gate(mode=mode,remote=remote,branch=branch,operation_id=operation_id,
          expected_plan_sha256=expected_plan_sha256,
          approval=approval,sandbox_bare=sandbox_bare)
    require(checkout.is_dir() and not checkout.is_symlink(), 'Clone nao encontrado')
    origin=_output(checkout,'remote','get-url','origin').decode('utf8','replace')
    require(origin==remote,'Origem clone nao autorizada')
    require(_output(checkout,'status','--porcelain')==b'', 'Clone sujo')
    require(_output(checkout,'rev-parse','HEAD').decode()==expected_head,
            'HEAD clone desatualizado')
    require(_remote_head(checkout,branch)==expected_head,
            'HEAD remoto alterado antes da reserva')
    before=_git_file(checkout,LEDGER)
    history=_git_file(checkout,HISTORY)
    op=validate_plan_bytes(ledger_before=before,history_before=history,
        ledger_plan=proposed_ledger_bytes,expected_ledger_blob=expected_ledger_blob,
        expected_history_blob=expected_history_blob,operation_id=operation_id,
        expected_plan_sha256=expected_plan_sha256,
        expected_selection_sha=expected_selection_sha,
        expected_original_sha=expected_original_sha,
        expected_candidate_sha=expected_candidate_sha)
    target=checkout/LEDGER
    require(target.is_file() and not target.is_symlink(), 'Caminho ledger nao seguro')
    require(target.read_bytes()==before, 'Ledger local difere do commit')
    require((checkout/HISTORY).read_bytes()==history, 'Historico local divergiu')
    target.write_bytes(proposed_ledger_bytes)
    _git(checkout,'add','--',LEDGER)
    staged=_output(checkout,'diff','--cached','--name-only').decode('utf8','replace')
    require(staged==LEDGER,'Mudanca staged fora do ledger')
    _git(checkout,'diff','--cached','--check')
    _git(checkout,'commit','-m','LAB V31: reserva PLAN pre-publicacao; sem Blogger PUT')
    newhead=_output(checkout,'rev-parse','HEAD').decode()
    parent=_output(checkout,'rev-parse','HEAD^').decode()
    require(parent==expected_head and is_git_sha(newhead),'Parent do commit mudou')
    require(_git_file(checkout,LEDGER)==proposed_ledger_bytes
            and _git_file(checkout,HISTORY)==history,
            'Commit modificou arquivos alem do ledger')
    # Non-forced push: sibling commits cannot replace one another.
    require(_remote_head(checkout,branch)==expected_head,
            'Concorrencia detectada antes do push')
    result=_git(checkout,'push','origin','HEAD:refs/heads/'+branch,allowed_failure=True,timeout=45)
    require(result.returncode==0,'Reserva Git recusada (CAS/branch protection)')
    require(_remote_head(checkout,branch)==newhead,
            'Git remota alterou depois da reserva; revisar manualmente')
    return {'status':'V31_LAB_GIT_PLAN_RESERVATION_COMMITTED',
        'mode':mode,'blog_id':BLOG_ID,'page_id':PAGE_ID,
        'operation_id':operation_id,'selection_sha256':op['selectionSha'],
        'expected_parent_head':expected_head,'reserved_commit_head':newhead,
        'ledger_blob':git_blob_sha(proposed_ledger_bytes),
        'history_blob':git_blob_sha(history),'history_unchanged':True,
        'blogger_put_allowed':False,'cron_allowed':False,
        'live_git_write':mode=='LAB_REAL'}

def reserve_from_isolated_clone(*,remote:str,branch:str,
    expected_head:str,expected_ledger_blob:str,expected_history_blob:str,
    proposed_ledger_bytes:bytes,operation_id:str,
    expected_plan_sha256:str,expected_selection_sha:str,
    expected_original_sha:str,expected_candidate_sha:str,mode:str='SANDBOX',
    approval:str|None=None,sandbox_bare:Path|None=None)->dict:
    """Temporary clone avoids touching original checkout, including on failure."""
    _gate(mode=mode,remote=remote,branch=branch,operation_id=operation_id,
          expected_plan_sha256=expected_plan_sha256,
          approval=approval,sandbox_bare=sandbox_bare)
    with tempfile.TemporaryDirectory(prefix='v31-reserve-plan-') as folder:
        base=Path(folder)
        _git(base,'clone','--no-tags','--single-branch','--branch',branch,remote,'checkout',timeout=45)
        return commit_plan_on_checkout(checkout=base/'checkout',remote=remote,branch=branch,
            expected_head=expected_head,expected_ledger_blob=expected_ledger_blob,
            expected_history_blob=expected_history_blob,
            proposed_ledger_bytes=proposed_ledger_bytes,operation_id=operation_id,
            expected_plan_sha256=expected_plan_sha256,
            expected_selection_sha=expected_selection_sha,
            expected_original_sha=expected_original_sha,
            expected_candidate_sha=expected_candidate_sha,
            mode=mode,approval=approval,sandbox_bare=sandbox_bare)
