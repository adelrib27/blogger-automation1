"""Focused offline checks for the V31 daily dynamic candidate gate, no IO."""
import importlib.util
import json
from datetime import datetime, timedelta, time, timezone
from hashlib import sha256
from pathlib import Path
from zoneinfo import ZoneInfo
import unittest

MODULE = Path(__file__).resolve().parents[2] / 'src' / 'v31_daily_candidate_contract_safe.py'
SPEC = importlib.util.spec_from_file_location('v31_daily_candidate_contract_safe', MODULE)
SAFE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SAFE)
from v31_rotation_ledger import operation_id
from v31_store_safe import initial_page, SCHEMA

RECIFE = ZoneInfo('America/Recife')
CATS = ['Decoração', 'Organização', 'Cozinha', 'Quarto']
PROFILE = {
    'blog_id': SAFE.REPO and '4739187376492839837',
    'page_id': '2446067640331732447',
    'page_url': 'https://blog-teste-tema-worpress.blogspot.com/p/loja.html',
    'blog_host': 'blog-teste-tema-worpress.blogspot.com',
    'mode': 'SAFE', 'categories': CATS, 'expected_products': 16,
    'per_category': {c: 4 for c in CATS},
}


def product(item_id, cat, mode='new'):
    return {
        'itemId': str(item_id), 'productName': 'Produto verificado de teste '+str(item_id),
        'shopName': 'Loja Verificada', 'priceMin': '49.90',
        'affiliateUrl': 'https://s.shopee.com.br/aa'+str(item_id),
        'imageUrl': 'https://cf.shopee.com.br/file/'+str(item_id),
        'category': cat, 'source': 'shopee_affiliate_open_api',
        'rotationSelectionMode': mode,
    }


