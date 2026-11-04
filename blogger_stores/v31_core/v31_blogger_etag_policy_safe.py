"""Blogger v3 update If-Match proof-policy gate (no HTTP, no PUT).

Generic Google API docs describe If-Match but do not certify that Blogger's
Pages.update rejects a stale ETag. Only a separately authorized observed 412
and unchanged readback can satisfy the *technical* part of this contract.
Such an observation does not itself grant permission for a production PUT.
"""
from __future__ import annotations
import re

class EtagProofBlocked(ValueError): pass

def require(ok, msg):
    if not ok: raise EtagProofBlocked(msg)

def strong_etag(etag):
    return isinstance(etag,str) and re.fullmatch(r'"[\x21\x23-\x7e]+"',etag) is not None

def assess_if_match_proof(proof: dict | None) -> dict:
    require(isinstance(proof,dict),'LIVE Blogger stale-ETag proof absent')
    require(proof.get('blogId')=='4739187376492839837'
            and proof.get('pageId')=='2446067640331732447', 'Proof target mismatch')
    require(proof.get('apiMethod')=='blogger.pages.update' and proof.get('httpMethod')=='PUT',
            'Proof must test actual Pages.update PUT')
    require(strong_etag(proof.get('originalEtag')),'Strong original ETag required')
    require(strong_etag(proof.get('staleEtag')) and proof['staleEtag']!=proof['originalEtag'],
            'Distinct stale strong ETag required')
    require(proof.get('sentIfMatch')==proof['staleEtag'], 'Actual If-Match header not proven')
    require(proof.get('responseStatus')==412,'Blogger Pages.update 412 must be observed')
    require(proof.get('readbackNoMutation') is True and proof.get('authenticatedGet') is True,
            'Authenticated post-attempt GET must prove unchanged page')
    require(proof.get('independentEvidenceRef') and proof.get('authorizedTest') is True,
            'No auditable separately authorized test evidence')
    return {'status':'IF_MATCH_TECHNICAL_EVIDENCE_PRESENT',
            'evidence_ref':proof['independentEvidenceRef'],
            'publication_authorized':False,'blogger_put_allowed':False}
