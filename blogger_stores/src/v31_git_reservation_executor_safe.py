#!/usr/bin/env python3
"""V31 LAB Git reservation executor: remote READ ONLY + local bare Git race simulation.

SAFE boundary: this file does not contain any command that can push to the
GitHub remote. The only git push performed here targets a newly initialized
bare repository inside a temporary directory, created by this process.

A PASS is not authorization for Blogger PUT, real Git reservation, cron, or
promotion. Authentic Blogger GET/readback is a separate prerequisite.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from hashlib import sha256

CORE = Path(__file__).resolve().parents[1] / 'v31_core'
sys.path.insert(0, str(CORE))
from v31_multicycle_cas_contract import (
    REPO, BRANCH, BLOG_ID, PAGE_ID, ReservationBlocked,
    git_blob_sha, prepare_reservation, is_git_sha,
)

LEDGER = 'blogger_stores/v31_lab/state/v31_rotation_ledger.json'
HISTORY = 'blogger_stores/v31_lab/state/v31_rotation_history.json'
PROFILE = 'blogger_stores/v31_lab/perfil_v31_lab.json'
GITHUB_URL = f'https://github.com/{REPO}'
REMOTE_REF = f'refs/heads/{BRANCH}'
MAX_FILE = 1024 * 1024

class SafeExecutionBlocked(ValueError):
    pass

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SafeExecutionBlocked(reason)

def command(args: list[str], root: Path, timeout: int = 30, expect_success=True) -> subprocess.CompletedProcess:
    """Execute an exact argument vector, never a shell or user-supplied command."""
    result = subprocess.run(args, cwd=root, capture_output=True, timeout=timeout, check=False)
    if expect_success and result.returncode != 0:
        # Git stdout/stderr may disclose internal paths. Report a fixed sanitized error.
        raise SafeExecutionBlocked('Comando Git read-only/sandbox falhou: ' + args[1])
    return result

def git_read(root: Path, *args: str, timeout: int = 30) -> bytes:
    # Restrict COMPLETE argv signatures: git remote also has mutating subcommands.
    tuple_args = tuple(args)
    allowed = (
        tuple_args == ('remote', 'get-url', 'origin')
        or tuple_args == ('rev-parse', 'HEAD')
        or tuple_args == ('ls-remote', '--exit-code', 'origin', REMOTE_REF)
        or tuple_args == ('status', '--porcelain', '--', LEDGER, HISTORY)
        or (len(args) == 2 and args[0] in ('rev-parse','show')
            and re.fullmatch(r'[0-9a-f]{40}:(?:blogger_stores/v31_lab/(?:state/v31_rotation_(?:ledger|history)\.json|perfil_v31_lab\.json))',args[1]) is not None)
    )
    require(allowed, 'Git argv nao permitido em read-only')
    result = command(['git', *args], root, timeout=timeout).stdout
    return result if args[0] == 'show' else result.strip()

def strict_read(path: Path) -> bytes:
    require(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size < MAX_FILE,
            'Arquivo ausente, link ou tamanho invalido')
    return path.read_bytes()

def safe_origin(root: Path) -> None:
    url = git_read(root, 'remote', 'get-url', 'origin').decode('utf-8', 'replace').strip()
    require(url in (GITHUB_URL, GITHUB_URL + '.git'), 'Remote Git origem nao autorizado')

def remote_head(root: Path) -> str:
    result = git_read(root, 'ls-remote', '--exit-code', 'origin', REMOTE_REF, timeout=35).decode('ascii', 'replace').strip()
    rows = result.splitlines()
    require(len(rows) == 1, 'Referência remota ambigua/ausente')
    parts = rows[0].split('\t')
    require(len(parts) == 2 and parts[1] == REMOTE_REF and is_git_sha(parts[0]),
            'Formato do Git HEAD remoto incorreto')
    return parts[0]

def pinned_file(root: Path, relative: str, head: str) -> tuple[bytes, str]:
    require(re.fullmatch(r'[a-zA-Z0-9_/.-]+', relative) is not None and '..' not in relative,
            'Caminho Git nao autorizado')
    data = git_read(root, 'show', head + ':' + relative)
    require(0 < len(data) < MAX_FILE, 'Arquivo versionado invalido')
    blob = git_read(root, 'rev-parse', head + ':' + relative).decode('ascii').strip()
    require(is_git_sha(blob) and git_blob_sha(data) == blob, 'Hash Git do arquivo remoto nao confere')
    return data, blob

def sha256_check(data: bytes, expected: str, description: str):
    require(isinstance(expected, str) and re.fullmatch(r'[0-9a-f]{64}', expected) is not None,
            'SHA de ' + description + ' malformado')
    require(sha256(data).hexdigest() == expected, 'SHA de ' + description + ' divergente')

def read_only_reservation_preflight(*, repo_root: Path, selection: Path,
        original: Path, candidate: Path, expected_selection_sha: str,
        expected_original_sha: str, expected_candidate_sha: str,
        remote_reader=remote_head) -> dict:
    """No remote writes, even if every gate passes."""
    root = repo_root.resolve(strict=True)
    require(root.is_dir(), 'Repositório indisponível')
    safe_origin(root)
    head = git_read(root, 'rev-parse', 'HEAD').decode('ascii').strip()
    require(is_git_sha(head), 'Git HEAD local invalido')
    require(remote_reader(root) == head, 'Git branch remota diferente do checkout; bloquear')
    # Reject edits to canonical state, even in the read-only worktree.
    dirty = git_read(root, 'status', '--porcelain', '--', LEDGER, HISTORY)
    require(not dirty, 'Ledger/historico locais alterados; bloquear')
    state_bytes, ledger_blob = pinned_file(root, LEDGER, head)
    hist_bytes, hist_blob = pinned_file(root, HISTORY, head)
    profile_bytes, _ = pinned_file(root, PROFILE, head)
    profile = json.loads(profile_bytes)
    selected = strict_read(selection)
    before = strict_read(original)
    after = strict_read(candidate)
    sha256_check(selected, expected_selection_sha, 'selecao Shopee')
    sha256_check(before, expected_original_sha, 'HTML original')
    sha256_check(after, expected_candidate_sha, 'HTML candidato')
    proposed = prepare_reservation(repository=REPO, branch=BRANCH, profile=profile,
        ledger_bytes=state_bytes, history_bytes=hist_bytes, selection_bytes=selected,
        blogger_html_bytes=before, candidate_html_bytes=after,
        expected_head=head, observed_head=head,
        expected_ledger_blob=ledger_blob, expected_history_blob=hist_blob)
    require(remote_reader(root) == head, 'Branch remota mudou durante preflight')
    return {
        'status': 'V31_LAB_GIT_REMOTE_READ_ONLY_PREFLIGHT_PASS',
        'repository': REPO, 'branch': BRANCH, 'head': head,
        'blog_id': BLOG_ID, 'page_id': PAGE_ID,
        'operation_id': proposed['operation_id'],
        'selection_sha256': proposed['selection_sha256'],
        'original_sha256': proposed['original_html_sha256'],
        'candidate_sha256': proposed['candidate_html_sha256'],
        'baseline_ledger_blob': ledger_blob,
        'baseline_history_blob': hist_blob,
        'proposed_ledger_blob': proposed['proposed_ledger_blob'],
        'unchanged_history_blob': proposed['unchanged_history_blob'],
        'product_count': proposed['items'],
        'remote_read_only': True,
        'git_reservation_committed': False,
        'blogger_readback_live': False,
        'blogger_put_allowed': False,
        'git_remote_write_allowed': False,
        'cron_allowed': False,
        'note': 'Proposta simulada. Nova leitura autenticada Blogger e gate de escrita explicito sao obrigatorios.'
    }

def sandbox_race(*, parent_ledger: bytes, parent_history: bytes,
                 proposed_ledger: bytes) -> dict:
    """Genuine non-force Git pushes against a NEW LOCAL bare temp remote only.

    Does NOT read or write user GitHub repository. Two independent clones compete
    from the same base and only one may update a branch. Data is never uploaded.
    """
    require(shutil.which('git') is not None, 'Git nao instalado')
    for payload in (parent_ledger, parent_history, proposed_ledger):
        require(type(payload) is bytes and 0 < len(payload) < MAX_FILE, 'Sandbox payload invalido')
    old = json.loads(parent_ledger)
    new = json.loads(proposed_ledger)
    require(new['blogId'] == old['blogId'] == BLOG_ID
            and new['pageId'] == old['pageId'] == PAGE_ID
            and len(new['operations']) == len(old['operations'])+1
            and new['operations'][:-1] == old['operations']
            and new['operations'][-1]['status'] == 'PLAN',
            'Reserva simulada invalida')
    with tempfile.TemporaryDirectory(prefix='v31-lab-cas-') as td:
        t = Path(td)
        bare = t / 'isolated.git'
        command(['git', 'init', '--bare', str(bare)], t)
        seed = t / 'seed'
        seed.mkdir()
        command(['git', 'init', '-b', 'sandbox-v31'], seed)
        command(['git','config','user.name','SAFE-Test'], seed)
        command(['git','config','user.email','safe@example.invalid'], seed)
        for n, data in ((LEDGER,parent_ledger),(HISTORY,parent_history)):
            p=seed/n; p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        command(['git','add','--',LEDGER,HISTORY], seed)
        command(['git','commit','-m','SAFE seed'], seed)
        command(['git','remote','add','origin',str(bare)], seed)
        command(['git','push','origin','HEAD:refs/heads/sandbox-v31'], seed)
        runners=[]
        for label in ('writer-a','writer-b'):
            clone = t/label
            command(['git','clone','-b','sandbox-v31',str(bare),str(clone)],t)
            command(['git','config','user.name','SAFE-Test'],clone)
            command(['git','config','user.email','safe@example.invalid'],clone)
            (clone/LEDGER).write_bytes(proposed_ledger)
            command(['git','add','--',LEDGER],clone)
            command(['git','commit','-m','SAFE PLAN reservation '+label],clone)
            runners.append(clone)
        winner = command(['git','push','origin','HEAD:refs/heads/sandbox-v31'],runners[0],expect_success=False)
        loser = command(['git','push','origin','HEAD:refs/heads/sandbox-v31'],runners[1],expect_success=False)
        require(winner.returncode==0 and loser.returncode!=0, 'Concorrencia Git nao foi bloqueada')
        # Confirm exact bytes of winner's ledger/history from the bare repository.
        final_ledger=command(['git','show','refs/heads/sandbox-v31:'+LEDGER],bare).stdout
        final_history=command(['git','show','refs/heads/sandbox-v31:'+HISTORY],bare).stdout
        require(final_ledger==proposed_ledger and final_history==parent_history,
                'Sandbox alterou o historico ou a reserva foi perdida')
        return {'status':'V31_SANDBOX_GIT_NONFORCE_RACE_PASS',
                'isolated_temp_bare_repo': True,
                'writer_a_push_accepted':True,'writer_b_conflict_rejected':True,
                'ledger_blob':git_blob_sha(final_ledger),
                'history_blob':git_blob_sha(final_history),
                'github_write':False,'blogger_write':False}

def write_report(report: dict, output: Path, root: Path):
    target = output.resolve(strict=False)
    # An absolute filename outside the checkout cannot overwrite versioned state.
    require(output.is_absolute() and not target.is_relative_to(root.resolve()),
            'Relatorio deve ficar fora do repositorio original')
    require(not target.is_symlink(), 'Output link proibido')
    require(target.parent.is_dir() and not target.parent.is_symlink(), 'Diretorio do relatorio deve existir')
    data=(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)+'\n')
    with target.open('x',encoding='utf-8') as f:f.write(data)

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description='V31 LAB remote read-only preflight and local Git race')
    p.add_argument('--repo-root',required=True,type=Path)
    p.add_argument('--selection',required=True,type=Path)
    p.add_argument('--html-original',required=True,type=Path)
    p.add_argument('--html-candidate',required=True,type=Path)
    p.add_argument('--selection-sha',required=True)
    p.add_argument('--original-sha',required=True)
    p.add_argument('--candidate-sha',required=True)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--sandbox-race',action='store_true')
    args=p.parse_args(argv)
    try:
        report=read_only_reservation_preflight(repo_root=args.repo_root,
            selection=args.selection,original=args.html_original,candidate=args.html_candidate,
            expected_selection_sha=args.selection_sha,expected_original_sha=args.original_sha,
            expected_candidate_sha=args.candidate_sha)
        if args.sandbox_race:
            root=args.repo_root.resolve(strict=True)
            head=report['head']
            l,_=pinned_file(root,LEDGER,head)
            h,_=pinned_file(root,HISTORY,head)
            s=strict_read(args.selection);bf=strict_read(args.html_original);af=strict_read(args.html_candidate)
            profile=json.loads(pinned_file(root,PROFILE,head)[0])
            proposed=prepare_reservation(repository=REPO,branch=BRANCH,profile=profile,
                ledger_bytes=l,history_bytes=h,selection_bytes=s,
                blogger_html_bytes=bf,candidate_html_bytes=af,
                expected_head=head,observed_head=head,
                expected_ledger_blob=report['baseline_ledger_blob'],
                expected_history_blob=report['baseline_history_blob'])
            report['sandbox_race']=sandbox_race(parent_ledger=l,parent_history=h,
                proposed_ledger=proposed['proposed_ledger_bytes'])
        write_report(report,args.output,args.repo_root)
        print('V31_GIT_RESERVATION_EXECUTOR_SAFE_PASS; github_push=false; blogger_put=false; cron=false')
        return 0
    except (Exception) as e:
        # Avoid printing network trace or file contents; exception type is enough.
        print(json.dumps({'status':'V31_GIT_EXECUTOR_FAIL_CLOSED','error_type':type(e).__name__,
            'reason':str(e)[:100]}))
        return 2

if __name__=='__main__':sys.exit(main())
