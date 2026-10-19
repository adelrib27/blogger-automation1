#!/usr/bin/env python3
from __future__ import annotations

import base64
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "oficina_garagem" / "data"
HISTORY_PATH = DATA_DIR / "store_rotation.json"
LAST_SELECTION_PATH = DATA_DIR / "store_last_selection.json"
SCAN_DIR = DATA_DIR / "store_shopee_scan"
PAGE_ID = int(os.getenv("OFICINA_STORE_PAGE_ID", "45"))
WP_BASE = os.getenv("OFICINA_STORE_WP_BASE", "https://oficina.radartechbr.com.br").rstrip("/")
ITEMS_PER_CATEGORY = max(1, min(int(os.getenv("OFICINA_STORE_ITEMS_PER_CATEGORY", "4")), 8))
RECENT_DAYS = max(1, min(int(os.getenv("OFICINA_STORE_RECENT_DAYS", "1")), 30))
DRY_RUN = os.getenv("OFICINA_STORE_DRY_RUN", "false").strip().lower() in {"1", "true", "yes", "on"}
START_MARKER = "<!-- OFICINA_STORE_AUTO_START -->"
END_MARKER = "<!-- OFICINA_STORE_AUTO_END -->"

CATEGORY_SPECS = [
    ("Ferramentas", "Ferramentas", "ogs-ferramentas"),
    ("Manutencao", "Manutenção", "ogs-manutencao"),
    ("Acessorios Automotivos", "Acessórios automotivos", "ogs-auto"),
    ("Organizacao de Garagem", "Organização de garagem", "ogs-organizacao"),
    ("Limpeza e Conservacao", "Limpeza e conservação", "ogs-limpeza"),
    ("Seguranca e Protecao", "Segurança e proteção", "ogs-seguranca"),
]

os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(ROOT / "oficina_garagem" / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(ROOT / "oficina_garagem" / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(SCAN_DIR))
os.environ.setdefault("SHOPEE_CATEGORY", "all")
os.environ.setdefault("SHOPEE_TOP_N", "60")

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "oficina_garagem" / "src"))
import shopee_oportunidades_v23 as shopee_v23  # noqa: E402
import shopee_oportunidades_oficina as oficina_shopee  # noqa: E402

shopee_v23.run_regression_checks = oficina_shopee.regression_checks


def now_local() -> datetime:
    return datetime.now(ZoneInfo("America/Recife"))


def as_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_category(value: str) -> str:
    value = str(value or "").strip()
    aliases = {
        "Manutenção": "Manutencao",
        "Acessórios Automotivos": "Acessorios Automotivos",
        "Organização de Garagem": "Organizacao de Garagem",
        "Limpeza e Conservação": "Limpeza e Conservacao",
        "Segurança e Proteção": "Seguranca e Protecao",
    }
    return aliases.get(value, value)


def valid_product(product: dict) -> bool:
    return bool(
        str(product.get("itemId") or "").strip()
        and str(product.get("productName") or "").strip()
        and str(product.get("offerLink") or "").startswith("http")
        and str(product.get("imageUrl") or "").startswith("http")
        and as_float(product.get("priceMin")) > 0
    )


def load_history() -> dict:
    if not HISTORY_PATH.exists():
        return {"version": 1, "runs": []}
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError
    except Exception:
        return {"version": 1, "runs": []}
    data.setdefault("version", 1)
    data.setdefault("runs", [])
    return data


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


def group_candidates(ranking: list[dict]) -> dict[str, list[dict]]:
    grouped = {key: [] for key, _, _ in CATEGORY_SPECS}
    seen = {key: set() for key, _, _ in CATEGORY_SPECS}
    for product in ranking:
        if not valid_product(product):
            continue
        item_id = str(product.get("itemId"))
        categories = [normalize_category(c) for c in (product.get("categories") or [])]
        for key, _, _ in CATEGORY_SPECS:
            if key in categories and item_id not in seen[key]:
                grouped[key].append(product)
                seen[key].add(item_id)
    return grouped


