import argparse
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import shopee_oportunidades as base
import shopee_oportunidades_v23 as v23


BASE_DIR = Path(__file__).resolve().parent.parent
POLICY_PATH = BASE_DIR / "config" / "fase3_politica_editorial.json"
SHOPEE_CONFIG_PATH = BASE_DIR / "config" / "shopee_oportunidades.json"
WORDPRESS_HISTORY_PATH = BASE_DIR / "data" / "wordpress_historico.json"
QUEUE_PATH = BASE_DIR / "data" / "fase3" / "fila_dia.json"
CURRENT_PRODUCT_PATH = BASE_DIR / "data" / "fase3" / "produto_atual.json"


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default
    return data


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def tokens(text: str) -> set[str]:
    stop = {
        "para", "com", "sem", "kit", "novo", "nova", "original",
        "produto", "de", "da", "do", "das", "dos", "uma", "um",
        "e", "em", "a", "o", "as", "os",
    }
    return {
        token
        for token in normalize(text).split()
        if len(token) >= 3 and token not in stop
    }


def similarity(a: str, b: str) -> float:
    ta = tokens(a)
    tb = tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def now_local(policy: dict) -> datetime:
    timezone = str(policy.get("timezone") or "America/Sao_Paulo")
    return datetime.now(ZoneInfo(timezone))


def category_maps(policy: dict) -> tuple[dict[str, str], dict[str, str]]:
    source_to_display = dict(policy.get("category_map") or {})
    display_to_source = {display: source for source, display in source_to_display.items()}
    return source_to_display, display_to_source


def history_blockers(policy: dict) -> dict:
    history = load_json(WORDPRESS_HISTORY_PATH, [])
    if not isinstance(history, list):
        history = []

    exact_names = set()
    exact_links = set()
    exact_item_ids = set()

    for item in history:
        if not isinstance(item, dict):
            continue
        name = normalize(item.get("produto_principal"))
        link = str(item.get("link_afiliado") or "").strip()
        item_id = str(item.get("shopee_item_id") or item.get("itemId") or "").strip()
        if name:
            exact_names.add(name)
        if link:
            exact_links.add(link)
        if item_id:
            exact_item_ids.add(item_id)

    window = int(
        (policy.get("duplicate_control") or {}).get("recent_history_window_posts", 50)
    )
    recent = [item for item in history[: max(0, window)] if isinstance(item, dict)]

    return {
        "exact_names": exact_names,
        "exact_links": exact_links,
        "exact_item_ids": exact_item_ids,
        "recent": recent,
    }


def product_is_historically_allowed(product: dict, blockers: dict, policy: dict) -> bool:
    name = str(product.get("productName") or "").strip()
    link = str(product.get("offerLink") or "").strip()
    item_id = str(product.get("itemId") or "").strip()

    if not name or not link or not item_id:
        return False

    duplicate = policy.get("duplicate_control") or {}
    if duplicate.get("block_exact_product_already_used", True):
        if normalize(name) in blockers["exact_names"]:
            return False
    if duplicate.get("block_exact_affiliate_link_already_used", True):
        if link in blockers["exact_links"]:
            return False
    if duplicate.get("block_duplicate_item_id", True) or (
        (policy.get("daily_diversity") or {}).get("block_duplicate_item_id", True)
    ):
        if item_id in blockers["exact_item_ids"]:
            return False

    if duplicate.get("avoid_recent_similar_product_or_theme", True):
        for old in blockers["recent"]:
            old_text = " ".join(
                [
                    str(old.get("produto_principal") or ""),
                    str(old.get("palavra_chave") or ""),
                    str(old.get("titulo") or ""),
                ]
            )
            if similarity(name, old_text) >= 0.82:
                return False

    return True


def keyword_for_category(product: dict, source_category: str, shopee_config: dict) -> list[str]:
    allowed = {
        normalize(keyword): keyword
        for keyword in (shopee_config.get("categories") or {}).get(source_category, [])
    }
    found = []
    for keyword in product.get("intentMatchedKeywords") or product.get("keywords") or []:
        normalized = normalize(keyword)
        if normalized in allowed and allowed[normalized] not in found:
            found.append(allowed[normalized])
    return found


def product_categories(product: dict, source_to_display: dict[str, str]) -> set[str]:
    result = set()
    for source in product.get("categories") or []:
        display = source_to_display.get(source)
        if display:
            result.add(display)
    return result


