"""C7: teste end-to-end sem publicação — erro 1000 SIMULADO + R2 REAL.

Usa os scanners REAIS Casa/Oficina, mas injeta a resposta 1000 em memória:
não chama Shopee/WordPress. R2 é lido com credenciais privadas no Actions.
"""
from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from .catalog import host_allowed
from .opportunity_router import ROOT, run_router

PROJECTS = (
    ("wordpress_casa_decoracao", "casa_decoracao",
     "src/shopee_oportunidades_casa.py"),
    ("wordpress_oficina_garagem", "oficina_garagem",
     "src/shopee_oportunidades_oficina.py"),
)


def run() -> dict:
    sys.path.insert(0,str(ROOT/"src"))
    try:
        import shopee_oportunidades as base
        counts={}
        with tempfile.TemporaryDirectory(prefix="v31-c7-error1000-realr2-") as tmp:
            root=Path(tmp)
            for site,project,scanner_file in PROJECTS:
                proj=ROOT/project
                scanner=proj/scanner_file
                config=proj/"config/shopee_oportunidades.json"
                rules=proj/"config/shopee_intent_rules.json"
                output=root/project
                error={"errors":[{"message":"Shopee temporary failure",
                                  "extensions":{"code":1000}}]}
                with patch.dict(os.environ,{"SHOPEE_APP_ID":"SIMULATED_ONLY",
                                             "SHOPEE_SECRET":"SIMULATED_ONLY"}), \
                     patch.object(base,"post_graphql",return_value=error) as api, \
                     patch.object(base,"google_suggestions",return_value=[]), \
                     patch.object(base.time,"sleep",return_value=None):
                    source=run_router(site,str(scanner.relative_to(ROOT)),
                                      str(config),str(rules),str(output),limit=5)
                if source!="CSV_R2" or api.call_count!=1:
                    raise ValueError("router_not_short_circuited")
                ranking=json.loads((output/"ranking.json").read_text(encoding="utf-8"))
                report=json.loads((output/"intent_report.json").read_text(encoding="utf-8"))
                products=ranking.get("ranking") or []
                if not products or len(report.get("ranking") or [])!=len(products):
                    raise ValueError("ranking_contract_invalid")
                for row in products:
                    if (not host_allowed(row.get("offerLink") or "",allow_short=True)
                            or row.get("sourceModes")!=["csv_r2_verified_affiliate_cache"]
                            or not str(row.get("imageUrl") or "").startswith("https://")
                            or row.get("sales") is not None
                            or row.get("ratingStar") is not None):
                        raise ValueError("r2_product_unverified")
                counts[site]=len(products)
        return {"status":"PASS","simulated_api_error":1000,
                "api_calls_per_site":1,"sites":len(PROJECTS),
                "cached_product_counts":counts,"wordpress_calls":0,
                "shopee_network_calls":0}
    finally:
        sys.path.remove(str(ROOT/"src"))


def main() -> int:
    try:
        result=run()
        print("V31_C7_REAL_R2_SIMULATED_ERROR1000_PASS")
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception:
        print("V31_C7_REAL_R2_SIMULATED_ERROR1000_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
