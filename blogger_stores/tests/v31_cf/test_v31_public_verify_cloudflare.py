from pathlib import Path
from urllib.error import HTTPError, URLError
import hashlib
import json
import sys
import tempfile
import unittest

# Works regardless of current working directory (Windows and GitHub Linux).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from v31_public_verify_cloudflare import (fetch_via_browser_rendering, run, main,
    PublicThrottled, VerificationError, LAB_URL)

ACCOUNT = 'a' * 32
TOKEN = 'test-token-only-not-real-12345678'
CATS = ['Decoração', 'Organização', 'Cozinha', 'Quarto']


class FakeResponse:
    status = 200
    def __init__(self, payload): self.payload = payload
    def read(self, limit): return self.payload[:limit]
    def __enter__(self): return self
    def __exit__(self, *args): return False


def make_fixture():
    products = {}
    cards = []
    for i, cat in enumerate(CATS):
        items = []
        for j in range(4):
            pid = str(20000000001 + i*4 + j)
            link = f'https://s.shopee.com.br/test-{i}-{j}'
            img = f'https://cf.shopee.com.br/file/test-{i}-{j}'
            items.append(dict(itemId=pid, category=cat, affiliateUrl=link, imageUrl=img))
            cards.append(f'<article class="ub-product-card" data-item-id="{pid}" data-category="{cat}">'
                         f'<img src="{img}"><a class="ub-product-action" href="{link}" '
                         'rel="nofollow sponsored noopener">Ver</a></article>')
        products[cat] = items
    selection = dict(schemaVersion=1, status='SAFE_READY', publishReady=True, dryRun=True,
                     blogId='4739187376492839837', totalItems=16, uniqueItemIds=16,
                     affiliateLinkGeneration=dict(allResolvedToShopee=True, validatedCount=16),
                     gates=dict(allLinksResolved=True, failClosed=True), categories=products)
    profile = dict(blog_id='4739187376492839837', page_id='2446067640331732447',
                   page_url=LAB_URL, mode='SAFE', expected_products=16,
                   categories=CATS, per_category={x: 4 for x in CATS})
    html = ('<html><body><script>var userResumed = false;</script><div id="ub-v31-share"></div>'
            '<!-- UNIVERSAL_V31_STORE_AUTO_START -->' + ''.join(cards) +
            '<!-- UNIVERSAL_V31_STORE_AUTO_END -->' + ' ' * 1200 + '</body></html>')
    raw = json.dumps(selection, ensure_ascii=False).encode('utf-8')
    return raw, profile, html


