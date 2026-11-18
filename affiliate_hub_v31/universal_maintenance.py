"""C45 — manutenção autônoma do acervo UNIVERSAL, sem blog, Shopee ou post.

Fluxo: reavaliar SOMENTE antigos taxonomy_* com duas evidências verificadas,
gravar no máximo MAX_PER_RUN decisões com log auditável, e reconciliar o
índice separado se o catálogo principal avançou ou se falhou sincronização.
O cron compartilha mutex com todos os writers V31.

Não constrói campanhas, não cria links e não aprova a partir de categoria
oficial isolada. O próprio safe_reclassification impõe gates de política.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from .r2_state import R2State
from .safe_reclassification import MAX_PER_RUN, run_r2 as reclassify_r2
from .universal_index_storage import UniversalIndexStorage
from .universal_inventory import run_r2 as rebuild_inventory_r2


class UniversalMaintenanceError(ValueError):
    pass


def _utc_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise UniversalMaintenanceError("invalid_snapshot_timestamp")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise UniversalMaintenanceError("invalid_snapshot_timestamp") from None
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise UniversalMaintenanceError("timestamp_missing_timezone")
    return instant.astimezone(timezone.utc)


def needs_index_rebuild(core: dict | None, index: dict | None,
                        *, expected_products: int) -> bool:
    """Detecta divergência de versão, contagem ou ponteiro ausente.

    Uma alteração no link afiliado pode provocar rebuild conservador,
    mas nunca libera produtos de revisão.
    """
    if (not isinstance(core, dict) or
        not isinstance(core.get("created_utc"), str)):
        raise UniversalMaintenanceError("core_manifest_missing")
    if type(expected_products) is not int or expected_products < 1:
        raise UniversalMaintenanceError("invalid_product_count")
    if index is None:
        return True
    if not isinstance(index, dict):
        raise UniversalMaintenanceError("index_manifest_invalid")
    if type(index.get("product_count")) is not int:
        raise UniversalMaintenanceError("index_product_count_invalid")
    if index["product_count"] != expected_products:
        return True
    return _utc_timestamp(core["created_utc"]) > _utc_timestamp(
        index.get("created_utc"))


def maintain_universal(*, execute: bool = False,
                       limit: int = MAX_PER_RUN,
                       repair_index: bool = False) -> dict:
    if type(execute) is not bool or type(repair_index) is not bool:
        raise UniversalMaintenanceError("invalid_execution_mode")
    if type(limit) is not int or not 1 <= limit <= MAX_PER_RUN:
        raise UniversalMaintenanceError("limit_out_of_bounds")

    if not execute:
        # Dry-run permanece sem writes, nunca converte links.
        result = reclassify_r2(execute=False, limit=limit)
        if (result.get("mode") != "DRY_RUN" or
            result.get("approved_this_batch") != 0 or
            result.get("r2_writes") != 0):
            raise UniversalMaintenanceError("dry_run_unsafe")
        return {
            "mode": "C45_UNIVERSAL_MAINTENANCE_DRY_RUN",
            "products": result["products"],
            "eligible_evidence_candidates": result["supported_candidates_total"],
            "review_remaining": result["remaining_review"],
            "approved_this_batch": 0,
            "r2_catalog_writes": 0, "r2_index_writes": 0,
            "publication_calls": 0, "affiliate_conversion_calls": 0,
            "no_campaign_or_site_dependency": True,
        }

    # Testes e mutex do GitHub workflow antecedem o uso das credenciais R2.
    # A execução completa conserva as versões anteriores no storage.
    core_store = R2State.from_env()
    index_store = UniversalIndexStorage(core_store)
    result = reclassify_r2(execute=True, limit=limit)
    count = result.get("approved_this_batch")
    if (result.get("mode") != "C39_RECLASSIFICATION_APPLY" or
        type(count) is not int or not 0 <= count <= limit or
        not result.get("old_affiliate_links_preserved") or
        result.get("shopee_api_calls") != 0 or
        result.get("publication_calls") != 0 or
        type(result.get("r2_writes")) is not int or
        result["r2_writes"] != int(count > 0) or
        result.get("snapshot_verified") is not (count > 0)):
        raise UniversalMaintenanceError("reclassification_integrity_gate_failed")

    core_manifest = core_store._read_manifest()
    index_manifest = index_store._manifest()
    sync = (count > 0 or repair_index or
            needs_index_rebuild(
                core_manifest, index_manifest,
                expected_products=result["products"]))
    index_writes = 0
    if sync:
        index_result = rebuild_inventory_r2(execute=True)
        if (not index_result.get("r2_snapshot_saved_and_verified") or
            index_result.get("products_indexed") != result["products"] or
            index_result.get("new_approvals") != 0 or
            index_result.get("publication_calls") != 0 or
            index_result.get("converted") != 0 or
            index_result.get("r2_writes") != 1 or
            index_result.get("index_storage") != "R2_SIDECAR" or
            index_result.get("core_catalog_untouched") is not True):
            raise UniversalMaintenanceError("index_reconciliation_failed")
        index_writes = 1

    return {
        "mode": "C45_UNIVERSAL_MAINTENANCE_EXECUTE",
        "products": result["products"],
        "eligible_evidence_candidates_before": result[
            "supported_candidates_total"],
        "approved_this_batch": count,
        "review_remaining": result["remaining_review"],
        "r2_catalog_writes": result["r2_writes"],
        "r2_index_writes": index_writes,
        "index_reconciled": bool(sync),
        "existing_affiliate_links_preserved": True,
        "publication_calls": 0,
        "affiliate_conversion_calls": 0,
        "no_campaign_or_site_dependency": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="C45 — manutenção universal com gates; nenhum post")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--limit", type=int, default=MAX_PER_RUN)
    parser.add_argument("--repair-index", action="store_true")
    args = parser.parse_args()
    try:
        doc = maintain_universal(execute=args.execute,
                                 limit=args.limit,
                                 repair_index=args.repair_index)
        print("V31_C45_UNIVERSAL_MAINTENANCE_PASS")
        print(json.dumps(doc, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        print("V31_C45_UNIVERSAL_MAINTENANCE_FAILED_" +
              type(exc).__name__)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
