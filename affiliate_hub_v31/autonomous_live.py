"""Opt-in release gate. The repository ships with the proposed policy inactive."""

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path

from . import automatic_blogger_drafts as blogger
from . import automatic_wordpress_drafts as wordpress
from .article_commerce import _single_verified_offer
from .autonomous_review import ANGLE, verify_affiliate_target, verify_image
from .catalog import Catalog
from .d1_http_runner import CloudflareD1HTTPRunner
from .d1_universal_ready import UniversalD1ReadyState
from .final_fact_gate import scan_final_html
from .independent_review import _official_storage
from .manual_live_release import _content, _title
from .private_ready_envelope import ImmutablePrivateReadyEnvelope
from .r2_private_ready_backend import R2PrivateReadyBackend
from .reviewed_ready_promotion import _offer_in_same_html
from .routing import sites
from .universal_evidence_ready import _fingerprint

POLICY_PATH = Path(__file__).with_name("autonomous_live_policy.json")


class LivePolicyError(ValueError):
    pass


def approved_policy(site_key, *, policy_path=POLICY_PATH, env=None):
    env = os.environ if env is None else env
    raw = policy_path.read_bytes()
    policy = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    if (policy.get("version") != 1 or policy.get("activation") != "approved"
            or env.get("V31_AUTO_LIVE_APPROVED_POLICY_SHA256") != digest):
        raise LivePolicyError("live_policy_not_approved")
    rules = policy.get("sites", {}).get(site_key)
    if not isinstance(rules, dict) or set(rules) != {
        "max_attempts_per_utc_day", "minimum_interval_seconds", "minimum_article_words",
    }:
        raise LivePolicyError("live_site_policy_missing")
    for name, low, high in (("max_attempts_per_utc_day", 1, 8),
                            ("minimum_interval_seconds", 3600, 604800),
                            ("minimum_article_words", 350, 2500)):
        if type(rules[name]) is not int or not low <= rules[name] <= high:
            raise LivePolicyError("live_policy_limits_invalid")
    return digest, rules


def claim_attempt(state, *, tenant, fingerprint, post_id, digest, limits, now):
    site_key, campaign = tenant["site_key"], tenant["campaign"]
    rows = state._call("""
        INSERT INTO v31_autonomous_live_attempts
          (site_key,campaign,fingerprint,post_id,policy_sha256,created_epoch,status)
        SELECT ?,?,?,?,?,?,'CLAIMED'
        WHERE EXISTS (
          SELECT 1 FROM v31_ready_jobs j JOIN v31_verified_evidence e
            ON e.site_key=j.site_key AND e.campaign=j.campaign
            AND e.product_key=j.product_key AND e.evidence_sha256=j.evidence_sha256
          WHERE j.site_key=? AND j.campaign=? AND j.fingerprint=? AND j.status='USED'
            AND e.verified_epoch<=? AND e.expires_epoch>?
        ) AND NOT EXISTS (
          SELECT 1 FROM v31_autonomous_live_attempts
          WHERE site_key=? AND campaign=? AND
            (status IN ('CLAIMED','FAILED') OR created_epoch>?)
        ) AND (
          SELECT count(*) FROM v31_autonomous_live_attempts
          WHERE site_key=? AND campaign=? AND created_epoch>=?
        ) < ?
        ON CONFLICT DO NOTHING
        RETURNING fingerprint
    """, (site_key,campaign,fingerprint,post_id,digest,now,
           site_key,campaign,fingerprint,now,now,
           site_key,campaign,now-limits["minimum_interval_seconds"],
           site_key,campaign,now-now%86400,limits["max_attempts_per_utc_day"]))
    return rows == [{"fingerprint": fingerprint}]


def record_outcome(state, *, tenant, fingerprint, status):
    rows = state._call("""
        UPDATE v31_autonomous_live_attempts SET status=?
        WHERE site_key=? AND campaign=? AND fingerprint=? AND status='CLAIMED'
        RETURNING status
    """, (status, tenant["site_key"], tenant["campaign"], fingerprint))
    if rows != [{"status": status}]:
        raise LivePolicyError("live_outcome_requires_reconciliation")


def _cms(route, home, post_id, wordpress_client, blogger_service):
    if route["platform"] == "wordpress" and route["identifier"] == home:
        client = wordpress_client
        if client is None:
            username, password = wordpress.credentials_for(route["site_key"])
            client = wordpress.WordPressRestClient(base_url=home, username=username,
                                                   application_password=password)
        if not wordpress._verify_blog_url(client.site_settings().get("url"), home):
            raise LivePolicyError("live_wordpress_identity_mismatch")
        return (lambda: client.get_post(int(post_id)),
                lambda: client._call("POST", f"/wp-json/wp/v2/posts/{post_id}", {"status": "publish"}),
                "publish")
    if route["platform"] != "blogger":
        raise LivePolicyError("live_cms_identity_mismatch")
    service = blogger_service or blogger._get_blogger_service()
    blog_id = route["identifier"]
    blog = service.blogs().get(blogId=blog_id).execute()
    if blogger.validate_remote_identity(route, blog) != home:
        raise LivePolicyError("live_blogger_identity_mismatch")
    return (lambda: service.posts().get(blogId=blog_id, postId=post_id, view="ADMIN").execute(),
            lambda: service.posts().publish(blogId=blog_id, postId=post_id).execute(num_retries=0),
            "live")