class CloudflareTransportTests(unittest.TestCase):
    def test_01_correct_endpoint_payload_no_extra_query(self):
        _, _, html = make_fixture()
        def opener(req, timeout):
            self.assertEqual(req.full_url,
                             'https://api.cloudflare.com/client/v4/accounts/' + ACCOUNT +
                             '/browser-rendering/content?cacheTTL=0')
            body = json.loads(req.data)
            self.assertEqual(body['url'], LAB_URL)
            self.assertNotIn('utm_', req.data.decode())
            self.assertEqual(req.get_method(), 'POST')
            self.assertEqual(timeout, 65)
            return FakeResponse(json.dumps(dict(success=True, result=html)).encode())
        self.assertEqual(fetch_via_browser_rendering(ACCOUNT, TOKEN, opener=opener), html)

    def test_02_bad_account_rejected(self):
        with self.assertRaises(VerificationError): fetch_via_browser_rendering('wrong', TOKEN)

    def test_03_missing_token_rejected(self):
        with self.assertRaises(VerificationError): fetch_via_browser_rendering(ACCOUNT, '')

    def test_04_http_429_pending(self):
        with self.assertRaises(PublicThrottled): fetch_via_browser_rendering(
            ACCOUNT, TOKEN, opener=lambda *a, **k: (_ for _ in ()).throw(HTTPError(LAB_URL, 429, '', {}, None)))

    def test_05_http_503_pending(self):
        with self.assertRaises(PublicThrottled): fetch_via_browser_rendering(
            ACCOUNT, TOKEN, opener=lambda *a, **k: (_ for _ in ()).throw(HTTPError(LAB_URL, 503, '', {}, None)))

    def test_06_http_504_pending(self):
        with self.assertRaises(PublicThrottled): fetch_via_browser_rendering(
            ACCOUNT, TOKEN, opener=lambda *a, **k: (_ for _ in ()).throw(HTTPError(LAB_URL, 504, '', {}, None)))

    def test_07_http_401_not_success(self):
        with self.assertRaises(VerificationError): fetch_via_browser_rendering(
            ACCOUNT, TOKEN, opener=lambda *a, **k: (_ for _ in ()).throw(HTTPError(LAB_URL, 401, '', {}, None)))

    def test_08_network_error_pending(self):
        with self.assertRaises(PublicThrottled): fetch_via_browser_rendering(
            ACCOUNT, TOKEN, opener=lambda *a, **k: (_ for _ in ()).throw(URLError('temporary')))

    def test_09_invalid_json(self):
        with self.assertRaises(VerificationError): fetch_via_browser_rendering(
            ACCOUNT, TOKEN, opener=lambda *a, **k: FakeResponse(b'<html>not-json'))

    def test_10_false_success(self):
        with self.assertRaises(VerificationError): fetch_via_browser_rendering(
            ACCOUNT, TOKEN, opener=lambda *a, **k: FakeResponse(b'{"success":false,"result":"x"}'))

    def test_11_oversized_response(self):
        with self.assertRaises(VerificationError): fetch_via_browser_rendering(
            ACCOUNT, TOKEN, opener=lambda *a, **k: FakeResponse(b' ' * 4_000_001))

    def test_12_missing_html(self):
        with self.assertRaises(VerificationError): fetch_via_browser_rendering(
            ACCOUNT, TOKEN, opener=lambda *a, **k: FakeResponse(b'{"success":true,"result":null}'))

    def full_run(self, edited=None, change_sha=False):
        raw, profile, html = make_fixture()
        if edited: html = edited(html)
        with tempfile.TemporaryDirectory() as tmp:
            s = Path(tmp)/'selection.json'; p = Path(tmp)/'profile.json'
            s.write_bytes(raw); p.write_text(json.dumps(profile, ensure_ascii=False), encoding='utf-8')
            def opener(*a, **kw):
                return FakeResponse(json.dumps(dict(success=True, result=html)).encode())
            return run(s, p, '0'*64 if change_sha else hashlib.sha256(raw).hexdigest(),
                       ACCOUNT, TOKEN, opener=opener)

    def test_13_exact_catalog_pass(self):
        proof = self.full_run()
        self.assertEqual(proof['status'], 'PUBLIC_EXACT_PASS')
        self.assertTrue(proof['public_verified'])
        self.assertFalse(proof['publication_attempted'])
        self.assertEqual(proof['images'], 16)

    def test_14_wrong_id_fails(self):
        with self.assertRaises(VerificationError): self.full_run(lambda x:x.replace('20000000001','29999999999',1))

    def test_15_wrong_image_fails(self):
        with self.assertRaises(VerificationError): self.full_run(lambda x:x.replace('/test-0-0','/other-0-0',1))

    def test_16_wrong_link_fails(self):
        with self.assertRaises(VerificationError): self.full_run(lambda x:x.replace('https://s.shopee.com.br/test-0-0','https://s.shopee.com.br/bad-0-0',1))

    def test_17_wrong_category_fails(self):
        with self.assertRaises(VerificationError): self.full_run(lambda x:x.replace('data-category="Decoração"','data-category="Quarto"',1))

    def test_18_wrong_selection_sha_fails_before_http(self):
        with self.assertRaises(VerificationError): self.full_run(change_sha=True)

    def test_19_missing_theme_fails(self):
        with self.assertRaises(VerificationError): self.full_run(lambda x:x.replace('ub-v31-share','nothing'))

    def test_20_duplicate_marker_fails(self):
        with self.assertRaises(VerificationError): self.full_run(lambda x:x.replace('<!-- UNIVERSAL_V31_STORE_AUTO_END -->','<!-- UNIVERSAL_V31_STORE_AUTO_END --><!-- UNIVERSAL_V31_STORE_AUTO_END -->'))

    def test_21_missing_env_main_fails_closed_and_writes_report(self):
        raw, profile, html = make_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            s, p, dest = Path(tmp)/'selection.json', Path(tmp)/'profile.json', Path(tmp)/'report.json'
            s.write_bytes(raw); p.write_text(json.dumps(profile), encoding='utf-8')
            import unittest.mock as mock
            with mock.patch.dict('os.environ', {'CLOUDFLARE_ACCOUNT_ID':'', 'CLOUDFLARE_BROWSER_TOKEN':''}):
                code=main(['--selection',str(s),'--profile',str(p),'--selection-sha256',hashlib.sha256(raw).hexdigest(),'--report',str(dest)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(dest.read_text())['status'],'PUBLIC_VERIFICATION_FAILED')

if __name__ == '__main__': unittest.main()