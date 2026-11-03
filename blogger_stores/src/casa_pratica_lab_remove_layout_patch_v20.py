#!/usr/bin/env python3
from __future__ import annotations

import re
import sys

from blogger_new_blog_store_page_target import get_post_any_status, verify_page_contract
from blogger_policy_guard import require_store_html_allowed
from criar_rascunho import criar_servico_blogger

BLOG_ID = "8930870316690519385"
PAGE_ID = "7110845449177208439"
POST_ID = "7691087355641688975"
PAGE_URL = "https://casa-pratica-lab-20261102.blogspot.com/p/loja.html"
START = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_START -->"
END = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_END -->"
THEME_FRAME = "<!-- BLOGGER_NEW_STORE_PAGE_THEME_FRAME_PRESERVED -->"
INFO_PANEL = "<!-- BLOGGER_STORE_INFO_PANEL_V20_START -->"

REGION_RE = re.compile(
    re.escape(START) + r".*?" + re.escape(END) + r"\s*",
    re.S,
)


def validate_store(raw: str, *, page: bool) -> None:
    if START in raw or END in raw:
        raise RuntimeError("patch legado de layout ainda presente")
    if raw.count("data-item-id=") != 20:
        raise RuntimeError("Store precisa preservar exatamente 20 produtos")
    if raw.count("data-hero-item-id=") != 12:
        raise RuntimeError("Store precisa preservar exatamente 12 cards de hero")
    if raw.count('rel="nofollow sponsored noopener"') < 32:
        raise RuntimeError("links afiliados incompletos depois da remoção do patch")
    if INFO_PANEL not in raw:
        raise RuntimeError("painel informativo V20 compacto ausente")
    require_store_html_allowed(raw, expected_products=20, expected_hero=12)
    if page:
        if THEME_FRAME not in raw:
            raise RuntimeError("marcador de enquadramento do Tema V20 ausente")
        verify_page_contract(raw, PAGE_URL)


def strip_once(raw: str) -> str:
    if raw.count(START) != 1 or raw.count(END) != 1:
        raise RuntimeError(
            f"esperado um único patch legado; start={raw.count(START)} end={raw.count(END)}"
        )
    cleaned, count = REGION_RE.subn("", raw, count=1)
    if count != 1:
        raise RuntimeError(f"remoção do patch divergente: removidos={count}")
    return cleaned


def post_body(post: dict, content: str) -> dict:
    body = {"title": post.get("title") or "Loja", "content": content}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    return body


def main() -> int:
    service = criar_servico_blogger()
    page = service.pages().get(blogId=BLOG_ID, pageId=PAGE_ID).execute()
    post = get_post_any_status(service, BLOG_ID, POST_ID)

    if str(page.get("url") or "").rstrip("/") != PAGE_URL.rstrip("/"):
        raise RuntimeError(f"Page alvo divergente: {page.get('url')!r}")
    if str(page.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"Page inesperada: {page.get('title')!r}")
    if str(post.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"staging inesperado: {post.get('title')!r}")
    if str(post.get("status") or "").strip().lower() != "draft":
        raise RuntimeError(f"staging deve estar DRAFT antes da migração: {post.get('status')!r}")

    page_raw = str(page.get("content") or "")
    post_raw = str(post.get("content") or "")
    page_new = strip_once(page_raw)
    post_new = strip_once(post_raw)

    validate_store(page_new, page=True)
    validate_store(post_new, page=False)
    print("CASA_LAB_THEME_OWNED_LAYOUT_DRY_RUN_PASS: 20+12 preservados; patch legado removível em memória.")

    try:
        service.posts().update(
            blogId=BLOG_ID,
            postId=POST_ID,
            body=post_body(post, post_new),
        ).execute()
        post_verify = get_post_any_status(service, BLOG_ID, POST_ID)
        if str(post_verify.get("status") or "").strip().lower() != "draft":
            raise RuntimeError("staging deixou de ser DRAFT após update")
        validate_store(str(post_verify.get("content") or ""), page=False)

        service.pages().update(
            blogId=BLOG_ID,
            pageId=PAGE_ID,
            body={"title": page.get("title") or "LOJA", "content": page_new},
        ).execute()
        page_verify = service.pages().get(blogId=BLOG_ID, pageId=PAGE_ID).execute()
        if str(page_verify.get("url") or "").rstrip("/") != PAGE_URL.rstrip("/"):
            raise RuntimeError("URL canônica da Page mudou após update")
        validate_store(str(page_verify.get("content") or ""), page=True)
    except Exception:
        # Rollback best-effort dos dois objetos; falha continua fechada.
        try:
            service.posts().update(
                blogId=BLOG_ID,
                postId=POST_ID,
                body=post_body(post, post_raw),
            ).execute()
        except Exception as rollback_post:
            print(f"ROLLBACK_POST_WARNING: {rollback_post}", file=sys.stderr)
        try:
            service.pages().update(
                blogId=BLOG_ID,
                pageId=PAGE_ID,
                body={"title": page.get("title") or "LOJA", "content": page_raw},
            ).execute()
        except Exception as rollback_page:
            print(f"ROLLBACK_PAGE_WARNING: {rollback_page}", file=sys.stderr)
        raise

    print("CASA_LAB_THEME_OWNED_LAYOUT_LIVE_PASS: Page e staging sem BLOGGER_LIQ_LAYOUT_PATCH; staging DRAFT; 20+12 preservados.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"CASA_LAB_THEME_OWNED_LAYOUT_FAILED: {exc}", file=sys.stderr)
        raise
