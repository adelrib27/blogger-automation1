"""V31 — Pré-conversão de uma biblioteca UNIVERSAL, sem blogs predefinidos.

Separação intencional:
- o catálogo CSV tem produtos de qualquer assunto, inclusive futuros blogs;
- o pool pode pré-converter itens aprovados para uma campanha de biblioteca
  explicitamente configurada, INDEPENDENTE de site/SEO/artigos;
- links de um pool NÃO são copiados para outra campanha. Na criação de um
  blog com sua própria campanha, converte-se o item SELECIONADO nessa campanha.

Não gera conteúdo, não publica, não altera páginas de loja, nem escolhe temas
de futuros blogs. Conversões reais só ocorrem em --execute com orçamento 1–3.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path

from .catalog import Catalog
from .converter import ConversionError, convert_one, valid_campaign
from .r2_state import R2State, verify_database
from .source_category_index import create_source_category_schema
from .source_policy_gate import source_safe_for_use


class LibraryPoolError(ValueError):
    """Erros sanitizados, sem URLs ou produtos em logs."""


MAX_MUTATIONS = 3


def library_candidates(catalog: Catalog, campaign: str, limit: int = 3,
                       *, rotation: int = 0) -> list[str]:
    """Intercala TODOS os nichos elegíveis, sem conhecer blogs existentes.

    Não seleciona produto por histórico de publicação, palavras-chave de um
    blog ou seu perfil shadow. A rotação muda o nicho inicial, não decide
    qual futuro tema será solicitado pelo usuário.
    """
    valid_campaign(campaign)
    if not isinstance(limit, int) or not 1 <= limit <= MAX_MUTATIONS:
        raise LibraryPoolError("budget_invalid")
    if not isinstance(rotation, int) or rotation < 0:
        raise LibraryPoolError("rotation_invalid")
    rows = catalog.db.execute("""
        SELECT p.product_key, t.category, t.niche
        FROM products p
        JOIN product_taxonomy t ON t.product_key=p.product_key
        LEFT JOIN affiliate_links l
          ON l.product_key=p.product_key AND l.campaign=?
        WHERE p.moderation='eligible' AND t.status='matched'
          AND l.product_key IS NULL
        ORDER BY t.category,t.niche,p.product_key
    """, (campaign,)).fetchall()
    create_source_category_schema(catalog)
    pools: dict[tuple[str, str], list[str]] = defaultdict(list)
    for key, category, niche in rows:
        if source_safe_for_use(catalog,key):
            pools[(category, niche)].append(key)
    groups = sorted(pools)
    if not groups:
        return []
    offset = rotation % len(groups)
    groups = groups[offset:] + groups[:offset]
    selected = []
    index = 0
    while len(selected) < limit:
        progressed = False
        for group in groups:
            products = pools[group]
            if index < len(products):
                selected.append(products[index])
                progressed = True
            if len(selected) >= limit:
                break
        if not progressed:
            break
        index += 1
    return selected


def coverage(catalog: Catalog, campaign: str) -> dict:
    """Estatísticas do acervo, não um filtro para os blogs já criados."""
    valid_campaign(campaign)
    stats = catalog.stats()
    counts = catalog.db.execute("""
        SELECT COUNT(DISTINCT p.product_key),
               COUNT(DISTINCT t.category || '/' || t.niche)
        FROM products p JOIN product_taxonomy t
            ON t.product_key=p.product_key
        WHERE p.moderation='eligible' AND t.status='matched'
    """).fetchone()
    converted = catalog.db.execute("""
        SELECT COUNT(*) FROM affiliate_links WHERE campaign=?
    """, (campaign,)).fetchone()[0]
    return {
        "products_in_universal_catalog": stats["products"],
        "products_with_current_approved_taxonomy": counts[0],
        "current_taxonomy_groups": counts[1],
        "products_pending_or_under_review": stats["review"],
        "pool_campaign_links_converted": converted,
        "blog_profiles_used_for_selection": 0,
        "scope": "ALL_APPROVED_CATALOG_CATEGORIES_NOT_JUST_EXISTING_BLOGS",
    }


def replenish_library(storage: R2State, campaign: str, *, budget: int = 3,
                      execute: bool = False, rotation: int | None = None,
                      app_id: str = "", app_secret: str = "") -> dict:
    """Uma execução de baixo volume: 0 Shopee em dry-run, até 3 em --execute."""
    valid_campaign(campaign)
    if not isinstance(budget,int) or not 1 <= budget <= MAX_MUTATIONS:
        raise LibraryPoolError("budget_invalid")
    if execute and (not app_id.strip() or not app_secret.strip()):
        raise LibraryPoolError("credentials_missing")
    day=date.today().toordinal() if rotation is None else rotation
    with tempfile.TemporaryDirectory(prefix="v31-library-") as td:
        state=Path(td)/"catalog.sqlite3"
        if not storage.restore_to(state):
            raise LibraryPoolError("r2_state_missing")
        verify_database(state)
        converted=0
        attempts=0
        interrupted=False
        selected=[]
        with Catalog(state) as catalog:
            before=coverage(catalog,campaign)
            selected=library_candidates(catalog,campaign,budget,rotation=day)
            if execute:
                for key in selected:
                    attempts+=1
                    try:
                        _url,created=convert_one(catalog,key,campaign,
                                                 app_id,app_secret)
                    except ConversionError:
                        interrupted=True
                        break
                    converted+=int(created)
            if not catalog.integrity():
                raise LibraryPoolError("catalog_integrity_failed")
        saved=False
        pending=False
        if execute and converted:
            saved_result=storage.save_from(state)
            if not saved_result.get("state_saved"):
                raise LibraryPoolError("snapshot_not_saved")
            saved=True
            pending=bool(saved_result.get("retention_pending",False))
            verify=Path(td)/"verified.sqlite3"
            if not storage.restore_to(verify):
                raise LibraryPoolError("snapshot_not_restored")
            with Catalog(verify) as restored:
                after=coverage(restored,campaign)
                if (after["pool_campaign_links_converted"] <
                        before["pool_campaign_links_converted"]+converted or
                        not restored.integrity()):
                    raise LibraryPoolError("pool_persistence_mismatch")
        return {
            "mode":"LIBRARY_POOL_EXECUTE" if execute else "LIBRARY_POOL_DRY_RUN",
            "catalog":before,
            "planned":len(selected),
            "attempts":attempts,
            "converted":converted,
            "api_interrupted":interrupted,
            "r2_snapshot_saved":saved,
            "retention_pending":pending,
            "blog_creation_calls":0,
            "publication_calls":0,
            "links_copied_across_campaigns":0,
        }


def main() -> int:
    p=argparse.ArgumentParser(
        description="Biblioteca V31: conversor abrangente sem pré-definir blogs"
    )
    p.add_argument("--budget",type=int,default=3)
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    try:
        campaign=os.environ.get("V31_EDITORIAL_LIBRARY_CAMPAIGN","").strip()
        if not campaign:
            raise LibraryPoolError("library_campaign_not_configured")
        summary=replenish_library(
            R2State.from_env(),campaign,budget=args.budget,
            execute=args.execute,
            app_id=os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID",""),
            app_secret=os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET","")
        )
        print("V31_LIBRARY_POOL_PASS" if not summary["api_interrupted"]
              else "V31_LIBRARY_POOL_API_INTERRUPTED")
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        return 4 if summary["api_interrupted"] else 0
    except Exception:
        print("V31_LIBRARY_POOL_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
