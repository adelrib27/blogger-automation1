"""C8 — SHADOW read-only da capacidade de fallback CSV/R2 por blog.

- Lê uma vez o catálogo R2 privado, sem Shopee/API de publicação.
- Configuração modular: shadow.d/*.json + sites.d/*.json.
- Quantifica apenas links convertidos utilizáveis no contrato editorial do blog,
  não confunde produtos disponíveis no CSV com links afiliados.
- Não imprime nomes, URLs, campanhas, IDs comerciais nem credenciais.
- "SHADOW_READY" NÃO significa aprovação de publicação.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import tempfile
from pathlib import Path

from .catalog import Catalog
from .fallback_v23 import candidates_from_catalog, load_configuration
from .r2_state import R2State, verify_database
from .routing import sites

ROOT = Path(__file__).resolve().parents[1]
SHADOW_DIR = Path(__file__).with_name("shadow.d")
FIELDS = {"site_key", "config", "rules", "daily_slots", "reserve_days",
          "required_source_categories"}
MAX_PROFILES = 5000


class ShadowError(ValueError):
    pass


def relative_config(path: str, root: Path = ROOT) -> Path:
    if (not isinstance(path, str) or not 1 <= len(path) <= 180 or
            not re.fullmatch(r"[a-zA-Z0-9_./-]+",path) or
            path.startswith(("/", ".")) or ".." in path.split("/")):
        raise ShadowError("unsafe_profile_path")
    folder=root.resolve()
    target=(folder/path).resolve()
    if not target.is_relative_to(folder) or not target.is_file() or target.is_symlink():
        raise ShadowError("configuration_missing_or_untrusted")
    return target


def load_profiles(directory: Path = SHADOW_DIR, *, root: Path = ROOT) -> dict:
    if not directory.is_dir() or directory.is_symlink():
        raise ShadowError("shadow_profiles_missing")
    entries=list(sorted(directory.glob("*.json")))
    if not entries or len(entries)>MAX_PROFILES:
        raise ShadowError("shadow_profiles_count_invalid")
    available_sites=sites()
    profiles={}
    for path in entries:
        if path.is_symlink() or not path.is_file():
            raise ShadowError("profile_file_invalid")
        try:
            data=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,ValueError,UnicodeError):
            raise ShadowError("profile_file_invalid") from None
        if not isinstance(data,dict) or set(data)!=FIELDS:
            raise ShadowError("profile_schema_invalid")
        key=data["site_key"]
        if (not isinstance(key,str) or key not in available_sites
                or key in profiles or path.stem!=key):
            raise ShadowError("profile_site_invalid")
        for attr in ("daily_slots","reserve_days"):
            if (type(data[attr]) is not int or not 1 <= data[attr] <= 24):
                raise ShadowError("profile_daily_limit_invalid")
        if (not isinstance(data["required_source_categories"],list)
                or len(data["required_source_categories"])>60
                or len(data["required_source_categories"])!=len(set(
                    str(x) for x in data["required_source_categories"]))
                or any(not isinstance(x,str) or not 1 <= len(x) <= 80
                       for x in data["required_source_categories"])):
            raise ShadowError("profile_categories_invalid")
        data["_config_file"]=relative_config(data["config"],root)
        data["_rules_file"]=relative_config(data["rules"],root)
        profiles[key]=data
    return profiles


def audit_site(catalog_path: Path, profile: dict) -> dict:
    site=sites()[profile["site_key"]]
    cfg,rules=load_configuration(profile["_config_file"],profile["_rules_file"])
    expected=set(profile["required_source_categories"])
    if not expected.issubset(set(cfg["categories"])):
        raise ShadowError("profile_required_categories_unknown")
    # O adaptador já audita nichos, intenção, URL da imagem e o cache
    # de afiliado EXCLUSIVO da campanha do blog.
    rows=candidates_from_catalog(catalog_path,profile["site_key"],cfg,rules,limit=100)
    try:
        with sqlite3.connect(f"file:{catalog_path.resolve()}?mode=ro",uri=True) as db:
            cache_total=db.execute(
                "SELECT COUNT(*) FROM affiliate_links WHERE campaign=?",
                (site["campaign"],)).fetchone()[0]
    except (sqlite3.Error,OSError):
        raise ShadowError("cache_count_failed") from None
    distribution={k:0 for k in cfg["categories"]}
    for row in rows:
        for category in row["categories"]:
            if category in distribution:
                distribution[category]+=1
    missing=sorted(category for category in expected
                   if distribution.get(category,0)<1)
    target=profile["daily_slots"]*profile["reserve_days"]
    count=len(rows)
    ready=count>=target and not missing
    return {
        "site_key":profile["site_key"],
        "platform":site["platform"],
        "cached_links_for_campaign":cache_total,
        "usable_cached_products":count,
        "daily_slots":profile["daily_slots"],
        "target_reserve_days":profile["reserve_days"],
        "target_usable_products":target,
        "estimated_full_days":count//profile["daily_slots"],
        "categories_represented":sum(bool(n) for n in distribution.values()),
        "categories_in_profile":len(distribution),
        "required_categories_missing":missing,
        "state":"SHADOW_READY" if ready else "NOT_READY",
        "publication_enabled_by_shadow":False,
    }


def audit(storage: R2State, selected: str = "all",
          *, profiles: dict | None = None) -> dict:
    configs=load_profiles() if profiles is None else profiles
    if selected!="all" and selected not in configs:
        raise ShadowError("unknown_or_unconfigured_site")
    subset=configs if selected=="all" else {selected:configs[selected]}
    with tempfile.TemporaryDirectory(prefix="v31-c8-shadow-") as temp:
        path=Path(temp)/"catalog.sqlite3"
        if not storage.restore_to(path):
            raise ShadowError("r2_catalog_missing")
        verify_database(path)
        with Catalog(path) as catalog:
            summary=catalog.stats()
        reports=[audit_site(path,profile) for profile in subset.values()]
    return {
        "mode":"SHADOW_READ_ONLY",
        "total_registered_sites":len(sites()),
        "profiles_evaluated":len(reports),
        "catalog_products":summary["products"],
        "catalog_eligible":summary["eligible"],
        "catalog_cached_links":summary["cached_affiliate_links"],
        "sites_shadow_ready":sum(row["state"]=="SHADOW_READY" for row in reports),
        "sites_not_ready":sum(row["state"]!="SHADOW_READY" for row in reports),
        "publication_calls":0,
        "shopee_api_calls":0,
        "r2_writes":0,
        "note":"shadow_ready_is_not_live_publication_approval",
        "sites":reports,
    }


def main() -> int:
    parser=argparse.ArgumentParser(description="C8: diagnóstico R2 sem mutações/publicações")
    parser.add_argument("--site",default="all")
    args=parser.parse_args()
    try:
        report=audit(R2State.from_env(),args.site)
        print("V31_C8_SHADOW_READONLY_PASS")
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception:
        print("V31_C8_SHADOW_READONLY_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
