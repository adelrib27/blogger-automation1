"""C36 — contrato universal de oportunidades para um blog existente ou futuro.

O assunto e a quantidade são informados na hora; nenhum assunto futuro é fixado.
Blog futuro: exploração e revisão SEM campanha atribuída.
Blog real cadastrado: seleção, campanha exata e handoff v2.3 somente com link
oficial já persistido. Não chama Shopee nem Blogger/WordPress; não publica.
Os payloads por produto ficam apenas em artefatos privados locais, nunca logs.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .catalog import Catalog, host_allowed
from .r2_state import R2State, verify_database
from .routing import sites
from .universal_brief import create_universal_brief
from .site_launch_plan import preview_site_launch


class HandoffError(ValueError):
    pass


MAX_ARTICLES_PER_BATCH = 24


def plan_editorial_handoff(
    catalog: Catalog, *, topic: str, platform: str,
    articles: int, site_key: str | None = None,
) -> dict:
    """Produz um payload revisável; nenhum elemento publica automaticamente.

    Se faltar um link de uma campanha real, retorna só necessidade de conversão.
    Nunca transfere offerLink de campanha diferente nem publica item em revisão.
    """
    if type(articles) is not int or not 1 <= articles <= MAX_ARTICLES_PER_BATCH:
        raise HandoffError("invalid_article_count")
    if platform not in ("blogger", "wordpress"):
        raise HandoffError("unsupported_platform")
    if not isinstance(topic, str) or not topic.strip() or len(topic)>160:
        raise HandoffError("topic_invalid")
    real_site = sites().get(site_key) if site_key is not None else None
    if site_key is not None and real_site is None:
        raise HandoffError("real_site_not_registered")
    if real_site is not None and real_site["platform"] != platform:
        raise HandoffError("site_platform_mismatch")

    preview = preview_site_launch(
        catalog,topic=topic,platform=platform,site_key=site_key,
        max_items=articles,max_per_shop=1,
    )
    if preview["can_publish"] is not False:
        raise HandoffError("unsafe_preview")
    jobs=[]
    conversions=[]
    future_plans=[]
    conversion_plans=[]
    used_shops=set()
    campaign=real_site["campaign"] if real_site else None
    for article_index,item in enumerate(preview["approved_catalog_candidates"],1):
        key=item["product_key"]
        shop=item["shop_id"]
        if shop in used_shops:
            raise HandoffError("shop_diversity_broken")
        used_shops.add(shop)
        if catalog.for_conversion(key) is None:
            raise HandoffError("item_not_approved_for_conversion")
        dynamic=create_universal_brief(topic=topic,
            product_title=item["title"],product_key=key,
            article_index=article_index)
        if campaign is None:
            if item["affiliate_url"] is not None:
                raise HandoffError("hypothetical_campaign_link")
            future_plans.append({"product_key":key,"editorial_brief":dynamic,
                "affiliate_url":None,"campaign":None,"can_publish":False})
            continue
        official=catalog.cached_link(key,campaign)
        if official is None:
            conversions.append(key)
            conversion_plans.append({"product_key":key,
                "editorial_brief":item.get("editorial_brief") or dynamic,
                "affiliate_url":None,"campaign":campaign,
                "can_publish":False})
            continue
        if not host_allowed(official,allow_short=True):
            raise HandoffError("affiliate_link_invalid")
        if official != item.get("affiliate_url") or \
           item.get("affiliate_status")!="verified_for_campaign":
            raise HandoffError("campaign_link_inconsistent")
        row=catalog.db.execute("""
          SELECT shop_id,item_id,title,image_url,origin_url
          FROM products WHERE product_key=?
        """,(key,)).fetchone()
        if row is None or not str(row[0]).isdigit() or \
           not str(row[1]).isdigit() or \
           not str(row[3]).startswith("https://") or \
           not host_allowed(row[4]):
            raise HandoffError("product_contract_invalid")
        jobs.append({
            "site_key":site_key,
            "platform":platform,
            "topic":topic,
            "campaign":campaign,
            "product_key":key,
            "product":{
                "shopId":str(row[0]), "itemId":str(row[1]),
                "productName":row[2], "imageUrl":row[3],
                "productLink":row[4], "offerLink":official,
                "sourceModes":["csv_r2_verified_affiliate_cache"],
            },
            "editorial_brief":item.get("editorial_brief") or dynamic,
            "status":"REVIEW_REQUIRED",
            "publication_allowed":False,
        })
    if len(jobs)+len(conversions)>articles:
        raise HandoffError("article_count_exceeded")
    return {
        "mode":"C36_UNIVERSAL_HANDOFF_SAFE",
        "requested_articles":articles,
        "platform":platform,
        "site_registered":real_site is not None,
        "requires_registration":real_site is None,
        "requires_real_campaign":real_site is None,
        "discovered_approved":len(preview["approved_catalog_candidates"]),
        "review_candidates":preview["review_queue_count"],
        "ready_review_jobs":jobs,
        "conversion_required_keys":conversions,
        "future_review_plans":future_plans,
        "conversion_review_plans":conversion_plans,
        "missing_product_slots":articles-len(jobs)-len(conversions)
            if real_site is not None else
            articles-len(preview["approved_catalog_candidates"]),
        "editorial_approval_required":True,
        "platform_auth_required":True,
        "new_site_created":False,
        "r2_writes":0,
        "shopee_mutation_attempts":0,
        "publication_calls":0,
        "can_publish":False,
    }


def safe_summary(report: dict) -> dict:
    """Somente quantidades; nomes de blog, produtos e URLs nunca nos logs."""
    if report.get("mode")!="C36_UNIVERSAL_HANDOFF_SAFE" or \
       report.get("can_publish") is not False:
        raise HandoffError("invalid_report")
    return {
        "mode":report["mode"],
        "platform":report["platform"],
        "requested_articles":report["requested_articles"],
        "site_registered":report["site_registered"],
        "requires_registration":report["requires_registration"],
        "approved_catalog_candidates":report["discovered_approved"],
        "review_candidates":report["review_candidates"],
        "ready_review_jobs":len(report["ready_review_jobs"]),
        "future_review_plans":len(report["future_review_plans"]),
        "conversion_required":len(report["conversion_required_keys"]),
        "missing_product_slots":report["missing_product_slots"],
        "editorial_approval_required":True,
        "platform_auth_required":True,
        "new_site_created":False,
        "r2_writes":0,"shopee_mutation_attempts":0,
        "publication_calls":0,"can_publish":False,
    }


def main() -> int:
    p=argparse.ArgumentParser(description="V31: intake e handoff independente de nichos previstos")
    p.add_argument("--topic",required=True)
    p.add_argument("--platform",choices=("blogger","wordpress"),required=True)
    p.add_argument("--articles",type=int,required=True)
    p.add_argument("--site-key",default=None)
    p.add_argument("--mode",choices=("r2","local"),default="r2")
    p.add_argument("--db",default=None)
    args=p.parse_args()
    try:
        if (args.mode=="r2" and args.db is not None) or \
           (args.mode=="local" and args.db is None):
            raise HandoffError("invalid_source")
        with tempfile.TemporaryDirectory(prefix="v31-c36-handoff-") as tmp:
            if args.mode=="r2":
                db=Path(tmp)/"catalog.sqlite3"
                if not R2State.from_env().restore_to(db):
                    raise HandoffError("catalog_missing")
                verify_database(db)
            else:
                db=Path(args.db)
                if not db.is_file() or db.is_symlink():
                    raise HandoffError("local_catalog_invalid")
            with Catalog(db) as cat:
                report=plan_editorial_handoff(
                    cat,topic=args.topic,platform=args.platform,
                    articles=args.articles,site_key=args.site_key)
                summary=safe_summary(report)
        print("V31_C36_UNIVERSAL_EDITORIAL_HANDOFF_SAFE_PASS")
        print(json.dumps(summary,sort_keys=True,ensure_ascii=False))
        return 0
    except Exception as exc:
        print("V31_C36_UNIVERSAL_EDITORIAL_HANDOFF_FAILED_"+type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
