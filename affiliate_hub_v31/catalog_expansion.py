"""C17 — Expansão APENAS ADITIVA da biblioteca histórica Shopee.

Os dois feeds oficiais podem renovar quase todos os produtos. NÃO substituir
o catálogo antigo: preservar produtos, moderação, taxonomia e links anteriores.
Novos produtos são acrescentados, e as categorias oficiais L1/L2/L3
são indexadas para o conjunto atualmente presente nos feeds.
Dry-run por padrão. Não publica artigos nem gera/converte links.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path

from .catalog import Catalog, classify, fields, ids_from_url, normalized, utc_now
from .feed_download import check_feed_url, download_feed
from .r2_state import R2State, verify_database
from .source_category_index import import_source_categories, source_inventory
from .taxonomy import classify_title

MAX_FEED_ROWS = 250_000


class CatalogExpansionError(ValueError):
    pass


def install_original_keys(catalog: Catalog, old_keys: list[str] | None=None) -> list[str]:
    catalog.db.execute("DROP TABLE IF EXISTS temp.v31_original_keys")
    catalog.db.execute("""
        CREATE TEMP TABLE v31_original_keys(product_key TEXT PRIMARY KEY)
    """)
    if old_keys is None:
        old_keys=[r[0] for r in catalog.db.execute(
            "SELECT product_key FROM products ORDER BY product_key")]
    catalog.db.executemany(
        "INSERT INTO temp.v31_original_keys(product_key) VALUES(?)",
        ((k,) for k in old_keys))
    return old_keys


def fingerprint_original(catalog: Catalog) -> str:
    sha=hashlib.sha256()
    tables=(
        ("products","p"),
        ("product_taxonomy","t"),
        ("affiliate_links","l"),
    )
    for table,alias in tables:
        sha.update(table.encode("ascii"))
        keys="orig.product_key" if table!="affiliate_links" else "orig.product_key,l.campaign"
        sql=(
            f"SELECT {alias}.* FROM {table} {alias} "
            f"JOIN temp.v31_original_keys orig ON orig.product_key={alias}.product_key "
            f"ORDER BY {keys}"
        )
        for row in catalog.db.execute(sql):
            sha.update(json.dumps(row,ensure_ascii=False,
                                  separators=(",",":")).encode("utf-8"))
            sha.update(b"\n")
    return sha.hexdigest()


def append_feed(catalog: Catalog, path: Path | str, source: str) -> dict:
    if source not in ("feed1","feed2"):
        raise CatalogExpansionError("feed_source_invalid")
    report=Counter()
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        sample=f.read(8192)
        f.seek(0)
        try:
            dialect=csv.Sniffer().sniff(sample,delimiters=",;\t|")
        except csv.Error:
            dialect=csv.excel
        reader=csv.DictReader(f,delimiter=dialect.delimiter,
                              quotechar='"',doublequote=True,strict=True)
        if not reader.fieldnames or len(reader.fieldnames)>128:
            raise CatalogExpansionError("feed_header_invalid")
        if not any(normalized(v) in (
            "productname","productname","title","nome","nomeproduto","itemname"
        ) for v in reader.fieldnames):
            raise CatalogExpansionError("feed_title_missing")
        if not any(normalized(v) in (
            "productlink","producturl","itemurl","itemlink","originurl","url",
            "linkproduto"
        ) for v in reader.fieldnames):
            raise CatalogExpansionError("feed_product_url_missing")
        with catalog.db:
            for raw in reader:
                report["rows"]+=1
                if report["rows"]>MAX_FEED_ROWS:
                    raise CatalogExpansionError("feed_too_large")
                if None in raw or any(v is None for v in raw.values()):
                    raise CatalogExpansionError("csv_row_columns_invalid")
                data=fields(raw)
                key,moderation,reason=classify(data)
                if catalog.db.execute(
                    "SELECT 1 FROM products WHERE product_key=?",(key,)
                ).fetchone():
                    report["already_in_library"]+=1
                    continue
                route=classify_title(data["title"])
                if route.status!="matched":
                    moderation="review"
                    reason=",".join(filter(None,(reason,"taxonomy_"+route.reason)))
                shop,item=data["shop"],data["item"]
                if not shop or not item:
                    a,b=ids_from_url(data["url"])
                    shop,item=shop or a,item or b
                catalog.db.execute("""
                    INSERT INTO products
                    (product_key,shop_id,item_id,title,description,origin_url,
                     image_url,moderation,moderation_reason,first_source,last_seen_utc)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,(key,shop,item,data["title"],data["description"],data["url"],
                     data["image"],moderation,reason,source,utc_now()))
                catalog.db.execute("""
                    INSERT INTO product_taxonomy
                    (product_key,category,niche,status,reason,version)
                    VALUES(?,?,?,?,?,?)
                """,(key,route.category,route.niche,route.status,
                     route.reason,route.version))
                report["new_products"]+=1
                report["new_editorially_approved" if moderation=="eligible"
                       else "new_pending_review"]+=1
    return {"source":source,**{key:report[key] for key in (
        "rows","already_in_library","new_products",
        "new_editorially_approved","new_pending_review"
    )}}


