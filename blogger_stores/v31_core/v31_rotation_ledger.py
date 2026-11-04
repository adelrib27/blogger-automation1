"""Máquina de estados pura para rotação V31; não efetua IO nem publicação.

Status: PLAN -> PUBLISHED_PENDING_PUBLIC -> PUBLIC_VERIFIED -> PERSISTED.
Uma nova seleção é bloqueada se existir operação pendente. O histórico nunca
é alterado antes da confirmação pública exata, com operação idempotente.
A responsabilidade de autenticar a prova externa e persistir com compare-and-swap
cabe ao orquestrador futuro: este módulo apenas valida estrutura/transições.
"""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import re

SCHEMA = 1
ACTIVE = {'PLAN','PUBLISHED_PENDING_PUBLIC','PUBLIC_VERIFIED'}
TERMINAL = {'PERSISTED','ABORTED_PREWRITE'}

class LedgerError(ValueError):
    pass

def check(ok: bool, reason: str) -> None:
    if not ok:raise LedgerError(reason)

def operation_id(selection_sha: str, blog_id: str, page_id: str) -> str:
    check(isinstance(selection_sha,str) and re.fullmatch(r'[0-9a-f]{64}',selection_sha) is not None,
          'SHA-256 da seleção inválido')
    check(str(blog_id).isdigit() and str(page_id).isdigit(),'Blog/Page ID não numéricos')
    return sha256((str(blog_id)+'|'+str(page_id)+'|'+selection_sha).encode()).hexdigest()

def validate_state(state: dict) -> None:
    check(isinstance(state,dict) and state.get('schema')==SCHEMA, 'Versão de estado inválida')
    check(str(state.get('blogId','')).isdigit() and str(state.get('pageId','')).isdigit(),'Blog/Page ID inválidos')
    transactions=state.get('operations')
    check(isinstance(transactions,list),'Lista de operações ausente')
    seen=set()
    for op in transactions:
        check(isinstance(op,dict) and op.get('status') in ACTIVE|TERMINAL,'Estado de operação inválido')
        sid=op.get('selectionSha')
        check(op.get('operationId')==operation_id(sid,state['blogId'],state['pageId']),'ID de operação inválido')
        check(op['operationId'] not in seen,'Operação duplicada no ledger')
        seen.add(op['operationId'])
    check(sum(op['status'] in ACTIVE for op in transactions)<=1,
          'Mais de uma operação ativa concorrente')

def initial_state(blog_id: str, page_id: str) -> dict:
    check(str(blog_id).isdigit() and str(page_id).isdigit(),'Blog/Page ID inválidos')
    return {'schema':SCHEMA,'blogId':str(blog_id),'pageId':str(page_id),'operations':[]}

def stage(state: dict, selection_sha: str, current_sha: str, candidate_sha: str) -> dict:
    validate_state(state)
    oid=operation_id(selection_sha,state['blogId'],state['pageId'])
    for x in (current_sha,candidate_sha):
        check(isinstance(x,str) and re.fullmatch(r'[0-9a-f]{64}',x) is not None,
              'Hash de página inválido')
    check(current_sha!=candidate_sha,'Não há mudança efetiva de HTML')
    for op in state['operations']:
        if op['status'] in ACTIVE:
            check(op['operationId']==oid,'Outra seleção está pendente: bloquear nova publicação')
        if op['operationId']==oid:
            check(op['originalSha']==current_sha and op['candidateSha']==candidate_sha,
                  'Operação existente tem dados divergentes')
            return deepcopy(state)
    out=deepcopy(state)
    out['operations'].append({'operationId':oid,'selectionSha':selection_sha,
        'originalSha':current_sha,'candidateSha':candidate_sha,'status':'PLAN'})
    validate_state(out)
    return out

def mark_readback(state: dict, selection_sha: str, *, observed_candidate_sha: str) -> dict:
    validate_state(state)
    oid=operation_id(selection_sha,state['blogId'],state['pageId'])
    out=deepcopy(state)
    op=next((x for x in out['operations'] if x['operationId']==oid),None)
    check(op is not None,'Plano não existe no ledger')
    check(op['status'] in {'PLAN','PUBLISHED_PENDING_PUBLIC'},'Transição readback inválida')
    check(observed_candidate_sha==op['candidateSha'],'Readback Blogger diferente da candidata')
    op['status']='PUBLISHED_PENDING_PUBLIC'
    return out

def mark_public_verified(state: dict, selection_sha: str, *, proof: dict) -> dict:
    validate_state(state)
    out=deepcopy(state)
    op=next((x for x in out['operations'] if x['operationId']==operation_id(selection_sha,state['blogId'],state['pageId'])),None)
    check(op is not None and op['status'] in {'PUBLISHED_PENDING_PUBLIC','PUBLIC_VERIFIED'},
          'Estado não permite confirmar HTML público')
    check(isinstance(proof,dict) and proof.get('status')=='PUBLIC_EXACT_PASS'
          and proof.get('selection_sha256')==selection_sha and proof.get('cards')==16
          and proof.get('images')==16 and proof.get('links')==16
          and proof.get('public_http')==200,'Prova pública insuficiente')
    op['status']='PUBLIC_VERIFIED'
    return out

def history_commit(state: dict, selection_sha: str, history: dict,
                   *, published_items: list[dict], published_at: str) -> tuple[dict,dict]:
    validate_state(state)
    check(isinstance(history,dict) and history.get('version')==1
          and history.get('blogId')==state['blogId'] and isinstance(history.get('runs'),list),
          'Histórico de rotação incorreto')
    check(isinstance(published_at,str) and len(published_at)>10,'Timestamp de publicação inválido')
    check(isinstance(published_items,list) and len(published_items)==16,'Itens publicados incompletos')
    check(all(isinstance(p,dict) and re.fullmatch(r'\d{4,25}',str(p.get('itemId','')))
        and isinstance(p.get('category'),str) and p.get('category') for p in published_items),
          'Produtos a persistir inválidos')
    ids=[str(x['itemId']) for x in published_items]
    check(len(set(ids))==16,'Produto repetido no histórico')
    out=deepcopy(state);h=deepcopy(history)
    oid=operation_id(selection_sha,state['blogId'],state['pageId'])
    op=next((x for x in out['operations'] if x['operationId']==oid),None)
    check(op is not None and op['status'] in {'PUBLIC_VERIFIED','PERSISTED'},
          'Proibido persistir antes de PUBLIC_VERIFIED')
    existing=[r for r in h['runs'] if r.get('operationId')==oid]
    check(len(existing)<=1,'Histórico contém operação duplicada')
    if op['status']=='PERSISTED':
        check(len(existing)==1,'Estado persistido mas sem histórico correspondente')
        check(existing[0]['items']==published_items,'Tentativa duplicada alterou itens')
        return out,h
    check(not existing,'Histórico antecipou a confirmação')
    h['runs'].append({'timestamp':published_at,'source':'blogger_published',
                      'operationId':oid,'pageId':state['pageId'],'selectionSha':selection_sha,
                      'items':deepcopy(published_items)})
    op['status']='PERSISTED'
    return out,h