def candidate_options(
    ranking: list[dict],
    display_category: str,
    source_category: str,
    shopee_config: dict,
    source_to_display: dict[str, str],
    blockers: dict,
    policy: dict,
) -> list[tuple[dict, str]]:
    product_rules = policy.get("product_rules") or {}
    min_rating = float(product_rules.get("min_rating_when_available", 4.0))
    min_extra = float(product_rules.get("min_extra_commission_rate", 0.03))
    allow_no_rating = bool(product_rules.get("allow_products_without_rating", True))
    allow_reserve = bool(product_rules.get("standard_commission_only_as_reserve", True))

    options = []
    for product in ranking:
        if display_category not in product_categories(product, source_to_display):
            continue
        if not product_is_historically_allowed(product, blockers, policy):
            continue

        rating = base.to_float(product.get("ratingStar"))
        if rating <= 0 and not allow_no_rating:
            continue
        if rating > 0 and rating < min_rating:
            continue

        tier = str(product.get("priorityTier") or "")
        seller_rate = base.to_float(product.get("sellerCommissionRate"))
        if tier == "COMISSAO_EXTRA" and seller_rate < min_extra:
            continue
        if tier != "COMISSAO_EXTRA" and not allow_reserve:
            continue

        for keyword in keyword_for_category(product, source_category, shopee_config):
            options.append((product, keyword))

    options.sort(
        key=lambda pair: (
            1 if pair[0].get("priorityTier") == "COMISSAO_EXTRA" else 0,
            base.to_float(pair[0].get("opportunityScore")),
            base.to_int(pair[0].get("sales")),
        ),
        reverse=True,
    )
    return options


def choose_daily_products(
    categories_in_slot_order: list[str],
    ranking: list[dict],
    policy: dict,
    shopee_config: dict,
) -> list[dict]:
    source_to_display, display_to_source = category_maps(policy)
    blockers = history_blockers(policy)

    pools = {}
    for display_category in categories_in_slot_order:
        source_category = display_to_source.get(display_category)
        if not source_category:
            raise RuntimeError(f"Categoria sem mapeamento Shopee: {display_category}")
        pools[display_category] = candidate_options(
            ranking,
            display_category,
            source_category,
            shopee_config,
            source_to_display,
            blockers,
            policy,
        )
        print(
            f"Fila Fase 3 — {display_category}: "
            f"{len(pools[display_category])} opções qualificadas no ranking."
        )

    chosen = []
    used_shops = set()
    used_keywords = set()
    used_items = set()

    def backtrack(index: int) -> bool:
        if index >= len(categories_in_slot_order):
            return True

        category = categories_in_slot_order[index]
        source_category = display_to_source[category]

        for product, keyword in pools[category]:
            shop_id = str(product.get("shopId") or product.get("shopName") or "").strip()
            item_id = str(product.get("itemId") or "").strip()
            keyword_key = normalize(keyword)

            if not shop_id or not item_id or not keyword_key:
                continue
            if shop_id in used_shops:
                continue
            if keyword_key in used_keywords:
                continue
            if item_id in used_items:
                continue

            used_shops.add(shop_id)
            used_keywords.add(keyword_key)
            used_items.add(item_id)
            chosen.append(
                {
                    "category": category,
                    "sourceCategory": source_category,
                    "keyword": keyword,
                    "product": product,
                }
            )

            if backtrack(index + 1):
                return True

            chosen.pop()
            used_shops.remove(shop_id)
            used_keywords.remove(keyword_key)
            used_items.remove(item_id)

        return False

    if not backtrack(0):
        details = {
            category: len(pools[category])
            for category in categories_in_slot_order
        }
        raise RuntimeError(
            "Não foi possível montar uma fila completa respeitando 1 loja/dia, "
            f"1 keyword/dia e 1 post por categoria. Opções: {details}"
        )

    return chosen


def compact_product(product: dict) -> dict:
    fields = [
        "itemId",
        "productName",
        "offerLink",
        "productLink",
        "imageUrl",
        "shopId",
        "shopName",
        "ratingStar",
        "sales",
        "priceMin",
        "priceMax",
        "sellerCommissionRate",
        "shopeeCommissionRate",
        "commissionRate",
        "sellerExtraCommissionPct",
        "shopeeCommissionPct",
        "totalCommissionPct",
        "opportunityScore",
        "priorityTier",
        "semanticIntentScore",
        "selectionPass",
    ]
    return {field: product.get(field) for field in fields}


