"""C4: uma única conversão real Shopee e persistência R2; sem publicação.

NÃO imprime URLs, IDs de produtos, dados de lojas nem respostas GraphQL.
Reaproveita o cache em execuções posteriores; mutation no máximo uma vez.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .catalog import Catalog
from .converter import ConversionError, convert_one
from .r2_state import R2State

CAMPAIGN = "airfryers"
CATEGORY = "cozinha"
NICHE = "air_fryers"


def pilot(storage: R2State, app_id: str, app_secret: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="v31-c4-convert-private-") as tmp:
        folder=Path(tmp)
        state=folder/"catalog.sqlite3"
        if not storage.restore_to(state):
            raise ValueError("catalog_missing")
        with Catalog(state) as catalog:
            candidates=catalog.select_products(CAMPAIGN, limit=1,
                                                category=CATEGORY, niche=NICHE)
            if not candidates:
                raise ValueError("no_eligible_candidate")
            product_key=candidates[0][0]
            link, created=convert_one(catalog,product_key,CAMPAIGN,app_id,app_secret)
            # O segundo acesso não deve fazer outra chamada à API, mesmo sem
            # credenciais: converte uma única vez e reutiliza o mesmo cache.
            twice, created_twice=convert_one(catalog,product_key,CAMPAIGN,"","")
            if twice != link or created_twice:
                raise ValueError("idempotency_failed")
            expected_count=catalog.stats()["cached_affiliate_links"]
            if not catalog.integrity():
                raise ValueError("integrity_failed")
        if created:
            saved=storage.save_from(state)
            if not saved["state_saved"]:
                raise ValueError("snapshot_not_saved")
        else:
            saved={"state_saved":False, "retention_pending":False}
        restored=folder/"verify.sqlite3"
        if not storage.restore_to(restored):
            raise ValueError("snapshot_missing_after_conversion")
        with Catalog(restored) as verification:
            if verification.cached_link(product_key,CAMPAIGN) != link:
                raise ValueError("restored_link_mismatch")
            if verification.stats()["cached_affiliate_links"] != expected_count:
                raise ValueError("restored_count_mismatch")
        return {"campaign":CAMPAIGN,"created_now":created,"reused_from_cache":not created,
                "cached_affiliate_links":expected_count,
                "state_saved":saved["state_saved"],
                "retention_pending":saved.get("retention_pending",False),
                "restored_and_verified":True}


def main() -> int:
    try:
        app_id=os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID","").strip()
        app_secret=os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET","").strip()
        if not app_id or not app_secret:
            raise ValueError("app_credentials_missing")
        storage=R2State.from_env()
        summary=pilot(storage,app_id,app_secret)
        print("V31_C4_ONE_LINK_REAL_PASS")
        for k,v in summary.items():
            print(f"V31_C4_{k.upper()}={v}")
        return 0
    except ConversionError as exc:
        # ConversionError tem apenas códigos sanitizados definidos pelo módulo.
        code=str(exc)
        safe={"credentials_missing","not_eligible_for_conversion",
              "graphql_error","network_error","invalid_response",
              "untrusted_or_missing_affiliate_link","cache_not_persisted",
              "product_became_ineligible","cached_link_untrusted","response_too_large"}
        if code.startswith("http_error_") and code[len("http_error_"):].isdigit():
            safe.add(code)
        print("V31_C4_ONE_LINK_REAL_FAILED_"+(code if code in safe else "CONVERSION_ERROR"))
        return 3
    except Exception:
        print("V31_C4_ONE_LINK_REAL_FAILED_INTERNAL")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
