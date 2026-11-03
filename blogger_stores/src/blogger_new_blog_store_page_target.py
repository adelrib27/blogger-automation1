#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from urllib.parse import urlparse

from googleapiclient.errors import HttpError

from blogger_policy_guard import require_store_html_allowed
from blogger_store_share_card import inject_share_card, verify_share_card
from criar_rascunho import criar_servico_blogger

PAGE_COMPAT_START = "<!-- BLOGGER_STORE_AUTO_START -->"
PAGE_COMPAT_END = "<!-- BLOGGER_STORE_AUTO_END -->"
PAGE_THEME_FRAME_MARKER = "<!-- BLOGGER_NEW_STORE_PAGE_THEME_FRAME_PRESERVED -->"
LAYOUT_PATCH_START = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_START -->"
LAYOUT_PATCH_END = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_END -->"

# O Blogger pode recriar a Page depois de um clique. O índice é global e reaplicado
# a todas as cópias do carousel, de modo que nenhum clone volte sozinho ao slide 0.
PAGE_CAROUSEL_FIX = r'''<script id="blogger-new-store-page-carousel-fix">
(function(){
  let currentIndex=0;
  function roots(){return [...document.querySelectorAll('.bls-slider')];}
  function slides(root){return root?[...root.querySelectorAll('.bls-slide')]:[];}
  function dots(root){return root?[...root.querySelectorAll('#blsDots button')]:[];}
  function valid(root){return slides(root).length===3&&dots(root).length===3;}
  function paint(root,index){
    const ss=slides(root),ds=dots(root);
    if(ss.length!==3||ds.length!==3)return;
    ss.forEach((s,j)=>s.classList.toggle('is-active',j===index));
    ds.forEach((d,j)=>d.classList.toggle('is-active',j===index));
    root.dataset.pageCarouselDelegated='1';
    root.dataset.pageCarouselActive=String(index);
  }
  function apply(index){
    currentIndex=((index%3)+3)%3;
    roots().filter(valid).forEach(root=>paint(root,currentIndex));
  }
  function init(){apply(currentIndex);}
  document.addEventListener('click',function(event){
    const target=event.target instanceof Element?event.target:null;
    if(!target)return;
    const next=target.closest('.bls-next');
    const prev=target.closest('.bls-prev');
    const dot=target.closest('#blsDots button');
    const control=next||prev||dot;
    if(!control||!control.closest('.bls-slider'))return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if(next){apply(currentIndex+1);return;}
    if(prev){apply(currentIndex-1);return;}
    const root=control.closest('.bls-slider');
    apply(dots(root).indexOf(dot));
  },true);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
  const observer=new MutationObserver(init);observer.observe(document.documentElement,{childList:true,subtree:true});setTimeout(()=>observer.disconnect(),15000);
  if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){setInterval(()=>{if(roots().some(root=>{const r=root.getBoundingClientRect();return r.width>0&&r.height>0;}))apply(currentIndex+1);},6000);}
})();
</script>'''

LEGACY_CAROUSEL_RE = re.compile(
    r"<script>\s*document\.addEventListener\('DOMContentLoaded',function\(\)\{const root=document\.getElementById\('blsSlider'\).*?</script>",
    re.S,
)
LAYOUT_PATCH_RE = re.compile(
    re.escape(LAYOUT_PATCH_START) + r".*?" + re.escape(LAYOUT_PATCH_END) + r"\s*",
    re.S,
)

# Estes tokens foram usados pelo laboratório para criar uma superfície "clean/full-width".
# Eles são incompatíveis com o padrão visual V20 já validado, que preserva fundo decorativo
# e o enquadramento/card do tema. Qualquer reaparecimento deve falhar fechado.
FORBIDDEN_THEME_STRIPPING = [
    'id="blogger-new-store-page-surface-fix"',
    '.bg-photo-container{display:none!important',
    '.bg-photo{display:none!important',
    'background:transparent!important;border:0!important;box-shadow:none!important',
]


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


def strip_legacy_layout_patch(raw: str) -> str:
    starts = raw.count(LAYOUT_PATCH_START)
    ends = raw.count(LAYOUT_PATCH_END)
    if starts == 0 and ends == 0:
        return raw
    if starts != 1 or ends != 1:
        raise RuntimeError(
            f"Patch legado de layout inconsistente: start={starts} end={ends}."
        )
    cleaned, count = LAYOUT_PATCH_RE.subn("", raw, count=1)
    if count != 1 or LAYOUT_PATCH_START in cleaned or LAYOUT_PATCH_END in cleaned:
        raise RuntimeError("Patch legado de layout não pôde ser removido de forma determinística.")
    return cleaned


