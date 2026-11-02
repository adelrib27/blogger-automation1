#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from urllib.parse import urlparse

from googleapiclient.errors import HttpError

from blogger_policy_guard import require_store_html_allowed
from criar_rascunho import criar_servico_blogger

PAGE_COMPAT_START = "<!-- BLOGGER_STORE_AUTO_START -->"
PAGE_COMPAT_END = "<!-- BLOGGER_STORE_AUTO_END -->"

PAGE_SURFACE_FIX = r'''<style id="blogger-new-store-page-surface-fix">
body:has(.bls-page) .centered-bottom{display:grid!important;grid-template-columns:minmax(0,1fr)!important;grid-template-rows:auto!important;gap:0!important;margin-left:auto!important;margin-right:auto!important}
body:has(.bls-page) .main-container{grid-column:1!important;grid-area:1 / 1!important;width:100%!important;max-width:none!important;min-width:0!important;margin:0!important}
body:has(.bls-page) .sidebar-container,body:has(.bls-page) .sidebar-container-container,body:has(.bls-page) .main-container aside,body:has(.bls-page) .PopularPosts,body:has(.bls-page) .widget.PopularPosts,body:has(.bls-page) [id^="PopularPosts"]{display:none!important}
body:has(.bls-page) .main-container,body:has(.bls-page) .main,body:has(.bls-page) .blog-posts,body:has(.bls-page) .post-outer-container,body:has(.bls-page) .post-outer,body:has(.bls-page) .post,body:has(.bls-page) .post-body-container,body:has(.bls-page) .post-body{width:100%!important;max-width:none!important}
body:has(.bls-page) .post-outer-container,body:has(.bls-page) .post-outer,body:has(.bls-page) .post,body:has(.bls-page) .post-body-container{background:transparent!important;border:0!important;box-shadow:none!important;overflow:visible!important;padding-top:0!important;padding-bottom:0!important;margin-top:0!important;margin-bottom:0!important}
body:has(.bls-page) .post-title-container,body:has(.bls-page) .post-title,body:has(.bls-page) .entry-title,body:has(.bls-page) .post-header{display:none!important}
body:has(.bls-page) .post-body{margin:0!important;padding:0!important;overflow:visible!important}
body:has(.bls-page) .bls-page{width:min(1440px,calc(100vw - 48px))!important;max-width:none!important;position:relative!important;left:50%!important;transform:translateX(-50%)!important;margin-top:32px!important;margin-bottom:0!important}
@media(max-width:700px){body:has(.bls-page) .centered-bottom{display:block!important}body:has(.bls-page) .bls-page{width:calc(100vw - 16px)!important;margin-top:16px!important}}
</style>'''

# A Page do Blogger pode clonar/substituir o conteúdo depois que scripts inline já rodaram.
# Por isso o controlador é delegado no document e não fica preso a um nó específico.
PAGE_CAROUSEL_FIX = r'''<script id="blogger-new-store-page-carousel-fix">
(function(){
  function getRoot(node){return node&&node.closest?node.closest('.bls-slider'):null;}
  function getSlides(root){return root?[...root.querySelectorAll('.bls-slide')]:[];}
  function getDots(root){return root?[...root.querySelectorAll('#blsDots button')]:[];}
  function activeIndex(root){const slides=getSlides(root);const i=slides.findIndex(s=>s.classList.contains('is-active'));return i<0?0:i;}
  function show(root,n){
    const slides=getSlides(root),dots=getDots(root);
    if(slides.length!==3||dots.length!==3)return false;
    const i=(n+slides.length)%slides.length;
    slides.forEach((s,j)=>s.classList.toggle('is-active',j===i));
    dots.forEach((d,j)=>d.classList.toggle('is-active',j===i));
    root.dataset.pageCarouselActive=String(i);
    return true;
  }
  function move(root,delta){return show(root,activeIndex(root)+delta);}
  function init(){document.querySelectorAll('.bls-slider').forEach(root=>{if(getSlides(root).length===3&&getDots(root).length===3){show(root,activeIndex(root));root.dataset.pageCarouselDelegated='1';}});}
  document.addEventListener('click',function(event){
    const target=event.target instanceof Element?event.target:null;
    if(!target)return;
    const next=target.closest('.bls-next');
    const prev=target.closest('.bls-prev');
    const dot=target.closest('#blsDots button');
    const control=next||prev||dot;
    if(!control)return;
    const root=getRoot(control);
    if(!root)return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if(next){move(root,1);return;}
    if(prev){move(root,-1);return;}
    const dots=getDots(root);show(root,dots.indexOf(dot));
  },true);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
  const observer=new MutationObserver(init);observer.observe(document.documentElement,{childList:true,subtree:true});setTimeout(()=>observer.disconnect(),15000);
  if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){setInterval(()=>{document.querySelectorAll('.bls-slider').forEach(root=>{const r=root.getBoundingClientRect();if(r.width>0&&r.height>0)move(root,1);});},6000);}
})();
</script>'''

LEGACY_CAROUSEL_RE = re.compile(
    r"<script>\s*document\.addEventListener\('DOMContentLoaded',function\(\)\{const root=document\.getElementById\('blsSlider'\).*?</script>",
    re.S,
)


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


def _list_posts(service, blog_id: str, status: str) -> list[dict]:
    kwargs = {"blogId": blog_id, "status": status, "fetchBodies": True, "maxResults": 100}
    items: list[dict] = []
    while True:
        response = service.posts().list(**kwargs).execute()
        items.extend(response.get("items") or [])
        token = response.get("nextPageToken")
        if not token:
            return items
        kwargs["pageToken"] = token


