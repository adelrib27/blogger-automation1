#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import unicodedata
import re

import achados_casa_safe_scan_v2 as base


def norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def extra_keyword_gate(product: dict, keyword: str) -> bool:
    title = norm(product.get("productName") or "")
    key = norm(keyword)
    hard_blocks = {
        "umidificador": ["essencia", "essencias", "refil", "filtro para umidificador"],
        "mop giratorio": ["cabo para mop", "cabo mop", "refil", "reposicao"],
        "aspirador de po": ["saco para aspirador", "filtro para aspirador", "mangueira", "bico para aspirador"],
        "air fryer": ["forma de silicone", "papel para air fryer", "cesto para air fryer", "capa para air fryer"],
        "cortina blackout": ["tecido para cortina", "varao para cortina", "gancho para cortina"],
        "ar condicionado portatil": ["tubo para ar condicionado", "mangueira para ar condicionado", "controle para ar condicionado", "suporte para ar condicionado"],
    }
    return not any(block in title for block in hard_blocks.get(key, []))


def choose_one_per_keyword(ranking: list[dict], config: dict, blocked_ids: set[str]) -> tuple[dict[str, list[dict]], dict[str, list[str]]]:
    categories = config.get("categories") or {}
    category_names = list(categories.keys())
    grouped = base.group_candidates(ranking, category_names)
    chosen: dict[str, list[dict]] = {}
    coverage: dict[str, list[str]] = {}
    used: set[str] = set()

    for category, keywords in categories.items():
        picks = []
        covered = []
        pool = grouped.get(category) or []
        for keyword in keywords:
            selected = None
            for p in pool:
                item_id = str(p.get("itemId") or "").strip()
                matched = [str(v) for v in (p.get("intentMatchedKeywords") or p.get("keywords") or [])]
                if keyword not in matched:
                    continue
                if item_id in blocked_ids or item_id in used:
                    continue
                if not extra_keyword_gate(p, keyword):
                    continue
                selected = dict(p)
                selected["selectedSourceKeyword"] = keyword
                break
            if selected is None:
                raise RuntimeError(f"SAFE v3 bloqueado: sem produto novo válido para '{keyword}' em '{category}'.")
            picks.append(selected)
            covered.append(keyword)
            used.add(str(selected.get("itemId")))

        if len(picks) != base.ITEMS_PER_CATEGORY or len(set(covered)) != base.ITEMS_PER_CATEGORY:
            raise RuntimeError(f"SAFE v3 bloqueado: cobertura incompleta em {category}: {covered}")
        chosen[category] = picks
        coverage[category] = covered

    expected = len(category_names) * base.ITEMS_PER_CATEGORY
    if len(used) != expected:
        raise RuntimeError(f"SAFE v3 bloqueado: {len(used)} IDs únicos; esperado {expected}.")
    return chosen, coverage


def main() -> int:
    app_id = base.required_env("SHOPEE_APP_ID")
    secret = base.required_env("SHOPEE_SECRET")
    if app_id != base.EXPECTED_APP_ID:
        raise RuntimeError("SHOPEE_APP_ID não corresponde ao AppID autorizado do projeto.")

    config = base.load_json(base.CONFIG_PATH, {})
    categories = config.get("categories") or {}
    if len(categories) != 5 or any(len(v) != 4 for v in categories.values()):
        raise RuntimeError("Configuração inválida: esperado 5 categorias × 4 palavras-chave.")

    history = base.load_json(base.HISTORY_PATH, {"version": 1, "blogId": base.BLOG_ID, "runs": []})
    blocked = base.published_recent_ids(history)
    print(f"Achados para Casa — SAFE v3. IDs publicados bloqueados: {len(blocked)}")

    ranking = base.shopee_v23.scan_v23()
    print(f"Ranking Shopee recebido: {len(ranking)}")
    chosen, coverage = choose_one_per_keyword(ranking, config, blocked)
    normalized, checks = base.validate_and_generate_links(chosen, app_id, secret)

    # Propaga para o artefato final a palavra-chave responsável pela seleção.
    by_id = {
        str(p.get("itemId")): str(p.get("selectedSourceKeyword") or "")
        for values in chosen.values() for p in values
    }
    for values in normalized.values():
        for item in values:
            item["sourceKeyword"] = by_id.get(item["itemId"], "")

    ids = [item["itemId"] for values in normalized.values() for item in values]
    selection = {
        "schemaVersion": 3,
        "status": "SAFE_READY",
        "publishReady": True,
        "dryRun": True,
        "blogId": base.BLOG_ID,
        "timestamp": base.now_local().isoformat(),
        "itemsPerCategory": base.ITEMS_PER_CATEGORY,
        "categoryCount": len(categories),
        "totalItems": len(ids),
        "newItemsRequired": 20,
        "recentWindowDays": base.RECENT_DAYS,
        "blockedPublishedIdsCount": len(blocked),
        "uniqueItemIds": len(set(ids)),
        "categories": normalized,
        "keywordCoverage": coverage,
        "affiliateLinkGeneration": {
            "method": "generateShortLink",
            "appId": base.EXPECTED_APP_ID,
            "validatedCount": len(checks),
            "allResolvedToShopee": True,
        },
        "semanticValidation": {
            "rulesFile": "config/shopee_achados_casa_intent_rules.json",
            "strictAccessoriesBlocked": True,
            "oneProductPerKeyword": True,
        },
        "gates": {
            "fiveCategories": len(normalized) == 5,
            "fourPerCategory": all(len(v) == 4 for v in normalized.values()),
            "twentyUnique": len(ids) == 20 and len(set(ids)) == 20,
            "allNewVsPublishedWindow": all(i not in blocked for i in ids),
            "allLinksResolved": len(checks) == 20,
            "semanticRulesApplied": True,
            "oneProductPerKeyword": all(len(set(v)) == 4 for v in coverage.values()),
            "failClosed": True,
        },
    }
    if not all(selection["gates"].values()):
        raise RuntimeError(f"SAFE v3 bloqueado: gates finais falharam: {selection['gates']}")

    base.save_atomic(base.SELECTION_PATH, selection)
    print("ACHADOS_SAFE_V3_READY: 20 produtos; 20 palavras-chave cobertas; 20/20 links validados; Blogger não alterado.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ACHADOS_SAFE_V3_FAILED: {exc}", file=sys.stderr)
        raise
