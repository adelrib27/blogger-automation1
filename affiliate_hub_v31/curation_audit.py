"""C18 — auditoria READ-ONLY da curadoria e dos sinais de busca do catálogo.

Categorias oficiais são facetas, não aprovação para artigo. Não contém URLs,
nomes/IDs dos produtos nem dados pessoais nos relatórios. Sem chamadas Shopee.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .catalog import Catalog, host_allowed
from .r2_state import R2State, verify_database

# Categorias com potencial de restrição comercial e/ou revisão adicional.
# A presença nesta lista não condena todo o feed; apenas proíbe a aprovação
# automática de produtos a partir da categoria.
PROTECTED_ROOTS = frozenset((
    "health", "food beverages", "mom baby", "baby kids fashion",
    "hobbies collections",
))


def audit(catalog: Catalog) -> dict:
    stats=catalog.stats()
    row=catalog.db.execute("""
        WITH roots AS (
          SELECT s.product_key,
                 COUNT(DISTINCT s.level1) AS roots,
                 COUNT(DISTINCT s.level1 || char(31) || s.level2) AS branches,
                 COUNT(*) AS sources
          FROM product_source_categories s
          WHERE s.status='matched'
          GROUP BY s.product_key
        )
        SELECT COUNT(*),
               COALESCE(SUM(CASE WHEN roots>1 THEN 1 ELSE 0 END),0),
               COALESCE(SUM(CASE WHEN branches>1 THEN 1 ELSE 0 END),0),
               COALESCE(SUM(CASE WHEN sources>1 THEN 1 ELSE 0 END),0)
        FROM roots
    """).fetchone()
    classified=catalog.db.execute("""
        SELECT COUNT(DISTINCT s.product_key),
               COUNT(DISTINCT CASE WHEN p.moderation='eligible'
                 AND t.status='matched' THEN s.product_key END)
        FROM product_source_categories s
        JOIN products p ON p.product_key=s.product_key
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
        WHERE s.status='matched'
    """).fetchone()
    root_rows=catalog.db.execute("""
        SELECT s.level1,COUNT(DISTINCT s.product_key),
            COUNT(DISTINCT CASE WHEN p.moderation='eligible'
                 AND t.status='matched' THEN s.product_key END)
        FROM product_source_categories s
        JOIN products p ON p.product_key=s.product_key
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
        WHERE s.status='matched'
        GROUP BY s.level1 ORDER BY s.level1
    """).fetchall()
    return {
        "mode":"C18_READ_ONLY_CURATION_AUDIT",
        "catalog":stats,
        "official_category_coverage_products":classified[0] or 0,
        "official_category_editorially_approved":classified[1] or 0,
        "products_with_multiple_source_records":row[3] or 0,
        "conflicting_root_categories_across_sources":row[1] or 0,
        "conflicting_l1_l2_branches_across_sources":row[2] or 0,
        "protected_roots_not_automatically_promotable": [
            {"category":label,"products":count,"previously_approved":approved}
            for label,count,approved in root_rows if label in PROTECTED_ROOTS
        ],
        "source_category_groups":len(root_rows),
        "existing_affiliate_links_preserved":stats["cached_affiliate_links"],
        "product_identifiers_reported":0,
        "publication_calls":0,"graphql_calls":0,"r2_writes":0,
    }


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="v31-c18-curation-") as folder:
            path=Path(folder)/"catalog.sqlite3"
            storage=R2State.from_env()
            if not storage.restore_to(path):
                raise ValueError("catalog_missing")
            verify_database(path)
            with Catalog(path) as cat:
                report=audit(cat)
        print("V31_C18_CURATION_READ_ONLY_PASS")
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception:
        print("V31_C18_CURATION_READ_ONLY_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