def get_post_any_status(service, blog_id: str, post_id: str) -> dict:
    try:
        return service.posts().get(blogId=blog_id, postId=post_id).execute()
    except HttpError as exc:
        if getattr(exc, "resp", None) is None or int(exc.resp.status) != 404:
            raise
    for status in ("DRAFT", "SCHEDULED", "LIVE"):
        for item in _list_posts(service, blog_id, status):
            if str(item.get("id") or "") == post_id:
                return item
    raise RuntimeError(f"Store Post {post_id} não encontrado em LIVE/DRAFT/SCHEDULED.")


def verify_store_html(raw: str, page_url: str) -> None:
    require_store_html_allowed(raw, expected_products=20, expected_hero=12)
    if raw.count("data-item-id=") != 20:
        raise RuntimeError("Esperado exatamente 20 cards de Store.")
    if raw.count("data-hero-item-id=") != 12:
        raise RuntimeError("Esperado exatamente 12 cards de hero.")
    if raw.count('rel="nofollow sponsored noopener"') < 32:
        raise RuntimeError("Links afiliados incompletos.")
    if page_url not in raw:
        raise RuntimeError("URL canônica da LOJA ausente do HTML.")
    required = [
        'id="blsSlider"', 'class="bls-slide is-active"', ".bls-slide{display:none",
        ".bls-slide.is-active{display:grid", 'class="bls-nav bls-prev"',
        'class="bls-nav bls-next"', 'id="blsDots"',
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Contrato visual maduro incompleto: {missing}")


def strip_legacy_carousel(raw: str) -> str:
    cleaned, count = LEGACY_CAROUSEL_RE.subn("", raw)
    if count != 1:
        raise RuntimeError(f"Esperado remover 1 controlador legado; removidos={count}.")
    if "document.getElementById('blsSlider')" in cleaned:
        raise RuntimeError("Controlador legado do carousel ainda presente.")
    return cleaned


def pageify_store_html(raw: str) -> str:
    return PAGE_SURFACE_FIX + "\n" + strip_legacy_carousel(raw) + "\n" + PAGE_CAROUSEL_FIX


def verify_page_contract(raw: str, page_url: str) -> None:
    if raw.count(PAGE_COMPAT_START) != 1 or raw.count(PAGE_COMPAT_END) != 1:
        raise RuntimeError("Page LOJA perdeu BLOGGER_STORE_AUTO_START/END.")
    required = [
        'id="blogger-new-store-page-surface-fix"',
        'id="blogger-new-store-page-carousel-fix"',
        "document.addEventListener('click'",
        "closest('.bls-next')",
        "closest('.bls-prev')",
        "event.stopImmediatePropagation()",
        "new MutationObserver",
        "pageCarouselDelegated",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Controlador delegado incompleto: {missing}")
    if "document.getElementById('blsSlider')" in raw:
        raise RuntimeError("Page LOJA contém o controlador legado do carousel.")
    verify_store_html(raw, page_url)


def load_targets(require_post: bool = True):
    blog_id, page_id, post_id, page_url = env_target()
    service = criar_servico_blogger()
    post = get_post_any_status(service, blog_id, post_id) if require_post else None
    page = service.pages().get(blogId=blog_id, pageId=page_id).execute()
    if post is not None and str(post.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"Store Post inesperado: {post.get('title')!r}")
    if str(page.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"Page LOJA inesperada: {page.get('title')!r}")
    if str(page.get("url") or "").rstrip("/") != page_url.rstrip("/"):
        raise RuntimeError(f"URL da Page LOJA diverge: {page.get('url')!r}")
    return service, post, page, blog_id, page_id, post_id, page_url


def sync_page(dry_run: bool = False) -> int:
    service, post, page, blog_id, page_id, _, page_url = load_targets()
    raw = str((post or {}).get("content") or "")
    verify_store_html(raw, page_url)
    page_raw = PAGE_COMPAT_START + "\n" + pageify_store_html(raw) + "\n" + PAGE_COMPAT_END
    verify_page_contract(page_raw, page_url)
    if dry_run:
        print("BLOGGER_NEW_STORE_PAGE_MATURE_DRY_RUN_PASS: 20+12 + controlador delegado clone-safe; Blogger não alterado.")
        return 0
    service.pages().update(
        blogId=blog_id,
        pageId=page_id,
        body={"title": page.get("title") or "LOJA", "content": page_raw},
    ).execute()
    verify = service.pages().get(blogId=blog_id, pageId=page_id).execute()
    verify_page_contract(str(verify.get("content") or ""), page_url)
    print("BLOGGER_NEW_STORE_PAGE_MATURE_SYNC_PASS: /p/loja.html = 20+12 + layout amplo + carousel delegado clone-safe.")
    return 0


def ensure_store_post_draft() -> int:
    service, post, _, blog_id, _, post_id, _ = load_targets()
    if str((post or {}).get("status") or "").strip().lower() != "draft":
        service.posts().revert(blogId=blog_id, postId=post_id).execute()
    verify = get_post_any_status(service, blog_id, post_id)
    if str(verify.get("status") or "").strip().lower() != "draft":
        raise RuntimeError(f"Store Post técnico continua publicado: {verify.get('status')!r}")
    print("BLOGGER_NEW_STORE_POST_STAGING_PASS: Store Post técnico preservado fora da home (draft).")
    return 0


def verify_page() -> int:
    _, _, page, _, _, _, page_url = load_targets(require_post=False)
    verify_page_contract(str(page.get("content") or ""), page_url)
    print("BLOGGER_NEW_STORE_PAGE_MATURE_VERIFY_PASS: Page LOJA contém 20+12, layout amplo e carousel delegado.")
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
