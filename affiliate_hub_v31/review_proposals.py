"""C22 — propostas de curadoria por categoria OFICIAL, não aprovações.

A origem L1/L2 é útil para localizar produtos de blogs futuros, mas nunca
substitui taxonomia, moderação, revisão de texto nem conversão por campanha.
A CLI em R2 usa cópia temporária e registra somente contagens agregadas.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import tempfile
from pathlib import Path

from .catalog import Catalog, host_allowed
from .curation_audit import PROTECTED_ROOTS
from .r2_state import R2State, verify_database
from .source_policy_gate import source_safe_for_use
from .taxonomy import classify_title, normalize

# Mapeamento de INTENÇÃO para auditoria, não classificação autoritativa.
# Um termo textual positivo deve bater ANTES de uma sugestão de rota.
PATH_ROUTE_HINTS: dict[tuple[str,str], frozenset[str]] = {
    ("home living","kitchenware"):
        frozenset(("cozinha/organizacao_utensilios","cafe/preparo")),
    ("home living","decoration"):
        frozenset(("casa/decoracao",)),
    ("home living","furniture"):
        frozenset(("casa/organizacao",)),
    ("home living","tools home improvement"):
        frozenset(("ferramentas/eletricas_manuais",)),
    ("home living","home care supplies"):
        frozenset(("limpeza/equipamentos","casa/organizacao")),
    ("home appliances","kitchen appliances"):
        frozenset(("cozinha/air_fryers","cozinha/liquidificadores",
                   "cozinha/outros_eletroportateis","cafe/preparo")),
    ("spare parts and accessories for vehicles","internal accessories for automobiles"):
        frozenset(("automotivo/acessorios",)),
    ("spare parts and accessories for vehicles","external accessories for automobiles"):
        frozenset(("automotivo/acessorios",)),
}
TECHNICAL_REVIEW_ROOTS=frozenset((
    "spare parts and accessories for vehicles", "sports outdoors",
))


class ProposalError(ValueError):
    pass


def propose_review_batch(
    catalog: Catalog, *, category_l1: str, category_l2: str,
    limit: int=16, max_per_shop: int=1,
) -> dict:
    """Lista privada para humano/editor, sem strings em logs públicos de CI.

    Produtos mantêm o estado original; sugestão não inclui preço, venda,
    comissão, avaliação ou link de afiliado. Não cria schema ou registros.
    """
    if not isinstance(category_l1,str) or not 2<=len(category_l1)<=120 \
            or not normalize(category_l1):
        raise ProposalError("invalid_l1")
    if not isinstance(category_l2,str) or not 2<=len(category_l2)<=120 \
            or not normalize(category_l2):
        raise ProposalError("invalid_l2")
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=50:
        raise ProposalError("invalid_limit")
    if not isinstance(max_per_shop,int) or isinstance(max_per_shop,bool) \
            or not 1<=max_per_shop<=4:
        raise ProposalError("invalid_shop_limit")
    root, branch = normalize(category_l1),normalize(category_l2)
    if root in PROTECTED_ROOTS:
        raise ProposalError("protected_root_requires_separate_policy_review")
    exists = catalog.db.execute("""
        SELECT 1 FROM sqlite_master WHERE type='table'
          AND name='product_source_categories'
    """).fetchone()
    if not exists:
        raise ProposalError("official_source_category_index_unavailable")
    cursor=catalog.db.execute("""
        SELECT p.product_key,p.shop_id,p.title,p.origin_url,p.image_url,
               p.moderation,p.moderation_reason,COALESCE(t.status,'review'),
               s.level1,s.level2,COALESCE(s.level3,'')
        FROM products p
        JOIN product_source_categories s ON s.product_key=p.product_key
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
        WHERE s.status='matched' AND s.level1=? AND s.level2=?
          AND NOT (p.moderation='eligible' AND t.status='matched')
        GROUP BY p.product_key
        ORDER BY p.product_key
    """,(root,branch))
    selected=[]
    seen=set()
    shop_counts=Counter()
    screened=Counter()
    hints=PATH_ROUTE_HINTS.get((root,branch),frozenset())
    for row in cursor:
        key,shop,title,url,image,moderation,reason,tax,l1,l2,l3=row
        if key in seen:
            continue
        seen.add(key)
        if not source_safe_for_use(catalog,key):
            screened["source_conflict"]+=1
            continue
        if "categoria_sensivel" in reason or not host_allowed(url) or \
                not str(image).startswith("https://") or not shop.strip():
            screened["unsafe_or_incomplete"]+=1
            continue
        if shop_counts[shop]>=max_per_shop:
            screened["duplicate_shop"]+=1
            continue
        # A taxonomia de título não autoriza promoção mesmo quando bate.
        route=classify_title(title)
        suggested = (f"{route.category}/{route.niche}"
                     if route.status=="matched" and
                     f"{route.category}/{route.niche}" in hints else None)
        selected.append({
            "product_key":key,
            "shop_id":shop,
            "title":title,
            "source_category_l1":l1,
            "source_category_l2":l2,
            "source_category_l3":l3,
            "suggested_editorial_route":suggested,
            "suggestion_basis":"OFFICIAL_CATEGORY_PLUS_TITLE_RULE"
                               if suggested else "OFFICIAL_CATEGORY_ONLY",
            "manual_technical_review":root in TECHNICAL_REVIEW_ROOTS,
            "curation":"review_required",
            "affiliate_url":None,
            "can_convert":False,
            "can_publish":False,
            "review_required":True,
        })
        shop_counts[shop]+=1
        if len(selected)>=limit:
            break
    return {
        "mode":"C22_CATEGORY_REVIEW_PROPOSAL_ONLY",
        "requested_source_category_l1":root,
        "requested_source_category_l2":branch,
        "candidates":selected,
        "screened_counts":dict(sorted(screened.items())),
        "rejected_unsafe_roots":False,
        "ready_for_auto_approval":False,
        "new_approvals":0, "shopee_api_calls":0,
        "conversion_calls":0, "publication_calls":0,
        "r2_writes":0, "can_publish":False,
    }


def summarize_review_batch(report: dict) -> dict:
    if report.get("mode")!="C22_CATEGORY_REVIEW_PROPOSAL_ONLY" \
            or report.get("can_publish") is not False:
        raise ProposalError("invalid_proposal_report")
    items=report["candidates"]
    if any(x.get("affiliate_url") is not None or
           x.get("can_publish") or not x.get("review_required") for x in items):
        raise ProposalError("unsafe_proposal_result")
    return {
        "mode":report["mode"],
        "source_category_l1":report["requested_source_category_l1"],
        "source_category_l2":report["requested_source_category_l2"],
        "review_candidates":len(items),
        "distinct_shops":len({item["shop_id"] for item in items}),
        "title_and_source_supported_route_suggestions":sum(
            bool(item["suggested_editorial_route"]) for item in items),
        "source_only_needs_editor_review":sum(
            not item["suggested_editorial_route"] for item in items),
        "technical_review":sum(
            item["manual_technical_review"] for item in items),
        "screened_counts":report["screened_counts"],
        "new_approvals":0,"conversion_calls":0,
        "publication_calls":0,"r2_writes":0,
        "can_publish":False,
    }


def main()->int:
    p=argparse.ArgumentParser(description="C22 propostas seguras para curadoria")
    p.add_argument("--mode",choices=("local","r2"),required=True)
    p.add_argument("--db",default=None)
    p.add_argument("--l1",required=True)
    p.add_argument("--l2",required=True)
    p.add_argument("--limit",type=int,default=16)
    args=p.parse_args()
    try:
        if args.mode=="local":
            if not args.db:
                raise ProposalError("missing_local_db")
            with Catalog(Path(args.db)) as cat:
                report=summarize_review_batch(propose_review_batch(
                    cat,category_l1=args.l1,category_l2=args.l2,
                    limit=args.limit))
        else:
            if args.db:
                raise ProposalError("r2_local_conflict")
            with tempfile.TemporaryDirectory(prefix="v31-c22-readonly-") as folder:
                db=Path(folder)/"catalog.sqlite3"
                if not R2State.from_env().restore_to(db):
                    raise ProposalError("catalog_missing")
                verify_database(db)
                with Catalog(db) as cat:
                    report=summarize_review_batch(propose_review_batch(
                        cat,category_l1=args.l1,category_l2=args.l2,
                        limit=args.limit))
        print("V31_C22_REVIEW_PROPOSAL_SAFE_PASS")
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception as exc:
        print("V31_C22_REVIEW_PROPOSAL_SAFE_FAILED_"+type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
