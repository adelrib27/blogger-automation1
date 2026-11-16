"""C9 Radar FULL E2E: erro 1000 SIMULADO, scanner real, R2 REAL, fila real.

Nenhuma chamada à Shopee/WordPress. O objeto da fila só é montado em pasta
temporária e sua integridade/dimensões são verificadas antes de sair.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from .opportunity_router import ROOT,run_router
from .radar_legacy_adapter import build_from_ranking


def run() -> dict:
    config=ROOT/"config/shopee_oportunidades.json"
    rules=ROOT/"config/shopee_intent_rules.json"
    sys.path.insert(0,str(ROOT/"src"))
    try:
        import shopee_oportunidades as base
        with tempfile.TemporaryDirectory(prefix="v31-c9-radar-api1000-") as temp:
            output=Path(temp)/"ranked"
            err={"errors":[{"extensions":{"code":1000},
                            "message":"Simulated Shopee temporary failure"}]}
            with patch.dict(os.environ,{"SHOPEE_APP_ID":"SIMULATED_TEST",
                                         "SHOPEE_SECRET":"SIMULATED_TEST"}), \
                 patch.object(base,"post_graphql",return_value=err) as fake_api, \
                 patch.object(base,"google_suggestions",return_value=[]), \
                 patch.object(base.time,"sleep",return_value=None):
                source=run_router("wordpress_radartechbr",
                    "src/shopee_oportunidades_v23.py",str(config),str(rules),
                    str(output),limit=50,min_fallback=5)
            if source!="CSV_R2" or fake_api.call_count != 1:
                raise ValueError("radar_router_incompatible")
            built=build_from_ranking(output/"ranking.json",
                                     Path(temp)/"fila_radar_teste.json")
            if built["slots"]!=5 or built["unique_shops"]!=5:
                raise ValueError("radar_queue_incomplete")
            return {"site_key":"wordpress_radartechbr",
                    "source":"CSV_R2","simulated_error":1000,
                    "api_calls_simulated":fake_api.call_count,
                    "real_shopee_calls":0,"wordpress_calls":0,
                    "daily_slots":built["slots"],"unique_shops":built["unique_shops"],
                    "publication_calls":0,"real_production_queue_changes":0}
    finally:
        sys.path.remove(str(ROOT/"src"))


def main() -> int:
    try:
        summary=run()
        print("V31_C9_RADAR_FULL_ROUTER_ERROR1000_PASS")
        print(json.dumps(summary,sort_keys=True))
        return 0
    except Exception:
        print("V31_C9_RADAR_FULL_ROUTER_ERROR1000_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
