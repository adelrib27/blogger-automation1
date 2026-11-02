#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

from blogger_policy_guard import require_store_html_allowed
from blogger_new_blog_store_page_target import get_post_any_status
from criar_rascunho import criar_servico_blogger
import casa_pratica_lab_store as lab

SOURCE_BLOG_ID = "1719259388907013414"
SOURCE_POST_ID = "259394788951394758"
SOURCE_PAGE_URL = "https://conectaachados.blogspot.com/p/loja.html"

BLOG_ID = "8930870316690519385"
PAGE_ID = "7110845449177208439"
POST_ID = "7691087355641688975"
PAGE_URL = "https://casa-pratica-lab-20261102.blogspot.com/p/loja.html"
POST_URL = "https://casa-pratica-lab-20261102.blogspot.com/2026/11/loja.html"

base = lab.base


def require_target() -> None:
    expected = {
        "BLOGGER_BLOG_ID": BLOG_ID,
        "BLOGGER_STORE_PAGE_ID": PAGE_ID,
        "BLOGGER_STORE_POST_ID": POST_ID,
        "BLOGGER_STORE_PAGE_URL": PAGE_URL,
    }
    for key, wanted in expected.items():
        got = os.getenv(key, wanted).strip()
        if got != wanted:
            raise RuntimeError(f"Alvo incorreto em {key}: {got!r} != {wanted!r}")


def bridge_html() -> str:
    return (
        '<div style="max-width:760px;margin:48px auto;padding:28px;border:1px solid #dfe4e8;'
        'border-radius:18px;background:#fff;font-family:Arial,Helvetica,sans-serif;text-align:center">'
        '<h1 style="margin:0 0 12px;font-size:32px">Loja</h1>'
        '<p style="margin:0 0 20px;color:#5f6871;line-height:1.6">'
        'Abrindo a vitrine automática com produtos selecionados da Shopee.</p>'
        f'<p><a href="{POST_URL}" style="display:inline-block;padding:13px 20px;border-radius:10px;'
        'background:#ee4d2d;color:#fff;text-decoration:none;font-weight:700">Abrir Loja</a></p></div>'
        f"<script>window.location.replace('{POST_URL}');</script>"
    )


def build_mature_html(service) -> str:
    source = service.posts().get(blogId=SOURCE_BLOG_ID, postId=SOURCE_POST_ID).execute()
    raw = str(source.get("content") or "")
    if 'id="blsSlider"' not in raw or 'class="bls-nav bls-prev"' not in raw:
        raise RuntimeError("Fonte madura Conecta perdeu o contrato visual do carousel.")

    raw = lab.transform_identity(raw)
    raw = raw.replace(SOURCE_PAGE_URL, PAGE_URL)

    data = base.load_json(lab.SELECTION_PATH, {})
    base.validate_selection(data)
    raw = base.replace_region(raw, base.STORE_START, base.STORE_END, lab.render_store(data))
    slides = lab.build_hero(data)
    for (start, end), slide in zip(base.HERO_MARKERS, slides):
        raw = base.replace_region(raw, start, end, slide)

    lab.verify_identity(raw)
    base.verify_store_html(raw, data)
    base.verify_hero(raw, slides)
    verify_visual_contract(raw)
    return raw


def verify_visual_contract(raw: str) -> None:
    require_store_html_allowed(raw, expected_products=20, expected_hero=12)
    if raw.count("data-item-id=") != 20 or raw.count("data-hero-item-id=") != 12:
        raise RuntimeError("Quantidade da vitrine não é 20+12.")
    if raw.count('rel="nofollow sponsored noopener"') < 32:
        raise RuntimeError("Links patrocinados incompletos.")
    required = [
        "<!-- BLOGGER_LIQ_LAYOUT_PATCH_START -->",
        "<!-- BLOGGER_LIQ_LAYOUT_PATCH_END -->",
        'id="blsSlider"',
        'class="bls-slide is-active"',
        ".bls-slide{display:none",
        ".bls-slide.is-active{display:grid",
        'class="bls-nav bls-prev"',
        'class="bls-nav bls-next"',
        'id="blsDots"',
        "setInterval(()=>show(i+1),6000)",
        "bls-casa-organizacao",
        "bls-cozinha-eletroportateis",
        "bls-iluminacao-decoracao",
        "bls-clima-conforto",
        "bls-utilidades-rotina",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Contrato visual maduro incompleto: {missing}")


def get_live_post(service) -> dict | None:
    kwargs = {"blogId": BLOG_ID, "status": "LIVE", "fetchBodies": True, "maxResults": 100}
    while True:
        response = service.posts().list(**kwargs).execute()
        for item in response.get("items") or []:
            if str(item.get("id") or "") == POST_ID:
                return item
        token = response.get("nextPageToken")
        if not token:
            return None
        kwargs["pageToken"] = token


def load_targets(service):
    post = get_post_any_status(service, BLOG_ID, POST_ID)
    page = service.pages().get(blogId=BLOG_ID, pageId=PAGE_ID).execute()
    if str(post.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"Store Post inesperado: {post.get('title')!r}")
    if str(page.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"Page LOJA inesperada: {page.get('title')!r}")
    return post, page


def dry_run() -> int:
    require_target()
    service = criar_servico_blogger()
    build_mature_html(service)
    page = bridge_html()
    if POST_URL not in page or "window.location.replace" not in page:
        raise RuntimeError("Bridge da Page inválida.")
    print("CASA_PRATICA_LAB_MATURE_DRY_RUN_PASS: layout maduro + carousel + 20+12 + bridge.")
    return 0


def apply_live() -> int:
    require_target()
    service = criar_servico_blogger()
    post, page = load_targets(service)
    mature = build_mature_html(service)
    service.posts().update(
        blogId=BLOG_ID,
        postId=POST_ID,
        body={"title": "Loja", "content": mature, "labels": ["Loja"]},
    ).execute()

    if get_live_post(service) is None:
        service.posts().publish(blogId=BLOG_ID, postId=POST_ID).execute()

    service.pages().update(
        blogId=BLOG_ID,
        pageId=PAGE_ID,
        body={"title": page.get("title") or "LOJA", "content": bridge_html()},
    ).execute()
    return verify_api()


def verify_api() -> int:
    require_target()
    service = criar_servico_blogger()
    _, page = load_targets(service)
    post = get_live_post(service)
    if post is None:
        raise RuntimeError("Store Post não aparece na lista LIVE.")
    if "loja" not in [str(x).casefold() for x in (post.get("labels") or [])]:
        raise RuntimeError(f"Store Post sem label Loja: {post.get('labels')!r}")
    verify_visual_contract(str(post.get("content") or ""))
    page_raw = str(page.get("content") or "")
    if POST_URL not in page_raw or "window.location.replace" not in page_raw:
        raise RuntimeError("Page LOJA não redireciona para o Store Post.")
    if "data-item-id=" in page_raw or "data-hero-item-id=" in page_raw:
        raise RuntimeError("Page LOJA ainda contém a vitrine em vez da bridge.")
    print("CASA_PRATICA_LAB_MATURE_API_PASS: Store Post LIVE + label Loja + carousel; Page redirect.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["dry-run", "apply-live", "verify"])
    args = parser.parse_args()
    return {"dry-run": dry_run, "apply-live": apply_live, "verify": verify_api}[args.command]()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"CASA_PRATICA_LAB_MATURE_CONTRACT_FAILED: {exc}", file=sys.stderr)
        raise