def items(start):
    return [product(start+i, CATS[i//4]) for i in range(16)]


def setup():
    now = datetime.now(RECIFE)
    previous_date = (now - timedelta(days=1)).date()
    seed_at = datetime.combine(previous_date - timedelta(days=2), time(10, 0), RECIFE)
    first_at = datetime.combine(previous_date - timedelta(days=1), time(11, 0), RECIFE)
    last_at = datetime.combine(previous_date, time(12, 0), RECIFE)
    old = items(1300000)
    original_catalog = {
        'schema': SCHEMA, 'source': 'fixture_offline',
        'blog_id': PROFILE['blog_id'], 'page_id': PROFILE['page_id'],
        'products': [
            {'item_id':x['itemId'], 'name':x['productName'],
             'category':x['category'], 'affiliate_url':x['affiliateUrl'],
             'image_url':x['imageUrl'], 'price_brl':x['priceMin'],
             'available': True, 'policy_allowed': True} for x in old
        ],
    }
    current = initial_page(original_catalog, PROFILE, allow_fixture=True).encode('utf-8')
    current_sha = sha256(current).hexdigest()
    h1, h2 = 'a'*64, 'b'*64
    s1, s2 = 'c'*64, 'd'*64
    op1 = {'operationId':operation_id(s1,PROFILE['blog_id'],PROFILE['page_id']),
           'selectionSha':s1,'originalSha':h1,'candidateSha':h2,
           'status':'PERSISTED', 'pageUpdatedAt':first_at.isoformat(),
           'publicProof':{'transport':'CLOUDFLARE_BROWSER_RENDERING','htmlSha256':h2,
                          'sourceRun':41769090187,'verifiedAt':first_at.isoformat(),
                          'cards':16,'images':16,'links':16,'categories':4,'publicHttp':200}}
    op2 = {'operationId':operation_id(s2,PROFILE['blog_id'],PROFILE['page_id']),
           'selectionSha':s2,'originalSha':h2,'candidateSha':current_sha,
           'status':'PERSISTED', 'pageUpdatedAt':last_at.isoformat(),
           'prewriteClaim':{'state':'ATTEMPT_CLAIMED_BEFORE_PUT','backupSha256':h2},
           'publicProof':{'transport':'CLOUDFLARE_BROWSER_RENDERING','htmlSha256':current_sha,
                          'sourceRun':41938854284,'verifiedAt':last_at.isoformat(),
                          'cards':16,'images':16,'links':16,'categories':4,'publicHttp':200}}
    ledger = {'schema':1,'blogId':PROFILE['blog_id'],'pageId':PROFILE['page_id'],
              'operations':[op1,op2]}
    history = {'version':1,'blogId':PROFILE['blog_id'],'runs':[
        {'source':'seed_from_current_blogger_store','pageId':PROFILE['page_id'],
         'timestamp':seed_at.isoformat(),'items':items(1100000)},
        {'source':'blogger_published','pageId':PROFILE['page_id'],
         'operationId':op1['operationId'],'selectionSha':s1,
         'timestamp':first_at.isoformat(),'items':items(1200000)},
        {'source':'blogger_published','pageId':PROFILE['page_id'],
         'operationId':op2['operationId'],'selectionSha':s2,
         'timestamp':last_at.isoformat(),'items':old},
    ]}
    groups = {cat:items(1400000)[i*4:(i+1)*4] for i,cat in enumerate(CATS)}
    selection = {
        'schemaVersion':1,'status':'SAFE_READY','publishReady':True,'dryRun':True,
        'blogId':PROFILE['blog_id'],'timestamp':(now-timedelta(minutes=5)).isoformat(),
        'totalItems':16,'uniqueItemIds':16,'categories':groups,
        'gates':{'allLinksResolved':True,'semanticRulesApplied':True,
                 'finalProductGate':True,'failClosed':True,'allPhotosPresent':True,
                 'expectedCategories':True,'expectedItems':True},
        'semanticValidation':{'finalProductGate':True,'strictAccessoriesBlocked':True},
        'affiliateLinkGeneration':{'method':'generateShortLink',
                                   'validatedCount':16,'allResolvedToShopee':True},
    }
    return now, ledger, history, selection, current


def invoke(now, ledger, history, selection, current, *, profile=None, policy=None):
    raw = (json.dumps(selection,ensure_ascii=False)+'\n').encode('utf-8')
    return SAFE.preview_daily_candidate(
        profile=profile or PROFILE, ledger=ledger, history=history,
        selection_bytes=raw, current_page_bytes=current,
        now=now, policy_guard=policy or (lambda product: None))


class TestDailyCandidate(unittest.TestCase):
    def test_fresh_dynamic_plan_only(self):
        s=setup(); result=invoke(*s)
        self.assertEqual(result['status'],'V31_LAB_DAILY_CANDIDATE_DYNAMIC_SAFE_ONLY')
        self.assertEqual(result['cards'],16)
        self.assertEqual(len(result['proposedLedger']['operations']),3)
        self.assertEqual(result['proposedLedger']['operations'][-1]['status'],'PLAN')
        self.assertFalse(result['bloggerPutAllowed'])
        self.assertFalse(result['gitRemoteWriteAllowed'])
        self.assertFalse(result['cronEnabled'])
        self.assertFalse(result['publicationAuthorized'])

    def test_recent_id_not_new(self):
        now,l,h,sel,html=setup()
        sel['categories'][CATS[0]][0]['itemId']='1100000'
        with self.assertRaises(SAFE.DailyCandidateBlocked):invoke(now,l,h,sel,html)

    def test_older_fallback_allowed(self):
        now,l,h,sel,html=setup()
        p=sel['categories'][CATS[0]][0]
        p['itemId']='1200000';p['rotationSelectionMode']='fallback_older'
        self.assertEqual(invoke(now,l,h,sel,html)['rotationModes']['fallback_older'],1)

    def test_last_run_cannot_claim_older_fallback(self):
        now,l,h,sel,html=setup()
        p=sel['categories'][CATS[0]][0]
        p['itemId']='1300000';p['rotationSelectionMode']='fallback_older'
        with self.assertRaises(SAFE.DailyCandidateBlocked):invoke(now,l,h,sel,html)

    def test_carry_forward_one_item_allowed(self):
        now,l,h,sel,html=setup()
        p=sel['categories'][CATS[0]][0]
        p['itemId']='1300000';p['rotationSelectionMode']='carry_forward_last'
        self.assertEqual(invoke(now,l,h,sel,html)['rotationModes']['carry_forward_last'],1)

    def test_wrong_carry_forward_id_blocked(self):
        now,l,h,sel,html=setup()
        p=sel['categories'][CATS[0]][0]
        p['rotationSelectionMode']='carry_forward_last'
        with self.assertRaises(SAFE.DailyCandidateBlocked):invoke(now,l,h,sel,html)

    def test_no_change_in_entire_vitrine_blocked(self):
        now,l,h,sel,html=setup()
        for i,cat in enumerate(CATS):
            for j,p in enumerate(sel['categories'][cat]):
                p['itemId']=str(1300000+4*i+j)
                p['rotationSelectionMode']='carry_forward_last'
        with self.assertRaises(SAFE.DailyCandidateBlocked):invoke(now,l,h,sel,html)

    def test_duplicate_product_blocked(self):
        now,l,h,sel,html=setup()
        sel['categories'][CATS[0]][1]['itemId']=sel['categories'][CATS[0]][0]['itemId']
        with self.assertRaises(Exception):invoke(now,l,h,sel,html)

    def test_image_missing_blocked(self):
        now,l,h,sel,html=setup()
        sel['categories'][CATS[0]][0]['imageUrl']=''
        with self.assertRaises(Exception):invoke(now,l,h,sel,html)

    def test_stale_html_blocked(self):
        now,l,h,sel,html=setup()
        with self.assertRaises(SAFE.DailyCandidateBlocked):invoke(now,l,h,sel,html+b' ')

    def test_pending_previous_operation_blocked(self):
        now,l,h,sel,html=setup()
        l['operations'][-1]['status']='PLAN'
        with self.assertRaises(Exception):invoke(now,l,h,sel,html)

    def test_cross_blog_blocked(self):
        now,l,h,sel,html=setup()
        bad=dict(PROFILE,page_id='999')
        with self.assertRaises(Exception):invoke(now,l,h,sel,html,profile=bad)

    def test_stale_shopee_selection_blocked(self):
        now,l,h,sel,html=setup()
        sel['timestamp']=(now-timedelta(days=3)).isoformat()
        with self.assertRaises(Exception):invoke(now,l,h,sel,html)

    def test_policy_guard_rejection_blocks(self):
        now,l,h,sel,html=setup()
        def reject(_): raise ValueError('policy rejected')
        with self.assertRaises(ValueError):invoke(now,l,h,sel,html,policy=reject)

    def test_same_day_blocked(self):
        now,l,h,sel,html=setup()
        h['runs'][-1]['timestamp']=now.isoformat()
        l['operations'][-1]['pageUpdatedAt']=now.isoformat()
        with self.assertRaises(SAFE.DailyCandidateBlocked):invoke(now,l,h,sel,html)


if __name__=='__main__':unittest.main()
