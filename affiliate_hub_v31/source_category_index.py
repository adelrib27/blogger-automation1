"""C16 — Índice oficial de categorias Shopee L1/L2/L3 para TODO o catálogo.

Os dois CSV têm globalCategory1/2 (e o CSV grande também globalCategory3).
A organização é por produto, nunca por blog. A categoria que o feed informa
é um FACET DE BUSCA e não revoga a moderação editorial.

Não converte links, não publica, não escolhe assuntos futuros.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

from .catalog import Catalog, classify, fields, normalized
from .taxonomy import normalize

LEVELS = {
    "globalcategory1": "level1",
    "globalcategory2": "level2",
    "globalcategory3": "level3",
}
MAX_ROWS_PER_CSV = 250_000


class SourceCategoryError(ValueError):
    """Erro de importação, não incluir título/URL do CSV."""


def clean_category(value: str) -> str:
    if not isinstance(value,str) or len(value)>200:
        return ""
    return normalize(value)[:120]


def create_source_category_schema(catalog: Catalog) -> None:
    catalog.db.executescript("""
    CREATE TABLE IF NOT EXISTS product_source_categories (
      product_key TEXT NOT NULL,
      source TEXT NOT NULL,
      level1 TEXT NOT NULL DEFAULT '',
      level2 TEXT NOT NULL DEFAULT '',
      level3 TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL CHECK(status IN ('matched','review','conflict')),
      PRIMARY KEY(product_key,source),
      FOREIGN KEY(product_key) REFERENCES products(product_key)
    );
    CREATE INDEX IF NOT EXISTS idx_v31_source_category_hierarchy
      ON product_source_categories(status,level1,level2,level3,product_key);
    """)
    catalog.db.commit()


def source_columns(headers: list[str]) -> dict[str,str]:
    mapping={}
    for header in headers:
        target=LEVELS.get(normalized(header))
        if target:
            if target in mapping:
                raise SourceCategoryError("duplicate_level_headers")
            mapping[target]=header
    return mapping


def import_source_categories(catalog: Catalog, csv_path: Path | str,
                             source: str) -> dict:
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,40}",source):
        raise SourceCategoryError("source_invalid")
    create_source_category_schema(catalog)
    counters=Counter()
    with Path(csv_path).open("r",encoding="utf-8-sig",newline="") as stream:
        sample=stream.read(8192)
        stream.seek(0)
        try:
            dialect=csv.Sniffer().sniff(sample,delimiters=",;\t|")
        except csv.Error:
            dialect=csv.excel
        reader=csv.DictReader(stream,delimiter=dialect.delimiter,
                              quotechar='"',doublequote=True,strict=True)
        if not reader.fieldnames or len(reader.fieldnames)>128:
            raise SourceCategoryError("headers_invalid")
        columns=source_columns(reader.fieldnames)
        if "level1" not in columns:
            raise SourceCategoryError("official_level1_missing")
        with catalog.db:
            for raw in reader:
                counters["rows"]+=1
                if counters["rows"]>MAX_ROWS_PER_CSV:
                    raise SourceCategoryError("row_limit_exceeded")
                if None in raw or any(v is None for v in raw.values()):
                    raise SourceCategoryError("row_columns_invalid")
                data=fields(raw)
                key,_moderation,_reason=classify(data)
                product_exists=catalog.db.execute(
                    "SELECT 1 FROM products WHERE product_key=?",(key,)
                ).fetchone()
                if not product_exists:
                    counters["not_in_current_catalog"]+=1
                    continue
                values={
                    level:clean_category(str(raw.get(header) or ""))
                    for level,header in columns.items()
                }
                first=values.get("level1","")
                second=values.get("level2","")
                third=values.get("level3","")
                if not first:
                    counters["without_level1"]+=1
                    continue
                current=catalog.db.execute("""
                    SELECT level1,level2,level3,status FROM product_source_categories
                    WHERE product_key=? AND source=?
                """,(key,source)).fetchone()
                if current is not None:
                    if current[:3]!=(first,second,third) or current[3]=="conflict":
                        catalog.db.execute("""
                            UPDATE product_source_categories SET status='conflict'
                            WHERE product_key=? AND source=?
                        """,(key,source))
                        counters["category_conflicts"]+=1
                    else:
                        counters["duplicates_same_category"]+=1
                    continue
                catalog.db.execute("""
                    INSERT INTO product_source_categories
                    (product_key,source,level1,level2,level3,status)
                    VALUES(?,?,?,?,?,?)
                """,(key,source,first,second,third,"matched"))
                counters["new_category_records"]+=1
    return {
        "source":source,
        "rows":counters["rows"],
        "levels_present":sorted(columns),
        "new_category_records":counters["new_category_records"],
        "duplicates_same_category":counters["duplicates_same_category"],
        "category_conflicts":counters["category_conflicts"],
        "without_level1":counters["without_level1"],
        "not_in_current_catalog":counters["not_in_current_catalog"],
        "shopee_api_calls":0,"publication_calls":0,
    }


def source_inventory(catalog: Catalog) -> dict:
    create_source_category_schema(catalog)
    count,distinct,approved,ambiguous=catalog.db.execute("""
        SELECT COUNT(*),
               COUNT(DISTINCT s.product_key),
               COUNT(DISTINCT CASE WHEN p.moderation='eligible'
                    AND t.status='matched' AND s.status='matched'
                    THEN s.product_key END),
               COALESCE(SUM(CASE WHEN s.status!='matched' THEN 1 ELSE 0 END),0)
        FROM product_source_categories s
        JOIN products p ON p.product_key=s.product_key
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
    """).fetchone()
    groups=catalog.db.execute("""
        SELECT level1,COUNT(DISTINCT product_key) FROM product_source_categories
        WHERE status='matched'
        GROUP BY level1 ORDER BY COUNT(DISTINCT product_key) DESC,level1
    """).fetchall()
    return {
        "products_with_official_source_categories":distinct,
        "source_category_rows":count,
        "already_editorially_approved_products_with_source_facet":approved,
        "source_category_conflicts_or_review_rows":ambiguous,
        "level1_facets":[{"label":name,"products":number} for name,number in groups],
        "r2_writes":0,"shopee_api_calls":0,"publication_calls":0,
    }


def browse_source(catalog: Catalog, *, level1: str,
                  level2: str | None = None, level3: str | None = None,
                  limit: int = 20, campaign: str | None = None) -> list[dict]:
    """Busca universal inclusive produtos sob revisão; nunca chama um blog.

    O cliente deve respeitar 'editorial_approved' antes de publicar. Quando
    há campanha, somente links já convertidos para ela podem ser retornados.
    """
    from .converter import valid_campaign
    if not isinstance(limit,int) or not 1<=limit<=100:
        raise SourceCategoryError("limit_invalid")
    names=(level1,level2,level3)
    if not level1 or any(v is not None and (
        not isinstance(v,str) or len(v)>120 or not normalize(v)
    ) for v in names):
        raise SourceCategoryError("source_category_invalid")
    if campaign is not None:
        valid_campaign(campaign)
    create_source_category_schema(catalog)
    clauses=["s.status='matched'","s.level1=?"]
    args=[normalize(level1)]
    if level2 is not None:
        clauses.append("s.level2=?")
        args.append(normalize(level2))
    if level3 is not None:
        clauses.append("s.level3=?")
        args.append(normalize(level3))
    args.append(limit)
    rows=catalog.db.execute("""
        SELECT p.product_key,p.title,p.origin_url,p.image_url,
               MAX(CASE WHEN p.moderation='eligible' AND t.status='matched'
                   THEN 1 ELSE 0 END) AS approved,
               MAX(s.level1),MAX(s.level2),MAX(s.level3)
        FROM product_source_categories s
        JOIN products p ON p.product_key=s.product_key
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
        WHERE """+" AND ".join(clauses)+"""
        GROUP BY p.product_key
        ORDER BY approved DESC,p.product_key LIMIT ?
    """,args).fetchall()
    output=[]
    for key,title,origin,image,approved,first,second,third in rows:
        item={"product_key":key,"title":title,"product_url":origin,
              "image_url":image,"source_category_l1":first,
              "source_category_l2":second,"source_category_l3":third,
              "editorial_approved":bool(approved)}
        if campaign is not None:
            link=catalog.cached_link(key,campaign) if approved else None
            item["affiliate_ready"]=bool(link)
            if link:
                item["affiliate_url"]=link
        output.append(item)
    return output
