#!/usr/bin/env python3
"""LAB: uma consulta Shopee sem sort/listType, compara filtros sobre itens REAIS.

Nenhuma escrita em Blogger, nenhum artefato contendo ofertas, IDs ou secrets.
Limita resposta, tempo e tentativas; resultado com contagens agregadas somente.
"""
from __future__ import annotations
import hashlib
import json
import os
import time
import urllib.error
import urllib.request

from lab_shopee_filters_probe import strict_eligible, selected_count, CATEGORY, KEYWORD
from shopee_r2_safe import ENDPOINT, normalize

QUERY = ('query V31RealCount { productOfferV2(keyword: "mouse", page: 1, limit: 20) '
         '{ nodes { itemId productName offerLink imageUrl priceMin shopId ratingStar sales } } }')


def failure(status: str, http_status=None, codes=None):
    result = {"kind": "V31_LAB_ONE_QUERY_REAL_OFFER_COUNT",
              "status": status, "http_status": http_status,
              "graphql_error_codes": codes or [], "writes_blogger": False,
              "shopee_requests": 1, "shopee_mutations": False,
              "products_persisted": False}
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


def main():
    app = os.getenv("SHOPEE_APP_ID", "").strip()
    secret = os.getenv("SHOPEE_SECRET", "").strip()
    if not app.isdecimal() or not secret:
        return failure("NO_CREDENTIALS", None)
    body = json.dumps({"query": QUERY, "operationName": "V31RealCount"},
                      ensure_ascii=False, separators=(",", ":"))
    stamp = int(time.time())
    signature = hashlib.sha256((app + str(stamp) + body + secret).encode("utf-8")).hexdigest()
    req = urllib.request.Request(ENDPOINT, data=body.encode("utf-8"), method="POST", headers={
        "Authorization": "SHA256 Credential=" + app + ", Timestamp=" + str(stamp) +
                         ", Signature=" + signature,
        "Content-Type": "application/json", "Accept": "application/json",
        "User-Agent": "BloggerAutomation-V31-LAB-OneQuery/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            http, raw = res.status, res.read(200_001)
    except urllib.error.HTTPError as exc:
        http, raw = exc.code, exc.read(200_001)
    except (urllib.error.URLError, TimeoutError, OSError):
        return failure("NETWORK_ERROR", None)
    if len(raw) > 200_000:
        return failure("OVERSIZE", http)
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError):
        return failure("NON_JSON", http)
    if not isinstance(data, dict):
        return failure("INVALID_RESPONSE", http)
    errors = data.get("errors") or []
    if errors:
        codes = []
        for e in errors[:5]:
            ext = e.get("extensions") if isinstance(e, dict) else {}
            raw_code = (ext or {}).get("code") if isinstance(ext, (dict, type(None))) else None
            codes.append(raw_code if isinstance(raw_code, int) and 0 <= raw_code <= 999999 else "unknown")
        return failure("API_BLOCKED_NO_UPDATE", http, codes)
    nodes = ((data.get("data") or {}).get("productOfferV2") or {}).get("nodes")
    if http != 200 or not isinstance(nodes, list):
        return failure("NO_VALID_OFFERS_RESPONSE", http)
    strict = [p for item in nodes if isinstance(item, dict) and (p := strict_eligible(item))]
    relaxed = [p for item in nodes if isinstance(item, dict) and (p := normalize(item, CATEGORY))]
    result = {
        "kind": "V31_LAB_ONE_QUERY_REAL_OFFER_COUNT",
        "status": "RECEIVED_REAL_OFFERS_NO_WRITE",
        "http_status": http,
        "received_nodes": len(nodes),
        "eligible_strict": len(strict),
        "eligible_relaxed": len(relaxed),
        "selected_strict_max4": selected_count(strict, 2),
        "selected_relaxed_max4": selected_count(relaxed, 4),
        "writes_blogger": False, "shopee_requests": 1,
        "shopee_mutations": False, "products_persisted": False
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
