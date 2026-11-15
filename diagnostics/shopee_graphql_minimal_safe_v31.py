#!/usr/bin/env python3
"""Diagnóstico SAFE Shopee Affiliate GraphQL.

Somente um POST de leitura. Não imprime secrets, Authorization ou URLs completas.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

EXPECTED_APP_ID = "18352820579"
API = "https://open-api.affiliate.shopee.com.br/graphql"
QUERY = """query {
  productOfferV2(page: 1, limit: 1) {
    nodes { itemId imageUrl offerLink }
  }
}"""


def safe_text(value, app="", secret=""):
    value = " ".join(str(value or "").split())
    for sensitive in (secret, app):
        if sensitive:
            value = value.replace(sensitive, "[REDACTED]")
    return value[:180]


def get_request_id(headers):
    for name in ("x-request-id", "x-shopee-request-id", "x-trace-id", "trace-id"):
        value = headers.get(name) if headers is not None else None
        if value and re.fullmatch(r"[A-Za-z0-9:._-]{1,128}", str(value).strip()):
            return str(value).strip()
    return None


def allowed_url(value, kind):
    try:
        u = urlsplit(str(value or ""))
        host = (u.hostname or "").lower()
        if u.scheme != "https" or u.username or u.password:
            return False
        if kind == "offer":
            return host in ("s.shopee.com.br", "shopee.com.br", "www.shopee.com.br")
        return host == "shopee.com.br" or host.endswith(".shopee.com.br")
    except ValueError:
        return False


def signed_request(app, secret, timestamp):
    body = json.dumps({"query": QUERY}, ensure_ascii=False, separators=(",", ":"))
    sign = hashlib.sha256((app + str(timestamp) + body + secret).encode("utf-8")).hexdigest()
    auth = f"SHA256 Credential={app}, Timestamp={timestamp}, Signature={sign}"
    return body.encode("utf-8"), auth


def self_test():
    body, auth = signed_request("123", "abc", 1700000000)
    assert json.loads(body)["query"] == QUERY
    assert "Credential=123, Timestamp=1700000000, Signature=" in auth
    assert allowed_url("https://s.shopee.com.br/abc", "offer")
    assert allowed_url("https://cf.shopee.com.br/file/abc", "image")
    assert not allowed_url("https://evil.example/offer", "offer")
    assert not allowed_url("http://cf.shopee.com.br/file/abc", "image")
    print("SELF_TEST_PASS_NO_NETWORK")


def main():
    if "--self-test" in sys.argv:
        self_test()
        return 0
    app = os.getenv("SHOPEE_APP_ID", "").strip()
    secret = os.getenv("SHOPEE_SECRET", "").strip()
    if not app or not secret:
        print("FAIL_CLOSED credentials_missing")
        return 2
    if app != EXPECTED_APP_ID:
        print("FAIL_CLOSED app_id_mismatch")
        return 2
    body, auth = signed_request(app, secret, int(time.time()))
    req = urllib.request.Request(
        API, data=body, method="POST",
        headers={
            "Authorization": auth, "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BloggerEditorialV31-Shopee-MinimalSAFE/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            status, raw, headers = response.status, response.read(262145), response.headers
    except urllib.error.HTTPError as exc:
        status, raw, headers = exc.code, exc.read(262145), exc.headers
    except (urllib.error.URLError, TimeoutError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED_NETWORK", "error_type": type(exc).__name__}))
        return 2
    report = {
        "status": "FAIL_CLOSED",
        "http_status": status,
        "request_id": get_request_id(headers),
        "graphql_errors": [],
    }
    if len(raw) > 262144:
        report["reason"] = "response_too_large"
        print(json.dumps(report))
        return 2
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        report["reason"] = "invalid_json"
        print(json.dumps(report))
        return 2
    if not isinstance(data, dict):
        report["reason"] = "non_object_response"
        print(json.dumps(report))
        return 2
    if data.get("errors"):
        report["graphql_errors"] = [
            {
                "code": (error.get("extensions") or {}).get("code")
                if isinstance(error.get("extensions"), dict) else None,
                "message": safe_text(error.get("message"), app, secret),
            }
            for error in data["errors"][:3] if isinstance(error, dict)
        ]
        print(json.dumps(report, ensure_ascii=False))
        return 2
    offer_data = (data.get("data") or {}).get("productOfferV2") or {}
    nodes = offer_data.get("nodes") if isinstance(offer_data, dict) else None
    if not isinstance(nodes, list):
        report["reason"] = "invalid_nodes"
        print(json.dumps(report))
        return 2
    product = nodes[0] if nodes and isinstance(nodes[0], dict) else {}
    report["nodes_count"] = len(nodes)
    report["itemId"] = safe_text(product.get("itemId"), app, secret) if product else None
    report["fields_present"] = {
        key: bool(str(product.get(key) or "").strip())
        for key in ("itemId", "imageUrl", "offerLink")
    }
    report["urls_https_and_domain_valid"] = {
        "imageUrl": allowed_url(product.get("imageUrl"), "image"),
        "offerLink": allowed_url(product.get("offerLink"), "offer"),
    }
    if status == 200 and all(report["fields_present"].values()) and all(report["urls_https_and_domain_valid"].values()):
        report["status"] = "SAFE_MINIMAL_QUERY_PASS_NO_BLOGGER_WRITE"
        print(json.dumps(report, ensure_ascii=False))
        return 0
    report["reason"] = "no_complete_valid_product"
    print(json.dumps(report, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
