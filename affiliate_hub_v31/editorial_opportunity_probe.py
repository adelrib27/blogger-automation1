"""Inventory editorial opportunities without spending conversion or research budget."""
import argparse
import json
import tempfile
from pathlib import Path

from .automatic_wordpress_drafts import WordPressRestClient, _product_slug, _verify_blog_url, credentials_for
from .catalog import Catalog
from .d1_http_runner import CloudflareD1HTTPRunner
from .legacy_cms_collision import audit_candidate_history
from .r2_state import R2State
from .routing import sites
from .verified_supply import route_supply_keys
from .wordpress_category_routing import (
    ExcludedCategoryProduct, category_for_product, category_map, verify_remote_category,
)


def inspect(site_key):
    route = sites()[site_key]
    mapping = category_map(route)
    if not mapping or route["publish_enabled"] is not False:
        raise ValueError("opportunity_route_not_configured")
    user, password = credentials_for(site_key)
    client = WordPressRestClient(base_url=route["identifier"], username=user,
                                 application_password=password)
    if not _verify_blog_url(client.site_settings().get("url", ""), route["identifier"]):
        raise ValueError("opportunity_site_identity_mismatch")
    for binding in mapping.values():
        verify_remote_category(client, route, binding)
    posts = client.list_posts(include_unpublished=True)
    query = CloudflareD1HTTPRunner.from_environment(allow_mutations=False)
    campaign = route["campaign"]
    attempted = {row["product_key"] for row in query(
        "SELECT DISTINCT product_key FROM v31_shopee_conversion_attempts WHERE campaign=?",
        (campaign,))}
    jobs = query("SELECT status, COUNT(*) AS total FROM v31_ready_jobs "
                 "WHERE site_key=? AND campaign=? GROUP BY status", (site_key, campaign))
    storage = R2State.from_env()
    buckets = {path: {"inventory_sample": 0, "cached": [], "uncached": []}
               for path in mapping}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "catalog.sqlite3"
        if not storage.restore_to(path):
            raise ValueError("opportunity_catalog_missing")
        with Catalog(path) as catalog:
            for sku in route_supply_keys(catalog, route):
                try:
                    binding = category_for_product(catalog, route, sku)
                except ExcludedCategoryProduct:
                    continue
                bucket = buckets[binding["taxonomy_path"]]
                bucket["inventory_sample"] += 1
                title = catalog.db.execute("SELECT title FROM products WHERE product_key=?",
                                           (sku,)).fetchone()[0]
                title = " ".join(title.split())[:145]
                cached = bool(catalog.cached_link(sku, campaign))
                targets = bucket["cached" if cached else "uncached"]
                if len(targets) >= 10 or (not cached and sku in attempted):
                    continue
                audit = audit_candidate_history(platform="wordpress", posts=posts,
                                                product_key=sku, article_title=title,
                                                slug=_product_slug(site_key, sku))
                if audit["status"] == "NO_DETECTED_COLLISION":
                    targets.append({"product_key": sku, "title": title})
    related = []
    for post in posts:
        if post.get("status") != "publish" or not set(post.get("categories", [])) & {
            binding["id"] for binding in mapping.values()
        }:
            continue
        related.append({"id": post["id"], "categories": post["categories"],
                        "link": post.get("link"), "title": post["title"]["raw"]})
    return {"site_key": site_key, "posts_checked": len(posts), "jobs": jobs,
            "opportunities": buckets, "published_internal_targets": related,
            "writes": 0, "research_requests": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-key", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = inspect(args.site_key)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"site_key": args.site_key, "posts_checked": report["posts_checked"],
                      "jobs": report["jobs"], "writes": report["writes"]}))


if __name__ == "__main__":
    main()
