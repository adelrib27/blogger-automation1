"""C7 — validação REAL sem publicar: catálogo R2 -> fila original Casa.

É um teste de compatibilidade, não um publicador; usa diretório temporário
para toda a fila e não toca estado de produção.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

from .catalog import host_allowed
from .fallback_v23 import candidates_from_catalog, emit_v23_outputs, load_configuration
from .r2_state import R2State

ROOT=Path(__file__).resolve().parents[1]
SITE="wordpress_casa_decoracao"
CONFIG=ROOT/"casa_decoracao/config/shopee_oportunidades.json"
RULES=ROOT/"casa_decoracao/config/shopee_intent_rules.json"
SCRIPT=ROOT/"casa_decoracao/src/build_editorial_queue.py"


def validate(storage: R2State) -> dict:
    cfg,rules=load_configuration(CONFIG,RULES)
    with tempfile.TemporaryDirectory(prefix="v31-c7-casa-queue-") as dirname:
        root=Path(dirname)
        db=root/"catalog.sqlite3"
        if not storage.restore_to(db):
            raise ValueError("catalog_not_persisted")
        rows=candidates_from_catalog(db,SITE,cfg,rules,limit=10)
        if not rows:
            raise ValueError("no_verified_links_for_casa")
        source=root/"opportunities"
        emit_v23_outputs(rows,cfg,source)
        # Importa o construtor LEGADO da Casa, mas direciona todos os seus
        # arquivos ao diretório temporário; nenhuma rede nem publicação.
        sys.path.insert(0,str(SCRIPT.parent))
        try:
            spec=importlib.util.spec_from_file_location("v31_c7_casa_isolated",SCRIPT)
            if spec is None or spec.loader is None:
                raise ValueError("queue_builder_unavailable")
            mod=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.REPORT=source/"intent_report.json"
            mod.RANKING=source/"ranking.json"
            mod.CONFIG=CONFIG
            mod.OUT=root/"editorial_queue.json"
            mod.HISTORY=root/"publication_history.json"
            mod.ROTATION=root/"category_rotation.json"
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                mod.main()
        finally:
            sys.path.remove(str(SCRIPT.parent))
        queue=json.loads((root/"editorial_queue.json").read_text(encoding="utf-8"))
        items=queue.get("items") or []
        if not items:
            raise ValueError("legacy_queue_empty")
        for item in items:
            if not host_allowed(item.get("affiliate_link") or "",allow_short=True):
                raise ValueError("invalid_legacy_affiliate_link")
            if not (item.get("source_keyword") and item.get("category")
                    and str(item.get("image_url") or "").startswith("https://")
                    and item.get("status")=="PENDING"):
                raise ValueError("legacy_queue_incompatible")
        return {"mode":"SAFE_READ_ONLY", "site_key":SITE,
                "cached_r2_products":len(rows),"legacy_queue_items":len(items),
                "all_links_verified":True,"no_publication":True}


def main() -> int:
    try:
        result=validate(R2State.from_env())
        print("V31_C7_CASA_REAL_R2_QUEUE_PASS")
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception:
        print("V31_C7_CASA_REAL_R2_QUEUE_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
