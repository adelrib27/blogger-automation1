#!/usr/bin/env python3
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from criar_rascunho import criar_servico_blogger

BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "4473989735719981382").strip()
POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "1410775502611365606").strip()
START = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_START -->"
END = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_END -->"

BLOCK = f'''{START}
<style id="blogger-liq-layout-wide-css">
.post-body{{overflow:visible!important}}
body.ga-post-page:has(.bls-page) .centered-bottom{{display:grid!important;grid-template-columns:minmax(0,1fr)!important;grid-template-rows:auto!important;gap:0!important;margin-left:auto!important;margin-right:auto!important}}
body.ga-post-page:has(.bls-page) .main-container{{grid-column:1!important;grid-area:1 / 1!important;width:100%!important;max-width:none!important;min-width:0!important;margin:0!important}}
body.ga-post-page:has(.bls-page) .sidebar-container,
body:has(.bls-page) .sidebar-container,
body:has(.bls-page) .sidebar-container-container,
body:has(.bls-page) .main-container aside{{display:none!important}}
body:has(.bls-page) .main-container,
body:has(.bls-page) .main,
body:has(.bls-page) .blog-posts,
body:has(.bls-page) .post-outer-container:has(.bls-page),
body:has(.bls-page) .post-outer:has(.bls-page),
body:has(.bls-page) .post:has(.bls-page),
body:has(.bls-page) .post-body-container:has(.bls-page){{width:100%!important;max-width:none!important}}
body:has(.bls-page) .post-outer-container:has(.bls-page),
body:has(.bls-page) .post-outer:has(.bls-page),
body:has(.bls-page) .post:has(.bls-page),
body:has(.bls-page) .post-body-container:has(.bls-page){{background:transparent!important;border:0!important;box-shadow:none!important;overflow:visible!important;padding-top:0!important;padding-bottom:0!important;margin-top:0!important;margin-bottom:0!important}}
body:has(.bls-page) .post:has(.bls-page) .post-header,
body:has(.bls-page) .post:has(.bls-page) .post-title,
body:has(.bls-page) .post:has(.bls-page) .entry-title{{display:none!important}}
body:has(.bls-page) .post-body:has(.bls-page){{width:100%!important;max-width:none!important;margin:0!important;padding:0!important;overflow:visible!important}}
body:has(.bls-page) .PopularPosts,
body:has(.bls-page) .widget.PopularPosts,
body:has(.bls-page) [id^="PopularPosts"]{{display:none!important}}
.bls-page{{width:min(1440px,calc(100vw - 48px))!important;max-width:none!important;position:relative!important;left:50%!important;transform:translateX(-50%)!important;margin-top:32px!important;margin-bottom:0!important}}
@media(max-width:700px){{body.ga-post-page:has(.bls-page) .centered-bottom{{display:block!important}}.bls-page{{width:calc(100vw - 16px)!important;margin-top:16px!important}}}}
</style>
<script id="blogger-liq-header-loja-link">
document.addEventListener('DOMContentLoaded',function(){{
  const store='https://ventiladores-em-foco.blogspot.com/p/loja.html';
  const about=[...document.querySelectorAll('a[href$="/p/sobre.html"]')].find(a=>a.getBoundingClientRect().top<180);
  if(!about||!about.parentNode)return;
  const same=[...about.parentNode.querySelectorAll('a')].some(a=>/\/p\/loja\.html(?:$|[?#])/.test(a.href));
  if(same)return;
  const link=about.cloneNode(false);link.href=store;link.textContent='Loja';link.removeAttribute('aria-current');about.parentNode.insertBefore(link,about);
}});
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
    sc, ec = raw.count(START), raw.count(END)
    if sc or ec:
        if sc != 1 or ec != 1:
            raise RuntimeError("Marcadores do layout inconsistentes; post preservado.")
        a, b = raw.find(START), raw.find(END)
        if b <= a:
            raise RuntimeError("Ordem inválida dos marcadores do layout; post preservado.")
        updated = raw[:a] + BLOCK + raw[b + len(END):]
    else:
        updated = BLOCK + "\n" + raw
    if updated != raw:
        body = {"title": post.get("title") or "Loja", "content": updated}
        if post.get("labels") is not None:
            body["labels"] = post.get("labels")
        blogger.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = str(blogger.posts().get(blogId=BLOG_ID, postId=POST_ID).execute().get("content") or "")
    required = (START, END, "BLOGGER_LIQ_STORE_AUTO_START", "BLOGGER_LIQ_HERO_AUTO_1_START", "https://ventiladores-em-foco.blogspot.com/p/loja.html", '[id^="PopularPosts"]', "grid-template-columns:minmax(0,1fr)!important")
    missing = [x for x in required if x not in verify]
    if missing:
        raise RuntimeError(f"Falha na verificação do layout; ausentes={missing}")
    print("LAYOUT_WIDE_APPLIED")
    print("STORE_TARGET_VENTILADORES_OK")
    print("POPULAR_POSTS_HIDDEN_ON_STORE_OK")
    print("STORE_VIEWPORT_CENTERED_OK")


if __name__ == "__main__":
    patch_store_layout()
