#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
from pathlib import Path

from blogger_policy_guard import require_product_allowed
from criar_rascunho import criar_servico_blogger
from achados_casa_publish_post import affiliate_url, price_text, validate_selection

ROOT = Path(__file__).resolve().parents[2]
SELECTION_PATH = ROOT / "blogger_stores" / "data" / "achados_casa_selection.json"
BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "1426630233929943394").strip()
POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "854861801599328533").strip()
DRY_RUN = os.getenv("ACHADOS_STORE_DRY_RUN", "true").strip().lower() in {"1", "true", "yes", "on"}
EXPECTED_BLOG_ID = "1426630233929943394"
EXPECTED_POST_ID = "854861801599328533"

MARKERS = [
    ("<!-- BLOGGER_LIQ_HERO_AUTO_1_START -->", "<!-- BLOGGER_LIQ_HERO_AUTO_1_END -->"),
    ("<!-- BLOGGER_LIQ_HERO_AUTO_2_START -->", "<!-- BLOGGER_LIQ_HERO_AUTO_2_END -->"),
    ("<!-- BLOGGER_LIQ_HERO_AUTO_3_START -->", "<!-- BLOGGER_LIQ_HERO_AUTO_3_END -->"),
]


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def category_label(key: str) -> str:
    return {
        "Organizacao & Armazenamento": "Organização",
        "Cozinha & Utilidades": "Cozinha",
        "Limpeza & Lavanderia": "Limpeza",
        "Decoracao & Conforto": "Decoração",
        "Clima & Bem-estar": "Clima & bem-estar",
    }.get(key, key)


def card(product: dict, category: str) -> str:
    require_product_allowed(product)
    iid = str(product.get("itemId") or "").strip()
    name = str(product.get("productName") or "").strip()
    image = str(product.get("imageUrl") or "").strip()
    url = affiliate_url(product)
    return (
        f'<a class="blh-product" data-hero-item-id="{esc(iid)}" href="{esc(url)}" target="_blank" rel="nofollow sponsored noopener" title="{esc(name)}">'
        f'<span class="blh-product-img"><img src="{esc(image)}" alt="{esc(name)}" loading="lazy" decoding="async"></span>'
        f'<span class="blh-product-meta"><b>{esc(category_label(category))}</b><small>{esc(price_text(product))}</small></span>'
        '</a>'
    )


def hero_css() -> str:
    return """<style id="achados-casa-hero-auto-css">
.blh-card{width:min(520px,96%);background:#fff;border:1px solid rgba(17,24,39,.12);border-radius:22px;padding:24px;box-shadow:0 22px 48px rgba(17,24,39,.15)}
.blh-card>strong{display:block;margin-bottom:13px;font-size:27px;line-height:1.06;color:#17212b;font-weight:900}.blh-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px}
.blh-product{display:block;min-width:0;overflow:hidden;border:1px solid #e2e6ea;border-radius:14px;background:#fff;text-decoration:none;color:#17212b;box-shadow:0 6px 15px rgba(17,24,39,.07);transition:transform .2s ease,box-shadow .2s ease}.blh-product:hover{transform:translateY(-2px);box-shadow:0 10px 22px rgba(17,24,39,.13)}
.blh-product-img{display:block;width:100%;height:112px;background:#f7f7f5;overflow:hidden}.blh-product-img img{display:block;width:100%;height:100%;object-fit:contain}.blh-product-meta{display:flex;align-items:center;justify-content:space-between;gap:6px;padding:8px 9px;min-height:35px}.blh-product-meta b{min-width:0;font:900 10px/1.15 Arial,sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.blh-product-meta small{flex:none;font:800 9px/1.1 Arial,sans-serif;color:#e65c20;white-space:nowrap}@media(max-width:620px){.blh-card{padding:16px}.blh-card>strong{font-size:23px}.blh-product-img{height:96px}.blh-product-meta{display:block}.blh-product-meta small{display:block;margin-top:3px}}
</style>"""


def build_slides(data: dict) -> list[str]:
    categories = data.get("categories") or {}
    org = categories["Organizacao & Armazenamento"]
    coz = categories["Cozinha & Utilidades"]
    limp = categories["Limpeza & Lavanderia"]
    deco = categories["Decoracao & Conforto"]
    clima = categories["Clima & Bem-estar"]

    groups = [
        ("Organização e cozinha para uma casa prática", [(org[0], "Organizacao & Armazenamento"), (org[1], "Organizacao & Armazenamento"), (coz[0], "Cozinha & Utilidades"), (coz[1], "Cozinha & Utilidades")]),
        ("Limpeza, lavanderia e conforto", [(limp[0], "Limpeza & Lavanderia"), (limp[1], "Limpeza & Lavanderia"), (deco[0], "Decoracao & Conforto"), (deco[1], "Decoracao & Conforto")]),
        ("Clima e bem-estar em destaque", [(clima[0], "Clima & Bem-estar"), (clima[1], "Clima & Bem-estar"), (clima[2], "Clima & Bem-estar"), (clima[3], "Clima & Bem-estar")]),
    ]
    slides = []
    for index, (title, items) in enumerate(groups):
        cards = ''.join(card(product, category) for product, category in items)
        prefix = hero_css() if index == 0 else ""
        slides.append(prefix + f'<div class="blh-card"><strong>{esc(title)}</strong><div class="blh-grid">{cards}</div></div>')
    return slides


def replace_region(raw: str, start: str, end: str, content: str) -> str:
    if raw.count(start) != 1 or raw.count(end) != 1:
        raise RuntimeError(f"Marcadores hero ausentes ou duplicados: {start}")
    a = raw.find(start)
    b = raw.find(end)
    if b <= a:
        raise RuntimeError(f"Ordem inválida dos marcadores hero: {start}")
    return raw[: a + len(start)] + content + raw[b:]


def verify(raw: str, slides: list[str]) -> None:
    if raw.count("data-hero-item-id=") != 12:
        raise RuntimeError("Hero inválido: esperado 12 mini-cards.")
    ids = []
    for slide in slides:
        pos = 0
        while True:
            pos = slide.find('data-hero-item-id="', pos)
            if pos < 0:
                break
            pos += len('data-hero-item-id="')
            end = slide.find('"', pos)
            ids.append(slide[pos:end])
            pos = end + 1
    if len(ids) != 12 or len(set(ids)) != 12:
        raise RuntimeError("Hero inválido: IDs ausentes ou duplicados.")
    if any(f'data-hero-item-id="{iid}"' not in raw for iid in ids):
        raise RuntimeError("Hero inválido: item selecionado ausente no HTML.")
    if raw.count('rel="nofollow sponsored noopener"') < 32:
        raise RuntimeError("Hero inválido: rel afiliado incompleto.")


def main() -> int:
    if BLOG_ID != EXPECTED_BLOG_ID or POST_ID != EXPECTED_POST_ID:
        raise RuntimeError("Alvo Blogger do Achados para Casa não confere.")
    data = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    validate_selection(data)
    slides = build_slides(data)
    service = criar_servico_blogger()
    post = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    raw = str(post.get("content") or "")
    new_raw = raw
    for (start, end), content in zip(MARKERS, slides):
        new_raw = replace_region(new_raw, start, end, content)
    verify(new_raw, slides)
    if DRY_RUN:
        print("ACHADOS_CASA_HERO_DRY_RUN_PASS: 12 mini-cards validados em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify_post = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify(str(verify_post.get("content") or ""), slides)
    print("ACHADOS_CASA_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
