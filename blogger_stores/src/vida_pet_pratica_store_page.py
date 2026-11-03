#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

from blogger_new_blog_store_page_target import get_post_any_status
import vida_pet_pratica_store as pet

base = pet.base


def get_service_staging_post():
    env_blog = os.getenv("BLOGGER_BLOG_ID", pet.BLOG_ID).strip()
    env_post = os.getenv("BLOGGER_STORE_POST_ID", pet.POST_ID).strip()
    if env_blog != pet.BLOG_ID or env_post != pet.POST_ID:
        raise RuntimeError(f"Alvo Blogger incorreto: blog={env_blog} post={env_post}")
    service = base.criar_servico_blogger()
    post = get_post_any_status(service, pet.BLOG_ID, pet.POST_ID)
    if str(post.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"Store Post staging inesperado: {post.get('title')!r}")
    return service, post


def update_staging(service, post: dict, content: str) -> dict:
    body = {"title": post.get("title") or "Loja", "content": content}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=pet.BLOG_ID, postId=pet.POST_ID, body=body).execute()
    return get_post_any_status(service, pet.BLOG_ID, pet.POST_ID)


def identity_write(dry_run: bool) -> int:
    service, post = get_service_staging_post()
    raw = str(post.get("content") or "")
    new_raw = pet.transform_identity(raw)
    pet.verify_identity(new_raw)
    if dry_run:
        print("VIDA_PET_PRATICA_IDENTITY_DRY_RUN_PASS: staging DRAFT validado em memória.")
        return 0
    verify = update_staging(service, post, new_raw)
    pet.verify_identity(str(verify.get("content") or ""))
    print("VIDA_PET_PRATICA_IDENTITY_PASS: staging DRAFT relido com identidade pet correta.")
    return 0


def store_write(dry_run: bool) -> int:
    data = base.load_json(pet.SELECTION_PATH, {})
    base.validate_selection(data)
    service, post = get_service_staging_post()
    raw = str(post.get("content") or "")
    new_raw = base.replace_region(raw, base.STORE_START, base.STORE_END, pet.render_store(data))
    base.verify_store_html(new_raw, data)
    if dry_run:
        print("VIDA_PET_PRATICA_STORE_DRY_RUN_PASS: 20 produtos validados no staging DRAFT; Blogger não alterado.")
        return 0
    verify = update_staging(service, post, new_raw)
    base.verify_store_html(str(verify.get("content") or ""), data)
    print("VIDA_PET_PRATICA_POST_STAGING_PASS: 20 produtos gravados e relidos no staging DRAFT.")
    return 0


def hero_write(dry_run: bool) -> int:
    data = base.load_json(pet.SELECTION_PATH, {})
    base.validate_selection(data)
    slides = pet.build_hero(data)
    service, post = get_service_staging_post()
    raw = str(post.get("content") or "")
    new_raw = raw
    if dry_run:
        new_raw = base.replace_region(new_raw, base.STORE_START, base.STORE_END, pet.render_store(data))
    for (start, end), slide in zip(base.HERO_MARKERS, slides):
        new_raw = base.replace_region(new_raw, start, end, slide)
    base.verify_store_html(new_raw, data)
    base.verify_hero(new_raw, slides)
    if dry_run:
        print("VIDA_PET_PRATICA_FIRST_PUBLISH_COMBINED_DRY_RUN_PASS: Store 20 + Hero 12 simulados; gate 32 rels preservado.")
        return 0
    verify = update_staging(service, post, new_raw)
    verify_raw = str(verify.get("content") or "")
    base.verify_store_html(verify_raw, data)
    base.verify_hero(verify_raw, slides)
    print("VIDA_PET_PRATICA_HERO_STAGING_PASS: 12 mini-cards gravados e relidos no staging DRAFT.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["safe", "validate", "identity-dry-run", "identity-live", "identity", "store-dry-run", "store-live", "hero-dry-run", "hero-live", "persist"])
    args = parser.parse_args()
    return {
        "safe": pet.safe_scan,
        "validate": pet.validate_only,
        "identity-dry-run": lambda: identity_write(True),
        "identity-live": lambda: identity_write(False),
        "identity": lambda: identity_write(True),
        "store-dry-run": lambda: store_write(True),
        "store-live": lambda: store_write(False),
        "hero-dry-run": lambda: hero_write(True),
        "hero-live": lambda: hero_write(False),
        "persist": pet.persist,
    }[args.command]()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VIDA_PET_PRATICA_PAGE_ENGINE_FAILED: {exc}", file=sys.stderr)
        raise
