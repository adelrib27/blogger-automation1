"""Homologação C81: revisão aditiva do DRAFT 321, com dois envelopes imutáveis."""
import hashlib
import html
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from secrets import token_hex

from . import autonomous_review as review
from . import automatic_wordpress_drafts as wp
from .reviewed_draft_delivery import deliver_reviewed_draft
from .reviewed_ready_promotion import _json_sha

SITE = "wordpress_casa_decoracao"
SKU = "shopee:400124163:42079451217"
FP = "9d9a2f19d99aa825d3f741722ad8f0f8a3debf0c9dd5a495a4396077a785a71e"
OLD = "3569eba84b6a3cbef3929572767498f906949ff6d661e24b899f277d5f967f3a"
TENANT = {"site_key": SITE, "campaign": "casaedecoracaowp"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def main(mode):
    route = review.sites()[SITE]
    require(route["publish_enabled"] is False, "draft_route_required")
    policy = json.loads(review.PROFILE.read_text(encoding="utf-8"))[SITE]
    profile = policy["offers"][SKU]
    runner = review.CloudflareD1HTTPRunner.from_environment(allow_mutations=True)
    state = review.UniversalD1ReadyState(runner)
    storage = review._official_storage()
    envelope = review.ImmutablePrivateReadyEnvelope(backend=review.R2PrivateReadyBackend(storage))
    public = os.environ["V31_AUTONOMOUS_RELEASE_PUBLIC_KEY_HEX"]
    original = envelope.load(**TENANT, html_sha256=OLD, release_public_key=public)
    title = original["review"]["article_title"]
    old_html = original["html_content"]
    require(original["review"]["product_key"] == SKU, "old_sku_mismatch")
    related = review.verified_related_post(policy, profile)
    link = '<p>Veja também <a href="' + html.escape(related["url"]) + '">' + html.escape(related["title"]) + '</a>.</p>'
    require(old_html.count("<figure>") == 1 and related["url"] not in old_html, "old_shape")
    corrected = old_html.replace("<figure>", link + "\n<figure>")
    new = sha(corrected)
    job = state.get_job(**TENANT, fingerprint=FP)
    require(job["status"] == "USED" and job["product_key"] == SKU
            and job["html_sha256"] in (OLD, new), "job_changed")
    if mode == "review":
        private, key, derived_public = review.configured_signing_keys(
            private_key=os.environ["V31_REVIEW_RELEASE_PRIVATE_KEY_HEX"],
            receipt_key=os.environ["V31_READY_REVIEW_HMAC_KEY"])
        require(derived_public == public, "configured_key_mismatch")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "catalog.sqlite3"
            require(storage.restore_to(path), "catalog_missing")
            with review.Catalog(path) as catalog:
                article = review.verify_offer(policy=policy, profile=profile, route=route, sku=SKU,
                    catalog=catalog, state=state, token=os.environ["FIRECRAWL_API_KEY"])
                regenerated = article["html_content"]
                require(re.sub(r'data-v31-evidence-revision="[0-9a-f]{64}"', '', regenerated) ==
                        re.sub(r'data-v31-evidence-revision="[0-9a-f]{64}"', '', corrected), "unexpected_editorial_diff")
                now = review.utcnow()
                package = state.get_verified_evidence(**TENANT, product_key=SKU,
                    product_title=article["evidence_package"]["product_title"], now_epoch=int(now.timestamp()))
                require(package and _json_sha(package) == job["evidence_sha256"], "old_evidence_expired")
                article.update(html_content=corrected, evidence_package=package)
                payload = review.prepare_review_payload(article=article, catalog=catalog, now=now)
        digest = review.payload_digest(article)
        receipt = review.approval_receipt(candidate_sha256=digest,
            payload_sha256=review.payload_digest(payload), key=key)
        envelope.save(**TENANT, product_key=SKU, content_html=corrected, independent_review_key=None,
            attestation={"payload":payload,"candidate_sha256":digest,"signature":receipt["signature"]},
            release_signature=review.sign_release(receipt, private_key=private),
            release_public_key=public, embed_release_key=True)
    saved = envelope.load(**TENANT, html_sha256=new, release_public_key=public)
    require(saved["html_content"] == corrected and saved["review"]["article_title"] == title
            and saved["review"]["evidence_sha256"] == job["evidence_sha256"], "revision_signature_mismatch")
    if mode == "review":
        print("SIGNED_INTERNAL_LINK_REVISION", new)
        return
    user, password = wp.credentials_for(SITE)
    client = wp.WordPressRestClient(base_url=route["identifier"], username=user, application_password=password)
    client.site_settings()
    owner = dict(owner_nonce=token_hex(16), lease_name="writer")
    require(state.acquire_lease(**TENANT, **owner, now_epoch=int(time.time())), "writer_busy")
    try:
        def read():
            post = client.get_post(321)
            require(post["status"] == "draft" and post["slug"] == wp._product_slug(SITE, SKU)
                    and post["title"]["raw"] == title, "cms_identity_changed")
            return post["content"]["raw"]
        current = read()
        snapshot = state.get_job(**TENANT, fingerprint=FP)
        require(snapshot == job and current in (old_html, corrected), "unexpected_concurrent_edit")
        if current == old_html:
            require(job["html_sha256"] == OLD, "cms_revision_conflict")
            client._call("POST", "/wp-json/wp/v2/posts/321", {"content": corrected, "status": "draft"})
        require(read() == corrected, "revision_readback_failed")
        if job["html_sha256"] == OLD:
            changed = runner("""UPDATE v31_ready_jobs SET html_sha256=?
                WHERE site_key=? AND campaign=? AND fingerprint=? AND product_key=? AND status='USED'
                AND html_sha256=? AND evidence_sha256=? AND EXISTS (
                SELECT 1 FROM v31_ready_leases WHERE site_key=? AND campaign=? AND lease_name='writer'
                AND owner_nonce=? AND expires_epoch>?) RETURNING html_sha256""",
                (new, SITE, TENANT["campaign"], FP, SKU, OLD, job["evidence_sha256"],
                 SITE, TENANT["campaign"], owner["owner_nonce"], int(time.time())))
            require(changed == [{"html_sha256":new}], "revision_pointer_conflict")
    finally:
        require(state.release_lease(**TENANT, **owner), "writer_release_failed")
    for _ in range(2):
        result = deliver_reviewed_draft(site_key=SITE, fingerprint=FP, state=state,
            envelope=envelope, release_public_key=public, daily_cap=1, wordpress_client=client)
        require(result == {"status":"DRAFT_VERIFIED","draft_id":"321","html_sha256":new}, "replay_failed")
    print("REVISED_DRAFT_AND_REPLAY_VERIFIED", new)


if __name__ == "__main__":
    require(sys.argv[1:] in (["review"], ["deliver"]), "mode_invalid")
    main(sys.argv[1])
