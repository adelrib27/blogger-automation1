"""Pure, portable, offline fail-closed contract tests for atomic V31 history pair."""
import copy
import hashlib
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'v31_core'))
import v31_atomic_rotation as ar
from v31_rotation_ledger import operation_id

CATEGORIES=['Decoração','Organização','Cozinha','Quarto']
BID='4739187376492839837'
PID='2446067640331732447'

def fixture():
    products={}
    for k,cat in enumerate(CATEGORIES):
        products[cat]=[{'itemId':str(21000000001 + k*4+j), 'category':cat} for j in range(4)]
    selected={'schemaVersion':1,'status':'SAFE_READY','publishReady':True,'dryRun':True,
              'blogId':BID,'totalItems':16,'uniqueItemIds':16,'categories':products}
    b=json.dumps(selected).encode()
    sha=hashlib.sha256(b).hexdigest()
    pub='2026-11-03T22:19:09-03:00'
    state={'schema':1,'blogId':BID,'pageId':PID,'operations':[
        {'operationId':operation_id(sha,BID,PID),'selectionSha':sha,'originalSha':'b'*64,
         'candidateSha':'c'*64,'status':'PUBLISHED_PENDING_PUBLIC',
         'publishRunId':41753180692,'shopeeSelectionRunId':41751202914,'pageUpdatedAt':pub}]}
    seed={'version':1,'blogId':BID,'runs':[
        {'timestamp':'2026-11-03T21:27:35-03:00','source':'seed_from_current_blogger_store',
         'pageId':PID,'items':[{'itemId':str(12000000001+i),'category':CATEGORIES[i//4]} for i in range(16)]}]}
    proof={'status':'PUBLIC_EXACT_PASS','public_http':200,'cards':16,'images':16,'links':16,
           'categories':4,'selection_sha256':sha,'transport':'CLOUDFLARE_BROWSER_RENDERING',
           'public_verified':True,'publication_attempted':False,
           'public_html_sha256':'d'*64,
           'verified_at_utc':'2026-11-04T03:45:55+00:00'}
    fresh=copy.deepcopy(proof)
    fresh['verified_at_utc']=datetime.now(timezone.utc).isoformat()
    fresh['public_html_sha256']='e'*64
    run={'id':41769090187,'status':'completed','conclusion':'success','event':'push',
         'head_branch':'lab/v31r1-shopee-safe-20261103','head_sha':'169f3993578679045ea554097108fce8416fb811','path':'.github/workflows/v31_lab_cloudflare_public_live_readonly.yml',
         'repository':{'full_name':'adelrib27/blogger-automation1'}}
    artifact={'id':13294391153,'name':'v31-lab-cloudflare-public-proof-1',
              'expired':False,'digest':'sha256:'+'c04f72657bb4d344216cfce537cf6917e88f91de2edd6f9c0ccc5f4093f4c498',
              'workflow_run':{'id':41769090187}}
    profile={'blog_id':BID,'page_id':PID,
             'page_url':'https://blog-teste-tema-worpress.blogspot.com/p/loja.html',
             'mode':'SAFE','expected_products':16,
             'categories':CATEGORIES,'per_category':{c:4 for c in CATEGORIES}}
    rawproof=json.dumps(proof).encode()
    policy={'schema':1,'mode':'LAB','blogId':BID,'pageId':PID,'pageUrl':profile['page_url'],
            'repository':'adelrib27/blogger-automation1','branch':ar.PROOF_BRANCH if hasattr(ar,'PROOF_BRANCH') else 'lab/v31r1-shopee-safe-20261103',
            'selectionSha':sha,'proofRunId':41769090187,'proofArtifactId':13294391153,
            'proofArtifactDigest':'c04f72657bb4d344216cfce537cf6917e88f91de2edd6f9c0ccc5f4093f4c498',
            'originalProofSha':hashlib.sha256(rawproof).hexdigest(),
            'proofArtifactName':'v31-lab-cloudflare-public-proof-1',
            'proofWorkflow':'.github/workflows/v31_lab_cloudflare_public_live_readonly.yml',
            'proofCommitSha':'169f3993578679045ea554097108fce8416fb811',
            'publishedAt':pub,'publishRunId':41753180692,'selectionRunId':41751202914}
    return sha,dict(policy=policy,original_state=state,seed_history=seed,selection_bytes=b,
                    original_proof_bytes=rawproof,fresh_proof=fresh,
                    profile=profile,run_meta=run,artifact_meta=artifact)

class AtomicRotationContract(unittest.TestCase):
    def setUp(self):
        self.sha,self.data=fixture()
    def ok(self,**overrides):
        x=copy.deepcopy(self.data)
        x.update(overrides)
        return ar.reconcile(**x)
    def reject(self,**overrides):
        with self.assertRaises((ar.ReconcileError,ValueError)):
            self.ok(**overrides)
    def test_valid_atomic_pair(self):
        st,h=self.ok()
        self.assertEqual(st['operations'][0]['status'],'PERSISTED')
        self.assertEqual(len(h['runs']),2)
        self.assertEqual(h['runs'][1]['selectionSha'],self.sha)
        self.assertEqual(len(h['runs'][1]['items']),16)
        self.assertEqual(st['operations'][0]['publicProof']['sourceRun'],41769090187)
    def test_no_input_mutation(self):
        before=copy.deepcopy(self.data);self.ok();self.assertEqual(self.data,before)
    def test_canonical_deterministic(self):
        a=self.ok(); b=self.ok();self.assertEqual(ar.canonical(a[0]),ar.canonical(b[0]));self.assertEqual(ar.canonical(a[1]),ar.canonical(b[1]))
    def test_wrong_sha(self):self.reject(selection_bytes=b'{}')
    def test_cross_blog_profile(self):
        p=copy.deepcopy(self.data['profile']);p['blog_id']='999';self.reject(profile=p)
    def test_cross_page_profile(self):
        p=copy.deepcopy(self.data['profile']);p['page_id']='999';self.reject(profile=p)
    def test_foreign_selection(self):
        s=json.loads(self.data['selection_bytes']);s['blogId']='999';raw=json.dumps(s).encode()
        p=copy.deepcopy(self.data['policy']);p['selectionSha']=hashlib.sha256(raw).hexdigest();self.reject(selection_bytes=raw,policy=p)
    def test_duplicate_item(self):
        s=json.loads(self.data['selection_bytes']);s['categories'][CATEGORIES[0]][1]['itemId']=s['categories'][CATEGORIES[0]][0]['itemId'];raw=json.dumps(s).encode()
        p=copy.deepcopy(self.data['policy']);p['selectionSha']=hashlib.sha256(raw).hexdigest();self.reject(selection_bytes=raw,policy=p)
    def test_state_not_pending(self):
        s=copy.deepcopy(self.data['original_state']);s['operations'][0]['status']='PLAN';self.reject(original_state=s)
    def test_additional_active_operation(self):
        s=copy.deepcopy(self.data['original_state']);s['operations'].append(copy.deepcopy(s['operations'][0]));self.reject(original_state=s)
    def test_wrong_operation_source_run(self):
        s=copy.deepcopy(self.data['original_state']);s['operations'][0]['publishRunId']=1;self.reject(original_state=s)
    def test_proof_from_other_selection(self):
        p=json.loads(self.data['original_proof_bytes']);p['selection_sha256']='a'*64;self.reject(original_proof_bytes=json.dumps(p).encode())
    def test_proof_pending(self):
        p=copy.deepcopy(self.data['fresh_proof']);p['status']='PUBLIC_PENDING_THROTTLED';self.reject(fresh_proof=p)
    def test_proof_incomplete_items(self):
        p=copy.deepcopy(self.data['fresh_proof']);p['images']=15;self.reject(fresh_proof=p)
    def test_proof_expired(self):
        p=copy.deepcopy(self.data['fresh_proof']);p['verified_at_utc']='2026-11-04T03:46:00+00:00';self.reject(fresh_proof=p)
    def test_proof_before_publish(self):
        p=copy.deepcopy(self.data['fresh_proof']);p['verified_at_utc']='2020-01-01T00:00:00+00:00';self.reject(fresh_proof=p)
    def test_run_failed(self):
        p=copy.deepcopy(self.data['run_meta']);p['conclusion']='failure';self.reject(run_meta=p)
    def test_other_run_commit(self):
        p=copy.deepcopy(self.data['run_meta']);p['head_sha']='a'*40;self.reject(run_meta=p)
    def test_other_workflow(self):
        p=copy.deepcopy(self.data['run_meta']);p['path']='.github/workflows/evil.yml';self.reject(run_meta=p)
    def test_other_repo(self):
        p=copy.deepcopy(self.data['run_meta']);p['repository']['full_name']='not/right';self.reject(run_meta=p)
    def test_tampered_artifact_digest(self):
        p=copy.deepcopy(self.data['artifact_meta']);p['digest']='sha256:'+'b'*64;self.reject(artifact_meta=p)
    def test_artifact_not_from_run(self):
        p=copy.deepcopy(self.data['artifact_meta']);p['workflow_run']['id']=10;self.reject(artifact_meta=p)
    def test_untrusted_seed(self):
        p=copy.deepcopy(self.data['seed_history']);p['runs'][0]['source']='manual';self.reject(seed_history=p)
    def test_seed_overlap(self):
        p=copy.deepcopy(self.data['seed_history']);p['runs'][0]['items'][0]['itemId']='21000000001';self.reject(seed_history=p)
    def test_wrong_ledger_hash_pair(self):
        p=copy.deepcopy(self.data['original_state']);p['operations'][0]['candidateSha']='invalid';self.reject(original_state=p)

if __name__=='__main__':unittest.main()