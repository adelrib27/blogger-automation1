#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from criar_rascunho import criar_servico_blogger  # noqa: E402

BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "9144338307944682868").strip()
POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "115613719594316807").strip()
START = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_START -->"
END = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_END -->"

BLOCK = f'''{START}
<style id="blogger-liq-layout-wide-css">
.post-body{{overflow:visible!important}}
body:has(.bls-page) .post-outer-container:has(.bls-page),body:has(.bls-page) .post-outer:has(.bls-page),body:has(.bls-page) .post:has(.bls-page),body:has(.bls-page) .post-body-container:has(.bls-page){{background:transparent!important;border:0!important;box-shadow:none!important;overflow:visible!important;padding-top:0!important;padding-bottom:0!important;margin-top:0!important;margin-bottom:0!important}}
body:has(.bls-page) .post:has(.bls-page) .post-header,body:has(.bls-page) .post:has(.bls-page) .post-title,body:has(.bls-page) .post:has(.bls-page) .entry-title{{display:none!important}}
body:has(.bls-page) .post-body:has(.bls-page){{margin:0!important;padding:0!important;overflow:visible!important}}
.bls-page{{width:min(1440px,calc(100vw - 48px))!important;max-width:none!important;position:relative!important;left:50%!important;transform:translateX(-50%)!important;margin-top:32px!important;margin-bottom:0!important}}
@media(max-width:700px){{.bls-page{{width:calc(100vw - 16px)!important;margin-top:16px!important}}}}
</style>
<script id="blogger-liq-header-loja-link">
document.addEventListener('DOMContentLoaded',function(){{const store='https://vitrine-pratica.blogspot.com/p/loja.html';const about=[...document.querySelectorAll('a[href$="/p/sobre.html"]')].find(a=>a.getBoundingClientRect().top<180);if(!about||!about.parentNode)return;const same=[...about.parentNode.querySelectorAll('a')].some(a=>/\/p\/loja\.html(?:$|[?#])/.test(a.href));if(same)return;const link=about.cloneNode(false);link.href=store;link.textContent='Loja';link.removeAttribute('aria-current');about.parentNode.insertBefore(link,about)}});
</script>
{END}'''


def patch_store_layout() -> None:
    if not BLOG_ID or not POST_ID:
        raise RuntimeError("BLOGGER_BLOG_ID/BLOGGER_STORE_POST_ID ausente.")
    blogger = criar_servico_blogger()
    post = blogger.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    raw = str(post.get("content") or "")
    if "BLOGGER_LIQ_STORE_AUTO_START" not in raw or "BLOGGER_LIQ_HERO_AUTO_1_START" not in raw:
        raise RuntimeError("Post Loja sem marcadores esperados; layout preservado.")
    start_count, end_count = raw.count(START), raw.count(END)
    if start_count or end_count:
        if start_count != 1 or end_count != 1:
            raise RuntimeError("Marcadores do layout inconsistentes; post preservado.")
        a, b = raw.find(START), raw.find(END)
        if b <= a:
            raise RuntimeError("Ordem inválida dos marcadores do layout; post preservado.")
        updated = raw[:a] + BLOCK + raw[b + len(END):]
    else:
        updated = BLOCK + "\n" + raw
    if updated == raw:
        print("LAYOUT_WIDE_ALREADY_OK")
        return
    body = {"title": post.get("title") or "Loja", "content": updated}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    blogger.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = blogger.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_raw = str(verify.get("content") or "")
    for marker in (START, END, "BLOGGER_LIQ_STORE_AUTO_START", "BLOGGER_LIQ_HERO_AUTO_1_START"):
        if marker not in verify_raw:
            raise RuntimeError(f"Falha na verificação do layout; ausente={marker}")
    print("LAYOUT_WIDE_APPLIED")


if __name__ == "__main__":
    patch_store_layout()
