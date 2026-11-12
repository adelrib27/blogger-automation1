#!/usr/bin/env python3
"""LAB-only: diagnostico diferencial Shopee GraphQL, sem PUT Blogger.

Maximo 4 requisicoes HTTP POST autenticadas e sequenciais; nenhum secret, body,
header, produto, nome de loja, ID ou URL e exibido.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

ENDPOINT = "https://open-api.affiliate.shopee.com.br/graphql"
QUERIES = (
    ("graphql_root", "query V31Probe { __typename }"),
    ("offers_shape", 'query V31Probe { productOfferV2(keyword: "mouse", page: 1, limit: 1) { nodes { __typename } } }'),
    ("offers_fields", 'query V31Probe { productOfferV2(keyword: "mouse", page: 1, limit: 1) { nodes { itemId productName } } }'),
    ("offers_filters", 'query V31Probe { productOfferV2(keyword: "mouse", listType: 2, sortType: 2, page: 1, limit: 1) { nodes { itemId productName } } }'),
)
MAX_CALLS = 4


def safe_code(value):
    if isinstance(value, int) and 0 <= value <= 999999:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,6}", value):
        return int(value)
    return "unknown"


def sanitize_reply(http_status, raw, name):
    result = {"probe": name, "http_status": http_status, "json_ok": False,
              "graphql_error_codes": [], "api_data": False, "offers_count": None}
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError, TypeError):
        result["status"] = "NON_JSON"
        return result
    if not isinstance(data, dict):
        result["status"] = "INVALID_RESPONSE"
        return result
    result["json_ok"] = True
    errors = data.get("errors")
    if isinstance(errors, list) and errors:
        result["graphql_error_codes"] = [
            safe_code((e.get("extensions") or {}).get("code", e.get("code")))
            if isinstance(e, dict) and isinstance(e.get("extensions"), (dict, type(None)))
            else "unknown" for e in errors[:5]
        ]
        result["status"] = "GRAPHQL_ERROR"
        return result
    if not isinstance(data.get("data"), dict):
        result["status"] = "NO_DATA"
        return result
    result["api_data"] = True
    offers = data["data"].get("productOfferV2")
    if isinstance(offers, dict) and isinstance(offers.get("nodes"), list):
        result["offers_count"] = len(offers["nodes"])
    result["status"] = "GRAPHQL_OK" if http_status == 200 else "HTTP_ERROR_WITH_DATA"
    return result


def send_query(name, query, app, secret):
    payload = json.dumps({"query": query, "operationName": "V31Probe"},
                         ensure_ascii=False, separators=(",", ":"))
    now = int(time.time())
    signature = hashlib.sha256((app + str(now) + payload + secret).encode("utf-8")).hexdigest()
    request = urllib.request.Request(
        ENDPOINT,
        method="POST",
        data=payload.encode("utf-8"),
        headers={
            "Authorization": "SHA256 Credential=" + app + ", Timestamp=" + str(now) +
                             ", Signature=" + signature,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BloggerAutomation-V31-LAB-Diff/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=16) as response:
            http = response.status
            raw = response.read(100_001)
    except urllib.error.HTTPError as error:
        http = error.code
        raw = error.read(100_001)
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"probe": name, "status": "NETWORK_FAILURE", "http_status": None,
                "graphql_error_codes": [], "api_data": False}
    if len(raw) > 100_000:
        return {"probe": name, "status": "OVERSIZE", "http_status": http,
                "graphql_error_codes": [], "api_data": False}
    return sanitize_reply(http, raw, name)


def summarize(results):
    root = next((r for r in results if r["probe"] == "graphql_root"), {})
    products = [r for r in results if r["probe"].startswith("offers_")]
    if root.get("status") == "GRAPHQL_OK" and all(r.get("status") == "GRAPHQL_ERROR" for r in products):
        return "ROOT_OK_OFFERS_ERROR"
    if root.get("status") == "GRAPHQL_OK" and any(r.get("status") == "GRAPHQL_OK" for r in products):
        return "OFFERS_AT_LEAST_ONE_QUERY_OK"
    if root.get("status") == "GRAPHQL_ERROR":
        return "ROOT_QUERY_ERROR"
    return "INCONCLUSIVE"


def main():
    app = os.getenv("SHOPEE_APP_ID", "").strip()
    secret = os.getenv("SHOPEE_SECRET", "").strip()
    if not app.isdecimal() or not secret:
        print(json.dumps({"status": "NO_CREDENTIALS_SAFE_STOP", "writes_blogger": False}))
        return 2
    results = []
    for i, (name, query) in enumerate(QUERIES):
        if i:
            time.sleep(1.25)
        result = send_query(name, query, app, secret)
        results.append(result)
        # Em caso de bloqueio autenticação/rate-limit, não repetir.
        if result.get("status") in ("NETWORK_FAILURE", "OVERSIZE", "NON_JSON", "INVALID_RESPONSE"):
            break
        if result.get("http_status") in (401, 403, 429):
            break
        if any(c in (10020, 10030, 10035) for c in result.get("graphql_error_codes", [])):
            break
    summary = {"kind": "V31_SHOPEE_GRAPHQL_DIFFERENTIAL_SAFE", "classification": summarize(results),
               "queries_executed": len(results), "max_calls": MAX_CALLS,
               "writes_blogger": False, "shopee_mutations": False,
               "results": results}
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
