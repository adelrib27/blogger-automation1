"""V31 C34 — conversão sob demanda para qualquer blog REAL cadastrado.

Não depende de shadow.d, keywords de 3 WordPress ou temas previstos.
Tema vem da solicitação do novo blog; a campanha só é obtida da rota
AUTÊNTICA do blog já criado. Um blog hipotético nunca recebe link.

DRY_RUN por padrão; apenas --execute gera URLs oficiais, global 1–3
mutações Shopee, com verificação por chave+campanha após salvar o R2.
Nenhum publicador é acionado.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from .catalog import Catalog, host_allowed
from .converter import ConversionError, convert_one
from .r2_state import R2State, verify_database
from .routing import sites
from .site_launch_plan import preview_site_launch

MAX_MUTATIONS_PER_RUN = 3


class UniversalConversionError(ValueError):
    pass


def _candidates(catalog: Catalog, *, site_key: str, topic: str,
                budget: int) -> tuple[str,list[str]]:
    route=sites().get(site_key)
    if route is None:
        raise UniversalConversionError("real_registered_site_required")
    if type(budget) is not int or not 1<=budget<=MAX_MUTATIONS_PER_RUN:
        raise UniversalConversionError("mutation_budget_invalid")
    if not isinstance(topic,str) or not topic.strip() or len(topic)>160:
        raise UniversalConversionError("topic_invalid")
    campaign=route["campaign"]
    plan=preview_site_launch(catalog,topic=topic,
        platform=route["platform"],site_key=site_key,
        max_items=24,max_per_shop=1,commercial_only=True)
    selected=[]
    for item in plan["approved_catalog_candidates"]:
        key=item["product_key"]
        if not isinstance(key,str) or catalog.for_conversion(key) is None:
            continue
        if catalog.cached_link(key,campaign) is not None:
            continue
        if item.get("affiliate_status") != "requires_conversion":
            continue
        selected.append(key)
        if len(selected)>=budget:
            break
    return campaign,selected


def convert_for_registered_blog(
    storage: R2State, *, site_key: str, topic: str,
    budget: int=1, execute: bool=False,
    app_id: str="", app_secret: str="",
) -> dict:
    """Sem credencial de site real, sem conversão; nunca inventar campanha."""
    if execute and (not app_id.strip() or not app_secret.strip()):
        raise UniversalConversionError("shopee_credentials_missing")
    with tempfile.TemporaryDirectory(prefix="v31-universal-conv-") as folder:
        path=Path(folder)/"snapshot.sqlite3"
        if not storage.restore_to(path):
            raise UniversalConversionError("catalog_missing")
        verify_database(path)
        before_stat=None
        created_keys=[]
        interrupted=False
        attempts=0
        with Catalog(path) as cat:
            before_stat=cat.stats()
            campaign,keys=_candidates(
                cat,site_key=site_key,topic=topic,budget=budget)
            if execute:
                for key in keys:
                    attempts+=1
                    try:
                        _,created=convert_one(cat,key,campaign,app_id,app_secret)
                    except ConversionError:
                        interrupted=True
                        break
                    if created:
                        created_keys.append(key)
            if not cat.integrity():
                raise UniversalConversionError("catalog_integrity_failed")
            after_stat=cat.stats()
            if after_stat["products"]!=before_stat["products"] or \
               after_stat["eligible"]!=before_stat["eligible"] or \
               after_stat["review"]!=before_stat["review"]:
                raise UniversalConversionError("catalog_changed_by_conversion")
        saved=False
        if created_keys:
            receipt=storage.save_from(path)
            if not receipt.get("state_saved"):
                raise UniversalConversionError("r2_persistence_failed")
            restored=Path(folder)/"restored.sqlite3"
            if not storage.restore_to(restored):
                raise UniversalConversionError("r2_restore_failed")
            verify_database(restored)
            with Catalog(restored) as cat:
                if cat.stats()["products"]!=before_stat["products"]:
                    raise UniversalConversionError("r2_products_changed")
                if cat.stats()["cached_affiliate_links"] \
                   < before_stat["cached_affiliate_links"]+len(created_keys):
                    raise UniversalConversionError("r2_link_count_invalid")
                for key in created_keys:
                    url=cat.cached_link(key,campaign)
                    if not url or not host_allowed(url,allow_short=True):
                        raise UniversalConversionError("r2_exact_campaign_link_missing")
            saved=True
        return {
            "mode":"CACHE_ONLY" if execute else "DRY_RUN",
            "registered_site_required":True,
            "campaign_taken_only_from_site_registry":True,
            "candidate_count":len(keys),
            "shopee_mutation_attempts":attempts,
            "converted":len(created_keys),
            "api_interrupted":interrupted,
            "r2_snapshot_saved_and_verified":saved,
            "r2_writes":int(saved),
            "publication_calls":0,
            "new_blog_creation_calls":0,
            "no_cross_campaign_links":True,
        }


def main()->int:
    p=argparse.ArgumentParser(description="Conversor universal de blog real; nunca publica")
    p.add_argument("--site-key",required=True)
    p.add_argument("--topic",required=True)
    p.add_argument("--budget",type=int,default=1)
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    try:
        report=convert_for_registered_blog(
            R2State.from_env(),site_key=args.site_key,
            topic=args.topic,budget=args.budget,execute=args.execute,
            app_id=os.getenv("V31_EDITORIAL_SHOPEE_APP_ID",""),
            app_secret=os.getenv("V31_EDITORIAL_SHOPEE_APP_SECRET",""))
        print("V31_UNIVERSAL_CONVERTER_"+(
            "API_INTERRUPTED" if report["api_interrupted"] else "PASS"))
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 4 if report["api_interrupted"] else 0
    except Exception as exc:
        print("V31_UNIVERSAL_CONVERTER_FAILED_"+type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
