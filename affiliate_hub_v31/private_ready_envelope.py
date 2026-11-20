"""C78 — immutable private HTML envelope for a future V31 R2 adapter (SAFE).

The engine never calls Cloudflare, CMS or Firecrawl by itself. The supplied
backend implements atomic put_if_absent(key: str, bytes: bytes) -> bool and
get(key: str) -> bytes|None, and MUST use a private bucket with an actual
atomic conditional PUT (If-None-Match: *), not a GET-then-PUT race.

This module preserves exact reviewed bytes; it does not approve READY or LIVE.
C77 must independently revalidate catalogue, SEO, facts and reviewer signature
before D1 reservation. An unreferenced private envelope is never publishable.
"""
from __future__ import annotations

import hashlib
import json
import re

from .reviewed_ready_promotion import (
    ReviewedReadyError, _check_review_signature, review_payload,
)
from .routing import sites


class PrivateEnvelopeError(ValueError):
    """Only sanitized errors; never include HTML, URLs, tokens or object data."""


MAX_BYTES = 700_000
MAX_HTML_BYTES = 500_000
HEX = re.compile(r"[a-f0-9]{64}")
REQUIRED_FIELDS = frozenset({
    "version", "site_key", "campaign", "product_key",
    "site_url", "article_url", "article_title",
    "primary_query", "angle", "html_sha256", "evidence_sha256",
    "seo_context_sha256", "reviewed_text_hashes",
})


def _site(site_key: str, campaign: str) -> dict:
    if (not isinstance(site_key, str) or
            not re.fullmatch(r"[a-z0-9_]{3,50}", site_key) or
            not isinstance(campaign, str) or
            not re.fullmatch(r"[a-z0-9_-]{1,32}", campaign)):
        raise PrivateEnvelopeError("private_envelope_tenant_invalid")
    route = sites().get(site_key)
    if (not isinstance(route, dict) or route.get("site_key") != site_key
            or route.get("campaign") != campaign
            or route.get("publish_enabled") is not False
            or route.get("platform") not in ("blogger", "wordpress")):
        raise PrivateEnvelopeError("private_envelope_registered_route_required")
    return route


def object_key(site_key: str, campaign: str, html_sha256: str) -> str:
    _site(site_key, campaign)
    if not isinstance(html_sha256, str) or not HEX.fullmatch(html_sha256):
        raise PrivateEnvelopeError("private_envelope_sha_invalid")
    return (f"v31/private-ready/v1/{site_key}/{campaign}/"
            f"{html_sha256[:2]}/{html_sha256}.json")


def _attestation(attestation: dict, *, site_key: str, campaign: str,
                 product_key: str, content_html: str, key: bytes) -> tuple[str, dict]:
    if (not isinstance(attestation, dict) or
            not isinstance(attestation.get("payload"), dict)):
        raise PrivateEnvelopeError("private_envelope_review_required")
    reviewed = attestation["payload"]
    html_sha = hashlib.sha256(content_html.encode("utf-8")).hexdigest()
    if (set(reviewed) != REQUIRED_FIELDS or reviewed.get("version") != 1
            or reviewed.get("site_key") != site_key
            or reviewed.get("campaign") != campaign
            or reviewed.get("product_key") != product_key
            or reviewed.get("html_sha256") != html_sha
            or not isinstance(reviewed.get("reviewed_text_hashes"), list)
            or any(not isinstance(h, str) or not HEX.fullmatch(h)
                   for h in reviewed["reviewed_text_hashes"])
            or any(not isinstance(reviewed.get(field), str)
                   or not HEX.fullmatch(reviewed[field])
                   for field in ("evidence_sha256", "seo_context_sha256"))):
        raise PrivateEnvelopeError("private_envelope_review_binding_mismatch")
    if (reviewed["reviewed_text_hashes"]
            != sorted(set(reviewed["reviewed_text_hashes"]))):
        raise PrivateEnvelopeError("private_envelope_review_hashes_invalid")
    try:
        expected = review_payload(
            site_key=site_key, campaign=campaign, product_key=product_key,
            site_url=reviewed["site_url"], article_url=reviewed["article_url"],
            article_title=reviewed["article_title"],
            primary_query=reviewed["primary_query"], angle=reviewed["angle"],
            html_sha256=html_sha, evidence_sha256=reviewed["evidence_sha256"],
            seo_context_sha256=reviewed["seo_context_sha256"],
            reviewed_text_hashes=reviewed["reviewed_text_hashes"],
        )
        _check_review_signature(expected, attestation=attestation, key=key)
    except (ReviewedReadyError, TypeError, ValueError, KeyError):
        raise PrivateEnvelopeError("private_envelope_signature_invalid") from None
    return html_sha, reviewed