def build_queue() -> dict:
    policy = load_json(POLICY_PATH, {})
    shopee_config = load_json(SHOPEE_CONFIG_PATH, {})
    if not policy or not shopee_config:
        raise RuntimeError("Configuração da Fase 3 ou da Shopee não encontrada.")

    categories = list(policy.get("allowed_categories") or [])
    slots = list(policy.get("publication_slots") or [])
    if len(categories) != 5 or len(slots) != 5:
        raise RuntimeError("A Fase 3 exige exatamente 5 categorias e 5 horários aprovados.")

    local_now = now_local(policy)
    rotation = local_now.date().toordinal() % len(categories)
    categories_in_slot_order = categories[rotation:] + categories[:rotation]

    print("=== RADAR TECH BR — FASE 3 / FILA DIÁRIA ===")
    print("Data local:", local_now.date().isoformat())
    print("Rotação de categorias:", " -> ".join(categories_in_slot_order))

    ranking = v23.scan_v23()
    if not ranking:
        raise RuntimeError("Ranking Shopee vazio; nenhuma fila será criada.")

    chosen = choose_daily_products(
        categories_in_slot_order,
        ranking,
        policy,
        shopee_config,
    )

    queue_slots = []
    for slot_time, selection in zip(slots, chosen):
        queue_slots.append(
            {
                "time": slot_time,
                "category": selection["category"],
                "sourceCategory": selection["sourceCategory"],
                "keyword": selection["keyword"],
                "status": "AGENDADO",
                "product": compact_product(selection["product"]),
            }
        )

    queue = {
        "version": 1,
        "project": "Radar Tech BR",
        "policyVersion": policy.get("version"),
        "date": local_now.date().isoformat(),
        "timezone": policy.get("timezone"),
        "generatedAt": local_now.isoformat(),
        "complete": len(queue_slots) == 5,
        "rotationIndex": rotation,
        "rules": {
            "minimumOnePerCategory": True,
            "maxOneShopPerDay": True,
            "maxOneKeywordPerDay": True,
            "minRatingWhenAvailable": 4.0,
            "minExtraCommissionRate": 0.03,
            "standardCommissionOnlyAsReserve": True,
        },
        "slots": queue_slots,
    }

    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(
        json.dumps(queue, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Fila completa criada:", QUEUE_PATH)
    for slot in queue_slots:
        product = slot["product"]
        print(
            f"{slot['time']} | {slot['category']} | {slot['keyword']} | "
            f"{product.get('productName')} | loja={product.get('shopName')}"
        )

    return queue


def select_slot(slot_time: str) -> dict:
    policy = load_json(POLICY_PATH, {})
    queue = load_json(QUEUE_PATH, {})
    if not queue:
        raise RuntimeError("Fila diária da Fase 3 ainda não existe.")

    local_now = now_local(policy)
    today = local_now.date().isoformat()
    if queue.get("date") != today:
        raise RuntimeError(
            f"Fila desatualizada: fila={queue.get('date')} hoje={today}. Nada será publicado."
        )
    if queue.get("complete") is not True:
        raise RuntimeError("Fila diária incompleta. Nada será publicado.")

    for slot in queue.get("slots") or []:
        if str(slot.get("time")) != str(slot_time):
            continue
        if slot.get("status") == "PUBLICADO":
            raise RuntimeError(f"Horário {slot_time} já foi publicado hoje.")

        payload = {
            "date": queue.get("date"),
            "time": slot.get("time"),
            "category": slot.get("category"),
            "sourceCategory": slot.get("sourceCategory"),
            "keyword": slot.get("keyword"),
            "product": slot.get("product") or {},
        }
        CURRENT_PRODUCT_PATH.parent.mkdir(parents=True, exist_ok=True)
        CURRENT_PRODUCT_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("Produto da Fase 3 selecionado para", slot_time)
        print(payload["category"], "|", payload["product"].get("productName"))
        return payload

    raise RuntimeError(f"Horário não encontrado na fila: {slot_time}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    select = sub.add_parser("select-slot")
    select.add_argument("--slot", required=True)
    args = parser.parse_args()

    if args.command == "build":
        build_queue()
    elif args.command == "select-slot":
        select_slot(args.slot)


if __name__ == "__main__":
    main()
