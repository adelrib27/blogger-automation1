#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from criar_rascunho import criar_servico_blogger  # noqa: E402

BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "5271798990390532475").strip()
POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "8867555367475283866").strip()

START = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_START -->"
END = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_END -->"

BLOCK = f'''{START}
<style id="blogger-liq-layout-wide-css">
.post-body{{overflow:visible!important}}
.bls-page{{
  width:min(1440px,calc(100vw - 48px))!important;
  max-width:none!important;
  position:relative!important;
  left:50%!important;
  transform:translateX(-50%)!important;
}}
@media(max-width:700px){{
  .bls-page{{
    width:calc(100vw - 16px)!important;
  }}
}}
</style>
{END}'''


def patch_store_layout() -> None:
    if not BLOG_ID or not POST_ID:
        raise RuntimeError("BLOGGER_BLOG_ID/BLOGGER_STORE_POST_ID ausente.")

    blogger = criar_servico_blogger()
    post = blogger.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    raw = str(post.get("content") or "")

    required_store_markers = ("BLOGGER_LIQ_STORE_AUTO_START", "BLOGGER_LIQ_HERO_AUTO_1_START")
    if any(marker not in raw for marker in required_store_markers):
        raise RuntimeError("Post Loja sem marcadores esperados; layout preservado.")

    start_count = raw.count(START)
    end_count = raw.count(END)
    if start_count or end_count:
        if start_count != 1 or end_count != 1:
            raise RuntimeError("Marcadores do layout inconsistentes; post preservado.")
        start = raw.find(START)
        end = raw.find(END)
        if end <= start:
            raise RuntimeError("Ordem inválida dos marcadores do layout; post preservado.")
        updated = raw[:start] + BLOCK + raw[end + len(END):]
    else:
        updated = BLOCK + "\n" + raw

    if updated == raw:
        print("LAYOUT_WIDE_ALREADY_OK")
        return

    body = {
        "title": post.get("title") or "Loja",
        "content": updated,
    }
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")

    blogger.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()

    verify = blogger.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_raw = str(verify.get("content") or "")
    required = (START, END, "BLOGGER_LIQ_STORE_AUTO_START", "BLOGGER_LIQ_HERO_AUTO_1_START")
    missing = [marker for marker in required if marker not in verify_raw]
    if missing:
        raise RuntimeError(f"Falha na verificação do layout; ausentes={missing}")

    print("LAYOUT_WIDE_APPLIED")


if __name__ == "__main__":
    patch_store_layout()
