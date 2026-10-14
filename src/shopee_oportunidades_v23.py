import json
import os
import re
import unicodedata
from pathlib import Path

import shopee_oportunidades as base
import shopee_oportunidades_v22 as v22


INTENT_RULES_PATH = Path(
    os.getenv("SHOPEE_INTENT_RULES", "config/shopee_intent_rules.json")
)


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def contains_phrase(normalized_text: str, phrase: str) -> bool:
    phrase_norm = normalize(phrase)
    if not phrase_norm:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(phrase_norm).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
    return re.search(pattern, normalized_text) is not None


def load_intent_rules() -> dict:
    with INTENT_RULES_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def evaluate_keyword(product_name: str, keyword: str, rules_doc: dict) -> dict:
    name = normalize(product_name)
    key = normalize(keyword)
    rules = rules_doc.get("rules") or {}
    rule = rules.get(keyword) or rules.get(key)

    if not rule:
        product_tokens = set(name.split())
        keyword_tokens = {token for token in key.split() if len(token) >= 3}
        overlap = len(product_tokens & keyword_tokens) / max(1, len(keyword_tokens))
        accepted = overlap >= 0.6
        return {
            "accepted": accepted,
            "score": round(overlap, 4),
            "reason": "fallback_token_overlap" if accepted else "fallback_overlap_insuficiente",
            "matched": sorted(product_tokens & keyword_tokens),
        }

    blocked = []
    for phrase in rule.get("block_phrases") or []:
        if contains_phrase(name, phrase):
            blocked.append(phrase)

    if blocked:
        return {
            "accepted": False,
            "score": 0.0,
            "reason": "termo_bloqueado",
            "blocked": blocked,
            "matched": [],
        }

    groups = rule.get("require_groups") or []
    matched_groups = []
    missing_groups = []

    for group in groups:
        matches = [phrase for phrase in group if contains_phrase(name, phrase)]
        if matches:
            matched_groups.append(matches)
        else:
            missing_groups.append(group)

    accepted = not missing_groups
    score = 1.0 if not groups and accepted else (len(matched_groups) / max(1, len(groups)))

    if accepted and key and contains_phrase(name, key):
        score = min(1.0, score + 0.10)

    return {
        "accepted": accepted,
        "score": round(score, 4),
        "reason": "intencao_confirmada" if accepted else "nucleo_do_produto_ausente",
        "matched": matched_groups,
        "missing": missing_groups,
    }


def keyword_category_map(config: dict) -> dict[str, str]:
    mapping = {}
    for category, keywords in (config.get("categories") or {}).items():
        for keyword in keywords:
            mapping[normalize(keyword)] = category
    return mapping


def semantic_filter(products: list[dict], config: dict, rules_doc: dict) -> tuple[list[dict], dict]:
    category_map = keyword_category_map(config)
    accepted_products = []
    rejected_products = []

    for product in products:
        original_keywords = list(product.get("keywords") or [])
        accepted_keywords = []
        evaluations = {}

        for keyword in original_keywords:
            result = evaluate_keyword(product.get("productName") or "", keyword, rules_doc)
            evaluations[keyword] = result
            if result.get("accepted"):
                accepted_keywords.append(keyword)

        if not accepted_keywords:
            rejected_products.append({
                "itemId": product.get("itemId"),
                "productName": product.get("productName"),
                "shopName": product.get("shopName"),
                "keywords": original_keywords,
                "evaluations": evaluations,
            })
            continue

        product["sourceKeywords"] = original_keywords
        product["keywords"] = accepted_keywords
        product["intentMatchedKeywords"] = accepted_keywords
        product["intentDecision"] = "ACEITO"
        product["semanticIntentScore"] = round(
            max(base.to_float(evaluations[k].get("score")) for k in accepted_keywords),
            4,
        )
        product["intentEvaluations"] = evaluations

        matched_categories = []
        for keyword in accepted_keywords:
            category = category_map.get(normalize(keyword))
            if category and category not in matched_categories:
                matched_categories.append(category)
        if matched_categories:
            product["categories"] = matched_categories

        accepted_products.append(product)

    stats = {
        "input": len(products),
        "accepted": len(accepted_products),
        "rejected": len(rejected_products),
        "rejectedProducts": rejected_products,
    }
    return accepted_products, stats


def run_regression_checks(rules_doc: dict) -> None:
    cases = [
        ("Carimbo Docinho VENTILADOR Impressão 3D Confeitaria Criativa", "ventilador", False),
        ("Ventilador de Teto com Luz Silencioso Controle Remoto", "ventilador", True),
        ("Adaptador de Tomada de Porcelana para Secador Air Fryer 20A", "air fryer", False),
        ("Kit 6 Forma de Silicone para Fritadeira Air Fryer", "air fryer", False),
        ("Fritadeira Elétrica Air Fryer 5L Digital 1500W", "air fryer", True),
        ("Papa Bolinhas Elétrico Tira Pelos de Roupas Aparador", "aparador de pelos", False),
        ("Máquina de Barbear e Aparador Pelos Elétrico 3 em 1", "aparador de pelos", True),
        ("Óculos de Sol Redondo Premium UV400", "oculos uv400", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})

    if failures:
        raise SystemExit(
            "Falha nos testes de regressão semântica: "
            + json.dumps(failures, ensure_ascii=False)
        )
    print(f"Testes semânticos de regressão: {len(cases)}/{len(cases)} OK")


