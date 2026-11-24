"""C22 — contrato de seleção por tema para Blogger/WordPress conhecidos ou futuros.

O usuário escolhe o assunto na criação do blog. Nunca antecipamos blogs,
inventamos campanhas ou copiamos links de um outro site. Para site registrado,
a lista obedece o nicho cadastrado e monta pautas (sem persistir ou publicar).
O conteúdo comercial só segue por APIs existentes após gates independentes.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .catalog import Catalog
from .editorial import EditorialError, make_brief
from .future_site_intake import preview_future_site
from .r2_state import R2State, verify_database
from .routing import sites
from .editorial_scope_validation import load_policy, scope_status

class SiteLaunchError(ValueError):
    pass


def preview_site_launch(
    catalog: Catalog, *, topic: str, platform: str,
    site_key: str | None=None, campaign: str | None=None,
    max_items: int=12, max_per_shop: int=1,
) -> dict:
    """Prepara a intenção de compra sem criar site, converter ou publicar.

    Site existente: campanha é imposta pelo registro e a taxonomia do item
    precisa pertencer ao conjunto de nichos autorizados pela rota.
    Blog futuro: sem campanha provisória, sem inventar novos nichos.
    """
    if platform not in ("blogger","wordpress"):
        raise SiteLaunchError("platform_not_supported")
    if not isinstance(max_items,int) or isinstance(max_items,bool) \
            or not 1<=max_items<=24:
        raise SiteLaunchError("max_items_invalid")
    if not isinstance(max_per_shop,int) or isinstance(max_per_shop,bool) \
            or not 1<=max_per_shop<=4:
        raise SiteLaunchError("max_per_shop_invalid")
    registered = None
    if site_key is not None:
        if not isinstance(site_key,str):
            raise SiteLaunchError("site_key_invalid")
        registered=sites().get(site_key)
        # C140: exclusão expressa aplica-se até aos fluxos manuais de prévia
        # e conversão; rota histórica não é permissão para usar o blog.
        if registered is not None:
            status = scope_status(load_policy(), registered)
            if status in {"EXCLUDED_BY_OWNER", "DELETED_BY_OWNER",
                          "REFERENCE_ONLY_NOT_V31_DESTINATION"}:
                raise SiteLaunchError("owner_excluded_or_deleted_editorial_site")
        if registered is None:
            raise SiteLaunchError("site_not_registered")
        if registered["platform"]!=platform or registered["publish_enabled"] is not False:
            raise SiteLaunchError("site_registration_mismatch")
        if campaign is not None and campaign!=registered["campaign"]:
            raise SiteLaunchError("cross_campaign_forbidden")
        campaign=registered["campaign"]
    elif campaign is not None:
        # Não há autorização para vincular campanha a blog hipotético.
        raise SiteLaunchError("unregistered_campaign_forbidden")

    # Solicita mais itens que o necessário; o filtro de nichos registrados
    # pode remover muitos resultados. Nunca usa candidados under review.
    sample=preview_future_site(
        catalog,topic=topic,platform=platform,campaign=campaign,
        approved_limit=24,review_limit=12,max_per_shop=max_per_shop)
    selected=[]
    for item in sample["approved_candidates"]:
        row=catalog.db.execute("""
            SELECT t.category,t.niche FROM product_taxonomy t
            WHERE t.product_key=? AND t.status='matched'
        """,(item["product_key"],)).fetchone()
        if row is None:
            continue
        category,niche=row
        route=f"{category}/{niche}"
        official=f"{item['source_category_l1']}/{item['source_category_l2']}"
        legacy_allowed=registered is not None and route in registered["allowed_niches"]
        official_allowed=(registered is not None and
                          official in registered.get("allowed_source_paths",[]))
        if registered is not None and not (legacy_allowed or official_allowed):
            continue

        # Reforço da autorização de origem na última milha.
        if catalog.for_conversion(item["product_key"]) is None:
            continue
        if item["affiliate_url"] is not None and campaign is None:
            raise SiteLaunchError("campaign_link_leak")
        editorial=None
        if registered:
            try:
                brief=make_brief(site_key,item["product_key"],item["title"],
                                category,niche,"criterios")
            except EditorialError:
                if not official_allowed:
                    continue
                # Nicho futuro pode nao possuir template editorial registrado.
                # Uma proposta para o gerador apropriado, sem inventar titulo.
                editorial={
                    "proposed_title":None,"keyword":None,
                    "topic":topic,"slug":None,"status":"REVIEW_REQUIRED",
                }
            else:
                editorial={
                    "proposed_title":brief.title,
                    "keyword":brief.keyword,"topic":brief.topic,
                    "slug":brief.slug,"status":"REVIEW_REQUIRED",
                }
        selected.append({
            "product_key":item["product_key"],
            "shop_id":item["shop_id"],
            "title":item["title"],
            "original_product_url":item["product_origin_url"],
            "editorial_category":category,
            "editorial_niche":niche,
            "source_category_l1":item["source_category_l1"],
            "source_category_l2":item["source_category_l2"],
            "semantic_score":item["semantic_score"],
            "affiliate_status":item["affiliate_status"],
            "affiliate_url":item["affiliate_url"],
            "editorial_brief":editorial,
            "can_publish":False,
        })
        if len(selected)>=max_items:
            break
    if any(x["can_publish"] or (x["affiliate_url"] and campaign is None)
           for x in selected):
        raise SiteLaunchError("unsafe_output")
    return {
        "mode":"C22_SITE_LAUNCH_REVIEW_ONLY",
        "platform":platform,
        "site_key":site_key,
        "campaign":campaign,
        "registered_site":bool(registered),
        "future_site_needs_registration":registered is None,
        "topic":topic,
        "approved_catalog_candidates":selected,
        "requires_conversion":sum(
            x["affiliate_status"]=="requires_conversion" for x in selected),
        "cached_for_campaign":sum(
            x["affiliate_status"]=="verified_for_campaign" for x in selected),
        "review_queue_count":len(sample["review_queue"]),
        "category_paths_count":len(sample["category_paths"]),
        "ready_for_unreviewed_publication":False,
        "requires_original_body_and_editorial_approval":True,
        "requires_platform_authentication":True,
        "site_creation_calls":0,"shopee_api_calls":0,
        "affiliate_conversion_calls":0,
        "publication_calls":0,"r2_writes":0,
        "can_publish":False,
    }


def summarize_site_launch(report:dict)->dict:
    """Resumo seguro para GitHub: nomes de sites, pautas, links e SKU omitidos."""
    if report.get("mode")!="C22_SITE_LAUNCH_REVIEW_ONLY" or \
            report.get("can_publish") is not False:
        raise SiteLaunchError("not_safe_site_launch")
    items=report["approved_catalog_candidates"]
    if any(x.get("can_publish") for x in items):
        raise SiteLaunchError("publication_attempt_detected")
    return {
        "mode":report["mode"],
        "platform":report["platform"],
        "registered_site":report["registered_site"],
        "future_site_needs_registration":report["future_site_needs_registration"],
        "selected_catalog_candidates":len(items),
        "distinct_shops":len({x["shop_id"] for x in items}),
        "cached_links_for_exact_campaign":report["cached_for_campaign"],
        "items_requiring_conversion_for_exact_campaign":report["requires_conversion"],
        "proposed_editorial_briefs":sum(
            x["editorial_brief"] is not None for x in items),
        "separate_review_queue_items":report["review_queue_count"],
        "category_paths_found":report["category_paths_count"],
        "requires_original_body_and_editorial_approval":True,
        "requires_platform_authentication":True,
        "publication_calls":0,
        "affiliate_conversion_calls":0,
        "site_creation_calls":0,
        "r2_writes":0,"can_publish":False,
    }


def main()->int:
    parser=argparse.ArgumentParser(description="C22 proposta de lançamento SAFE")
    parser.add_argument("--mode",choices=("local","r2"),required=True)
    parser.add_argument("--db",default=None)
    parser.add_argument("--platform",choices=("blogger","wordpress"),required=True)
    parser.add_argument("--topic",required=True)
    parser.add_argument("--site-key",default=None)
    args=parser.parse_args()
    try:
        if args.mode=="local":
            if not args.db:
                raise SiteLaunchError("local_db_required")
            with Catalog(Path(args.db)) as cat:
                report=summarize_site_launch(preview_site_launch(
                    cat,topic=args.topic,platform=args.platform,
                    site_key=args.site_key))
        else:
            if args.db:
                raise SiteLaunchError("r2_db_conflict")
            with tempfile.TemporaryDirectory(prefix="v31-c22-launch-") as folder:
                db=Path(folder)/"catalog.sqlite3"
                if not R2State.from_env().restore_to(db):
                    raise SiteLaunchError("r2_catalog_unavailable")
                verify_database(db)
                with Catalog(db) as cat:
                    report=summarize_site_launch(preview_site_launch(
                        cat,topic=args.topic,platform=args.platform,
                        site_key=args.site_key))
        print("V31_C22_SITE_LAUNCH_SAFE_PASS")
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception as exc:
        print("V31_C22_SITE_LAUNCH_SAFE_FAILED_"+type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
