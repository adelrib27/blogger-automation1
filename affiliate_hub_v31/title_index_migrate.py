"""C19 — construir índice textual FTS5 no snapshot R2, preservando tudo.

Comparação EXATA dos resultados de ranking e sugestões de categorias antes/
depois em uma amostra real. Salvar só após hashes e equivalência de seleção.
Dry-run por padrão. Nenhum GraphQL, conversão, post ou Pinterest.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from time import perf_counter

from .catalog import Catalog
from .product_discovery import discover,suggest_category_paths
from .r2_state import R2State,verify_database
from .source_enrichment import protected_fingerprint
from .title_index import has_index,rebuild_index


SCENARIOS=(
    ("Air Fryer","Home Appliances"),
    ("Guarda Roupa","Home & Living"),
    ("Freio","Spare Parts and Accessories for Vehicles"),
)


class SearchMigrationError(ValueError):
    pass


def sample_selections(catalog: Catalog) -> list[tuple[list[dict],list[dict]]]:
    results=[]
    for topic,category in SCENARIOS:
        ranked=discover(catalog,topic=topic,category=category,
                        campaign="futuresitec19",limit=12,max_per_shop=1,
                        include_review=False)
        paths=suggest_category_paths(catalog,topic=topic,limit=5)
        if not ranked or not paths:
            raise SearchMigrationError("search_contract_missing")
        results.append((ranked,paths))
    return results


def migrate(storage: R2State, *, execute: bool=False) -> dict:
    with tempfile.TemporaryDirectory(prefix="v31-c19-index-") as directory:
        db=Path(directory)/"catalog.sqlite3"
        if not storage.restore_to(db):
            raise SearchMigrationError("catalog_missing")
        verify_database(db)
        with Catalog(db) as catalog:
            initial_stats=catalog.stats()
            prior_hash=protected_fingerprint(catalog)
            index_already_present=has_index(catalog)
            start=perf_counter()
            original_results=sample_selections(catalog)
            scan_ms=round((perf_counter()-start)*1000,2)
            indexed=rebuild_index(catalog)
            start=perf_counter()
            indexed_results=sample_selections(catalog)
            index_ms=round((perf_counter()-start)*1000,2)
            if original_results!=indexed_results:
                raise SearchMigrationError("search_rank_or_category_changed")
            if catalog.stats()!=initial_stats or not catalog.integrity():
                raise SearchMigrationError("catalog_modified_or_invalid")
            if protected_fingerprint(catalog)!=prior_hash:
                raise SearchMigrationError("protected_product_link_data_modified")
        saved=False
        pending=False
        if execute:
            result=storage.save_from(db)
            if not result.get("state_saved"):
                raise SearchMigrationError("r2_snapshot_not_saved")
            saved=True
            pending=bool(result.get("retention_pending",False))
            restored=Path(directory)/"restored.sqlite3"
            if not storage.restore_to(restored):
                raise SearchMigrationError("r2_snapshot_not_restored")
            verify_database(restored)
            with Catalog(restored) as catalog:
                if (not has_index(catalog) or
                    catalog.stats()!=initial_stats or
                    not catalog.integrity() or
                    protected_fingerprint(catalog)!=prior_hash or
                    catalog.db.execute(
                        "SELECT COUNT(*) FROM v31_catalog_fts"
                    ).fetchone()[0]!=initial_stats["products"] or
                    sample_selections(catalog)!=original_results):
                    raise SearchMigrationError("r2_restored_index_integrity_failed")
        return {
            "mode":"FTS5_EXECUTE" if execute else "FTS5_DRY_RUN",
            "search_index_already_present":index_already_present,
            "indexed_products":indexed["index_rows"],
            "catalog_products_unchanged":initial_stats["products"],
            "affiliate_links_unchanged":initial_stats["cached_affiliate_links"],
            "previously_approved_products_unchanged":initial_stats["eligible"],
            "sample_queries":len(SCENARIOS),
            "ranked_results_exactly_equal":True,
            "unindexed_sample_ms":scan_ms,
            "indexed_sample_ms":index_ms,
            "timings_note":"single run; not throughput guarantee",
            "r2_snapshot_saved_and_restored":saved,
            "retention_pending":pending,
            "graphql_calls":0,"publication_calls":0,"pinterest_calls":0,
        }


def main()->int:
    p=argparse.ArgumentParser(description="C19 migrar FTS5 R2 sem posts")
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    try:
        report=migrate(R2State.from_env(),execute=args.execute)
        print("V31_C19_INDEX_"+("EXECUTE" if args.execute else "DRY_RUN")+"_PASS")
        print(json.dumps(report,sort_keys=True))
        return 0
    except Exception:
        print("V31_C19_INDEX_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
