"""V31 LAB: review schema for independent Blogger Pages.update If-Match evidence.

PURE/READ-ONLY. Validating a supplied report cannot authenticate its origin,
prove server behavior, or grant Blogger PUT permission. The live probe must use
an explicitly authorized sacrificial page, NEVER the LOJA or an institutional
page. No API requests, credentials or writes are implemented here.
"""
from __future__ import annotations
import re
from urllib.parse import urlsplit

LAB_BLOG = '4739187376492839837'
LOJA_PAGE = '2446067640331732447'
PROTECTED_PAGES = frozenset({
    LOJA_PAGE, '2986843712929543286', '6280557664516445465',
    '5303118031131491498', '7850045876114690994', '1601621877328706822',
})
TITLE = 'V31-IF-MATCH-TEST-SACRIFICIAL'
HOST = 'blog-teste-tema-worpress.blogspot.com'
RUN_PREFIX = 'https://github.com/adelrib27/blogger-automation1/actions/runs/'

class InvalidEvidence(ValueError):
    pass


def need(value: bool, reason: str):
    if not value:
        raise InvalidEvidence(reason)


def strong_etag(value):
    return isinstance(value, str) and re.fullmatch(r'"[\x21\x23-\x7e]+"', value) is not None


def sha(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def review_proof_shape(evidence: dict | None) -> dict:
    """Validate evidence *shape*, NOT trust; never authorize Blogger PUT."""
    need(type(evidence) is dict, 'Independent observed live evidence missing')
    need(evidence.get('blogId') == LAB_BLOG, 'Must be same LAB blog')
    page_id = evidence.get('pageId')
    need(isinstance(page_id, str) and re.fullmatch('[0-9]{10,24}', page_id) is not None,
         'Sacrificial page ID required')
    need(page_id not in PROTECTED_PAGES, 'Never test on LOJA or institutional pages')
    need(evidence.get('pageTitle') == TITLE, 'Only a distinctly labelled sacrificial page')
    page_url = evidence.get('pageUrl', '')
    u = urlsplit(page_url)
    need(u.scheme == 'https' and u.hostname == HOST and u.path.startswith('/p/')
         and not u.query and not u.fragment, 'Sacrificial page URL mismatch')
    need(evidence.get('apiMethod') == 'blogger.pages.update'
         and evidence.get('httpMethod') == 'PUT', 'Must probe actual Blogger Pages.update')
    need(evidence.get('authorizedTest') is True, 'Test authorization required')
    before = evidence.get('before')
    after = evidence.get('after')
    need(type(before) is dict and type(after) is dict, 'Authenticated GET snapshots required')
    for label, value in (('before', before), ('after', after)):
        need(value.get('blogId') == LAB_BLOG and value.get('pageId') == page_id,
             label+' snapshot identity mismatch')
        need(value.get('authenticatedGet') is True, label+' authenticated GET not proven')
        need(sha(value.get('htmlSha256')), label+' HTML hash missing')
        need(strong_etag(value.get('etag')), label+' strong ETag missing')
        need(isinstance(value.get('updatedAt'), str) and len(value['updatedAt']) >= 19,
             label+' update timestamp missing')
    need(before['htmlSha256'] == after['htmlSha256']
         and before['etag'] == after['etag']
         and before['updatedAt'] == after['updatedAt'],
         'Rejected stale PUT must leave page completely unchanged')
    stale = evidence.get('staleIfMatch')
    need(strong_etag(stale) and stale != before['etag'], 'Distinct stale strong ETag required')
    need(evidence.get('sentIfMatch') == stale, 'Actual request If-Match mismatch')
    need(evidence.get('responseStatus') == 412, 'Must observe HTTP 412 from Blogger')
    run = evidence.get('independentGitHubRun')
    need(isinstance(run, str) and run.startswith(RUN_PREFIX)
         and re.fullmatch('[0-9]+', run[len(RUN_PREFIX):]) is not None,
         'Auditable external workflow evidence missing')
    need(evidence.get('synthetic') is False, 'Synthetic evidence never establishes server semantics')
    return {
        'status': 'EVIDENCE_SHAPE_ACCEPTED_PENDING_INDEPENDENT_VERIFICATION',
        'sacrificial_page_id': page_id,
        'independent_github_run': run,
        'real_server_behavior_verified': False,
        'publication_authorized': False,
        'blogger_put_allowed': False,
    }
