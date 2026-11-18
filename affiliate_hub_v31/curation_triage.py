"""C21 — triagem exaustiva e somente leitura do acervo universal V31.

Agrupa a demanda por revisão SEM aprovar SKU, converter link, gerar post ou
alterar o R2. Prioridade significa "ordem de investigação editorial", não
potencial de comissão, venda ou classificação comercial. Conserva flags das
duas origens Shopee, inclusive status='conflict' (nunca ignorá-los).
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import tempfile
from pathlib import Path

from .catalog import Catalog, host_allowed
from .curation_audit import PROTECTED_ROOTS
from .r2_state import R2State, verify_database
from .source_category_index import create_source_category_schema

LANES = (
    "SOURCE_CONFLICT",
    "POLICY_REVIEW",
    "DATA_REPAIR",
    "NO_OFFICIAL_CATEGORY",
    "TAXONOMY_REVIEW",
    "MODERATION_REVIEW",
    "OTHER_HOLD",
)
INVESTIGATE_LANES = frozenset(("TAXONOMY_REVIEW", "MODERATION_REVIEW"))


class TriageError(ValueError):
    pass


def lane_for_record(
    *, title: str, shop_id: str, origin_url: str, image_url: str,
    moderation: str, moderation_reason: str, taxonomy_status: str,
    source_l1: str, source_record_count: int, branches: int,
    leaves: int, invalid_sources: int,
) -> str:
    """Uma única lane por SKU. Ordem conservadora, independente de blog/campanha."""
    if invalid_sources or branches > 1 or leaves > 1:
        return "SOURCE_CONFLICT"
    if source_l1 in PROTECTED_ROOTS or "categoria_sensivel" in moderation_reason:
        return "POLICY_REVIEW"
    if not title.strip() or not shop_id.strip() or not host_allowed(origin_url) or \
            not image_url.startswith("https://"):
        return "DATA_REPAIR"
    if source_record_count == 0 or not source_l1:
        return "NO_OFFICIAL_CATEGORY"
    if taxonomy_status != "matched":
        return "TAXONOMY_REVIEW"
    if moderation != "eligible":
        return "MODERATION_REVIEW"
    return "OTHER_HOLD"


def triage_backlog(catalog: Catalog, *, max_categories: int = 12) -> dict:
    """Varre produtos uma vez, com cursor incremental e nenhum banco novo.

    IDs de produto, lojas, URLs e títulos jamais entram no relatório.
    As categorias exibidas são as facetas L1/L2 normalizadas pelo importador.
    """
    if not isinstance(max_categories, int) or isinstance(max_categories, bool) \
            or not 1 <= max_categories <= 30:
        raise TriageError("invalid_max_categories")
    create_source_category_schema(catalog)
    stats = catalog.stats()
    rows = catalog.db.execute("""
        WITH facets AS (
            SELECT product_key,
                COUNT(*) AS source_count,
                MIN(CASE WHEN status='matched' THEN level1 END) AS l1,
                MIN(CASE WHEN status='matched' THEN level2 END) AS l2,
                COUNT(DISTINCT CASE WHEN status='matched' THEN
                    level1 || char(31) || level2 END) AS branches,
                COUNT(DISTINCT CASE WHEN status='matched' AND level3!='' THEN
                    level3 END) AS leaves,
                SUM(CASE WHEN status!='matched' THEN 1 ELSE 0 END) AS invalid_sources
            FROM product_source_categories
            GROUP BY product_key
        )
        SELECT p.shop_id,p.title,p.origin_url,p.image_url,p.moderation,
               p.moderation_reason,COALESCE(t.status,'review'),
               COALESCE(f.l1,''),COALESCE(f.l2,''),
               COALESCE(f.source_count,0),COALESCE(f.branches,0),
               COALESCE(f.leaves,0),COALESCE(f.invalid_sources,0)
        FROM products p
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
        LEFT JOIN facets f ON f.product_key=p.product_key
    """)

    counts = Counter()
    opportunities = Counter()
    shops = defaultdict(set)
    legacy_protected = 0
    total_seen = 0
    for (shop_id,title,origin_url,image_url,moderation,reason,tax_status,
         l1,l2,source_count,branches,leaves,invalid_sources) in rows:
        total_seen += 1
        existing_approved = moderation == "eligible" and tax_status == "matched"
        inconsistent_source = bool(invalid_sources or branches > 1 or leaves > 1)
        if existing_approved:
            if l1 in PROTECTED_ROOTS or inconsistent_source:
                legacy_protected += 1
            continue

        lane = lane_for_record(
            title=title, shop_id=shop_id, origin_url=origin_url,
            image_url=image_url, moderation=moderation,
            moderation_reason=reason, taxonomy_status=tax_status,
            source_l1=l1, source_record_count=source_count,
            branches=branches, leaves=leaves,
            invalid_sources=invalid_sources,
        )
        counts[lane] += 1
        if lane in INVESTIGATE_LANES and l1 and l2:
            group = (l1, l2)
            opportunities[group] += 1
            shops[group].add(shop_id)

    if total_seen != stats["products"] or sum(counts.values()) != stats["review"]:
        raise TriageError("catalog_stats_inconsistent")
    if stats["eligible"] + stats["review"] != stats["products"]:
        raise TriageError("review_count_mismatch")
    ranked = sorted(opportunities, key=lambda g: (
        -len(shops[g]), -opportunities[g], g,
    ))[:max_categories]
    return {
        "mode": "C21_CURATION_READONLY",
        "products": stats["products"],
        "previously_approved": stats["eligible"],
        "pending_review": stats["review"],
        "sum_review_lanes": sum(counts.values()),
        "prior_approvals_with_protected_or_conflicting_source": legacy_protected,
        "lane_counts": {name: counts[name] for name in LANES},
        "review_opportunity_paths": [
            {"category_l1": l1, "category_l2": l2,
             "pending_for_manual_review": opportunities[(l1,l2)],
             "distinct_shops": len(shops[(l1,l2)]),
             "publication_approved": False,
             "estimated_sales_or_commission": None}
            for l1,l2 in ranked
        ],
        "existing_affiliate_links": stats["cached_affiliate_links"],
        "new_approvals": 0,
        "affiliate_conversion_calls": 0, "shopee_api_calls": 0,
        "site_creation_calls": 0, "publication_calls": 0,
        "r2_writes": 0,
        "can_publish": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="C21 auditoria integral SAFE da curadoria")
    parser.add_argument("--mode", choices=("local", "r2"), required=True)
    parser.add_argument("--db", default=None)
    parser.add_argument("--max-categories", type=int, default=12)
    args = parser.parse_args()
    try:
        if args.mode == "local":
            if not args.db:
                raise TriageError("missing_local_database")
            with Catalog(Path(args.db)) as cat:
                report = triage_backlog(cat,max_categories=args.max_categories)
        else:
            if args.db is not None:
                raise TriageError("r2_and_local_path_conflict")
            with tempfile.TemporaryDirectory(prefix="v31-c21-curation-ro-") as folder:
                db=Path(folder)/"catalog.sqlite3"
                if not R2State.from_env().restore_to(db):
                    raise TriageError("catalog_absent")
                verify_database(db)
                with Catalog(db) as cat:
                    report=triage_backlog(cat,max_categories=args.max_categories)
        print("V31_C21_CURATION_READONLY_PASS")
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception as exc:
        print("V31_C21_CURATION_READONLY_FAILED_"+type(exc).__name__)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
