"""C17 — prova de busca em nichos Shopee por um blog AINDA INEXISTENTE.

Não cria um site nem converte URL. Usa somente o catálogo privado R2 e
devolve contagens: títulos, IDs, URLs e secret jamais aparecem no log.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .catalog import Catalog
from .r2_state import R2State,verify_database
from .source_category_index import browse_source,source_inventory,category_hierarchy


def probe(storage: R2State)->dict:
    examples=[
        ("Home & Living","Furniture"),
        ("Beauty","Hair Care"),
        ("Spare Parts and Accessories for Vehicles","Spare Parts for Automobiles"),
    ]
    with tempfile.TemporaryDirectory(prefix="v31-c17-search-") as td:
        target=Path(td)/"catalog.sqlite3"
        if not storage.restore_to(target):
            raise ValueError("catalog_missing")
        verify_database(target)
        with Catalog(target) as cat:
            stats=cat.stats()
            facets=source_inventory(cat)
            if facets["products_with_official_source_categories"]<100000:
                raise ValueError("source_categories_not_ready")
            top=category_hierarchy(cat)
            second=category_hierarchy(cat,level1="Home & Living")
            third=category_hierarchy(cat,level1="Home & Living",
                                     level2="Furniture")
            if len(top)<20 or not second or not third:
                raise ValueError("three_level_navigation_incomplete")
            examples_result=[]
            for category,niche in examples:
                # Campanha de blog inexistente, nunca atribuir os links
                # existentes a ela. O tema só é informado na busca.
                rows=browse_source(cat,level1=category,level2=niche,
                                   campaign="blogfuturotest",limit=100)
                examples_result.append({
                    "category":category.lower(),
                    "niche":niche.lower(),
                    "results_sampled":len(rows),
                    "editorially_approved_in_sample":sum(bool(x["editorial_approved"]) for x in rows),
                    "wrong_campaign_links":sum(bool(x.get("affiliate_ready")) for x in rows),
                })
                if not rows or any(x.get("affiliate_url") for x in rows):
                    raise ValueError("new_blog_campaign_isolation_failed")
            if not cat.integrity():
                raise ValueError("sqlite_integrity_failure")
        return {
            "status":"PASS",
            "product_count":stats["products"],
            "affiliate_links_still_cached":stats["cached_affiliate_links"],
            "products_with_official_categories":
                facets["products_with_official_source_categories"],
            "category_level1_groups":len(facets["level1_facets"]),
            "navigable_level1":len(top),
            "navigable_level2_home_living":len(second),
            "navigable_level3_furniture":len(third),
            "simulated_nonexistent_blog_campaign":"blogfuturotest",
            "searches":examples_result,
            "shopee_requests":0,
            "r2_writes":0,
            "publication_calls":0,
            "pinterest_calls":0,
        }


def main()->int:
    try:
        report=probe(R2State.from_env())
        print("V31_C17_NEW_BLOG_DISCOVERY_R2_PASS")
        print(json.dumps(report,sort_keys=True))
        return 0
    except Exception:
        print("V31_C17_NEW_BLOG_DISCOVERY_R2_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
