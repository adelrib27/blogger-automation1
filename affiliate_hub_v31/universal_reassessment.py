"""C33 — reavaliação integral e somente leitura da biblioteca universal Shopee.

A reimportação cumulativa preserva o estado antigo dos SKUs existentes.
Este planejador mede o trabalho necessário para reclassificar TODO o backlog,
sem inferir uma aprovação a partir de um único sinal de título ou categoria.
Nenhum ID, título, link ou campanha é escrito nos relatórios consolidados.
Não chama Shopee, não grava R2, não publica, não aprova produtos.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import shutil
import tempfile
from pathlib import Path

from .catalog import Catalog
from .curation_triage import LANES, lane_for_record
from .review_proposals import PATH_ROUTE_HINTS
from .r2_state import R2State, verify_database
from .taxonomy import classify_title

SIGNALS = (
    "TITLE_AND_OFFICIAL_PATH",
    "TITLE_ONLY_UNVALIDATED_PATH",
    "TITLE_WITHOUT_OFFICIAL_FACET",
    "OFFICIAL_FACET_WITHOUT_TITLE_ROUTE",
    "NO_SOURCE_OR_TITLE_ROUTE",
    "SOURCE_CONFLICT_BLOCKED",
    "POLICY_REVIEW_BLOCKED",
    "DATA_REPAIR_BLOCKED",
    "OTHER_REVIEW_BLOCKED",
)
ELIGIBLE_FOR_REASSESSMENT = frozenset((
    "TAXONOMY_REVIEW", "MODERATION_REVIEW", "NO_OFFICIAL_CATEGORY",
))


class ReassessmentError(ValueError):
    pass


def plan_universal_reassessment(catalog: Catalog, *, max_paths: int = 20) -> dict:
    """Varre todos os pendentes, conta sugestões e mantém status intactos.

    TITLE_AND_OFFICIAL_PATH é EVIDÊNCIA para revisão, nunca aprovação.
    Os demais sinais também são apenas propostas de investigação.
    """
    if type(max_paths) is not int or not 1 <= max_paths <= 100:
        raise ReassessmentError("invalid_max_paths")
    present = catalog.db.execute("""
      SELECT 1 FROM sqlite_master WHERE type='table'
      AND name='product_source_categories'
    """).fetchone()
    if not present:
        raise ReassessmentError("official_facets_missing")

    stats = catalog.stats()
    cursor = catalog.db.execute("""
        WITH facets AS (
          SELECT product_key, COUNT(*) AS source_count,
            MIN(CASE WHEN status='matched' THEN level1 END) AS l1,
            MIN(CASE WHEN status='matched' THEN level2 END) AS l2,
            COUNT(DISTINCT CASE WHEN status='matched' THEN
               level1 || char(31) || level2 END) AS branches,
            COUNT(DISTINCT CASE WHEN status='matched' AND level3!='' THEN
               level3 END) AS leaves,
            SUM(CASE WHEN status!='matched' THEN 1 ELSE 0 END) AS bad_sources
          FROM product_source_categories GROUP BY product_key
        )
        SELECT p.title,p.shop_id,p.origin_url,p.image_url,p.moderation,
          p.moderation_reason,COALESCE(t.status,'review'),COALESCE(f.l1,''),
          COALESCE(f.l2,''),COALESCE(f.source_count,0),
          COALESCE(f.branches,0),COALESCE(f.leaves,0),
          COALESCE(f.bad_sources,0)
        FROM products p
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
        LEFT JOIN facets f ON f.product_key=p.product_key
        WHERE NOT (p.moderation='eligible' AND t.status='matched')
        ORDER BY p.product_key
    """)

    lanes = Counter()
    signals = Counter()
    paths = defaultdict(Counter)
    shops = defaultdict(set)
    count = 0
    for row in cursor:
        (title,shop,url,image,moderation,reason,tax_status,l1,l2,
         source_count,branches,leaves,bad_sources) = row
        count += 1
        lane = lane_for_record(
            title=title, shop_id=shop, origin_url=url, image_url=image,
            moderation=moderation, moderation_reason=reason,
            taxonomy_status=tax_status, source_l1=l1,
            source_record_count=source_count, branches=branches,
            leaves=leaves, invalid_sources=bad_sources,
        )
        lanes[lane] += 1
        if lane == "SOURCE_CONFLICT":
            signal = "SOURCE_CONFLICT_BLOCKED"
        elif lane == "POLICY_REVIEW":
            signal = "POLICY_REVIEW_BLOCKED"
        elif lane == "DATA_REPAIR":
            signal = "DATA_REPAIR_BLOCKED"
        elif lane not in ELIGIBLE_FOR_REASSESSMENT:
            signal = "OTHER_REVIEW_BLOCKED"
        else:
            route = classify_title(title)
            if lane == "NO_OFFICIAL_CATEGORY":
                signal = ("TITLE_WITHOUT_OFFICIAL_FACET"
                          if route.status == "matched" else
                          "NO_SOURCE_OR_TITLE_ROUTE")
            elif route.status != "matched":
                signal = "OFFICIAL_FACET_WITHOUT_TITLE_ROUTE"
            elif f"{route.category}/{route.niche}" in PATH_ROUTE_HINTS.get(
                    (l1,l2), frozenset()):
                signal = "TITLE_AND_OFFICIAL_PATH"
            else:
                signal = "TITLE_ONLY_UNVALIDATED_PATH"
        signals[signal] += 1
        if l1 and l2 and lane in ("TAXONOMY_REVIEW", "MODERATION_REVIEW"):
            key = (l1,l2)
            paths[key]["pending"] += 1
            paths[key][signal] += 1
            if signal == "TITLE_AND_OFFICIAL_PATH":
                shops[key].add(shop)

    if count != stats["review"] or sum(lanes.values()) != count or \
       sum(signals.values()) != count:
        raise ReassessmentError("backlog_count_inconsistent")

    ranked = sorted(paths, key=lambda k: (
        -paths[k]["TITLE_AND_OFFICIAL_PATH"],
        -len(shops[k]), -paths[k]["pending"], k,
    ))[:max_paths]
    return {
        "mode": "C33_UNIVERSAL_REASSESSMENT_READONLY",
        "products": stats["products"],
        "previously_approved": stats["eligible"],
        "pending_review": count,
        "review_lane_counts": {name: lanes[name] for name in LANES},
        "evidence_counts": {name: signals[name] for name in SIGNALS},
        "source_paths_awaiting_review": len(paths),
        "priority_review_paths": [
            {"category_l1": l1, "category_l2": l2,
             "pending": paths[(l1,l2)]["pending"],
             "title_and_official_evidence":
                 paths[(l1,l2)]["TITLE_AND_OFFICIAL_PATH"],
             "distinct_shops_with_both_signals": len(shops[(l1,l2)]),
             "can_autoapprove": False}
            for l1,l2 in ranked
        ],
        "review_proposal_only": True,
        "new_approvals": 0,
        "shopee_api_calls": 0,
        "affiliate_conversion_calls": 0,
        "r2_writes": 0,
        "publication_calls": 0,
        "can_publish": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="C33 — mapa de reclassificação universal, zero alterações")
    parser.add_argument("--mode", choices=("local","r2"), required=True)
    parser.add_argument("--db", default=None)
    parser.add_argument("--max-paths", type=int, default=20)
    args = parser.parse_args()
    try:
        if (args.mode == "r2" and args.db is not None) or \
           (args.mode == "local" and args.db is None):
            raise ReassessmentError("invalid_source_arguments")
        with tempfile.TemporaryDirectory(prefix="v31-c33-reassess-") as tmp:
            local = Path(tmp)/"catalog.sqlite3"
            if args.mode == "r2":
                if not R2State.from_env().restore_to(local):
                    raise ReassessmentError("r2_catalog_missing")
                verify_database(local)
            else:
                path = Path(args.db)
                if not path.is_file() or path.is_symlink():
                    raise ReassessmentError("local_catalog_invalid")
                shutil.copy2(path,local)
            with Catalog(local) as cat:
                result = plan_universal_reassessment(
                    cat,max_paths=args.max_paths)
        print("V31_C33_UNIVERSAL_REASSESSMENT_READONLY_PASS")
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
        return 0
    except Exception as exc:
        print("V31_C33_UNIVERSAL_REASSESSMENT_READONLY_FAILED_"
              + type(exc).__name__)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
