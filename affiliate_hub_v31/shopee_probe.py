"""Consulta única SAFE de autenticação Shopee para o V31 Editorial.

NÃO converte links, NÃO publica, NÃO altera estado e NÃO imprime dados comerciais.
O workflow de execução real é exclusivamente manual e limitado à branch main revisada.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request

ENDPOINT = "https://open-api.affiliate.shopee.com.br/graphql"
MAX_RESPONSE_BYTES = 131_072
QUERY = (
    'query V31EditorialSafeProbe { '
    'productOfferV2(keyword: "organizador", sortType: 1, page: 1, limit: 1) '
    '{ nodes { itemId } pageInfo { page limit hasNextPage } } }'
)


def payload() -> str:
    return json.dumps(
        {"query": QUERY, "operationName": "V31EditorialSafeProbe"},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def authorization(app_id: str, secret: str, body: str, timestamp: int) -> str:
    if not app_id.strip() or not secret.strip():
        raise ValueError("Credenciais ausentes")
    digest = hashlib.sha256(f"{app_id}{timestamp}{body}{secret}".encode("utf-8")).hexdigest()
    return f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={digest}"


def probe(app_id: str, secret: str) -> str:
    body = payload()
    auth = authorization(app_id, secret, body, int(time.time()))
    request = urllib.request.Request(
        ENDPOINT,
        data=body.encode("utf-8"),
        method="POST",
        headers={
            "Authorization": auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "V31EditorialShopeeSafeProbe/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        # Não ler/imprimir o corpo do erro: pode conter dados sensíveis.
        return "V31_SHOPEE_API_HTTP_ERROR_" + str(exc.code)
    except (urllib.error.URLError, TimeoutError):
        return "V31_SHOPEE_API_NETWORK_ERROR"

    if status != 200:
        return "V31_SHOPEE_API_UNEXPECTED_HTTP_STATUS"
    if len(raw) > MAX_RESPONSE_BYTES:
        return "V31_SHOPEE_API_RESPONSE_TOO_LARGE"
    try:
        parsed = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return "V31_SHOPEE_API_INVALID_JSON"
    if not isinstance(parsed, dict) or parsed.get("errors"):
        return "V31_SHOPEE_API_GRAPHQL_ERROR"
    offers = (parsed.get("data") or {}).get("productOfferV2")
    if not isinstance(offers, dict) or not isinstance(offers.get("nodes"), list):
        return "V31_SHOPEE_API_UNEXPECTED_SCHEMA"
    return "V31_SHOPEE_API_PASS"


def main() -> int:
    app_id = os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID", "").strip()
    secret = os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET", "").strip()
    if not app_id or not secret:
        print("V31_SHOPEE_API_CREDENTIALS_MISSING")
        return 2
    outcome = probe(app_id, secret)
    print(outcome)
    return 0 if outcome == "V31_SHOPEE_API_PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
