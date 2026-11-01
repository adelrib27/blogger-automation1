#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "blogger_stores" / "data"
SCAN_DIR = DATA_DIR / "achados_casa_scan"
HISTORY_PATH = DATA_DIR / "achados_casa_rotation.json"
SELECTION_PATH = DATA_DIR / "achados_casa_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_achados_casa.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "1426630233929943394"
ITEMS_PER_CATEGORY = 4
RECENT_DAYS = max(1, min(int(os.getenv("ACHADOS_STORE_RECENT_DAYS", "14")), 90))

os.environ["SHOPEE_OPPORTUNITIES_CONFIG"] = str(CONFIG_PATH)
os.environ["SHOPEE_INTENT_RULES"] = str(INTENT_RULES_PATH)
os.environ["SHOPEE_OUTPUT_DIR"] = str(SCAN_DIR)
os.environ["SHOPEE_CATEGORY"] = "all"
os.environ.setdefault("SHOPEE_TOP_N", "100")

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "radar_tech_br" / "src"))

import shopee_oportunidades_v23 as shopee_v23  # noqa: E402
from refresh_blogger_offer_links import generate_short_link, resolved_to_shopee  # noqa: E402


def now_local() -> datetime:
    return datetime.now(ZoneInfo("America/Recife"))


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def as_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def recent_ids(history: dict) -> set[str]:
    cutoff = now_local() - timedelta(days=RECENT_DAYS)
    result: set[str] = set()
    for run in history.get("runs") or []:
        try:
            dt = datetime.fromisoformat(str(run.get("timestamp") or ""))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("America/Recife"))
        except Exception:
            continue
        if dt < cutoff:
            continue
        for item in run.get("items") or []:
            item_id = str(item.get("itemId") or "").strip()
            if item_id:
                result.add(item_id)
    return result


def valid_candidate(p: dict) -> bool:
    return bool(
        str(p.get("itemId") or "").strip()
        and str(p.get("productName") or "").strip()
        and str(p.get("shopName") or "").strip()
        and str(p.get("imageUrl") or "").startswith("http")
        and str(p.get("productLink") or "").startswith("http")
        and as_float(p.get("priceMin")) > 0
    )


def group_candidates(ranking: list[dict], category_names: list[str]) -> dict[str, list[dict]]:
    grouped = {name: [] for name in category_names}
    seen_by_category = {name: set() for name in category_names}
    for p in ranking:
        if not valid_candidate(p):
            continue
        item_id = str(p.get("itemId") or "").strip()
        categories = [str(c or "").strip() for c in (p.get("categories") or [])]
        for category in categories:
            if category in grouped and item_id not in seen_by_category[category]:
                grouped[category].append(p)
                seen_by_category[category].add(item_id)
    return grouped


def choose_new_products(ranking: list[dict], category_names: list[str], blocked_ids: set[str]) -> dict[str, list[dict]]:
    grouped = group_candidates(ranking, category_names)
    chosen: dict[str, list[dict]] = {}
    used: set[str] = set()
    for category in category_names:
        fresh_pool = [p for p in grouped.get(category, []) if str(p.get("itemId")) not in blocked_ids]
        picks = []
        for p in fresh_pool:
            item_id = str(p.get("itemId") or "").strip()
            if not item_id or item_id in used:
                continue
            picks.append(p)
            used.add(item_id)
            if len(picks) == ITEMS_PER_CATEGORY:
                break
        if len(picks) != ITEMS_PER_CATEGORY:
            raise RuntimeError(
                f"SAFE bloqueado: categoria {category} tem apenas {len(picks)}/{ITEMS_PER_CATEGORY} produtos novos válidos."
            )
        chosen[category] = picks
    expected = len(category_names) * ITEMS_PER_CATEGORY
    if len(used) != expected:
        raise RuntimeError(f"SAFE bloqueado: {len(used)} IDs únicos; esperado {expected}.")
    return chosen


