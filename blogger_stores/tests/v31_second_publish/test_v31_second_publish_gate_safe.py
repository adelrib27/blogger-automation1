"""Offline SAFE tests. Fixtures model a first persisted + second PLAN. No network/IO."""
import copy
from hashlib import sha256
from html import escape
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'v31_core'))
from v31_second_publish_gate_safe import (
    REPOSITORY, BRANCH, BLOG_ID, PAGE_ID, PAGE_URL, CATEGORIES, START, END,
    GateBlocked, gate_second_publish_safe, sha256hex, gitblob,
)

def enc(obj):
    return (json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode()

def products(base):
    result=[]
    for cat_index,cat in enumerate(CATEGORIES):
        for i in range(4):
            ident=str(base+cat_index*4+i)
            result.append({'itemId':ident,'category':cat,
                  'affiliateUrl':'https://s.shopee.com.br/'+ident,
                  'imageUrl':'https://cf.shopee.com.br/file/'+ident})
    return result

def page(items):
    content=''.join('<article class="ub-product-card" data-item-id="'+p['itemId']+'">'+
                    '<div class="ub-product-image"><img src="'+p['imageUrl']+'"/></div>'+
                    '<a class="ub-product-action" href="'+p['affiliateUrl']+'">Oferta</a></article>'
                    for p in items)
    # minimum 5000 bytes, like real LIVE Blogger payload
    return ('<div id="cp-loja">\n'+START+'\n<!-- safe filler '+('x'*6000)+' -->\n'+content+'\n'+END+'\n</div>').encode()

def fixture():
    old=products(10000); prior=products(20000); chosen=products(30000)
    h={'blogId':BLOG_ID,'version':1,'runs':[
        {'source':'seed_from_current_blogger_store','pageId':PAGE_ID,'items':old},
        {'source':'blogger_published','pageId':PAGE_ID,'items':prior,
         'operationId':'a'*64,'selectionSha':'b'*64}]}
    original=page(prior); candidate=page(chosen)
    selection={'schemaVersion':1,'status':'SAFE_READY','dryRun':True,'publishReady':True,
        'blogId':BLOG_ID,'totalItems':16,'uniqueItemIds':16,
        'gates':{key:True for key in ('allLinksResolved','semanticRulesApplied','finalProductGate',
                                    'failClosed','allPhotosPresent','expectedCategories','expectedItems')},
        'categories':{cat:chosen[i*4:(i+1)*4] for i,cat in enumerate(CATEGORIES)}}
    sel=enc(selection); selection_sha=sha256hex(sel);origsha=sha256hex(original);candsha=sha256hex(candidate)
    oid=sha256((BLOG_ID+'|'+PAGE_ID+'|'+selection_sha).encode()).hexdigest()
    led={'schema':1,'blogId':BLOG_ID,'pageId':PAGE_ID,'operations':[
       {'status':'PERSISTED','operationId':'a'*64,'selectionSha':'b'*64,
        'originalSha':'c'*64,'candidateSha':origsha},
       {'status':'PLAN','operationId':oid,'selectionSha':selection_sha,
        'originalSha':origsha,'candidateSha':candsha}]}
    profile={'mode':'SAFE','blog_id':BLOG_ID,'page_id':PAGE_ID,'page_url':PAGE_URL,
             'categories':list(CATEGORIES),'expected_products':16,
             'per_category':{cat:4 for cat in CATEGORIES}}
    ledger,hist=enc(led),enc(h)
    pins={'selection':selection_sha,'original':origsha,'candidate':candsha,
          'ledger_blob':gitblob(ledger),'history_blob':gitblob(hist),'operation':oid}
    return dict(repository=REPOSITORY,branch=BRANCH,branch_head='d'*40,
        reservation_is_ancestor=True,profile_bytes=enc(profile),ledger_bytes=ledger,
        history_bytes=hist,selection_bytes=sel,original_html_bytes=original,
        candidate_html_bytes=candidate,observed_blogger_html_bytes=original,pins=pins)

class SecondPublishGate(unittest.TestCase):
    def setUp(self):self.a=fixture()
    def run_gate(self,**updates):
        p={**self.a,**updates}
        return gate_second_publish_safe(**p)
    def blocked(self,**updates):
        with self.assertRaises(GateBlocked):self.run_gate(**updates)
    def test_clean_plan_recognized_without_put(self):
        r=self.run_gate()
        self.assertEqual(r['decision'],'EXISTING_PLAN_READBACK_ORIGINAL_SEPARATE_APPROVAL_REQUIRED')
        self.assertEqual(r['ledger_statuses'],['PERSISTED','PLAN'])
        self.assertFalse(r['blogger_put_allowed'])
        self.assertFalse(r['git_write_allowed'])
        self.assertFalse(r['cron_allowed'])
    def test_candidate_already_received_blogger_prevents_reput(self):
        r=self.run_gate(observed_blogger_html_bytes=self.a['candidate_html_bytes'])
        self.assertEqual(r['decision'],'CANDIDATE_ALREADY_IN_BLOGGER_SKIP_PUT_VERIFY_PUBLIC_ONLY')
    def test_wrong_repo(self):self.blocked(repository='other/foo')
    def test_wrong_branch(self):self.blocked(branch='main')
    def test_wrong_head(self):self.blocked(branch_head='nope')
    def test_missing_reservation_ancestry(self):self.blocked(reservation_is_ancestor=False)
    def test_unknown_blogger_html(self):self.blocked(observed_blogger_html_bytes=b'stale')
    def test_history_blob_changed(self):self.blocked(history_bytes=self.a['history_bytes']+b' ')
    def test_ledger_blob_changed(self):self.blocked(ledger_bytes=self.a['ledger_bytes']+b' ')
    def test_selection_sha_changed(self):self.blocked(selection_bytes=self.a['selection_bytes']+b' ')
    def test_original_html_sha_changed(self):self.blocked(original_html_bytes=self.a['original_html_bytes']+b' ')
    def test_candidate_html_sha_changed(self):self.blocked(candidate_html_bytes=self.a['candidate_html_bytes']+b' ')
    def test_extra_pending_operation(self):
        led=json.loads(self.a['ledger_bytes']);led['operations'].append(copy.deepcopy(led['operations'][-1]))
        self.blocked(ledger_bytes=enc(led),pins={**self.a['pins'],'ledger_blob':gitblob(enc(led))})
    def test_already_persisted_second_op(self):
        led=json.loads(self.a['ledger_bytes']);led['operations'][-1]['status']='PERSISTED'
        self.blocked(ledger_bytes=enc(led),pins={**self.a['pins'],'ledger_blob':gitblob(enc(led))})
    def test_operation_identity_changed(self):
        led=json.loads(self.a['ledger_bytes']);led['operations'][-1]['operationId']='f'*64
        self.blocked(ledger_bytes=enc(led),pins={**self.a['pins'],'ledger_blob':gitblob(enc(led))})
    def test_first_op_no_longer_persisted(self):
        led=json.loads(self.a['ledger_bytes']);led['operations'][0]['status']='PLAN'
        self.blocked(ledger_bytes=enc(led),pins={**self.a['pins'],'ledger_blob':gitblob(enc(led))})
    def test_duplicate_item_in_selection(self):
        d=json.loads(self.a['selection_bytes']);d['categories'][CATEGORIES[0]][1]['itemId']=d['categories'][CATEGORIES[0]][0]['itemId']
        self.blocked(selection_bytes=enc(d),pins={**self.a['pins'],'selection':sha256hex(enc(d))})
    def test_unknown_shopee_affiliate(self):
        d=json.loads(self.a['selection_bytes']);d['categories'][CATEGORIES[0]][0]['affiliateUrl']='https://attacker.example/1'
        self.blocked(selection_bytes=enc(d),pins={**self.a['pins'],'selection':sha256hex(enc(d))})
    def test_missing_photo(self):
        d=json.loads(self.a['selection_bytes']);d['gates']['allPhotosPresent']=False
        self.blocked(selection_bytes=enc(d),pins={**self.a['pins'],'selection':sha256hex(enc(d))})
    def test_history_includes_new_product(self):
        d=json.loads(self.a['history_bytes']);d['runs'][0]['items'][0]['itemId']='30000'
        self.blocked(history_bytes=enc(d),pins={**self.a['pins'],'history_blob':gitblob(enc(d))})
    def test_history_has_extra_entry(self):
        d=json.loads(self.a['history_bytes']);d['runs'].append(copy.deepcopy(d['runs'][-1]))
        self.blocked(history_bytes=enc(d),pins={**self.a['pins'],'history_blob':gitblob(enc(d))})
    def test_original_website_ids_mismatch_history(self):
        modified=page(products(11111))
        self.blocked(original_html_bytes=modified,pins={**self.a['pins'],'original':sha256hex(modified)})
    def test_candidate_ids_out_of_order(self):
        p=products(30000);p[0],p[1]=p[1],p[0];new=page(p)
        self.blocked(candidate_html_bytes=new,pins={**self.a['pins'],'candidate':sha256hex(new)})
    def test_candidate_links_mismatch(self):
        p=products(30000);p[0]['affiliateUrl']='https://s.shopee.com.br/wrong';new=page(p)
        self.blocked(candidate_html_bytes=new,pins={**self.a['pins'],'candidate':sha256hex(new)})
    def test_candidate_images_mismatch(self):
        p=products(30000);p[0]['imageUrl']='https://cf.shopee.com.br/file/wrong';new=page(p)
        self.blocked(candidate_html_bytes=new,pins={**self.a['pins'],'candidate':sha256hex(new)})
    def test_candidate_outside_markers_changed(self):
        new=self.a['candidate_html_bytes'].replace(b'</div>',b'<!--x--></div>')
        self.blocked(candidate_html_bytes=new,pins={**self.a['pins'],'candidate':sha256hex(new)})
    def test_candidate_injected_script(self):
        new=self.a['candidate_html_bytes'].replace(END.encode(),b'<script src="evil.js"></script>'+END.encode())
        self.blocked(candidate_html_bytes=new,pins={**self.a['pins'],'candidate':sha256hex(new)})
    def test_invalid_page_root(self):
        old=self.a['original_html_bytes'].replace(b'cp-loja',b'evil-x')
        self.blocked(original_html_bytes=old,pins={**self.a['pins'],'original':sha256hex(old)})
    def test_wrong_profile_target(self):
        d=json.loads(self.a['profile_bytes']);d['page_id']='1000'
        self.blocked(profile_bytes=enc(d))
    def test_wrong_profile_mode(self):
        d=json.loads(self.a['profile_bytes']);d['mode']='LIVE'
        self.blocked(profile_bytes=enc(d))
    def test_no_implicit_live_proof(self):
        r=self.run_gate();self.assertFalse(r['observed_blogger_live_authenticated'])
        r=self.run_gate(observed_blogger_is_authenticated_live=True)
        self.assertTrue(r['observed_blogger_live_authenticated'])
        self.assertFalse(r['blogger_put_allowed'])
    def test_all_inputs_immutable(self):
        original=copy.deepcopy(self.a);self.run_gate();self.assertEqual(self.a,original)

if __name__=='__main__': unittest.main()
