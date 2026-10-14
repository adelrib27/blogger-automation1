import json
from collections import Counter

import shopee_oportunidades as base


def product_axes(product: dict) -> tuple[str, str, str]:
    shop = str(product.get("shopId") or product.get("shopName") or "sem-loja")
    keywords = product.get("keywords") or []
    categories = product.get("categories") or []
    keyword = str(keywords[0]) if keywords else "sem-subcategoria"
    category = str(categories[0]) if categories else "sem-categoria"
    return shop, keyword, category


def _fits(counts: dict[str, Counter], product: dict, caps: dict) -> bool:
    shop, keyword, category = product_axes(product)
    return (
        counts["shop"][shop] < int(caps["max_per_shop"])
        and counts["keyword"][keyword] < int(caps["max_per_keyword"])
        and counts["category"][category] < int(caps["max_per_category"])
    )


def _add(counts: dict[str, Counter], product: dict) -> None:
    shop, keyword, category = product_axes(product)
    counts["shop"][shop] += 1
    counts["keyword"][keyword] += 1
    counts["category"][category] += 1


def _initial_counts(existing: list[dict] | None = None) -> dict[str, Counter]:
    counts = {
        "shop": Counter(),
        "keyword": Counter(),
        "category": Counter(),
    }
    for product in existing or []:
        _add(counts, product)
    return counts


def select_with_diversity(
    candidates: list[dict],
    limit: int,
    config: dict,
    existing: list[dict] | None = None,
) -> tuple[list[dict], dict]:
    diversity = config.get("diversity") or {}
    if not diversity.get("enabled", True):
        selected = candidates[:limit]
        for p in selected:
            p["selectionPass"] = "diversity_disabled"
        return selected, {"strict": 0, "relaxed": 0, "fallback": len(selected)}

    strict_caps = {
        "max_per_shop": int(diversity.get("max_per_shop", 3)),
        "max_per_keyword": int(diversity.get("max_per_keyword", 4)),
        "max_per_category": int(diversity.get("max_per_category", 8)),
    }
    relaxed_cfg = diversity.get("relaxed_caps") or {}
    relaxed_caps = {
        "max_per_shop": int(relaxed_cfg.get("max_per_shop", max(5, strict_caps["max_per_shop"]))),
        "max_per_keyword": int(relaxed_cfg.get("max_per_keyword", max(6, strict_caps["max_per_keyword"]))),
        "max_per_category": int(relaxed_cfg.get("max_per_category", max(10, strict_caps["max_per_category"]))),
    }

    counts = _initial_counts(existing)
    selected: list[dict] = []
    selected_ids: set[str] = set()
    deferred: list[dict] = []
    stats = {"strict": 0, "relaxed": 0, "fallback": 0}

    for product in candidates:
        if len(selected) >= limit:
            break
        item_id = str(product.get("itemId") or "")
        if item_id in selected_ids:
            continue
        if _fits(counts, product, strict_caps):
            product["selectionPass"] = "strict_diversity"
            selected.append(product)
            selected_ids.add(item_id)
            _add(counts, product)
            stats["strict"] += 1
        else:
            deferred.append(product)

    if len(selected) < limit:
        still_deferred: list[dict] = []
        for product in deferred:
            if len(selected) >= limit:
                break
            item_id = str(product.get("itemId") or "")
            if item_id in selected_ids:
                continue
            if _fits(counts, product, relaxed_caps):
                product["selectionPass"] = "relaxed_diversity"
                selected.append(product)
                selected_ids.add(item_id)
                _add(counts, product)
                stats["relaxed"] += 1
            else:
                still_deferred.append(product)

        deferred = still_deferred

    if len(selected) < limit:
        for product in deferred:
            if len(selected) >= limit:
                break
            item_id = str(product.get("itemId") or "")
            if item_id in selected_ids:
                continue
            product["selectionPass"] = "fallback_fill"
            selected.append(product)
            selected_ids.add(item_id)
            _add(counts, product)
            stats["fallback"] += 1

    return selected, stats


def diversity_summary(ranking: list[dict], stats: dict, config: dict) -> dict:
    shops = Counter()
    keywords = Counter()
    categories = Counter()
    for product in ranking:
        shop, keyword, category = product_axes(product)
        shops[shop] += 1
        keywords[keyword] += 1
        categories[category] += 1

    return {
        "policy": config.get("diversity") or {},
        "selectionPasses": stats,
        "shopDistribution": shops.most_common(),
        "keywordDistribution": keywords.most_common(),
        "categoryDistribution": categories.most_common(),
    }


