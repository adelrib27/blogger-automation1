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
DATA_DIR = ROOT / "radar_tech_br" / "data"
HISTORY_PATH = DATA_DIR / "store_rotation.json"
LAST_SELECTION_PATH = DATA_DIR / "store_last_selection.json"
SCAN_DIR = DATA_DIR / "store_shopee_scan"
PAGE_ID = int(os.getenv("RADAR_STORE_PAGE_ID", "213"))
WP_BASE = os.getenv("RADAR_STORE_WP_BASE", "https://radartechbr.com.br").rstrip("/")
ITEMS_PER_CATEGORY = max(1, min(int(os.getenv("RADAR_STORE_ITEMS_PER_CATEGORY", "4")), 8))
RECENT_DAYS = max(1, min(int(os.getenv("RADAR_STORE_RECENT_DAYS", "1")), 30))
DRY_RUN = os.getenv("RADAR_STORE_DRY_RUN", "false").strip().lower() in {"1", "true", "yes", "on"}
START_MARKER = "<!-- RADAR_STORE_AUTO_START -->"
END_MARKER = "<!-- RADAR_STORE_AUTO_END -->"
CATEGORY_SPECS = [
    ("Tecnologia", "Tecnologia", "rtm-tecnologia"),
    ("Casa & Decoracao", "Casa & decoração", "rtm-casa"),
    ("Cozinha & Utilidades", "Cozinha & utilidades", "rtm-cozinha"),
    ("Ferramentas & Auto", "Ferramentas & auto", "rtm-ferramentas"),
    ("Moda & Beleza", "Moda & beleza", "rtm-moda"),
]