def release(*, site_key, post_id, fingerprint, catalog, state, envelope,
            expected_html_sha256,
            policy_path=POLICY_PATH, env=None, wordpress_client=None, blogger_service=None):
    env = os.environ if env is None else env
    digest, limits = approved_policy(site_key, policy_path=policy_path, env=env)
    route = sites().get(site_key)
    if (not route or route["publish_enabled"] is not False
            or not re.fullmatch(r"[0-9]{1,24}", post_id)
            or not re.fullmatch(r"[a-f0-9]{64}", fingerprint)):
        raise LivePolicyError("live_route_invalid")
    tenant = {"site_key": site_key, "campaign": route["campaign"]}
    job = state.get_job(**tenant, fingerprint=fingerprint)
    if not job or job["status"] != "USED" or job["html_sha256"] != expected_html_sha256:
        raise LivePolicyError("live_requires_verified_draft")
    public_key = env.get("V31_AUTONOMOUS_RELEASE_PUBLIC_KEY_HEX", "")
    if not re.fullmatch(r"[a-f0-9]{64}", public_key):
        raise LivePolicyError("live_verifier_public_key_missing")
    stored = envelope.load(**tenant, html_sha256=job["html_sha256"], release_public_key=public_key)
    content, review = stored["html_content"], stored["review"]
    sku = review["product_key"]
    if (review["angle"] != ANGLE or sku != job["product_key"]
            or review["evidence_sha256"] != job["evidence_sha256"]
            or _fingerprint(sku, review["primary_query"], review["angle"]) != fingerprint):
        raise LivePolicyError("live_manifest_mismatch")

    _, image, affiliate = _single_verified_offer(catalog, site_key=site_key, product_key=sku)
    _offer_in_same_html(content, image=image, affiliate=affiliate)
    verify_affiliate_target(affiliate, sku)
    verify_image(image)
    scan = scan_final_html(content)
    words = re.findall(r"\b[\wÀ-ÿ]+\b", " ".join([*scan.unbound, *scan.facts.values()]))
    if len(words) < limits["minimum_article_words"]:
        raise LivePolicyError("live_editorial_length_insufficient")
    read, publish, live_status = _cms(route, review["site_url"], post_id, wordpress_client, blogger_service)

    def exact(status):
        post = read()
        if route["platform"] == "blogger":
            marker = "v31-" + fingerprint[:32]
            is_ours = (marker in (post.get("labels") or [])
                       and str((post.get("blog") or {}).get("id")) == route["identifier"])
        else:
            slug = wordpress._product_slug(site_key, sku)
            is_ours = slug in (post.get("slug"), post.get("generated_slug"))
        return (is_ours and str(post.get("id")) == post_id and str(post.get("status")).casefold() == status
                and _content(post, route["platform"]) == content
                and _title(post, route["platform"]) == review["article_title"])

    if not exact("draft"):
        raise LivePolicyError("live_draft_bytes_changed")
    if not claim_attempt(state, tenant=tenant, fingerprint=fingerprint, post_id=post_id,
                         digest=digest, limits=limits, now=int(time.time())):
        raise LivePolicyError("live_attempt_paused_or_rate_limited")
    try:
        if not exact("draft"):
            raise LivePolicyError("live_draft_changed_before_publish")
        publish()
        if not exact(live_status):
            raise LivePolicyError("live_readback_unverified")
    except Exception:
        # A write may have happened. Keep the tenant stopped for reconciliation.
        record_outcome(state, tenant=tenant, fingerprint=fingerprint, status="FAILED")
        raise LivePolicyError("live_attempt_stopped_requires_reconciliation") from None
    record_outcome(state, tenant=tenant, fingerprint=fingerprint, status="PUBLISHED")
    return {"status": "LIVE_CONFIRMED", "site_key": site_key, "post_id": post_id,
            "policy_sha256": digest, "html_sha256": job["html_sha256"]}


def main():
    parser = argparse.ArgumentParser(description="Publicação V31 regida por política autorizada")
    parser.add_argument("--execute-approved-policy", action="store_true", required=True)
    parser.parse_args()
    try:
        proof = json.loads(os.environ.get("V31_VERIFIED_DRAFT", ""))
        site_key = proof["site_key"]
        if proof.get("status") != "DRAFT_VERIFIED":
            raise LivePolicyError("live_requires_verified_draft")
        approved_policy(site_key)
        storage = _official_storage()
        state = UniversalD1ReadyState(CloudflareD1HTTPRunner.from_environment(allow_mutations=True))
        envelope = ImmutablePrivateReadyEnvelope(backend=R2PrivateReadyBackend(storage))
        with tempfile.TemporaryDirectory(prefix="v31-approved-live-") as directory:
            path = Path(directory) / "catalog.sqlite3"
            if not storage.restore_to(path):
                raise LivePolicyError("live_official_catalog_missing")
            with Catalog(path) as catalog:
                result = release(site_key=site_key, post_id=proof["draft_id"],
                                 fingerprint=proof["fingerprint"], catalog=catalog,
                                 state=state, envelope=envelope,
                                 expected_html_sha256=proof["html_sha256"])
    except LivePolicyError as error:
        print(str(error))
        return 1
    except Exception:
        print("autonomous_live_failed_closed")
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
