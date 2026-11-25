"""Factual verification and controlled rendering, outside the generator."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from secrets import token_hex
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener

from .article_commerce import _single_verified_offer, CommerceArticleError
from .catalog import Catalog
from .d1_http_runner import CloudflareD1HTTPRunner
from .d1_universal_ready import UniversalD1ReadyState
from .independent_review import _NoRedirect, _official_storage, decode_candidate, prepare_review_payload, read_candidate
from .private_ready_envelope import ImmutablePrivateReadyEnvelope
from .r2_private_ready_backend import R2PrivateReadyBackend
from .review_signatures import approval_receipt, configured_signing_keys, payload_digest, sign_release
from .reviewed_ready_promotion import stage_reviewed_ready
from .routing import sites
from .site_request_queue import (VERIFIER_PROFILES as PROFILE, load_requests,
                                 claim_conversion_attempt)
from .on_demand_conversion import OnDemandConversionError, convert_for_review
from .site_launch_plan import preview_site_launch
from .structured_review_source import catalog_gtin, gtin_facts
from .manufacturer_review import (ManufacturerEvidenceError, source_page_allowed,
                                  verify_manufacturer_markdown)
from .verified_supply import supply_profiles, route_allows_sku
from .universal_evidence_ready import _fingerprint

ANGLE = "guia de decisão com fatos verificados v1"
SHOPEE = {"shopee.com.br", "www.shopee.com.br", "s.shopee.com.br"}


class VerificationError(ValueError):
    pass


# Diagnóstico C146: rótulos estáticos, sem exceções, URL, parâmetros ou segredos.
# Só executado pelo CLI serial; não altera a política de aprovação de artigos.
SAFE_STAGES = frozenset({
    "boot", "registered_site", "cms_history", "r2_connect", "d1_connect",
    "draft_quota", "r2_catalog_restore", "catalog_open", "candidate_selection",
    "d1_job_check", "offer_affiliate", "offer_image", "affiliate_conversion", "external_research",
    "related_article", "article_render", "article_review", "ready_promotion",
    "complete",
})
_CURRENT_STAGE = "boot"


def _mark_stage(stage: str) -> None:
    global _CURRENT_STAGE
    if stage not in SAFE_STAGES:
        raise VerificationError("diagnostic_stage_untrusted")
    _CURRENT_STAGE = stage


def _safe_failure_stage() -> str:
    return _CURRENT_STAGE if _CURRENT_STAGE in SAFE_STAGES else "boot"


def utcnow():
    return datetime.now(timezone.utc)


def prose_hashes(content):
    "Digest substantive paragraphs independently of markup and punctuation."
    hashes = set()
    for paragraph in re.findall(r"<p\b[^>]*>(.*?)</p\s*>", content, flags=re.I | re.S):
        words = re.findall(r"\w+", extract_text(paragraph.encode("utf-8")))
        if len(words) >= 18:
            hashes.add(hashlib.sha256(" ".join(words).encode()).hexdigest())
    return hashes


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.words = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "template", "noscript") or (
            tag not in ("img", "br", "input", "meta", "link", "hr") and "hidden" in dict(attrs)
        ):
            self.hidden.append(tag)

    def handle_endtag(self, tag):
        if self.hidden and self.hidden[-1] == tag:
            self.hidden.pop()

    def handle_data(self, value):
        if not self.hidden:
            self.words.append(value)


def extract_text(raw):
    scanner = VisibleText()
    scanner.feed(raw.decode("utf-8", errors="replace"))
    scanner.close()
    return " ".join(" ".join(scanner.words).casefold().split())


def _url(url, hosts):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in hosts or parsed.username
            or parsed.password or parsed.port not in (None, 443) or parsed.fragment):
        raise VerificationError("untrusted_network_destination")
    return parsed


def _read(url, *, hosts, mime, limit=2_500_000, headers=None, data=None):
    _url(url, hosts)
    request = Request(url, data=data, headers={"User-Agent": "V31Editorial/1.0",
                                               **(headers or {})})
    with build_opener(_NoRedirect()).open(request, timeout=18) as response:
        if response.headers.get_content_type() not in mime:
            raise VerificationError("unexpected_media_type")
        raw = response.read(limit + 1)
    if not raw or len(raw) > limit:
        raise VerificationError("network_body_out_of_range")
    return raw


def verify_affiliate_target(url, sku):
    _, shop, item = sku.split(":")
    opener = build_opener(_NoRedirect())
    for _ in range(5):
        path = _url(url, SHOPEE).path
        if (re.fullmatch(fr"/(?:(?:universal-link/)?product|opaanlp)/{shop}/{item}/?", path)
                or re.search(fr"-i\.{shop}\.{item}/?$", path)):
            return
        if re.search(r"/(?:product|opaanlp)/\d+/\d+|[-.]i\.\d+\.\d+", path):
            raise VerificationError("affiliate_target_wrong_sku")
        try:
            with opener.open(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=12):
                break
        except HTTPError as error:
            with error:
                redirect = error.headers.get("Location")
                if error.code not in (301, 302, 303, 307, 308) or not redirect:
                    break
                url = urljoin(url, redirect)
    raise VerificationError("affiliate_target_unverified")


def verify_image(url):
    try:
        raw = _read(url, hosts={urlsplit(url).hostname},
                    mime={"image/jpeg", "image/png", "image/webp"})
    except HTTPError as error:
        error.close()
        raise VerificationError(f"image_http_{error.code}") from None
    except OSError:
        raise VerificationError("image_connection_failed") from None
    if not (raw.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n"))
            or raw.startswith(b"RIFF") and raw[8:12] == b"WEBP"):
        raise VerificationError("image_bytes_invalid")
    return hashlib.sha256(raw).hexdigest()


def scrape_source(url, token):
    return firecrawl("scrape", token, {"url": url, "formats": ["markdown"],
                                        "onlyMainContent": True, "maxAge": 0})


def firecrawl(path, token, payload):
    if not token:
        raise VerificationError("firecrawl_key_missing")
    raw = _read("https://api.firecrawl.dev/v2/" + path, hosts={"api.firecrawl.dev"},
                mime={"application/json"}, data=json.dumps(payload).encode(),
                headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    result = json.loads(raw)
    if result.get("success") is not True or not isinstance(result.get("data"), dict):
        raise VerificationError("firecrawl_unverified_response")
    return result["data"]


def checked_claims(profile, raw_text):
    visible_markdown = re.sub(r"!?\[([^\]]*)\]\([^\n)]*\)", r"\1", raw_text)
    text = " ".join(visible_markdown.replace("**", "").casefold().split())
    if not all(marker in text for marker in profile["identity"]):
        raise VerificationError("external_product_identity_unverified")
    claims = []
    for claim_type, pattern, claim_text in profile["facts"]:
        matches = {match.group() for match in re.finditer(pattern, text)}
        if not matches:
            raise VerificationError("external_fact_missing_" + claim_type)
        claims.append((claim_type, claim_text, min(matches, key=lambda x: (len(x), x))))
    if len(claims) < 2:
        raise VerificationError("independent_evidence_insufficient")
    return claims


def render_article(*, policy, profile, route, sku, title, image, affiliate, claims,
                   source_hash, image_hash, related, checked, search_hash):
    escaped = html.escape
    site_url = policy["home"]
    if route["platform"] == "wordpress":
        from .automatic_wordpress_drafts import _product_slug
        path = _product_slug(route["site_key"], sku) + "/"
    else:
        path = "guia-v31-" + sku.rsplit(":", 1)[-1] + ".html"
    source = profile["source_url"]
    evidence = [{"evidence_id": f"C81_AUTO_{i}", "identity_level": "EXACT_PRODUCT",
                 "product_key": sku, "source_kind": "external", "source_url": source,
                 "approved_host": urlsplit(source).hostname, "review_status": "AUTHORIZED",
                 "authorized": True, "checked_utc": checked, "claim_type": kind,
                 "claim_text": claim, "source_sha256": source_hash, "matched_excerpt": excerpt}
                for i, (kind, claim, excerpt) in enumerate(claims)]
    title_for_post = profile["name"] + ": o que conferir antes de comprar"
    package = {"product_key": sku, "product_title": title, "product_status": "VERIFIED",
               "verified_utc": checked, "sources": evidence, "image_sha256": image_hash}
    revision = payload_digest({"evidence": package, "search_sha256": search_hash})
    parts = [f'<article lang="pt-BR" data-v31-product-key="{escaped(sku)}" '
             f'data-v31-evidence-revision="{revision}">',
             "<h2>Confira a ficha técnica</h2>"]
    for fact in evidence:
        parts.append(f'<p><span data-v31-fact-id="{fact["evidence_id"]}">'
                     f'{escaped(fact["claim_text"])}</span></p>')
    for heading, paragraph in profile["advice"]:
        parts.append(f"<h2>{escaped(heading)}</h2><p>{escaped(paragraph)}</p>")
    if related:
        parts.append(f'<p>Veja também <a href="{escaped(related["url"])}">'
                     f'{escaped(related["title"])}</a>.</p>')
    parts.extend([
        f'<figure><img src="{escaped(image)}" alt="{escaped(profile["name"])} do anúncio"></figure>',
        '<p>Este artigo contém link de afiliado. Podemos receber comissão por compras elegíveis.</p>',
        f'<p>Confira <a href="{escaped(affiliate)}" rel="nofollow sponsored noopener">'
        f'{escaped(profile["name"])}</a> na oferta correspondente.</p>',
        f'<p><a href="{escaped(affiliate)}" rel="nofollow sponsored noopener">'
        'Ver produto na Shopee</a></p></article>',
    ])
    return {"site_key": route["site_key"], "product_key": sku, "site_url": site_url,
            "article_url": urljoin(site_url, path), "article_title": title_for_post,
            "angle": ANGLE, "intent": "buying_guide",
            "primary_query": profile["query"], "cluster_id": profile["cluster"],
            "meta_description": f'Compare {profile["name"]}, as medidas do ambiente e os critérios práticos antes de escolher a oferta.',
            "html_content": "\n".join(parts), "published_posts": [related] if related else [],
            "keyword_evidence": {"source": "serp_research", "query": profile["query"],
                                 "observed_utc": checked, "response_sha256": search_hash},
            "evidence_package": package,
            "used_evidence_ids": [fact["evidence_id"] for fact in evidence]}


def _research(*, state, tenant, cap, callback):
    lease = {"lease_name": "firecrawl", "owner_nonce": token_hex(16)}
    clock = lambda: int(utcnow().timestamp())
    if not state.acquire_lease(**tenant, **lease, now_epoch=clock()):
        raise VerificationError("research_lease_busy")
    def paid(kind, fn):
        if not state.claim_search_budget(**tenant, owner_nonce=lease["owner_nonce"],
                                         now_epoch=clock(), kind=kind, daily_cap=cap):
            raise VerificationError("research_budget_exhausted")
        try:
            return fn()
        except HTTPError as error:
            error.close()
            if error.code == 429:
                state.block_search_on_429(**tenant, owner_nonce=lease["owner_nonce"], now_epoch=clock())
            raise VerificationError(f"research_http_{error.code}") from None
        except OSError:
            raise VerificationError("research_connection_failed") from None
    try:
        return callback(paid)
    finally:
        if not state.release_lease(**tenant, **lease):
            raise VerificationError("research_lease_release_unverified")


def verified_related_post(policy, profile):
    if not profile.get("related"):
        return None
    url, anchor = profile["related"]
    hosts = {urlsplit(policy["home"]).hostname}
    _url(url, hosts)
    post_id = profile.get("related_wordpress_id")
    if post_id is not None:
        if type(post_id) is not int or post_id < 1:
            raise VerificationError("related_wordpress_id_invalid")
        endpoint = urljoin(policy["home"], f"wp-json/wp/v2/posts/{post_id}?_fields=id,status,link,title")
        item = json.loads(_read(endpoint, hosts=hosts, mime={"application/json"}))
        if (item.get("id") != post_id or item.get("status") != "publish"
                or item.get("link") != url
                or html.unescape(item.get("title", {}).get("rendered", "")) != anchor):
            raise VerificationError("related_public_article_unverified")
    else:
        page = _read(url, hosts=hosts, mime={"text/html"})
        if not set(profile["cluster"].split("-")) <= set(re.findall(r"\w+", extract_text(page))):
            raise VerificationError("related_public_article_unverified")
    return {"url": url, "title": anchor, "status": "publish", "cluster_id": profile["cluster"]}


def verify_offer(*, policy, profile, route, sku, catalog, state, token):
    title, image, affiliate = _single_verified_offer(catalog, site_key=route["site_key"],
                                                     product_key=sku, verified_site_route=route)
    if not all(marker in title.casefold() for marker in profile.get("catalog_identity", ())):
        raise VerificationError("catalog_product_identity_changed")
    _mark_stage("offer_affiliate")
    verify_affiliate_target(affiliate, sku)
    _mark_stage("offer_image")
    image_hash = verify_image(image)

    def fetch(paid):
        if "manufacturer_identity" in profile:
            identity = profile["manufacturer_identity"]
            search = paid("SEARCH", lambda: firecrawl("search", token, {
                "query": profile["query"], "limit": 8,
                "sources": [{"type": "web"}], "country": "BR",
            }))
            for hit in search.get("web", []):
                if not isinstance(hit, dict):
                    continue
                url = hit.get("url")
                if not source_page_allowed(url, identity):
                    continue
                source = paid("HTTP", lambda: scrape_source(url, token))
                try:
                    facts = verify_manufacturer_markdown(
                        identity=identity, catalog_title=title, source_url=url,
                        source_metadata=source.get("metadata"),
                        markdown=source.get("markdown"))
                except ManufacturerEvidenceError:
                    continue
                profile["source_url"] = url
                return (facts,
                        hashlib.sha256(source["markdown"].encode()).hexdigest(),
                        payload_digest(search))
            raise VerificationError("trusted_manufacturer_source_unavailable")
        if "gtin" in profile:
            gtin = profile["gtin"]
            hosts = set(policy.get("trusted_structured_hosts", ()))
            search = paid("SEARCH", lambda: firecrawl("search", token, {
                "query": gtin, "limit": 6, "sources": [{"type": "web"}], "country": "BR",
            }))
            for hit in search.get("web", []):
                if not isinstance(hit, dict) or not isinstance(hit.get("url"), str):
                    continue
                url = hit["url"]
                if urlsplit(url).hostname not in hosts:
                    continue
                try:
                    raw = paid("HTTP", lambda: _read(url, hosts=hosts, mime={"text/html"}))
                    facts = gtin_facts(raw, gtin)
                except OSError:
                    continue
                except ValueError as error:
                    if str(error) not in ("trusted_source_gtin_mismatch",
                                           "structured_facts_insufficient_or_conflicting"):
                        raise
                    continue
                profile["source_url"] = url
                return facts, hashlib.sha256(raw).hexdigest(), payload_digest(search)
            raise VerificationError("trusted_structured_source_unavailable")
        source = paid("HTTP", lambda: scrape_source(profile["source_url"], token))
        expected = urlsplit(profile["source_url"])
        meta = source.get("metadata", {})
        resolved = urlsplit(meta.get("url") or meta.get("sourceURL", ""))
        if (resolved.scheme, resolved.netloc, resolved.path) != (expected.scheme, expected.netloc, expected.path):
            raise VerificationError("external_source_redirect_unverified")
        markdown = source.get("markdown")
        if not isinstance(markdown, str):
            raise VerificationError("external_source_missing")
        claims = checked_claims(profile, markdown)
        search = paid("SEARCH", lambda: firecrawl("search", token, {
            "query": profile["query"], "limit": 4, "sources": [{"type": "web"}], "country": "BR",
        }))
        hits = search.get("web")
        terms = set(re.findall(r"\w+", profile["query"].casefold()))
        if not isinstance(hits, list) or not any(
            isinstance(hit, dict) and str(hit.get("url", "")).startswith("https://")
            and len(terms & set(re.findall(r"\w+", str(hit.get("title", "")).casefold()))) >= 2
            for hit in hits
        ):
            raise VerificationError("search_intent_unverified")
        return claims, hashlib.sha256(markdown.encode()).hexdigest(), payload_digest(search)

    _mark_stage("external_research")
    claims, source_hash, search_hash = _research(
        state=state, tenant={"site_key": route["site_key"], "campaign": route["campaign"]},
        cap=policy["daily_research_attempts"], callback=fetch)
    _mark_stage("related_article")
    related = verified_related_post(policy, profile)
    _mark_stage("article_render")
    return render_article(policy=policy, profile=profile, route=route, sku=sku, title=title,
                          image=image, affiliate=affiliate, claims=claims, source_hash=source_hash,
                          image_hash=image_hash, related=related,
                          checked=utcnow().isoformat(timespec="seconds"),
                          search_hash=search_hash)


def _selection(catalog, route, request, policy, sku):
    """Broaden approved supply beyond the 24-item editorial preview.

    Manual product profiles remain first, but newer products only acquire
    a reviewer when they have a valid GTIN or a known manufacturer/model.
    Neither path bypasses the exact affiliate campaign or the signed review.
    """
    yield from supply_profiles(catalog, route, policy, only_key=sku)


def recover_fresh_ready(*, state, envelope, catalog, route, policy, prior_keys,
                        prior_slugs, prior_prose, public_key_sha256, now_epoch):
    """Recover already approved work without research or conversion.
    
    Current commercial eligibility, exact media/link, signed content, D1
    evidence and CMS history still apply. The writer rechecks before POST.
    """
    tenant = {"site_key": route["site_key"], "campaign": route["campaign"]}
    for job in state.list_fresh_ready(**tenant, now_epoch=now_epoch):
        key = job["product_key"]
        if hashlib.sha256(key.encode()).hexdigest() in prior_keys:
            continue
        if route["platform"] == "wordpress":
            from .automatic_wordpress_drafts import _product_slug
            if hashlib.sha256(_product_slug(route["site_key"], key).encode()).hexdigest() in prior_slugs:
                continue
        if not route_allows_sku(catalog, route, key):
            continue
        try:
            _, image, affiliate = _single_verified_offer(
                catalog, site_key=route["site_key"], product_key=key, verified_site_route=route)
        except CommerceArticleError:
            continue
        stored = envelope.load(**tenant, html_sha256=job["html_sha256"],
                               release_public_key_sha256=public_key_sha256)
        review = stored["review"]
        if (review["product_key"] != key
                or review["evidence_sha256"] != job["evidence_sha256"]
                or review["site_url"] != policy["home"]
                or _fingerprint(key, review["primary_query"], review["angle"]) != job["fingerprint"]):
            raise VerificationError("recovered_ready_binding_mismatch")
        content = stored["html_content"]
        if (f'href="{html.escape(affiliate)}"' not in content
                or f'src="{html.escape(image)}"' not in content
                or len(prose_hashes(content) & prior_prose) >= 2):
            continue
        return {"site_key": route["site_key"], "fingerprint": job["fingerprint"],
                "public_key_sha256": public_key_sha256, "status": "READY"}
    return None


def run(*, site_key, history, digest=None, pilot=False, pilot_sku=None, probe=False):
    _mark_stage("registered_site")
    registry = json.loads(PROFILE.read_text(encoding="utf-8"))
    policy = registry.get(site_key)
    route = sites().get(site_key)
    request = next((item for item in load_requests() if item["site_key"] == site_key), None)
    if (not policy or not route or route["publish_enabled"] is not False or not request
            or route["platform"] == "wordpress" and policy["home"] != route["identifier"]):
        raise VerificationError("autonomous_site_not_enabled")
    _mark_stage("cms_history")
    if (history.get("site_key") != site_key or not isinstance(history.get("keys"), list)
            or not isinstance(history.get("slugs"), list)
            or not isinstance(history.get("prose"), list) or type(history.get("count")) is not int):
        raise VerificationError("authenticated_cms_history_required")
    if request["articles"] is not None and history["count"] >= request["articles"]:
        return {"site_key": site_key, "status": "NO_NEW_OFFER", "reason": "site_quota_reached"}
    prior_keys = set(history["keys"])
    prior_slugs = set(history["slugs"])
    prior_prose = set(history["prose"])
    _mark_stage("r2_connect")
    storage = _official_storage()
    sku = None
    if pilot:
        if pilot_sku != policy.get("pilot_sku") or pilot_sku not in policy["offers"] or digest:
            raise VerificationError("pilot_requires_registered_offer")
        sku = pilot_sku
    elif digest:
        hint = decode_candidate(read_candidate(storage, site_key=site_key, digest=digest), digest=digest)
        sku = hint["product_key"]

    _mark_stage("d1_connect")
    query = CloudflareD1HTTPRunner.from_environment(allow_mutations=True)
    state = UniversalD1ReadyState(query)
    envelope = ImmutablePrivateReadyEnvelope(backend=R2PrivateReadyBackend(storage))
    if not probe:
        private_key, hmac_key, public_key = configured_signing_keys(
            private_key=os.environ.get("V31_REVIEW_RELEASE_PRIVATE_KEY_HEX", ""),
            receipt_key=os.environ.get("V31_READY_REVIEW_HMAC_KEY", ""),
        )
        if public_key != os.environ.get("V31_REVIEW_RELEASE_PUBLIC_KEY_HEX"):
            raise VerificationError("independent_public_key_configuration_mismatch")
        public_key_sha256 = hashlib.sha256(bytes.fromhex(public_key)).hexdigest()
    tenant = {"site_key": site_key, "campaign": route["campaign"]}
    _mark_stage("draft_quota")
    cap_reached = (not probe and state.count_draft_attempts_today(
        **tenant, now_epoch=int(utcnow().timestamp())) >= policy["max_drafts_per_day"])
    with tempfile.TemporaryDirectory(prefix="v31-autonomous-verify-") as tmp:
        file = Path(tmp) / "catalog.sqlite3"
        _mark_stage("r2_catalog_restore")
        if not storage.restore_to(file):
            raise VerificationError("official_catalog_missing")
        _mark_stage("catalog_open")
        with Catalog(file) as catalog:
            # Resume signed work before ranking or spending any research quota.
            if not (pilot or probe or digest or cap_reached):
                _mark_stage("d1_job_check")
                recovered = recover_fresh_ready(
                    state=state, envelope=envelope, catalog=catalog, route=route, policy=policy,
                    prior_keys=prior_keys, prior_slugs=prior_slugs, prior_prose=prior_prose,
                    public_key_sha256=public_key_sha256, now_epoch=int(utcnow().timestamp()))
                if recovered is not None:
                    return recovered
            rejected = []
            _mark_stage("candidate_selection")
            # Cache primeiro. Após esgotar os candidatos já convertidos,
            # considerar UM SKU elegível sem link, durante o MESMO ciclo DRAFT.
            # Revisão factual, assinaturas e gates continuam obrigatórios.
            candidates = list(_selection(catalog, route, request, policy, sku))
            candidates.sort(key=lambda entry: catalog.cached_link(
                entry[0], route["campaign"]) is None)
            on_demand_attempted = False
            allow_on_demand = (os.environ.get("V31_ON_DEMAND_CONVERSION") == "true"
                               and not pilot and not probe and digest is None)
            for selected, profile in candidates:
                if route["platform"] == "wordpress":
                    from .automatic_wordpress_drafts import _product_slug
                    in_cms = hashlib.sha256(_product_slug(site_key, selected).encode()).hexdigest() in prior_slugs
                else:
                    in_cms = False
                if in_cms or hashlib.sha256(selected.encode()).hexdigest() in prior_keys:
                    if pilot:
                        return {"site_key": site_key, "status": "NO_NEW_OFFER",
                                "reason": "pilot_offer_already_present"}
                    continue
                fingerprint = _fingerprint(selected, profile["query"], ANGLE)
                _mark_stage("d1_job_check")
                existing = state.get_job(**tenant, fingerprint=fingerprint)
                if cap_reached and (existing is None or existing["status"] != "USED"):
                    continue
                if existing and not probe and (existing["status"] == "USED"
                        or state.ready_has_fresh_evidence(**tenant, fingerprint=fingerprint,
                                                          now_epoch=int(utcnow().timestamp()))):
                    # Regular READY recovery has already checked current scope,
                    # media, link and history. Never bypass a rejection here.
                    if existing["status"] == "READY" and not (pilot or digest):
                        continue
                    envelope.load(**tenant, html_sha256=existing["html_sha256"],
                                  release_public_key_sha256=public_key_sha256)
                    return {"site_key": site_key, "fingerprint": fingerprint,
                            "public_key_sha256": public_key_sha256,
                            "status": existing["status"]}
                if not catalog.cached_link(selected, route["campaign"]):
                    # Um job pré-existente SEM link verificável não autoriza
                    # outra mutação Shopee nem reenvio de conteúdo.
                    if existing is not None:
                        raise VerificationError("on_demand_existing_job_missing_cache")
                    if not allow_on_demand or cap_reached or on_demand_attempted:
                        continue
                    on_demand_attempted = True
                    _mark_stage("affiliate_conversion")
                    try:
                        outcome = convert_for_review(
                            catalog=catalog, storage=storage, route=route,
                            product_key=selected,
                            app_id=os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID", ""),
                            app_secret=os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET", ""),
                            reserve_attempt=lambda campaign, product_key: claim_conversion_attempt(
                                query, day_utc=utcnow().date().isoformat(),
                                campaign=campaign, product_key=product_key),
                            verification_path=Path(tmp) / "converted_cache_readback.sqlite3",
                        )
                    except OnDemandConversionError as error:
                        raise VerificationError(str(error)) from None
                    if outcome == "BUDGET_DENIED":
                        return {"site_key": site_key, "status": "NO_NEW_OFFER",
                                "reason": "conversion_daily_budget_exhausted"}
                    if outcome not in ("CONVERTED", "CACHED"):
                        raise VerificationError("on_demand_conversion_untrusted")
                _mark_stage("offer_affiliate")
                try:
                    article = verify_offer(policy=policy, profile=profile, route=route, sku=selected,
                                           catalog=catalog, state=state,
                                           token=os.environ.get("FIRECRAWL_API_KEY", ""))
                    if len(prose_hashes(article["html_content"]) & prior_prose) >= 2:
                        raise VerificationError("article_prose_reused")
                except VerificationError as error:
                    code = str(error)
                    if code == "research_budget_exhausted":
                        return {"site_key": site_key, "status": "NO_NEW_OFFER",
                                "reason": "research_budget_exhausted"}
                    if code not in {"catalog_product_identity_changed",
                                    "external_product_identity_unverified", "search_intent_unverified",
                                    "trusted_structured_source_unavailable", "affiliate_target_unverified",
                                    "article_prose_reused",
                                    "trusted_manufacturer_source_unavailable"} \
                            and not code.startswith("external_fact_missing_"):
                        raise
                    rejected.append(code)
                    if len(rejected) >= policy["daily_research_attempts"]:
                        return {"site_key": site_key, "status": "NO_NEW_OFFER",
                                "reason": "no_new_offer_with_trusted_source",
                                "candidates_with_source_rejected": len(rejected)}
                    continue
                else:
                    break
            else:
                if cap_reached:
                    return {"site_key": site_key, "status": "NO_NEW_OFFER",
                            "reason": "draft_daily_cap_reached"}
                if rejected:
                    return {"site_key": site_key, "status": "NO_NEW_OFFER",
                            "reason": "no_new_offer_with_trusted_source",
                            "candidates_with_source_rejected": len(rejected)}
                if sku is not None and not pilot:
                    raise VerificationError("product_has_no_trusted_source_profile")
                return {"site_key": site_key, "status": "NO_NEW_OFFER",
                        "reason": "no_new_offer_with_trusted_source"}
            now = utcnow()
            _mark_stage("article_review")
            try:
                payload = prepare_review_payload(article=article, catalog=catalog, now=now)
            except ValueError as error:
                raise VerificationError(str(error)) from None
            if probe:
                return {"site_key": site_key, "status": "VERIFIED_WITHOUT_SIGNATURE",
                        "facts": len(article["used_evidence_ids"])}
            candidate_sha = digest or payload_digest(article)
            receipt = approval_receipt(candidate_sha256=candidate_sha, payload_sha256=payload_digest(payload),
                                       key=hmac_key)
            signature = sign_release(receipt, private_key=private_key)
            _mark_stage("ready_promotion")
            try:
                result = stage_reviewed_ready(
                    **article, catalog=catalog, owner_nonce=token_hex(16), now=now,
                    state=state, envelope=envelope, independent_review_key=None, release_public_key=public_key,
                    embed_release_key=True,
                    attestation={"payload": payload, "candidate_sha256": candidate_sha, "signature": receipt["signature"]},
                    release_signature=signature,
                )
            except ValueError as error:
                raise VerificationError(str(error)) from None
    if result.get("job_status") not in ("READY", "USED"):
        raise VerificationError("ready_reservation_unverified")
    _mark_stage("complete")
    return {"site_key": site_key, "fingerprint": result["fingerprint"],
            "public_key_sha256": public_key_sha256,
            "status": result["job_status"]}


def main():
    _mark_stage("boot")
    parser = argparse.ArgumentParser(description="Verificar fontes e preparar artigo V31")
    parser.add_argument("--site-key", required=True)
    parser.add_argument("--digest")
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--pilot-sku")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--pilot", action="store_true")
    modes.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(run(site_key=args.site_key, digest=args.digest, pilot=args.pilot,
                             pilot_sku=args.pilot_sku, probe=args.probe,
                             history=json.loads(args.history.read_text(encoding="utf-8")))))
    except VerificationError as error:
        print(str(error))
        return 1
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        print("autonomous_verification_failed_closed:" + _safe_failure_stage())
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