os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(ROOT / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(ROOT / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(SCAN_DIR))
os.environ.setdefault("SHOPEE_CATEGORY", "all")
os.environ.setdefault("SHOPEE_TOP_N", "40")
sys.path.insert(0, str(ROOT / "src"))
import shopee_oportunidades_v23 as shopee_v23  # noqa: E402


def now_sp() -> datetime:
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def as_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_category(value: str) -> str:
    value = str(value or "")
    return value.replace("Decoração", "Decoracao").replace("Automotivo", "Auto").strip()


def valid_product(p: dict) -> bool:
    return bool(
        str(p.get("itemId") or "").strip()
        and str(p.get("productName") or "").strip()
        and str(p.get("offerLink") or "").startswith("http")
        and str(p.get("imageUrl") or "").startswith("http")
        and as_float(p.get("priceMin")) > 0
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
    cutoff = now_sp() - timedelta(days=RECENT_DAYS)
    result: set[str] = set()
    for run in history.get("runs") or []:
        try:
            dt = datetime.fromisoformat(str(run.get("timestamp") or ""))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
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
    aliases = {"Casa & Decoração": "Casa & Decoracao", "Ferramentas & Automotivo": "Ferramentas & Auto"}
    for p in ranking:
        if not valid_product(p):
            continue
        item_id = str(p.get("itemId"))
        categories = [aliases.get(normalize_category(c), normalize_category(c)) for c in (p.get("categories") or [])]
        for key, _, _ in CATEGORY_SPECS:
            if key in categories and item_id not in seen[key]:
                grouped[key].append(p)
                seen[key].add(item_id)
    return grouped


def choose_products(ranking: list[dict], history: dict) -> dict[str, list[dict]]:
    grouped = group_candidates(ranking)
    recent = recent_ids(history)
    chosen: dict[str, list[dict]] = {}
    used_today: set[str] = set()
    for key, _, _ in CATEGORY_SPECS:
        pool = grouped.get(key) or []
        ordered = [p for p in pool if str(p.get("itemId")) not in recent] + [p for p in pool if str(p.get("itemId")) in recent]
        picks = []
        for p in ordered:
            item_id = str(p.get("itemId"))
            if item_id in used_today:
                continue
            picks.append(p)
            used_today.add(item_id)
            if len(picks) == ITEMS_PER_CATEGORY:
                break
        if len(picks) != ITEMS_PER_CATEGORY:
            raise RuntimeError(f"Categoria {key} sem candidatos suficientes: {len(picks)}/{ITEMS_PER_CATEGORY}. Página preservada.")
        chosen[key] = picks
    expected = len(CATEGORY_SPECS) * ITEMS_PER_CATEGORY
    if len(used_today) != expected:
        raise RuntimeError(f"Seleção inválida: {len(used_today)} IDs únicos; esperado {expected}.")
    return chosen


def brl(value) -> str:
    raw = f"{as_float(value):,.2f}"
    return "R$ " + raw.replace(",", "X").replace(".", ",").replace("X", ".")


def price_label(p: dict) -> str:
    pmin, pmax = as_float(p.get("priceMin")), as_float(p.get("priceMax"))
    return f"A partir de {brl(pmin)}" if pmax > pmin + 0.009 else brl(pmin)


def short_name(name: str, limit=72) -> str:
    value = re.sub(r"\s+", " ", str(name or "")).strip()
    if len(value) <= limit:
        return value
    cut = value[:limit].rsplit(" ", 1)[0].rstrip(" -–—,.;:")
    return (cut or value[:limit]).rstrip() + "…"


def render_product(p: dict) -> str:
    item_id = html.escape(str(p.get("itemId") or ""), quote=True)
    url = html.escape(str(p.get("offerLink") or ""), quote=True)
    image = html.escape(str(p.get("imageUrl") or ""), quote=True)
    full_name = str(p.get("productName") or "").strip()
    name = html.escape(short_name(full_name))
    alt = html.escape(short_name(full_name, 100), quote=True)
    shop = html.escape(short_name(str(p.get("shopName") or ""), 34))
    price = html.escape(price_label(p))
    return f'''<a class="rtm-product rtm-product-auto" data-item-id="{item_id}" href="{url}" target="_blank" rel="nofollow sponsored noopener">
  <img src="{image}" alt="{alt}" loading="lazy" decoding="async">
  <span class="rtm-product-name">{name}</span>
  <strong>{price}</strong>
  <small class="rtm-product-shop">{shop}</small>
</a>'''


def render_store_block(chosen: dict[str, list[dict]]) -> str:
    panels = []
    for key, label, anchor in CATEGORY_SPECS:
        products = "\n".join(render_product(p) for p in chosen[key])
        panels.append(f'''<div class="rtm-panel rtm-panel-auto" id="{anchor}">
  <div class="rtm-panel-top"><h3>{html.escape(label)}</h3></div>
  <div class="rtm-products">{products}</div>
  <span class="rtm-auto-note">Seleção atualizada automaticamente</span>
</div>''')
    stamp = now_sp().strftime("%d/%m/%Y às %H:%M")
    return f'''{START_MARKER}
<style id="rtm-store-auto-css">
.rtm-showcase-auto{{background:#fff;padding:26px 0 40px}}
.rtm-showcase-auto .rtm-container{{width:min(1440px,calc(100% - 32px));margin:0 auto}}
.rtm-store-grid{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px}}
.rtm-panel-auto{{min-width:0}}
.rtm-product-auto{{display:block}}
.rtm-product-name{{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.65em;margin-top:8px;font-size:13px;line-height:1.32;color:#111827}}
.rtm-product-auto strong{{font-size:15px;margin-top:6px}}
.rtm-product-shop{{display:block;margin-top:3px;color:#6b7280;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.rtm-auto-note{{display:block;margin-top:14px;color:#6b7280;font-size:11px}}
.rtm-store-updated{{margin:0 0 12px;color:#6b7280;font-size:12px}}
@media(max-width:1280px){{.rtm-store-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}}}
@media(max-width:860px){{.rtm-store-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:640px){{.rtm-store-grid{{grid-template-columns:1fr}}}}
</style>
<section class="rtm-showcase rtm-showcase-auto" id="rtm-destaques">
  <div class="rtm-container">
    <p class="rtm-store-updated">Vitrine atualizada em {stamp} · preços e disponibilidade podem mudar na Shopee.</p>
    <div class="rtm-store-grid">{''.join(panels)}</div>
  </div>
</section>
{END_MARKER}'''


def auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


def wp_request(method: str, path: str, username: str, password: str, payload=None) -> dict:
    headers = {"Authorization": auth_header(username, password), "Accept": "application/json", "User-Agent": "RadarTechBR-StoreAuto/1.0"}
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{WP_BASE}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"WordPress HTTP {exc.code}: {body[:500]}") from exc


def wp_credentials() -> tuple[str, str]:
    user = os.getenv("WORDPRESS_USERNAME", "").strip()
    password = os.getenv("WORDPRESS_APP_PASSWORD", "").strip()
    if not user or not password:
        raise RuntimeError("Credenciais WordPress ausentes.")
    return user, password


def locate_region(raw: str) -> tuple[int, int]:
    start, end = raw.find(START_MARKER), raw.find(END_MARKER)
    if start >= 0 and end > start:
        return start, end + len(END_MARKER)
    match = re.search(r'<section class="rtm-showcase" id="rtm-destaques">.*?</section>', raw, flags=re.S)
    if match:
        return match.start(), match.end()
    raise RuntimeError("Região da vitrine não encontrada; nenhuma alteração será feita.")


def validate_wordpress_target() -> None:
    user, password = wp_credentials()
    page = wp_request("GET", f"/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", user, password)
    raw = ((page.get("content") or {}).get("raw") or "")
    if len(raw) < 6000:
        raise RuntimeError("Página da loja retornou conteúdo inesperadamente pequeno.")
    locate_region(raw)
    print("Alvo WordPress validado em modo somente leitura.")


def update_wordpress(block: str, chosen: dict[str, list[dict]]) -> dict:
    user, password = wp_credentials()
    page = wp_request("GET", f"/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", user, password)
    raw = ((page.get("content") or {}).get("raw") or "")
    start, end = locate_region(raw)
    updated = raw[:start] + block + raw[end:]
    if updated.count(START_MARKER) != 1 or updated.count(END_MARKER) != 1:
        raise RuntimeError("Marcadores inválidos após composição.")
    if len(updated) < max(6000, int(len(raw) * 0.55)):
        raise RuntimeError("Proteção de integridade: conteúdo resultante ficou pequeno demais.")
    response = wp_request("POST", f"/wp-json/wp/v2/pages/{PAGE_ID}", user, password, {"content": updated})
    verify = wp_request("GET", f"/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", user, password)
    verify_raw = ((verify.get("content") or {}).get("raw") or "")
    ids = {str(p.get("itemId")) for values in chosen.values() for p in values}
    missing = [i for i in ids if f'data-item-id="{i}"' not in verify_raw]
    if START_MARKER not in verify_raw or END_MARKER not in verify_raw or missing:
        raise RuntimeError(f"Falha pós-publicação; IDs ausentes={missing[:5]}")
    return {"pageId": response.get("id"), "modified": response.get("modified"), "link": response.get("link"), "itemsVerified": len(ids)}


def snapshot(chosen: dict[str, list[dict]], status: str, wp=None) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    categories = {}
    for key, _, _ in CATEGORY_SPECS:
        categories[key] = [{
            "itemId": str(p.get("itemId")), "productName": str(p.get("productName") or ""),
            "shopName": str(p.get("shopName") or ""), "priceMin": p.get("priceMin"), "priceMax": p.get("priceMax"),
            "offerLink": str(p.get("offerLink") or ""), "imageUrl": str(p.get("imageUrl") or "")
        } for p in chosen[key]]
    data = {"version": 1, "status": status, "timestamp": now_sp().isoformat(), "dryRun": DRY_RUN,
            "itemsPerCategory": ITEMS_PER_CATEGORY, "categoryCount": len(CATEGORY_SPECS),
            "totalItems": ITEMS_PER_CATEGORY * len(CATEGORY_SPECS), "categories": categories, "wordpress": wp}
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
    if len(ids) != len(set(ids)):
        raise RuntimeError("Produto duplicado entre categorias.")
    expected = ITEMS_PER_CATEGORY * len(CATEGORY_SPECS)
    if len(ids) != expected or block.count('rel="nofollow sponsored noopener"') != expected or block.count("data-item-id=") != expected:
        raise RuntimeError("Quantidade de cards/links não corresponde à seleção.")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Radar Tech BR — Loja automática v1")
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
    wp = update_wordpress(block, chosen)
    data = snapshot(chosen, "PUBLISHED", wp)
    append_history(data)
    print(f"PUBLICAÇÃO OK: {data['totalItems']} produtos únicos; página {wp.get('pageId')} verificada.")


if __name__ == "__main__":
    main()
