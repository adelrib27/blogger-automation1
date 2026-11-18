"""C37 — envelopes editoriais privados no R2, separados por site/campanha.

O catalogo principal R2 continua fonte da verdade para os links.
Este sidecar entrega SOMENTE ofertas verificadas da campanha exata ao
orquestrador do blog. Estado REVIEW_REQUIRED, nunca autoriza postagem.
Nem links, títulos, IDs ou campanhas aparecem nos logs de execução.
"""
from __future__ import annotations

import hashlib
import io
import json
import re

from .catalog import host_allowed
from .routing import sites

PREFIX="v31-editorial/editorial-handoff/"
SCHEMA="v31-editorial-handoff/v1"


class HandoffStorageError(ValueError):
    pass


def _canonical(data:dict)->bytes:
    return json.dumps(data,sort_keys=True,ensure_ascii=False,
                      separators=(",",":")).encode("utf-8")


def validate_report(report:dict,site_key:str)->None:
    if (not isinstance(site_key,str) or
        not re.fullmatch(r"[a-z0-9_]{3,50}",site_key)):
        raise HandoffStorageError("site_key_invalid")
    route=sites().get(site_key)
    if route is None or route.get("publish_enabled") is not False:
        raise HandoffStorageError("real_site_not_registered")
    if (not isinstance(report,dict) or
        report.get("mode")!="C36_UNIVERSAL_HANDOFF_SAFE" or
        report.get("site_registered") is not True or
        report.get("requires_registration") is not False or
        report.get("can_publish") is not False or
        report.get("publication_calls")!=0 or
        report.get("platform")!=route["platform"]):
        raise HandoffStorageError("unsafe_handoff_report")
    jobs=report.get("ready_review_jobs")
    if not isinstance(jobs,list) or len(jobs)>24:
        raise HandoffStorageError("invalid_job_list")
    seen=set()
    for job in jobs:
        if (not isinstance(job,dict) or
            job.get("site_key")!=site_key or
            job.get("campaign")!=route["campaign"] or
            job.get("platform")!=route["platform"] or
            job.get("publication_allowed") is not False or
            job.get("status")!="REVIEW_REQUIRED" or
            not isinstance(job.get("product"),dict)):
            raise HandoffStorageError("job_campaign_or_state_invalid")
        product=job["product"]
        if (not host_allowed(str(product.get("offerLink","")),allow_short=True) or
            not host_allowed(str(product.get("productLink",""))) or
            product.get("sourceModes")!=["csv_r2_verified_affiliate_cache"]):
            raise HandoffStorageError("job_unverified_offer")
        key=job.get("product_key")
        if not isinstance(key,str) or key in seen:
            raise HandoffStorageError("duplicate_or_invalid_product")
        seen.add(key)
    for item in report.get("future_review_plans",[]):
        raise HandoffStorageError("future_blog_must_not_persist")
    for item in report.get("conversion_review_plans",[]):
        if not isinstance(item,dict) or
            item.get("campaign")!=route["campaign"] or
            item.get("affiliate_url") is not None or
            item.get("can_publish") is not False:
            raise HandoffStorageError("invalid_conversion_plan")


def persist_private_handoff(storage,*,site_key:str,report:dict)->dict:
    """S3 versão->hash de leitura->ponteiro; idempotente; sem logs privados."""
    validate_report(report,site_key)
    payload={"schema":SCHEMA,"site_key":site_key,
             "campaign":sites()[site_key]["campaign"],
             "platform":sites()[site_key]["platform"],
             "requested_articles":report["requested_articles"],
             "status":"REVIEW_REQUIRED",
             "jobs":report["ready_review_jobs"],
             "conversion_required":len(report["conversion_required_keys"]),
             "review_candidates":report["review_candidates"],
             "publication_allowed":False}
    raw=_canonical(payload)
    if not 1<=len(raw)<=1_000_000:
        raise HandoffStorageError("handoff_size_invalid")
    sha=hashlib.sha256(raw).hexdigest()
    key=f"{PREFIX}{site_key}/versions/{sha}.json"
    pointer=f"{PREFIX}{site_key}/CURRENT.json"
    try:
        storage.s3.put_object(Bucket=storage.bucket,Key=key,Body=raw,
            ContentType="application/json",
            Metadata={"sha256":sha},CacheControl="no-store")
        read=storage.s3.get_object(Bucket=storage.bucket,Key=key)
        verified=read["Body"].read(1_000_001)
        if hashlib.sha256(verified).hexdigest()!=sha:
            raise HandoffStorageError("r2_handoff_verify_failed")
        manifest={"schema":SCHEMA,"key":key,"sha256":sha,
                  "site_key":site_key,"publication_allowed":False}
        storage.s3.put_object(Bucket=storage.bucket,Key=pointer,
            Body=_canonical(manifest),ContentType="application/json",
            CacheControl="no-store")
    except HandoffStorageError:
        raise
    except Exception:
        raise HandoffStorageError("r2_handoff_save_failed") from None
    return {"saved_and_verified":True,
            "review_jobs":len(report["ready_review_jobs"]),
            "conversion_required":len(report["conversion_required_keys"]),
            "publication_calls":0}


def read_private_handoff(storage,*,site_key:str)->dict:
    """Leitura para gerador autenticado; revalida autorização da campanha."""
    if not isinstance(site_key,str) or not re.fullmatch(r"[a-z0-9_]{3,50}",site_key):
        raise HandoffStorageError("site_key_invalid")
    try:
        pointer=f"{PREFIX}{site_key}/CURRENT.json"
        meta=json.loads(storage.s3.get_object(Bucket=storage.bucket,
                          Key=pointer)["Body"].read(4096))
        expected=f"{PREFIX}{site_key}/versions/{meta['sha256']}.json"
        if meta.get("schema")!=SCHEMA or meta.get("key")!=expected or
           meta.get("publication_allowed") is not False:
            raise HandoffStorageError("invalid_handoff_pointer")
        data=storage.s3.get_object(Bucket=storage.bucket,
                                  Key=expected)["Body"].read(1_000_001)
        if hashlib.sha256(data).hexdigest()!=meta["sha256"]:
            raise HandoffStorageError("handoff_integrity_failed")
        result=json.loads(data)
    except HandoffStorageError:
        raise
    except Exception:
        raise HandoffStorageError("handoff_unavailable") from None
    route=sites().get(site_key)
    if not route or result.get("campaign")!=route["campaign"] or
       result.get("site_key")!=site_key or
       result.get("publication_allowed") is not False or
       result.get("status")!="REVIEW_REQUIRED":
        raise HandoffStorageError("handoff_route_mismatch")
    return result
