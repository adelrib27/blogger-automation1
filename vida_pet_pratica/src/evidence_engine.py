import hashlib
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

FIRECRAWL_ENDPOINT = os.getenv("FIRECRAWL_SEARCH_ENDPOINT", "https://api.firecrawl.dev/v2/search").strip()


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def tokens(text: str) -> set[str]:
    stop = {"para", "com", "sem", "por", "uma", "um", "de", "da", "do", "das", "dos", "e", "em", "a", "o", "as", "os", "no", "na", "kit", "novo", "nova"}
    return {t for t in normalize(text).split() if len(t) >= 3 and t not in stop}


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def model_tokens(product_name: str) -> list[str]:
    found = []
    for token in re.findall(r"\b[A-Za-z0-9._-]{3,}\b", str(product_name or "")):
        compact = re.sub(r"[^A-Za-z0-9]", "", token)
        if len(compact) >= 3 and any(c.isalpha() for c in compact) and any(c.isdigit() for c in compact):
            found.append(compact.lower())
    return sorted(set(found))


def _safe_excerpt(result: dict, max_chars: int = 2400) -> str:
    parts = []
    for key in ("description", "snippet", "markdown", "answer"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    metadata = result.get("metadata") or {}
    if isinstance(metadata, dict):
        for key in ("description", "og:description", "ogDescription"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
    unique, seen = [], set()
    for part in parts:
        clean = re.sub(r"\s+", " ", part).strip()
        if clean and clean not in seen:
            seen.add(clean)
            unique.append(clean)
    return "\n".join(unique)[:max_chars]


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _exact_shopee_match(url: str, item_id: str) -> bool:
    low = str(url or "").lower()
    return bool(item_id and "shopee.com.br" in low and item_id in low)


def _matched_model(result: dict, product_name: str, models: list[str]) -> bool:
    if not models:
        return False
    haystack = normalize(" ".join([str(result.get("title") or ""), str(result.get("description") or ""), str(result.get("url") or ""), _safe_excerpt(result, 1200)]))
    return all(normalize(m) in haystack for m in models) and similarity(product_name, haystack) >= 0.35


def _firecrawl_retry_after(detail: str, headers=None) -> float:
    values = []
    if headers:
        raw = headers.get("Retry-After") or headers.get("retry-after")
        if raw:
            try:
                values.append(float(raw))
            except Exception:
                pass
    try:
        parsed = json.loads(detail)
        raw = parsed.get("retry_after_seconds")
        if raw is not None:
            values.append(float(raw))
    except Exception:
        pass
    match = re.search(r"retry after\s+([0-9.]+)s", detail, flags=re.I)
    if match:
        try:
            values.append(float(match.group(1)))
        except Exception:
            pass
    return max(values or [3.0])


def firecrawl_search(query: str, limit: int = 8) -> tuple[list[dict], dict]:
    api_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    payload = {
        "query": query,
        "limit": max(1, min(int(limit), 20)),
        "sources": ["web"],
        "scrapeOptions": {"formats": ["markdown"], "onlyMainContent": True},
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "VidaPetPratica-EvidenceEngine/1.2"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    doc = None
    last_error = None
    for attempt in range(1, 5):
        request = urllib.request.Request(FIRECRAWL_ENDPOINT, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                doc = json.loads(response.read().decode("utf-8", "replace"))
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:1600]
            last_error = f"Firecrawl HTTP {exc.code}: {detail}"
            if exc.code == 429 and attempt < 4:
                wait = min(15.0, max(2.0, _firecrawl_retry_after(detail, exc.headers) + 1.0))
                time.sleep(wait)
                continue
            raise RuntimeError(last_error) from exc
        except Exception as exc:
            last_error = f"Firecrawl indisponível: {exc}"
            if attempt < 3:
                time.sleep(3.0 * attempt)
                continue
            raise RuntimeError(last_error) from exc

    if doc is None:
        raise RuntimeError(last_error or "Firecrawl sem resposta após retries")

    data = doc.get("data") or {}
    web = data.get("web") or doc.get("web") or []
    if not isinstance(web, list):
        web = []
    return web, {
        "endpoint": FIRECRAWL_ENDPOINT,
        "auth_mode": "API_KEY" if api_key else "KEYLESS_LAB",
        "search_id": doc.get("id"),
        "credits_used": doc.get("creditsUsed"),
        "query": query,
    }


@dataclass
class EvidenceSource:
    evidence_id: str
    identity_level: str
    source_url: str
    source_domain: str
    source_title: str
    support_text: str
    allowed_in_article: bool
    confidence: float
    reason: str


def build_evidence_package(item: dict, max_results: int = 8, min_external_authorized_sources: int = 1) -> dict:
    item_id = str(item.get("itemId") or "").strip()
    product_name = re.sub(r"\s+", " ", str(item.get("productName") or "")).strip()
    if not item_id or not product_name:
        return {"status": "REJECTED_EVIDENCE", "reasons": ["missing_item_identity"], "product": {"itemId": item_id, "productName": product_name}, "sources": []}

    search_runs = []
    merged_results = []
    seen_urls = set()
    for query in (f'"{product_name}"', f'"{item_id}" site:shopee.com.br'):
        results, meta = firecrawl_search(query, limit=max_results)
        search_runs.append(meta)
        for result in results:
            url = str(result.get("url") or "").strip()
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged_results.append(result)
        if any(_exact_shopee_match(str(r.get("url") or ""), item_id) for r in merged_results):
            break

    models = model_tokens(product_name)
    sources = [EvidenceSource(
        evidence_id="EV-SHOPEE-API-" + item_id,
        identity_level="EXACT_PRODUCT",
        source_url=str(item.get("productLink") or item.get("offerLink") or ""),
        source_domain="open-api.affiliate.shopee.com.br",
        source_title=product_name,
        support_text=product_name,
        allowed_in_article=True,
        confidence=1.0,
        reason="Shopee Affiliate API returned this exact itemId and productName",
    )]

    for index, result in enumerate(merged_results, start=1):
        url = str(result.get("url") or "").strip()
        title = re.sub(r"\s+", " ", str(result.get("title") or "")).strip()
        excerpt = _safe_excerpt(result) or title
        identity, allowed, confidence = "SIMILAR_PRODUCT", False, 0.30
        reason = "Search result is context only; exact identity not proven"
        if _exact_shopee_match(url, item_id):
            identity, allowed, confidence = "EXACT_PRODUCT", True, 1.0
            reason = "Shopee URL contains the exact itemId"
        elif _matched_model(result, product_name, models):
            identity, allowed, confidence = "MATCHED_MODEL", True, 0.85
            reason = "Distinct model token(s) and product similarity matched"
        key = hashlib.sha256(f"{item_id}|{url}|{index}".encode("utf-8")).hexdigest()[:12]
        sources.append(EvidenceSource(
            evidence_id=f"EV-WEB-{key}", identity_level=identity, source_url=url, source_domain=_domain(url),
            source_title=title, support_text=excerpt, allowed_in_article=allowed, confidence=confidence, reason=reason,
        ))

    external_authorized = [s for s in sources if s.source_domain != "open-api.affiliate.shopee.com.br" and s.allowed_in_article and s.support_text]
    reasons = []
    if len(external_authorized) < min_external_authorized_sources:
        reasons.append(f"external_authorized_sources:{len(external_authorized)}<{min_external_authorized_sources}")

    return {
        "status": "VERIFIED" if not reasons else "REJECTED_EVIDENCE",
        "version": "EVIDENCE_ENGINE_V1_2",
        "verified_at": int(time.time()),
        "product": {
            "itemId": item_id, "productName": product_name, "shopName": item.get("shopName"),
            "productLink": item.get("productLink"), "offerLink": item.get("offerLink"),
            "intentMatchedKeywords": item.get("intentMatchedKeywords") or item.get("keywords") or [],
            "categories": item.get("categories") or [], "modelTokens": models,
        },
        "search_runs": search_runs,
        "rules": {
            "similar_product_specs_authorized": False,
            "exact_product_authorized": True,
            "matched_model_authorized_only_with_distinct_model_tokens": True,
            "min_external_authorized_sources": min_external_authorized_sources,
            "rate_limit_retry_enabled": True,
        },
        "authorized_evidence_ids": [s.evidence_id for s in sources if s.allowed_in_article and s.support_text],
        "external_authorized_evidence_ids": [s.evidence_id for s in external_authorized],
        "conflicts": [], "reasons": reasons, "sources": [asdict(s) for s in sources],
    }
