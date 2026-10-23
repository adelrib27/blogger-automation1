#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "blogger_product_store"
DATA_DIR = MODULE_DIR / "data"
HISTORY_PATH = DATA_DIR / "store_rotation.json"
LAST_SELECTION_PATH = DATA_DIR / "store_last_selection.json"
SCAN_DIR = DATA_DIR / "store_shopee_scan"

BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "5271798990390532475").strip()
PAGE_ID = os.getenv("BLOGGER_STORE_PAGE_ID", "").strip()
ITEMS_PER_CATEGORY = max(1, min(int(os.getenv("BLOGGER_STORE_ITEMS_PER_CATEGORY", "4")), 8))
RECENT_DAYS = max(1, min(int(os.getenv("BLOGGER_STORE_RECENT_DAYS", "1")), 30))
DRY_RUN = os.getenv("BLOGGER_STORE_DRY_RUN", "false").strip().lower() in {"1", "true", "yes", "on"}

START_MARKER = "<!-- BLOGGER_LIQ_STORE_AUTO_START -->"
END_MARKER = "<!-- BLOGGER_LIQ_STORE_AUTO_END -->"

CATEGORY_SPECS = [
    ("Liquidificadores", "Liquidificadores", "bls-liquidificadores"),
    ("Mixers", "Mixers", "bls-mixers"),
    ("Processadores", "Processadores", "bls-processadores"),
    ("Trituradores", "Trituradores", "bls-trituradores"),
    ("Complementos", "Complementos de cozinha", "bls-complementos"),
]

os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(SCAN_DIR))
os.environ.setdefault("SHOPEE_CATEGORY", "all")
os.environ.setdefault("SHOPEE_TOP_N", "50")

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(MODULE_DIR / "src"))

import shopee_oportunidades_v23 as shopee_v23  # noqa: E402
import shopee_oportunidades_liquidificador as niche_shopee  # noqa: E402
from criar_rascunho import criar_servico_blogger  # noqa: E402

shopee_v23.run_regression_checks = niche_shopee.regression_checks


def now_local() -> datetime:
    return datetime.now(ZoneInfo("America/Recife"))


def as_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
            raise ValueError("histórico inválido")
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


