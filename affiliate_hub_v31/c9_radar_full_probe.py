"""C9 — prova da fila Radar COMPLETA com produtos reais no cache R2.

Somente restauro de snapshot (READ-ONLY) e elaboração da fila temporária.
Não usa Shopee API nem WordPress. Reutiliza o seletor original do Radar e
exige cinco categorias, cinco lojas, cinco keywords e itens distintos.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .fallback_v23 import candidates_from_catalog,emit_v23_outputs,load_configuration
from .radar_legacy_adapter import build_from_ranking,RadarQueueError
from .r2_state import R2State,verify_database

ROOT=Path(__file__).resolve().parents[1]
SITE="wordpress_radartechbr"
CONFIG=ROOT/"config/shopee_oportunidades.json"
RULES=ROOT/"config/shopee_intent_rules.json"


def run(storage: R2State) -> dict:
    config,rules=load_configuration(CONFIG,RULES)
    with tempfile.TemporaryDirectory(prefix="v31-c9-radar-real-") as folder:
        base=Path(folder)
        db=base/"state.sqlite3"
        if not storage.restore_to(db):
            raise ValueError("r2_state_missing")
        verify_database(db)
        selected=candidates_from_catalog(db,SITE,config,rules,limit=100)
        if len(selected)<5:
            raise ValueError("cached_products_less_than_five")
        opportunities=base/"ranking"
        emit_v23_outputs(selected,config,opportunities)
        complete=build_from_ranking(opportunities/"ranking.json",
                                    base/"radar_queue.json")
        queue=json.loads((base/"radar_queue.json").read_text(encoding="utf-8"))
        if queue["complete"] is not True or len(queue["slots"])!=5:
            raise ValueError("daily_queue_invalid")
        return {
            "site_key":SITE,
            "cached_products_in_ranking":len(selected),
            "complete_categories":len(set(x["category"] for x in queue["slots"])),
            "unique_shops":complete["unique_shops"],
            "slots_verified":complete["slots"],
            "api_calls":0,
            "r2_writes":0,
            "wordpress_calls":0,
            "production_queue_writes":0,
            "publication_calls":0
        }


def main()->int:
    try:
        result=run(R2State.from_env())
        print("V31_C9_RADAR_FULL_QUEUE_REAL_R2_PASS")
        print(json.dumps(result,sort_keys=True))
        return 0
    except RadarQueueError as error:
        safe={"ranking_size_invalid","ranking_item_invalid","ranking_input_invalid",
              "unsafe_output","complete_daily_queue_invalid",
              "legacy_builder_unavailable_or_incomplete"}
        code=str(error)
        print("V31_C9_RADAR_FULL_QUEUE_REAL_R2_NOT_READY_"+(
            code if code in safe else "RADAR_CONTRACT"))
        return 3
    except Exception:
        print("V31_C9_RADAR_FULL_QUEUE_REAL_R2_NOT_READY")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
