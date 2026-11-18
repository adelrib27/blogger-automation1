"""C9 — Adaptador de ranking V31 para a fila diária ORIGINAL do Radar.

Não executa scanner nem publica artigos. Reutiliza a própria lógica
fase3_fila_radar.choose_daily_products()/build_queue() com ranking validado
recebido como artefato. Falha fechada se faltar uma das cinco categorias,
loja/keyword únicos, ou um link afiliado Shopee verdadeiro.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

from .catalog import host_allowed

ROOT=Path(__file__).resolve().parents[1]


class RadarQueueError(ValueError):
    pass


def validate_ranking(path: Path) -> list[dict]:
    try:
        doc=json.loads(Path(path).read_text(encoding="utf-8"))
        rows=doc["ranking"]
        if not isinstance(rows,list) or not 5 <= len(rows) <= 100:
            raise RadarQueueError("ranking_size_invalid")
        for row in rows:
            if not isinstance(row,dict):
                raise RadarQueueError("ranking_item_invalid")
            if (not str(row.get("itemId") or "").isdigit() or
                    not str(row.get("shopId") or "").isdigit() or
                    not str(row.get("productName") or "").strip() or
                    not host_allowed(str(row.get("offerLink") or ""),allow_short=True) or
                    not str(row.get("imageUrl") or "").startswith("https://") or
                    not isinstance(row.get("categories"),list) or
                    not isinstance(row.get("intentMatchedKeywords"),list)):
                raise RadarQueueError("ranking_item_invalid")
        return rows
    except (OSError,ValueError,KeyError,UnicodeError):
        raise RadarQueueError("ranking_input_invalid") from None


def build_from_ranking(ranking_file: Path, output_file: Path) -> dict:
    rows=validate_ranking(ranking_file)
    output=Path(output_file)
    if output.is_symlink() or output.parent.is_symlink():
        raise RadarQueueError("unsafe_output")
    output.parent.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(ROOT/"src"))
    try:
        import fase3_fila_radar as legacy
        original=legacy.QUEUE_PATH
        scan=legacy.v23.scan_v23
        # A montagem original não pode escrever no diretório LIVE até
        # TODAS as 5 categorias e as diversidades serem validadas.
        with tempfile.TemporaryDirectory(prefix=".v31-c9-radar-",dir=output.parent) as td:
            staged=Path(td)/"fila_dia.json"
            try:
                legacy.QUEUE_PATH=staged
                legacy.v23.scan_v23=lambda:rows
                with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                    built=legacy.build_queue()
            finally:
                legacy.QUEUE_PATH=original
                legacy.v23.scan_v23=scan
            slots=built.get("slots") or []
            shops=[str((s.get("product") or {}).get("shopId") or "") for s in slots]
            keywords=[str(s.get("keyword") or "").casefold().strip() for s in slots]
            items=[str((s.get("product") or {}).get("itemId") or "") for s in slots]
            categories=[str(s.get("category") or "") for s in slots]
            expected=set(legacy.load_json(legacy.POLICY_PATH,{})["allowed_categories"])
            if (built.get("complete") is not True or len(slots)!=5 or
                    set(categories)!=expected or
                    any(not x for x in shops+keywords+items) or
                    len(set(shops))!=5 or len(set(keywords))!=5 or
                    len(set(items))!=5 or
                    any(not host_allowed(s.get("product",{}).get("offerLink",""),
                                         allow_short=True) for s in slots)):
                raise RadarQueueError("complete_daily_queue_invalid")
            os.replace(staged,output)
    except (ImportError,RuntimeError,OSError,KeyError) as exc:
        raise RadarQueueError("legacy_builder_unavailable_or_incomplete") from None
    finally:
        sys.path.remove(str(ROOT/"src"))
    return {"slots":5,"unique_shops":5,"unique_keywords":5,
            "complete":True,"publication_calls":0}


def main() -> int:
    p=argparse.ArgumentParser(description="Radar: ranking API/R2 -> fila original SAFE")
    p.add_argument("--ranking",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    try:
        status=build_from_ranking(Path(args.ranking),Path(args.output))
        print("V31_C9_RADAR_COMPLETE_QUEUE_PASS")
        print(json.dumps(status,sort_keys=True))
        return 0
    except Exception:
        print("V31_C9_RADAR_COMPLETE_QUEUE_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
