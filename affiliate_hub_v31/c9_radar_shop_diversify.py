"""C9 Radar: reparar UM conflito de loja entre as cinco categorias.

É uma extensão do cache UNIVERSAL, não substitui publicador Radar.
A própria fila antiga exige 5 lojas distintas e 5 categorias; quando
há conflito, converte 1 alternativa de loja ainda não usada na categoria.
Nunca imprime IDs/lojas/URLs nem cria/publica posts.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

from .catalog import Catalog,host_allowed
from .converter import convert_one
from .fallback_v23 import candidates_from_catalog,load_configuration,semantic_score
from .r2_state import R2State,verify_database
from .routing import sites

ROOT=Path(__file__).resolve().parents[1]
SITE="wordpress_radartechbr"


class ShopDiversificationError(ValueError):
    pass


def choose_replacement(catalog: Catalog, cfg: dict, rules: dict) -> tuple[str,str]:
    rows=candidates_from_catalog(catalog.path,SITE,cfg,rules,limit=100)
    first={}
    for category in cfg["categories"]:
        current=next((r for r in rows if category in r.get("categories",[])),None)
        if current is None:
            raise ShopDiversificationError("missing_category_cache")
        first[category]=current
    shop_counts=Counter(row["shopId"] for row in first.values())
    duplicated=[cat for cat,row in first.items() if shop_counts[row["shopId"]]>1]
    if not duplicated:
        raise ShopDiversificationError("no_duplicate_shop_in_first_choices")
    used_shops=set(row["shopId"] for row in first.values())
    allowed=set(sites()[SITE]["allowed_niches"])
    existing={r["itemId"] for r in rows}
    sys.path.insert(0,str(ROOT/"src"))
    try:
        import fase3_fila_radar as legacy
        policy=legacy.load_json(legacy.POLICY_PATH,{})
        blockers=legacy.history_blockers(policy)
    finally:
        sys.path.remove(str(ROOT/"src"))
    products=catalog.db.execute("""
      SELECT p.product_key,p.title,p.origin_url,p.image_url,p.shop_id,
             p.item_id,t.category,t.niche
      FROM products p JOIN product_taxonomy t ON t.product_key=p.product_key
      LEFT JOIN affiliate_links l ON l.product_key=p.product_key AND l.campaign=?
      WHERE p.moderation='eligible' AND t.status='matched'
        AND l.product_key IS NULL
      ORDER BY p.product_key
    """,(sites()[SITE]["campaign"],)).fetchall()
    for category in duplicated:
        keywords=cfg["categories"][category]
        for key,title,origin,image,shop,item_id,cat,niche in products:
            if (str(shop) in used_shops or not str(shop).isdigit() or
                    not str(item_id).isdigit() or str(item_id) in existing or
                    f"{cat}/{niche}" not in allowed or
                    not host_allowed(origin) or
                    not str(image).startswith("https://")):
                continue
            if not any(semantic_score(title,kw,rules)>0 for kw in keywords):
                continue
            if not legacy.product_is_historically_allowed({
                "productName":title,"itemId":str(item_id),"offerLink":origin
            },blockers,policy):
                continue
            return key,category
    raise ShopDiversificationError("no_alternate_shop_found")


def diversify(storage: R2State, app_id: str, app_secret: str,
              dry_run: bool = False) -> dict:
    if not dry_run and (not app_id or not app_secret):
        raise ShopDiversificationError("credentials_missing")
    cfg,rules=load_configuration(ROOT/"config/shopee_oportunidades.json",
                                 ROOT/"config/shopee_intent_rules.json")
    with tempfile.TemporaryDirectory(prefix="v31-c9-radar-shop-") as td:
        file=Path(td)/"state.sqlite3"
        if not storage.restore_to(file):
            raise ShopDiversificationError("catalog_missing")
        verify_database(file)
        with Catalog(file) as catalog:
            key,category=choose_replacement(catalog,cfg,rules)
            if dry_run:
                return {"mode":"DRY_RUN","replacement_available":True,
                        "category":category,"mutations":0,"publication_calls":0}
            link,created=convert_one(catalog,key,sites()[SITE]["campaign"],
                                     app_id,app_secret)
            if not created or not host_allowed(link,allow_short=True):
                raise ShopDiversificationError("conversion_not_new_or_untrusted")
            if not catalog.integrity():
                raise ShopDiversificationError("catalog_integrity_failed")
        stored=storage.save_from(file)
        if not stored["state_saved"]:
            raise ShopDiversificationError("state_not_saved")
        restored=Path(td)/"recovered.sqlite3"
        if not storage.restore_to(restored):
            raise ShopDiversificationError("restore_failed")
        with Catalog(restored) as catalog:
            if catalog.cached_link(key,sites()[SITE]["campaign"]) != link:
                raise ShopDiversificationError("restored_link_missing")
        return {"mode":"ONE_NEW_SHOP_LINK","category":category,
                "converted":1,"r2_snapshot_saved":True,
                "retention_pending":stored.get("retention_pending",False),
                "publication_calls":0}


def main() -> int:
    try:
        dry=os.environ.get("V31_C9_DRY_RUN","true").strip().lower() != "false"
        result=diversify(R2State.from_env(),
                         os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID",""),
                         os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET",""),
                         dry_run=dry)
        print("V31_C9_RADAR_SHOP_DIVERSIFY_PASS")
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception:
        print("V31_C9_RADAR_SHOP_DIVERSIFY_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
