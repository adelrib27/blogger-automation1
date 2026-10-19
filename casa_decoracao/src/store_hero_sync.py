#!/usr/bin/env python3
from __future__ import annotations

import base64
import html
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SELECTION_PATH = ROOT / "casa_decoracao" / "data" / "store_last_selection.json"
PAGE_ID = int(os.getenv("CASA_STORE_PAGE_ID", "136"))
WP_BASE = os.getenv("CASA_STORE_WP_BASE", "https://casaedecoracao.radartechbr.com.br").rstrip("/")
DRY_RUN = os.getenv("CASA_STORE_DRY_RUN", "false").strip().lower() in {"1", "true", "yes", "on"}

HERO_PLAN = [
    ("Casa com intenção", [("Decoracao", 0, "Decoração"), ("Organizacao", 0, "Organização"), ("Cozinha", 0, "Cozinha"), ("Cama Mesa Banho", 0, "Cama & banho")]),
    ("Conforto em camadas", [("Sala", 0, "Sala"), ("Quarto", 0, "Quarto"), ("Decoracao", 1, "Decoração"), ("Organizacao", 1, "Organização")]),
    ("Escolha com contexto", [("Banheiro", 0, "Banheiro"), ("Area Externa", 0, "Área externa"), ("Cozinha", 1, "Cozinha"), ("Cama Mesa Banho", 1, "Cama & banho")]),
]


def marker_start(index: int) -> str:
    return f"<!-- CASA_HERO_AUTO_{index}_START -->"


def marker_end(index: int) -> str:
    return f"<!-- CASA_HERO_AUTO_{index}_END -->"


