"""Targeted contract checks: NO Blogger or GitHub I/O."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'v31_core'))
from v31_sacrificial_if_match_proof_safe import (
    review_proof_shape, InvalidEvidence, LAB_BLOG, LOJA_PAGE, TITLE, HOST,
)

PAGE = '9990008887776665554'

def sample():
    snap = dict(blogId=LAB_BLOG, pageId=PAGE, authenticatedGet=True,
                htmlSha256='a'*64, etag='"current-ETag"', updatedAt='2026-11-04T19:00:00-03:00')
    return dict(blogId=LAB_BLOG, pageId=PAGE, pageTitle=TITLE,
                pageUrl=f'https://{HOST}/p/v31-if-match-test.html',
                apiMethod='blogger.pages.update', httpMethod='PUT',
                authorizedTest=True, before=snap.copy(), after=snap.copy(),
                staleIfMatch='"stale-ETag"', sentIfMatch='"stale-ETag"',
                responseStatus=412,
                independentGitHubRun='https://github.com/adelrib27/blogger-automation1/actions/runs/99999',
                synthetic=False)

class EvidenceShapeSafe(unittest.TestCase):
    def denied(self, mutate):
        p=deepcopy(sample());mutate(p)
        with self.assertRaises(InvalidEvidence): review_proof_shape(p)

    def test_absent_evidence_rejected(self):
        with self.assertRaises(InvalidEvidence): review_proof_shape(None)
    def test_structurally_valid_receipt_is_still_untrusted(self):
        x=review_proof_shape(sample())
        self.assertFalse(x['real_server_behavior_verified'])
        self.assertFalse(x['publication_authorized'])
        self.assertFalse(x['blogger_put_allowed'])
    def test_never_test_loja(self):
        self.denied(lambda p: p.update(pageId=LOJA_PAGE))
    def test_never_test_institutional_page(self):
        self.denied(lambda p: p.update(pageId='2986843712929543286'))
    def test_other_blog_rejected(self):
        self.denied(lambda p: p.update(blogId='9999'))
    def test_unmarked_page_rejected(self):
        self.denied(lambda p: p.update(pageTitle='LOJA'))
    def test_forged_external_host_rejected(self):
        self.denied(lambda p: p.update(pageUrl='https://other.example/p/test.html'))
    def test_not_put_rejected(self):
        self.denied(lambda p: p.update(httpMethod='PATCH'))
    def test_wrong_response_rejected(self):
        self.denied(lambda p: p.update(responseStatus=200))
    def test_weak_etag_rejected(self):
        self.denied(lambda p: p.update(staleIfMatch='W/"stale"', sentIfMatch='W/"stale"'))
    def test_unchanged_page_required(self):
        self.denied(lambda p: p['after'].update(htmlSha256='b'*64))
    def test_original_etag_must_persist(self):
        self.denied(lambda p: p['after'].update(etag='"new-ETag"'))
    def test_wrong_if_match_rejected(self):
        self.denied(lambda p: p.update(sentIfMatch='"not-sent"'))
    def test_synthetic_rejected(self):
        self.denied(lambda p: p.update(synthetic=True))
    def test_approval_required(self):
        self.denied(lambda p: p.update(authorizedTest=False))
    def test_no_independent_run_rejected(self):
        self.denied(lambda p: p.update(independentGitHubRun='OFFLINE_SYNTHETIC_ONLY'))

if __name__ == '__main__':
    unittest.main()
