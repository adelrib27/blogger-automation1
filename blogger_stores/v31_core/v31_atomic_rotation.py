"""Fail-closed preparation of one V31 store rotation history transaction.

Pure functions: no IO, no Blogger writes. Caller atomically persists BOTH JSON documents
via one Git commit and a non-force push with an expected current branch head.
Deployment-specific IDs/pins are supplied in a separate versioned LAB policy JSON.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from v31_rotation_ledger import (validate_state, mark_public_verified,
                                 history_commit, operation_id)

class ReconcileError(ValueError):
    pass

def check(ok, reason):
    if not ok: raise ReconcileError(reason)

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)+'\n'

def get_time(v):
    check(isinstance(v,str), 'timestamp ausente')
    try: t=datetime.fromisoformat(v.replace('Z','+00:00'))
    except ValueError as e: raise ReconcileError('timestamp inválido') from e
    check(t.tzinfo is not None, 'timestamp sem timezone')
    return t.astimezone(timezone.utc)

def hexsha(s):
    return isinstance(s,str) and re.fullmatch(r'[0-9a-f]{64}',s) is not None

def validate_policy(policy):
    check(isinstance(policy,dict) and policy.get('schema')==1 and policy.get('mode')=='LAB',
          'política LAB obrigatória')
    for k in ('blogId','pageId'):
        check(isinstance(policy.get(k),str) and policy[k].isdigit(), k+' inválido')
    for k in ('selectionSha','proofArtifactDigest','originalProofSha'):
        check(hexsha(policy.get(k)),k+' inválido')
    for k in ('proofRunId','proofArtifactId','publishRunId','selectionRunId'):
        check(type(policy.get(k)) is int and policy[k]>0,k+' inválido')
    for k in ('repository','branch','pageUrl','proofWorkflow','proofArtifactName','proofCommitSha','publishedAt'):
        check(isinstance(policy.get(k),str) and policy[k],k+' não definido')
    check(policy['pageUrl'].startswith('https://') and 'blogspot.com/p/loja.html' in policy['pageUrl'],
          'URL de página canônica inválida')
    check(re.fullmatch(r'[0-9a-f]{40}',policy['proofCommitSha']) is not None,'commit de origem inválido')
    get_time(policy['publishedAt'])

def validate_run(meta,policy):
    check(isinstance(meta,dict) and meta.get('id')==policy['proofRunId']
          and meta.get('status')=='completed' and meta.get('conclusion')=='success'
          and meta.get('event')=='push','run não validado')
    check(meta.get('head_branch')==policy['branch']
          and meta.get('head_sha')==policy['proofCommitSha']
          and meta.get('path')==policy['proofWorkflow']
          and (meta.get('repository') or {}).get('full_name')==policy['repository'],
          'origem do workflow incompatível')

def validate_artifact(meta,policy):
    check(isinstance(meta,dict) and meta.get('id')==policy['proofArtifactId']
          and meta.get('name')==policy['proofArtifactName']
          and meta.get('expired') is False
          and meta.get('digest')=='sha256:'+policy['proofArtifactDigest']
          and (meta.get('workflow_run') or {}).get('id')==policy['proofRunId'],
          'artefato de auditoria não confiável')

def items_from_selection(s, profile):
    check(isinstance(s,dict) and s.get('schemaVersion')==1
          and s.get('status')=='SAFE_READY' and s.get('publishReady') is True
          and s.get('dryRun') is True, 'seleção não passou por SAFE')
    check(s.get('blogId')==profile['blog_id'], 'seleção de outro blog')
    cats=profile['categories'];groups=s.get('categories')
    check(isinstance(groups,dict) and list(groups)==cats,'categorias divergentes')
    result=[]
    for cat in cats:
        subset=groups[cat]
        check(isinstance(subset,list) and len(subset)==profile['per_category'][cat],
              'quantidade inválida da categoria')
        for p in subset:
            ident=str(p.get('itemId') or '')
            check(re.fullmatch(r'[0-9]{4,25}',ident) is not None and p.get('category')==cat,
                  'id ou categoria inválidos')
            result.append({'itemId':ident,'category':cat})
    count=profile['expected_products']
    check(count==16 and len(result)==count and len({i['itemId'] for i in result})==count
          and s.get('totalItems')==count and s.get('uniqueItemIds')==count,
          '16 produtos únicos obrigatórios no contrato atual')
    return result

def valid_public_proof(proof,policy,profile):
    count=profile['expected_products']
    check(isinstance(proof,dict) and proof.get('status')=='PUBLIC_EXACT_PASS'
          and proof.get('public_verified') is True
          and proof.get('publication_attempted') is False
          and proof.get('transport')=='CLOUDFLARE_BROWSER_RENDERING'
          and proof.get('public_http')==200, 'prova pública não autenticada/aceita')
    check(proof.get('selection_sha256')==policy['selectionSha']
          and proof.get('cards')==count and proof.get('images')==count
          and proof.get('links')==count and proof.get('categories')==len(profile['categories']),
          'quantidade/identidade da seleção pública inconsistente')
    check(hexsha(proof.get('public_html_sha256')),'hash HTML público ausente')
    check(get_time(proof.get('verified_at_utc'))>get_time(policy['publishedAt']),
          'verificação pública anterior à publicação')

def reconcile(*,policy,original_state,seed_history,selection_bytes,
              original_proof_bytes,fresh_proof,profile,run_meta,artifact_meta,now=None):
    validate_policy(policy)
    check(profile.get('blog_id')==policy['blogId']
          and profile.get('page_id')==policy['pageId']
          and profile.get('page_url')==policy['pageUrl']
          and profile.get('mode')=='SAFE', 'perfil fora do LAB')
    check(sha256(selection_bytes).hexdigest()==policy['selectionSha'],'SHA-256 de seleção divergente')
    check(sha256(original_proof_bytes).hexdigest()==policy['originalProofSha'],
          'prova original foi modificada')
    items=items_from_selection(json.loads(selection_bytes),profile)
    validate_run(run_meta,policy)
    validate_artifact(artifact_meta,policy)
    proof=json.loads(original_proof_bytes)
    valid_public_proof(proof,policy,profile)
    valid_public_proof(fresh_proof,policy,profile)
    check(get_time(fresh_proof['verified_at_utc']) >= get_time(proof['verified_at_utc']),
          'prova nova anterior à prova original')
    now=now or datetime.now(timezone.utc)
    check(now.tzinfo is not None,'agora sem timezone')
    seconds=(now.astimezone(timezone.utc)-get_time(fresh_proof['verified_at_utc'])).total_seconds()
    check(0<=seconds<=900,'prova recente expirada (15 minutos)')
    check(original_state.get('blogId')==policy['blogId']
          and original_state.get('pageId')==policy['pageId'],'estado de outro blog')
    validate_state(original_state)
    ops=original_state.get('operations',[])
    oid=operation_id(policy['selectionSha'],policy['blogId'],policy['pageId'])
    check(len(ops)==1 and ops[0].get('operationId')==oid,'operação não única')
    op=ops[0]
    check(op.get('status')=='PUBLISHED_PENDING_PUBLIC'
          and op.get('pageUpdatedAt')==policy['publishedAt']
          and op.get('publishRunId')==policy['publishRunId']
          and op.get('shopeeSelectionRunId')==policy['selectionRunId'],
          'registro de publicação diferente')
    check(hexsha(op.get('originalSha')) and hexsha(op.get('candidateSha'))
          and op['originalSha'] != op['candidateSha'], 'hash da página original/candidata inválido')
    check(seed_history.get('version')==1 and seed_history.get('blogId')==policy['blogId']
          and len(seed_history.get('runs',[]))==1
          and seed_history['runs'][0].get('source')=='seed_from_current_blogger_store'
          and seed_history['runs'][0].get('pageId')==policy['pageId'],
          'histórico anterior não é seed esperado')
    seed_items=seed_history['runs'][0].get('items',[])
    check(len(seed_items)==16 and len({str(i['itemId']) for i in seed_items})==16
          and not {str(i['itemId']) for i in seed_items}.intersection({i['itemId'] for i in items}),
          'histórico anterior inconsistente ou seleção repetida')
    published=mark_public_verified(original_state,policy['selectionSha'],proof=fresh_proof)
    new_state,new_history=history_commit(published,policy['selectionSha'],seed_history,
                                          published_items=items,published_at=policy['publishedAt'])
    new_state['operations'][0]['publicProof']={
        'sourceRun':policy['proofRunId'],
        'sourceArtifact':policy['proofArtifactId'],
        'sourceArtifactDigest':'sha256:'+policy['proofArtifactDigest'],
        'sourceProofSha256':policy['originalProofSha'],
        'verifiedAt':fresh_proof['verified_at_utc'],
        'htmlSha256':fresh_proof['public_html_sha256'],
        'transport':fresh_proof['transport'],
    }
    validate_state(new_state)
    check(len(new_history['runs'])==2 and new_state['operations'][0]['status']=='PERSISTED',
          'histórico não persistido no modelo')
    return new_state,new_history