def save_diversity_report(ranking: list[dict], stats: dict, config: dict) -> None:
    base.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = diversity_summary(ranking, stats, config)
    (base.OUTPUT_DIR / "diversity_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def scan_v22() -> list[dict]:
    config = base.load_config()
    app_id = base.required_env("SHOPEE_APP_ID")
    secret = base.required_env("SHOPEE_SECRET")
    selected_categories = base.select_categories(config)

    query_limit = int(config.get("query_limit", 15))
    reserve_query_limit = int(config.get("reserve_query_limit", query_limit))
    min_seller_rate = base.to_float(config.get("min_seller_commission_rate", 0.001))
    min_rating = base.to_float(config.get("min_rating_when_available", 4.0))
    reserve_min_rating = base.to_float(config.get("reserve_min_rating_when_available", min_rating))
    reserve_enabled = bool(config.get("reserve_enabled", True))
    top_n = max(1, int(base.TOP_N_OVERRIDE or config.get("top_n", 30)))

    suggestions_by_keyword: dict[str, list[str]] = {}

    print("=== Radar Tech BR — Shopee Oportunidades Fase 2.2 ===")
    print("Regra 1: comissão extra primeiro; comissão padrão somente se faltarem opções com extra.")
    print("Regra 2: diversidade por loja, subcategoria de busca e categoria editorial.")
    print("Regra 3: sinal de busca tem peso reforçado, sem tratar Autocomplete como volume mensal.")
    print(f"Meta do ranking: {top_n} produtos.")

    primary_merged = base.scan_primary_extra(
        app_id,
        secret,
        selected_categories,
        query_limit,
        min_seller_rate,
        min_rating,
        suggestions_by_keyword,
    )
    primary = base.score_products(list(primary_merged.values()), config)
    print(f"\nProdutos qualificados com comissão extra: {len(primary)}")

    primary_selected, primary_stats = select_with_diversity(primary, min(top_n, len(primary)), config)
    ranking = list(primary_selected)
    aggregate_stats = dict(primary_stats)

    if len(ranking) < top_n and reserve_enabled and len(primary) < top_n:
        missing = top_n - len(ranking)
        print(f"Faltam {missing} opções com comissão extra; ativando reserva de comissão padrão.")
        reserve_merged = base.scan_reserve_standard(
            app_id,
            secret,
            selected_categories,
            reserve_query_limit,
            reserve_min_rating,
            suggestions_by_keyword,
            set(primary_merged.keys()),
        )
        reserve = base.score_products(list(reserve_merged.values()), config)
        reserve_selected, reserve_stats = select_with_diversity(
            reserve,
            missing,
            config,
            existing=ranking,
        )
        ranking.extend(reserve_selected)
        for key in aggregate_stats:
            aggregate_stats[key] += reserve_stats.get(key, 0)
        print(f"Produtos de reserva encontrados: {len(reserve)}")
        print(f"Produtos de reserva usados: {len(reserve_selected)}")
    else:
        print("Reserva não utilizada.")

    base.save_outputs(ranking, suggestions_by_keyword, config)
    save_diversity_report(ranking, aggregate_stats, config)
    return ranking


def print_v22(ranking: list[dict]) -> None:
    if not ranking:
        print("Nenhuma oportunidade passou pelos filtros.")
        return

    extra_count = sum(1 for p in ranking if p.get("priorityTier") == "COMISSAO_EXTRA")
    reserve_count = len(ranking) - extra_count
    shops = Counter(str(p.get("shopName") or "sem-loja") for p in ranking)
    categories = Counter((p.get("categories") or ["sem-categoria"])[0] for p in ranking)

    print(f"\nRANKING FINAL: {len(ranking)} produtos | extra={extra_count} | reserva={reserve_count}")
    print(f"Diversidade: {len(shops)} lojas | {len(categories)} categorias editoriais")
    print("Lojas mais presentes: " + ", ".join(f"{name}={count}" for name, count in shops.most_common(5)))

    print(f"\nTOP {min(len(ranking), 15)} OPORTUNIDADES")
    for index, p in enumerate(ranking[:15], start=1):
        tier = "EXTRA" if p.get("priorityTier") == "COMISSAO_EXTRA" else "RESERVA"
        keyword = (p.get("keywords") or ["-"])[0]
        category = (p.get("categories") or ["-"])[0]
        print(
            f"{index:02d}. [{tier}] score={p.get('opportunityScore')} | "
            f"seller extra={p.get('sellerExtraCommissionPct')}% | "
            f"busca={round(base.to_float(p.get('searchDemandProxy')) * 100, 1)} | "
            f"vendas={p.get('sales')} | nota={p.get('ratingStar')}"
        )
        print(f"    {p.get('productName')}")
        print(
            f"    loja={p.get('shopName')} | categoria={category} | termo={keyword} | "
            f"seleção={p.get('selectionPass')}"
        )
        print(f"    {p.get('offerLink')}")


def main() -> None:
    ranking = scan_v22()
    print_v22(ranking)
    print(f"\nArquivos gerados em: {base.OUTPUT_DIR}")


if __name__ == "__main__":
    main()
