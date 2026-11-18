"""V31 — Adaptadores que preparam payload de RASCUNHO sem chamar Blogger/WordPress.

Conteúdo editorial é fornecido por uma camada de escrita/revisão independente.
Não inventa avaliações, especificações, preços, experiências ou garantias.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from .catalog import Catalog, host_allowed
from .article_commerce import product_offer_html, related_articles_html, CommerceArticleError
from .editorial import EditorialError, fold, title_key
from .routing import sites


class DraftError(ValueError):
    """Falha de preparação com código estático, sem dados comerciais."""


@dataclass(frozen=True)
class DraftPayload:
    platform: str
    site_key: str
    brief_id: str
    title: str
    content_html: str
    meta: dict
    status: str = "draft"


def prepare_draft(catalog: Catalog, site_key: str, brief_id: str,
                  paragraphs: list[str],
                  related_posts: list[tuple[str,str]] | None = None,
                  blog_home_url: str | None = None) -> DraftPayload:
    """Somente dados estruturados para um futuro cliente autenticado.

    Requer aprovação explícita do briefing antes de preparar rascunho.
    Os parágrafos fornecidos são escapados: nada de HTML arbitrário.
    """
    site=sites().get(site_key)
    if site is None:
        raise DraftError("unknown_site")
    row=catalog.db.execute("""
        SELECT site_key,product_key,title,keyword,category,niche,status,slug
        FROM editorial_briefs WHERE brief_id=?
    """,(brief_id,)).fetchone()
    if row is None or row[0] != site_key:
        raise DraftError("unknown_brief")
    key, title, keyword, category, niche, status, article_slug = row[1:]
    if status != "APPROVED":
        raise DraftError("brief_not_approved")
    if fold(keyword) not in fold(title):
        raise DraftError("keyword_missing_from_title")
    if not catalog.for_conversion(key):
        raise DraftError("product_ineligible")
    if not isinstance(paragraphs,list) or len(paragraphs)<4:
        raise DraftError("body_not_ready")
    cleaned=[]
    for p in paragraphs:
        if not isinstance(p,str):
            raise DraftError("body_not_ready")
        p=re.sub(r"\s+"," ",p).strip()
        if len(p)<70 or len(p)>3000:
            raise DraftError("paragraph_length_invalid")
        cleaned.append(p)
    all_text=" ".join(cleaned)
    if len(all_text.split())<250:
        raise DraftError("body_too_short")
    if fold(keyword) not in fold(all_text):
        raise DraftError("seo_keyword_missing_from_body")
    # NUNCA inventar URL afiliada se não houve conversão/cadastro validado.
    campaign=site["campaign"]
    affiliate=catalog.cached_link(key,campaign)
    if not affiliate or not host_allowed(affiliate,allow_short=True):
        raise DraftError("affiliate_link_not_verified")
    body="".join("<p>"+html.escape(p,quote=True)+"</p>" for p in cleaned)
    try:
        commercial = product_offer_html(
            catalog, site_key=site_key, product_key=key, topic=keyword)
        related = related_articles_html(related_posts or [],
            blog_home_url=blog_home_url) if related_posts else ""
    except CommerceArticleError as exc:
        raise DraftError("verified_product_commerce_required") from exc
    output = body + commercial + related
    platform=site["platform"]
    if platform=="blogger":
        metadata={"kind":"blogger#post","blog":{"id":site["identifier"]},"title":title,
                  "content":output,"labels":[category,niche],"isDraft":True}
    elif platform=="wordpress":
        metadata={"title":title,"slug":article_slug,"content":output,
                  "status":"draft","meta":{"_v31_editorial_brief_id":brief_id}}
    else:
        raise DraftError("unsupported_platform")
    return DraftPayload(platform,site_key,brief_id,title,output,metadata)