def pageify_store_html(raw: str, page_url: str) -> str:
    # A largura/no-sidebar da Loja pertence ao TEMA MODELO V20 (BLS Store nativa).
    # O adapter pode retirar o patch histórico durante migração, mas nunca o publica na Page final.
    clean = strip_legacy_layout_patch(raw)
    page_raw = strip_legacy_carousel(clean) + "\n" + PAGE_THEME_FRAME_MARKER + "\n" + PAGE_CAROUSEL_FIX
    page_raw = inject_share_card(page_raw, page_url)
    verify_share_card(page_raw, page_url)
    return page_raw


def verify_page_contract(raw: str, page_url: str) -> None:
    if raw.count(PAGE_COMPAT_START) != 1 or raw.count(PAGE_COMPAT_END) != 1:
        raise RuntimeError("Page LOJA perdeu BLOGGER_STORE_AUTO_START/END.")
    required = [
        PAGE_THEME_FRAME_MARKER,
        'id="blogger-new-store-page-carousel-fix"',
        "let currentIndex=0",
        "document.addEventListener('click'",
        "closest('.bls-next')",
        "closest('.bls-prev')",
        "event.stopImmediatePropagation()",
        "new MutationObserver",
        "pageCarouselDelegated",
        "apply(currentIndex+1)",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Controlador delegado/enquadramento V20 incompleto: {missing}")
    stripped = [token for token in FORBIDDEN_THEME_STRIPPING if token in raw]
    if stripped:
        raise RuntimeError(f"Page LOJA está removendo o enquadramento visual do Tema V20: {stripped}")
    if LAYOUT_PATCH_START in raw or LAYOUT_PATCH_END in raw:
        raise RuntimeError("Page LOJA contém BLOGGER_LIQ_LAYOUT_PATCH; layout deve pertencer ao Tema V20.")
    if "document.getElementById('blsSlider')" in raw:
        raise RuntimeError("Page LOJA contém o controlador legado do carousel.")
    verify_store_html(raw, page_url)
    verify_share_card(raw, page_url)


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
    page_raw = PAGE_COMPAT_START + "\n" + pageify_store_html(raw, page_url) + "\n" + PAGE_COMPAT_END
    verify_page_contract(page_raw, page_url)
    if dry_run:
        print("BLOGGER_NEW_STORE_PAGE_MATURE_DRY_RUN_PASS: 20+12 + layout nativo Tema V20 + carousel + share compacto; Blogger não alterado.")
        return 0
    service.pages().update(
        blogId=blog_id,
        pageId=page_id,
        body={"title": page.get("title") or "LOJA", "content": page_raw},
    ).execute()
    verify = service.pages().get(blogId=blog_id, pageId=page_id).execute()
    verify_page_contract(str(verify.get("content") or ""), page_url)
    print("BLOGGER_NEW_STORE_PAGE_MATURE_SYNC_PASS: /p/loja.html = 20+12 + layout nativo Tema V20 + carousel + share compacto.")
    return 0


def ensure_store_post_draft() -> int:
    service, post, _, blog_id, _, post_id, page_url = load_targets()
    if str((post or {}).get("status") or "").strip().lower() != "draft":
        service.posts().revert(blogId=blog_id, postId=post_id).execute()
    verify = get_post_any_status(service, blog_id, post_id)
    if str(verify.get("status") or "").strip().lower() != "draft":
        raise RuntimeError(f"Store Post técnico continua publicado: {verify.get('status')!r}")

    raw = str(verify.get("content") or "")
    clean = strip_legacy_layout_patch(raw)
    if clean != raw:
        body = {"title": verify.get("title") or "Loja", "content": clean}
        if verify.get("labels") is not None:
            body["labels"] = verify.get("labels")
        service.posts().update(blogId=blog_id, postId=post_id, body=body).execute()
        verify = get_post_any_status(service, blog_id, post_id)
        if str(verify.get("status") or "").strip().lower() != "draft":
            raise RuntimeError("Store Post técnico deixou de ser DRAFT ao remover patch legado de layout.")

    verify_raw = str(verify.get("content") or "")
    if LAYOUT_PATCH_START in verify_raw or LAYOUT_PATCH_END in verify_raw:
        raise RuntimeError("Store Post staging ainda contém BLOGGER_LIQ_LAYOUT_PATCH.")
    verify_store_html(verify_raw, page_url)
    print("BLOGGER_NEW_STORE_POST_STAGING_PASS: staging DRAFT, 20+12 e sem patch de layout; largura/sidebar pertencem ao Tema V20.")
    return 0


def verify_page() -> int:
    _, _, page, _, _, _, page_url = load_targets(require_post=False)
    verify_page_contract(str(page.get("content") or ""), page_url)
    print("BLOGGER_NEW_STORE_PAGE_MATURE_VERIFY_PASS: Page LOJA contém 20+12, layout nativo Tema V20, carousel e share compacto.")
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
