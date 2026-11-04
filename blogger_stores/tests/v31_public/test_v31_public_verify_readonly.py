from pathlib import Path
import json
import sys
import unittest
from urllib.error import HTTPError, URLError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from v31_public_verify_readonly import (reference, verify_html, fetch_public, run,
    VerificationError, PublicThrottled, START, END, LAB_URL)

ROOT=Path(__file__).resolve().parents[2]/'V31_PRIMEIRA_SELECAO_REAL_SAFE_V1'
# The tests never access network; use an explicitly supplied fixture copied from V23 artifact.
class Response:
    status=200
    def __init__(self, html):self.html=html
    def geturl(self):return LAB_URL
    def read(self,n):return self.html.encode()
    def __enter__(self):return self
    def __exit__(self,*args):return False
class TestReadOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import hashlib
        cls.profile={
            'blog_id':'4739187376492839837', 'page_id':'2446067640331732447',
            'page_url':LAB_URL, 'mode':'SAFE',
            'categories':['Decoração','Organização','Cozinha','Quarto'],
            'expected_products':16,
            'per_category':{c:4 for c in ['Decoração','Organização','Cozinha','Quarto']},
        }
        products={}
        for ci,category in enumerate(cls.profile['categories']):
            products[category]=[
                {'itemId':str(20042293295 + ci*4 + j),
                 'category':category,
                 'affiliateUrl':f'https://s.shopee.com.br/fixture-{ci}-{j}',
                 'imageUrl':f'https://cf.shopee.com.br/file/fixture-{ci}-{j}'}
                for j in range(4)
            ]
        cls.selection={
            'schemaVersion':1,'status':'SAFE_READY','publishReady':True,'dryRun':True,
            'blogId':cls.profile['blog_id'],'totalItems':16,'uniqueItemIds':16,
            'affiliateLinkGeneration':{'allResolvedToShopee':True,'validatedCount':16},
            'gates':{'allLinksResolved':True,'failClosed':True}, 'categories':products,
        }
        cls.sha=hashlib.sha256(json.dumps(cls.selection).encode()).hexdigest()
        cls.ref=reference(cls.profile,cls.selection,cls.sha)
        cats=''.join(f'<article class="ub-product-card" data-item-id="{p["id"]}" data-category="{p["category"]}"><img src="{p["image"]}"><a class="ub-product-action" href="{p["link"]}" rel="nofollow sponsored noopener"></a></article>' for p in cls.ref['products'])
        cls.html='<html><body><!-- theme var userResumed = false; ub-v31-share -->'+START+cats+END+'</body></html>'
        cls.html=cls.html+' '*1100
    def test_valid_exact_html(self):self.assertEqual(verify_html(self.html,self.ref)['status'],'PUBLIC_EXACT_PASS')
    def test_ids_mismatch(self):
        with self.assertRaises(VerificationError):verify_html(self.html.replace('20042293295','12345678900',1),self.ref)
    def test_images_mismatch(self):
        with self.assertRaises(VerificationError):verify_html(self.html.replace(self.ref['products'][0]['image'],'https://cf.shopee.com.br/file/alterado',1),self.ref)
    def test_links_mismatch(self):
        with self.assertRaises(VerificationError):verify_html(self.html.replace(self.ref['products'][0]['link'],'https://s.shopee.com.br/alterado',1),self.ref)
    def test_categories_mismatch(self):
        with self.assertRaises(VerificationError):verify_html(self.html.replace('data-category="Decoração"','data-category="Quarto"',1),self.ref)
    def test_theme_mismatch(self):
        with self.assertRaises(VerificationError):verify_html(self.html.replace('ub-v31-share','absent'),self.ref)
    def test_markers_duplicated(self):
        with self.assertRaises(VerificationError):verify_html(self.html.replace(END,END+END),self.ref)
    def test_429_is_pending(self):
        with self.assertRaises(PublicThrottled):fetch_public(opener=lambda *a,**k: (_ for _ in ()).throw(HTTPError(LAB_URL,429,'Too Many Requests',{},None)))
    def test_unavailable_is_pending(self):
        with self.assertRaises(PublicThrottled):fetch_public(opener=lambda *a,**k: (_ for _ in ()).throw(URLError('temporary')))
    def test_redirect_rejected(self):
        class Other(Response):
            def geturl(self):return 'https://example.com/p/loja.html'
        with self.assertRaises(VerificationError):fetch_public(opener=lambda *a,**k: Other(self.html))
    def test_successful_http_fixture(self):self.assertEqual(fetch_public(opener=lambda *a,**k:Response(self.html)),self.html)
    def test_foreign_blog_blocked(self):
        p=dict(self.profile,blog_id='999')
        with self.assertRaises(VerificationError):reference(p,self.selection,self.sha)
    def test_fake_selection_blocked(self):
        s=dict(self.selection,status='PUBLISHED')
        with self.assertRaises(VerificationError):reference(self.profile,s,self.sha)
    def test_duplicate_product_blocked(self):
        s=json.loads(json.dumps(self.selection))
        s['categories']['Decoração'][1]['itemId']=s['categories']['Decoração'][0]['itemId']
        with self.assertRaises(VerificationError):reference(self.profile,s,self.sha)
if __name__=='__main__':unittest.main()