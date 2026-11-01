#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "blogger_policy_guard.json"


class PolicyGuardError(RuntimeError):
    pass


def _norm(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def load_policy(path: str | Path = DEFAULT_CONFIG) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if int(doc.get("schemaVersion") or 0) != 1:
        raise PolicyGuardError("blogger_policy_guard: schemaVersion inválido.")
    return doc


def _host(url: str) -> str:
    try:
        return (urlparse(str(url or "")).hostname or "").lower()
    except Exception:
        return ""


def _host_allowed(host: str, allowed: list[str]) -> bool:
    return any(host == x or host.endswith("." + x) for x in allowed)


def product_policy_check(product: dict, policy: dict | None = None) -> dict:
    policy = policy or load_policy()
    title = str(product.get("productName") or product.get("title") or "").strip()
    normalized = _norm(title)
    reasons: list[str] = []

    if not title:
        reasons.append("missing_product_name")

    for phrase in policy.get("regulatedProductPhrases") or []:
        if _norm(phrase) in normalized:
            reasons.append(f"regulated_product:{phrase}")
            break

    offer = str(product.get("offerLink") or product.get("affiliateUrl") or "").strip()
    if not offer.startswith("https://"):
        reasons.append("affiliate_url_not_https")
    else:
        host = _host(offer)
        if not _host_allowed(host, list(policy.get("allowedAffiliateHosts") or [])):
            reasons.append(f"affiliate_host_not_allowed:{host}")

    image = str(product.get("imageUrl") or "").strip()
    if not image.startswith("https://"):
        reasons.append("image_url_not_https")
    else:
        host = _host(image)
        allowed_fragments = [str(x).lower() for x in (policy.get("allowedShopeeImageHostFragments") or [])]
        if allowed_fragments and not any(fragment in host for fragment in allowed_fragments):
            reasons.append(f"image_host_not_shopee_source:{host}")

    return {"accepted": not reasons, "reasons": reasons, "productName": title}


def require_product_allowed(product: dict, policy: dict | None = None) -> None:
    result = product_policy_check(product, policy)
    if not result["accepted"]:
        raise PolicyGuardError("Produto bloqueado pelo BLOGGER_POLICY_GUARD: " + ", ".join(result["reasons"]))


def generated_copy_check(text: str, policy: dict | None = None) -> dict:
    policy = policy or load_policy()
    normalized = _norm(text)
    reasons: list[str] = []
    for phrase in policy.get("deceptiveGeneratedCopyPhrases") or []:
        if _norm(phrase) in normalized:
            reasons.append(f"deceptive_generated_copy:{phrase}")
    return {"accepted": not reasons, "reasons": reasons}


def cookie_safety_check(html: str, policy: dict | None = None) -> dict:
    policy = policy or load_policy()
    raw = str(html or "")
    normalized = raw.lower()
    reasons: list[str] = []

    for pattern in policy.get("cookieDisablePatterns") or []:
        if str(pattern).lower() in normalized:
            reasons.append(f"native_blogger_cookie_notice_disabled:{pattern}")

    # Bloqueia apenas padrões explícitos de ocultação do aviso nativo.
    for selector in policy.get("cookieHideSelectors") or []:
        selector_low = str(selector).lower()
        if selector_low in normalized:
            # Procura display:none em uma janela curta após o seletor.
            pos = normalized.find(selector_low)
            window = normalized[pos:pos + 500]
            if "display:none" in window or "display: none" in window:
                reasons.append(f"native_blogger_cookie_notice_hidden:{selector}")

    return {"accepted": not reasons, "reasons": reasons}


def store_html_policy_check(html: str, expected_products: int = 20, expected_hero: int = 12, policy: dict | None = None) -> dict:
    policy = policy or load_policy()
    raw = str(html or "")
    normalized = _norm(raw)
    reasons: list[str] = []

    if expected_products >= 0 and raw.count("data-item-id=") != expected_products:
        reasons.append(f"unexpected_product_count:{raw.count('data-item-id=')}")
    if expected_hero >= 0 and raw.count("data-hero-item-id=") != expected_hero:
        reasons.append(f"unexpected_hero_count:{raw.count('data-hero-item-id=')}")

    disclosures = [_norm(x) for x in (policy.get("affiliateDisclosureRequiredAny") or [])]
    if disclosures and not any(x in normalized for x in disclosures):
        reasons.append("affiliate_disclosure_missing")

    cookie = cookie_safety_check(raw, policy)
    reasons.extend(cookie["reasons"])

    # Verifica os links afiliados que aparecem em cards da Loja.
    href_pattern = re.compile(r'<a\b[^>]*class="[^"]*bls-(?:product|product-cta|hero)[^"]*"[^>]*>', re.I)
    for tag in href_pattern.findall(raw):
        href = re.search(r'href="([^"]+)"', tag, re.I)
        if not href:
            continue
        host = _host(href.group(1))
        if not _host_allowed(host, list(policy.get("allowedAffiliateHosts") or [])):
            reasons.append(f"store_affiliate_host_not_allowed:{host}")
        rel = re.search(r'rel="([^"]+)"', tag, re.I)
        rel_tokens = set((rel.group(1).lower().split() if rel else []))
        required_rel = {"nofollow", "sponsored", "noopener"}
        if not required_rel.issubset(rel_tokens):
            reasons.append("affiliate_rel_incomplete")

    return {"accepted": not reasons, "reasons": sorted(set(reasons))}


def require_store_html_allowed(html: str, expected_products: int = 20, expected_hero: int = 12, policy: dict | None = None) -> None:
    result = store_html_policy_check(html, expected_products, expected_hero, policy)
    if not result["accepted"]:
        raise PolicyGuardError("BLOGGER_POLICY_GUARD rejeitou a Loja: " + ", ".join(result["reasons"]))
