"""C16 — enriquecer a biblioteca R2 com categorias oficiais sem mexer nos posts.

Só escreve a nova tabela product_source_categories. O conteúdo das tabelas
products, product_taxonomy e affiliate_links é verificado por hash antes e
depois, assim como após restaurar o snapshot salvo. Execução padrão: dry-run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

from .catalog import Catalog
from .feed_download import check_feed_url, download_feed
from .r2_state import R2State, verify_database
from .source_category_index import import_source_categories, source_inventory


class EnrichmentError(ValueError):
    pass


def protected_fingerprint(catalog: Catalog) -> str:
    sha=hashlib.sha256()
    for table,keys in (
        ("products","product_key"),
        ("product_taxonomy","product_key"),
        ("affiliate_links","product_key,campaign"),
    ):
        sha.update(table.encode("ascii"))
        for row in catalog.db.execute("SELECT * FROM "+table+" ORDER BY "+keys):
            sha.update(json.dumps(row,ensure_ascii=False,
                                  separators=(",",":")).encode("utf-8"))
            sha.update(b"\n")
    return sha.hexdigest()


def enrich(storage: R2State, files: tuple[Path,Path], *, execute: bool=False,
           fail_if_feed_has_new_products: bool=True) -> dict:
    with tempfile.TemporaryDirectory(prefix="v31-c16-enrich-") as td:
        file=Path(td)/"catalog.sqlite3"
        if not storage.restore_to(file):
            raise EnrichmentError("catalog_missing")
        verify_database(file)
        with Catalog(file) as cat:
            original_stats=cat.stats()
            original_hash=protected_fingerprint(cat)
            source_results=[
                import_source_categories(cat,files[0],"feed1"),
                import_source_categories(cat,files[1],"feed2")
            ]
            inventory=source_inventory(cat)
            total_missing=sum(r["not_in_current_catalog"] for r in source_results)
            if cat.stats()!=original_stats:
                raise EnrichmentError("original_catalog_counts_changed")
            if protected_fingerprint(cat)!=original_hash:
                raise EnrichmentError("protected_catalog_data_changed")
            if not cat.integrity():
                raise EnrichmentError("sqlite_integrity_failed")
            if (execute and fail_if_feed_has_new_products and total_missing):
                raise EnrichmentError("feed_has_new_products_resynchronize_first")
            if not inventory["products_with_official_source_categories"]:
                raise EnrichmentError("source_category_index_empty")
        saved=False
        pending=False
        if execute:
            status=storage.save_from(file)
            if not status.get("state_saved"):
                raise EnrichmentError("r2_save_failed")
            saved=True
            pending=bool(status.get("retention_pending",False))
            recovered=Path(td)/"recovered.sqlite3"
            if not storage.restore_to(recovered):
                raise EnrichmentError("r2_restore_failed")
            verify_database(recovered)
            with Catalog(recovered) as cat:
                if cat.stats()!=original_stats:
                    raise EnrichmentError("r2_protected_counts_changed")
                if protected_fingerprint(cat)!=original_hash:
                    raise EnrichmentError("r2_protected_fingerprint_changed")
                recovered_inventory=source_inventory(cat)
                if recovered_inventory!=inventory:
                    raise EnrichmentError("r2_category_inventory_changed")
        return {
            "mode":"EXECUTE" if execute else "DRY_RUN",
            "feeds":[{"source":r["source"],"rows":r["rows"],
                      "levels_present":r["levels_present"],
                      "new_category_records":r["new_category_records"],
                      "duplicates_same_category":r["duplicates_same_category"],
                      "category_conflicts":r["category_conflicts"],
                      "without_level1":r["without_level1"],
                      "not_in_current_catalog":r["not_in_current_catalog"]}
                     for r in source_results],
            "original_products_preserved":original_stats["products"],
            "original_affiliate_links_preserved":original_stats["cached_affiliate_links"],
            "original_approved_items_preserved":original_stats["eligible"],
            "category_index":inventory,
            "snapshot_saved_and_restored":saved,
            "retention_pending":pending,
            "graphql_requests":0,"publication_calls":0,
        }


def run(*,execute:bool=False)->dict:
    urls=(os.environ.get("V31_EDITORIAL_DATAFEED_URL_1",""),
          os.environ.get("V31_EDITORIAL_DATAFEED_URL_2",""))
    for url in urls:
        check_feed_url(url)
    storage=R2State.from_env()
    with tempfile.TemporaryDirectory(prefix="v31-c16-feed-") as td:
        folder=Path(td)
        files=(folder/"feed1.csv",folder/"feed2.csv")
        for url,path in zip(urls,files):
            download_feed(url,path)
        return enrich(storage,files,execute=execute)


def main()->int:
    parser=argparse.ArgumentParser(
        description="V31: indexar categorias oficiais dos CSVs sem publicar"
    )
    parser.add_argument("--execute",action="store_true",
                        help="Só com esta opção salva tabela de categorias no R2")
    args=parser.parse_args()
    try:
        result=run(execute=args.execute)
        print("V31_C16_SOURCE_CATEGORIES_"+("EXECUTE" if args.execute else "DRY_RUN")+"_PASS")
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception:
        print("V31_C16_SOURCE_CATEGORIES_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
