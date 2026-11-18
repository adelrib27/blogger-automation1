"""C16 — Diagnóstico de taxonomia existente nos feeds/R2, SEM mutações.

Somente contagens e bigramas com frequência mínima; nenhum título de produto,
ID, URL, campanha, nome de vendedor ou segredo em logs.
"""
from __future__ import annotations

import json
import tempfile
from collections import Counter
from pathlib import Path

from .catalog import Catalog
from .r2_state import R2State, verify_database
from .taxonomy import normalize, rules

STOP = frozenset({
    "para","com","sem","de","da","do","dos","das","uma","um","em","que",
    "pro","por","kit","novo","nova","original","premium","uso","brasil",
    "sua","seu","mais","ideal","produto","pcs","und","unidades","unidade",
    "unissex","preto","preta","branco","branca","rosa","azul","verde",
    "modelo","cor","cores","tamanho","tipo","grande","pequeno","pequena",
    "feminino","feminina","masculino","masculina","loja","atacado",
    "oferta","desconto","promocao","frete","gratis","original",
})


def _useful_words(title: str) -> list[str]:
    words=normalize(title).split()
    return [w for w in words if w.isalpha() and len(w)>=4 and w not in STOP]


def diagnose(catalog: Catalog, *, top: int = 35) -> dict:
    if not isinstance(top,int) or not 1<=top<=50:
        raise ValueError("top_limit_invalid")
    reasons=Counter()
    reviews=Counter()
    grams=Counter()
    total=0
    safe_for_future_reclassification=0
    cursor=catalog.db.execute("""
        SELECT p.title,p.moderation,p.moderation_reason,
               COALESCE(t.status,'missing'),COALESCE(t.reason,'missing')
        FROM products p
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
        WHERE p.moderation!='eligible' OR t.status!='matched' OR t.status IS NULL
    """)
    for title,moderation,reason,tax_status,tax_reason in cursor:
        total+=1
        # Taxonomia e moderação são classificações locais, não texto do feed.
        safe_reason=tax_reason if tax_reason in (
            "unclassified","ambiguous_niches","excluded_accessory_or_semantics",
            "conflicting_or_unclassified_reimport","empty_title","missing"
        ) else "other"
        reasons[safe_reason]+=1
        moderation_kind=(
            "only_taxonomy_unclassified" if reason=="taxonomy_unclassified"
            else "only_taxonomy_ambiguous" if reason=="taxonomy_ambiguous_niches"
            else "moderation_other_or_conflict"
        )
        reviews[moderation_kind]+=1
        if reason=="taxonomy_unclassified" and safe_reason=="unclassified":
            safe_for_future_reclassification+=1
        # Bigramas apenas dos títulos ainda "unclassified" para orientar
        # taxonomia futura, nunca para inferir rótulo automaticamente.
        if tax_reason=="unclassified":
            words=_useful_words(title)
            grams.update(set(zip(words,words[1:])) if len(words)>1 else ())
    version,_=rules()
    common=[{"phrase":" ".join(pair),"titles":count}
            for pair,count in grams.most_common(top)
            if count>=25]
    return {
        "mode":"TAXONOMY_DIAGNOSTIC_READ_ONLY",
        "taxonomy_version":version,
        "pending_products":total,
        "taxonomy_reasons":dict(sorted(reasons.items())),
        "moderation_reasons":dict(sorted(reviews.items())),
        "potentially_reclassifiable_without_prior_conflict":
            safe_for_future_reclassification,
        "common_unclassified_title_bigram_counts":common,
        "blog_preselection":0,"shopee_api_calls":0,"r2_writes":0,
        "publication_calls":0,
    }


def main()->int:
    try:
        with tempfile.TemporaryDirectory(prefix="v31-c16-tax-audit-") as td:
            file=Path(td)/"catalog.sqlite3"
            storage=R2State.from_env()
            if not storage.restore_to(file):
                raise ValueError("catalog_missing")
            verify_database(file)
            with Catalog(file) as c:
                result=diagnose(c)
        print("V31_C16_TAXONOMY_DIAGNOSTIC_PASS")
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
        return 0
    except Exception:
        print("V31_C16_TAXONOMY_DIAGNOSTIC_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