def validate_and_generate_links(chosen: dict[str, list[dict]], app_id: str, secret: str) -> tuple[dict, dict]:
    normalized: dict[str, list[dict]] = {}
    link_checks: dict[str, dict] = {}
    all_ids: set[str] = set()
    index = 0

    for category, products in chosen.items():
        normalized[category] = []
        for p in products:
            index += 1
            item_id = str(p.get("itemId") or "").strip()
            if item_id in all_ids:
                raise RuntimeError(f"SAFE bloqueado: item duplicado {item_id}.")
            all_ids.add(item_id)

            origin = str(p.get("productLink") or "").strip()
            short = generate_short_link(app_id, secret, origin)
            ok, final_url, http_status = resolved_to_shopee(short)
            if not ok:
                raise RuntimeError(
                    f"SAFE bloqueado: link não resolveu para Shopee. item={item_id} short={short} final={final_url} status={http_status}"
                )

            normalized[category].append({
                "itemId": item_id,
                "productName": str(p.get("productName") or "").strip(),
                "shopName": str(p.get("shopName") or "").strip(),
                "priceMin": p.get("priceMin"),
                "priceMax": p.get("priceMax"),
                "imageUrl": str(p.get("imageUrl") or "").strip(),
                "productLink": origin,
                "affiliateUrl": short,
                "offerLink": short,
                "category": category,
                "source": "shopee_affiliate_open_api",
                "discoveredAt": now_local().isoformat(),
            })
            link_checks[item_id] = {
                "shortLink": short,
                "resolvedUrl": final_url,
                "httpStatus": http_status,
            }
            print(f"[{index:02d}/20] {category} — item {item_id}: link afiliado validado.")
            time.sleep(0.15)

    if len(all_ids) != 20 or len(link_checks) != 20:
        raise RuntimeError(f"SAFE bloqueado: validação incompleta {len(link_checks)}/20.")
    return normalized, link_checks


def save_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def append_scan_history(selection: dict) -> None:
    history = load_json(HISTORY_PATH, {"version": 1, "blogId": BLOG_ID, "runs": []})
    runs = list(history.get("runs") or [])
    runs.append({
        "timestamp": selection["timestamp"],
        "source": "safe_scan_ready",
        "items": [
            {"category": category, "itemId": item["itemId"]}
            for category, values in selection["categories"].items()
            for item in values
        ],
    })
    history["runs"] = runs[-60:]
    save_atomic(HISTORY_PATH, history)


def main() -> int:
    app_id = required_env("SHOPEE_APP_ID")
    secret = required_env("SHOPEE_SECRET")
    if app_id != EXPECTED_APP_ID:
        raise RuntimeError("SHOPEE_APP_ID não corresponde ao AppID autorizado do projeto.")

    config = load_json(CONFIG_PATH, {})
    category_names = list((config.get("categories") or {}).keys())
    if len(category_names) != 5:
        raise RuntimeError(f"Configuração inválida: esperado 5 categorias, recebido {len(category_names)}.")

    history = load_json(HISTORY_PATH, {"version": 1, "blogId": BLOG_ID, "runs": []})
    blocked = recent_ids(history)
    print(f"Achados para Casa — SAFE Shopee. IDs bloqueados pela rotação: {len(blocked)}")

    ranking = shopee_v23.scan_v23()
    print(f"Ranking Shopee recebido: {len(ranking)}")
    chosen = choose_new_products(ranking, category_names, blocked)
    normalized, link_checks = validate_and_generate_links(chosen, app_id, secret)

    ids = [item["itemId"] for values in normalized.values() for item in values]
    selection = {
        "schemaVersion": 1,
        "status": "SAFE_READY",
        "publishReady": True,
        "dryRun": True,
        "blogId": BLOG_ID,
        "timestamp": now_local().isoformat(),
        "itemsPerCategory": ITEMS_PER_CATEGORY,
        "categoryCount": len(category_names),
        "totalItems": len(ids),
        "newItemsRequired": 20,
        "recentWindowDays": RECENT_DAYS,
        "blockedRecentIdsCount": len(blocked),
        "uniqueItemIds": len(set(ids)),
        "categories": normalized,
        "affiliateLinkGeneration": {
            "method": "generateShortLink",
            "appId": EXPECTED_APP_ID,
            "validatedCount": len(link_checks),
            "allResolvedToShopee": True,
        },
        "gates": {
            "fiveCategories": len(normalized) == 5,
            "fourPerCategory": all(len(v) == 4 for v in normalized.values()),
            "twentyUnique": len(ids) == 20 and len(set(ids)) == 20,
            "allNewVsRecentWindow": all(i not in blocked for i in ids),
            "allLinksResolved": len(link_checks) == 20,
            "failClosed": True,
        },
    }

    if not all(selection["gates"].values()):
        raise RuntimeError(f"SAFE bloqueado: gates finais falharam: {selection['gates']}")

    save_atomic(SELECTION_PATH, selection)
    append_scan_history(selection)
    print("ACHADOS_SAFE_READY: 20 produtos novos, 5 categorias, 20/20 links afiliados validados; nenhuma página Blogger foi alterada.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ACHADOS_SAFE_FAILED: {exc}", file=sys.stderr)
        raise