def choose_products(ranking: list[dict], history: dict) -> dict[str, list[dict]]:
    grouped = group_candidates(ranking)
    recent = recent_ids(history)
    chosen: dict[str, list[dict]] = {}
    used_now: set[str] = set()
    for key, _, _ in CATEGORY_SPECS:
        pool = grouped.get(key) or []
        fresh = [p for p in pool if str(p.get("itemId")) not in recent]
        repeated = [p for p in pool if str(p.get("itemId")) in recent]
        picks = []
        for product in fresh + repeated:
            item_id = str(product.get("itemId"))
            if item_id in used_now:
                continue
            picks.append(product)
            used_now.add(item_id)
            if len(picks) == ITEMS_PER_CATEGORY:
                break
        if len(picks) != ITEMS_PER_CATEGORY:
            raise RuntimeError(f"Categoria {key} sem candidatos suficientes: {len(picks)}/{ITEMS_PER_CATEGORY}. Página preservada.")
        chosen[key] = picks
    expected = len(CATEGORY_SPECS) * ITEMS_PER_CATEGORY
    if len(used_now) != expected:
        raise RuntimeError(f"Seleção inválida: {len(used_now)} IDs únicos; esperado {expected}.")
    return chosen


def brl(value) -> str:
    raw = f"{as_float(value):,.2f}"
    return "R$ " + raw.replace(",", "X").replace(".", ",").replace("X", ".")


def price_label(product: dict) -> str:
    pmin, pmax = as_float(product.get("priceMin")), as_float(product.get("priceMax"))
    return f"A partir de {brl(pmin)}" if pmax > pmin + 0.009 else brl(pmin)


def short_name(name: str, limit: int = 76) -> str:
    value = re.sub(r"\s+", " ", str(name or "")).strip()
    if len(value) <= limit:
        return value
    cut = value[:limit].rsplit(" ", 1)[0].rstrip(" -–—,.;:")
    return (cut or value[:limit]).rstrip() + "…"


def render_product(product: dict) -> str:
    item_id = html.escape(str(product.get("itemId") or ""), quote=True)
    url = html.escape(str(product.get("offerLink") or ""), quote=True)
    image = html.escape(str(product.get("imageUrl") or ""), quote=True)
    full_name = str(product.get("productName") or "").strip()
    name = html.escape(short_name(full_name))
    alt = html.escape(short_name(full_name, 105), quote=True)
    shop = html.escape(short_name(str(product.get("shopName") or "Shopee"), 38))
    price = html.escape(price_label(product))
    return f'''<a class="ogs-product" data-item-id="{item_id}" href="{url}" target="_blank" rel="nofollow sponsored noopener">
<span class="ogs-product-img"><img src="{image}" alt="{alt}" loading="lazy" decoding="async"></span>
<span class="ogs-product-name">{name}</span><strong>{price}</strong><small>{shop}</small></a>'''


