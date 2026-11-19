"""C68 — SEO e links internos para PRÓXIMOS blogs, sem tocar blogs atuais.

Biblioteca offline/SAFE. Não acessa rede, API Shopee, WordPress, Blogger nem
GitHub e não executa publicação. Evidências externas devem ser fornecidas
explicitamente por quem cadastrou o site e gerou o brief.
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit


class FutureSEOError(ValueError):
    """Entrada ou domínio incorreto; nunca adivinhar origem de um blog."""


# As regras são editoriais, não limites oficiais do Google nem ranking garantido.
MIN_DESCRIPTION_RECOMMENDED = 70
MAX_DESCRIPTION_RECOMMENDED = 170
COMMERCIAL_INTENTS = frozenset((
    "buying_guide", "comparison", "alternatives", "use_case",
    "value", "features",
))
RESEARCH_SOURCES = frozenset((
    "search_console", "keyword_tool", "serp_research",
))
STOP = frozenset((
    "a", "as", "o", "os", "e", "de", "da", "das", "do", "dos", "em",
    "na", "nas", "no", "nos", "um", "uma", "uns", "umas", "para",
    "por", "com", "sem", "sobre", "que", "qual", "quais", "como",
    "onde", "antes", "ou", "se", "ao", "aos", "seu", "sua",
    "melhor", "melhores", "guia", "artigo", "dicas", "produto",
    "produtos", "comprar", "compra", "preco", "oferta", "ofertas",
))


def _terms(value: str) -> set[str]:
    folded = unicodedata.normalize("NFKD", value.casefold())
    ascii_text = "".join(x for x in folded if not unicodedata.combining(x))
    return {
        token for token in re.findall(r"[a-z0-9]+", ascii_text)
        if len(token) >= 3 and token not in STOP
    }


def _url(url: str) -> tuple[str, str] | None:
    """Canonical HTTPS absoluto; não aceitar queries, credenciais ou fragments."""
    if not isinstance(url, str) or len(url) > 2048:
        return None
    try:
        u = urlsplit(url)
        host = (u.hostname or "").lower().rstrip(".")
        if (u.scheme != "https" or not host or
                u.port not in (None, 443) or
                u.username or u.password or u.query or u.fragment or
                not u.path.startswith("/") or "\\" in url or
                not re.fullmatch(r"[a-z0-9.-]+", host)):
            return None
    except ValueError:
        return None
    return host, u.path.rstrip("/") or "/"


def _site_host(home_url: str) -> str:
    parsed = _url(home_url)
    if parsed is None or parsed[1] != "/":
        raise FutureSEOError("seo_site_https_home_required")
    return parsed[0]


def _valid_published_post(doc: dict, *, host: str) -> tuple[str, str] | None:
    if not isinstance(doc, dict):
        return None
    status = doc.get("status")
    if not isinstance(status, str) or status.casefold() not in ("publish", "live"):
        return None
    title, url = doc.get("title"), doc.get("url")
    if not isinstance(title, str) or len(title.strip()) < 10:
        return None
    parsed = _url(url)
    if parsed is None or parsed[0] != host or parsed[1] == "/":
        return None
    return title.strip(), url


def plan_internal_links(
    *, site_url: str, current_url: str, primary_query: str,
    published_posts: list[dict], cluster_id: str = "",
    limit: int = 3,
) -> dict:
    """Links apenas do mesmo domínio e PUBLICADOS; não completar lista com lixo.

    Estágios de site novo sem posts são explicitamente declarados. Uma
    futura atualização do post pilar deve ligar de volta aos satélites.
    """
    host = _site_host(site_url)
    current = _url(current_url)
    if not current or current[0] != host or current[1] == "/":
        raise FutureSEOError("seo_current_url_site_mismatch")
    if not isinstance(primary_query, str) or not _terms(primary_query):
        raise FutureSEOError("seo_query_required")
    if not isinstance(published_posts, list) or len(published_posts) > 10000:
        raise FutureSEOError("seo_published_history_invalid")
    if not isinstance(cluster_id, str) or len(cluster_id) > 80:
        raise FutureSEOError("seo_cluster_id_invalid")
    if type(limit) is not int or not 1 <= limit <= 6:
        raise FutureSEOError("seo_link_limit_invalid")

    query_tokens = _terms(primary_query)
    ranked: list[tuple[int, int, str, str, str]] = []
    seen = set()
    verified = 0
    for index, post in enumerate(published_posts):
        valid = _valid_published_post(post, host=host)
        if valid is None:
            continue
        title, link = valid
        parsed = _url(link)
        assert parsed is not None
        key = (parsed[0], parsed[1])
        if key == current or key in seen:
            continue
        seen.add(key)
        verified += 1
        title_tokens = _terms(title)
        post_terms = title_tokens | _terms(
            " ".join(post.get("keywords", []))
            if isinstance(post.get("keywords"), list)
            and all(isinstance(x, str) for x in post["keywords"])
            else ""
        )
        matching = query_tokens & post_terms
        related_cluster = bool(
            cluster_id and post.get("cluster_id") == cluster_id
        )
        if not matching and not related_cluster:
            continue
        score = 3 * len(matching) + (4 if related_cluster else 0)
        is_pillar = post.get("role") == "pillar" and related_cluster
        if is_pillar:
            score += 10
        ranked.append((score, index, title, link,
                       "pillar" if is_pillar else "related"))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    selected = [
        {"title": title, "anchor_text": title, "url": link,
         "role": role, "relevance_score": score}
        for score, _, title, link, role in ranked[:limit]
    ]
    status = (
        "COLD_START_NO_PUBLISHED_ARTICLES" if verified == 0
        else "NO_RELEVANT_INTERNAL_POSTS" if not ranked
        else "RELATED_POSTS_VERIFIED"
    )
    return {
        "status": status, "links": selected,
        "verified_site_host": host,
        "verified_published_posts": verified,
        "related_published_posts": len(ranked),
        "recommended_max_links": limit,
        "relink_after_new_pillar_or_satellites": len(selected) < limit,
        "publication_calls": 0, "network_calls": 0,
    }


def render_related_links(plan: dict) -> str:
    """Renderiza SOMENTE os links verificados pelo planejador acima."""
    if not isinstance(plan, dict) or not isinstance(plan.get("links"), list):
        raise FutureSEOError("seo_link_plan_invalid")
    entries = plan["links"]
    host = plan.get("verified_site_host")
    if not isinstance(host, str) or not re.fullmatch(r"[a-z0-9.-]+", host):
        raise FutureSEOError("seo_link_plan_site_missing")
    if not entries:
        return ""
    out = []
    for entry in entries:
        # Validação redundante de formato, não confiar em HTML de terceiros.
        if (not isinstance(entry, dict) or
                not isinstance(entry.get("anchor_text"), str) or
                len(entry["anchor_text"].strip()) < 10 or
                _url(entry.get("url")) is None or
                _url(entry["url"])[0] != host):
            raise FutureSEOError("seo_link_plan_invalid")
        url = html.escape(entry["url"], quote=True)
        anchor = html.escape(entry["anchor_text"], quote=True)
        out.append('<li><a href="' + url + '">' + anchor + '</a></li>')
    return ('<aside class="v31-seo-related"><h2>Leia também</h2>'
            '<ul>' + "".join(out) + '</ul></aside>')


class _Signals(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h2 = 0
        self.h1 = 0
        self.images: list[dict] = []
        self.links: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "h2":
            self.h2 += 1
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img":
            self.images.append(data)
        elif tag == "a":
            self.links.append(data)


def _research_verified(evidence: dict | None, query: str) -> bool:
    """Fonte real + data válida: não inventar volume ou concorrência."""
    if not isinstance(evidence, dict):
        return False
    if (evidence.get("source") not in RESEARCH_SOURCES or
            evidence.get("query") != query or
            not isinstance(evidence.get("observed_utc"), str)):
        return False
    try:
        observed = datetime.fromisoformat(
            evidence["observed_utc"].replace("Z", "+00:00")
        )
        if (observed.tzinfo is None or
                observed.utcoffset() != timezone.utc.utcoffset(observed) or
                observed > datetime.now(timezone.utc)):
            return False
    except ValueError:
        return False
    return True


def audit_future_article(
    *, site_url: str, article_url: str, title: str,
    meta_description: str, primary_query: str,
    intent: str, html_content: str, published_posts: list[dict],
    keyword_evidence: dict | None = None, cluster_id: str = "",
) -> dict:
    """Gate técnico offline PRÓXIMOS blogs, sem prometer resultados SEO.

    O auditor não consegue medir SERPs/Core Web Vitals, verificar Search
    Console, estoque Shopee, comissões ou schema publicado pelo tema.
    Esses itens permanecem UNKNOWN até fontes reais/URL pública.
    """
    host = _site_host(site_url)
    parsed = _url(article_url)
    if not parsed or parsed[0] != host or parsed[1] == "/":
        raise FutureSEOError("seo_article_site_mismatch")
    if not all(isinstance(v, str) for v in (
        title, meta_description, primary_query, intent, html_content
    )):
        raise FutureSEOError("seo_article_fields_invalid")
    if not isinstance(published_posts, list):
        raise FutureSEOError("seo_published_history_invalid")
    if intent not in COMMERCIAL_INTENTS:
        raise FutureSEOError("seo_commercial_intent_required")
    signals = _Signals()
    signals.feed(html_content)

    blockers = []
    warnings = []
    if not 25 <= len(title.strip()) <= 85:
        warnings.append("TITLE_LENGTH_EDITORIAL_REVIEW")
    if not MIN_DESCRIPTION_RECOMMENDED <= len(meta_description.strip()) <= MAX_DESCRIPTION_RECOMMENDED:
        warnings.append("META_DESCRIPTION_LENGTH_EDITORIAL_REVIEW")
    if not _terms(primary_query):
        blockers.append("PRIMARY_QUERY_MISSING")
    if not _research_verified(keyword_evidence, primary_query):
        blockers.append("SEARCH_INTENT_RESEARCH_EVIDENCE_REQUIRED")
    if signals.h2 < 3:
        blockers.append("STRUCTURED_DECISION_CONTENT_REQUIRED")
    if signals.h1 > 1:
        blockers.append("MULTIPLE_ARTICLE_H1_REVIEW")
    if not signals.images:
        blockers.append("REAL_PRODUCT_IMAGE_REQUIRED")
    for image in signals.images:
        alt = image.get("alt")
        if not isinstance(alt, str) or len(alt.strip()) < 10:
            blockers.append("IMAGE_DESCRIPTIVE_ALT_REQUIRED")
            break
    shopee = [x for x in signals.links
              if isinstance(x.get("href"), str)
              and urlsplit(x["href"]).hostname == "s.shopee.com.br"]
    if not shopee:
        blockers.append("SHOPEE_AFFILIATE_LINK_REQUIRED")
    if any("sponsored" not in (x.get("rel") or "").casefold().split()
           for x in shopee):
        blockers.append("AFFILIATE_SPONSORED_REL_REQUIRED")
    if "link de afiliado" not in html_content.casefold() and "comiss" not in html_content.casefold():
        blockers.append("AFFILIATE_DISCLOSURE_REQUIRED")
    if re.search(r'"@type"\s*:\s*"(?:Review|AggregateRating)"', html_content, re.I):
        blockers.append("UNVERIFIED_REVIEW_SCHEMA_FORBIDDEN")
    if re.search(r'"@type"\s*:\s*"Product"', html_content, re.I):
        warnings.append("PRODUCT_SCHEMA_NEEDS_INDEPENDENT_FACT_CHECK")

    link_plan = plan_internal_links(
        site_url=site_url, current_url=article_url,
        primary_query=primary_query, published_posts=published_posts,
        cluster_id=cluster_id,
    )
    eligible_urls = {_url(x["url"]) for x in published_posts
                     if _valid_published_post(x, host=host)}
    for link in signals.links:
        href = link.get("href")
        if not isinstance(href, str):
            continue
        link_parsed = _url(href)
        if link_parsed and link_parsed[0] == host and link_parsed[1] != "/":
            if link_parsed not in eligible_urls:
                blockers.append("INTERNAL_LINK_NOT_VERIFIED_AS_PUBLISHED")
                break
    if link_plan["links"] and not any(
        _url(link.get("href")) in {_url(x["url"]) for x in link_plan["links"]}
        for link in signals.links if isinstance(link.get("href"), str)
    ):
        warnings.append("RELATED_CLUSTER_LINKS_NOT_INSERTED")
    if not link_plan["links"]:
        warnings.append("INTERNAL_LINK_COLD_START_OR_NO_RELEVANT_POSTS")

    return {
        "status": "BLOCKED_SAFE" if blockers else "READY_FOR_EDITORIAL_SAFE_REVIEW",
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "intent": intent,
        "keyword_source_verified": _research_verified(keyword_evidence, primary_query),
        "internal_link_plan": link_plan,
        "technical_not_measured": [
            "GOOGLE_SEARCH_CONSOLE_VERIFIED_DOMAIN",
            "SITEMAP_ROBOTS_AND_CANONICAL_REMOTE_AUDIT",
            "MOBILE_CORE_WEB_VITALS_LCP_INP_CLS",
            "IMAGE_FILE_BYTES_AND_RENDERED_LCP",
            "CMS_OR_THEME_SCHEMA_AND_META_RENDERED",
            "LIVE_SHOPEE_COMMISSION_STOCK_AND_OFFER",
            "CATALOG_PRODUCT_IMAGE_SKU_MATCH",
        ],
        "manual_quality_review_required": True,
        "publication_calls": 0,
        "network_calls": 0,
    }


def main() -> int:
    """Relatório offline redigido a partir de um JSON local sem Secrets."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="V31 SEO novos blogs — SAFE offline")
    parser.add_argument("--input-json", required=True)
    args = parser.parse_args()
    input_path = Path(args.input_json)
    if not input_path.is_file() or input_path.is_symlink():
        parser.error("seo_input_file_missing")
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        parser.error("seo_payload_invalid")
    try:
        report = audit_future_article(**payload)
    except (FutureSEOError, TypeError) as exc:
        parser.error(type(exc).__name__ + "_blocked")
    # Não emitir HTML/credenciais/links ao log; apenas status e regras.
    print(json.dumps({k: v for k, v in report.items()
                      if k != "internal_link_plan"}, ensure_ascii=False))
    return 0 if report["status"] != "BLOCKED_SAFE" else 3


if __name__ == "__main__":
    raise SystemExit(main())
