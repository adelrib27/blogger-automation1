#!/usr/bin/env python3
"""Reconcile a verified V31 LAB rotation; write two JSON files for ONE atomic Git commit.

No Blogger write, no Cloudflare call. Caller must run fresh public verifier first;
this script validates GitHub run+artifact origin and computes the exact state pair.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'v31_core'))
from v31_atomic_rotation import (canonical,reconcile,validate_policy,
                                  validate_artifact,validate_run,ReconcileError)

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

OPEN=build_opener(NoRedirect)

def get_json(url:str,token:str) -> dict:
    if not isinstance(token,str) or len(token)<15:
        raise ReconcileError('Credencial GitHub ausente; fail-closed')
    req=Request(url,headers={'Authorization':'Bearer '+token,
                             'Accept':'application/vnd.github+json',
                             'X-GitHub-Api-Version':'2022-11-28',
                             'User-Agent':'V31-LAB-AtomicRotation/1.0'})
    try:
        with OPEN.open(req,timeout=25) as r:
            if r.status!=200: raise ReconcileError('GitHub retornou não 200')
            data=r.read(1048576+1)
            if len(data)>1048576: raise ReconcileError('GitHub response oversized')
    except (HTTPError,URLError,TimeoutError) as e:
        raise ReconcileError('GitHub metadata unavailable; fail-closed') from e
    try:return json.loads(data)
    except ValueError as e:raise ReconcileError('GitHub metadata not JSON') from e

def github_provenance(policy:dict,token:str)->tuple[dict,dict]:
    validate_policy(policy)
    base='https://api.github.com/repos/'+policy['repository']
    run=get_json(base+'/actions/runs/'+str(policy['proofRunId']),token)
    validate_run(run,policy)
    arts=get_json(base+'/actions/runs/'+str(policy['proofRunId'])+'/artifacts?per_page=100',token)
    items=arts.get('artifacts') if isinstance(arts,dict) else None
    if not isinstance(items,list):raise ReconcileError('GitHub artifacts missing')
    matches=[item for item in items if item.get('id')==policy['proofArtifactId']]
    if len(matches)!=1:raise ReconcileError('GitHub proof artifact not unique')
    validate_artifact(matches[0],policy)
    return run,matches[0]

def check_destinations(state_path:Path,history_path:Path):
    if state_path.exists() or history_path.exists():
        raise ReconcileError('Canonical ledger/history already present; do not overwrite/retry')

def write_atomically_prepared_files(args,token:str):
    paths=(args.ledger_output,args.history_output)
    check_destinations(*paths)
    policy=json.loads(args.policy.read_text(encoding='utf-8'))
    run,artifact=github_provenance(policy,token)
    state,hist=reconcile(policy=policy,
         original_state=json.loads(args.pending.read_text(encoding='utf-8')),
         seed_history=json.loads(args.seed.read_text(encoding='utf-8')),
         selection_bytes=args.selection.read_bytes(),
         original_proof_bytes=args.proof.read_bytes(),
         fresh_proof=json.loads(args.fresh_proof.read_text(encoding='utf-8')),
         profile=json.loads(args.profile.read_text(encoding='utf-8')),
         run_meta=run,artifact_meta=artifact)
    s,h=canonical(state),canonical(hist)
    metadata={'status':'ATOMIC_PAIR_SAFE_READY','blogId':policy['blogId'],
              'pageId':policy['pageId'],'proofRunId':policy['proofRunId'],
              'proofArtifactId':policy['proofArtifactId'],
              'operationId':state['operations'][0]['operationId'],
              'ledgerSha256':sha256(s.encode()).hexdigest(),
              'historySha256':sha256(h.encode()).hexdigest(),
              'historyRuns':len(hist['runs']),
              'publicationAttempted':False,'gitCommitted':False}
    if args.dry_run: return metadata
    # Do not stage/commit this transaction until ALL inputs and both outputs validate.
    for p in paths:p.parent.mkdir(parents=True,exist_ok=True)
    # Files are new: exclusive creation; avoid overwriting concurrent in-filesystem changes.
    created=[]
    try:
        for p,value in zip(paths,(s,h)):
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(value)
            created.append(p)
    except Exception:
        for p in created:
            try:p.unlink()
            except OSError:pass
        raise
    metadata['status']='ATOMIC_PAIR_WRITTEN_LOCALLY_AWAITING_SINGLE_GIT_COMMIT'
    return metadata

def main():
    ap=argparse.ArgumentParser()
    for key in ('policy','pending','seed','selection','proof','fresh-proof','profile',
                'ledger-output','history-output'):
        ap.add_argument('--'+key,required=True,type=Path,dest=key.replace('-','_'))
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    try:
        result=write_atomically_prepared_files(args,os.environ.get('GITHUB_TOKEN',''))
        print(json.dumps(result,sort_keys=True));return 0
    except Exception as e:
        print(json.dumps({'status':'FAIL_CLOSED_NO_COMMIT','error_type':type(e).__name__,
                          'reason':str(e)[:140]}))
        return 2
if __name__=='__main__':sys.exit(main())