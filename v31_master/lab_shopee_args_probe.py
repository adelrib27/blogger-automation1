#!/usr/bin/env python3
"""LAB SAFE: isola parâmetros productOfferV2 e campos, sem Blogger nem logs sensíveis."""
from __future__ import annotations
import json
import os
import time

from lab_shopee_graphql_diagnostic import send_query

QUERIES = (
    ("enriched_no_filters", 'query V31Probe { productOfferV2(keyword: "mouse", page: 1, limit: 1) { nodes { itemId productName offerLink imageUrl priceMin shopId ratingStar sales } } }'),
    ("sort_2_only", 'query V31Probe { productOfferV2(keyword: "mouse", sortType: 2, page: 1, limit: 1) { nodes { itemId productName } } }'),
    ("list_2_only", 'query V31Probe { productOfferV2(keyword: "mouse", listType: 2, page: 1, limit: 1) { nodes { itemId productName } } }'),
    ("sort_1_only", 'query V31Probe { productOfferV2(keyword: "mouse", sortType: 1, page: 1, limit: 1) { nodes { itemId productName } } }'),
    ("baseline_repeat", 'query V31Probe { productOfferV2(keyword: "mouse", page: 1, limit: 1) { nodes { itemId productName } } }'),
)
MAX_CALLS = 5


def summarize(rows):
    by_name = {r["probe"]: r for r in rows}
    baseline = by_name.get("baseline_repeat", {})
    enriched = by_name.get("enriched_no_filters", {})
    sort2 = by_name.get("sort_2_only", {})
    list2 = by_name.get("list_2_only", {})
    sort1 = by_name.get("sort_1_only", {})
    result = []
    if baseline.get("status") == "GRAPHQL_OK":
        result.append("BASELINE_OK")
    if enriched.get("status") == "GRAPHQL_OK":
        result.append("REQUIRED_FIELDS_OK")
    if sort1.get("status") == "GRAPHQL_OK":
        result.append("SORT1_OK")
    if sort2.get("status") == "GRAPHQL_ERROR":
        result.append("SORT2_FAILS")
    if list2.get("status") == "GRAPHQL_ERROR":
        result.append("LIST2_FAILS")
    return result or ["INCONCLUSIVE"]


def main():
    app = os.getenv("SHOPEE_APP_ID", "").strip()
    secret = os.getenv("SHOPEE_SECRET", "").strip()
    if not app.isdecimal() or not secret:
        print(json.dumps({"status": "NO_CREDENTIALS_SAFE_STOP", "writes_blogger": False}))
        return 2
    rows = []
    for i, (name, query) in enumerate(QUERIES):
        if i:
            time.sleep(1.5)
        result = send_query(name, query, app, secret)
        rows.append(result)
        if result.get("status") in ("NETWORK_FAILURE", "OVERSIZE", "NON_JSON", "INVALID_RESPONSE"):
            break
        if result.get("http_status") in (401, 403, 429):
            break
        if any(c in (10020, 10030, 10035) for c in result.get("graphql_error_codes", [])):
            break
    print(json.dumps({
        "kind": "V31_SHOPEE_ARGS_DIFFERENTIAL_SAFE",
        "classification": summarize(rows),
        "queries_executed": len(rows),
        "max_calls": MAX_CALLS,
        "writes_blogger": False,
        "shopee_mutations": False,
        "results": rows,
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
