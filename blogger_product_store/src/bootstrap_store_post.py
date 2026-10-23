#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from criar_rascunho import criar_servico_blogger  # noqa: E402

BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "5271798990390532475").strip()
SOURCE_PAGE_ID = os.getenv("BLOGGER_STORE_SOURCE_PAGE_ID", "5473313787015756722").strip()


def main() -> None:
    blogger = criar_servico_blogger()
    posts = blogger.posts().list(blogId=BLOG_ID, maxResults=100, status=["live"]).execute().get("items", [])
    existing = [p for p in posts if str(p.get("title") or "").strip().lower() == "loja"]
    if existing:
        post = existing[0]
        print(f"STORE_POST_EXISTS id={post.get('id')} url={post.get('url')}")
        return

    page = blogger.pages().get(blogId=BLOG_ID, pageId=SOURCE_PAGE_ID).execute()
    content = str(page.get("content") or "")
    if "BLOGGER_LIQ_STORE_AUTO_START" not in content or "BLOGGER_LIQ_HERO_AUTO_1_START" not in content:
        raise RuntimeError("Página fonte não contém os marcadores esperados; post não criado.")

    post = blogger.posts().insert(
        blogId=BLOG_ID,
        isDraft=False,
        body={"title": "Loja", "content": content, "labels": ["Loja"]},
    ).execute()
    print(f"STORE_POST_CREATED id={post.get('id')} url={post.get('url')}")


if __name__ == "__main__":
    main()