def render_store_block(chosen: dict[str, list[dict]]) -> str:
    panels = []
    for key, label, anchor in CATEGORY_SPECS:
        products = "\n".join(render_product(p) for p in chosen[key])
        panels.append(f'''<article class="ogs-panel" id="{anchor}"><div class="ogs-panel-head"><span>Seleção da categoria</span><h3>{html.escape(label)}</h3></div><div class="ogs-products">{products}</div><div class="ogs-panel-foot">Atualização automática · confirme preço e disponibilidade na Shopee</div></article>''')
    stamp = now_local().strftime("%d/%m/%Y às %H:%M")
    return f'''{START_MARKER}
<style id="oficina-store-auto-css">
.ogs-store-status{{margin:0 0 16px;padding:12px 16px;border-left:4px solid #f97316;background:#fff7ed;color:#657078;font-size:12px;line-height:1.5}}
.ogs-store-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}}
.ogs-panel{{min-width:0;border:1px solid #d9dfe2;border-radius:20px;background:#fff;padding:22px;box-shadow:0 9px 28px rgba(17,24,32,.06)}}
.ogs-panel-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:18px;padding-bottom:13px;border-bottom:1px solid #e8ecee}}
.ogs-panel-head span{{font-size:10px;font-weight:900;letter-spacing:.11em;text-transform:uppercase;color:#f97316}}
.ogs-panel-head h3{{margin:0;font-size:26px;line-height:1;font-weight:900;color:#111820;text-align:right}}
.ogs-products{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 14px}}
.ogs-product{{display:block;min-width:0;text-decoration:none;color:#162029}}
.ogs-product-img{{display:block;width:100%;aspect-ratio:1/1;border-radius:15px;overflow:hidden;background:#f3f4f3;border:1px solid #e3e7e9}}
.ogs-product-img img{{display:block;width:100%;height:100%;object-fit:contain;transition:transform .25s ease}}
.ogs-product:hover .ogs-product-img img{{transform:scale(1.025)}}
.ogs-product-name{{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.7em;margin-top:10px;font-size:13px;line-height:1.35}}
.ogs-product strong{{display:block;margin-top:6px;color:#111820;font-size:16px}}
.ogs-product small{{display:block;margin-top:3px;color:#747d82;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.ogs-panel-foot{{margin-top:17px;padding-top:12px;border-top:1px solid #e8ecee;color:#81898e;font-size:10px;line-height:1.45}}
@media(max-width:900px){{.ogs-store-grid{{grid-template-columns:1fr}}}}
@media(max-width:560px){{.ogs-panel{{padding:17px;border-radius:16px}}.ogs-panel-head{{display:block}}.ogs-panel-head h3{{margin-top:5px;text-align:left;font-size:24px}}.ogs-products{{gap:16px 10px}}.ogs-product-name{{font-size:12px}}.ogs-product strong{{font-size:14px}}}}
</style>
<p class="ogs-store-status">Vitrine atualizada em {stamp} · produtos selecionados automaticamente · preços e disponibilidade podem mudar na Shopee.</p>
<div class="ogs-store-grid">{''.join(panels)}</div>
{END_MARKER}'''


def auth_header(username: str, password: str) -> str:
    return "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()


def credentials() -> tuple[str, str]:
    username = os.getenv("OFICINA_WORDPRESS_USERNAME", "admin").strip()
    password = os.getenv("OFICINA_WORDPRESS_APP_PASSWORD", "").strip()
    if not username or not password:
        raise RuntimeError("Credenciais WordPress do Oficina & Garagem ausentes.")
    return username, password


def wp_request(method: str, path: str, username: str, password: str, payload=None) -> dict:
    headers = {"Authorization": auth_header(username, password), "Accept": "application/json", "User-Agent": "OficinaGaragem-StoreAuto/1.0"}
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{WP_BASE}{path}", data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"WordPress HTTP {exc.code}: {detail[:500]}") from exc


def locate_region(raw: str) -> tuple[int, int]:
    if raw.count(START_MARKER) != 1 or raw.count(END_MARKER) != 1:
        raise RuntimeError("Marcadores da vitrine Oficina ausentes ou duplicados; página preservada.")
    start, end = raw.find(START_MARKER), raw.find(END_MARKER)
    if start < 0 or end <= start:
        raise RuntimeError("Marcadores da vitrine Oficina inválidos; página preservada.")
    return start, end + len(END_MARKER)


def validate_wordpress_target() -> None:
    username, password = credentials()
    page = wp_request("GET", f"/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", username, password)
    raw = ((page.get("content") or {}).get("raw") or "")
    if len(raw) < 6000 or str(page.get("slug") or "") != "loja":
        raise RuntimeError("Alvo WordPress inesperado; página preservada.")
    locate_region(raw)
    print("Alvo WordPress Oficina validado em modo somente leitura.")


