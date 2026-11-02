#!/usr/bin/env python3
from __future__ import annotations

import os

from blogger_new_blog_store_page_target import get_post_any_status
import casa_pratica_lab_store as lab

base = lab.base


def get_service_staging_post():
    env_blog = os.getenv("BLOGGER_BLOG_ID", lab.BLOG_ID).strip()
    env_post = os.getenv("BLOGGER_STORE_POST_ID", lab.POST_ID).strip()
    if env_blog != lab.BLOG_ID or env_post != lab.POST_ID:
        raise RuntimeError(f"Alvo Blogger incorreto: blog={env_blog} post={env_post}")
    service = base.criar_servico_blogger()
    post = get_post_any_status(service, lab.BLOG_ID, lab.POST_ID)
    if str(post.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"Store Post staging inesperado: {post.get('title')!r}")
    return service, post


# Isolado para o contrato de BLOG NOVO. A rede legada continua exigindo Store Post LIVE.
base.get_service_post = get_service_staging_post


if __name__ == "__main__":
    raise SystemExit(lab.main())
