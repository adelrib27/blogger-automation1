"""C15 — Índice universal por categoria e nicho, sem conhecer blogs futuros.

Consome o catálogo CSV/R2 já deduplicado e taxonomizado.
- Cada produto aparece em uma categoria/nicho aprovado ou em revisão.
- O blog ainda não existe ao indexar produtos.
- A decisão de artigo ocorre somente após o pedido de criação do blog.
- URL de produto NÃO é URL de afiliado. Links só valem na própria campanha.
- Leitura apenas: sem API Shopee, conversão, geração, Pinterest ou publicação.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

from .catalog import Catalog, host_allowed
from .converter import valid_campaign
from .r2_state import R2State, verify_database
from .taxonomy import normalize

UNCLASSIFIED_CATEGORY = "revisao_pendente"
UNCLASSIFIED_NICHE = "nao_classificado"


class IndexErrorV31(ValueError):
    pass


def grouped_inventory(catalog: Catalog) -> list[dict]:
    """Cobertura de 100% do acervo, incluindo produtos aguardando classificação."""
    rows=catalog.db.execute("""
        SELECT
          CASE WHEN p.moderation='eligible' AND t.status='matched'
            THEN t.category ELSE ? END AS category,
          CASE WHEN p.moderation='eligible' AND t.status='matched'
            THEN t.niche ELSE ? END AS niche,
          CASE WHEN p.moderation='eligible' AND t.status='matched'
            THEN 'approved' ELSE 'review' END AS state,
          COUNT(*)
        FROM products p
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
        GROUP BY category,niche,state
        ORDER BY category,niche,state
    """, (UNCLASSIFIED_CATEGORY, UNCLASSIFIED_NICHE)).fetchall()
    return [{"category":category,"niche":niche,"state":state,"products":count}
            for category,niche,state,count in rows]


def lookup(catalog: Catalog, *, category: str | None = None,
           niche: str | None = None, query: str = "",
           campaign: str | None = None, limit: int = 20) -> list[dict]:
    """Busca candidatos aprovados por tema, sem inferir nichos de futuros blogs.

    Consulta a biblioteca independente de site_key e retorna apenas links
    de afiliado da campanha expressamente informada. Nunca retorna um link
    de campanha alheia, mesmo quando o produto já foi pré-convertido.
    """
    if not isinstance(limit,int) or not 1<=limit<=100:
        raise IndexErrorV31("limit_invalid")
    for name,value in (("category",category),("niche",niche)):
        if value is not None and (
                not isinstance(value,str) or
                not re.fullmatch(r"[a-z0-9_]{2,50}",value)):
            raise IndexErrorV31(name+"_invalid")
    if not isinstance(query,str) or len(query)>160:
        raise IndexErrorV31("query_invalid")
    search=normalize(query)
    terms=search.split()
    if not category and not niche and not terms:
        raise IndexErrorV31("search_constraint_required")
    if campaign is not None:
        valid_campaign(campaign)
    clauses=["p.moderation='eligible'","t.status='matched'"]
    args=[]
    if category is not None:
        clauses.append("t.category=?")
        args.append(category)
    if niche is not None:
        clauses.append("t.niche=?")
        args.append(niche)
    # Sem limitações de blog pré-cadastrado: índice do próprio catálogo.
    products=catalog.db.execute("""
        SELECT p.product_key,p.title,p.description,p.origin_url,p.image_url,
               t.category,t.niche
        FROM products p JOIN product_taxonomy t ON t.product_key=p.product_key
        WHERE """+" AND ".join(clauses)+"""
        ORDER BY p.product_key
    """,args).fetchall()
    result=[]
    for key,title,description,origin,image,cat,subcat in products:
        if terms and not all(term in normalize(title+" "+description).split()
                             for term in terms):
            continue
        if not host_allowed(origin) or not str(image).startswith("https://"):
            continue
        row={"product_key":key,"title":title,"category":cat,"niche":subcat,
             "product_url":origin,"image_url":image}
        if campaign is not None:
            link=catalog.cached_link(key,campaign)
            if link and not host_allowed(link,allow_short=True):
                raise IndexErrorV31("untrusted_cached_affiliate_link")
            row["affiliate_ready"]=bool(link)
            if link:
                row["affiliate_url"]=link
        result.append(row)
        if len(result)>=limit:
            break
    return result


def audit(storage: R2State) -> dict:
    with tempfile.TemporaryDirectory(prefix="v31-universal-index-") as td:
        db=Path(td)/"catalog.sqlite3"
        if not storage.restore_to(db):
            raise IndexErrorV31("r2_catalog_missing")
        verify_database(db)
        with Catalog(db) as cat:
            groups=grouped_inventory(cat)
            stats=cat.stats()
        if sum(x["products"] for x in groups)!=stats["products"]:
            raise IndexErrorV31("inventory_count_mismatch")
        return {"mode":"UNIVERSAL_CATALOG_READ_ONLY",
                "products":stats["products"],
                "approved":stats["eligible"],
                "awaiting_review":stats["review"],
                "categories_and_niches":groups,
                "predefined_blog_count":0,
                "shopee_api_calls":0,
                "r2_writes":0,
                "publishing_calls":0,
                "pinterest_calls":0}


def main() -> int:
    parser=argparse.ArgumentParser(
        description="Conferir índice universal categoria/nicho dos dois feeds CSV no R2")
    parser.parse_args()
    try:
        result=audit(R2State.from_env())
        print("V31_C15_UNIVERSAL_INDEX_PASS")
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception:
        print("V31_C15_UNIVERSAL_INDEX_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
