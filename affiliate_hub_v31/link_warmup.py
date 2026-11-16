"""C7 — Pré-aquecimento de cache por site, sem publicar.

O catálogo central e a API Shopee são compartilhados, mas links cacheados
permanecem segregados pela campanha editorial de cada site. O script funciona
com qualquer blog cadastrado em sites.d/ ou site_routes.json.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from .catalog import Catalog, host_allowed
from .converter import ConversionError, convert_one
from .fallback_v23 import FallbackUnavailable, load_configuration, semantic_score
from .r2_state import R2State
from .routing import sites

MAX_WARMUP_PER_RUN = 3


def warmup_candidates(catalog: Catalog, site_key: str, config: dict,
                      rules: dict, limit: int) -> list[str]:
    site=sites().get(site_key)
    if site is None:
        raise FallbackUnavailable("site_not_registered")
    if not 1 <= limit <= MAX_WARMUP_PER_RUN:
        raise FallbackUnavailable("warmup_limit_invalid")
    allowed=set(site["allowed_niches"])
    all_rows=catalog.db.execute("""
      SELECT p.product_key,p.title,p.item_id,p.image_url,p.origin_url,t.category,t.niche
      FROM products p JOIN product_taxonomy t ON t.product_key=p.product_key
      LEFT JOIN affiliate_links l ON l.product_key=p.product_key AND l.campaign=?
      WHERE p.moderation='eligible' AND t.status='matched'
        AND l.product_key IS NULL
      ORDER BY p.product_key
    """,(site["campaign"],)).fetchall()
    selected=[]
    used=set()
    for category,keywords in config["categories"].items():
        for keyword in keywords:
            for key,title,item_id,image,origin,cat,niche in all_rows:
                if (key in used or f"{cat}/{niche}" not in allowed
                    or not str(item_id).isdigit()
                    or not str(image).startswith("https://")
                    or not host_allowed(origin)):
                    continue
                if semantic_score(title,keyword,rules)<=0:
                    continue
                selected.append(key)
                used.add(key)
                break
            if len(selected)>=limit:
                return selected
    return selected


def warmup(site_key: str, config_file: Path, rules_file: Path,
           limit: int, dry_run: bool) -> dict:
    if site_key not in sites():
        raise FallbackUnavailable("site_not_registered")
    if not 1 <= limit <= MAX_WARMUP_PER_RUN:
        raise FallbackUnavailable("warmup_limit_invalid")
    cfg,rules=load_configuration(config_file,rules_file)
    storage=R2State.from_env()
    with tempfile.TemporaryDirectory(prefix="v31-c7-warmup-") as t:
        file=Path(t)/"state.sqlite3"
        if not storage.restore_to(file):
            raise FallbackUnavailable("r2_state_missing")
        with Catalog(file) as catalog:
            keys=warmup_candidates(catalog,site_key,cfg,rules,limit)
            count=catalog.db.execute(
                "SELECT count(*) FROM affiliate_links WHERE campaign=?",
                (sites()[site_key]["campaign"],)).fetchone()[0]
            if dry_run:
                return {"mode":"DRY_RUN", "site_key":site_key,
                        "eligible_for_warmup":len(keys),"existing_cached_links":count}
            if not keys:
                return {"mode":"NO_CANDIDATES", "site_key":site_key,
                        "eligible_for_warmup":0, "existing_cached_links":count,
                        "converted":0, "snapshot_saved":False}
            app_id=os.getenv("V31_EDITORIAL_SHOPEE_APP_ID","").strip()
            app_secret=os.getenv("V31_EDITORIAL_SHOPEE_APP_SECRET","").strip()
            if not app_id or not app_secret:
                raise ConversionError("credentials_missing")
            converted=0
            error=None
            for key in keys:
                try:
                    _,new=convert_one(catalog,key,sites()[site_key]["campaign"],app_id,app_secret)
                    converted+=int(new)
                except ConversionError:
                    error="shopee_unavailable"
                    break
            if not catalog.integrity():
                raise FallbackUnavailable("catalog_integrity_failed")
        # Persistir quaisquer sucessos mesmo se outra API falhar, mantendo
        # apenas dados comerciais no R2 e nenhum link nos logs.
        stored=storage.save_from(file) if converted else {"state_saved":False}
        verify=Path(t)/"verify.sqlite3"
        if converted:
            if not storage.restore_to(verify):
                raise FallbackUnavailable("restore_missing")
            with Catalog(verify) as after:
                total=after.db.execute(
                    "SELECT count(*) FROM affiliate_links WHERE campaign=?",
                    (sites()[site_key]["campaign"],)).fetchone()[0]
            if total < count+converted:
                raise FallbackUnavailable("links_not_persisted")
        return {"mode":"LIVE_CACHE_ONLY", "site_key":site_key,
                "eligible_for_warmup":len(keys), "existing_cached_links":count,
                "converted":converted, "snapshot_saved":stored["state_saved"],
                "api_interrupted":error is not None,
                "retention_pending":stored.get("retention_pending",False)}


def main() -> int:
    p=argparse.ArgumentParser(description="C7: cache de links para fallback sem publicação")
    p.add_argument("--site",required=True)
    p.add_argument("--config",required=True)
    p.add_argument("--rules",required=True)
    p.add_argument("--limit",type=int,default=1)
    p.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    try:
        result=warmup(args.site,Path(args.config),Path(args.rules),args.limit,args.dry_run)
        print("V31_C7_WARMUP_PASS")
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception:
        print("V31_C7_WARMUP_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
