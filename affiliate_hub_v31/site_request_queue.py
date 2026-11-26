"""C37 — fila de pedidos de blogs REAIS, sem antecipar nichos ou campanhas.

Qualquer blog registrado pode ter um pedido com o tema informado quando
ele foi criado. Um cron independente das três lojas WordPress verifica R2,
seleciona somente produtos aprovados e converte 0–3 URLs oficiais na campanha
real de cada site; nunca chama publicadores nem manipula métricas.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

from .catalog import Catalog,host_allowed
from .converter import ConversionError,convert_one
from .d1_http_runner import CloudflareD1HTTPRunner, D1HTTPError
from .r2_state import R2State,verify_database
from .routing import sites
from .editorial_scope_validation import is_route_in_active_scope
from .site_launch_plan import preview_site_launch
from .verified_supply import conversion_priority_keys, route_supply_keys, route_allows_sku

REQUESTS_DIR=Path(__file__).with_name("site_requests.d")
VERIFIER_PROFILES=Path(__file__).with_name("autonomous_review_sources.json")
MAX_REQUESTS=500
MAX_BUDGET=3


class RequestQueueError(ValueError):
    pass


def load_requests(directory:Path=REQUESTS_DIR, *, commercial:bool=False)->list[dict]:
    """Editorial por padrão; cache regular tem autorização independente e explícita."""
    if type(commercial) is not bool:
        raise RequestQueueError("request_mode_invalid")
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
        if not isinstance(doc,dict) or set(doc) not in (required, required | {"commercial_enabled"}):
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
        commercial_enabled=doc.get("commercial_enabled",doc["enabled"])
        if type(commercial_enabled) is not bool:
            raise RequestQueueError("request_commercial_enabled_invalid")
        if doc["enabled"] or commercial_enabled:
            # C140: nenhuma rota antiga/excluída nem blog não autenticado entra
            # no conversor ou nos writers por engano. Vale para TODO nicho.
            if not is_route_in_active_scope(site):
                raise RequestQueueError("site_outside_verified_active_scope")
        if commercial_enabled if commercial else doc["enabled"]:
            entries.append(doc)
    return entries


def _rotation(entries:list[dict],ordinal:int)->list[dict]:
    if not entries:
        return []
    start=ordinal%len(entries)
    return entries[start:]+entries[:start]


def autonomous_sites_for_writes() -> set[str]:
    """Return only sites explicitly migrated to the verified autonomous writer.

    V31_AUTODRAFT_ACTIVE is a global arm, *not* permission to migrate every
    registered route. Deployment must name one site until full rollout is
    separately authorized. Both old writers and the new scheduler use this
    function; they cannot disagree about who owns a migrated route.
    """
    if os.environ.get("V31_AUTODRAFT_ACTIVE") != "true":
        return set()
    registry = json.loads(VERIFIER_PROFILES.read_text(encoding="utf-8"))
    eligible = {item["site_key"] for item in load_requests()
                if item["site_key"] in registry}
    target = os.environ.get("V31_AUTODRAFT_ROLLOUT_SITE", "")
    if target == "all":
        return (eligible if os.environ.get("V31_AUTODRAFT_FULL_ROLLOUT_APPROVED")
                == "true" else set())
    return {target} if target in eligible else set()


def reserved_pilot_sku(site_key: str) -> str | None:
    rules = json.loads(VERIFIER_PROFILES.read_text(encoding="utf-8")).get(site_key, {})
    sku = rules.get("pilot_sku")
    return sku if sku in rules.get("offers", {}) else None


def claim_conversion_attempt(query, *, day_utc: str, campaign: str, product_key: str) -> bool:
    """Reserve a shared daily slot, but never reattempt this SKU+campaign on another day.

    A D1 attempt is not proof of successful conversion: if the former
    site-specific workflow got a shortlink without persisting R2, the universal
    converter must reconcile that outcome instead of issuing another POST.
    Keep other campaigns independent. The NOT EXISTS check lives in the
    conditional INSERT, not in a separate read-and-write race.
    """
    rows = query("""
      INSERT INTO v31_shopee_conversion_attempts (day_utc, slot, campaign, product_key)
      SELECT ?, COALESCE(max(slot), 0) + 1, ?, ?
      FROM v31_shopee_conversion_attempts WHERE day_utc=?
      HAVING COALESCE(max(slot), 0) < ?
      AND NOT EXISTS (
        SELECT 1 FROM v31_shopee_conversion_attempts
        WHERE campaign=? AND product_key=?
      )
      ON CONFLICT DO NOTHING
      RETURNING slot
    """, (day_utc, campaign, product_key, day_utc, MAX_BUDGET,
          campaign, product_key))
    return isinstance(rows, list) and len(rows) == 1


def process_requests(storage:R2State, *, directory:Path=REQUESTS_DIR,
                     budget:int=3,execute:bool=False,
                     app_id:str="",app_secret:str="",
                     ordinal:int|None=None, pilot_site_key:str|None=None,
                     target_site_key:str|None=None, target_product_key:str|None=None,
                     authenticated_cms_keys:list[str]|None=None,
                     reserve_conversion=None, previously_attempted=None)->dict:
    if type(budget) is not int or not 1<=budget<=MAX_BUDGET:
        raise RequestQueueError("budget_invalid")
    if type(execute) is not bool:
        raise RequestQueueError("execute_invalid")
    if ordinal is not None and (type(ordinal) is not int or ordinal<0):
        raise RequestQueueError("rotation_invalid")
    regular = pilot_site_key is None and target_site_key is None and target_product_key is None
    if previously_attempted is not None and not isinstance(previously_attempted, (set, frozenset)):
        raise RequestQueueError("historical_attempts_invalid")
    requests=_rotation(load_requests(directory, commercial=regular),
                       date.today().toordinal() if ordinal is None else ordinal)
    if (target_site_key is None) != (target_product_key is None):
        raise RequestQueueError("exact_target_site_and_sku_required")
    if target_site_key is not None:
        # One-off recovery must not silently act on multiple campaigns or
        # reuse an already published/drafted SKU from authenticated CMS.
        if (not execute or budget != 1 or pilot_site_key is not None
            or target_site_key not in autonomous_sites_for_writes()
            or not re.fullmatch(r"shopee:\d+:\d+",str(target_product_key))
            or type(authenticated_cms_keys) is not list
            or any(not isinstance(x,str) or not re.fullmatch(r"[a-f0-9]{64}",x)
                   for x in authenticated_cms_keys)):
            raise RequestQueueError("targeted_autodraft_migration_guard_failed")
        if hashlib.sha256(target_product_key.encode()).hexdigest() in authenticated_cms_keys:
            raise RequestQueueError("target_product_already_in_cms")
        requests = [r for r in requests if r["site_key"] == target_site_key]
        if not requests:
            raise RequestQueueError("target_site_request_disabled_or_missing")
    pilot_sku = None
    if pilot_site_key is not None:
        requests = [request for request in requests if request["site_key"] == pilot_site_key]
        pilot_sku = reserved_pilot_sku(pilot_site_key)
        if not requests or pilot_sku is None or budget != 1:
            raise RequestQueueError("conversion_registered_pilot_required")
    if not requests:
        return {
            "mode":"SITE_REQUEST_QUEUE_LIVE_CACHE_ONLY" if execute else "DRY_RUN",
            "requests_active":0,"requests_evaluated":0,
            "conversion_candidates":0,"shopee_mutation_attempts":0,
            "conversion_reservations_denied":0,
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
        attempted_keys=set(previously_attempted or ()) if regular else set()
        converted=[]
        before_campaign={}
        interrupted=False
        mutation_attempts=0
        denied_attempts=0
        with Catalog(path) as cat:
            before=cat.stats()
            migrated_sites = autonomous_sites_for_writes()
            for request in requests:
                key=request["site_key"]
                route=sites()[key]
                campaign=route["campaign"]
                plan=preview_site_launch(
                    cat,topic=request["topic"],platform=request["platform"],
                    site_key=key,max_items=(24 if request["articles"] is None else request["articles"]),max_per_shop=1, commercial_only=True)
                if not plan["registered_site"] or plan["can_publish"] is not False:
                    raise RequestQueueError("request_plan_unsafe")
                before_campaign[campaign]=cat.db.execute(
                    "SELECT count(*) FROM affiliate_links WHERE campaign=?",
                    (campaign,)).fetchone()[0]
                ready=plan["cached_for_campaign"]
                available=[]
                approved = plan["approved_catalog_candidates"]
                # Perfil factual é prioridade opcional; nunca bloqueia cache comercial.
                # A recuperação pontual mantém os seus gates independentes.
                preferred = (list(conversion_priority_keys(
                    cat, route, verified_routes.get(key, {})))
                    if key in migrated_sites else [])
                if target_site_key is not None:
                    if key != target_site_key or target_product_key not in preferred:
                        raise RequestQueueError("target_offer_not_in_verified_supply")
                    preferred = [target_product_key]
                profiled = verified_routes.get(key, {}).get("offers", {})
                pending_profiles = {sku for sku in profiled if cat.cached_link(sku, campaign) is None}
                if pending_profiles or pilot_sku:
                    wider = preview_site_launch(cat, topic=request["topic"], platform=request["platform"],
                                                site_key=key, max_items=24, max_per_shop=4, commercial_only=True)
                    priority = [item for item in wider["approved_catalog_candidates"]
                                if item["product_key"] in pending_profiles]
                    priority_keys = {item["product_key"] for item in priority}
                    approved = priority + [item for item in approved if item["product_key"] not in priority_keys]
                    if pilot_sku:
                        approved = [item for item in wider["approved_catalog_candidates"]
                                    if item["product_key"] == pilot_sku]
                        if not approved or cat.for_conversion(pilot_sku) is None:
                            raise RequestQueueError("conversion_pilot_offer_ineligible")
                        ready = int(cat.cached_link(pilot_sku, campaign) is not None)
                if pilot_sku:
                    # A operação de um piloto permanece exatamente isolada.
                    preferred = [sku for sku in preferred if sku == pilot_sku]
                elif target_site_key is not None:
                    # Recuperação pontual do writer continua restrita ao SKU exato.
                    approved = []
                # Cache-only sites can use eligible route supply without a
                # textual editorial template or manufacturer-specific profile.
                # Keep the actual route and independent product safety gates.
                if regular and request.get("commercial_enabled") is True and not request["enabled"]:
                    existing_keys = {item["product_key"] for item in approved}
                    for sku in route_supply_keys(cat, route, limit_per_path=35):
                        if sku not in existing_keys and not cat.cached_link(sku, campaign):
                            row = cat.db.execute(
                                "SELECT origin_url,image_url FROM products WHERE product_key=?", (sku,)).fetchone()
                            if row and host_allowed(row[0]) and isinstance(row[1],str) and row[1].startswith("https://"):
                                approved.append({"product_key":sku,"affiliate_status":"requires_conversion"})
                                existing_keys.add(sku)
                covered = {item["product_key"] for item in approved}
                priority = [{"product_key": sku, "affiliate_status": "requires_conversion"}
                            for sku in preferred if sku not in covered]
                approved = priority + approved
                for item in approved:
                    key_product=item["product_key"]
                    if ((campaign,key_product) not in attempted_keys and
                        item["affiliate_status"]=="requires_conversion" and
                        cat.for_conversion(key_product) is not None and
                        route_allows_sku(cat,route,key_product) and
                        cat.cached_link(key_product,campaign) is None):
                        available.append((key_product,campaign))
                        attempted_keys.add((campaign,key_product))
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
                    try:
                        reserved = reserve_conversion is None or reserve_conversion(campaign, key)
                    except D1HTTPError:
                        interrupted = True
                        break
                    if not reserved:
                        denied_attempts += 1
                        continue
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
            "commercial_only_requests":sum(not r["enabled"] for r in requests),
            "candidate_campaigns":sorted({campaign for _,campaign in queue}),
            "conversion_candidates":len(queue),
            "shopee_mutation_attempts":mutation_attempts,
            "conversion_reservations_denied":denied_attempts,
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
    p.add_argument("--pilot-site-key")
    p.add_argument("--target-site-key")
    p.add_argument("--target-product-key")
    args=p.parse_args()
    try:
        cms_keys = None
        if args.target_site_key or args.target_product_key:
            if (not args.target_site_key or not args.target_product_key
                    or not args.execute or args.budget != 1):
                raise RequestQueueError("exact_target_requires_one_real_conversion")
            from .reviewed_draft_delivery import read_draft_history
            history = read_draft_history(args.target_site_key)
            if (history.get("site_key") != args.target_site_key or
                    type(history.get("keys")) is not list):
                raise RequestQueueError("cms_history_authenticated_read_required")
            cms_keys = history["keys"]
        reserve_conversion = None
        previously_attempted = None
        if args.execute:
            query = CloudflareD1HTTPRunner.from_environment(allow_mutations=True)
            if not args.pilot_site_key and not args.target_site_key:
                history_rows = query("SELECT campaign, product_key FROM v31_shopee_conversion_attempts", ())
                if any(not isinstance(r,dict) or not isinstance(r.get("campaign"),str) or not isinstance(r.get("product_key"),str) for r in history_rows):
                    raise RequestQueueError("historical_attempts_untrusted")
                previously_attempted = {(r["campaign"],r["product_key"]) for r in history_rows}
            def reserve_conversion(campaign, product_key):
                return claim_conversion_attempt(
                    query, day_utc=datetime.now(timezone.utc).date().isoformat(),
                    campaign=campaign, product_key=product_key)
        result=process_requests(
            R2State.from_env(),budget=args.budget,execute=args.execute,
            app_id=os.getenv("V31_EDITORIAL_SHOPEE_APP_ID",""),
            app_secret=os.getenv("V31_EDITORIAL_SHOPEE_APP_SECRET",""),
            pilot_site_key=args.pilot_site_key, reserve_conversion=reserve_conversion,
            target_site_key=args.target_site_key,
            target_product_key=args.target_product_key,
            authenticated_cms_keys=cms_keys, previously_attempted=previously_attempted)
        print("V31_C37_SITE_REQUEST_QUEUE_"+(
            "PARTIAL_API_INTERRUPTED" if result["api_interrupted"] else "PASS"))
        print(json.dumps(result,sort_keys=True))
        return 4 if result["api_interrupted"] else 0
    except Exception as exc:
        print("V31_C37_SITE_REQUEST_QUEUE_FAILED_"+type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
