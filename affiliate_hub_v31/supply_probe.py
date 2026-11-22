"""Read-only V31 supply audit. No D1, Shopee, Firecrawl or CMS calls.

Never emits catalog URLs, titles, SKUs or affiliate credentials.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .catalog import Catalog
from .r2_state import R2State, verify_database
from .routing import sites
from .site_request_queue import load_requests, VERIFIER_PROFILES
from .site_launch_plan import preview_site_launch
from .structured_review_source import catalog_gtin
from .manufacturer_review import models_for_catalog_title


def _has_valid_gtin(catalog: Catalog, key: str) -> bool:
    row = catalog.db.execute(
        "SELECT description FROM products WHERE product_key=?", (key,)
    ).fetchone()
    if row is None:
        return False
    try:
        catalog_gtin(str(row[0] or ""))
        return True
    except ValueError:
        return False



def _has_trusted_model(catalog: Catalog, key: str, site_key: str) -> bool:
    row = catalog.db.execute(
        "SELECT title FROM products WHERE product_key=?", (key,)
    ).fetchone()
    return bool(row and models_for_catalog_title(str(row[0]), site_key=site_key))


def audit_catalog(catalog: Catalog, site_key: str) -> dict:
    route = sites().get(site_key)
    request = next((r for r in load_requests() if r["site_key"] == site_key), None)
    if not route or not request or route.get("publish_enabled") is not False:
        raise ValueError("registered_draft_only_request_required")
    profiles = json.loads(VERIFIER_PROFILES.read_text(encoding="utf-8"))
    site_profile = profiles.get(site_key) or {}
    configured = site_profile.get("offers", {})
    report = {
        "site_key": site_key,
        "mode": "READ_ONLY_NO_REMOTE_MUTATIONS",
        "profiled_offer_count": len(configured),
        "profiled_with_campaign_link": 0,
        "profiled_approved_without_campaign_link": 0,
        "profiled_approved_with_campaign_link": 0,
        "profiled_missing_or_ineligible": 0,
        "top24_approved": 0,
        "top24_with_campaign_link": 0,
        "top24_gtin": 0,
        "top24_trusted_model": 0,
        "top24_model_with_campaign_link": 0,
        "top24_gtin_with_campaign_link": 0,
        "authorized_pool_scanned": 0,
        "authorized_pool_with_campaign_link": 0,
        "authorized_pool_valid_gtin": 0,
        "authorized_pool_trusted_model": 0,
        "authorized_pool_model_with_campaign_link": 0,
        "authorized_pool_gtin_with_campaign_link": 0,
        "authorized_pool_limit_per_path": 100,
        "source_facts_verified": 0,
        "cms_posts_created": 0,
        "publication_calls": 0,
        "shopee_conversion_calls": 0,
        "paid_research_calls": 0,
        "r2_mutations": 0,
    }
    for key in configured:
        if catalog.for_conversion(key) is None:
            report["profiled_missing_or_ineligible"] += 1
        else:
            report["profiled_approved_" + (
                "with_campaign_link" if catalog.cached_link(key, route["campaign"])
                else "without_campaign_link")] += 1
    report["profiled_with_campaign_link"] = report["profiled_approved_with_campaign_link"]
    result = preview_site_launch(
        catalog, topic=request["topic"], platform=route["platform"],
        site_key=site_key, max_items=24, max_per_shop=1
    )
    top = result["approved_catalog_candidates"]
    report["top24_approved"] = len(top)
    for item in top:
        converted = item["affiliate_status"] == "verified_for_campaign"
        gtin = _has_valid_gtin(catalog, item["product_key"])
        model = _has_trusted_model(catalog, item["product_key"], site_key)
        report["top24_trusted_model"] += int(model)
        report["top24_model_with_campaign_link"] += int(model and converted)
        report["top24_with_campaign_link"] += int(converted)
        report["top24_gtin"] += int(gtin)
        report["top24_gtin_with_campaign_link"] += int(gtin and converted)
    seen = set()
    pools = []
    for pair in route["allowed_niches"]:
        category, niche = pair.split("/", 1)
        pools.append(catalog.select_products(route["campaign"], limit=100,
                                             category=category, niche=niche))
    for pair in route.get("allowed_source_paths", []):
        a, b = pair.split("/", 1)
        pools.append(catalog.select_by_source_path(route["campaign"], a, b, limit=100))
    for pool in pools:
        for row in pool:
            key = row[0]
            if key in seen or catalog.for_conversion(key) is None:
                continue
            seen.add(key)
            cached = bool(row[4])
            gtin = _has_valid_gtin(catalog, key)
            model = _has_trusted_model(catalog, key, site_key)
            report["authorized_pool_trusted_model"] += int(model)
            report["authorized_pool_model_with_campaign_link"] += int(cached and model)
            report["authorized_pool_scanned"] += 1
            report["authorized_pool_with_campaign_link"] += int(cached)
            report["authorized_pool_valid_gtin"] += int(gtin)
            report["authorized_pool_gtin_with_campaign_link"] += int(cached and gtin)
    return report


def main() -> int:
    p = argparse.ArgumentParser(description="V31 catalog supply read-only audit")
    p.add_argument("--site-key", required=True)
    a = p.parse_args()
    try:
        with tempfile.TemporaryDirectory(prefix="v31-supply-audit-") as td:
            db = Path(td) / "catalog.sqlite3"
            if not R2State.from_env().restore_to(db):
                raise ValueError("r2_catalog_missing")
            verify_database(db)
            with Catalog(db) as catalog:
                report = audit_catalog(catalog, a.site_key)
        print("V31_C89_SUPPLY_READONLY_PASS")
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, TypeError):
        print("V31_C89_SUPPLY_READONLY_FAILED_CLOSED")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
