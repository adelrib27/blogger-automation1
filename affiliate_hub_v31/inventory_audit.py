"""C9 — diagnóstico READ-ONLY de oferta de produtos por categoria.

Verifica a cobertura dos CSV reais independentemente de links já convertidos.
Não lê preços em logs, não chama Shopee/WordPress e não grava no R2.
Novos blogs são registrados em shadow.d/*.json.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from pathlib import Path

from .catalog import host_allowed
from .fallback_v23 import load_configuration, semantic_score
from .r2_state import R2State, verify_database
from .shadow_audit import load_profiles
from .routing import sites


class InventoryError(ValueError):
    pass


def eligible_inventory(db_path: Path, site_key: str, cfg: dict,
                       intent_rules: dict) -> dict:
    if site_key not in sites():
        raise InventoryError("site_unknown")
    allowed=set(sites()[site_key]["allowed_niches"])
    try:
        uri="file:"+str(Path(db_path).resolve())+"?mode=ro"
        with sqlite3.connect(uri,uri=True) as db:
            products=db.execute("""
                SELECT p.product_key,p.title,p.origin_url,p.image_url,
                       t.category,t.niche
                FROM products p JOIN product_taxonomy t ON t.product_key=p.product_key
                WHERE p.moderation='eligible' AND t.status='matched'
                ORDER BY p.product_key
            """).fetchall()
    except (OSError,sqlite3.Error):
        raise InventoryError("r2_catalog_query_failed") from None
    scope=[(key,title) for key,title,origin,image,cat,niche in products
           if f"{cat}/{niche}" in allowed and host_allowed(origin)
           and str(image).startswith("https://")]
    results={}
    for category,keywords in cfg["categories"].items():
        matches=set()
        for key,title in scope:
            if any(semantic_score(title,kw,intent_rules)>0 for kw in keywords):
                matches.add(key)
        results[category]=len(matches)
    return {
        "site_key":site_key,
        "allowed_eligible_products":len(scope),
        "category_supply":results,
        "zero_supply_categories":[name for name,n in results.items() if n==0],
        "unique_products_sufficient_for_one_day":
             len({key for key,_ in scope}) >= 1,
    }


def audit(storage: R2State, site: str = "all") -> dict:
    profiles=load_profiles()
    if site!="all" and site not in profiles:
        raise InventoryError("site_unconfigured")
    keys=sorted(profiles) if site=="all" else [site]
    with tempfile.TemporaryDirectory(prefix="v31-c9-inventory-") as tmp:
        path=Path(tmp)/"state.sqlite3"
        if not storage.restore_to(path):
            raise InventoryError("r2_state_missing")
        verify_database(path)
        output=[]
        for key in keys:
            profile=profiles[key]
            cfg,rules=load_configuration(profile["_config_file"],
                                          profile["_rules_file"])
            supply=eligible_inventory(path,key,cfg,rules)
            required=profile["required_source_categories"]
            supply["required_categories_without_supply"]=[
                name for name in required if supply["category_supply"].get(name,0)==0]
            supply["all_required_categories_have_inventory"]=not supply[
                "required_categories_without_supply"]
            output.append(supply)
    return {
        "mode":"CSV_R2_INVENTORY_READ_ONLY",
        "sites_checked":len(output),
        "writes_to_r2":0,"shopee_requests":0,"publication_calls":0,
        "sites":output
    }


def main() -> int:
    p=argparse.ArgumentParser(description="C9: produtos suficientes por categoria CSV/R2")
    p.add_argument("--site",default="all")
    args=p.parse_args()
    try:
        result=audit(R2State.from_env(),args.site)
        print("V31_C9_INVENTORY_AUDIT_PASS")
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception:
        print("V31_C9_INVENTORY_AUDIT_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
