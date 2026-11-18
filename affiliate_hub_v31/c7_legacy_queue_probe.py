"""C7 — prova sem publicação para qualquer fila legada estilo Shopee v2.3.

Executa o construtor de fila original em sandbox de arquivos temporários.
Sem credenciais WordPress nem API Shopee. Somente leitura do catálogo R2.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import re
import sys
import tempfile
from pathlib import Path

from .catalog import host_allowed
from .fallback_v23 import candidates_from_catalog, emit_v23_outputs, load_configuration
from .r2_state import R2State
from .routing import sites

ROOT=Path(__file__).resolve().parents[1]


def validate(site: str, project: str, storage: R2State, limit: int = 10) -> dict:
    if site not in sites():
        raise ValueError("site_not_registered")
    if not re.fullmatch(r"[a-z0-9_]{3,50}",project):
        raise ValueError("project_invalid")
    if not 1 <= limit <= 100:
        raise ValueError("invalid_limit")
    folder=ROOT/project
    config=folder/"config/shopee_oportunidades.json"
    rules=folder/"config/shopee_intent_rules.json"
    builder=folder/"src/build_editorial_queue.py"
    if not config.is_file() or not rules.is_file() or not builder.is_file():
        raise ValueError("legacy_project_contract_missing")
    cfg,intents=load_configuration(config,rules)
    with tempfile.TemporaryDirectory(prefix="v31-c7-queue-") as tmp:
        temp=Path(tmp)
        db=temp/"state.sqlite3"
        if not storage.restore_to(db):
            raise ValueError("r2_catalog_missing")
        rows=candidates_from_catalog(db,site,cfg,intents,limit=limit)
        if not rows:
            raise ValueError("no_cached_link_matching_site")
        output=temp/"shopee_opportunities"
        emit_v23_outputs(rows,cfg,output)
        sys.path.insert(0,str(builder.parent))
        try:
            spec=importlib.util.spec_from_file_location("v31_c7_legacy_queue_isolated",builder)
            if spec is None or spec.loader is None:
                raise ValueError("invalid_queue_builder")
            mod=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.REPORT=output/"intent_report.json"
            mod.RANKING=output/"ranking.json"
            mod.CONFIG=config
            mod.OUT=temp/"editorial_queue.json"
            mod.HISTORY=temp/"publication_history.json"
            if hasattr(mod,"ROTATION"):
                mod.ROTATION=temp/"category_rotation.json"
            # O construtor original só lê arquivos no diretório temporário.
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                mod.main()
        finally:
            sys.path.remove(str(builder.parent))
        payload=json.loads((temp/"editorial_queue.json").read_text(encoding="utf-8"))
        items=payload.get("items") or []
        if not items:
            raise ValueError("legacy_queue_empty")
        for row in items:
            if (not str(row.get("shopee_item_id") or "").isdigit() or
                not str(row.get("product") or "").strip() or
                not host_allowed(row.get("affiliate_link") or "",allow_short=True) or
                not str(row.get("image_url") or "").startswith("https://") or
                not str(row.get("source_keyword") or "").strip() or
                not str(row.get("category") or "").strip() or
                row.get("status")!="PENDING"):
                raise ValueError("legacy_queue_row_invalid")
        return {"mode":"SAFE_READ_ONLY", "site_key":site,
                "cached_products":len(rows), "legacy_queue_items":len(items),
                "valid_affiliate_links":True, "publication":False}


def main() -> int:
    p=argparse.ArgumentParser(description="Validação SAFE do formato real da fila")
    p.add_argument("--site",required=True)
    p.add_argument("--project",required=True)
    p.add_argument("--limit",type=int,default=10)
    args=p.parse_args()
    try:
        result=validate(args.site,args.project,R2State.from_env(),args.limit)
        print("V31_C7_LEGACY_QUEUE_R2_PASS")
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception:
        print("V31_C7_LEGACY_QUEUE_R2_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
