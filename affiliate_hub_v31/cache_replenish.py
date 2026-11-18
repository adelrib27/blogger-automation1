"""C8 — Reposição equitativa de links afiliados por campanha no R2.

API Shopee é chamada APENAS em --execute, com orçamento GLOBAL
de 1 a 3 mutations por execução; depois de uma falha, para tudo.
Um snapshot R2 por execução, preservando o cache de todos os sites.
Cadastro de novos blogs via shadow.d/*.json + sites.d/*.json.
Sem publicador, sem tocar imagens ou WordPress/Blogger.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import date
from pathlib import Path

from .catalog import Catalog
from .converter import ConversionError, convert_one
from .fallback_v23 import FallbackUnavailable, load_configuration
from .link_warmup import warmup_candidates
from .r2_state import R2State, verify_database
from .shadow_audit import ShadowError, audit_site, load_profiles
from .routing import sites

MAX_GLOBAL_BUDGET = 3


def rotated_sites(names: list[str], ordinal: int, budget: int) -> list[str]:
    """Fair rotation independent of blog naming and number of registered sites."""
    if not isinstance(budget,int) or not 1<=budget<=MAX_GLOBAL_BUDGET:
        raise ShadowError("budget_invalid")
    if not isinstance(ordinal,int) or ordinal<1:
        raise ShadowError("rotation_invalid")
    ordered=sorted(names)
    if not ordered:
        return []
    start=(ordinal*budget)%len(ordered)
    return ordered[start:]+ordered[:start]


def replenish(storage: R2State, selected: str = "all", budget: int = 3,
              execute: bool = False, *, ordinal: int | None = None,
              profiles: dict | None = None,
              app_id: str = "", app_secret: str = "") -> dict:
    if not isinstance(budget,int) or not 1 <= budget <= MAX_GLOBAL_BUDGET:
        raise ShadowError("budget_invalid")
    configs=load_profiles() if profiles is None else profiles
    if selected!="all" and selected not in configs:
        raise ShadowError("unknown_or_unconfigured_site")
    names=([selected] if selected!="all" else
           rotated_sites(list(configs),date.today().toordinal()
                         if ordinal is None else ordinal,budget))
    per_site=(budget if selected!="all" else 1)
    if execute and (not app_id.strip() or not app_secret.strip()):
        raise ConversionError("credentials_missing")
    with tempfile.TemporaryDirectory(prefix="v31-c8-replenish-") as temp:
        file=Path(temp)/"catalog.sqlite3"
        if not storage.restore_to(file):
            raise ShadowError("r2_catalog_missing")
        verify_database(file)
        before={}
        plan=[]
        actual=0
        interrupted=False
        mutation_attempts=0
        with Catalog(file) as catalog:
            for key in names:
                if len(plan)>=len(configs) or mutation_attempts>=budget:
                    break
                profile=configs[key]
                current=audit_site(file,profile)
                before[key]=catalog.db.execute(
                    "SELECT COUNT(*) FROM affiliate_links WHERE campaign=?",
                    (sites()[key]["campaign"],)).fetchone()[0]
                if current["state"]=="SHADOW_READY":
                    plan.append({"site_key":key,"status":"SUFFICIENT",
                                 "eligible_for_next_conversion":0,"converted":0})
                    continue
                config,rules=load_configuration(profile["_config_file"],
                                                profile["_rules_file"])
                candidates=warmup_candidates(catalog,key,config,rules,
                           min(per_site,budget-mutation_attempts))
                if not candidates:
                    plan.append({"site_key":key,"status":"NO_MATCHING_PRODUCT",
                                 "eligible_for_next_conversion":0,"converted":0})
                    continue
                state={"site_key":key,"status":"PLAN_ONLY" if not execute else "ATTEMPTED",
                       "eligible_for_next_conversion":len(candidates),
                       "converted":0}
                plan.append(state)
                if not execute:
                    # Only plan a global maximum, even if some sites lack products.
                    if sum(x["eligible_for_next_conversion"] for x in plan)>=budget:
                        break
                    continue
                for product_key in candidates:
                    if mutation_attempts>=budget:
                        break
                    mutation_attempts+=1
                    try:
                        _,created=convert_one(catalog,product_key,
                                              sites()[key]["campaign"],app_id,app_secret)
                    except ConversionError:
                        interrupted=True
                        state["status"]="API_INTERRUPTED"
                        break
                    if created:
                        state["converted"]+=1
                        actual+=1
                if interrupted:
                    break
            if not catalog.integrity():
                raise ShadowError("catalog_integrity_failed")
        saved={"state_saved":False,"retention_pending":False}
        if execute and actual:
            saved=storage.save_from(file)
            if not saved["state_saved"]:
                raise ShadowError("r2_snapshot_not_saved")
            restored=Path(temp)/"restored.sqlite3"
            if not storage.restore_to(restored):
                raise ShadowError("r2_restore_missing")
            with Catalog(restored) as verification:
                delta=0
                for entry in plan:
                    if entry["converted"]:
                        key=entry["site_key"]
                        latest=verification.db.execute(
                            "SELECT COUNT(*) FROM affiliate_links WHERE campaign=?",
                            (sites()[key]["campaign"],)).fetchone()[0]
                        if latest<before[key]+entry["converted"]:
                            raise ShadowError("r2_link_cache_verify_failed")
                        delta+=entry["converted"]
                if delta!=actual or not verification.integrity():
                    raise ShadowError("r2_cache_integrity_failed")
        return {
            "mode":"CACHE_LIVE_ONLY" if execute else "DRY_RUN",
            "sites_configured":len(configs),
            "sites_inspected":len(plan),
            "global_mutation_budget":budget,
            "shopee_mutation_attempts":mutation_attempts,
            "converted":actual,
            "api_interrupted":interrupted,
            "r2_snapshot_saved":saved["state_saved"],
            "retention_pending":saved.get("retention_pending",False),
            "publication_calls":0,
            "plan":plan,
        }


def main() -> int:
    parser=argparse.ArgumentParser(description="C8: lote controlado de cache, nunca publica")
    parser.add_argument("--site",default="all")
    parser.add_argument("--budget",type=int,default=3)
    parser.add_argument("--execute",action="store_true",
                        help="Permite conversões comerciais limitadas; sem esta flag é somente leitura")
    args=parser.parse_args()
    try:
        summary=replenish(R2State.from_env(),args.site,args.budget,args.execute,
            app_id=os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID",""),
            app_secret=os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET",""))
        print("V31_C8_REPLENISH_"+("PARTIAL_API_INTERRUPTED"
              if summary["api_interrupted"] else "PASS"))
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        return 4 if summary["api_interrupted"] else 0
    except Exception:
        print("V31_C8_REPLENISH_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
