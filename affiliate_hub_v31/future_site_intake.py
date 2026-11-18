"""C20 — entrada de futuros blogs usando catálogo universal, somente SAFE.

Esta interface é para o orquestrador de criação/edição consultar DEPOIS que
o usuário indicar o assunto, nunca para inventar blogs ou categorias.
O resultado mantém dois compartimentos: aprovados preexistentes e fila de
revisão. Não aprova, converte, reserva, cria blog, escreve R2 ou publica.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import tempfile
from pathlib import Path

from .catalog import Catalog
from .curation_audit import PROTECTED_ROOTS
from .product_discovery import discover, suggest_category_paths
from .r2_state import R2State, verify_database


class IntakeError(ValueError):
    pass


def _review_flags(catalog: Catalog, candidate: dict) -> list[str]:
    row = catalog.db.execute("""
        SELECT p.moderation, COALESCE(t.status,'review')
        FROM products p LEFT JOIN product_taxonomy t
        ON t.product_key=p.product_key WHERE p.product_key=?
    """, (candidate["product_key"],)).fetchone()
    if row is None:
        raise IntakeError("product_disappeared_during_preview")
    moderation, taxonomy = row
    flags = []
    if candidate["source_category_l1"] in PROTECTED_ROOTS:
        flags.append("PROTECTED_SOURCE_ROOT")
    if not candidate["source_category_l1"]:
        flags.append("NO_OFFICIAL_SOURCE_FACET")
    if moderation != "eligible":
        flags.append("MODERATION_REQUIRED")
    if taxonomy != "matched":
        flags.append("EDITORIAL_TAXONOMY_UNMATCHED")
    return flags or ["MANUAL_REVIEW_REQUIRED"]


def preview_future_site(
    catalog: Catalog, *, topic: str, platform: str = "unspecified",
    campaign: str | None = None, category: str | None = None,
    subcategory: str | None = None, approved_limit: int = 12,
    review_limit: int = 12, max_per_shop: int = 1
) -> dict:
    """Consulta contextual. Uma campanha só pode receber os SEUS links reais.

    URL pré-convertida de outro site nunca é copiada para a futura campanha.
    O resumo de CI deve usar summarize_preview(), não a seleção bruta.
    """
    if platform not in ("unspecified", "blogger", "wordpress"):
        raise IntakeError("platform_not_supported")
    if not isinstance(approved_limit, int) or not 1 <= approved_limit <= 24:
        raise IntakeError("approved_limit_invalid")
    if not isinstance(review_limit, int) or not 1 <= review_limit <= 24:
        raise IntakeError("review_limit_invalid")

    paths = suggest_category_paths(catalog, topic=topic, limit=8)
    kwargs = dict(topic=topic, category=category, subcategory=subcategory,
                  campaign=campaign, max_per_shop=max_per_shop)
    approved = discover(catalog, limit=approved_limit, **kwargs)
    pending = discover(catalog, limit=review_limit, include_review=True,
                       review_only=True, **kwargs)

    if any(c["curation"] != "approved" or c["can_publish"] for c in approved):
        raise IntakeError("approved_pool_gate_failed")
    if any(c["curation"] != "review_required" or c["affiliate_url"] is not None
           or c["can_publish"] for c in pending):
        raise IntakeError("review_pool_gate_failed")

    queue = [{**item, "review_reasons": _review_flags(catalog, item)}
             for item in pending]
    return {
        "mode": "C20_SAFE_PREVIEW_ONLY",
        "platform": platform,
        "topic": topic,
        "campaign_explicitly_selected": campaign is not None,
        "category_paths": paths,
        "approved_candidates": approved,
        "review_queue": queue,
        "requires_campaign_for_conversion": campaign is None,
        "requires_editorial_and_platform_gates": True,
        "can_publish": False,
        "site_creation_calls": 0,
        "affiliate_conversion_calls": 0,
        "publication_calls": 0,
        "r2_writes": 0,
    }


def summarize_preview(result: dict) -> dict:
    """Somente contagens e flags, sem links, títulos, chaves ou termos do usuário."""
    if result.get("mode") != "C20_SAFE_PREVIEW_ONLY":
        raise IntakeError("not_a_safe_preview")
    approved = result["approved_candidates"]
    queue = result["review_queue"]
    flags = Counter(flag for item in queue for flag in item["review_reasons"])
    return {
        "mode": result["mode"],
        "platform": result["platform"],
        "campaign_explicitly_selected": result["campaign_explicitly_selected"],
        "suggested_category_paths": len(result["category_paths"]),
        "protected_category_paths": sum(
            bool(p["manual_review_required_for_root"]) for p in result["category_paths"]),
        "approved_candidate_count": len(approved),
        "review_candidate_count": len(queue),
        "verified_links_for_selected_campaign": sum(
            c["affiliate_status"] == "verified_for_campaign" for c in approved),
        "candidates_requiring_conversion": sum(
            c["affiliate_status"] == "requires_conversion" for c in approved),
        "review_reason_counts": dict(sorted(flags.items())),
        "requires_editorial_and_platform_gates": True,
        "can_publish": False,
        "site_creation_calls": 0, "affiliate_conversion_calls": 0,
        "publication_calls": 0, "r2_writes": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V31 C20 — prévia SAFE para novo blog")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--platform", choices=["unspecified", "blogger", "wordpress"],
                        default="unspecified")
    parser.add_argument("--campaign", default=None)
    parser.add_argument("--mode", choices=["local", "r2"], required=True)
    parser.add_argument("--db")
    args = parser.parse_args()
    try:
        if args.mode == "local":
            if not args.db:
                raise IntakeError("local_database_required")
            with Catalog(Path(args.db)) as cat:
                report = summarize_preview(preview_future_site(
                    cat, topic=args.topic, platform=args.platform,
                    campaign=args.campaign))
        else:
            if args.db:
                raise IntakeError("r2_mode_cannot_accept_local_db")
            with tempfile.TemporaryDirectory(prefix="v31-c20-readonly-") as folder:
                path = Path(folder) / "snapshot.sqlite3"
                state = R2State.from_env()
                if not state.restore_to(path):
                    raise IntakeError("catalog_not_found")
                verify_database(path)
                with Catalog(path) as cat:
                    report = summarize_preview(preview_future_site(
                        cat, topic=args.topic, platform=args.platform,
                        campaign=args.campaign))
        print("V31_C20_FUTURE_SITE_READONLY_PASS")
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print("V31_C20_FUTURE_SITE_READONLY_FAILED_" + type(exc).__name__)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
