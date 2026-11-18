"""C39 — rever histórico REVIEW quando regras editoriais aprovadas evoluem.

Não confundir facetas oficiais com licença para anunciar.
Promoção exige simultaneamente: revisão antiga APENAS por taxonomia,
título correspondente a regra editorial explícita, compatibilidade
L1/L2 oficial com mapeamento editorial revisado, fonte única/consistente,
URL/imagem/IDs válidos, ausência de termos de risco, política não protegida.
Dry-run é padrão, execução cria auditoria e restaura snapshot R2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime,timezone
from pathlib import Path

from .catalog import Catalog,classify,host_allowed
from .curation_audit import PROTECTED_ROOTS
from .r2_state import R2State,verify_database
from .review_proposals import PATH_ROUTE_HINTS
from .source_policy_gate import source_safe_for_use
from .taxonomy import classify_title

MAX_PER_RUN=100


class ReclassificationError(ValueError):
    pass


def _link_hash(cat:Catalog)->str:
    h=hashlib.sha256()
    for row in cat.db.execute("""
        SELECT product_key,campaign,affiliate_url,verified_origin,updated_utc
        FROM affiliate_links ORDER BY product_key,campaign
    """):
        h.update(json.dumps(row,ensure_ascii=False,separators=(",",":")).encode())
        h.update(b"\n")
    return h.hexdigest()


def find_candidates(cat:Catalog,*,limit:int=MAX_PER_RUN)->tuple[list[dict],dict]:
    if type(limit) is not int or not 1<=limit<=MAX_PER_RUN:
        raise ReclassificationError("candidate_limit_invalid")
    has_facets=cat.db.execute("""
      SELECT 1 FROM sqlite_master WHERE type='table'
      AND name='product_source_categories'
    """).fetchone()
    if not has_facets:
        raise ReclassificationError("official_source_facets_missing")
    rows=cat.db.execute("""
      WITH facets AS (
        SELECT product_key,MIN(CASE WHEN status='matched'
              THEN level1 END) AS l1,
          MIN(CASE WHEN status='matched' THEN level2 END) AS l2,
          COUNT(*) AS source_count,
          COUNT(DISTINCT CASE WHEN status='matched'
              THEN level1 || char(31) || level2 END) AS branches,
          COUNT(DISTINCT CASE WHEN status='matched' AND level3!=''
              THEN level3 END) AS leaves,
          SUM(CASE WHEN status!='matched' THEN 1 ELSE 0 END) AS bad
        FROM product_source_categories GROUP BY product_key
      )
      SELECT p.product_key,p.title,p.description,p.shop_id,p.item_id,
        p.origin_url,p.image_url,p.moderation_reason,
        t.category,t.niche,t.status,t.reason,t.version,
        COALESCE(f.l1,''),COALESCE(f.l2,''),
        COALESCE(f.source_count,0),COALESCE(f.branches,0),
        COALESCE(f.leaves,0),COALESCE(f.bad,0)
      FROM products p
      JOIN product_taxonomy t ON t.product_key=p.product_key
      LEFT JOIN facets f ON f.product_key=p.product_key
      WHERE p.moderation='review' AND t.status='review'
      ORDER BY p.product_key
    """)
    result=[]
    counts={"review_records_scanned":0,"review_no_taxonomy_evidence":0,
            "unsafe_or_protected":0,"title_no_route":0,
            "source_editorial_route_mismatch":0,"supported_review_candidates":0}
    for row in rows:
        (key,title,description,shop,item,url,image,reason,
         old_cat,old_niche,old_status,old_reason,old_version,
         l1,l2,n_sources,branches,leaves,bad)=row
        counts["review_records_scanned"]+=1
        tokens=[v.strip() for v in reason.split(",") if v.strip()]
        if not tokens or any(not v.startswith("taxonomy_") for v in tokens):
            counts["review_no_taxonomy_evidence"]+=1
            continue
        source_allowed=(n_sources>0 and branches==1 and leaves<=1 and
            bad==0 and l1 not in PROTECTED_ROOTS and bool(l1) and bool(l2))
        data={"shop":shop,"item":item,"title":title,"description":description,
              "url":url,"image":image}
        _key,moderation,block=classify(data)
        safe=(source_allowed and moderation=="eligible" and
            not block and shop.isdigit() and item.isdigit() and
            host_allowed(url) and str(image).startswith("https://"))
        if not safe:
            counts["unsafe_or_protected"]+=1
            continue
        route=classify_title(title)
        if route.status!="matched":
            counts["title_no_route"]+=1
            continue
        desired=f"{route.category}/{route.niche}"
        if desired not in PATH_ROUTE_HINTS.get((l1,l2),frozenset()):
            counts["source_editorial_route_mismatch"]+=1
            continue
        if not source_safe_for_use(cat,key):
            counts["unsafe_or_protected"]+=1
            continue
        counts["supported_review_candidates"]+=1
        if len(result)<limit:
            result.append({
                "key":key,"new_category":route.category,
                "new_niche":route.niche,"new_reason":route.reason,
                "new_version":route.version,
                "old_moderation_reason":reason,"old_category":old_cat,
                "old_niche":old_niche,"old_taxonomy_status":old_status,
                "old_taxonomy_reason":old_reason,
                "old_taxonomy_version":old_version,
                "evidence_l1":l1,"evidence_l2":l2,
            })
    return result,counts


def reclassify(cat:Catalog,*,limit:int=MAX_PER_RUN,
               execute:bool=False)->dict:
    if type(execute) is not bool:
        raise ReclassificationError("execute_invalid")
    before=cat.stats()
    links_before=_link_hash(cat)
    selected,counts=find_candidates(cat,limit=limit)
    applied=0
    if execute and selected:
        with cat.db:
            cat.db.execute("""
              CREATE TABLE IF NOT EXISTS v31_taxonomy_reclassification_audit (
                product_key TEXT PRIMARY KEY,old_moderation_reason TEXT NOT NULL,
                old_category TEXT NOT NULL,old_niche TEXT NOT NULL,
                old_taxonomy_status TEXT NOT NULL,old_taxonomy_reason TEXT NOT NULL,
                old_taxonomy_version TEXT NOT NULL,approved_version TEXT NOT NULL,
                official_l1 TEXT NOT NULL,official_l2 TEXT NOT NULL,
                approved_at_utc TEXT NOT NULL
              )
            """)
            for row in selected:
                key=row["key"]
                inserted=cat.db.execute("""
                  INSERT OR IGNORE INTO v31_taxonomy_reclassification_audit
                  (product_key,old_moderation_reason,old_category,old_niche,
                   old_taxonomy_status,old_taxonomy_reason,old_taxonomy_version,
                   approved_version,official_l1,official_l2,approved_at_utc)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,(key,row["old_moderation_reason"],
                     row["old_category"],row["old_niche"],
                     row["old_taxonomy_status"],row["old_taxonomy_reason"],
                     row["old_taxonomy_version"],row["new_version"],
                     row["evidence_l1"],row["evidence_l2"],
                     datetime.now(timezone.utc).isoformat())).rowcount
                if inserted!=1:
                    continue
                p=cat.db.execute("""
                  UPDATE products SET moderation='eligible',
                  moderation_reason=''
                  WHERE product_key=? AND moderation='review'
                    AND moderation_reason=?
                """,(key,row["old_moderation_reason"])).rowcount
                t=cat.db.execute("""
                  UPDATE product_taxonomy
                  SET category=?,niche=?,status='matched',reason=?,version=?
                  WHERE product_key=? AND status='review'
                """,(row["new_category"],row["new_niche"],
                     "dual_evidence_title_and_official_category",
                     row["new_version"],key)).rowcount
                if p!=1 or t!=1:
                    raise ReclassificationError("concurrent_review_change")
                applied+=1
    after=cat.stats()
    if (after["products"]!=before["products"] or
        after["cached_affiliate_links"]!=before["cached_affiliate_links"] or
        _link_hash(cat)!=links_before or not cat.integrity() or
        after["eligible"]!=before["eligible"]+applied or
        after["review"]!=before["review"]-applied):
        raise ReclassificationError("catalog_or_links_changed")
    return {
        "mode":"C39_RECLASSIFICATION_APPLY" if execute else "DRY_RUN",
        "products":before["products"],
        "review_before":before["review"],
        "supported_candidates_total":counts["supported_review_candidates"],
        "proposed_this_batch":len(selected),
        "approved_this_batch":applied,
        "remaining_review":after["review"],
        "evidence_counts":counts,
        "old_affiliate_links_preserved":True,
        "r2_writes":0,"shopee_api_calls":0,
        "publication_calls":0,
    }


