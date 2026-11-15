"""V31 C2.3 — Reserva de pautas em catálogo R2 com execução fail-closed.

NÃO acessa Blogger, WordPress, Shopee ou serviços de geração de texto.
Somente agenda pautas para REVISÃO; não cria/publica artigos.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from .catalog import Catalog
from .editorial import EditorialLedger, EditorialError
from .r2_state import R2State
from .routing import plan_site, sites


def plan(catalog: Catalog, site_key: str, limit: int) -> dict:
    if site_key not in sites():
        raise ValueError("unknown_site")
    if not 1 <= limit <= 20:
        raise ValueError("invalid_limit")
    selection = plan_site(catalog, site_key, limit=min(100, max(limit * 8, 20)))
    ledger = EditorialLedger(catalog)
    created = 0
    exhausted = 0
    for product_key in selection["product_keys"]:
        if created >= limit:
            break
        try:
            ledger.next_brief(site_key, product_key)
            created += 1
        except EditorialError as exc:
            if str(exc) == "editorial_angles_exhausted":
                exhausted += 1
                continue
            raise
    return {"site_key": site_key, "reserved_for_review": created,
            "unavailable_subjects": exhausted, "all_status": "REVIEW_REQUIRED"}


def plan_network(catalog: Catalog, limit: int = 1) -> dict:
    if not 1 <= limit <= 3:
        raise ValueError("network_limit_invalid")
    results = [plan(catalog, site_key, limit) for site_key in sorted(sites())]
    return {"mode": "SAFE_NO_PUBLICATION", "sites": len(results),
            "reserved_for_review": sum(r["reserved_for_review"] for r in results),
            "unavailable_subjects": sum(r["unavailable_subjects"] for r in results),
            "all_status": "REVIEW_REQUIRED"}


def run_cloud(site_key: str, limit: int) -> dict:
    # Estado anterior é obrigatório: sem checkpoint a fila nunca reinicializa.
    storage = R2State.from_env()
    with tempfile.TemporaryDirectory(prefix="v31-editorial-plan-") as folder:
        local = Path(folder) / "catalog.sqlite3"
        if not storage.restore_to(local):
            raise ValueError("catalog_not_initialized")
        with Catalog(local) as catalog:
            result = (plan_network(catalog, limit) if site_key == "all"
                      else plan(catalog, site_key, limit))
            if not catalog.integrity():
                raise ValueError("catalog_integrity_failed")
        if result["reserved_for_review"]:
            result["snapshot_saved"] = storage.save_from(local)["state_saved"]
        else:
            result["snapshot_saved"] = False
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Reservar pautas SAFE sem publicação")
    parser.add_argument("--site", required=True)
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--mode", choices=["local", "cloud"], required=True)
    parser.add_argument("--db")
    args = parser.parse_args()
    try:
        if args.mode == "local":
            if not args.db:
                raise ValueError("missing_db")
            with Catalog(Path(args.db)) as catalog:
                result = (plan_network(catalog, args.limit) if args.site == "all"
                          else plan(catalog, args.site, args.limit))
        else:
            if args.db:
                raise ValueError("cloud_db_not_allowed")
            result = run_cloud(args.site, args.limit)
        # Em logs somente métricas agregadas; não nomes, IDs de produtos, URLs e títulos.
        print("V31_C2_3_EDITORIAL_PLAN_SAFE_PASS")
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print("V31_C2_3_EDITORIAL_PLAN_FAILED_" + type(exc).__name__)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