class ImmutablePrivateReadyEnvelope:
    """Inert adapter: no preconfigured R2 credentials, endpoint or bucket."""

    def __init__(self, *, backend):
        if not callable(getattr(backend, "get", None)) or not callable(
                getattr(backend, "put_if_absent", None)):
            raise PrivateEnvelopeError("conditional_private_backend_required")
        self.backend = backend

    def _get_bytes(self, key: str) -> bytes | None:
        try:
            existing = self.backend.get(key)
        except Exception:
            raise PrivateEnvelopeError("private_envelope_read_failed_closed") from None
        if existing is not None and (
                not isinstance(existing, bytes) or len(existing) > MAX_BYTES):
            raise PrivateEnvelopeError("private_envelope_untrusted_content")
        return existing

    def save(self, *, site_key: str, campaign: str, product_key: str,
             content_html: str, attestation: dict,
             independent_review_key: bytes) -> dict:
        _site(site_key, campaign)
        if (not isinstance(product_key, str)
                or not re.fullmatch(r"shopee:[0-9]+:[0-9]+", product_key)
                or not isinstance(content_html, str)
                or not 100 <= len(content_html) <= 120_000
                or len(content_html.encode("utf-8")) > MAX_HTML_BYTES):
            raise PrivateEnvelopeError("private_envelope_content_invalid")
        html_sha, reviewed = _attestation(
            attestation, site_key=site_key, campaign=campaign,
            product_key=product_key, content_html=content_html,
            key=independent_review_key,
        )
        objkey = object_key(site_key, campaign, html_sha)
        body = json.dumps({
            "schema": "v31-private-ready-envelope-1",
            "site_key": site_key, "campaign": campaign,
            "product_key": product_key, "html_sha256": html_sha,
            "content_html": content_html, "attestation": attestation,
        }, sort_keys=True, ensure_ascii=False,
            separators=(",", ":")).encode("utf-8")
        if len(body) > MAX_BYTES:
            raise PrivateEnvelopeError("private_envelope_too_large")
        try:
            created = self.backend.put_if_absent(objkey, body)
        except Exception:
            raise PrivateEnvelopeError("private_envelope_write_failed_closed") from None
        if type(created) is not bool:
            raise PrivateEnvelopeError("private_envelope_backend_cas_invalid")
        readback = self._get_bytes(objkey)
        if readback != body:
            raise PrivateEnvelopeError("private_envelope_readback_mismatch")
        # Existing object with identical bytes is idempotent. A collision or
        # changed editorial manifest under the same SHA is rejected.
        return {
            "status": "PRIVATE_ENVELOPE_CREATED" if created
                      else "PRIVATE_ENVELOPE_ALREADY_VALID",
            "html_sha256": html_sha, "object_key": objkey,
            "conditional_object_write_attempts": 1,
            "object_readback_attempts": 1,
            "cms_draft_calls": 0, "publication_calls": 0,
            "live_publication_authorized": False,
        }

    def load(self, *, site_key: str, campaign: str, html_sha256: str,
             independent_review_key: bytes) -> dict:
        objkey = object_key(site_key, campaign, html_sha256)
        body = self._get_bytes(objkey)
        if body is None:
            raise PrivateEnvelopeError("private_envelope_missing")
        try:
            data = json.loads(body)
            if (not isinstance(data, dict) or set(data) != {
                    "schema", "site_key", "campaign", "product_key",
                    "html_sha256", "content_html", "attestation"
                } or data["schema"] != "v31-private-ready-envelope-1"
                    or data["site_key"] != site_key
                    or data["campaign"] != campaign
                    or data["html_sha256"] != html_sha256
                    or not isinstance(data["content_html"], str)
                    or len(data["content_html"].encode("utf-8")) > MAX_HTML_BYTES):
                raise ValueError("bad envelope")
            confirmed_hash, _ = _attestation(
                data["attestation"], site_key=site_key, campaign=campaign,
                product_key=data["product_key"],
                content_html=data["content_html"], key=independent_review_key,
            )
            if confirmed_hash != html_sha256:
                raise ValueError("hash mismatch")
            # Reject attacker-controlled serialization with superfluous
            # whitespace/duplicate JSON keys: only canonical bytes are valid.
            canonical = json.dumps(
                data, sort_keys=True, ensure_ascii=False,
                separators=(",", ":")
            ).encode("utf-8")
            if canonical != body:
                raise ValueError("non-canonical bytes")
        except (ValueError, TypeError, KeyError, PrivateEnvelopeError):
            raise PrivateEnvelopeError("private_envelope_integrity_failed_closed") from None
        return {
            "status": "PRIVATE_ENVELOPE_VALIDATED",
            "html_content": data["content_html"],
            "html_sha256": html_sha256,
            "object_key": objkey,
            "live_publication_authorized": False,
        }