def run_r2(*,execute:bool=False,limit:int=MAX_PER_RUN)->dict:
    with tempfile.TemporaryDirectory(prefix="v31-c39-reclass-") as t:
        path=Path(t)/"catalog.sqlite3"
        storage=R2State.from_env()
        if not storage.restore_to(path):
            raise ReclassificationError("r2_catalog_missing")
        verify_database(path)
        with Catalog(path) as cat:
            report=reclassify(cat,limit=limit,execute=execute)
            before_link_count=cat.stats()["cached_affiliate_links"]
        saved=False
        if execute and report["approved_this_batch"]:
            reply=storage.save_from(path)
            if not reply.get("state_saved"):
                raise ReclassificationError("r2_save_failed")
            restored=Path(t)/"verify.sqlite3"
            if not storage.restore_to(restored):
                raise ReclassificationError("r2_restore_failed")
            verify_database(restored)
            with Catalog(restored) as cat:
                s=cat.stats()
                if (s["review"]!=report["remaining_review"] or
                    s["cached_affiliate_links"]!=before_link_count or
                    not cat.integrity()):
                    raise ReclassificationError("r2_reclassification_verify_failed")
            saved=True
        report["r2_writes"]=int(saved)
        report["snapshot_verified"]=saved
        return report


def main()->int:
    p=argparse.ArgumentParser(description="C39 - revisão histórica com evidência dupla")
    p.add_argument("--execute",action="store_true")
    p.add_argument("--limit",type=int,default=MAX_PER_RUN)
    args=p.parse_args()
    try:
        result=run_r2(execute=args.execute,limit=args.limit)
        print("V31_C39_EVIDENCE_RECLASSIFICATION_PASS")
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception as exc:
        print("V31_C39_EVIDENCE_RECLASSIFICATION_FAILED_"+type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
