"""C46 — caminhos sugeridos (NÃO aprovação) para itens sem faceta oficial.

Usa exclusivamente os 1.399 termos agregados por L1/L2 dos próprios feeds.
Dois ou mais sinais por título, dominância entre caminhos e veto de conteúdo
sensível. Sem prever blogs, inventar nichos, gerar links ou publicar.

Sugestões permanecem PRIVADAS no sidecar R2 com review_only=1. O status
original dos SKUs e a campanha dos links não são alterados.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import sqlite3

from .curation_audit import PROTECTED_ROOTS
from .taxonomy import normalize
# A constante é declarada localmente para evitar importação circular.
from .universal_lexicon import SENSITIVE_TERMS, _features

NO_SOURCE = "sem_categoria_oficial"
MIN_TERMS = 2
MIN_SCORE = 4
MIN_MARGIN = 2


class ReviewHintsError(ValueError):
    pass


def _exists(db: sqlite3.Connection, table: str) -> bool:
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,)).fetchone() is not None


def build_review_path_hints(catalog_db: sqlite3.Connection,
                            sidecar: sqlite3.Connection) -> dict:
    """Popula tabela de sugestões reprovadas por padrão. Nunca muda core."""
    for table in ("v31_universal_inventory",
                  "v31_universal_title_lexicon"):
        if not _exists(sidecar, table):
            raise ReviewHintsError("universal_index_or_lexicon_required")

    # Termos só participam se apareceram em muitos SKUs/lojas não protegidos.
    inverted = defaultdict(set)
    for l1, l2, term, products, shops, only_review in sidecar.execute("""
        SELECT source_l1,source_l2,term,product_count,
               shop_count_floor,review_only
        FROM v31_universal_title_lexicon
    """):
        if (not isinstance(l1, str) or not isinstance(l2, str) or
            not l1 or not l2 or l1 in PROTECTED_ROOTS or
            not isinstance(term, str) or len(term)>90 or
            type(products) is not int or products<25 or
            type(shops) is not int or shops<8 or only_review != 1):
            continue
        if term != normalize(term):
            continue
        inverted[term].add((l1,l2))

    # Em catálogos pequenos/de teste o léxico pode legitimamente estar vazio.
    # Isso produz ZERO sugestões, jamais aprovação inferida.
    # Inclui SOMENTE a lane sem categoria oficial: conflitos, política, dados
    # inválidos e aprovações existentes não podem entrar nesta tabela.
    keys={x[0] for x in sidecar.execute("""
        SELECT product_key FROM v31_universal_inventory
        WHERE source_l1=? AND review_lane='NO_OFFICIAL_CATEGORY'
          AND decision='review_required' AND can_convert=0
    """,(NO_SOURCE,))}
    suggestions=[]
    processed=0
    sensitive_skipped=0
    insufficient=0
    ambiguous=0
    groups=Counter()
    for key,title in catalog_db.execute("""
        SELECT product_key,title FROM products WHERE moderation='review'
        ORDER BY product_key
    """):
        if key not in keys:
            continue
        processed+=1
        if (not isinstance(title,str) or not title.strip() or
            len(title)>500 or
            any(t in SENSITIVE_TERMS for t in normalize(title).split())):
            sensitive_skipped+=1
            continue
        evidence=defaultdict(set)
        for term in _features(title):
            for path in inverted.get(term,()):
                evidence[path].add(term)
        if not evidence:
            insufficient+=1
            continue
        ranked=sorted(
            ((sum(2 if " " in t else 1 for t in terms),
              len(terms),l1,l2) for (l1,l2),terms in evidence.items()),
            key=lambda x:(-x[0],-x[1],x[2],x[3]))
        best=ranked[0]
        next_score=ranked[1][0] if len(ranked)>1 else 0
        if best[1]<MIN_TERMS or best[0]<MIN_SCORE:
            insufficient+=1
            continue
        if best[0]-next_score<MIN_MARGIN:
            ambiguous+=1
            continue
        suggestions.append(
            (key,best[2],best[3],best[1],best[0],next_score,1))
        groups[(best[2],best[3])]+=1

    if processed!=len(keys):
        raise ReviewHintsError("review_inventory_core_divergence")

    sidecar.execute("""
        CREATE TABLE IF NOT EXISTS v31_unclassified_review_hints (
          product_key TEXT PRIMARY KEY,
          suggested_l1 TEXT NOT NULL,
          suggested_l2 TEXT NOT NULL,
          evidence_terms INTEGER NOT NULL CHECK(evidence_terms>=2),
          evidence_score INTEGER NOT NULL CHECK(evidence_score>=4),
          second_best_score INTEGER NOT NULL CHECK(second_best_score>=0),
          review_only INTEGER NOT NULL CHECK(review_only=1)
        )
    """)
    with sidecar:
        sidecar.execute("DELETE FROM v31_unclassified_review_hints")
        for start in range(0,len(suggestions),1000):
            sidecar.executemany("""
                INSERT INTO v31_unclassified_review_hints
                VALUES(?,?,?,?,?,?,?)
            """,suggestions[start:start+1000])
    sidecar.execute("""
        CREATE INDEX IF NOT EXISTS idx_v31_review_hints_path
        ON v31_unclassified_review_hints
            (suggested_l1,suggested_l2,review_only)
    """)
    actual=sidecar.execute("""
        SELECT COUNT(*) FROM v31_unclassified_review_hints
        WHERE review_only=1
    """).fetchone()[0]
    if actual!=len(suggestions) or sidecar.execute(
            "PRAGMA integrity_check").fetchone()[0]!="ok":
        raise ReviewHintsError("review_hints_integrity_failed")

    return {
        "mode":"C46_UNCLASSIFIED_REVIEW_PATH_HINTS",
        "unclassified_review_scanned":processed,
        "review_path_hints_created":actual,
        "still_without_confident_hint":processed-actual,
        "sensitive_or_invalid_title_held":sensitive_skipped,
        "ambiguous_evidence_held":ambiguous,
        "insufficient_evidence_held":insufficient,
        "distinct_official_paths_suggested":len(groups),
        "review_only":True,
        "new_approvals":0,
        "affiliate_conversion_calls":0,
        "publication_calls":0,
        "core_catalog_mutations":0,
    }


def suggested_path_counts(sidecar: sqlite3.Connection, *,
                          limit: int=30) -> list[dict]:
    if type(limit) is not int or not 1<=limit<=100:
        raise ReviewHintsError("invalid_summary_limit")
    if not _exists(sidecar,"v31_unclassified_review_hints"):
        raise ReviewHintsError("review_hints_missing")
    rows=sidecar.execute("""
        SELECT suggested_l1,suggested_l2,COUNT(*) AS n
        FROM v31_unclassified_review_hints WHERE review_only=1
        GROUP BY suggested_l1,suggested_l2
        ORDER BY n DESC,suggested_l1,suggested_l2
        LIMIT ?
    """,(limit,)).fetchall()
    return [
        {"source_l1_review_hint":l1,
         "source_l2_review_hint":l2,
         "pending_review_products":count,
         "approved_for_publication":False}
        for l1,l2,count in rows
    ]
