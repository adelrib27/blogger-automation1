#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from urllib.parse import urlparse

from blogger_policy_guard import require_store_html_allowed
from criar_rascunho import criar_servico_blogger


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def env_target() -> tuple[str, str, str, str]:
    blog_id = required_env("BLOGGER_BLOG_ID")
    page_id = required_env("BLOGGER_STORE_PAGE_ID")
    post_id = required_env("BLOGGER_STORE_POST_ID")
    page_url = required_env("BLOGGER_STORE_PAGE_URL")
    if not (blog_id.isdigit() and page_id.isdigit() and post_id.isdigit()):
        raise RuntimeError("Blog/Page/Post IDs precisam ser numéricos.")
    parsed = urlparse(page_url)
    if parsed.scheme != "https" or parsed.path != "/p/loja.html":
        raise RuntimeError(f"BLOGGER_STORE_PAGE_URL inválida: {page_url}")
    return blog_id, page_id, post_id, page_url


def verify_store_html(raw: str, page_url: str) -> None:
    require_store_html_allowed(raw, expected_products=20, expected_hero=12)
    if raw.count("data-item-id=") != 20:
        raise RuntimeError("Page-target inválida: esperado exatamente 20 cards de Store.")
    if raw.count("data-hero-item-id=") != 12:
        raise RuntimeError("Page-target inválida: esperado exatamente 12 cards de hero.")
    if raw.count('rel="nofollow sponsored noopener"') < 32:
        raise RuntimeError("Page-target inválida: links afiliados incompletos.")
    if page_url not in raw:
        raise RuntimeError("Page-target inválida: URL canônica da LOJA não está presente no HTML.")


def load_targets():
    blog_id, page_id, post_id, page_url = env_target()
    service = criar_servico_blogger()
    post = service.posts().get(blogId=blog_id, postId=post_id).execute()
    page = service.pages().get(blogId=blog_id, pageId=page_id).execute()
    if str(post.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"Store Post inesperado: {post.get('title')!r}")
    if str(page.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"Page LOJA inesperada: {page.get('title')!r}")
    if str(page.get("url") or "").rstrip("/") != page_url.rstrip("/"):
        raise RuntimeError(f"URL da Page LOJA diverge: {page.get('url')!r}")
    return service, post, page, blog_id, page_id, post_id, page_url


def sync_page(dry_run: bool = False) -> int:
    service, post, page, blog_id, page_id, _, page_url = load_targets()
    raw = str(post.get("content") or "")
    verify_store_html(raw, page_url)
    if dry_run:
        print("BLOGGER_NEW_STORE_PAGE_DRY_RUN_PASS: Store Post staging 20+12 validado; Page não alterada.")
        return 0
    body = {"title": page.get("title") or "LOJA", "content": raw}
    service.pages().update(blogId=blog_id, pageId=page_id, body=body).execute()
    verify = service.pages().get(blogId=blog_id, pageId=page_id).execute()
    verify_store_html(str(verify.get("content") or ""), page_url)
    print("BLOGGER_NEW_STORE_PAGE_SYNC_PASS: /p/loja.html sincronizada com Store 20 + Hero 12.")
    return 0


def ensure_store_post_draft() -> int:
    service, post, _, blog_id, _, post_id, _ = load_targets()
    status = str(post.get("status") or "").strip().lower()
    if status != "draft":
        service.posts().revert(blogId=blog_id, postId=post_id).execute()
    verify = service.posts().get(blogId=blog_id, postId=post_id).execute()
    final_status = str(verify.get("status") or "").strip().lower()
    if final_status and final_status != "draft":
        raise RuntimeError(f"Store Post técnico continua publicado: status={final_status}")
    print("BLOGGER_NEW_STORE_POST_STAGING_PASS: Store Post técnico preservado fora da home (draft).")
    return 0


def verify_page() -> int:
    _, _, page, _, _, _, page_url = load_targets()
    verify_store_html(str(page.get("content") or ""), page_url)
    print("BLOGGER_NEW_STORE_PAGE_VERIFY_PASS: Page LOJA contém 20 Store + 12 Hero.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["sync-dry-run", "sync-live", "ensure-staging-draft", "verify-page"])
    args = parser.parse_args()
    return {
        "sync-dry-run": lambda: sync_page(True),
        "sync-live": lambda: sync_page(False),
        "ensure-staging-draft": ensure_store_post_draft,
        "verify-page": verify_page,
    }[args.command]()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"BLOGGER_NEW_STORE_PAGE_TARGET_FAILED: {exc}", file=sys.stderr)
        raise
