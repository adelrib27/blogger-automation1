#!/usr/bin/env python3
"""Matriz de leitura Shopee: isolar keyword/sortType/campos sem publicar.

Não mostra Authorization, assinatura, Secret, ofertas/URLs ou resposta bruta.
No máximo sete chamadas assinadas, intervalos de três segundos.
"""
from __future__ import annotations
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from shopee_graphql_minimal_safe_v31 import (
    API, EXPECTED_APP_ID, get_request_id, safe_text,
)

CASES = (
    ("keyword_only", 'query { productOfferV2(keyword: "cordas para violao nylon", page: 1, limit: 1) { nodes { itemId imageUrl offerLink } } }'),
    ("sort_only", 'query { productOfferV2(sortType: 2, page: 1, limit: 1) { nodes { itemId imageUrl offerLink } } }'),
    ("rich_fields", 'query { productOfferV2(page: 1, limit: 1) { nodes { itemId productName imageUrl offerLink priceMin priceMax shopName ratingStar sales } pageInfo { page hasNextPage } } }'),
    ("v31_shape", 'query ViolaoComeco { productOfferV2(keyword: "cordas para violao nylon", sortType: 2, page: 1, limit: 1) { nodes { itemId productName imageUrl offerLink priceMin priceMax shopName ratingStar sales } pageInfo { page hasNextPage } } }'),
    ("v31_limit10", 'query ViolaoComeco { productOfferV2(keyword: "encordoamento violao nylon", sortType: 2, page: 1, limit: 10) { nodes { itemId productName imageUrl offerLink priceMin priceMax shopName ratingStar sales } pageInfo { page hasNextPage } } }'),
    ("v31_limit20_page1", 'query ViolaoComeco { productOfferV2(keyword: "encordoamento violao nylon", sortType: 2, page: 1, limit: 20) { nodes { itemId productName imageUrl offerLink priceMin priceMax shopName ratingStar sales } pageInfo { page hasNextPage } } }'),
    ("v31_limit20_page2", 'query ViolaoComeco { productOfferV2(keyword: "encordoamento violao nylon", sortType: 2, page: 2, limit: 20) { nodes { itemId productName imageUrl offerLink priceMin priceMax shopName ratingStar sales } pageInfo { page hasNextPage } } }'),
)


def one_case(app, secret, case, query):
    payload = {"query": query}
    if case == "v31_shape" or case.startswith("v31_limit"):
        payload["operationName"] = "ViolaoComeco"
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    ts = str(int(time.time()))
    sign = hashlib.sha256((app + ts + body + secret).encode()).hexdigest()
    req = urllib.request.Request(
        API,
        data=body.encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"SHA256 Credential={app}, Timestamp={ts}, Signature={sign}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BloggerEditorialV31-Shopee-MatrixSAFE/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=24) as res:
            status, raw, headers = res.status, res.read(262145), res.headers
    except urllib.error.HTTPError as exc:
        status, raw, headers = exc.code, exc.read(262145), exc.headers
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"case": case, "status": "NETWORK_ERROR", "error_type": type(exc).__name__}
    result = {
        "case": case, "http_status": status, "request_id": get_request_id(headers),
    }
    if len(raw) > 262144:
        return dict(result, status="RESPONSE_TOO_LARGE")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        return dict(result, status="INVALID_JSON")
    if not isinstance(parsed, dict):
        return dict(result, status="INVALID_RESPONSE")
    if parsed.get("errors"):
        err = parsed["errors"][0]
        ext = err.get("extensions") or {} if isinstance(err, dict) else {}
        return dict(
            result, status="GRAPHQL_ERROR",
            code=ext.get("code") if isinstance(ext, dict) else None,
            message=safe_text(err.get("message") if isinstance(err, dict) else "", app, secret),
        )
    offer = (parsed.get("data") or {}).get("productOfferV2") or {}
    nodes = offer.get("nodes") if isinstance(offer, dict) else None
    return dict(result, status="OK" if isinstance(nodes, list) else "INVALID_NODES",
                nodes_count=len(nodes) if isinstance(nodes, list) else None)


def main():
    app = os.getenv("SHOPEE_APP_ID", "").strip()
    secret = os.getenv("SHOPEE_SECRET", "").strip()
    if not app or not secret or app != EXPECTED_APP_ID:
        print("FAIL_CLOSED missing_credentials_or_app_mismatch")
        return 2
    for idx, (name, query) in enumerate(CASES):
        if idx:
            time.sleep(3)
        print(json.dumps(one_case(app, secret, name, query), ensure_ascii=False), flush=True)
    print("MATRIX_DIAGNOSTIC_COMPLETE_NO_BLOGGER_WRITE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
