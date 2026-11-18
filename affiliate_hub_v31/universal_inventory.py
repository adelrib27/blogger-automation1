"""C34 — catálogo universal materializado, INDEPENDENTE dos blogs.

Organiza todos os SKUs por hierarquia oficial ou pelo compartimento
SEM_CATEGORIA_OFICIAL. Uma categoria no feed é evidência de busca, NÃO
significa aprovação editorial ou permissão para converter/publicar.

Preserva products, product_taxonomy, affiliate_links e a FTS. Auditoria
agregada, sem impressão de ID, link, título ou credencial.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import sqlite3
import tempfile
from pathlib import Path

from .catalog import Catalog, host_allowed
from .curation_audit import PROTECTED_ROOTS
from .curation_triage import lane_for_record
from .r2_state import R2State, verify_database
from .universal_index_storage import UniversalIndexStorage
from .universal_lexicon import build_lexicon
from .unclassified_review_hints import build_review_path_hints

SCHEMA_VERSION = "v31-universal-inventory-1"
NO_OFFICIAL_CATEGORY = "sem_categoria_oficial"


class UniversalInventoryError(ValueError):
    pass


def create_schema(catalog: Catalog) -> None:
    catalog.db.executescript("""
      CREATE TABLE IF NOT EXISTS v31_universal_inventory (
        product_key TEXT PRIMARY KEY REFERENCES products(product_key),
        source_l1 TEXT NOT NULL, source_l2 TEXT NOT NULL,
        source_l3 TEXT NOT NULL,
        editorial_category TEXT NOT NULL, editorial_niche TEXT NOT NULL,
        review_lane TEXT NOT NULL,
        decision TEXT NOT NULL CHECK(decision IN
          ('approved','review_required','legacy_source_blocked')),
        can_convert INTEGER NOT NULL CHECK(can_convert IN (0,1)),
        schema_version TEXT NOT NULL
      );
      CREATE INDEX IF NOT EXISTS idx_v31_inventory_source
        ON v31_universal_inventory(source_l1,source_l2,source_l3,decision);
      CREATE INDEX IF NOT EXISTS idx_v31_inventory_review
        ON v31_universal_inventory(review_lane,source_l1,source_l2);
      CREATE INDEX IF NOT EXISTS idx_v31_inventory_editorial
        ON v31_universal_inventory(editorial_category,editorial_niche,decision);
    """)


def create_sidecar_schema(db: sqlite3.Connection) -> None:
    """Tabela compacta independente do grande banco de catálogo."""
    db.executescript("""
      CREATE TABLE IF NOT EXISTS v31_universal_inventory (
        product_key TEXT PRIMARY KEY,source_l1 TEXT NOT NULL,
        source_l2 TEXT NOT NULL,source_l3 TEXT NOT NULL,
        editorial_category TEXT NOT NULL,editorial_niche TEXT NOT NULL,
        review_lane TEXT NOT NULL,decision TEXT NOT NULL
          CHECK(decision IN ('approved','review_required','legacy_source_blocked')),
        can_convert INTEGER NOT NULL CHECK(can_convert IN (0,1)),
        schema_version TEXT NOT NULL
      );
    """)


def rebuild_universal_inventory(
    catalog: Catalog, *, sidecar: sqlite3.Connection | None = None,
) -> dict:
    """Mapeia todo o acervo (inclusive review) sem PROMOVER nenhum SKU.

    Nenhuma heurística editorial nova é aplicada aqui. A única origem de
    aprovação é a moderação+taxonomia já aprovada, com veto adicional a
    facetas conflitantes/protegidas.
    """
    facets = catalog.db.execute("""
      SELECT 1 FROM sqlite_master WHERE type='table'
      AND name='product_source_categories'
    """).fetchone()
    if not facets:
        raise UniversalInventoryError("source_category_index_missing")
    before = catalog.stats()
    if sidecar is None:
        create_schema(catalog)
    else:
        create_sidecar_schema(sidecar)
    target = catalog.db if sidecar is None else sidecar
    rows = catalog.db.execute("""
      WITH facets AS (
        SELECT product_key,
          MIN(CASE WHEN status='matched' THEN level1 END) AS l1,
          MIN(CASE WHEN status='matched' THEN level2 END) AS l2,
          MIN(CASE WHEN status='matched' THEN level3 END) AS l3,
          COUNT(*) AS source_count,
          COUNT(DISTINCT CASE WHEN status='matched'
            THEN level1 || char(31) || level2 END) AS branches,
          COUNT(DISTINCT CASE WHEN status='matched' AND level3!=''
            THEN level3 END) AS leaves,
          SUM(CASE WHEN status!='matched' THEN 1 ELSE 0 END) AS bad_sources
        FROM product_source_categories
        GROUP BY product_key
      )
      SELECT p.product_key,p.shop_id,p.item_id,p.title,p.origin_url,p.image_url,
        p.moderation,p.moderation_reason,
        COALESCE(t.status,'review'),COALESCE(t.category,''),
        COALESCE(t.niche,''),COALESCE(f.l1,''),COALESCE(f.l2,''),
        COALESCE(f.l3,''),COALESCE(f.source_count,0),
        COALESCE(f.branches,0),COALESCE(f.leaves,0),
        COALESCE(f.bad_sources,0)
      FROM products p
      LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
      LEFT JOIN facets f ON f.product_key=p.product_key
      ORDER BY p.product_key
    """)
    agg=Counter()
    source_counts=Counter()
    batch=[]
    with target:
        target.execute("DELETE FROM v31_universal_inventory")
        for row in rows:
            (key,shop,item,title,origin,image,moderation,reason,
             tax_status,category,niche,l1,l2,l3,
             source_count,branches,leaves,bad) = row
            unsafe=bad>0 or branches>1 or leaves>1 or l1 in PROTECTED_ROOTS
            historical_approved=moderation=="eligible" and tax_status=="matched"
            if historical_approved and not unsafe and host_allowed(origin) \
                    and str(image).startswith("https://") \
                    and str(shop).isdigit() and str(item).isdigit():
                decision="approved"
                lane="APPROVED"
                can_convert=1
            elif historical_approved:
                decision="legacy_source_blocked"
                lane="SOURCE_PROTECTION" if unsafe else "DATA_REPAIR"
                can_convert=0
            else:
                decision="review_required"
                lane=lane_for_record(
                    title=title,shop_id=shop,origin_url=origin,
                    image_url=image,moderation=moderation,
                    moderation_reason=reason,taxonomy_status=tax_status,
                    source_l1=l1,source_record_count=source_count,
                    branches=branches,leaves=leaves,
                    invalid_sources=bad,
                )
                can_convert=0
            path_l1=l1 if not unsafe and l1 else NO_OFFICIAL_CATEGORY
            path_l2=l2 if path_l1!=NO_OFFICIAL_CATEGORY else ""
            path_l3=l3 if path_l1!=NO_OFFICIAL_CATEGORY else ""
            # Veto de origem não apaga hierarquia do produto; porém jamais
            # expor ramo conflitante/protegido como nicho utilizável.
            if l1 in PROTECTED_ROOTS:
                path_l1=l1
                path_l2=l2
                path_l3=l3
            batch.append((key,path_l1,path_l2,path_l3,category,niche,
                          lane,decision,can_convert,SCHEMA_VERSION))
            agg[decision]+=1
            agg["lanes_"+lane]+=1
            source_counts[path_l1]+=1
            if len(batch)>=1000:
                target.executemany("""
                  INSERT INTO v31_universal_inventory VALUES
                  (?,?,?,?,?,?,?,?,?,?)
                """,batch)
                batch.clear()
        if batch:
            target.executemany("""
              INSERT INTO v31_universal_inventory VALUES
              (?,?,?,?,?,?,?,?,?,?)
            """,batch)
    after=catalog.stats()
    stored=target.execute(
        "SELECT count(*) FROM v31_universal_inventory").fetchone()[0]
    if sidecar is not None:
        target.executescript("""
          CREATE INDEX IF NOT EXISTS idx_v31_inventory_source
            ON v31_universal_inventory(source_l1,source_l2,source_l3,decision);
          CREATE INDEX IF NOT EXISTS idx_v31_inventory_review
            ON v31_universal_inventory(review_lane,source_l1,source_l2);
          CREATE INDEX IF NOT EXISTS idx_v31_inventory_editorial
            ON v31_universal_inventory(editorial_category,editorial_niche,decision);
        """)
    if before!=after or stored!=before["products"] or \
        sum(agg[decision] for decision in
            ("approved","review_required","legacy_source_blocked"))!=stored:
        raise UniversalInventoryError("catalog_preservation_failed")
    if not catalog.integrity() or \
       target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise UniversalInventoryError("sqlite_integrity_failed")
    return {
        "mode":"C34_UNIVERSAL_INVENTORY_REBUILD",
        "products_indexed":stored,
        "existing_product_and_links_counts_preserved":True,
        "inventory_approved_preexisting":agg["approved"],
        "inventory_review_required":agg["review_required"],
        "inventory_legacy_blocked":agg["legacy_source_blocked"],
        "no_official_category":source_counts[NO_OFFICIAL_CATEGORY],
        "official_root_groups":len(source_counts)-int(
            NO_OFFICIAL_CATEGORY in source_counts),
        "review_lane_counts":{
            lane[6:]:count for lane,count in sorted(agg.items())
            if lane.startswith("lanes_")
        },
        "source_classification_is_not_approval":True,
        "new_approvals":0,
        "converted":0,
        "publication_calls":0,
        "shopee_api_calls":0,
        "schema_version":SCHEMA_VERSION,
    }


def run_r2(*,execute:bool=False) -> dict:
    """O banco comercial quase tem 1 GiB; gravar FACETAS EM SIDECAR R2.

    Nunca sobrescreve CURRENT.json nem aumenta o SQLite dos links Shopee.
    """
    with tempfile.TemporaryDirectory(prefix="v31-c34-inventory-") as temp:
        origin=Path(temp)/"catalog.sqlite3"
        if not R2State.from_env().restore_to(origin):
            raise UniversalInventoryError("r2_catalog_missing")
        verify_database(origin)
        index=Path(temp)/"universal_index.sqlite3"
        with Catalog(origin) as catalog:
            initial=catalog.stats()
            with sqlite3.connect(index) as sidecar:
                summary=rebuild_universal_inventory(catalog,sidecar=sidecar)
                lexicon=build_lexicon(catalog.db,sidecar)
                hints=build_review_path_hints(catalog.db,sidecar)
            if catalog.stats()!=initial:
                raise UniversalInventoryError("original_catalog_modified")
        saved=False
        if execute:
            store=UniversalIndexStorage.from_env()
            result=store.save_from(index,product_count=initial["products"])
            if not result.get("index_saved"):
                raise UniversalInventoryError("index_r2_save_failed")
            check=Path(temp)/"restored_index.sqlite3"
            if not store.restore_to(check,
                     expected_product_count=summary["products_indexed"]):
                raise UniversalInventoryError("index_r2_restore_failed")
            saved=True
        return {**summary,"dynamic_title_lexicon":lexicon,
                "unclassified_review_hints":hints,
                "r2_snapshot_saved_and_verified":saved,
                "r2_writes":int(saved),"index_storage":"R2_SIDECAR",
                "core_catalog_untouched":True}


def main()->int:
    parser=argparse.ArgumentParser(description="C34 index universal independente de blog")
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    try:
        report=run_r2(execute=args.execute)
        print("V31_C34_UNIVERSAL_INVENTORY_"+(
            "PERSISTED" if args.execute else "DRYRUN")+"_PASS")
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception as exc:
        print("V31_C34_UNIVERSAL_INVENTORY_FAILED_"+type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
