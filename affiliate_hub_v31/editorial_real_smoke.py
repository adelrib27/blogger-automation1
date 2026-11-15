"""C5 SAFE: 1 produto, 2 blogs, 2 abordagens/títulos; R2 privado.

Apenas reserva pautas em REVIEW_REQUIRED. Não gera texto, não envia
rascunhos ou publicações e não imprime títulos/links comerciais.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .catalog import Catalog
from .editorial import EditorialLedger, fold
from .r2_state import R2State

BLOGS = ("blogger_air_fryers", "blogger_cozinha_sem_complicacao")


def validate(storage: R2State) -> dict:
    with tempfile.TemporaryDirectory(prefix="v31-editorial-real-safe-") as tmp:
        dbfile=Path(tmp)/"state.sqlite3"
        if not storage.restore_to(dbfile):
            raise ValueError("catalog_missing")
        with Catalog(dbfile) as catalog:
            source=catalog.select_products("airfryers",1,
                    category="cozinha",niche="air_fryers")
            if not source:
                raise ValueError("no_product_in_niche")
            key=source[0][0]
            ledger=EditorialLedger(catalog)
            chosen=[]
            for site_key in BLOGS:
                brief, reference=ledger.next_brief(site_key,key)
                if brief.status != "REVIEW_REQUIRED" or "air fryer" not in fold(brief.title):
                    raise ValueError("editorial_seo_invalid")
                chosen.append((brief,reference))
            if (chosen[0][0].title == chosen[1][0].title or
                    chosen[0][0].angle == chosen[1][0].angle):
                raise ValueError("article_subject_not_distinct")
            if not catalog.integrity():
                raise ValueError("catalog_corrupted")
        result=storage.save_from(dbfile)
        restored=Path(tmp)/"recovered.sqlite3"
        if not storage.restore_to(restored):
            raise ValueError("restore_missing")
        with Catalog(restored) as catalog:
            for brief,reference in chosen:
                row=catalog.db.execute("""SELECT site_key,status,normalized_title,angle
                  FROM editorial_briefs WHERE brief_id=?""",(reference,)).fetchone()
                if not row or row[0]!=brief.site_key or row[1]!="REVIEW_REQUIRED":
                    raise ValueError("brief_not_persisted")
            n=catalog.db.execute("SELECT COUNT(*) FROM editorial_briefs WHERE product_key=?",
                                 (key,)).fetchone()[0]
        return {"sites_tested":2, "one_product_reused":True,
                "different_titles_and_angles":True,
                "reserved_for_review":2,
                "existing_subjects_for_product":n,
                "r2_snapshot_saved":result["state_saved"],
                "r2_restored":True,"retention_pending":result.get("retention_pending",False)}


def main() -> int:
    try:
        result=validate(R2State.from_env())
        print("V31_C5_EDITORIAL_REUSE_REAL_PASS")
        for key,val in result.items():
            print(f"V31_C5_{key.upper()}={val}")
        return 0
    except Exception:
        print("V31_C5_EDITORIAL_REUSE_REAL_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
