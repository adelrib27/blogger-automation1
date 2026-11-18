"""C7 Radar Tech: validar UM slot legado com produto do R2 real, sem publicar.

O Radar exige cinco categorias na fila diária; este PROBE cria somente
uma simulação de fila em diretório TEMPORÁRIO para provar o contrato de
prepare_slot.py. Não gera fila válida para operação ou publicação real.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from .catalog import host_allowed
from .fallback_v23 import candidates_from_catalog, load_configuration
from .r2_state import R2State

ROOT=Path(__file__).resolve().parents[1]
SITE="wordpress_radartechbr"
CONFIG=ROOT/"config/shopee_oportunidades.json"
RULES=ROOT/"config/shopee_intent_rules.json"
POLICY=ROOT/"config/fase3_politica_editorial.json"
PREPARE=ROOT/"radar_tech_br/src/prepare_slot.py"


def validate(storage: R2State) -> dict:
    cfg,intents=load_configuration(CONFIG,RULES)
    policy=json.loads(POLICY.read_text(encoding="utf-8"))
    mapping=policy["category_map"]
    categories=policy["allowed_categories"]
    times=policy["publication_slots"]
    if len(categories)!=5 or len(times)!=5 or set(mapping.values())!=set(categories):
        raise ValueError("radar_policy_invalid")
    with tempfile.TemporaryDirectory(prefix="v31-radar-slot-safe-") as tmp:
        root=Path(tmp)
        db=root/"catalog.sqlite3"
        if not storage.restore_to(db):
            raise ValueError("r2_catalog_missing")
        rows=candidates_from_catalog(db,SITE,cfg,intents,limit=20)
        if not rows:
            raise ValueError("radar_cached_affiliate_unavailable")
        first=next((r for r in rows if (r.get("categories") or [None])[0] in mapping),None)
        if first is None:
            raise ValueError("radar_category_not_mapped")
        source_cat=first["categories"][0]
        display_cat=mapping[source_cat]
        keyword=(first["intentMatchedKeywords"] or [None])[0]
        if not keyword or not host_allowed(first["offerLink"],allow_short=True):
            raise ValueError("radar_product_unverified")
        target=times[categories.index(display_cat)]
        # Exclusivamente arquivo efêmero de contrato: os outros quatro
        # slots são placeholders, não candidatos aprovados a publicar.
        slots=[]
        for category,clock in zip(categories,times):
            slot={"time":clock,"category":category,
                  "status":"QUARENTENA","keyword":"","product":{}}
            if category==display_cat:
                slot["status"]="NA_FILA"
                slot["sourceCategory"]=source_cat
                slot["keyword"]=keyword
                slot["product"]={
                    "itemId":first["itemId"],"productName":first["productName"],
                    "offerLink":first["offerLink"],"imageUrl":first["imageUrl"],
                    "shopName":first.get("shopName") or "",
                    "priorityTier":first.get("priorityTier"),
                    "opportunityScore":first.get("opportunityScore")
                }
            slots.append(slot)
        current=datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()
        fake_file=root/"fila_somente_teste.json"
        fake_file.write_text(json.dumps({
            "project":"Radar Tech BR","date":current,
            "complete":True,"probe_only":True,"slots":slots
        },ensure_ascii=False),encoding="utf-8")
        # Usa o preparador original mas redireciona ENTRADA e SAÍDA
        # exclusivamente ao diretório temporário de testes.
        spec=importlib.util.spec_from_file_location("v31_radar_prepare_safe",PREPARE)
        if spec is None or spec.loader is None:
            raise ValueError("radar_prepare_missing")
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output=root/"radar_editorial_queue.json"
        with patch.object(module,"LEGACY_QUEUE",fake_file), \
             patch.object(module,"OUT",output), \
             patch.dict(os.environ,{"RADAR_TARGET_SLOT":target}), \
             contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            module.main()
        doc=json.loads(output.read_text(encoding="utf-8"))
        items=doc.get("items") or []
        if (len(items)!=1 or items[0].get("slot")!=target
            or items[0].get("category")!=display_cat
            or items[0].get("status")!="PENDING"
            or not host_allowed(items[0].get("affiliate_link") or "",allow_short=True)
            or not str(items[0].get("image_url") or "").startswith("https://")):
            raise ValueError("radar_slot_contract_failed")
        return {"site_key":SITE,"cached_rows":len(rows),
                "slots_verified":1,"full_daily_queue_ready":False,
                "original_prepare_slot_compatible":True,
                "all_files_temporary":True,"publication":False}


def main() -> int:
    try:
        result=validate(R2State.from_env())
        print("V31_C7_RADAR_SLOT_R2_PASS")
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception:
        print("V31_C7_RADAR_SLOT_R2_FAILED")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