def save_intent_report(
    ranking: list[dict],
    primary_stats: dict,
    reserve_stats: dict | None,
    diversity_stats: dict,
    config: dict,
) -> None:
    base.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "version": "2.3",
        "policy": "semantic intent -> extra commission priority -> search/performance score -> diversity -> standard commission reserve",
        "primarySemanticFilter": {
            "input": primary_stats.get("input", 0),
            "accepted": primary_stats.get("accepted", 0),
            "rejected": primary_stats.get("rejected", 0),
        },
        "reserveSemanticFilter": None,
        "diversity": v22.diversity_summary(ranking, diversity_stats, config),
        "ranking": [
            {
                "rank": index,
                "itemId": product.get("itemId"),
                "productName": product.get("productName"),
                "priorityTier": product.get("priorityTier"),
                "semanticIntentScore": product.get("semanticIntentScore"),
                "intentMatchedKeywords": product.get("intentMatchedKeywords"),
                "opportunityScore": product.get("opportunityScore"),
                "shopName": product.get("shopName"),
                "offerLink": product.get("offerLink"),
            }
            for index, product in enumerate(ranking, start=1)
        ],
        "rejectedSample": primary_stats.get("rejectedProducts", [])[:80],
    }
    if reserve_stats is not None:
        report["reserveSemanticFilter"] = {
            "input": reserve_stats.get("input", 0),
            "accepted": reserve_stats.get("accepted", 0),
            "rejected": reserve_stats.get("rejected", 0),
        }
        report["reserveRejectedSample"] = reserve_stats.get("rejectedProducts", [])[:40]

    (base.OUTPUT_DIR / "intent_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def scan_v23() -> list[dict]:
    config = base.load_config()
    rules_doc = load_intent_rules()
    run_regression_checks(rules_doc)

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

    print("=== Radar Tech BR — Shopee Oportunidades Fase 2.3 ===")
    print("Filtro novo: intenção semântica do produto antes do ranking.")
    print("Mantido: comissão extra primeiro, busca reforçada, performance e diversidade.")
    print(f"Meta do ranking: {top_n} produtos.")

    raw_primary = base.scan_primary_extra(
        app_id,
        secret,
        selected_categories,
        query_limit,
        min_seller_rate,
        min_rating,
        suggestions_by_keyword,
    )
    primary_filtered, primary_stats = semantic_filter(
        list(raw_primary.values()), config, rules_doc
    )
    primary = base.score_products(primary_filtered, config)

    print(
        f"Comissão extra: brutos={primary_stats['input']} | "
        f"semânticos aceitos={primary_stats['accepted']} | "
        f"rejeitados={primary_stats['rejected']}"
    )

    primary_selected, diversity_stats = v22.select_with_diversity(
        primary,
        min(top_n, len(primary)),
        config,
    )
    ranking = list(primary_selected)
    reserve_stats = None

    if len(ranking) < top_n and reserve_enabled:
        missing = top_n - len(ranking)
        print(f"Faltam {missing} produtos semânticos com comissão extra; ativando reserva padrão.")
        raw_reserve = base.scan_reserve_standard(
            app_id,
            secret,
            selected_categories,
            reserve_query_limit,
            reserve_min_rating,
            suggestions_by_keyword,
            set(raw_primary.keys()),
        )
        reserve_filtered, reserve_stats = semantic_filter(
            list(raw_reserve.values()), config, rules_doc
        )
        reserve = base.score_products(reserve_filtered, config)
        reserve_selected, reserve_diversity_stats = v22.select_with_diversity(
            reserve,
            missing,
            config,
            existing=ranking,
        )
        ranking.extend(reserve_selected)
        for key in diversity_stats:
            diversity_stats[key] += reserve_diversity_stats.get(key, 0)
        print(
            f"Reserva: brutos={reserve_stats['input']} | "
            f"semânticos aceitos={reserve_stats['accepted']} | "
            f"rejeitados={reserve_stats['rejected']} | usados={len(reserve_selected)}"
        )
    else:
        print("Reserva não utilizada.")

    base.save_outputs(ranking, suggestions_by_keyword, config)
    v22.save_diversity_report(ranking, diversity_stats, config)
    save_intent_report(ranking, primary_stats, reserve_stats, diversity_stats, config)
    return ranking


def print_v23(ranking: list[dict]) -> None:
    if not ranking:
        print("Nenhuma oportunidade passou pelos filtros.")
        return

    extra_count = sum(1 for p in ranking if p.get("priorityTier") == "COMISSAO_EXTRA")
    reserve_count = len(ranking) - extra_count
    print(f"\nRANKING FINAL 2.3: {len(ranking)} produtos | extra={extra_count} | reserva={reserve_count}")

    for index, product in enumerate(ranking[:15], start=1):
        tier = "EXTRA" if product.get("priorityTier") == "COMISSAO_EXTRA" else "RESERVA"
        print(
            f"{index:02d}. [{tier}] score={product.get('opportunityScore')} | "
            f"intenção={round(base.to_float(product.get('semanticIntentScore')) * 100, 1)} | "
            f"seller extra={product.get('sellerExtraCommissionPct')}% | "
            f"busca={round(base.to_float(product.get('searchDemandProxy')) * 100, 1)} | "
            f"vendas={product.get('sales')} | nota={product.get('ratingStar')}"
        )
        print(f"    {product.get('productName')}")
        print(
            f"    loja={product.get('shopName')} | termos={', '.join(product.get('intentMatchedKeywords') or [])} | "
            f"seleção={product.get('selectionPass')}"
        )
        print(f"    {product.get('offerLink')}")


def main() -> None:
    ranking = scan_v23()
    print_v23(ranking)
    print(f"\nArquivos gerados em: {base.OUTPUT_DIR}")


if __name__ == "__main__":
    main()
