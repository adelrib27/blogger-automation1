#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime
from pathlib import Path

from blogger_policy_guard import require_product_allowed
from criar_rascunho import criar_servico_blogger

ROOT = Path(__file__).resolve().parents[2]
SELECTION_PATH = ROOT / "blogger_stores" / "data" / "achados_casa_selection.json"
BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "1426630233929943394").strip()
POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "854861801599328533").strip()
DRY_RUN = os.getenv("ACHADOS_STORE_DRY_RUN", "true").strip().lower() in {"1", "true", "yes", "on"}
START = "<!-- BLOGGER_LIQ_STORE_AUTO_START -->"
END = "<!-- BLOGGER_LIQ_STORE_AUTO_END -->"
EXPECTED_APP_ID = "18352820579"
EXPECTED_BLOG_ID = "1426630233929943394"
EXPECTED_POST_ID = "854861801599328533"

CATEGORY_META = {
    "Organizacao & Armazenamento": ("Organização & Armazenamento", "bls-organizacao-armazenamento"),
    "Cozinha & Utilidades": ("Cozinha & Utilidades", "bls-cozinha-utilidades"),
    "Limpeza & Lavanderia": ("Limpeza & Lavanderia", "bls-limpeza-lavanderia"),
    "Decoracao & Conforto": ("Decoração & Conforto", "bls-decoracao-conforto"),
    "Clima & Bem-estar": ("Clima & Bem-estar", "bls-clima-bem-estar"),
}


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def money(value) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return ""


def price_text(product: dict) -> str:
    direct = product.get("priceText") or product.get("price_text")
    if direct:
        return str(direct)
    pmin = product.get("priceMin")
    pmax = product.get("priceMax")
    if pmin is None:
        pmin = product.get("price")
    if pmin is None:
        return "Confira o preço"
    if pmax is None:
        pmax = pmin
    try:
        a, b = float(pmin), float(pmax)
    except Exception:
        return "Confira o preço"
    if abs(a - b) < 0.005:
        return money(a)
    return f"A partir de {money(a)}"


def affiliate_url(product: dict) -> str:
    return str(product.get("affiliateUrl") or product.get("offerLink") or "").strip()


def validate_target() -> None:
    if BLOG_ID != EXPECTED_BLOG_ID:
        raise RuntimeError(f"Blog alvo incorreto: {BLOG_ID}")
    if POST_ID != EXPECTED_POST_ID:
        raise RuntimeError(f"Store Post alvo incorreto: {POST_ID}")


def validate_selection(data: dict) -> list[dict]:
    if int(data.get("schemaVersion") or 0) != 6:
        raise RuntimeError("Seleção Achados precisa estar em schemaVersion=6.")
    if data.get("status") != "SAFE_READY" or data.get("publishReady") is not True:
        raise RuntimeError("Seleção Achados não está SAFE_READY/publishReady.")
    if str(data.get("blogId")) != EXPECTED_BLOG_ID:
        raise RuntimeError("blogId da seleção não corresponde ao Achados para Casa.")
    if int(data.get("categoryCount") or 0) != 5 or int(data.get("totalItems") or 0) != 20:
        raise RuntimeError("Seleção não contém 5 categorias / 20 produtos.")
    if int(data.get("uniqueItemIds") or 0) != 20:
        raise RuntimeError("Seleção não contém 20 IDs únicos.")

    link_meta = data.get("affiliateLinkGeneration") or {}
    if str(link_meta.get("appId")) != EXPECTED_APP_ID:
        raise RuntimeError("AppID da seleção não corresponde ao AppID autorizado.")
    if int(link_meta.get("validatedCount") or 0) != 20 or link_meta.get("allResolvedToShopee") is not True:
        raise RuntimeError("Links afiliados não estão validados 20/20.")

    semantic = data.get("semanticValidation") or {}
    if semantic.get("strictAccessoriesBlocked") is not True:
        raise RuntimeError("Gate semântico de acessórios não confirmado.")
    if semantic.get("oneProductPerKeyword") is not True:
        raise RuntimeError("Gate de diversidade por palavra-chave não confirmado.")
    if int(semantic.get("homeUsePostGateVersion") or 0) != 6:
        raise RuntimeError("Gate final de uso doméstico v6 ausente.")
    if semantic.get("fritadeiraApplianceOnly") is not True:
        raise RuntimeError("Gate de fritadeira completa ausente.")

    gates = data.get("gates") or {}
    if not gates or not all(bool(v) for v in gates.values()):
        raise RuntimeError(f"Gates SAFE inválidos: {gates}")

    categories = data.get("categories") or {}
    if set(categories) != set(CATEGORY_META):
        raise RuntimeError(f"Categorias inesperadas: {list(categories)}")
    if any(len(categories.get(key) or []) != 4 for key in CATEGORY_META):
        raise RuntimeError("Categorias não estão em 5 × 4.")

    coverage = data.get("keywordCoverage") or {}
    if set(coverage) != set(CATEGORY_META) or any(len(set(coverage.get(key) or [])) != 4 for key in CATEGORY_META):
        raise RuntimeError("Cobertura semântica por palavra-chave incompleta.")

    products = [p for key in CATEGORY_META for p in (categories.get(key) or [])]
    ids = [str(p.get("itemId") or "").strip() for p in products]
    if len(ids) != 20 or len(set(ids)) != 20 or any(not x for x in ids):
        raise RuntimeError("itemIds inválidos ou duplicados.")

    for product in products:
        require_product_allowed(product)
        url = affiliate_url(product)
        if not url.startswith("https://"):
            raise RuntimeError(f"Link afiliado inválido: {product.get('itemId')}")
        if not str(product.get("productName") or "").strip():
            raise RuntimeError("Produto sem nome.")
        if not str(product.get("imageUrl") or "").startswith("https://"):
            raise RuntimeError(f"Imagem inválida: {product.get('itemId')}")
    return products


