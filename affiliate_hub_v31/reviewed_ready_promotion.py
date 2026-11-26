"""C77 — one SAFE, universal preflight before D1 READY metadata reservation.

Only catalog/SEO/evidence/HTML are checked here. A separately controlled
editorial reviewer must sign the *exact* payload using a secret unavailable to
the AI or ordinary writer. This cannot verify a review actually happened:
signing-key custody and independent source approval are operational gates.

An injected private envelope can persist verified HTML before READY.
The caller configures storage explicitly. No research or CMS calls occur here.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from time import monotonic
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit
from typing import TYPE_CHECKING

from .article_commerce import CommerceArticleError, _single_verified_offer
from .d1_universal_ready import UniversalD1ReadyState, D1SafeError
from .final_fact_gate import FinalFactGateError, verify_final_html_facts
from .future_blog_seo import FutureSEOError, audit_future_article
from .routing import sites
from .wordpress_category_routing import category_for_product, validate_binding
from .review_signatures import verify_public_attestation
from .universal_evidence_ready import (
    UniversalReadyError, UniversalReadyPolicy, _fingerprint,
    evidence_whitelist,
)

if TYPE_CHECKING:
    from .private_ready_envelope import ImmutablePrivateReadyEnvelope


class ReviewedReadyError(ValueError):
    """Sanitized failure; no SQL, model text, product links, or keys."""


class _CommerceHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images: list[str] = []
        self.shopee_links: list[dict] = []
        self.links: list[dict] = []
        self.text: list[str] = []
        self._anchor: dict | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img":
            self.images.append(a.get("src"))
        elif tag == "a":
            self._anchor = {"href": a.get("href"), "rel": a.get("rel", ""),
                            "text": []}
            self.links.append(self._anchor)

    def handle_data(self, data):
        self.text.append(data)
        if self._anchor is not None:
            self._anchor["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            self._anchor = None


def _offer_in_same_html(html: str, *, image: str, affiliate: str) -> None:
    scan = _CommerceHTML()
    scan.feed(html)
    scan.close()
    # Fail closed if content displays an unrelated SKU photo.
    if not scan.images or any(src != image for src in scan.images):
        raise ReviewedReadyError("sku_image_not_exact_in_final_html")
    verified_links = 0
    cta = False
    for link in scan.links:
        href = link["href"]
        if not isinstance(href, str):
            continue
        try:
            host = (urlsplit(href).hostname or "").lower()
        except ValueError:
            raise ReviewedReadyError("affiliate_link_malformed") from None
        if host == "s.shopee.com.br" and href != affiliate:
            raise ReviewedReadyError("different_shopee_campaign_in_html")
        if href == affiliate:
            rel = link["rel"]
            words = rel.casefold().split() if isinstance(rel, str) else []
            if "sponsored" not in words or "nofollow" not in words:
                raise ReviewedReadyError("affiliate_rel_required")
            verified_links += 1
            cta |= "shopee" in " ".join(link["text"]).casefold()
    if verified_links == 0 or not cta:
        raise ReviewedReadyError("exact_campaign_cta_required")
    if "link de afiliado" not in " ".join(scan.text).casefold():
        raise ReviewedReadyError("affiliate_disclosure_required")


def _json_sha(value: dict) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True
    ).encode("utf-8")).hexdigest()


def review_payload(
    *, site_key: str, campaign: str, product_key: str,
    site_url: str, article_url: str, article_title: str,
    primary_query: str, angle: str, html_sha256: str,
    evidence_sha256: str, seo_context_sha256: str,
    reviewed_text_hashes: list[str], wordpress_category: dict | None = None,
) -> dict:
    """Construct *unsigned* material for an INDEPENDENT review service.

    A valid signature may be created only by a separate trusted reviewer
    that has visually/semantically approved every hash and evidence source.
    Merely calling this function is never a review or permission to publish.
    """
    binding = {} if wordpress_category is None else {"wordpress_category": validate_binding(wordpress_category)}
    return {
        "version": 2 if binding else 1, **binding,
        "site_key": site_key, "campaign": campaign,
        "product_key": product_key, "site_url": site_url,
        "article_url": article_url, "article_title": article_title,
        "primary_query": primary_query, "angle": angle,
        "html_sha256": html_sha256, "evidence_sha256": evidence_sha256,
        "seo_context_sha256": seo_context_sha256,
        "reviewed_text_hashes": sorted(reviewed_text_hashes),
    }


def _check_review_signature(payload: dict, *, attestation: dict, key: bytes) -> None:
    if not isinstance(key, bytes) or len(key) < 32:
        raise ReviewedReadyError("independent_review_key_required")
    if (not isinstance(attestation, dict)
            or set(attestation) != {"payload", "signature"}
            or attestation["payload"] != payload):
        raise ReviewedReadyError("review_attestation_mismatch")
    signature = attestation["signature"]
    if not isinstance(signature, str) or not re.fullmatch("[0-9a-f]{64}", signature):
        raise ReviewedReadyError("review_attestation_invalid")
    canonical = json.dumps(payload, ensure_ascii=False,
                           sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected = hmac.new(key, canonical, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ReviewedReadyError("independent_review_signature_invalid")


def stage_reviewed_ready(
    *, catalog, state: UniversalD1ReadyState,
    site_key: str, product_key: str, html_content: str,
    site_url: str, article_url: str, article_title: str,
    meta_description: str, primary_query: str, angle: str,
    intent: str, keyword_evidence: dict,
    published_posts: list[dict], cluster_id: str,
    evidence_package: dict, used_evidence_ids: list[str],
    attestation: dict, independent_review_key: bytes | None,
    owner_nonce: str, now: datetime,
    policy: UniversalReadyPolicy = UniversalReadyPolicy(),
    envelope: ImmutablePrivateReadyEnvelope | None = None,
    release_signature: str | None = None,
    release_public_key: str | None = None,
    embed_release_key: bool = False,
) -> dict:
    """Preflight and reserve D1 READY after optional exact R2 readback.

    The caller must independently load attestation + secret from protected
    review infrastructure (not from an AI candidate or user-submitted form).
    The caller must verify the approved source data upstream; syntactically
    valid keyword/source metadata is not external research proof on its own.
    """
    if not isinstance(state, UniversalD1ReadyState):
        raise ReviewedReadyError("isolated_d1_state_required")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ReviewedReadyError("verified_clock_required")
    if release_public_key is not None and envelope is None:
        raise ReviewedReadyError("approved_release_requires_private_envelope")
    if envelope is not None:
        from .private_ready_envelope import ImmutablePrivateReadyEnvelope

        if not isinstance(envelope, ImmutablePrivateReadyEnvelope):
            raise ReviewedReadyError("immutable_private_envelope_required")
    clock = now.astimezone(timezone.utc)
    epoch = int(clock.timestamp())
    started = monotonic()
    try:
        route = sites().get(site_key)
        if (not isinstance(route, dict) or route.get("site_key") != site_key
                or route.get("platform") not in ("blogger", "wordpress")
                or route.get("publish_enabled") is not False):
            raise ReviewedReadyError("registered_draft_only_site_required")
        campaign = route["campaign"]
        # WordPress identity is a canonical URL in routing.sites; never
        # authorize SEO or editorial review on an unrelated hostname.
        if (route["platform"] == "wordpress"
                and route.get("identifier") != site_url):
            raise ReviewedReadyError("wordpress_site_origin_mismatch")
        title, image, affiliate = _single_verified_offer(
            catalog, site_key=site_key, product_key=product_key,
            verified_site_route=route,
        )
        _offer_in_same_html(html_content, image=image, affiliate=affiliate)
        if (not isinstance(angle, str) or not 6 <= len(angle.strip()) <= 200
                or not isinstance(primary_query, str)
                or not 3 <= len(primary_query.strip()) <= 160):
            raise ReviewedReadyError("editorial_intent_required")
        seo_context = {
            "site_url": site_url, "article_url": article_url,
            "title": article_title, "meta_description": meta_description,
            "primary_query": primary_query, "intent": intent,
            "html_content": html_content, "published_posts": published_posts,
            "keyword_evidence": keyword_evidence, "cluster_id": cluster_id,
        }
        seo = audit_future_article(**seo_context)
        if (seo["status"] != "READY_FOR_EDITORIAL_SAFE_REVIEW"
                or seo["blockers"] or seo["keyword_source_verified"] is not True):
            raise ReviewedReadyError("seo_live_html_preflight_failed")
        evidence_whitelist(
            package=evidence_package, product_key=product_key,
            product_title=title, now=clock, policy=policy,
        )
        # The only accepted prose hashes come from the separately signed
        # editorial attestation. No model-controlled approval boolean.
        hashes = attestation.get("payload", {}).get("reviewed_text_hashes", []) \
            if isinstance(attestation, dict) and isinstance(attestation.get("payload"), dict) \
            else []
        if (not isinstance(hashes, list) or len(hashes) > 300
                or len(set(hashes)) != len(hashes)
                or any(not isinstance(h, str)
                       or not re.fullmatch("[a-f0-9]{64}", h) for h in hashes)):
            raise ReviewedReadyError("reviewed_hashes_invalid")
        html_sha = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
        evidence_sha = _json_sha(evidence_package)
        seo_sha = _json_sha(seo_context)
        expected = review_payload(
            site_key=site_key, campaign=campaign, product_key=product_key,
            site_url=site_url, article_url=article_url,
            article_title=article_title, primary_query=primary_query,
            angle=angle, html_sha256=html_sha, evidence_sha256=evidence_sha,
            seo_context_sha256=seo_sha, reviewed_text_hashes=hashes,
            wordpress_category=category_for_product(catalog, route, product_key),
        )
        if independent_review_key is not None or release_public_key is None:
            _check_review_signature(
                expected, attestation=attestation, key=independent_review_key,
            )
        else:
            verify_public_attestation(
                expected, attestation=attestation, signature=release_signature,
                public_key=release_public_key, require_receipt=True,
            )
        verified = verify_final_html_facts(
            html_content=html_content, evidence_package=evidence_package,
            product_key=product_key, product_title=title,
            used_evidence_ids=used_evidence_ids,
            trusted_reviewed_text_hashes=hashes, now=clock, policy=policy,
        )
        if verified["ready_publication_authorized"] is not False:
            raise ReviewedReadyError("draft_only_contract_violation")
        fingerprint = _fingerprint(product_key, primary_query, angle)
        # Only after all independent preflight gates: acquire the shared
        # refill lease. Cache and READY reserve are SQL atomic via C76.
        epoch = int(clock.timestamp() + monotonic() - started)
        if not state.acquire_lease(
            site_key=site_key, campaign=campaign, lease_name="refill",
            owner_nonce=owner_nonce, now_epoch=epoch,
        ):
            return _summary("LEASE_BUSY")
        try:
            if envelope is not None:
                previous = state.get_job(
                    site_key=site_key, campaign=campaign, fingerprint=fingerprint,
                )
                if previous is not None:
                    if previous["product_key"] != product_key:
                        raise ReviewedReadyError("ready_job_binding_conflict")
                    bound = (previous["status"] == "USED" or state.ready_has_fresh_evidence(
                        site_key=site_key, campaign=campaign, fingerprint=fingerprint, now_epoch=epoch))
                    if bound and (previous["html_sha256"], previous["evidence_sha256"]) != (html_sha, evidence_sha):
                        raise ReviewedReadyError("ready_job_binding_conflict")
                    if not bound:
                        previous = None
                # R2 first: a failed SQL commit can leave an unreferenced
                # object. Identical retries reuse it through conditional PUT.
                saved = envelope.save(
                    site_key=site_key, campaign=campaign, product_key=product_key,
                    content_html=html_content, attestation=attestation,
                    independent_review_key=independent_review_key,
                    release_signature=release_signature,
                    release_public_key=release_public_key,
                    embed_release_key=embed_release_key,
                )
                if previous is not None:
                    return _summary("READY_ALREADY_STAGED") | {
                        "fingerprint": fingerprint,
                        "html_sha256": saved["html_sha256"],
                        "job_status": previous["status"],
                    }
                epoch = int(clock.timestamp() + monotonic() - started)
            stored = state.cache_verified_evidence(
                site_key=site_key, campaign=campaign, owner_nonce=owner_nonce,
                product_key=product_key, product_title=title,
                package=evidence_package, now_epoch=epoch, policy=policy,
            )
            if not stored:
                cached = state.get_verified_evidence(
                    site_key=site_key, campaign=campaign,
                    product_key=product_key, product_title=title,
                    now_epoch=epoch, policy=policy,
                )
                if cached != evidence_package:
                    raise ReviewedReadyError("verified_evidence_cache_mismatch")
            epoch = int(clock.timestamp() + monotonic() - started)
            reserved = state.reserve_ready(
                site_key=site_key, campaign=campaign, owner_nonce=owner_nonce,
                fingerprint=fingerprint, product_key=product_key,
                html_sha256=html_sha, evidence_sha256=evidence_sha,
                now_epoch=epoch, min_ready=policy.min_ready,
                cooldown_days=policy.product_cooldown_days,
            )
            result = _summary("READY_RESERVED_FOR_DRAFT_REVIEW" if reserved
                              else "READY_NOT_RESERVED")
            if envelope is not None and reserved:
                result.update(fingerprint=fingerprint, html_sha256=html_sha,
                              job_status="READY")
            return result
        finally:
            if not state.release_lease(
                site_key=site_key, campaign=campaign,
                lease_name="refill", owner_nonce=owner_nonce,
            ):
                raise ReviewedReadyError("d1_lease_release_failed_closed")
    except (CommerceArticleError, FutureSEOError, UniversalReadyError,
            FinalFactGateError, D1SafeError, TypeError, ValueError, KeyError) as exc:
        if isinstance(exc, ReviewedReadyError):
            raise
        if isinstance(exc, D1SafeError) and str(exc) == "evidence_not_verified":
            raise ReviewedReadyError("reviewed_ready_d1_evidence_not_verified") from None
        # Details may carry product/title/content in upstream errors.
        raise ReviewedReadyError("reviewed_ready_gate_failed_closed") from None


def _summary(status: str) -> dict:
    return {
        "status": status, "requires_manual_live_approval": True,
        "live_publication_authorized": False, "cms_draft_calls": 0,
        "publication_calls": 0, "shopee_conversions": 0,
        "external_research_calls": 0,
    }
