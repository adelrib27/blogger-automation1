"""C41 — receber envelope universal privado e preparar RASCUNHO Blogger/WordPress.

Requer aprovação editorial explícita do briefing e corpo original de um
gerador confiável. Nunca gera texto comercial do nada, não posta, não cria
blog, nem usa link de outra campanha. Reconfere os dados no catálogo R2.
"""
from __future__ import annotations

import hashlib
import html
import re

from .catalog import Catalog,host_allowed
from .article_commerce import (CommerceArticleError, product_offer_html, related_articles_html)
from .draft_adapter import DraftPayload
from .editorial import fold
from .routing import sites


class UniversalDraftError(ValueError):
    pass


def prepare_universal_draft(
    catalog:Catalog, *, site_key:str, envelope:dict,
    product_key:str, paragraphs:list[str], approved:bool=False,
    related_posts:list[tuple[str,str]]|None=None,
    blog_home_url:str|None=None,
)->DraftPayload:
    if approved is not True:
        raise UniversalDraftError("human_editorial_approval_required")
    route=sites().get(site_key)
    if route is None or route.get("publish_enabled") is not False:
        raise UniversalDraftError("real_site_required")
    if (not isinstance(envelope,dict) or
        envelope.get("site_key")!=site_key or
        envelope.get("campaign")!=route["campaign"] or
        envelope.get("platform")!=route["platform"] or
        envelope.get("status")!="REVIEW_REQUIRED" or
        envelope.get("publication_allowed") is not False or
        not isinstance(envelope.get("jobs"),list)):
        raise UniversalDraftError("untrusted_or_wrong_campaign_envelope")
    matches=[job for job in envelope["jobs"]
             if isinstance(job,dict) and job.get("product_key")==product_key]
    if len(matches)!=1:
        raise UniversalDraftError("product_missing_or_duplicate_in_envelope")
    job=matches[0]
    if (job.get("status")!="REVIEW_REQUIRED" or
        job.get("publication_allowed") is not False or
        job.get("campaign")!=route["campaign"] or
        job.get("site_key")!=site_key or
        job.get("platform")!=route["platform"]):
        raise UniversalDraftError("unsafe_job")
    brief=job.get("editorial_brief")
    if not isinstance(brief,dict):
        raise UniversalDraftError("missing_editorial_brief")
    title=brief.get("proposed_title")
    keyword=brief.get("keyword")
    slug=brief.get("slug")
    if (not isinstance(title,str) or not title.strip() or len(title)>120 or
        not isinstance(keyword,str) or not keyword.strip() or
        not isinstance(slug,str) or not re.fullmatch(r"[a-z0-9-]{5,120}",slug) or
        fold(keyword) not in fold(title)):
        raise UniversalDraftError("brief_not_ready")
    if brief.get("status",brief.get("editorial_status"))!="REVIEW_REQUIRED":
        raise UniversalDraftError("brief_status_invalid")
    row=catalog.db.execute("""
        SELECT shop_id,item_id,title,image_url,origin_url
        FROM products WHERE product_key=?
    """,(product_key,)).fetchone()
    if row is None or catalog.for_conversion(product_key) is None:
        raise UniversalDraftError("product_no_longer_approved")
    cached=catalog.cached_link(product_key,route["campaign"])
    product=job.get("product")
    if (not isinstance(product,dict) or
        not cached or not host_allowed(cached,allow_short=True) or
        product.get("offerLink")!=cached or
        product.get("sourceModes")!=["csv_r2_verified_affiliate_cache"] or
        product.get("shopId")!=str(row[0]) or
        product.get("itemId")!=str(row[1]) or
        product.get("productLink")!=str(row[4]) or
        not host_allowed(str(row[4])) or
        not str(row[3]).startswith("https://")):
        raise UniversalDraftError("exact_campaign_cache_mismatch")
    if (not isinstance(paragraphs,list) or len(paragraphs)<4 or
        any(not isinstance(p,str) or not 70<=len(p.strip())<=3000
            for p in paragraphs)):
        raise UniversalDraftError("editorial_body_invalid")
    cleaned=[" ".join(p.split()) for p in paragraphs]
    if (len(" ".join(cleaned).split())<250 or
        fold(keyword) not in fold(" ".join(cleaned))):
        raise UniversalDraftError("body_insufficient_or_keyword_missing")
    body="".join("<p>"+html.escape(p,quote=True)+"</p>" for p in cleaned)
    try:
        commercial=product_offer_html(catalog,site_key=site_key,
            product_key=product_key,topic=keyword,
            verified_site_route=route)
        related=related_articles_html(related_posts or [],
            blog_home_url=blog_home_url) if related_posts else ""
    except CommerceArticleError as exc:
        raise UniversalDraftError("product_commerce_or_internal_links_invalid") from exc
    article=body+commercial+related
    brief_id=hashlib.sha256(
        (site_key+"|"+product_key+"|"+slug).encode()).hexdigest()[:32]
    if route["platform"]=="blogger":
        meta={"kind":"blogger#post","blog":{"id":route["identifier"]},
              "title":title,"content":article,
              "labels":[str(job.get("topic") or keyword)[:80]],
              "isDraft":True}
    elif route["platform"]=="wordpress":
        meta={"title":title,"slug":slug,"content":article,
              "status":"draft","meta":{"_v31_editorial_brief_id":brief_id}}
    else:
        raise UniversalDraftError("unsupported_platform")
    return DraftPayload(route["platform"],site_key,brief_id,title,
                        article,meta,status="draft")