def status_text(data: dict) -> str:
    raw = str(data.get("timestamp") or "")
    try:
        dt = datetime.fromisoformat(raw)
        stamp = dt.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        stamp = "agora"
    return f"Vitrine selecionada em {stamp} · preços e disponibilidade podem mudar na Shopee."


def render(data: dict) -> str:
    categories = data.get("categories") or {}
    css = """<style id="achados-casa-store-auto-css">
.bls-store-status{margin:0 0 16px;padding:12px 16px;border-left:4px solid #e65c20;background:#fff5ef;color:#667085;font-size:12px;line-height:1.5}
.bls-store-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}
.bls-panel{min-width:0;border:1px solid #e3e6ea;border-radius:22px;background:#fff;padding:22px;box-shadow:0 9px 28px rgba(17,24,39,.06)}
.bls-panel:last-child{grid-column:1/-1}.bls-panel-head{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:18px;padding-bottom:13px;border-bottom:1px solid #eef0f2}
.bls-panel-head span{font-size:10px;font-weight:900;letter-spacing:.11em;text-transform:uppercase;color:#e65c20}.bls-panel-head h3{margin:0;font-size:26px;line-height:1;font-weight:900;color:#17212b;text-align:right}
.bls-products{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 14px}.bls-panel:last-child .bls-products{grid-template-columns:repeat(4,minmax(0,1fr))}
.bls-product{display:block;min-width:0;text-decoration:none;color:#17212b;position:relative;z-index:2;pointer-events:auto!important;cursor:pointer!important}.bls-product>*{pointer-events:none!important}
.bls-product-cta{display:flex;align-items:center;justify-content:center;margin-top:9px;padding:9px 10px;border-radius:8px;background:#ee4d2d;color:#fff;font-size:11px;font-weight:900;line-height:1.15;text-align:center}
.bls-product-img{display:block;width:100%;aspect-ratio:1/1;border-radius:16px;overflow:hidden;background:#f7f7f5;border:1px solid #e9ecef}.bls-product-img img{display:block;width:100%;height:100%;object-fit:contain;transition:transform .25s ease}.bls-product:hover .bls-product-img img{transform:scale(1.025)}
.bls-product-name{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.7em;margin-top:10px;font-size:13px;line-height:1.35}.bls-product strong{display:block;margin-top:6px;color:#17212b;font-size:16px}.bls-product small{display:block;margin-top:3px;color:#747d82;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bls-panel-foot{margin-top:17px;padding-top:12px;border-top:1px solid #eef0f2;color:#81898e;font-size:10px;line-height:1.45}
@media(max-width:900px){.bls-store-grid{grid-template-columns:1fr}.bls-panel:last-child{grid-column:auto}.bls-panel:last-child .bls-products{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){.bls-panel{padding:17px;border-radius:17px}.bls-panel-head{display:block}.bls-panel-head h3{margin-top:5px;text-align:left;font-size:24px}.bls-products,.bls-panel:last-child .bls-products{grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 10px}.bls-product-name{font-size:12px}.bls-product strong{font-size:14px}}
</style>"""
    out = [css, f'<p class="bls-store-status">{esc(status_text(data))}</p>', '<div class="bls-store-grid">']
    for key, (label, panel_id) in CATEGORY_META.items():
        items = categories.get(key) or []
        out.append(f'<article class="bls-panel" id="{esc(panel_id)}"><div class="bls-panel-head"><span>Seleção da categoria</span><h3>{esc(label)}</h3></div><div class="bls-products">')
        for p in items:
            iid = str(p.get("itemId") or "").strip()
            name = str(p.get("productName") or "").strip()
            shop = str(p.get("shopName") or "").strip()
            image = str(p.get("imageUrl") or "").strip()
            url = affiliate_url(p)
            out.append(
                f'<a class="bls-product" data-item-id="{esc(iid)}" href="{esc(url)}" target="_blank" rel="nofollow sponsored noopener">'
                f'<span class="bls-product-img"><img src="{esc(image)}" alt="{esc(name)}" loading="lazy" decoding="async"></span>'
                f'<span class="bls-product-name">{esc(name)}</span>'
                f'<strong>{esc(price_text(p))}</strong><small>{esc(shop)}</small>'
                '<span class="bls-product-cta">Ver oferta na Shopee</span></a>'
            )
        out.append('</div><div class="bls-panel-foot">Atualização automática · confirme preço e disponibilidade na Shopee</div></article>')
    out.append('</div>')
    return ''.join(out)


