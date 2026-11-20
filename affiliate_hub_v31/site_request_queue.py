"""C37 — fila de pedidos de blogs REAIS, sem antecipar nichos ou campanhas.

Qualquer blog registrado pode ter um pedido com o tema informado quando
ele foi criado. Um cron independente das três lojas WordPress verifica R2,
seleciona somente produtos aprovados e converte 0–3 URLs oficiais na campanha
real de cada site; nunca chama publicadores nem manipula métricas.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import date
from pathlib import Path

from .catalog import Catalog,host_allowed
from .converter import ConversionError,convert_one
from .r2_state import R2State,verify_database
from .routing import sites
from .site_launch_plan import preview_site_launch

REQUESTS_DIR=Path(__file__).with_name("site_requests.d")
VERIFIER_PROFILES=Path(__file__).with_name("autonomous_review_sources.json")
MAX_REQUESTS=500
MAX_BUDGET=3


class RequestQueueError(ValueError):
    pass


def load_requests(directory:Path=REQUESTS_DIR)->list[dict]:
    """Valida pedidos reais, nunca inventa blog, nicho ou campanha."""
    if not directory.is_dir() or directory.is_symlink():
        raise RequestQueueError("request_directory_missing")
    files=sorted(directory.glob("*.json"))
    if len(files)>MAX_REQUESTS:
        raise RequestQueueError("too_many_site_requests")
    registry=sites()
    found=set()
    entries=[]
    required={"site_key","topic","platform","articles","enabled"}
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise RequestQueueError("untrusted_request_file")
        try:
            doc=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,ValueError,UnicodeError):
            raise RequestQueueError("request_invalid_json") from None
        if not isinstance(doc,dict) or set(doc)!=required:
            raise RequestQueueError("request_schema_invalid")
        key=doc["site_key"]
        if not isinstance(key,str) or not re.fullmatch(r"[a-z0-9_]{3,50}",key) or \
           path.stem!=key or key in found:
            raise RequestQueueError("request_site_key_invalid")
        found.add(key)
        site=registry.get(key)
        if site is None or site["platform"]!=doc["platform"] or \
           site.get("publish_enabled") is not False:
            raise RequestQueueError("real_registered_site_required")
        topic=doc["topic"]
        if not isinstance(topic,str) or not topic.strip() or len(topic)>160:
            raise RequestQueueError("request_topic_invalid")
        if doc["articles"] is not None and (type(doc["articles"]) is not int or not 1<=doc["articles"]<=24):
            raise RequestQueueError("request_articles_invalid")
        if type(doc["enabled"]) is not bool:
            raise RequestQueueError("request_enabled_invalid")
        if doc["enabled"]:
            entries.append(doc)
    return entries


def _rotation(entries:list[dict],ordinal:int)->list[dict]:
    if not entries:
        return []
    start=ordinal%len(entries)
    return entries[start:]+entries[:start]


def autonomous_sites_for_writes() -> set[str]:
    if os.environ.get("V31_AUTODRAFT_ACTIVE") != "true":
        return set()
    registry = json.loads(VERIFIER_PROFILES.read_text(encoding="utf-8"))
    return {item["site_key"] for item in load_requests() if item["site_key"] in registry}


def process_requests(storage:R2State, *, directory:Path=REQUESTS_DIR,
                     budget:int=3,execute:bool=False,
                     app_id:str="",app_secret:str="",
                     ordinal:int|None=None)->dict:
    if type(budget) is not int or not 1<=budget<=MAX_BUDGET:
        raise RequestQueueError("budget_invalid")
    if type(execute) is not bool:
        raise RequestQueueError("execute_invalid")
    if ordinal is not None and (type(ordinal) is not int or ordinal<0):
        raise RequestQueueError("rotation_invalid")
    requests=_rotation(load_requests(directory),
                       date.today().toordinal() if ordinal is None else ordinal)
    if not requests:
        return {
            "mode":"SITE_REQUEST_QUEUE_LIVE_CACHE_ONLY" if execute else "DRY_RUN",
            "requests_active":0,"requests_evaluated":0,
            "conversion_candidates":0,"shopee_mutation_attempts":0,
            "converted":0,"ready_review_jobs":0,
            "needs_curation":0,"api_interrupted":False,
            "r2_snapshot_saved_and_verified":False,"publication_calls":0,
        }
    with tempfile.TemporaryDirectory(prefix="v31-c37-queue-") as tmp:
        verified_routes = json.loads(VERIFIER_PROFILES.read_text(encoding="utf-8"))
        path=Path(tmp)/"catalog.sqlite3"
        if not storage.restore_to(path):
            raise RequestQueueError("catalog_missing")
        verify_database(path)
        plans=[]
        selected=[]
        attempted_keys=set()
        converted=[]
        before_campaign={}
        interrupted=False
        mutation_attempts=0
        with Catalog(path) as cat:
            before=cat.stats()
            for request in requests:
                key=request["site_key"]
                route=sites()[key]
                campaign=route["campaign"]
                plan=preview_site_launch(
                    cat,topic=request["topic"],platform=request["platform"],
                    site_key=key,max_items=(24 if request["articles"] is None else request["articles"]),max_per_shop=1)
                if not plan["registered_site"] or plan["can_publish"] is not False:
                    raise RequestQueueError("request_plan_unsafe")
                before_campaign[campaign]=cat.db.execute(
                    "SELECT count(*) FROM affiliate_links WHERE campaign=?",
                    (campaign,)).fetchone()[0]
                ready=plan["cached_for_campaign"]
                available=[]
                approved = plan["approved_catalog_candidates"]
                profiled = verified_routes.get(key, {}).get("offers", {})
                pending_profiles = {sku for sku in profiled if cat.cached_link(sku, campaign) is None}
                if pending_profiles:
                    wider = preview_site_launch(cat, topic=request["topic"], platform=request["platform"],
                                                site_key=key, max_items=24, max_per_shop=4)
                    priority = [item for item in wider["approved_catalog_candidates"]
                                if item["product_key"] in pending_profiles]
                    priority_keys = {item["product_key"] for item in priority}
                    approved = priority + [item for item in approved if item["product_key"] not in priority_keys]
                for item in approved:
                    key_product=item["product_key"]
                    if (key_product not in attempted_keys and
                        item["affiliate_status"]=="requires_conversion" and
                        cat.for_conversion(key_product) is not None and
                        cat.cached_link(key_product,campaign) is None):
                        available.append((key_product,campaign))
                plans.append({"ready":ready,"eligible":len(available),
                              "review":plan["review_queue_count"]})
                # Rodada equitativa: um SKU por blog antes da próxima rodada.
                selected.append(available)
            queue=[]
            while len(queue)<budget and any(selected):
                for offers in selected:
                    if offers and len(queue)<budget:
                        key,campaign=offers.pop(0)
                        queue.append((key,campaign))
                if len(queue)>=budget:
                    break
            if execute and queue and (not app_id.strip() or not app_secret.strip()):
                raise RequestQueueError("shopee_credentials_missing")
            if execute:
                for key,campaign in queue:
                    mutation_attempts+=1
                    try:
                        _,new=convert_one(cat,key,campaign,app_id,app_secret)
                    except ConversionError:
                        interrupted=True
                        break
                    if new:
                        converted.append((key,campaign))
            if not cat.integrity() or cat.stats()["products"]!=before["products"] or \
               cat.stats()["eligible"]!=before["eligible"]:
                raise RequestQueueError("catalog_changed")
        saved=False
        if converted:
            receipt=storage.save_from(path)
            if not receipt.get("state_saved"):
                raise RequestQueueError("r2_save_failed")
            verified=Path(tmp)/"restored.sqlite3"
            if not storage.restore_to(verified):
                raise RequestQueueError("r2_restore_failed")
            verify_database(verified)
            with Catalog(verified) as cat:
                after=cat.stats()
                if (after["products"]!=before["products"] or
                    after["cached_affiliate_links"]<
                    before["cached_affiliate_links"]+len(converted)):
                    raise RequestQueueError("r2_counts_not_preserved")
                for key,campaign in converted:
                    url=cat.cached_link(key,campaign)
                    if not url or not host_allowed(url,allow_short=True):
                        raise RequestQueueError("exact_campaign_link_missing")
            saved=True
        return {
            "mode":"SITE_REQUEST_QUEUE_LIVE_CACHE_ONLY" if execute else "DRY_RUN",
            "requests_active":len(requests),
            "requests_evaluated":len(plans),
            "conversion_candidates":len(queue),
            "shopee_mutation_attempts":mutation_attempts,
            "converted":len(converted),
            "ready_review_jobs":sum(x["ready"] for x in plans),
            "needs_curation":sum(x["review"] for x in plans),
            "api_interrupted":interrupted,
            "r2_snapshot_saved_and_verified":saved,
            "publication_calls":0,
        }


def main()->int:
    p=argparse.ArgumentParser(description="V31 — pedidos reais por nicho aberto, 0 posts")
    p.add_argument("--budget",type=int,default=3)
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    try:
        result=process_requests(
            R2State.from_env(),budget=args.budget,execute=args.execute,
            app_id=os.getenv("V31_EDITORIAL_SHOPEE_APP_ID",""),
            app_secret=os.getenv("V31_EDITORIAL_SHOPEE_APP_SECRET",""))
        print("V31_C37_SITE_REQUEST_QUEUE_"+(
            "PARTIAL_API_INTERRUPTED" if result["api_interrupted"] else "PASS"))
        print(json.dumps(result,sort_keys=True))
        return 4 if result["api_interrupted"] else 0
    except Exception as exc:
        print("V31_C37_SITE_REQUEST_QUEUE_FAILED_"+type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