def brl(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    raw = f"{number:,.2f}"
    return "R$ " + raw.replace(",", "X").replace(".", ",").replace("X", ".")


def price_label(product: dict) -> str:
    try:
        pmin = float(product.get("priceMin") or 0)
        pmax = float(product.get("priceMax") or 0)
    except (TypeError, ValueError):
        pmin = pmax = 0.0
    return f"A partir de {brl(pmin)}" if pmax > pmin + 0.009 else brl(pmin)


def load_selection() -> dict:
    if not SELECTION_PATH.exists():
        raise RuntimeError("Snapshot da loja não encontrado.")
    data = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    categories = data.get("categories") or {}
    for category, _, _ in [spec for _, specs in HERO_PLAN for spec in specs]:
        if len(categories.get(category) or []) < 2:
            raise RuntimeError(f"Snapshot sem produtos suficientes em {category}.")
    return data


def product_tile(product: dict, label: str) -> str:
    item_id = html.escape(str(product.get("itemId") or ""), quote=True)
    image = html.escape(str(product.get("imageUrl") or ""), quote=True)
    url = html.escape(str(product.get("offerLink") or ""), quote=True)
    name = html.escape(str(product.get("productName") or label), quote=True)
    price = html.escape(price_label(product))
    label_html = html.escape(label)
    if not item_id or not image.startswith("http") or not url.startswith("http"):
        raise RuntimeError(f"Produto inválido para mini-card: {item_id or 'sem itemId'}")
    return f'''<a class="cds-hero-product" data-hero-item-id="{item_id}" href="{url}" target="_blank" rel="nofollow sponsored noopener" title="{name}">
  <span class="cds-hero-product-img"><img src="{image}" alt="{name}" loading="lazy" decoding="async"></span>
  <span class="cds-hero-product-meta"><b>{label_html}</b><small>{price}</small></span>
</a>'''


def render_hero(index: int, title: str, specs: list[tuple[str, int, str]], categories: dict) -> str:
    tiles = "\n".join(product_tile(categories[category][position], label) for category, position, label in specs)
    css = ""
    if index == 1:
        css = '''<style id="casa-hero-auto-css">
.cds-room-card.cds-room-card-products{width:min(500px,96%);padding:24px}
.cds-room-card-products>strong{margin-bottom:12px;font-size:29px}
.cds-hero-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px}
.cds-hero-product{display:block;min-width:0;overflow:hidden;border:1px solid #dedfd8;border-radius:17px;background:#fff;text-decoration:none;color:#173e37;box-shadow:0 5px 14px rgba(23,62,55,.05);transition:transform .2s ease,box-shadow .2s ease}
.cds-hero-product:hover{transform:translateY(-2px);box-shadow:0 9px 20px rgba(23,62,55,.10)}
.cds-hero-product-img{display:block;width:100%;height:112px;background:#f7f7f1;overflow:hidden}
.cds-hero-product-img img{display:block;width:100%;height:100%;object-fit:contain}
.cds-hero-product-meta{display:flex;align-items:center;justify-content:space-between;gap:6px;padding:8px 9px;min-height:35px}
.cds-hero-product-meta b{min-width:0;font:800 10px/1.15 Arial,sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cds-hero-product-meta small{flex:none;font:700 9px/1.1 Arial,sans-serif;color:#e46f63;white-space:nowrap}
@media(max-width:620px){.cds-room-card.cds-room-card-products{padding:16px}.cds-room-card-products>strong{font-size:25px}.cds-hero-product-img{height:96px}.cds-hero-product-meta{display:block}.cds-hero-product-meta small{display:block;margin-top:3px}}
</style>'''
    return f'''{marker_start(index)}{css}<div class="cds-room-card cds-room-card-products"><strong>{html.escape(title)}</strong><div class="cds-hero-grid">{tiles}</div></div>{marker_end(index)}'''


def auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


def credentials() -> tuple[str, str]:
    username = os.getenv("CASA_WORDPRESS_USERNAME", "").strip()
    password = os.getenv("CASA_WORDPRESS_APP_PASSWORD", "").strip()
    if not username or not password:
        raise RuntimeError("Credenciais WordPress do Casa e Decoração ausentes.")
    return username, password


def wp_request(method: str, path: str, username: str, password: str, payload=None) -> dict:
    headers = {"Authorization": auth_header(username, password), "Accept": "application/json", "User-Agent": "CasaDecoracao-HeroSync/1.0"}
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{WP_BASE}{path}", data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"WordPress HTTP {exc.code}: {detail[:500]}") from exc


def replace_marked(raw: str, index: int, replacement: str) -> str:
    start_marker, end_marker = marker_start(index), marker_end(index)
    if raw.count(start_marker) != 1 or raw.count(end_marker) != 1:
        raise RuntimeError(f"Marcadores do carrossel {index} ausentes ou duplicados; página preservada.")
    start = raw.find(start_marker)
    end = raw.find(end_marker, start)
    if end <= start:
        raise RuntimeError(f"Marcadores do carrossel {index} inválidos; página preservada.")
    return raw[:start] + replacement + raw[end + len(end_marker):]


def main() -> None:
    data = load_selection()
    categories = data["categories"]
    username, password = credentials()
    page = wp_request("GET", f"/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", username, password)
    raw = ((page.get("content") or {}).get("raw") or "")
    if len(raw) < 7000 or str(page.get("slug") or "") != "loja":
        raise RuntimeError("Alvo WordPress inesperado; página preservada.")

    updated = raw
    hero_ids: list[str] = []
    for index, (title, specs) in enumerate(HERO_PLAN, start=1):
        replacement = render_hero(index, title, specs, categories)
        updated = replace_marked(updated, index, replacement)
        for category, position, _ in specs:
            hero_ids.append(str(categories[category][position].get("itemId")))

    if len(hero_ids) != 12 or len(set(hero_ids)) != 12:
        raise RuntimeError("Seleção do carrossel não possui 12 produtos únicos.")
    if updated.count("data-hero-item-id=") != 12:
        raise RuntimeError("Quantidade inválida de mini-cards do carrossel.")

    if DRY_RUN:
        print("HERO DRY-RUN OK: 12 mini-cards; WordPress somente leitura.")
        return

    wp_request("POST", f"/wp-json/wp/v2/pages/{PAGE_ID}", username, password, {"content": updated})
    verify = wp_request("GET", f"/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", username, password)
    verify_raw = ((verify.get("content") or {}).get("raw") or "")
    missing = [item_id for item_id in hero_ids if f'data-hero-item-id="{item_id}"' not in verify_raw]
    if verify_raw.count("data-hero-item-id=") != 12 or missing:
        raise RuntimeError(f"Falha pós-publicação do carrossel; IDs ausentes={missing[:4]}")
    print("HERO PUBLICAÇÃO OK: 12 mini-cards sincronizados com a vitrine.")


if __name__ == "__main__":
    main()