def update_wordpress(block: str, chosen: dict[str, list[dict]]) -> dict:
    username, password = credentials()
    page = wp_request("GET", f"/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", username, password)
    raw = ((page.get("content") or {}).get("raw") or "")
    start, end = locate_region(raw)
    updated = raw[:start] + block + raw[end:]
    if updated.count(START_MARKER) != 1 or updated.count(END_MARKER) != 1:
        raise RuntimeError("Marcadores inválidos após composição; página preservada.")
    if len(updated) < max(6000, int(len(raw) * 0.60)):
        raise RuntimeError("Proteção de integridade: conteúdo resultante ficou pequeno demais.")
    response = wp_request("POST", f"/wp-json/wp/v2/pages/{PAGE_ID}", username, password, {"content": updated})
    verify = wp_request("GET", f"/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", username, password)
    verify_raw = ((verify.get("content") or {}).get("raw") or "")
    ids = {str(p.get("itemId")) for values in chosen.values() for p in values}
    missing = [item_id for item_id in ids if f'data-item-id="{item_id}"' not in verify_raw]
    if verify_raw.count(START_MARKER) != 1 or verify_raw.count(END_MARKER) != 1 or missing:
        raise RuntimeError(f"Falha pós-publicação; IDs ausentes={missing[:5]}")
    return {"pageId": response.get("id"), "modified": response.get("modified"), "link": response.get("link"), "itemsVerified": len(ids)}


def snapshot(chosen: dict[str, list[dict]], status: str, wordpress=None) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    categories = {}
    for key, _, _ in CATEGORY_SPECS:
        categories[key] = [{"itemId": str(p.get("itemId")), "productName": str(p.get("productName") or ""), "shopName": str(p.get("shopName") or ""), "priceMin": p.get("priceMin"), "priceMax": p.get("priceMax"), "offerLink": str(p.get("offerLink") or ""), "imageUrl": str(p.get("imageUrl") or "")} for p in chosen[key]]
    data = {"version": 1, "project": "Oficina & Garagem — Loja", "status": status, "timestamp": now_local().isoformat(), "dryRun": DRY_RUN, "itemsPerCategory": ITEMS_PER_CATEGORY, "categoryCount": len(CATEGORY_SPECS), "totalItems": ITEMS_PER_CATEGORY * len(CATEGORY_SPECS), "categories": categories, "wordpress": wordpress}
    LAST_SELECTION_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def append_history(data: dict) -> None:
    history = load_history()
    items = [{"category": category, "itemId": item.get("itemId")} for category, values in data["categories"].items() for item in values]
    runs = list(history.get("runs") or [])
    runs.append({"timestamp": data["timestamp"], "items": items})
    history["runs"] = runs[-30:]
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_shape(chosen: dict[str, list[dict]], block: str) -> None:
    expected_keys = {key for key, _, _ in CATEGORY_SPECS}
    if set(chosen) != expected_keys:
        raise RuntimeError("Categorias selecionadas inválidas.")
    ids = [str(p.get("itemId")) for key, _, _ in CATEGORY_SPECS for p in chosen[key]]
    expected = ITEMS_PER_CATEGORY * len(CATEGORY_SPECS)
    if len(ids) != len(set(ids)):
        raise RuntimeError("Produto duplicado entre categorias.")
    if len(ids) != expected or block.count("data-item-id=") != expected:
        raise RuntimeError(f"Quantidade de produtos inválida: {len(ids)}/{expected}.")
    if block.count('rel="nofollow sponsored noopener"') != expected:
        raise RuntimeError("Quantidade de links patrocinados inválida.")
    if block.count(START_MARKER) != 1 or block.count(END_MARKER) != 1:
        raise RuntimeError("Marcadores do bloco automático inválidos.")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Oficina & Garagem — Loja automática v1")
    print("Modo:", "DRY-RUN" if DRY_RUN else "PUBLICAÇÃO")
    ranking = shopee_v23.scan_v23()
    print("Ranking Shopee recebido:", len(ranking))
    chosen = choose_products(ranking, load_history())
    block = render_store_block(chosen)
    validate_shape(chosen, block)
    if DRY_RUN:
        validate_wordpress_target()
        data = snapshot(chosen, "DRY_RUN_OK")
        print(f"DRY-RUN OK: {data['totalItems']} produtos únicos em {data['categoryCount']} categorias; WordPress não alterado.")
        return
    wordpress = update_wordpress(block, chosen)
    data = snapshot(chosen, "PUBLISHED", wordpress)
    append_history(data)
    print(f"PUBLICAÇÃO OK: {data['totalItems']} produtos únicos; página {wordpress.get('pageId')} verificada.")


if __name__ == "__main__":
    main()