def expand(storage: R2State, files: tuple[Path,Path], *,
           execute: bool=False) -> dict:
    with tempfile.TemporaryDirectory(prefix="v31-c17-expand-") as td:
        local=Path(td)/"catalog.sqlite3"
        if not storage.restore_to(local):
            raise CatalogExpansionError("catalog_missing")
        verify_database(local)
        with Catalog(local) as cat:
            old_stats=cat.stats()
            keys=install_original_keys(cat)
            before_hash=fingerprint_original(cat)
            outputs=[
                append_feed(cat,files[0],"feed1"),
                append_feed(cat,files[1],"feed2"),
            ]
            source_reports=[
                import_source_categories(cat,files[0],"feed1"),
                import_source_categories(cat,files[1],"feed2"),
            ]
            categories=source_inventory(cat)
            after_stats=cat.stats()
            expected_new=sum(x["new_products"] for x in outputs)
            expected_approved=sum(x["new_editorially_approved"] for x in outputs)
            if after_stats["products"]!=old_stats["products"]+expected_new:
                raise CatalogExpansionError("product_count_mismatch")
            if after_stats["eligible"]!=old_stats["eligible"]+expected_approved:
                raise CatalogExpansionError("editorial_approval_count_mismatch")
            if after_stats["cached_affiliate_links"]!=old_stats["cached_affiliate_links"]:
                raise CatalogExpansionError("affiliate_link_count_changed")
            if fingerprint_original(cat)!=before_hash:
                raise CatalogExpansionError("original_data_modified")
            if (not categories["products_with_official_source_categories"] or
                not cat.integrity()):
                raise CatalogExpansionError("category_index_or_sqlite_integrity_failed")
        saved=False
        pending=False
        if execute:
            result=storage.save_from(local)
            if not result.get("state_saved"):
                raise CatalogExpansionError("r2_snapshot_failed")
            saved=True
            pending=bool(result.get("retention_pending",False))
            recovered=Path(td)/"verified.sqlite3"
            if not storage.restore_to(recovered):
                raise CatalogExpansionError("r2_snapshot_restore_failed")
            verify_database(recovered)
            with Catalog(recovered) as cat:
                install_original_keys(cat,keys)
                if fingerprint_original(cat)!=before_hash:
                    raise CatalogExpansionError("restored_original_data_modified")
                if cat.stats()!=after_stats:
                    raise CatalogExpansionError("restored_catalog_counts_invalid")
                check=source_inventory(cat)
                if check!=categories:
                    raise CatalogExpansionError("restored_source_categories_invalid")
        return {
            "mode":"EXPAND_EXECUTE" if execute else "EXPAND_DRY_RUN",
            "previous_catalog":old_stats,
            "current_catalog":after_stats,
            "feeds":outputs,
            "official_source_category_import":[
                {"source":x["source"],"rows":x["rows"],
                 "levels_present":x["levels_present"],
                 "new_category_records":x["new_category_records"],
                 "category_conflicts":x["category_conflicts"],
                 "not_in_current_catalog":x["not_in_current_catalog"]}
                for x in source_reports
            ],
            "source_categories":categories,
            "existing_products_links_and_review_states_preserved":True,
            "snapshot_saved_and_restored":saved,
            "retention_pending":pending,
            "graphql_calls":0,"r2_only_writes":int(saved),
            "publication_calls":0,
        }


def run(*,execute:bool=False)->dict:
    urls=(os.environ.get("V31_EDITORIAL_DATAFEED_URL_1",""),
          os.environ.get("V31_EDITORIAL_DATAFEED_URL_2",""))
    for u in urls:
        check_feed_url(u)
    storage=R2State.from_env()
    with tempfile.TemporaryDirectory(prefix="v31-c17-feeds-") as folder:
        files=(Path(folder)/"feed1.csv",Path(folder)/"feed2.csv")
        for url,path in zip(urls,files):
            download_feed(url,path)
        return expand(storage,files,execute=execute)


def main()->int:
    p=argparse.ArgumentParser(description="Expandir catálogo Shopee com categorias oficiais")
    p.add_argument("--execute",action="store_true",
                   help="Sem flag, 0 writes R2; com flag, salvar snapshot verificado")
    args=p.parse_args()
    try:
        report=run(execute=args.execute)
        print("V31_C17_CATALOG_"+("EXECUTE" if args.execute else "DRY_RUN")+"_PASS")
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 0
    except Exception:
        print("V31_C17_CATALOG_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
