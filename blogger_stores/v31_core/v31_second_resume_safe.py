"""Decisao pura e fail-closed de retomada V31 em LAB.

Nao publica, nao faz rede, nao escreve ledger/historico, nao libera cron.
Protege principalmente o caso PUT Blogger bem-sucedido seguido de falha no job.
Esta funcao NAO autoriza publicar: PLAN com pagina original exige gate externo.
"""
from __future__ import annotations
import re
from v31_rotation_ledger import operation_id, validate_state

class ResumeBlocked(ValueError):
    pass

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ResumeBlocked(reason)

def _valid_sha(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None

def validate_persisted_pair(state: dict, history: dict) -> None:
    """Confere os pares de operacoes PERSISTED e linhas de historico.

    Uma operacao em PLAN/PENDING/VERIFIED nao pode aparecer no historico.
    A verificacao nao confunde seed com primeira publicacao real.
    """
    validate_state(state)
    require(isinstance(history, dict) and history.get('version') == 1
            and history.get('blogId') == state['blogId']
            and isinstance(history.get('runs'), list), 'Historico de outro blog/versao')
    runs = history['runs']
    require(bool(runs) and runs[0].get('source') == 'seed_from_current_blogger_store'
            and runs[0].get('pageId') == state['pageId'], 'Seed original ausente/invalido')
    persisted = [op for op in state['operations'] if op['status'] == 'PERSISTED']
    recorded = runs[1:]
    require(len(persisted) == len(recorded), 'Ledger e historico divergentes')
    for op, run in zip(persisted, recorded):
        require(run.get('source') == 'blogger_published'
                and run.get('pageId') == state['pageId']
                and run.get('operationId') == op['operationId']
                and run.get('selectionSha') == op['selectionSha'],
                'Operacao/historico nao correspondem')
        items = run.get('items')
        require(isinstance(items, list) and len(items) == 16
                and all(isinstance(x, dict) and isinstance(x.get('category'), str)
                        and re.fullmatch(r'[0-9]{4,25}', str(x.get('itemId', '')))
                        for x in items)
                and len({str(x['itemId']) for x in items}) == 16,
                'Itens registrados nao confiaveis')
    require(all(op['status'] not in ('PLAN', 'PUBLISHED_PENDING_PUBLIC', 'PUBLIC_VERIFIED')
                for op in state['operations'][:-1]),
            'Operacao pendente antiga; bloquear')

def decide_resume(*, state: dict, history: dict, blog_id: str, page_id: str,
                  selection_sha: str, observed_html_sha: str) -> dict:
    """Retorna apenas uma classificacao SAFE; nunca uma ordem de PUT/commit."""
    require(str(blog_id).isdigit() and str(page_id).isdigit(), 'Alvo nao numerico')
    require(state.get('blogId') == str(blog_id) and state.get('pageId') == str(page_id),
            'Alvo blog/pagina incorreto')
    require(_valid_sha(selection_sha) and _valid_sha(observed_html_sha),
            'Hash informado invalido')
    validate_persisted_pair(state, history)
    oid = operation_id(selection_sha, str(blog_id), str(page_id))
    matches = [op for op in state['operations'] if op['operationId'] == oid]
    require(len(matches) == 1, 'Operacao nao registrada; nao publicar')
    op = matches[0]
    require(op is state['operations'][-1], 'Selecao nao e a ultima operacao')
    require(_valid_sha(op.get('originalSha')) and _valid_sha(op.get('candidateSha'))
            and op['originalSha'] != op['candidateSha'], 'Hashes da operacao invalidos')
    observed = observed_html_sha
    status = op['status']
    if status == 'PLAN':
        if observed == op['originalSha']:
            decision = 'PLAN_ONLY_REQUIRES_EXPLICIT_WRITE_GATE'
        elif observed == op['candidateSha']:
            decision = 'PUT_MAY_HAVE_SUCCEEDED_SKIP_RETRY'
        else:
            raise ResumeBlocked('Pagina divergente em PLAN: interromper')
    elif status == 'PUBLISHED_PENDING_PUBLIC':
        require(observed == op['candidateSha'],
                'Pagina divergente no estado pendente: interromper')
        decision = 'VERIFY_PUBLIC_ONLY_NO_PUT'
    elif status == 'PUBLIC_VERIFIED':
        require(observed == op['candidateSha'],
                'Pagina divergente apos prova publica: interromper')
        decision = 'PREPARE_ATOMIC_PAIR_AWAIT_CAS'
    elif status == 'PERSISTED':
        require(observed == op['candidateSha'],
                'Pagina divergente apos persistencia: interromper')
        decision = 'ALREADY_PERSISTED_NO_ACTION'
    else:
        raise ResumeBlocked('Operacao encerrada/invalida; bloquear')
    return {'status': 'V31_LAB_RECOVERY_SAFE', 'decision': decision,
            'operationId': oid, 'blogger_put_allowed': False,
            'git_state_write_allowed': False, 'cron_allowed': False}