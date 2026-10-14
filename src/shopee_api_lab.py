import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request


ENDPOINT = os.getenv(
    "SHOPEE_AFFILIATE_ENDPOINT",
    "https://open-api.affiliate.shopee.com.br/graphql",
).strip()


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        print(f"ERRO: variável obrigatória ausente: {name}")
        sys.exit(2)
    return value


def _safe_limit(value: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = 3
    return max(1, min(number, 10))


def _build_payload(keyword: str, limit: int) -> str:
    # json.dumps() aqui também faz o escape seguro da string inserida no GraphQL.
    graphql_keyword = json.dumps(keyword, ensure_ascii=False)

    query = f"""
query ShopeeAffiliateLab {{
  productOfferV2(keyword: {graphql_keyword}, sortType: 1, page: 1, limit: {limit}) {{
    nodes {{
      itemId
      productName
      commissionRate
      price
      imageUrl
      offerLink
      shopName
      sales
      ratingStar
    }}
    pageInfo {{
      page
      limit
      hasNextPage
    }}
  }}
}}
""".strip()

    # IMPORTANTE: a assinatura usa exatamente esta mesma string enviada no body.
    return json.dumps(
        {"query": query, "operationName": "ShopeeAffiliateLab"},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _authorization_header(app_id: str, secret: str, payload: str, timestamp: int) -> str:
    raw = f"{app_id}{timestamp}{payload}{secret}"
    signature = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return (
        f"SHA256 Credential={app_id}, "
        f"Timestamp={timestamp}, "
        f"Signature={signature}"
    )


def _post_graphql(app_id: str, secret: str, payload: str) -> tuple[int, dict]:
    timestamp = int(time.time())
    authorization = _authorization_header(app_id, secret, payload, timestamp)

    request = urllib.request.Request(
        ENDPOINT,
        data=payload.encode("utf-8"),
        method="POST",
        headers={
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RadarTechBR-ShopeeAffiliate-Lab/1.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.getcode()
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        print(f"ERRO DE REDE: {exc.reason}")
        sys.exit(3)

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print(f"ERRO: resposta não-JSON da Shopee (HTTP {status}).")
        print(body[:1500])
        sys.exit(4)

    return status, parsed


def _error_code(error: dict):
    extensions = error.get("extensions") or {}
    return extensions.get("code")


def _print_api_errors(status: int, errors: list[dict]) -> None:
    print(f"Shopee respondeu com erro (HTTP {status}).")
    for error in errors[:5]:
        code = _error_code(error)
        message = error.get("message", "erro sem mensagem")
        if code is not None:
            print(f"- código {code}: {message}")
        else:
            print(f"- {message}")

    print("\nDiagnóstico rápido:")
    print("- 10010 / GraphQL schema: credencial pode estar válida; ajuste campos/argumentos da query.")
    print("- 10020 / Invalid Credential ou Signature: confira App ID, Secret e horário do runner.")
    print("- 10030 / Rate Limit: aguarde e tente novamente com menor frequência.")
    print("- 10035 / No API Access: confirme que a Open API está habilitada para sua conta de afiliado.")


def main() -> None:
    app_id = _required_env("SHOPEE_APP_ID")
    secret = _required_env("SHOPEE_SECRET")
    keyword = os.getenv("SHOPEE_TEST_KEYWORD", "casa").strip() or "casa"
    limit = _safe_limit(os.getenv("SHOPEE_TEST_LIMIT", "3"))

    print("=== Shopee Affiliate Open API — laboratório seguro ===")
    print(f"Endpoint: {ENDPOINT}")
    print(f"Consulta: productOfferV2 | palavra-chave: {keyword!r} | limite: {limit}")
    print("Credenciais carregadas por variáveis de ambiente. O Secret não será exibido.")

    payload = _build_payload(keyword, limit)
    status, response = _post_graphql(app_id, secret, payload)

    errors = response.get("errors") or []
    if errors:
        _print_api_errors(status, errors)
        sys.exit(5)

    offers = ((response.get("data") or {}).get("productOfferV2") or {})
    nodes = offers.get("nodes") or []
    page_info = offers.get("pageInfo") or {}

    print(f"SUCESSO: autenticação aceita e GraphQL respondeu HTTP {status}.")
    print(f"Produtos retornados: {len(nodes)}")
    print(f"Paginação: {json.dumps(page_info, ensure_ascii=False)}")

    if not nodes:
        print("Nenhum produto retornado para esta palavra-chave. Tente outra no workflow manual.")
        return

    for index, item in enumerate(nodes[:limit], start=1):
        print(f"\nProduto {index}")
        print(f"- nome: {item.get('productName')}")
        print(f"- itemId: {item.get('itemId')}")
        print(f"- loja: {item.get('shopName')}")
        print(f"- preço bruto da API: {item.get('price')}")
        print(f"- comissão: {item.get('commissionRate')}")
        print(f"- vendas: {item.get('sales')}")
        print(f"- avaliação: {item.get('ratingStar')}")
        print(f"- imagem: {item.get('imageUrl')}")
        print(f"- link de afiliado: {item.get('offerLink')}")


if __name__ == "__main__":
    main()
