"""C9 — Diagnóstico SAFE de motivos que bloqueiam 5 slots do Radar.

Usa seleção ORIGINAL do Radar e o cache REAL do R2, mas mostra somente
contagens por categoria (nunca IDs, lojas ou links comerciais). Não publica.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from .fallback_v23 import candidates_from_catalog,load_configuration
from .r2_state import R2State,verify_database

ROOT=Path(__file__).resolve().parents[1]


def analyze(storage: R2State) -> dict:
    cfg,rules=load_configuration(ROOT/"config/shopee_oportunidades.json",
                                 ROOT/"config/shopee_intent_rules.json")
    with tempfile.TemporaryDirectory(prefix="v31-c9-radar-diagnose-") as tmp:
        db=Path(tmp)/"state.sqlite3"
        if not storage.restore_to(db):
            raise ValueError("catalog_missing")
        verify_database(db)
        rows=candidates_from_catalog(db,"wordpress_radartechbr",cfg,rules,limit=100)
        sys.path.insert(0,str(ROOT/"src"))
        try:
            import fase3_fila_radar as legacy
            policy=legacy.load_json(legacy.POLICY_PATH,{})
            mapping,_=legacy.category_maps(policy)
            blockers=legacy.history_blockers(policy)
            reports={}
            for category in policy["allowed_categories"]:
                source=next((s for s,d in mapping.items() if d==category),"")
                raw=[r for r in rows if source in r.get("categories",[])]
                accepted=legacy.candidate_options(
                    rows,category,source,cfg,mapping,blockers,policy)
                reports[category]={
                    "cached_category_products":len(raw),
                    "surviving_original_editorial_filters":len(accepted),
                    "unique_shops_after_filters":len(set(
                        str(prod.get("shopId") or prod.get("shopName") or "")
                        for prod,_ in accepted)),
                    "distinct_keywords_after_filters":len(set(
                        str(kw) for _,kw in accepted)),
                }
            return {
                "site_key":"wordpress_radartechbr",
                "cached_ranked_products":len(rows),
                "category_diagnostics":reports,
                "categories_with_zero_filtered_candidates":[
                    key for key,info in reports.items()
                    if info["surviving_original_editorial_filters"]==0],
                "publication_calls":0,"r2_writes":0,"shopee_api_calls":0
            }
        finally:
            sys.path.remove(str(ROOT/"src"))


def main() -> int:
    try:
        result=analyze(R2State.from_env())
        print("V31_C9_RADAR_DIAGNOSTIC_PASS")
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception:
        print("V31_C9_RADAR_DIAGNOSTIC_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
