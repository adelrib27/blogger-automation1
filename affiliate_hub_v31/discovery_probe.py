"""C18 — canário REAL R2 da seleção de produtos por assunto de um blog futuro.

Logs contêm apenas contagens por tema pré-definido no código (não IDs, título,
URL, afiliado, vendedor nem credencial); leitura somente do snapshot privado.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .catalog import Catalog
from .product_discovery import discover
from .r2_state import R2State,verify_database

SCENARIOS=(
    {"theme":"air_fryer", "topic":"Air Fryer", "category":"Home Appliances"},
    {"theme":"guarda_roupa", "topic":"Guarda Roupa", "category":"Home & Living"},
    {"theme":"freio_automotivo", "topic":"Freio",
     "category":"Spare Parts and Accessories for Vehicles"},
)


def probe(storage: R2State)->dict:
    with tempfile.TemporaryDirectory(prefix="v31-c18-topic-") as t:
        target=Path(t)/"catalog.sqlite3"
        if not storage.restore_to(target):
            raise ValueError("catalog_missing")
        verify_database(target)
        with Catalog(target) as cat:
            before=cat.stats()
            summaries=[]
            for scenario in SCENARIOS:
                params={"topic":scenario["topic"],
                        "category":scenario["category"],
                        "campaign":"futureblogv31","limit":12,
                        "max_per_shop":1}
                approved=discover(cat,**params)
                reviewed=discover(cat,**params,include_review=True)
                if not reviewed:
                    raise ValueError("topic_not_discoverable")
                if any(x["curation"]!="approved" for x in approved):
                    raise ValueError("unapproved_in_publisher_eligible_candidates")
                if any(x["affiliate_url"] is not None for x in approved+reviewed):
                    raise ValueError("foreign_campaign_link_leaked")
                if any(x["can_publish"] for x in approved+reviewed):
                    raise ValueError("publication_gate_not_closed")
                if len({x["shop_id"] for x in reviewed})!=len(reviewed):
                    raise ValueError("shop_diversity_gate_failed")
                summaries.append({
                    "theme":scenario["theme"],
                    "approved_candidates_in_top12":len(approved),
                    "all_candidates_for_editorial_review_in_top12":len(reviewed),
                    "different_shops_in_top12":len(reviewed),
                    "wrong_campaign_links":0
                })
            if cat.stats()!=before or not cat.integrity():
                raise ValueError("catalog_modified")
        return {
            "mode":"C18_NEW_BLOG_THEME_DISCOVERY_READ_ONLY",
            "catalog_products":before["products"],
            "approved_catalog_products":before["eligible"],
            "preserved_affiliate_link_count":before["cached_affiliate_links"],
            "site_profiles_required":0,
            "sample_topics":summaries,
            "graphQL_calls":0,"r2_writes":0,"publication_calls":0,
        }


def main()->int:
    try:
        summary=probe(R2State.from_env())
        print("V31_C18_TOPIC_DISCOVERY_R2_PASS")
        print(json.dumps(summary,sort_keys=True,ensure_ascii=False))
        return 0
    except Exception:
        print("V31_C18_TOPIC_DISCOVERY_R2_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