def normalize_category(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


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
        picks: list[dict] = []
        for product in fresh + repeated:
            item_id = str(product.get("itemId"))
            if item_id in used_now:
                continue
            picks.append(product)
            used_now.add(item_id)
            if len(picks) == ITEMS_PER_CATEGORY:
                break
        if len(picks) != ITEMS_PER_CATEGORY:
            raise RuntimeError(
                f"Categoria {key} sem candidatos suficientes: "
                f"{len(picks)}/{ITEMS_PER_CATEGORY}. Página preservada."
            )
        chosen[key] = picks

    expected = len(CATEGORY_SPECS) * ITEMS_PER_CATEGORY
    if len(used_now) != expected:
        raise RuntimeError(f"Seleção inválida: {len(used_now)} IDs únicos; esperado {expected}.")
    return chosen


def brl(value) -> str:
    raw = f"{as_float(value):,.2f}"
    return "R$ " + raw.replace(",", "X").replace(".", ",").replace("X", ".")


def price_label(product: dict) -> str:
    pmin = as_float(product.get("priceMin"))
    pmax = as_float(product.get("priceMax"))
    return f"A partir de {brl(pmin)}" if pmax > pmin + 0.009 else brl(pmin)


def short_name(name: str, limit: int = 74) -> str:
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
    alt = html.escape(short_name(full_name, 110), quote=True)
    shop = html.escape(short_name(str(product.get("shopName") or "Shopee"), 40))
    price = html.escape(price_label(product))
    return f'''<a class="bls-product" data-item-id="{item_id}" href="{url}" target="_blank" rel="nofollow sponsored noopener">
  <span class="bls-product-img"><img src="{image}" alt="{alt}" loading="lazy" decoding="async"></span>
  <span class="bls-product-name">{name}</span>
  <strong>{price}</strong>
  <small>{shop}</small>
</a>'''


def render_store_block(chosen: dict[str, list[dict]]) -> str:
    panels = []
    for key, label, anchor in CATEGORY_SPECS:
        products = "\n".join(render_product(p) for p in chosen[key])
        panels.append(f'''<article class="bls-panel" id="{anchor}">
  <div class="bls-panel-head"><span>Seleção da categoria</span><h3>{html.escape(label)}</h3></div>
  <div class="bls-products">{products}</div>
  <div class="bls-panel-foot">Atualização automática · confirme preço e disponibilidade na Shopee</div>
</article>''')

    stamp = now_local().strftime("%d/%m/%Y às %H:%M")
    return f'''{START_MARKER}
<style id="blogger-liq-store-auto-css">
.bls-store-status{{margin:0 0 16px;padding:12px 16px;border-left:4px solid #e65c20;background:#fff5ef;color:#667085;font-size:12px;line-height:1.5}}
.bls-store-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}}
.bls-panel{{min-width:0;border:1px solid #e3e6ea;border-radius:22px;background:#fff;padding:22px;box-shadow:0 9px 28px rgba(17,24,39,.06)}}
.bls-panel:last-child{{grid-column:1/-1}}
.bls-panel-head{{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:18px;padding-bottom:13px;border-bottom:1px solid #eef0f2}}
.bls-panel-head span{{font-size:10px;font-weight:900;letter-spacing:.11em;text-transform:uppercase;color:#e65c20}}
.bls-panel-head h3{{margin:0;font-size:26px;line-height:1;font-weight:900;color:#17212b;text-align:right}}
.bls-products{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 14px}}
.bls-panel:last-child .bls-products{{grid-template-columns:repeat(4,minmax(0,1fr))}}
.bls-product{{display:block;min-width:0;text-decoration:none;color:#17212b}}
.bls-product-img{{display:block;width:100%;aspect-ratio:1/1;border-radius:16px;overflow:hidden;background:#f7f7f5;border:1px solid #e9ecef}}
.bls-product-img img{{display:block;width:100%;height:100%;object-fit:contain;transition:transform .25s ease}}
.bls-product:hover .bls-product-img img{{transform:scale(1.025)}}
.bls-product-name{{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.7em;margin-top:10px;font-size:13px;line-height:1.35}}
.bls-product strong{{display:block;margin-top:6px;color:#17212b;font-size:16px}}
.bls-product small{{display:block;margin-top:3px;color:#747d82;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.bls-panel-foot{{margin-top:17px;padding-top:12px;border-top:1px solid #eef0f2;color:#81898e;font-size:10px;line-height:1.45}}
@media(max-width:900px){{.bls-store-grid{{grid-template-columns:1fr}}.bls-panel:last-child{{grid-column:auto}}.bls-panel:last-child .bls-products{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:560px){{.bls-panel{{padding:17px;border-radius:17px}}.bls-panel-head{{display:block}}.bls-panel-head h3{{margin-top:5px;text-align:left;font-size:24px}}.bls-products,.bls-panel:last-child .bls-products{{grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 10px}}.bls-product-name{{font-size:12px}}.bls-product strong{{font-size:14px}}}}
</style>
<p class="bls-store-status">Vitrine atualizada em {stamp} · produtos selecionados automaticamente · preços e disponibilidade podem mudar na Shopee.</p>
<div class="bls-store-grid">{''.join(panels)}</div>
{END_MARKER}'''


def page_id() -> str:
    if not PAGE_ID:
        raise RuntimeError("BLOGGER_STORE_PAGE_ID ausente.")
    return PAGE_ID


def get_target_page() -> tuple[object, dict, str]:
    blogger = criar_servico_blogger()
    page = blogger.pages().get(blogId=BLOG_ID, pageId=page_id()).execute()
    raw = str(page.get("content") or "")
    return blogger, page, raw


def locate_region(raw: str) -> tuple[int, int]:
    start = raw.find(START_MARKER)
    end = raw.find(END_MARKER)
    if start < 0 or end <= start:
        raise RuntimeError("Marcadores da vitrine Blogger não encontrados; nenhuma alteração será feita.")
    if raw.count(START_MARKER) != 1 or raw.count(END_MARKER) != 1:
        raise RuntimeError("Quantidade inválida de marcadores da vitrine Blogger; página preservada.")
    return start, end + len(END_MARKER)


def validate_blogger_target() -> None:
    _, page, raw = get_target_page()
    if len(raw) < 4500:
        raise RuntimeError("Página da loja Blogger retornou conteúdo inesperadamente pequeno.")
    locate_region(raw)
    if str(page.get("title") or "").strip().lower() != "loja":
        raise RuntimeError("Page ID não corresponde ao título Loja; nenhuma alteração será feita.")
    print("Alvo Blogger validado em modo somente leitura.")


def update_blogger(block: str, chosen: dict[str, list[dict]]) -> dict:
    blogger, page, raw = get_target_page()
    start, end = locate_region(raw)
    updated = raw[:start] + block + raw[end:]
    if updated.count(START_MARKER) != 1 or updated.count(END_MARKER) != 1:
        raise RuntimeError("Marcadores inválidos após composição.")
    if len(updated) < max(4500, int(len(raw) * 0.55)):
        raise RuntimeError("Proteção de integridade: conteúdo resultante ficou pequeno demais.")

    result = blogger.pages().update(
        blogId=BLOG_ID,
        pageId=page_id(),
        body={"title": page.get("title") or "Loja", "content": updated},
    ).execute()

    verify = blogger.pages().get(blogId=BLOG_ID, pageId=page_id()).execute()
    verify_raw = str(verify.get("content") or "")
    ids = {str(p.get("itemId")) for values in chosen.values() for p in values}
    missing = [item_id for item_id in ids if f'data-item-id="{item_id}"' not in verify_raw]
    if START_MARKER not in verify_raw or END_MARKER not in verify_raw or missing:
        raise RuntimeError(f"Falha pós-publicação Blogger; IDs ausentes={missing[:5]}")
    return {
        "pageId": result.get("id"),
        "updated": result.get("updated"),
        "url": result.get("url"),
        "itemsVerified": len(ids),
    }


def snapshot(chosen: dict[str, list[dict]], status: str, blogger=None) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    categories = {}
    for key, _, _ in CATEGORY_SPECS:
        categories[key] = [{
            "itemId": str(p.get("itemId")),
            "productName": str(p.get("productName") or ""),
            "shopName": str(p.get("shopName") or ""),
            "priceMin": p.get("priceMin"),
            "priceMax": p.get("priceMax"),
            "offerLink": str(p.get("offerLink") or ""),
            "imageUrl": str(p.get("imageUrl") or ""),
        } for p in chosen[key]]
    data = {
        "version": 1,
        "status": status,
        "timestamp": now_local().isoformat(),
        "dryRun": DRY_RUN,
        "itemsPerCategory": ITEMS_PER_CATEGORY,
        "categoryCount": len(CATEGORY_SPECS),
        "totalItems": ITEMS_PER_CATEGORY * len(CATEGORY_SPECS),
        "categories": categories,
        "blogger": blogger,
    }
    LAST_SELECTION_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def append_history(data: dict) -> None:
    history = load_history()
    items = [
        {"category": category, "itemId": item.get("itemId")}
        for category, values in data["categories"].items()
        for item in values
    ]
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
    if (
        len(ids) != expected
        or block.count('rel="nofollow sponsored noopener"') != expected
        or block.count("data-item-id=") != expected
    ):
        raise RuntimeError("Quantidade de cards/links não corresponde à seleção.")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Blogger — Loja automática Liquidificador Philips Walita RI2242 v1")
    print("Modo:", "DRY-RUN" if DRY_RUN else "PUBLICAÇÃO")
    ranking = shopee_v23.scan_v23()
    print("Ranking Shopee recebido:", len(ranking))
    chosen = choose_products(ranking, load_history())
    block = render_store_block(chosen)
    validate_shape(chosen, block)

    if DRY_RUN:
        validate_blogger_target()
        data = snapshot(chosen, "DRY_RUN_OK")
        print(
            f"DRY-RUN OK: {data['totalItems']} produtos únicos em "
            f"{data['categoryCount']} categorias; Blogger não alterado."
        )
        return

    blogger_info = update_blogger(block, chosen)
    data = snapshot(chosen, "PUBLISHED", blogger_info)
    append_history(data)
    print(
        f"PUBLICAÇÃO OK: {data['totalItems']} produtos únicos; "
        f"página Blogger {blogger_info.get('pageId')} verificada."
    )


if __name__ == "__main__":
    main()
