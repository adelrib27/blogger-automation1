"""C35 — vocabulário pesquisável dos TÍTULOS ligado às facetas oficiais.

Gera termos por grupo L1/L2 apenas se repetidos em muitos produtos e lojas.
Não usa categorias ou nichos presumidos para blogs futuros; o tema solicitado
vira uma consulta ao acervo. Nunca aprova/reclassifica SKUs nem produz link.
O arquivo SQLite é o sidecar R2 C34 (não o catálogo comercial).
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import json
import re
import sqlite3
import tempfile
from pathlib import Path

from .curation_audit import PROTECTED_ROOTS
from .taxonomy import normalize
from .universal_index_storage import UniversalIndexStorage

STOPWORDS=frozenset((
    "para","com","sem","por","das","dos","uma","uns","novo","nova",
    "modelo","premium","original","universal","produto","unidade",
    "tamanho","preto","preta","branco","branca","azul","vermelho",
    "marca","tipo","alto","alta","baixo","baixa","melhor","super",
    "profissional","acessorio","acessorios","pequeno","grande",
    "unidades","cor","kit","jogo","combo","pack","pct","pecas",
    "peca","mais","tambem","este","esta","essa","esse","depois",
))
# Jamais sugerir produtos potencialmente restritos com base em vocabulário.
SENSITIVE_TERMS=frozenset((
    "carabina","espingarda","municao","armas","arma","pistola","airsoft",
    "vape","cigarro","nicotina","veneno","pesticida","replica",
    "anabolizante","esteroide","canabis","cannabis","maconha",
))
MAX_INPUT_CHARS=160


class LexiconError(ValueError):
    pass


def _tokens(value:str)->tuple[str,...]:
    if not isinstance(value,str):
        return ()
    terms=[x for x in normalize(value).split() if
           len(x)>=4 and not x.isdigit() and x not in STOPWORDS and
           x not in SENSITIVE_TERMS]
    return tuple(dict.fromkeys(terms))


def _features(value:str)->set[str]:
    tokens=_tokens(value)
    return set(tokens)|{a+" "+b for a,b in zip(tokens,tokens[1:])
                        if a!=b}


def build_lexicon(catalog_db:sqlite3.Connection, sidecar:sqlite3.Connection,
                  *, min_products:int=25,min_shops:int=8,
                  max_terms_per_path:int=24)->dict:
    """Treina somente agregações k-anônimas das categorias OFICIAIS.

    Não traz títulos/IDs para logs e não cria credenciais nem campanha.
    """
    if (type(min_products)is not int or type(min_shops)is not int or
        type(max_terms_per_path)is not int or
        not 2<=min_products<=1000 or not 2<=min_shops<=200 or
        not 1<=max_terms_per_path<=100):
        raise LexiconError("invalid_group_threshold")
    indexed=sidecar.execute("""
      SELECT 1 FROM sqlite_master WHERE type='table'
      AND name='v31_universal_inventory'
    """).fetchone()
    if not indexed:
        raise LexiconError("universal_inventory_required")

    rows=catalog_db.execute("""
      SELECT p.product_key,p.shop_id,p.title,
        MIN(CASE WHEN s.status='matched' THEN s.level1 END) AS l1,
        MIN(CASE WHEN s.status='matched' THEN s.level2 END) AS l2,
        COUNT(DISTINCT CASE WHEN s.status='matched'
          THEN s.level1 || char(31) || s.level2 END) AS branches,
        COALESCE(SUM(CASE WHEN s.status!='matched' THEN 1 ELSE 0 END),0) AS bad
      FROM products p
      JOIN product_source_categories s ON s.product_key=p.product_key
      GROUP BY p.product_key
    """)
    vocab=defaultdict(Counter)
    shops=defaultdict(lambda:defaultdict(set))
    seen_products=Counter()
    for key,shop,title,l1,l2,branches,bad in rows:
        if (branches!=1 or bad or not l1 or not l2 or
            l1 in PROTECTED_ROOTS or not str(shop).isdigit()):
            continue
        feats=_features(title)
        if not feats or _tokens(title) and any(
            x in SENSITIVE_TERMS for x in normalize(title).split()):
            continue
        path=(l1,l2)
        seen_products[path]+=1
        for term in feats:
            vocab[path][term]+=1
            if len(shops[path][term])<min_shops:
                shops[path][term].add(shop)

    sidecar.executescript("""
      CREATE TABLE IF NOT EXISTS v31_universal_title_lexicon (
        source_l1 TEXT NOT NULL,source_l2 TEXT NOT NULL,
        term TEXT NOT NULL,product_count INTEGER NOT NULL,
        shop_count_floor INTEGER NOT NULL,
        review_only INTEGER NOT NULL DEFAULT 1 CHECK(review_only=1),
        PRIMARY KEY(source_l1,source_l2,term)
      );
    """)
    inserted=0
    groups=0
    with sidecar:
        sidecar.execute("DELETE FROM v31_universal_title_lexicon")
        for (l1,l2),freq in sorted(vocab.items()):
            terms=[(token,n) for token,n in freq.items()
                if n>=min_products and
                   len(shops[(l1,l2)][token])>=min_shops]
            terms.sort(key=lambda x:(-x[1],x[0]))
            terms=terms[:max_terms_per_path]
            if not terms:continue
            groups+=1
            sidecar.executemany("""
              INSERT INTO v31_universal_title_lexicon
              (source_l1,source_l2,term,product_count,shop_count_floor,review_only)
              VALUES(?,?,?,?,?,1)
            """,((l1,l2,term,n,len(shops[(l1,l2)][term]))
                 for term,n in terms))
            inserted+=len(terms)
    sidecar.executescript("""
      CREATE INDEX IF NOT EXISTS idx_v31_lexicon_term
      ON v31_universal_title_lexicon(term,source_l1,source_l2);
    """)
    if sidecar.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
        raise LexiconError("lexicon_sqlite_invalid")
    return {"mode":"C35_UNIVERSAL_SOURCE_LEXICON",
            "source_paths_scanned":len(seen_products),
            "source_paths_with_aggregate_terms":groups,
            "aggregate_terms_indexed":inserted,
            "minimum_products_per_term":min_products,
            "minimum_distinct_shops_per_term":min_shops,
            "publications":0,"affiliate_conversions":0,
            "new_approvals":0,"title_lexicon_never_authorizes_publication":True}


def paths_for_topic(sidecar:sqlite3.Connection, topic:str,
                    *,limit:int=12)->list[dict]:
    if not isinstance(topic,str) or not 1<=len(topic.strip())<=MAX_INPUT_CHARS:
        raise LexiconError("topic_invalid")
    if type(limit)is not int or not 1<=limit<=30:
        raise LexiconError("limit_invalid")
    features=_features(topic)
    if not features:
        return []
    placeholders=",".join("?" for _ in features)
    query="""
      SELECT source_l1,source_l2,COUNT(*) hits,
             SUM(product_count) AS evidence,
             MIN(shop_count_floor) AS min_shop_support
      FROM v31_universal_title_lexicon
      WHERE term IN ("""+placeholders+""") AND review_only=1
      GROUP BY source_l1,source_l2
      ORDER BY hits DESC,evidence DESC,source_l1,source_l2
      LIMIT ?
    """
    rows=sidecar.execute(query,(*sorted(features),limit)).fetchall()
    return [{"category_l1":l1,"category_l2":l2,
             "matching_aggregated_terms":hits,
             "aggregate_product_support":evidence,
             "shop_support_floor":shops,
             "is_review_signal_only":True,
             "publication_approved":False}
            for l1,l2,hits,evidence,shops in rows]


def run_query_r2(topic:str,limit:int=12)->dict:
    with tempfile.TemporaryDirectory(prefix="v31-lexicon-query-") as t:
        file=Path(t)/"universal_index.sqlite3"
        if not UniversalIndexStorage.from_env().restore_to(file):
            raise LexiconError("universal_index_missing")
        with sqlite3.connect(f"file:{file.resolve()}?mode=ro",uri=True) as db:
            paths=paths_for_topic(db,topic,limit=limit)
    return {"mode":"C35_UNIVERSAL_REVIEW_PATH_QUERY",
            "suggested_official_paths":paths,
            "requires_product_review":True,
            "publication_calls":0,"shopee_mutations":0}


def main()->int:
    p=argparse.ArgumentParser(description="Consulta tema livre no índice universal R2")
    p.add_argument("--topic",required=True)
    p.add_argument("--limit",type=int,default=12)
    args=p.parse_args()
    try:
        result=run_query_r2(args.topic,args.limit)
        print("V31_C35_UNIVERSAL_LEXICON_QUERY_PASS")
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
        return 0
    except Exception as e:
        print("V31_C35_UNIVERSAL_LEXICON_QUERY_FAILED_"+type(e).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
