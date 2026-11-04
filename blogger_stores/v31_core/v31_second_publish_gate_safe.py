"""V31 R1: fail-closed pre-PUT READ-ONLY gate for the reserved second rotation.

This module performs NO network, file, Git, Blogger or Cloudflare IO.
It does not authorize Blogger PUT, Git writes, scheduled updates or production.
The caller supplies independently authenticated Blogger readback bytes and Git
blobs plus the immutable Shopee selection and HTMLs. The CI contract uses
archived originals only; live Blogger must be verified separately.
"""
from __future__ import annotations

from hashlib import sha1, sha256
from html.parser import HTMLParser
import json
import re
from urllib.parse import urlsplit

REPOSITORY = 'adelrib27/blogger-automation1'
BRANCH = 'lab/v31r1-shopee-safe-20261103'
RESERVATION_COMMIT = '801381b4e0d2d23fa60f478da67b6dca6ec3df32'
BLOG_ID = '4739187376492839837'
PAGE_ID = '2446067640331732447'
PAGE_URL = 'https://blog-teste-tema-worpress.blogspot.com/p/loja.html'
CATEGORIES = ('Decoração', 'Organização', 'Cozinha', 'Quarto')
START = '<!-- UNIVERSAL_V31_STORE_AUTO_START -->'
END = '<!-- UNIVERSAL_V31_STORE_AUTO_END -->'

# Immutable pins validated in GitHub Actions during second selection/preflight
SELECTION_SHA = 'aea7191e1e4ea77581b33591e0e940f6bd582114c90ea2e457a7173faf3664b7'
ORIGINAL_SHA = '6f3810a364fe2114865b96fa5f118c10495bfe39943406624710ac9aaf25f450'
CANDIDATE_SHA = 'd33070c001281ed795489a032a504accfcab2b593010c1a9e8cf5bb86b8109b8'
LEDGER_BLOB = '8331d025d77fc752230eec71f6c7d8ba86ece5a5'
HISTORY_BLOB = 'de0f022994ca47f0b8316169815afe25722fdfff'
OPERATION_ID = '2ab915f6079855824374fd9577411783bf6d8e5c2bca7eb36a4aa8e1d08d5a93'

PINS = dict(selection=SELECTION_SHA, original=ORIGINAL_SHA, candidate=CANDIDATE_SHA,
            ledger_blob=LEDGER_BLOB, history_blob=HISTORY_BLOB, operation=OPERATION_ID)


class GateBlocked(ValueError):
    """Fail closed without publishing or modifying state."""


def must(condition: bool, reason: str):
    if not condition:
        raise GateBlocked(reason)


def sha256hex(value: bytes) -> str:
    must(type(value) is bytes, 'Input must be bytes')
    return sha256(value).hexdigest()


def gitblob(value: bytes) -> str:
    must(type(value) is bytes, 'Git blob must be bytes')
    return sha1(b'blob ' + str(len(value)).encode('ascii') + b'\0' + value).hexdigest()


def jsondoc(data: bytes, label: str) -> dict:
    must(type(data) is bytes and 0 < len(data) < 1024*1024, label + ' absent/oversize')
    try:
        obj = json.loads(data.decode('utf-8'))
    except (UnicodeError, ValueError) as exc:
        raise GateBlocked(label + ' invalid UTF8/JSON') from exc
    must(type(obj) is dict, label + ' JSON root must be object')
    return obj


class StoreParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.images = [], [], []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'article' and 'ub-product-card' in (a.get('class') or '').split():
            self.ids.append(a.get('data-item-id'))
        if tag == 'a' and 'ub-product-action' in (a.get('class') or '').split():
            self.links.append(a.get('href'))
        if tag == 'img':
            self.images.append(a.get('src'))


def html_catalog(raw: bytes) -> tuple[str, StoreParser]:
    must(type(raw) is bytes and 5000 < len(raw) < 180000, 'Page HTML absent/size invalid')
    try:
        page = raw.decode('utf-8')
    except UnicodeError as exc:
        raise GateBlocked('HTML not UTF8') from exc
    must(page.startswith('<div id="cp-loja">') and page.endswith('</div>'),
         'Store root changed')
    must(page.count(START) == page.count(END) == 1 and page.index(START) < page.index(END),
         'V31 markers missing/duplicated/misordered')
    must('<script' not in page.lower(), 'HTML inserted a script')
    inner = page.split(START, 1)[1].split(END, 1)[0]
    parser = StoreParser()
    parser.feed(inner)
    must(len(parser.ids) == len(parser.links) == len(parser.images) == 16,
         'Store must contain exactly 16 cards, links, images')
    must(len(set(parser.ids)) == 16 and all(re.fullmatch('[0-9]{4,25}', x or '') for x in parser.ids),
         'Invalid/repeated product IDs')
    must(all(urlsplit(u or '').scheme == 'https' and urlsplit(u).hostname == 's.shopee.com.br' for u in parser.links),
         'Invalid affiliate destination')
    must(all(urlsplit(u or '').scheme == 'https' and bool(urlsplit(u).hostname) for u in parser.images),
         'Invalid image URL')
    return page, parser


