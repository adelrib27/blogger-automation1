#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "blogger_product_store"
DATA_DIR = MODULE_DIR / "data"
LAST_SELECTION_PATH = DATA_DIR / "store_last_selection.json"
BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "5271798990390532475").strip()
PAGE_ID = os.getenv("BLOGGER_STORE_PAGE_ID", "").strip()

sys.path.insert(0, str(ROOT / "src"))
from criar_rascunho import criar_servico_blogger  # noqa: E402

HERO_MARKERS = [
    ("<!-- BLOGGER_LIQ_HERO_AUTO_1_START -->", "<!-- BLOGGER_LIQ_HERO_AUTO_1_END -->"),
    ("<!-- BLOGGER_LIQ_HERO_AUTO_2_START -->", "<!-- BLOGGER_LIQ_HERO_AUTO_2_END -->"),
    ("<!-- BLOGGER_LIQ_HERO_AUTO_3_START -->", "<!-- BLOGGER_LIQ_HERO_AUTO_3_END -->"),
]


def page_id() -> str:
    if not PAGE_ID:
        raise RuntimeError("BLOGGER_STORE_PAGE_ID ausente.")
    return PAGE_ID


def as_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def brl(value) -> str:
    raw = f"{as_float(value):,.2f}"
    return "R$ " + raw.replace(",", "X").replace(".", ",").replace("X", ".")


def price_label(product: dict) -> str:
    pmin = as_float(product.get("priceMin"))
    pmax = as_float(product.get("priceMax"))
    return f"A partir de {brl(pmin)}" if pmax > pmin + 0.009 else brl(pmin)


def short_name(value: str, limit: int = 88) -> str:
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(value) <= limit:
        return value
    cut = value[:limit].rsplit(" ", 1)[0].rstrip(" -–—,.;:")
    return (cut or value[:limit]).rstrip() + "…"


def load_selection() -> dict:
    if not LAST_SELECTION_PATH.exists():
        raise RuntimeError("Snapshot da vitrine não encontrado.")
    data = json.loads(LAST_SELECTION_PATH.read_text(encoding="utf-8"))
    if data.get("status") != "PUBLISHED":
        raise RuntimeError("Hero só sincroniza após uma vitrine PUBLISHED confirmada.")
    if int(data.get("totalItems") or 0) != 20:
        raise RuntimeError("Snapshot da vitrine não possui 20 produtos confirmados.")
    return data


def hero_sets(data: dict) -> list[list[tuple[str, dict]]]:
    c = data.get("categories") or {}
    required = ["Liquidificadores", "Mixers", "Processadores", "Trituradores", "Complementos"]
    for key in required:
        if len(c.get(key) or []) != 4:
            raise RuntimeError(f"Categoria {key} inválida no snapshot do hero.")

    slides = [
        [("Liquidificador", p) for p in c["Liquidificadores"]],
        [("Mixer", p) for p in c["Mixers"][:2]] + [("Processador", p) for p in c["Processadores"][:2]],
        [("Triturador", p) for p in c["Trituradores"][:2]] + [("Complemento", p) for p in c["Complementos"][:2]],
    ]
    ids = [str(p.get("itemId")) for slide in slides for _, p in slide]
    if len(ids) != 12 or len(set(ids)) != 12:
        raise RuntimeError("Seleção do hero não contém 12 produtos únicos.")
    return slides


def render_card(label: str, product: dict) -> str:
    item_id = html.escape(str(product.get("itemId") or ""), quote=True)
    url = html.escape(str(product.get("offerLink") or ""), quote=True)
    image = html.escape(str(product.get("imageUrl") or ""), quote=True)
    full_name = str(product.get("productName") or "").strip()
    alt = html.escape(short_name(full_name, 110), quote=True)
    title = html.escape(short_name(full_name, 110), quote=True)
    price = html.escape(price_label(product))
    return f'''<a class="blh-product" data-hero-item-id="{item_id}" href="{url}" target="_blank" rel="nofollow sponsored noopener" title="{title}">
  <span class="blh-product-img"><img src="{image}" alt="{alt}" loading="lazy" decoding="async"></span>
  <span class="blh-product-meta"><b>{html.escape(label)}</b><small>{price}</small></span>
</a>'''


