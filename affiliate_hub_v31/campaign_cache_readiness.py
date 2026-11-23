"""C137: inspecionar cache de URL afiliada de campanha exata na snapshot R2.

Leitura apenas: R2 GET + SQLite query_only; não valida redirecionamento,
estoque, fabricante ou identidade final da oferta; não habilita publicações.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import tempfile
from pathlib import Path

from .catalog import Catalog, host_allowed
from .r2_state import R2State
from .routing import sites
from .source_policy_gate import source_safe_for_use

PILOTS = (
    "blogger_cozinha_sem_complicacao",
    "blogger_estilo",
    "blogger_limpeza",
)
MAX_RESULTS = 4
MAX_SCAN_PER_NICHE = 35
SKU = re.compile(r"shopee:[0-9]+:[0-9]+\Z")
VALID_PROVENANCE = {"shopee_api", "verified_legacy"}


class CampaignCacheAuditError(ValueError):
    pass


def inspect_campaign_cache(catalog: Catalog, route: dict,
                           *, limit: int = MAX_RESULTS) -> dict:
    if (not isinstance(route, dict) or route.get("platform") != "blogger"
            or route.get("publish_enabled") is not False
            or not isinstance(route.get("campaign"), str)
            or not re.fullmatch(r"[a-z0-9_-]{1,32}", route["campaign"])
            or not isinstance(route.get("allowed_niches"), list)
            or not isinstance(route.get("site_key"), str)
            or type(limit) is not int or not 1 <= limit <= MAX_RESULTS):
        raise CampaignCacheAuditError("safe_blogger_route_required")
    campaign = route["campaign"]
    seen = set()
    candidates = []
    for pair in route["allowed_niches"]:
        if not isinstance(pair, str) or len(pair.split("/")) != 2:
            raise CampaignCacheAuditError("route_niche_invalid")
        cat, niche = pair.split("/")
        query = """
           SELECT p.product_key,p.title,p.origin_url,p.image_url,p.shop_id,p.item_id,
                  a.affiliate_url,a.verified_origin,a.updated_utc
           FROM products p
           JOIN product_taxonomy t ON t.product_key=p.product_key
           LEFT JOIN affiliate_links a
             ON a.product_key=p.product_key AND a.campaign=?
           WHERE p.moderation='eligible' AND t.status='matched'
             AND t.category=? AND t.niche=?
           ORDER BY p.last_seen_utc DESC LIMIT ?
        """
        for row in catalog.db.execute(query, (campaign, cat, niche, MAX_SCAN_PER_NICHE)):
            sku, title, origin, image, shop, item, affiliate, proven, updated = row
            if (sku in seen or not isinstance(sku, str) or
                    not SKU.fullmatch(sku) or
                    not isinstance(shop, str) or not shop.isdigit() or
                    not isinstance(item, str) or not item.isdigit() or
                    sku != f"shopee:{shop}:{item}" or
                    not isinstance(title, str) or not 24 <= len(title) <= 190 or
                    not isinstance(origin, str) or not host_allowed(origin) or
                    not isinstance(image, str) or not image.startswith("https://")):
                continue
            if not source_safe_for_use(catalog, sku) or catalog.for_conversion(sku) is None:
                continue
            if affiliate is not None:
                if (not isinstance(affiliate, str) or
                        not host_allowed(affiliate, allow_short=True) or
                        proven not in VALID_PROVENANCE or
                        not isinstance(updated, str) or not updated):
                    raise CampaignCacheAuditError("cached_link_untrusted_fail_closed")
            seen.add(sku)
            candidates.append({
                "product_key": sku,
                "title": title[:145],
                "cached_for_exact_campaign": affiliate is not None,
                "cache_origin": proven if affiliate is not None else None,
                "cache_updated_utc": updated if affiliate is not None else None,
                "manufacturer_facts_verified": False,
                "redirect_target_currently_verified": False,
                "cms_duplicate_checked": False,
                "eligible_for_draft_write": False,
            })
            if len(candidates) >= limit:
                break
        if len(candidates) >= limit:
            break
    return {
        "site_key": route["site_key"], "campaign": campaign,
        "catalog_candidates": len(candidates),
        "cached_exact_campaign": sum(1 for x in candidates if x["cached_for_exact_campaign"]),
        "items": candidates,
        "status": "READ_ONLY_NOT_RELEASE_APPROVAL",
        "r2_writes": 0, "cms_writes": 0, "d1_writes": 0,
        "affiliate_conversions": 0, "automatic_live_authorized": False,
    }


def audit(*, site_keys: tuple[str, ...] = PILOTS) -> dict:
    if (not isinstance(site_keys, tuple) or not 1 <= len(site_keys) <= 8
            or len(set(site_keys)) != len(site_keys)
            or any(not isinstance(x, str) for x in site_keys)):
        raise CampaignCacheAuditError("sites_invalid")
    registry = sites()
    with tempfile.TemporaryDirectory(prefix="v31-c137-") as temp:
        path = Path(temp) / "catalog-read-only.sqlite3"
        if R2State.from_env().restore_to(path) is not True:
            raise CampaignCacheAuditError("r2_snapshot_unavailable")
        db = sqlite3.connect("file:" + str(path) + "?mode=ro", uri=True)
        try:
            db.execute("PRAGMA query_only=ON")
            catalog = Catalog.__new__(Catalog)
            catalog.db = db
            reports = []
            for key in site_keys:
                route = registry.get(key)
                if route is None:
                    raise CampaignCacheAuditError("route_unregistered")
                reports.append(inspect_campaign_cache(catalog, route))
        finally:
            db.close()
    return {
        "mode": "R2_OFFICIAL_SNAPSHOT_SQLITE_READ_ONLY",
        "site_count": len(reports),
        "reports": reports,
        "total_candidates": sum(x["catalog_candidates"] for x in reports),
        "total_exact_campaign_cached": sum(x["cached_exact_campaign"] for x in reports),
        "r2_writes": 0, "cms_writes": 0, "d1_writes": 0,
        "affiliate_conversions": 0, "automatic_live_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V31 C137 somente inventário de cache")
    parser.add_argument("--site-key", default=None)
    args = parser.parse_args()
    try:
        result = audit(site_keys=(args.site_key,) if args.site_key else PILOTS)
    except Exception:
        print("C137_CAMPAIGN_CACHE_FAILED_CLOSED")
        return 1
    print("C137_CAMPAIGN_CACHE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
