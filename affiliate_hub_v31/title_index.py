"""C19 — índice FTS5 opcional do acervo Shopee, para buscas em escala.

Armazena somente product_key, title e description do próprio R2.
Nenhum novo produto/link, nenhuma chamada Shopee, publicação ou métricas
comerciais fabricadas. Busca sem FTS continua funcionando como fallback.
"""
from __future__ import annotations

import re
import sqlite3

from .catalog import Catalog


class SearchIndexError(ValueError):
    pass


def has_index(catalog: Catalog) -> bool:
    return bool(catalog.db.execute("""
        SELECT 1 FROM sqlite_master WHERE name='v31_catalog_fts'
          AND type='table'
    """).fetchone())


def rebuild_index(catalog: Catalog) -> dict:
    """Indexa todo o catálogo atual, transação única com verificação."""
    try:
        with catalog.db:
            catalog.db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS v31_catalog_fts
                USING fts5(product_key UNINDEXED, title, description,
                  tokenize='unicode61 remove_diacritics 2')
            """)
            catalog.db.execute("DELETE FROM v31_catalog_fts")
            catalog.db.execute("""
                INSERT INTO v31_catalog_fts(product_key,title,description)
                SELECT product_key,title,description FROM products ORDER BY product_key
            """)
            rows,distinct=catalog.db.execute("""
                SELECT COUNT(*),COUNT(DISTINCT product_key)
                FROM v31_catalog_fts
            """).fetchone()
            products=catalog.db.execute(
                "SELECT COUNT(*) FROM products"
            ).fetchone()[0]
            if rows!=products or distinct!=products:
                raise SearchIndexError("fts_population_mismatch")
    except sqlite3.Error:
        raise SearchIndexError("fts_unavailable_or_build_failed") from None
    return {
        "mode":"FTS5_INDEX_BUILT",
        "index_rows":rows,
        "products_indexed":products,
        "unique_indexed_products":distinct,
        "graphql_calls":0,
        "publication_calls":0,
    }


def safe_match_expression(terms: tuple[str,...]) -> str | None:
    if (not terms or len(terms)>8 or any(not isinstance(term,str)
            or not re.fullmatch(r"[a-z0-9]{3,32}",term) for term in terms)):
        return None
    return " OR ".join('"'+term+'"' for term in terms)


def fts_condition(catalog: Catalog, terms: tuple[str,...]) -> tuple[str,list[str]]:
    """Condição SQL e parâmetros para pré-filtro, ou fallback sem índice.

    A pontuação final é sempre calculada pelo seletor editorial. Não se
    autoriza SKU diferente só porque o FTS retornou uma correspondência.
    """
    expression=safe_match_expression(terms)
    if expression is None or not has_index(catalog):
        return "",[]
    return ("""p.product_key IN (
                SELECT product_key FROM v31_catalog_fts
                WHERE v31_catalog_fts MATCH ?
              )""",[expression])