def render_region(start: str, end: str, heading: str, items: list[tuple[str, dict]], include_css: bool = False) -> str:
    css = '''<style id="blogger-liq-hero-auto-css">
.blh-card{width:min(520px,96%);background:#fff;border:1px solid rgba(17,24,39,.12);border-radius:22px;padding:24px;box-shadow:0 22px 48px rgba(17,24,39,.15)}
.blh-card>strong{display:block;margin-bottom:13px;font-size:27px;line-height:1.06;color:#17212b;font-weight:900}
.blh-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px}
.blh-product{display:block;min-width:0;overflow:hidden;border:1px solid #e2e6ea;border-radius:14px;background:#fff;text-decoration:none;color:#17212b;box-shadow:0 6px 15px rgba(17,24,39,.07);transition:transform .2s ease,box-shadow .2s ease}
.blh-product:hover{transform:translateY(-2px);box-shadow:0 10px 22px rgba(17,24,39,.13)}
.blh-product-img{display:block;width:100%;height:112px;background:#f7f7f5;overflow:hidden}
.blh-product-img img{display:block;width:100%;height:100%;object-fit:contain}
.blh-product-meta{display:flex;align-items:center;justify-content:space-between;gap:6px;padding:8px 9px;min-height:35px}
.blh-product-meta b{min-width:0;font:900 10px/1.15 Arial,sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.blh-product-meta small{flex:none;font:800 9px/1.1 Arial,sans-serif;color:#e65c20;white-space:nowrap}
@media(max-width:620px){.blh-card{padding:16px}.blh-card>strong{font-size:23px}.blh-product-img{height:96px}.blh-product-meta{display:block}.blh-product-meta small{display:block;margin-top:3px}}
</style>''' if include_css else ""
    cards = "\n".join(render_card(label, p) for label, p in items)
    return f'''{start}{css}<div class="blh-card"><strong>{html.escape(heading)}</strong><div class="blh-grid">{cards}</div></div>{end}'''


def locate(raw: str, start: str, end: str) -> tuple[int, int]:
    a = raw.find(start)
    b = raw.find(end)
    if a < 0 or b <= a:
        raise RuntimeError(f"Marcadores do hero ausentes: {start}")
    if raw.count(start) != 1 or raw.count(end) != 1:
        raise RuntimeError(f"Marcadores duplicados do hero: {start}")
    return a, b + len(end)


def main() -> None:
    data = load_selection()
    slides = hero_sets(data)
    blocks = [
        render_region(*HERO_MARKERS[0], "Liquidificadores em destaque", slides[0], include_css=True),
        render_region(*HERO_MARKERS[1], "Mais versatilidade no preparo", slides[1]),
        render_region(*HERO_MARKERS[2], "Complete sua bancada", slides[2]),
    ]

    blogger = criar_servico_blogger()
    page = blogger.pages().get(blogId=BLOG_ID, pageId=page_id()).execute()
    raw = str(page.get("content") or "")
    original_len = len(raw)

    for (start, end), block in zip(HERO_MARKERS, blocks):
        a, b = locate(raw, start, end)
        raw = raw[:a] + block + raw[b:]

    if len(raw) < max(4500, int(original_len * 0.55)):
        raise RuntimeError("Proteção de integridade do hero: página resultante ficou pequena demais.")

    blogger.pages().update(
        blogId=BLOG_ID,
        pageId=page_id(),
        body={"title": page.get("title") or "Loja", "content": raw},
    ).execute()

    verify = blogger.pages().get(blogId=BLOG_ID, pageId=page_id()).execute()
    verify_raw = str(verify.get("content") or "")
    ids = [str(p.get("itemId")) for slide in slides for _, p in slide]
    missing = [i for i in ids if f'data-hero-item-id="{i}"' not in verify_raw]
    if missing or verify_raw.count("data-hero-item-id=") != 12:
        raise RuntimeError(f"Falha na sincronização do hero; IDs ausentes={missing[:5]}")
    print("HERO OK: 12 mini-cards únicos sincronizados na página Blogger.")


if __name__ == "__main__":
    main()