def checked_selection(raw: bytes, profile: dict) -> list[dict]:
    selection = jsondoc(raw, 'Shopee selection')
    must(selection.get('schemaVersion') == 1 and selection.get('blogId') == BLOG_ID
         and selection.get('status') == 'SAFE_READY' and selection.get('dryRun') is True
         and selection.get('publishReady') is True and selection.get('totalItems') == 16
         and selection.get('uniqueItemIds') == 16, 'Shopee SAFE identity/status invalid')
    gates = selection.get('gates')
    must(type(gates) is dict and all(gates.get(k) is True for k in (
         'allLinksResolved', 'semanticRulesApplied', 'finalProductGate', 'failClosed',
         'allPhotosPresent', 'expectedCategories', 'expectedItems')), 'Shopee gates incomplete')
    cats = selection.get('categories')
    must(type(cats) is dict and tuple(cats.keys()) == CATEGORIES, 'Shopee categories changed')
    products = []
    for cat in CATEGORIES:
        group = cats[cat]
        must(type(group) is list and len(group) == 4, 'Expected 4 products per category')
        for row in group:
            must(type(row) is dict and row.get('category') == cat, 'Shopee category changed')
            ident = str(row.get('itemId', ''))
            must(re.fullmatch('[0-9]{4,25}', ident) is not None, 'Shopee item ID invalid')
            must(type(row.get('affiliateUrl')) is str and urlsplit(row['affiliateUrl']).scheme == 'https'
                 and urlsplit(row['affiliateUrl']).hostname == 's.shopee.com.br', 'Shopee link changed')
            must(type(row.get('imageUrl')) is str and urlsplit(row['imageUrl']).scheme == 'https'
                 and bool(urlsplit(row['imageUrl']).hostname), 'Shopee image invalid')
            products.append(row)
    must(len(products) == len({str(x['itemId']) for x in products}) == 16,
         'Selection contains duplicate products')
    return products


