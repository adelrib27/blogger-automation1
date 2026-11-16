"""Router compartilhado v31: API Shopee normal; fallback R2 no erro GraphQL 1000.

Sem acoplamento a nomes de blogs. O scanner legado é um script de projeto,
e o site vem de sites.d ou site_routes.json; nenhum publicador é invocado.
Este módulo não é ativado nos workflows LIVE antigos automaticamente.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import runpy
import sys
import tempfile
from pathlib import Path

from .catalog import host_allowed
from .fallback_v23 import FallbackUnavailable, run_cloud
from .routing import sites

ROOT=Path(__file__).resolve().parents[1]


class RoutingError(RuntimeError):
    """Códigos simples, sem URLs ou conteúdo dos feeds."""


def is_api_error_1000(response: dict) -> bool:
    if not isinstance(response,dict):
        return False
    for error in response.get("errors") or []:
        if not isinstance(error,dict):
            continue
        extensions=error.get("extensions") or {}
        if isinstance(extensions,dict) and str(extensions.get("code")) == "1000":
            return True
        message=str(error.get("message") or "").lower()
        if re.search(r"\b(?:error|erro|code|c[oó]digo)\s*[:=#-]?\s*1000\b",message):
            return True
    return False


class ApiError1000Detected(RuntimeError):
    """Interrompe o scanner após a PRIMEIRA ocorrência, evitando mais chamadas."""


class ErrorObserver:
    """Intercepta somente o resultado estruturado; não imprime payload ou token."""
    def __init__(self, post_graphql):
        self.original=post_graphql
        self.error_1000=False
        self.calls=0

    def __call__(self,*args,**kwargs):
        self.calls+=1
        result=self.original(*args,**kwargs)
        if is_api_error_1000(result):
            self.error_1000=True
            raise ApiError1000Detected("shopee_api_error_1000")
        return result


def validate_scanner(path: str) -> Path:
    value=Path(path)
    candidate=(ROOT / value).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        raise RoutingError("scanner_outside_repository") from None
    if value.is_absolute() or candidate.suffix != ".py" or not candidate.is_file():
        raise RoutingError("scanner_not_found")
    # Repositório e scanner são código confiável revisado no PR, não input remoto.
    return candidate


def validate_api_ranking(path: Path) -> int:
    try:
        payload=json.loads(path.read_text(encoding="utf-8"))
        ranking=payload["ranking"]
        if not isinstance(ranking,list):
            return 0
        for row in ranking:
            if (not isinstance(row,dict) or
                    not str(row.get("itemId") or "").strip().isdigit() or
                    not str(row.get("productName") or "").strip() or
                    not host_allowed(str(row.get("offerLink") or ""),allow_short=True)):
                raise RoutingError("api_ranking_invalid")
        return len(ranking)
    except (OSError,ValueError,TypeError,KeyError):
        return 0


def choose_source(api_rows: int, saw_error_1000: bool) -> str:
    """API é preferida se entregou ofertas válidas; só então erro 1000 aciona R2."""
    if api_rows > 0:
        return "API"
    if saw_error_1000:
        return "CSV_R2"
    raise RoutingError("api_unavailable_without_confirmed_1000")


def _publish_staged(staging: Path, destination: Path) -> None:
    mandatory=["ranking.json","intent_report.json","ranking.csv","search_signals.json"]
    for name in mandatory:
        if not (staging/name).is_file():
            raise RoutingError("output_contract_incomplete")
    # Diretório pode conter dados de publicação existentes, mas só arquivos
    # oficiais de oportunidades são substituídos após o staging passar.
    destination.mkdir(parents=True,exist_ok=True)
    if destination.is_symlink():
        raise RoutingError("unsafe_output")
    import os
    for name in mandatory+["diversity_report.json"]:
        file=staging/name
        if file.is_file():
            os.replace(file,destination/name)


def run_router(site_key: str, scanner: str, config: str, rules: str,
               output: str, limit: int = 30, min_fallback: int = 1) -> str:
    if site_key not in sites():
        raise RoutingError("site_not_registered")
    if not 1<=limit<=100:
        raise RoutingError("limit_invalid")
    if not isinstance(min_fallback,int) or not 1<=min_fallback<=limit:
        raise RoutingError("minimum_fallback_invalid")
    scanner_file=validate_scanner(scanner)
    destination=Path(output)
    destination.parent.mkdir(parents=True,exist_ok=True)
    config_file=Path(config).resolve()
    rules_file=Path(rules).resolve()
    if not config_file.is_file() or not rules_file.is_file():
        raise RoutingError("site_configuration_missing")
    with tempfile.TemporaryDirectory(prefix=".v31-scan-",dir=destination.parent) as t:
        stage=Path(t)
        updates={
            "SHOPEE_OPPORTUNITIES_CONFIG":str(config_file),
            "SHOPEE_INTENT_RULES":str(rules_file),
            "SHOPEE_OUTPUT_DIR":str(stage),
        }
        old={k:os.environ.get(k) for k in updates}
        os.environ.update(updates)
        sys.path.insert(0,str(ROOT/"src"))
        try:
            import shopee_oportunidades as base
            import shopee_oportunidades_v23 as v23
            original=base.post_graphql
            old_config=base.CONFIG_PATH
            old_output=base.OUTPUT_DIR
            old_top=base.TOP_N_OVERRIDE
            old_intent=v23.INTENT_RULES_PATH
            base.CONFIG_PATH=config_file
            base.OUTPUT_DIR=stage
            base.TOP_N_OVERRIDE=str(limit)
            v23.INTENT_RULES_PATH=rules_file
            observer=ErrorObserver(original)
            base.post_graphql=observer
            scanner_failed=False
            try:
                # Os scanners antigos imprimem nomes/URLs; mantemos os logs
                # da ponte somente com métricas, sem produtos comerciais.
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    runpy.run_path(str(scanner_file),run_name="__main__")
            except (Exception,SystemExit):
                scanner_failed=True
            finally:
                base.post_graphql=original
                base.CONFIG_PATH=old_config
                base.OUTPUT_DIR=old_output
                base.TOP_N_OVERRIDE=old_top
                v23.INTENT_RULES_PATH=old_intent
            rows=validate_api_ranking(stage/"ranking.json") if not scanner_failed else 0
            source=choose_source(rows,observer.error_1000)
            if source=="CSV_R2":
                # Fallback somente com link afiliado verificado e cacheado.
                run_cloud(site_key,config_file,rules_file,stage,limit)
                verified=validate_api_ranking(stage/"ranking.json")
                if verified < min_fallback:
                    raise RoutingError("insufficient_verified_cached_offers")
            _publish_staged(stage,destination)
            return source
        finally:
            sys.path.remove(str(ROOT/"src"))
            for key,value in old.items():
                if value is None:
                    os.environ.pop(key,None)
                else:
                    os.environ[key]=value


def main() -> int:
    p=argparse.ArgumentParser(description="V31: Shopee API + fallback CSV/R2, sem publicação")
    p.add_argument("--site",required=True)
    p.add_argument("--scanner",required=True)
    p.add_argument("--config",required=True)
    p.add_argument("--rules",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--limit",type=int,default=30)
    p.add_argument("--min-fallback",type=int,default=1,
                   help="Mínimo de links afiliados para liberar artefatos no erro 1000")
    args=p.parse_args()
    try:
        source=run_router(args.site,args.scanner,args.config,args.rules,args.output,args.limit,args.min_fallback)
        print("V31_C6_OPPORTUNITY_ROUTER_PASS_"+source)
        return 0
    except Exception as exc:
        # Nenhuma URL/ID de produto/resposta de API é incluída em logs.
        print("V31_C6_OPPORTUNITY_ROUTER_FAILED_"+type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
