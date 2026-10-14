import csv
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ENDPOINT = os.getenv(
    "SHOPEE_AFFILIATE_ENDPOINT",
    "https://open-api.affiliate.shopee.com.br/graphql",
).strip()
CONFIG_PATH = Path(os.getenv("SHOPEE_OPPORTUNITIES_CONFIG", "config/shopee_oportunidades.json"))
OUTPUT_DIR = Path(os.getenv("SHOPEE_OUTPUT_DIR", "data/shopee_oportunidades"))
CATEGORY_FILTER = os.getenv("SHOPEE_CATEGORY", "all").strip()
TOP_N_OVERRIDE = os.getenv("SHOPEE_TOP_N", "").strip()

STOPWORDS = {
    "a", "as", "o", "os", "de", "da", "das", "do", "dos", "e", "em", "para",
    "com", "sem", "por", "um", "uma", "kit", "novo", "nova", "original", "produto"
}


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        print(f"ERRO: variável obrigatória ausente: {name}")
        sys.exit(2)
    return value


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def authorization_header(app_id: str, secret: str, payload: str, timestamp: int) -> str:
    raw = f"{app_id}{timestamp}{payload}{secret}"
    signature = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"


def post_graphql(app_id: str, secret: str, query: str, retries: int = 3) -> dict:
    payload = json.dumps(
        {"query": query, "operationName": "ShopeeOpportunityScan"},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    for attempt in range(1, retries + 1):
        timestamp = int(time.time())
        request = urllib.request.Request(
            ENDPOINT,
            data=payload.encode("utf-8"),
            method="POST",
            headers={
                "Authorization": authorization_header(app_id, secret, payload, timestamp),
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "RadarTechBR-ShopeeOpportunities/2.1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8", errors="replace")
                parsed = json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"errors": [{"message": f"HTTP {exc.code}: resposta não JSON"}]}
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == retries:
                raise RuntimeError(f"Falha de rede após {retries} tentativas: {exc}") from exc
            time.sleep(2 * attempt)
            continue

        errors = parsed.get("errors") or []
        if not errors:
            return parsed

        codes = {(err.get("extensions") or {}).get("code") for err in errors}
        if 10030 in codes and attempt < retries:
            time.sleep(3 * attempt)
            continue
        return parsed

    raise RuntimeError("Falha inesperada ao consultar Shopee")


def product_query(keyword: str, list_type: int, sort_type: int, limit: int, ams_only: bool) -> str:
    keyword_json = json.dumps(keyword, ensure_ascii=False)
    ams_value = "true" if ams_only else "false"
    return f"""
query ShopeeOpportunityScan {{
  productOfferV2(
    keyword: {keyword_json},
    listType: {list_type},
    sortType: {sort_type},
    isAMSOffer: {ams_value},
    page: 1,
    limit: {limit}
  ) {{
    nodes {{
      itemId
      productName
      productLink
      offerLink
      imageUrl
      priceMin
      priceMax
      priceDiscountRate
      sales
      ratingStar
      commissionRate
      sellerCommissionRate
      shopeeCommissionRate
      commission
      shopId
      shopName
      shopType
      periodStartTime
      periodEndTime
    }}
    pageInfo {{ page limit hasNextPage }}
  }}
}}
""".strip()


def google_suggestions(keyword: str) -> list[str]:
    params = urllib.parse.urlencode({
        "client": "firefox",
        "hl": "pt-BR",
        "gl": "br",
        "q": keyword,
    })
    url = f"https://suggestqueries.google.com/complete/search?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
        if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
            return [str(x) for x in data[1][:10]]
    except Exception:
        pass
    return []


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9áàâãéêíóôõúç ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokens(text: str) -> set[str]:
    return {t for t in normalize_text(text).split() if len(t) >= 3 and t not in STOPWORDS}


def to_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def search_proxy_for_product(product_name: str, keyword: str, suggestions: list[str]) -> float:
    name_norm = normalize_text(product_name)
    keyword_norm = normalize_text(keyword)
    name_tokens = tokens(product_name)
    keyword_tokens = tokens(keyword)

    score = 0.0
    if keyword_norm and keyword_norm in name_norm:
        score += 0.50
    elif keyword_tokens:
        overlap = len(name_tokens & keyword_tokens) / max(1, len(keyword_tokens))
        score += 0.35 * min(1.0, overlap)

    for rank, suggestion in enumerate(suggestions[:10], start=1):
        suggestion_tokens = tokens(suggestion)
        if not suggestion_tokens:
            continue
        overlap = len(name_tokens & suggestion_tokens) / max(1, len(suggestion_tokens))
        if overlap >= 0.5:
            score += (0.50 / rank) * overlap

    richness = min(len(suggestions), 10) / 10.0
    score += 0.15 * richness
    return min(score, 1.0)


def minmax(value: float, maximum: float) -> float:
    if maximum <= 0:
        return 0.0
    return max(0.0, min(value / maximum, 1.0))


def select_categories(config: dict) -> dict[str, list[str]]:
    categories = config.get("categories") or {}
    if CATEGORY_FILTER.lower() in {"", "all", "todas", "todos"}:
        return categories

    wanted = normalize_text(CATEGORY_FILTER)
    selected = {
        category: keywords
        for category, keywords in categories.items()
        if normalize_text(category) == wanted
    }
    if not selected:
        available = ", ".join(categories.keys())
        raise SystemExit(f"Categoria não encontrada: {CATEGORY_FILTER}. Disponíveis: {available}")
    return selected


def merge_item(merged: dict[str, dict], item: dict, category: str, keyword: str, source_mode: str, suggestions: list[str], priority_tier: str) -> None:
    item_id = str(item.get("itemId") or "").strip()
    if not item_id:
        return

    current = merged.setdefault(item_id, dict(item))
    current.setdefault("categories", [])
    current.setdefault("keywords", [])
    current.setdefault("sourceModes", [])
    current["priorityTier"] = priority_tier

    if category not in current["categories"]:
        current["categories"].append(category)
    if keyword not in current["keywords"]:
        current["keywords"].append(keyword)
    if source_mode not in current["sourceModes"]:
        current["sourceModes"].append(source_mode)

    proxy = search_proxy_for_product(item.get("productName") or "", keyword, suggestions)
    current["searchDemandProxy"] = max(to_float(current.get("searchDemandProxy")), proxy)


def scan_primary_extra(app_id: str, secret: str, selected_categories: dict[str, list[str]], query_limit: int, min_seller_rate: float, min_rating: float, suggestions_by_keyword: dict[str, list[str]]) -> dict[str, dict]:
    merged: dict[str, dict] = {}

    print("\n=== CAMADA 1 — COMISSÃO EXTRA ===")
    for category, keywords in selected_categories.items():
        print(f"\nCategoria: {category}")
        for keyword in keywords:
            suggestions = google_suggestions(keyword)
            suggestions_by_keyword[keyword] = suggestions
            print(f"- {keyword}: {len(suggestions)} sugestões Google")

            scans = [
                ("extra_commission", 1, 5),
                ("top_performance", 2, 2),
            ]
            for source_mode, list_type, sort_type in scans:
                response = post_graphql(
                    app_id,
                    secret,
                    product_query(keyword, list_type, sort_type, query_limit, ams_only=True),
                )
                errors = response.get("errors") or []
                if errors:
                    safe_errors = [
                        {"code": (e.get("extensions") or {}).get("code"), "message": e.get("message")}
                        for e in errors[:3]
                    ]
                    print(f"  aviso {source_mode}: {json.dumps(safe_errors, ensure_ascii=False)}")
                    continue

                nodes = (((response.get("data") or {}).get("productOfferV2") or {}).get("nodes") or [])
                for item in nodes:
                    seller_rate = to_float(item.get("sellerCommissionRate"))
                    rating = to_float(item.get("ratingStar"))
                    if seller_rate < min_seller_rate:
                        continue
                    if rating > 0 and rating < min_rating:
                        continue
                    merge_item(merged, item, category, keyword, source_mode, suggestions, "COMISSAO_EXTRA")

                time.sleep(0.15)

    return merged


def scan_reserve_standard(app_id: str, secret: str, selected_categories: dict[str, list[str]], query_limit: int, min_rating: float, suggestions_by_keyword: dict[str, list[str]], exclude_ids: set[str]) -> dict[str, dict]:
    merged: dict[str, dict] = {}

    print("\n=== CAMADA 2 — RESERVA, COMISSÃO PADRÃO ===")
    print("Esta camada só é consultada porque faltaram produtos com comissão extra.")

    for category, keywords in selected_categories.items():
        for keyword in keywords:
            suggestions = suggestions_by_keyword.get(keyword)
            if suggestions is None:
                suggestions = google_suggestions(keyword)
                suggestions_by_keyword[keyword] = suggestions

            scans = [
                ("reserve_top_performance", 2, 2),
                ("reserve_search", 1, 1),
            ]
            for source_mode, list_type, sort_type in scans:
                response = post_graphql(
                    app_id,
                    secret,
                    product_query(keyword, list_type, sort_type, query_limit, ams_only=False),
                )
                errors = response.get("errors") or []
                if errors:
                    safe_errors = [
                        {"code": (e.get("extensions") or {}).get("code"), "message": e.get("message")}
                        for e in errors[:3]
                    ]
                    print(f"  aviso {source_mode}/{keyword}: {json.dumps(safe_errors, ensure_ascii=False)}")
                    continue

                nodes = (((response.get("data") or {}).get("productOfferV2") or {}).get("nodes") or [])
                for item in nodes:
                    item_id = str(item.get("itemId") or "").strip()
                    if not item_id or item_id in exclude_ids:
                        continue

                    seller_rate = to_float(item.get("sellerCommissionRate"))
                    rating = to_float(item.get("ratingStar"))
                    shopee_rate = to_float(item.get("shopeeCommissionRate"))
                    total_rate = to_float(item.get("commissionRate"))

                    if seller_rate > 0:
                        continue
                    if shopee_rate <= 0 and total_rate <= 0:
                        continue
                    if rating > 0 and rating < min_rating:
                        continue

                    merge_item(merged, item, category, keyword, source_mode, suggestions, "RESERVA_COMISSAO_PADRAO")

                time.sleep(0.15)

    return merged


def score_products(products: list[dict], config: dict) -> list[dict]:
    if not products:
        return []

    max_seller = max(to_float(p.get("sellerCommissionRate")) for p in products)
    max_sales_log = max(math.log1p(to_int(p.get("sales"))) for p in products)
    weights = config.get("weights") or {}

    for p in products:
        seller_rate = to_float(p.get("sellerCommissionRate"))
        sales_log = math.log1p(to_int(p.get("sales")))
        rating = to_float(p.get("ratingStar"))
        discount = to_float(p.get("priceDiscountRate"))
        search_proxy = to_float(p.get("searchDemandProxy"))
        top_perf = 1.0 if any(
            mode in {"top_performance", "reserve_top_performance"}
            for mode in p.get("sourceModes", [])
        ) else 0.0

        components = {
            "seller_extra_commission": minmax(seller_rate, max_seller),
            "search_demand_proxy": search_proxy,
            "sales": minmax(sales_log, max_sales_log),
            "rating": minmax(rating, 5.0),
            "discount": minmax(discount, 100.0),
            "top_performance": top_perf,
        }
        score = sum(to_float(weights.get(k)) * v for k, v in components.items())
        p["opportunityScore"] = round(score * 100, 2)
        p["scoreComponents"] = {k: round(v, 4) for k, v in components.items()}
        p["sellerExtraCommissionPct"] = round(seller_rate * 100, 2)
        p["shopeeCommissionPct"] = round(to_float(p.get("shopeeCommissionRate")) * 100, 2)
        p["totalCommissionPct"] = round(to_float(p.get("commissionRate")) * 100, 2)
        p["priorityRank"] = 1 if p.get("priorityTier") == "COMISSAO_EXTRA" else 2

    products.sort(
        key=lambda p: (
            to_float(p.get("opportunityScore")),
            to_float(p.get("sellerCommissionRate")),
            to_int(p.get("sales")),
        ),
        reverse=True,
    )
    return products


def scan() -> list[dict]:
    config = load_config()
    app_id = required_env("SHOPEE_APP_ID")
    secret = required_env("SHOPEE_SECRET")
    selected_categories = select_categories(config)

    query_limit = int(config.get("query_limit", 15))
    reserve_query_limit = int(config.get("reserve_query_limit", query_limit))
    min_seller_rate = to_float(config.get("min_seller_commission_rate", 0.001))
    min_rating = to_float(config.get("min_rating_when_available", 4.0))
    reserve_min_rating = to_float(config.get("reserve_min_rating_when_available", min_rating))
    reserve_enabled = bool(config.get("reserve_enabled", True))
    top_n = max(1, int(TOP_N_OVERRIDE or config.get("top_n", 30)))

    suggestions_by_keyword: dict[str, list[str]] = {}

    print("=== Radar Tech BR — Shopee Oportunidades Fase 2.1 ===")
    print("Regra: comissão extra primeiro; comissão padrão somente para completar vagas.")
    print("Sinal de busca: Google Autocomplete como proxy; não é volume mensal exato.")
    print(f"Meta do ranking: {top_n} produtos.")

    primary_merged = scan_primary_extra(
        app_id, secret, selected_categories, query_limit, min_seller_rate, min_rating, suggestions_by_keyword
    )
    primary = score_products(list(primary_merged.values()), config)

    print(f"\nProdutos qualificados com comissão extra: {len(primary)}")

    if len(primary) >= top_n or not reserve_enabled:
        ranking = primary[:top_n]
        print("Reserva não utilizada.")
    else:
        missing = top_n - len(primary)
        print(f"Faltam {missing} vagas; buscando produtos de reserva.")

        reserve_merged = scan_reserve_standard(
            app_id,
            secret,
            selected_categories,
            reserve_query_limit,
            reserve_min_rating,
            suggestions_by_keyword,
            set(primary_merged.keys()),
        )
        reserve = score_products(list(reserve_merged.values()), config)
        ranking = primary[:top_n] + reserve[:missing]

        print(f"Produtos de reserva encontrados: {len(reserve)}")
        print(f"Produtos de reserva usados: {min(missing, len(reserve))}")

    ranking.sort(
        key=lambda p: (
            -to_int(p.get("priorityRank"), 2),
            to_float(p.get("opportunityScore")),
            to_int(p.get("sales")),
        ),
        reverse=True,
    )

    save_outputs(ranking, suggestions_by_keyword, config)
    return ranking


def save_outputs(ranking: list[dict], suggestions: dict[str, list[str]], config: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / "ranking.json"
    csv_path = OUTPUT_DIR / "ranking.csv"
    search_path = OUTPUT_DIR / "search_signals.json"

    extra_count = sum(1 for p in ranking if p.get("priorityTier") == "COMISSAO_EXTRA")
    reserve_count = sum(1 for p in ranking if p.get("priorityTier") == "RESERVA_COMISSAO_PADRAO")

    json_path.write_text(
        json.dumps(
            {
                "generatedAt": int(time.time()),
                "method": "seller-extra-first; standard commission only as reserve; Google Autocomplete proxy; Shopee performance",
                "searchSignalWarning": "Google Autocomplete é proxy de intenção/popularidade, não volume mensal exato.",
                "priorityPolicy": {
                    "commissionExtraFirst": True,
                    "standardCommissionOnlyToFillMissingSlots": True,
                    "extraCount": extra_count,
                    "reserveCount": reserve_count,
                },
                "config": config,
                "ranking": ranking,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    search_path.write_text(json.dumps(suggestions, ensure_ascii=False, indent=2), encoding="utf-8")

    fields = [
        "rank", "priorityTier", "priorityRank", "opportunityScore", "itemId",
        "productName", "shopName", "priceMin", "priceMax",
        "sellerExtraCommissionPct", "shopeeCommissionPct", "totalCommissionPct",
        "commission", "sales", "ratingStar", "priceDiscountRate",
        "searchDemandProxy", "categories", "keywords", "sourceModes", "imageUrl", "offerLink",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for index, product in enumerate(ranking, start=1):
            row = {field: product.get(field) for field in fields}
            row["rank"] = index
            for list_field in ("categories", "keywords", "sourceModes"):
                row[list_field] = " | ".join(product.get(list_field) or [])
            writer.writerow(row)


def print_ranking(ranking: list[dict]) -> None:
    if not ranking:
        print("Nenhuma oportunidade passou pelos filtros.")
        return

    extra_count = sum(1 for p in ranking if p.get("priorityTier") == "COMISSAO_EXTRA")
    reserve_count = len(ranking) - extra_count
    print(f"\nRANKING FINAL: {len(ranking)} produtos | extra={extra_count} | reserva={reserve_count}")

    print(f"\nTOP {min(len(ranking), 15)} OPORTUNIDADES")
    for index, p in enumerate(ranking[:15], start=1):
        tier = "EXTRA" if p.get("priorityTier") == "COMISSAO_EXTRA" else "RESERVA"
        print(
            f"{index:02d}. [{tier}] score={p.get('opportunityScore')} | "
            f"seller extra={p.get('sellerExtraCommissionPct')}% | "
            f"Shopee={p.get('shopeeCommissionPct')}% | "
            f"total={p.get('totalCommissionPct')}% | "
            f"vendas={p.get('sales')} | nota={p.get('ratingStar')}"
        )
        print(f"    {p.get('productName')}")
        print(f"    loja={p.get('shopName')} | comissão estimada={p.get('commission')}")
        print(
            f"    busca-proxy={round(to_float(p.get('searchDemandProxy')) * 100, 1)} | "
            f"{p.get('offerLink')}"
        )


def main() -> None:
    ranking = scan()
    print_ranking(ranking)
    print(f"\nArquivos gerados em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
