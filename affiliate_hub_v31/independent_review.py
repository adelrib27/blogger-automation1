"""Approve an immutable private candidate from a protected GitHub review job."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from secrets import token_hex
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .article_commerce import _single_verified_offer
from .catalog import Catalog
from .d1_http_runner import CloudflareD1HTTPRunner
from .d1_universal_ready import UniversalD1ReadyState
from .final_fact_gate import reviewed_text_digest, scan_final_html, verify_final_html_facts
from .future_blog_seo import audit_future_article
from .private_ready_envelope import ImmutablePrivateReadyEnvelope
from .r2_private_ready_backend import ACCOUNT_ID, BUCKET, R2PrivateReadyBackend, _error_response
from .r2_state import R2State
from .review_signatures import approval_receipt, payload_digest, sign_release
from .reviewed_ready_promotion import _json_sha, _offer_in_same_html, review_payload, stage_reviewed_ready
from .routing import sites
from .site_request_queue import load_requests

REPOSITORY = "adelrib27/blogger-automation1"
REVIEW_ENVIRONMENT = "v31-independent-review"
MAX_CANDIDATE_BYTES = 450_000
HEX_SHA = re.compile(r"[0-9a-f]{64}")
SEO_FIELDS = ("site_url", "article_url", "meta_description", "primary_query", "intent",
              "html_content", "published_posts", "keyword_evidence", "cluster_id")
ARTICLE_FIELDS = frozenset(SEO_FIELDS) | {
    "site_key", "product_key", "article_title", "angle", "evidence_package",
    "used_evidence_ids",
}


class IndependentReviewError(ValueError):
    """Sanitized errors for the protected workflow."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _proposed_evidence(article: dict) -> dict:
    evidence = article.get("evidence_package")
    if (not isinstance(evidence, dict) or evidence.get("product_status") != "PROPOSED"
            or not isinstance(evidence.get("sources"), list)
            or not all(isinstance(source, dict) and source.get("authorized") is False
                       and source.get("review_status") == "PROPOSED"
                       for source in evidence["sources"])):
        raise IndependentReviewError("review_candidate_must_contain_only_proposed_evidence")
    return evidence


def _material_for_review(article: dict) -> dict:
    evidence = _proposed_evidence(article)
    prepared = {
        **evidence, "product_status": "VERIFIED",
        "sources": [{**source, "authorized": True, "review_status": "AUTHORIZED"}
                    for source in evidence["sources"]],
    }
    return {**article, "evidence_package": prepared}


def decode_candidate(raw: bytes, *, digest: str) -> dict:
    if (not isinstance(digest, str) or not HEX_SHA.fullmatch(digest)
            or not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_CANDIDATE_BYTES
            or hashlib.sha256(raw).hexdigest() != digest):
        raise IndependentReviewError("review_candidate_digest_mismatch")
    try:
        article = json.loads(raw)
        canonical = json.dumps(article, sort_keys=True, ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, RecursionError):
        raise IndependentReviewError("review_candidate_json_invalid") from None
    if (not isinstance(article, dict) or set(article) != ARTICLE_FIELDS
            or canonical != raw or not isinstance(article["site_key"], str)):
        raise IndependentReviewError("review_candidate_schema_invalid")
    scan_final_html(article["html_content"])
    _proposed_evidence(article)
    return article


def candidate_key(site_key: str, digest: str) -> str:
    if (not isinstance(site_key, str) or not re.fullmatch(r"[a-z0-9_]{3,50}", site_key)
            or not isinstance(digest, str) or not HEX_SHA.fullmatch(digest)):
        raise IndependentReviewError("review_candidate_reference_invalid")
    if not any(request["site_key"] == site_key for request in load_requests()):
        raise IndependentReviewError("review_candidate_request_missing")
    return f"v31/private-review/v1/{site_key}/{digest}.json"


def _official_storage() -> R2State:
    if (os.environ.get("V31_EDITORIAL_R2_ACCOUNT_ID") != ACCOUNT_ID
            or os.environ.get("V31_EDITORIAL_R2_BUCKET") != BUCKET):
        raise IndependentReviewError("review_storage_identity_invalid")
    return R2State.from_env()


def read_candidate(storage: R2State, *, site_key: str, digest: str) -> bytes:
    key = candidate_key(site_key, digest)
    try:
        obj = storage.s3.get_object(Bucket=BUCKET, Key=key)
        with obj["Body"] as body:
            raw = body.read(MAX_CANDIDATE_BYTES + 1)
    except Exception:
        raise IndependentReviewError("review_candidate_get_failed") from None
    article = decode_candidate(raw, digest=digest)
    if article["site_key"] != site_key:
        raise IndependentReviewError("review_candidate_tenant_mismatch")
    return raw