def locate(raw: str) -> tuple[int, int]:
    if raw.count(START) != 1 or raw.count(END) != 1:
        raise RuntimeError("Marcadores da Loja ausentes ou duplicados; POST preservado.")
    a = raw.find(START)
    b = raw.find(END)
    if b <= a:
        raise RuntimeError("Ordem inválida dos marcadores; POST preservado.")
    return a, b


def verify_html(raw: str, data: dict) -> None:
    products = [p for key in CATEGORY_META for p in ((data.get("categories") or {}).get(key) or [])]
    ids = [str(p.get("itemId")) for p in products]
    if raw.count("data-item-id=") != 20:
        raise RuntimeError("Validação: quantidade de cards diferente de 20.")
    if len(set(ids)) != 20 or any(f'data-item-id="{iid}"' not in raw for iid in ids):
        raise RuntimeError("Validação: itemId selecionado ausente ou duplicado.")
    for p in products:
        url = affiliate_url(p)
        if f'href="{html.escape(url, quote=True)}"' not in raw:
            raise RuntimeError(f"Validação: href ausente para {p.get('itemId')}.")
    if raw.count('rel="nofollow sponsored noopener"') < 20:
        raise RuntimeError("Validação: rel afiliado ausente.")
    for _, panel_id in CATEGORY_META.values():
        if f'id="{panel_id}"' not in raw:
            raise RuntimeError(f"Validação: painel {panel_id} ausente.")
    if re.search(r"onclick\s*=|window\.location|location\.assign", raw, flags=re.I):
        raise RuntimeError("Validação: JavaScript de navegação proibido detectado.")


def main() -> int:
    validate_target()
    data = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    validate_selection(data)
    service = criar_servico_blogger()
    post = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    raw = str(post.get("content") or "")
    a, b = locate(raw)
    new_raw = raw[: a + len(START)] + "\n" + render(data) + "\n" + raw[b:]
    verify_html(new_raw, data)
    if DRY_RUN:
        print("ACHADOS_CASA_STORE_DRY_RUN_PASS: 20 produtos validados em memória; Blogger não alterado.")
        return 0

    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_raw = str(verify.get("content") or "")
    verify_html(verify_raw, data)
    print(f"ACHADOS_CASA_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
