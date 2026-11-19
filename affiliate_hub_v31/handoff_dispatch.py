"""C37 — materializar envelopes REVISÁVEIS do acervo para blogs reais.

O cron de cache executa primeiro; esta etapa consulta o R2 atualizado
e salva fila privada por site. Dados completos só no bucket privado,
nunca em outputs do GitHub. Não gera nem publica posts.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .catalog import Catalog
from .handoff_storage import persist_private_handoff
from .r2_state import R2State,verify_database
from .site_request_queue import REQUESTS_DIR,load_requests
from .universal_editorial_handoff import MAX_ARTICLES_PER_BATCH,plan_editorial_handoff


class DispatchError(ValueError):
    pass


def dispatch(storage:R2State,*,directory:Path=REQUESTS_DIR,
             execute:bool=False)->dict:
    if type(execute) is not bool:
        raise DispatchError("execute_invalid")
    requests=load_requests(directory)
    if not requests:
        return {"mode":"REVIEW_HANDOFF_LIVE_ONLY" if execute else "DRY_RUN",
                "requests_evaluated":0,"private_envelopes_saved":0,
                "ready_review_jobs":0,"conversion_needed":0,
                "publication_calls":0,"catalog_r2_writes":0}
    with tempfile.TemporaryDirectory(prefix="v31-c37-handoff-") as td:
        path=Path(td)/"catalog.sqlite3"
        if not storage.restore_to(path):
            raise DispatchError("r2_catalog_missing")
        verify_database(path)
        ready=needed=saved=0
        with Catalog(path) as cat:
            for request in requests:
                report=plan_editorial_handoff(
                    cat,site_key=request["site_key"],
                    platform=request["platform"],topic=request["topic"],
                    # articles=None means an unlimited TOTAL request. C36 only
                    # plans a finite selection batch (not a lifetime quota).
                    articles=(MAX_ARTICLES_PER_BATCH if request["articles"] is None
                              else request["articles"]))
                if not report["site_registered"] or report["can_publish"] is not False:
                    raise DispatchError("unsafe_or_unregistered_plan")
                ready+=len(report["ready_review_jobs"])
                needed+=len(report["conversion_required_keys"])
                if execute:
                    receipt=persist_private_handoff(
                        storage,site_key=request["site_key"],report=report)
                    if not receipt["saved_and_verified"]:
                        raise DispatchError("handoff_not_persisted")
                    saved+=1
        return {
            "mode":"REVIEW_HANDOFF_LIVE_ONLY" if execute else "DRY_RUN",
            "requests_evaluated":len(requests),
            "private_envelopes_saved":saved,
            "ready_review_jobs":ready,
            "conversion_needed":needed,
            "publication_calls":0,
            "catalog_r2_writes":0,
        }


def main()->int:
    p=argparse.ArgumentParser(description="Handoff privado por pedido de blog real")
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    try:
        result=dispatch(R2State.from_env(),execute=args.execute)
        print("V31_C37_PRIVATE_EDITORIAL_HANDOFF_PASS")
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception as exc:
        print("V31_C37_PRIVATE_EDITORIAL_HANDOFF_FAILED_"+type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