def submit_candidate(storage: R2State, *, raw: bytes) -> tuple[str, str]:
    try:
        article = json.loads(raw)
        raw = json.dumps(article, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, RecursionError):
        raise IndependentReviewError("review_candidate_json_invalid") from None
    digest = hashlib.sha256(raw).hexdigest()
    article = decode_candidate(raw, digest=digest)
    site_key = article["site_key"]
    key = candidate_key(site_key, digest)
    try:
        storage.s3.put_object(Bucket=BUCKET, Key=key, Body=raw, IfNoneMatch="*",
                              ContentType="application/json", CacheControl="private, no-store")
    except Exception as exc:
        if _error_response(exc) != ("PreconditionFailed", 412):
            raise IndependentReviewError("review_candidate_put_failed") from None
    if read_candidate(storage, site_key=site_key, digest=digest) != raw:
        raise IndependentReviewError("review_candidate_readback_mismatch")
    return site_key, digest


def require_independent_approval(env: dict, *, site_key: str, digest: str) -> str:
    run = env.get("GITHUB_RUN_ID", "")
    reviewer = env.get("V31_PROTECTED_REVIEWER", "")
    token = env.get("V31_ACTIONS_READ_TOKEN", "")
    if (env.get("GITHUB_REPOSITORY") != REPOSITORY
            or env.get("GITHUB_REF") != "refs/heads/main"
            or env.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
            or not re.fullmatch(r"[0-9]{1,20}", run)
            or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", reviewer) or not token):
        raise IndependentReviewError("protected_review_context_required")
    try:
        with Path(env["GITHUB_EVENT_PATH"]).open("rb") as event_file:
            inputs = json.load(event_file)["inputs"]
        if inputs["site_key"] != site_key or inputs["candidate_digest"] != digest:
            raise ValueError("different candidate")
        request = Request(
            f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{run}/approvals",
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/vnd.github+json"},
        )
        with build_opener(_NoRedirect()).open(request, timeout=15) as response:
            decisions = json.loads(response.read(250_001))
        if not isinstance(decisions, list):
            raise ValueError("invalid review decisions")
        for entry in decisions:
            if not any(e["name"] == REVIEW_ENVIRONMENT for e in entry["environments"]):
                continue
            if (entry["state"].casefold() == "approved"
                    and entry["user"]["login"].casefold() == reviewer.casefold()):
                return reviewer
            raise IndependentReviewError("independent_review_not_approved")
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        raise IndependentReviewError("independent_review_lookup_failed") from None
    raise IndependentReviewError("independent_approval_missing")


def prepare_review_payload(*, article: dict, catalog: Catalog, now: datetime) -> dict:
    site_key = article["site_key"]
    route = sites().get(site_key)
    if route is None or route.get("publish_enabled") is not False:
        raise IndependentReviewError("review_route_invalid")
    product_key = article["product_key"]
    title, image, affiliate = _single_verified_offer(
        catalog, site_key=site_key, product_key=product_key, verified_site_route=route)
    html_content = article["html_content"]
    _offer_in_same_html(html_content, image=image, affiliate=affiliate)
    hashes = sorted({reviewed_text_digest(t) for t in scan_final_html(html_content).unbound})
    verify_final_html_facts(
        html_content=html_content, evidence_package=article["evidence_package"],
        product_key=product_key, product_title=title,
        used_evidence_ids=article["used_evidence_ids"],
        trusted_reviewed_text_hashes=hashes, now=now,
    )
    seo_context = {field: article[field] for field in SEO_FIELDS}
    seo_context["title"] = article["article_title"]
    seo = audit_future_article(**seo_context)
    if (seo["status"] != "READY_FOR_EDITORIAL_SAFE_REVIEW"
            or seo["blockers"] or seo["keyword_source_verified"] is not True):
        raise IndependentReviewError("review_candidate_seo_failed")
    return review_payload(
        site_key=site_key, campaign=route["campaign"], product_key=product_key,
        site_url=article["site_url"], article_url=article["article_url"],
        article_title=article["article_title"], primary_query=article["primary_query"],
        angle=article["angle"], html_sha256=hashlib.sha256(html_content.encode("utf-8")).hexdigest(),
        evidence_sha256=_json_sha(article["evidence_package"]),
        seo_context_sha256=_json_sha(seo_context), reviewed_text_hashes=hashes,
    )


@contextmanager
def _review_context(*, site_key: str, digest: str):
    storage = _official_storage()
    # Prepare the would-be approved material only in memory. C77 will persist
    # it only when the separately signed receipt is valid for these bytes.
    proposal = decode_candidate(read_candidate(storage, site_key=site_key, digest=digest),
                                digest=digest)
    article = _material_for_review(proposal)
    with tempfile.TemporaryDirectory(prefix="v31-review-catalog-") as directory:
        path = Path(directory) / "catalog.sqlite3"
        if not storage.restore_to(path):
            raise IndependentReviewError("review_catalog_missing")
        with Catalog(path) as catalog:
            now = datetime.now(timezone.utc)
            payload = prepare_review_payload(article=article, catalog=catalog, now=now)
            yield storage, catalog, article, payload, now


def authorize_receipt(*, site_key: str, digest: str, payload_sha256: str) -> dict:
    require_independent_approval(os.environ, site_key=site_key, digest=digest)
    receipt = approval_receipt(
        candidate_sha256=digest, payload_sha256=payload_sha256,
        key=bytes.fromhex(os.environ.get("V31_READY_REVIEW_HMAC_KEY", "")),
    )
    release = sign_release(receipt, private_key=os.environ.get(
        "V31_REVIEW_RELEASE_PRIVATE_KEY_HEX", ""))
    return {"hmac": receipt["signature"], "release_signature": release}


def stage_approved_receipt(*, site_key: str, digest: str, payload_sha256: str) -> dict:
    with _review_context(site_key=site_key, digest=digest) as (
        storage, catalog, article, payload, now,
    ):
        if payload_digest(payload) != payload_sha256:
            raise IndependentReviewError("review_payload_changed")
        attestation = {"payload": payload, "candidate_sha256": digest,
                       "signature": os.environ.get("V31_APPROVAL_HMAC", "")}
        return stage_reviewed_ready(
            **article, catalog=catalog, owner_nonce=token_hex(16), now=now,
            state=UniversalD1ReadyState(CloudflareD1HTTPRunner.from_environment(
                allow_mutations=True)),
            envelope=ImmutablePrivateReadyEnvelope(backend=R2PrivateReadyBackend(storage)),
            independent_review_key=None, attestation=attestation,
            release_signature=os.environ.get("V31_APPROVAL_RELEASE_SIGNATURE", ""),
            release_public_key=os.environ.get("V31_REVIEW_RELEASE_PUBLIC_KEY_HEX", ""),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Revisão independente de candidato V31")
    actions = parser.add_subparsers(dest="action", required=True)
    upload = actions.add_parser("submit")
    upload.add_argument("--file", required=True, type=Path)
    export = actions.add_parser("export")
    export.add_argument("--site-key", required=True)
    export.add_argument("--digest", required=True)
    export.add_argument("--file", required=True, type=Path)
    for action in ("prepare", "authorize", "stage"):
        command = actions.add_parser(action)
        command.add_argument("--site-key", required=True)
        command.add_argument("--digest", required=True)
        if action != "prepare":
            command.add_argument("--payload-sha256", required=True)
    args = parser.parse_args()
    try:
        if args.action == "stage":
            result = stage_approved_receipt(site_key=args.site_key, digest=args.digest,
                                            payload_sha256=args.payload_sha256)
            if result.get("job_status") not in ("READY", "USED"):
                raise IndependentReviewError("review_ready_reservation_unverified")
            print(json.dumps({"fingerprint": result["fingerprint"], "candidate": args.digest}))
        elif args.action == "prepare":
            with _review_context(site_key=args.site_key, digest=args.digest) as (
                _, _, _, payload, _,
            ):
                print(json.dumps({"payload_sha256": payload_digest(payload)}))
        elif args.action == "authorize":
            print(json.dumps(authorize_receipt(site_key=args.site_key, digest=args.digest,
                                               payload_sha256=args.payload_sha256)))
        elif args.action == "submit":
            with args.file.open("rb") as stream:
                raw = stream.read(MAX_CANDIDATE_BYTES + 1)
            if len(raw) > MAX_CANDIDATE_BYTES:
                raise IndependentReviewError("review_candidate_too_large")
            site, digest = submit_candidate(_official_storage(), raw=raw)
            print(json.dumps({"site_key": site, "candidate": digest}))
        else:
            raw = read_candidate(_official_storage(), site_key=args.site_key, digest=args.digest)
            with args.file.open("xb") as destination:
                destination.write(raw)
    except (ValueError, OSError, TypeError, KeyError, RuntimeError):
        print("V31_INDEPENDENT_REVIEW_FAILED_CLOSED")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
