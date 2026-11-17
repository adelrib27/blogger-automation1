"""C21 — gate conservador para consumir facetas oficiais Shopee.

Aprovação editorial histórica NÃO ignora status conflict/review na fonte,
categorias protegidas nem divergências entre feeds. Sem facetas oficiais,
mantém compatibilidade com produto legado aprovado por outros gates.

Os consumidores chamam create_source_category_schema() uma vez antes da
consulta. Este gate é read-only e não altera moderação ou links antigos.
"""
from __future__ import annotations

from .curation_audit import PROTECTED_ROOTS


def source_safe_for_use(catalog, product_key: str) -> bool:
    """Retorna False se qualquer fonte registrada tornar o SKU inseguro.

    A tabela product_source_categories deve existir (garantida pelo caller).
    Facetas ausentes não significam autorização: moderação/taxonomia
    continuam requisitos independentes no consumidor.
    """
    if not isinstance(product_key, str) or not product_key:
        return False
    protected = tuple(sorted(PROTECTED_ROOTS))
    placeholders = ",".join("?" for _ in protected)
    sql = """
        SELECT
          COUNT(DISTINCT CASE WHEN status='matched' THEN
            level1 || char(31) || level2 END) AS branches,
          COUNT(DISTINCT CASE WHEN status='matched' AND level3!=''
            THEN level3 END) AS leaves,
          COALESCE(SUM(CASE WHEN status!='matched' OR level1 IN (""" + \
          placeholders + """) THEN 1 ELSE 0 END),0) AS bad
        FROM product_source_categories
        WHERE product_key=?
    """
    branches, leaves, bad = catalog.db.execute(
        sql, (*protected, product_key)
    ).fetchone()
    return branches <= 1 and leaves <= 1 and bad == 0
