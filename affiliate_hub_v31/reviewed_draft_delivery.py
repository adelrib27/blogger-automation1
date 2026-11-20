"""Deliver one reviewed READY job via the existing draft publishers."""

from __future__ import annotations

import argparse
import json
import os
import time
from secrets import token_hex

from . import automatic_blogger_drafts as blogger
from . import automatic_wordpress_drafts as wordpress
from .d1_universal_ready import UniversalD1ReadyState
from .d1_http_runner import CloudflareD1HTTPRunner
from .private_ready_envelope import ImmutablePrivateReadyEnvelope
from .r2_private_ready_backend import R2PrivateReadyBackend
from .routing import sites
from .universal_evidence_ready import _fingerprint


class ReviewedDraftError(ValueError):
    """A delivery or reconciliation failure without private content."""


def _blogger_draft(*, route, review, marker, content, authorize, service):
    blog_id = route["identifier"]
    service = service or blogger._get_blogger_service()
    blog = service.blogs().get(blogId=blog_id).execute()
    if blogger.validate_remote_identity(route, blog) != review["site_url"]:
        raise ReviewedDraftError("reviewed_blogger_site_mismatch")
    history = blogger._list_posts(service, blog_id, label=marker)
    matches = [post for post in history if marker in (post.get("labels") or [])]
    if len(matches) > 1:
        raise ReviewedDraftError("reviewed_blogger_multiple_drafts")
    if matches:
        post_id = matches[0].get("id")
    else:
        if not authorize():
            return None
        result = service.posts().insert(
            blogId=blog_id, isDraft=True, body={
                "kind": "blogger#post", "title": review["article_title"],
                "content": content, "labels": [marker],
            },
        ).execute(num_retries=0)
        post_id = result.get("id")
    if not isinstance(post_id, str) or not post_id.isascii() or not post_id.isdecimal():
        raise ReviewedDraftError("reviewed_blogger_post_id_invalid")
    post = service.posts().get(blogId=blog_id, postId=post_id, view="ADMIN").execute()
    if (str(post.get("id")) != post_id
            or str((post.get("blog") or {}).get("id")) != blog_id
            or str(post.get("status", "")).lower() != "draft"
            or marker not in (post.get("labels") or [])
            or post.get("title") != review["article_title"]
            or post.get("content") != content):
        raise ReviewedDraftError("reviewed_blogger_draft_readback_mismatch")
    if matches:
        authorize()
    return post_id


def _wordpress_draft(*, route, review, content, authorize, client):
    site_key = route["site_key"]
    site_url = route["identifier"]
    if site_url != review["site_url"]:
        raise ReviewedDraftError("reviewed_wordpress_site_mismatch")
    if client is None:
        user, password = wordpress.credentials_for(site_key)
        client = wordpress.WordPressRestClient(
            base_url=site_url, username=user, application_password=password,
        )
    settings = client.site_settings()
    if not wordpress._verify_blog_url(settings.get("url", ""), site_url):
        raise ReviewedDraftError("reviewed_wordpress_site_mismatch")
    product_key = review["product_key"]
    if set(blogger.KEY_PATTERN.findall(content)) != {product_key}:
        raise ReviewedDraftError("reviewed_wordpress_product_marker_mismatch")
    slug = wordpress._product_slug(site_key, product_key)
    history = client.list_posts(include_unpublished=True, slug=slug)
    matches = [post for post in history
               if slug in (post.get("slug"), post.get("generated_slug"))]
    if len(matches) > 1:
        raise ReviewedDraftError("reviewed_wordpress_multiple_drafts")
    if matches:
        post_id = matches[0].get("id")
    else:
        if not authorize():
            return None
        result = client.create_draft(title=review["article_title"],
                                     slug=slug, content=content)
        post_id = result.get("id")
    post = client.get_post(post_id)
    if (post.get("id") != post_id or post.get("status") != "draft"
            or slug not in (post.get("slug"), post.get("generated_slug"))
            or (post.get("title") or {}).get("raw") != review["article_title"]
            or (post.get("content") or {}).get("raw") != content):
        raise ReviewedDraftError("reviewed_wordpress_draft_readback_mismatch")
    if matches:
        authorize()
    return str(post_id)


