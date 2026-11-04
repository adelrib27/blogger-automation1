"""SAFE-only Git CAS/recovery tests, no external IO, synthetic data."""
import copy
import json
import sys
import unittest
from hashlib import sha256
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'v31_core'))
from v31_rotation_ledger import operation_id, mark_readback, mark_public_verified, history_commit
from v31_multicycle_cas_contract import (
    BRANCH, REPO, BLOG_ID, PAGE_ID, START, END,
    ReservationBlocked, git_blob_sha, require_cas, prepare_reservation,
    inspect_committed_reservation, selection_ids)

CAT = ['Decoração', 'Organização', 'Cozinha', 'Quarto']
FIRST_SELECTION = 'a' * 64
FIRST_CANDIDATE = 'b' * 64
HEAD = 'c' * 40
RESERVED_HEAD = 'd' * 40

def encoded(obj):
    return (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode('utf-8')

def objects():
    original = {'schema': 1, 'blogId': BLOG_ID, 'pageId': PAGE_ID,
        'operations': [{'status': 'PERSISTED', 'operationId': operation_id(FIRST_SELECTION, BLOG_ID, PAGE_ID),
                        'selectionSha': FIRST_SELECTION, 'originalSha': '3'*64,
                        'candidateSha': FIRST_CANDIDATE}]}
    history = {'version': 1, 'blogId': BLOG_ID, 'runs': [
        {'source': 'seed_from_current_blogger_store', 'pageId': PAGE_ID,
         'items': [{'itemId': str(50000+i), 'category': CAT[i//4]} for i in range(16)]},
        {'source': 'blogger_published', 'pageId': PAGE_ID,
         'operationId': operation_id(FIRST_SELECTION, BLOG_ID, PAGE_ID),
         'selectionSha': FIRST_SELECTION,
         'items': [{'itemId': str(60000+i), 'category': CAT[i//4]} for i in range(16)]}]}
    profile = {'mode': 'SAFE', 'blog_id': BLOG_ID, 'page_id': PAGE_ID,
        'page_url': 'https://blog-teste-tema-worpress.blogspot.com/p/loja.html',
        'categories': CAT, 'expected_products': 16,
        'per_category': {c: 4 for c in CAT}}
    return original, history, profile

def selection(base=70000):
    products = {cat: [{'itemId': str(base+i), 'category': cat,
                      'imageUrl': 'https://img.example.test/image.jpg',
                      'affiliateUrl': 'https://s.shopee.com.br/foobar'}
                      for i in range(n*4, n*4+4)] for n,cat in enumerate(CAT)}
    return {'schemaVersion': 1, 'status': 'SAFE_READY', 'publishReady': True,
        'dryRun': True, 'blogId': BLOG_ID, 'totalItems': 16,
        'uniqueItemIds': 16, 'categories': products,
        'gates': {k: True for k in ('allLinksResolved','semanticRulesApplied',
             'finalProductGate','failClosed','allPhotosPresent',
             'expectedCategories','expectedItems')}}

def html(items):
    return ('<div id="cp-loja">\n'+START+'\n<div class="ub-store-grid">'+
            ''.join(f'<article class="ub-product-card" data-item-id="{i}">'
                    '<img class="ub-product-image" src="https://img.example.test/foto.jpg" />'
                    '<a class="ub-product-action" href="https://s.shopee.com.br/xyz">Ver oferta</a>'
                    '</article>' for i in items)+
            '</div>\n'+END+'\n</div>').encode('utf-8')

class TestReservationCAS(unittest.TestCase):
    def setUp(self):
        self.ledger, self.history, self.profile = objects()
        self.selection = selection()
        self.oldhtml = html([str(60000+i) for i in range(16)])
        self.newhtml = html([str(70000+i) for i in range(16)])
        self.args = dict(repository=REPO, branch=BRANCH, profile=self.profile,
            ledger_bytes=encoded(self.ledger), history_bytes=encoded(self.history),
            selection_bytes=encoded(self.selection), blogger_html_bytes=self.oldhtml,
            candidate_html_bytes=self.newhtml, expected_head=HEAD,
            observed_head=HEAD, expected_ledger_blob=git_blob_sha(encoded(self.ledger)),
            expected_history_blob=git_blob_sha(encoded(self.history)))
    def call(self, **kwargs):
        args = dict(self.args); args.update(kwargs)
        return prepare_reservation(**args)
    def blocked(self, **kwargs):
        with self.assertRaises(ValueError): self.call(**kwargs)
    def test_realistic_second_reservation_proposed_only(self):
        p = self.call()
        self.assertEqual(p['status'], 'V31_LAB_PROPOSED_GIT_RESERVATION_OFFLINE')
        self.assertEqual(p['items'], 16)
        self.assertFalse(p['git_write_allowed'])
        self.assertFalse(p['blogger_put_allowed'])
        self.assertFalse(p['cron_allowed'])
        state = json.loads(p['proposed_ledger_bytes'])
        self.assertEqual([o['status'] for o in state['operations']], ['PERSISTED','PLAN'])
        self.assertEqual(p['expected_history_blob'], p['unchanged_history_blob'])
        self.assertEqual(p['proposed_ledger_blob'], git_blob_sha(p['proposed_ledger_bytes']))
    def test_inputs_unchanged(self):
        before=copy.deepcopy(self.args)
        self.call()
        self.assertEqual(self.args, before)
    def test_branch_conflict_blocks(self): self.blocked(observed_head='e'*40)
    def test_ledger_blob_changed_blocks(self): self.blocked(expected_ledger_blob='e'*40)
    def test_history_blob_changed_blocks(self): self.blocked(expected_history_blob='e'*40)
    def test_wrong_git_head_shape_blocks(self): self.blocked(expected_head='bad', observed_head='bad')
    def test_wrong_repo_blocks(self): self.blocked(repository='other/repository')
    def test_wrong_branch_blocks(self): self.blocked(branch='main')
    def test_wrong_blog_blocks(self):
        p=dict(self.profile,blog_id='555');self.blocked(profile=p)
    def test_wrong_page_blocks(self):
        p=dict(self.profile,page_id='555');self.blocked(profile=p)
    def test_non_safe_mode_blocks(self):
        p=dict(self.profile,mode='LIVE');self.blocked(profile=p)
    def test_bad_selection_status_blocks(self):
        x=selection();x['status']='DRAFT';self.blocked(selection_bytes=encoded(x))
    def test_incomplete_commercial_gate_blocks(self):
        x=selection();x['gates']['allPhotosPresent']=False;self.blocked(selection_bytes=encoded(x))
    def test_missing_affiliate_link_blocks(self):
        x=selection();x['categories'][CAT[0]][0]['affiliateUrl']='http://bad';self.blocked(selection_bytes=encoded(x))
    def test_duplicate_selected_item_blocks(self):
        x=selection();x['categories'][CAT[0]][1]['itemId']=x['categories'][CAT[0]][0]['itemId'];self.blocked(selection_bytes=encoded(x))
    def test_selection_overlap_last_history_blocks(self):
        x=selection(60000)
        self.blocked(selection_bytes=encoded(x),candidate_html_bytes=html([str(60000+i) for i in range(16)]))
    def test_selection_overlap_seed_history_blocks(self):
        x=selection(50000)
        self.blocked(selection_bytes=encoded(x),candidate_html_bytes=html([str(50000+i) for i in range(16)]))
    def test_candidate_html_mismatch_blocks(self):
        self.blocked(candidate_html_bytes=html([str(90000+i) for i in range(16)]))
    def test_original_html_changed_blocks(self): self.blocked(blogger_html_bytes=b'not the current HTML')
    def test_unknown_original_items_overlap_blocks(self):
        self.blocked(blogger_html_bytes=html([str(70000+i) for i in range(16)]))
    def test_missing_product_image_blocks(self):
        self.blocked(candidate_html_bytes=self.newhtml.replace(b'class="ub-product-image"',b'class="bad-image"',1))
    def test_missing_affiliate_action_blocks(self):
        self.blocked(candidate_html_bytes=self.newhtml.replace(b'class="ub-product-action"',b'class="bad-action"',1))
    def test_unexpected_script_blocks(self):
        self.blocked(candidate_html_bytes=self.newhtml.replace(END.encode(),b'<script>bad</script>'+END.encode()))
    def test_markers_must_exist(self):
        self.blocked(candidate_html_bytes=self.newhtml.replace(START.encode(),b''))
    def test_outside_marker_change_blocks(self):
        self.blocked(candidate_html_bytes=self.newhtml.replace(b'<div id="cp-loja">',b'<div id="other">'))
    def test_existing_pending_second_blocks_new_selection(self):
        p=self.call();self.ledger=json.loads(p['proposed_ledger_bytes'])
        self.blocked(ledger_bytes=encoded(self.ledger), expected_ledger_blob=git_blob_sha(encoded(self.ledger)))
    def test_history_tamper_blocks(self):
        h=copy.deepcopy(self.history);h['runs'][1]['selectionSha']='f'*64
        self.blocked(history_bytes=encoded(h),expected_history_blob=git_blob_sha(encoded(h)))
    def test_reservation_readback_before_put_does_not_authorize_put(self):
        p=self.call()
        r=inspect_committed_reservation(reservation=p,
            committed_ledger_bytes=p['proposed_ledger_bytes'],
            committed_history_bytes=encoded(self.history),
            parent_head=HEAD,reservation_commit_head=RESERVED_HEAD,
            observed_remote_head=RESERVED_HEAD,observed_blogger_html_bytes=self.oldhtml)
        self.assertEqual(r['decision'],'PLAN_ONLY_REQUIRES_EXPLICIT_WRITE_GATE')
        self.assertFalse(r['blogger_put_allowed'])
    def test_crash_after_put_skips_republish(self):
        p=self.call()
        r=inspect_committed_reservation(reservation=p,
            committed_ledger_bytes=p['proposed_ledger_bytes'],
            committed_history_bytes=encoded(self.history),
            parent_head=HEAD,reservation_commit_head=RESERVED_HEAD,
            observed_remote_head=RESERVED_HEAD,observed_blogger_html_bytes=self.newhtml)
        self.assertEqual(r['decision'],'PUT_MAY_HAVE_SUCCEEDED_SKIP_RETRY')
        self.assertFalse(r['blogger_put_allowed'])
    def test_reservation_parent_mismatch_blocks(self):
        p=self.call()
        with self.assertRaises(ReservationBlocked):
            inspect_committed_reservation(reservation=p,
                committed_ledger_bytes=p['proposed_ledger_bytes'],
                committed_history_bytes=encoded(self.history),parent_head='e'*40,
                reservation_commit_head=RESERVED_HEAD,observed_remote_head=RESERVED_HEAD,
                observed_blogger_html_bytes=self.oldhtml)
    def test_reservation_commit_lost_race_blocks(self):
        p=self.call()
        with self.assertRaises(ReservationBlocked):
            inspect_committed_reservation(reservation=p,
                committed_ledger_bytes=p['proposed_ledger_bytes'],
                committed_history_bytes=encoded(self.history),parent_head=HEAD,
                reservation_commit_head=RESERVED_HEAD,observed_remote_head='e'*40,
                observed_blogger_html_bytes=self.oldhtml)
    def test_reservation_history_was_changed_blocks(self):
        p=self.call();history=encoded({'version':1,'blogId':BLOG_ID,'runs':[]})
        with self.assertRaises(ReservationBlocked):
            inspect_committed_reservation(reservation=p,
                committed_ledger_bytes=p['proposed_ledger_bytes'],
                committed_history_bytes=history,parent_head=HEAD,
                reservation_commit_head=RESERVED_HEAD,observed_remote_head=RESERVED_HEAD,
                observed_blogger_html_bytes=self.oldhtml)
    def test_readback_unrecognised_html_blocks(self):
        p=self.call()
        with self.assertRaises(ValueError):
            inspect_committed_reservation(reservation=p,
                committed_ledger_bytes=p['proposed_ledger_bytes'],
                committed_history_bytes=encoded(self.history),parent_head=HEAD,
                reservation_commit_head=RESERVED_HEAD,observed_remote_head=RESERVED_HEAD,
                observed_blogger_html_bytes=b'tampered')
    def test_concurrent_reservations_reject_stale_head(self):
        _=self.call() # Both contenders observe identical old head
        self.blocked(observed_head=RESERVED_HEAD) # Loser sees winner's head
    def test_git_blob_calculation_is_git_hash_object_compatible(self):
        self.assertEqual(git_blob_sha(b''),'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')
    def test_second_and_third_cycle_pure_state(self):
        p=self.call()
        state=json.loads(p['proposed_ledger_bytes'])
        selhash=sha256(encoded(self.selection)).hexdigest()
        state=mark_readback(state, selhash, observed_candidate_sha=sha256(self.newhtml).hexdigest())
        proof={'status':'PUBLIC_EXACT_PASS','selection_sha256':selhash,
               'cards':16,'images':16,'links':16,'public_http':200}
        state=mark_public_verified(state,selhash,proof=proof) # mock only, not a real public proof
        items=[{'itemId':str(70000+i),'category':CAT[i//4]} for i in range(16)]
        state,h=history_commit(state,selhash,self.history,published_items=items,published_at='2026-11-04T18:00:00-03:00')
        self.assertEqual(len(h['runs']),3)
        self.assertEqual(len(state['operations']),2)
        self.assertTrue(all(o['status']=='PERSISTED' for o in state['operations']))
        third=selection(80000)
        b=encoded(state); hb=encoded(h)
        result=self.call(ledger_bytes=b,history_bytes=hb,
                         expected_ledger_blob=git_blob_sha(b),expected_history_blob=git_blob_sha(hb),
                         selection_bytes=encoded(third),blogger_html_bytes=self.newhtml,
                         candidate_html_bytes=html([str(80000+i) for i in range(16)]))
        self.assertEqual(len(json.loads(result['proposed_ledger_bytes'])['operations']),3)

if __name__ == '__main__': unittest.main()