def gate_second_publish_safe(*, repository: str, branch: str,
                             branch_head: str, reservation_is_ancestor: bool,
                             profile_bytes: bytes, ledger_bytes: bytes,
                             history_bytes: bytes, selection_bytes: bytes,
                             original_html_bytes: bytes, candidate_html_bytes: bytes,
                             observed_blogger_html_bytes: bytes,
                             observed_blogger_is_authenticated_live: bool = False,
                             pins: dict | None = None) -> dict:
    """Classify planned second publication; NEVER approve PUT or Git writes.

    ``pins`` is injectable only to unit-test synthetic contracts. Production
    preflight must use module PINS; external authority verifies branch and blobs.
    """
    pin = PINS if pins is None else pins
    must(repository == REPOSITORY and branch == BRANCH, 'Wrong repo/branch')
    must(type(branch_head) is str and re.fullmatch('[0-9a-f]{40}', branch_head) is not None,
         'Invalid branch head')
    must(reservation_is_ancestor is True, 'Reservation commit not in checked branch ancestry')
    must(observed_blogger_is_authenticated_live in (True, False) and
         type(observed_blogger_is_authenticated_live) is bool, 'Blogger source is ambiguous')
    must(gitblob(ledger_bytes) == pin['ledger_blob'] and gitblob(history_bytes) == pin['history_blob'],
         'Canonical Git state blobs differ')
    must(sha256hex(selection_bytes) == pin['selection']
         and sha256hex(original_html_bytes) == pin['original']
         and sha256hex(candidate_html_bytes) == pin['candidate'],
         'Approved artifact hashes differ')
    profile = jsondoc(profile_bytes, 'LAB profile')
    must(profile.get('mode') == 'SAFE' and profile.get('blog_id') == BLOG_ID
         and profile.get('page_id') == PAGE_ID and profile.get('page_url') == PAGE_URL
         and tuple(profile.get('categories', [])) == CATEGORIES
         and profile.get('expected_products') == 16
         and profile.get('per_category') == {cat: 4 for cat in CATEGORIES},
         'LAB profile mismatch')
    ledger, history = jsondoc(ledger_bytes, 'Ledger'), jsondoc(history_bytes, 'History')
    must(ledger.get('schema') == 1 and ledger.get('blogId') == BLOG_ID
         and ledger.get('pageId') == PAGE_ID and history.get('version') == 1
         and history.get('blogId') == BLOG_ID, 'Canonical target invalid')
    ops, runs = ledger.get('operations'), history.get('runs')
    must(type(ops) is list and len(ops) == 2 and
         [x.get('status') for x in ops] == ['PERSISTED', 'PLAN'],
         'Exactly one previous PERSISTED and one active PLAN required')
    must(type(runs) is list and len(runs) == 2 and
         runs[0].get('source') == 'seed_from_current_blogger_store' and
         runs[1].get('source') == 'blogger_published', 'Historical runs do not match first cycle')
    first, second = ops
    must(first.get('candidateSha') == pin['original'] and
         first.get('operationId') == runs[1].get('operationId') and
         first.get('selectionSha') == runs[1].get('selectionSha') and
         second.get('status') == 'PLAN' and second.get('operationId') == pin['operation']
         and second.get('originalSha') == pin['original']
         and second.get('candidateSha') == pin['candidate']
         and second.get('selectionSha') == pin['selection'], 'Existing PLAN differs from approved cycle')
    expected_op = sha256((BLOG_ID + '|' + PAGE_ID + '|' + pin['selection']).encode()).hexdigest()
    must(second['operationId'] == expected_op and first['operationId'] != second['operationId'],
         'PLAN operation identity invalid/reused')
    products = checked_selection(selection_bytes, profile)
    new_ids = [str(x['itemId']) for x in products]
    all_old_ids = []
    for i, run in enumerate(runs):
        must(run.get('pageId') == PAGE_ID and type(run.get('items')) is list
             and len(run['items']) == 16, 'Historical page/items invalid at run '+str(i))
        old_ids = [str(row.get('itemId')) for row in run['items']]
        must(len(set(old_ids)) == 16 and all(re.fullmatch('[0-9]{4,25}', x) for x in old_ids),
             'History product IDs corrupted')
        all_old_ids.extend(old_ids)
    must(len(set(all_old_ids)) == len(all_old_ids)
         and set(new_ids).isdisjoint(all_old_ids), 'Selection overlaps already-used history IDs')
    before, oldpage = html_catalog(original_html_bytes)
    after, newpage = html_catalog(candidate_html_bytes)
    must((before.split(START, 1)[0], before.split(END, 1)[1]) ==
         (after.split(START, 1)[0], after.split(END, 1)[1]),
         'Outside marked region changed')
    must(oldpage.ids == [str(x['itemId']) for x in runs[-1]['items']],
         'Original HTML no longer matches last published history')
    must(newpage.ids == new_ids
         and newpage.links == [x['affiliateUrl'] for x in products]
         and newpage.images == [x['imageUrl'] for x in products],
         'Candidate IDs/links/images differ from exact authorized selection')
    must(type(observed_blogger_html_bytes) is bytes, 'Blogger readback not bytes')
    current_sha = sha256hex(observed_blogger_html_bytes)
    if current_sha == pin['original']:
        decision = 'EXISTING_PLAN_READBACK_ORIGINAL_SEPARATE_APPROVAL_REQUIRED'
    elif current_sha == pin['candidate']:
        decision = 'CANDIDATE_ALREADY_IN_BLOGGER_SKIP_PUT_VERIFY_PUBLIC_ONLY'
    else:
        raise GateBlocked('Blogger HTML changed outside permitted original/candidate hashes')
    return {
       'status': 'V31_SECOND_PUBLISH_PREFLIGHT_SAFE_PASS',
       'decision': decision, 'repository': REPOSITORY, 'branch': BRANCH,
       'checked_branch_head': branch_head,
       'reservation_commit': RESERVATION_COMMIT,
       'operation_id': second['operationId'],
       'ledger_statuses': ['PERSISTED', 'PLAN'], 'history_entries': len(runs),
       'selected_products': len(products), 'old_product_ids_disjoint': True,
       'original_html_sha256': pin['original'],
       'candidate_html_sha256': pin['candidate'],
       'selection_sha256': pin['selection'],
       'observed_html_sha256': current_sha,
       'observed_blogger_live_authenticated': observed_blogger_is_authenticated_live,
       'blogger_put_allowed': False, 'git_write_allowed': False,
       'cron_allowed': False, 'production_allowed': False,
       'note': 'Classification only: explicit separate user approval and live Blogger CAS prewrite gate required before any PUT.',
    }