def deliver_reviewed_draft(*, site_key: str, fingerprint: str,
                          state: UniversalD1ReadyState,
                          envelope: ImmutablePrivateReadyEnvelope,
                          independent_review_key: bytes,
                          blogger_service=None, wordpress_client=None) -> dict:
    """Claim one POST through D1. After an ambiguous POST, replays only read CMS.

    USED is the durable POST authorization, not proof of delivery. A missing
    draft for an existing USED job requires reconciliation by an operator.
    """
    route = sites().get(site_key)
    if (not route or route.get("site_key") != site_key
            or route.get("publish_enabled") is not False
            or route.get("platform") not in ("blogger", "wordpress")):
        raise ReviewedDraftError("reviewed_draft_route_invalid")
    campaign = route["campaign"]
    tenant = {"site_key": site_key, "campaign": campaign}
    owner = {"owner_nonce": token_hex(16), "lease_name": "writer"}
    if not state.acquire_lease(**tenant, **owner, now_epoch=int(time.time())):
        return {"status": "LEASE_BUSY"}
    try:
        job = state.get_job(**tenant, fingerprint=fingerprint)
        if job is None:
            raise ReviewedDraftError("reviewed_draft_job_missing")
        stored = envelope.load(**tenant, html_sha256=job["html_sha256"],
                               independent_review_key=independent_review_key)
        review = stored["review"]
        if (review["product_key"] != job["product_key"]
                or review["evidence_sha256"] != job["evidence_sha256"]
                or _fingerprint(review["product_key"], review["primary_query"],
                                review["angle"]) != fingerprint):
            raise ReviewedDraftError("reviewed_draft_binding_mismatch")

        def authorize():
            if job["status"] == "USED":
                return False
            if not state.consume_one(**tenant, owner_nonce=owner["owner_nonce"],
                                     fingerprint=fingerprint, now_epoch=int(time.time())):
                raise ReviewedDraftError("reviewed_draft_claim_denied")
            return True

        try:
            inputs = {"route": route, "review": review,
                      "content": stored["html_content"], "authorize": authorize}
            if route["platform"] == "blogger":
                post_id = _blogger_draft(**inputs, marker=f"v31-{fingerprint[:32]}",
                                         service=blogger_service)
            else:
                post_id = _wordpress_draft(**inputs, client=wordpress_client)
        except ReviewedDraftError:
            raise
        except Exception:
            raise ReviewedDraftError("reviewed_draft_delivery_unverified") from None
        if post_id is None:
            return {"status": "DRAFT_RECONCILIATION_REQUIRED"}
        return {"status": "DRAFT_VERIFIED", "draft_id": post_id,
                "html_sha256": job["html_sha256"]}
    finally:
        if not state.release_lease(**tenant, **owner):
            raise ReviewedDraftError("reviewed_draft_lease_release_failed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificar e entregar um READY em DRAFT")
    parser.add_argument("--site-key", required=True)
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--execute-draft", action="store_true", required=True)
    args = parser.parse_args()
    try:
        review_key = bytes.fromhex(os.environ.get("V31_INDEPENDENT_REVIEW_KEY_HEX", ""))
        if len(review_key) < 32:
            raise ReviewedDraftError("reviewed_draft_verification_key_missing")
        result = deliver_reviewed_draft(
            site_key=args.site_key, fingerprint=args.fingerprint,
            state=UniversalD1ReadyState(
                CloudflareD1HTTPRunner.from_environment(allow_mutations=True)),
            envelope=ImmutablePrivateReadyEnvelope(
                backend=R2PrivateReadyBackend.from_environment()),
            independent_review_key=review_key,
        )
    except ValueError:
        print("V31_REVIEWED_DRAFT_FAILED_CLOSED")
        return 1
    print(json.dumps(result))
    return 0 if result["status"] == "DRAFT_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
