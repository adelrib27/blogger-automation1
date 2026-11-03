#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "blogger_stores" / "src"))

from blogger_new_blog_store_page_target import get_post_any_status  # noqa: E402
from blogger_policy_guard import require_store_html_allowed  # noqa: E402
from criar_rascunho import criar_servico_blogger  # noqa: E402

STYLE_START = "<!-- BLOGGER_STORE_INFO_PANEL_V20_START -->"
STYLE_END = "<!-- BLOGGER_STORE_INFO_PANEL_V20_END -->"
STYLE_ID = 'id="blogger-store-info-panel-v20"'

STYLE_BLOCK = r'''<!-- BLOGGER_STORE_INFO_PANEL_V20_START -->
<style id="blogger-store-info-panel-v20">
/* V20: transforma as antigas faixas escuras de confiança/aviso em um único painel claro e compacto. */
.bls-page .bls-trust{background:#fff!important;color:var(--deep,#111a24)!important;padding:8px 0 0!important}
.bls-page .bls-trust>.bls-shell{background:#f8fafc!important;border:1px solid #e2e8f0!important;border-bottom:0!important;border-radius:20px 20px 0 0!important;padding:18px 20px!important;box-shadow:0 10px 30px rgba(15,23,42,.05)!important}
.bls-page .bls-trust-grid{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:0!important}
.bls-page .bls-trust-item{min-width:0!important;padding:8px 20px!important;border-right:1px solid #e2e8f0!important;color:#0f172a!important}
.bls-page .bls-trust-item:last-child{border-right:0!important}
.bls-page .bls-trust-item strong{display:block!important;margin:0 0 6px!important;color:#0f172a!important;font-size:14px!important;line-height:1.25!important;font-weight:800!important}
.bls-page .bls-trust-item span{display:block!important;margin:0!important;color:#64748b!important;font-size:12px!important;line-height:1.55!important;font-weight:400!important}
.bls-page .bls-note{background:#fff!important;color:#0f172a!important;padding:0 0 28px!important}
.bls-page .bls-note>.bls-shell{background:#f8fafc!important;border:1px solid #e2e8f0!important;border-top:1px solid #e5e7eb!important;border-radius:0 0 20px 20px!important;padding:17px 20px 19px!important;box-shadow:0 10px 30px rgba(15,23,42,.05)!important}
.bls-page .bls-note h3{margin:0 0 7px!important;color:#0f172a!important;font-size:17px!important;line-height:1.35!important;font-weight:800!important;letter-spacing:0!important}
.bls-page .bls-note p{margin:0!important;max-width:none!important;color:#64748b!important;font-size:12px!important;line-height:1.65!important}
@media(max-width:860px){
  .bls-page .bls-trust-grid{grid-template-columns:1fr!important}
  .bls-page .bls-trust-item{padding:12px 4px!important;border-right:0!important;border-bottom:1px solid #e2e8f0!important}
  .bls-page .bls-trust-item:last-child{border-bottom:0!important}
}
@media(max-width:620px){
  .bls-page .bls-trust>.bls-shell,.bls-page .bls-note>.bls-shell{padding-left:15px!important;padding-right:15px!important}
  .bls-page .bls-note{padding-bottom:20px!important}
}
</style>
<!-- BLOGGER_STORE_INFO_PANEL_V20_END -->'''

CASA_LAB = {
    "title": "Casa Prática Lab",
    "blog_id": "8930870316690519385",
    "page_id": "7110845449177208439",
    "post_id": "7691087355641688975",
    "page_url": "https://casa-pratica-lab-20261102.blogspot.com/p/loja.html",
}
VIDA_PET = {
    "title": "Vida Pet Prática",
    "blog_id": "8052455848487624244",
    "page_id": "8624646966938350648",
    "post_id": "7332800716046515902",
    "page_url": "https://vida-pet-pratica.blogspot.com/p/loja.html",
}


def strip_old_panel_style(raw: str) -> str:
    while STYLE_START in raw or STYLE_END in raw:
        a = raw.find(STYLE_START)
        b = raw.find(STYLE_END)
        if a < 0 or b < 0 or b < a:
            raise RuntimeError("Marcadores do painel V20 estão corrompidos.")
        raw = raw[:a] + raw[b + len(STYLE_END):]
    return raw


def patch_html(raw: str) -> str:
    if 'class="bls-trust"' not in raw or 'class="bls-note"' not in raw:
        raise RuntimeError("Loja não contém os blocos .bls-trust e .bls-note esperados.")
    cleaned = strip_old_panel_style(raw).rstrip()
    return cleaned + "\n\n" + STYLE_BLOCK + "\n"


def verify_store(raw: str, *, require_page_marker: bool = False) -> None:
    require_store_html_allowed(raw, expected_products=20, expected_hero=12)
    if raw.count("data-item-id=") != 20:
        raise RuntimeError(f"Store != 20: {raw.count('data-item-id=')}")
    if raw.count("data-hero-item-id=") != 12:
        raise RuntimeError(f"Hero != 12: {raw.count('data-hero-item-id=')}")
    if raw.count('rel="nofollow sponsored noopener"') < 32:
        raise RuntimeError("Links patrocinados < 32.")
    if raw.count(STYLE_START) != 1 or raw.count(STYLE_END) != 1 or raw.count(STYLE_ID) != 1:
        raise RuntimeError("Painel informativo V20 ausente ou duplicado.")
    if 'background:#1e2b36!important' in raw or 'background:#0b1015!important' in raw:
        raise RuntimeError("Override escuro indevido detectado.")
    if require_page_marker and "BLOGGER_NEW_STORE_PAGE_THEME_FRAME_PRESERVED" not in raw:
        raise RuntimeError("Page-target perdeu o marcador de preservação do Tema V20.")


def list_post_ids(service, blog_id: str, status: str) -> set[str]:
    ids: set[str] = set()
    token = None
    while True:
        kwargs = {"blogId": blog_id, "status": status, "fetchBodies": False, "maxResults": 100}
        if token:
            kwargs["pageToken"] = token
        response = service.posts().list(**kwargs).execute()
        ids.update(str(x.get("id") or "") for x in (response.get("items") or []))
        token = response.get("nextPageToken")
        if not token:
            return ids


def public_fetch(url: str) -> str:
    last = ""
    for attempt in range(1, 7):
        p = urlsplit(url)
        q = dict(parse_qsl(p.query, keep_blank_values=True))
        q["v20_info_panel_probe"] = f"{int(time.time())}-{attempt}"
        target = urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))
        req = Request(target, headers={"User-Agent": "Mozilla/5.0 Chrome/156 Safari/537.36", "Cache-Control": "no-cache"})
        try:
            with urlopen(req, timeout=35) as r:
                if int(r.status) == 200:
                    return r.read().decode("utf-8", errors="ignore")
                last = f"HTTP {r.status}"
        except HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code not in (429, 500, 502, 503, 504):
                raise
        except URLError as exc:
            last = f"URL {exc.reason}"
        if attempt < 6:
            time.sleep(10 if "429" in last else 3)
    raise RuntimeError(f"Página pública sem HTTP 200: {url} ({last})")


def update_post_content(service, blog_id: str, post_id: str, raw: str, title: str, labels) -> None:
    body = {"title": title or "Loja", "content": raw}
    if labels is not None:
        body["labels"] = labels
    service.posts().update(blogId=blog_id, postId=post_id, body=body).execute()


def migrate_page_target(service, target: dict, *, lab: bool) -> None:
    blog_id = target["blog_id"]
    post_id = target["post_id"]
    page_id = target["page_id"]
    title = target["title"]
    print(f"TARGET_START | {title}")

    post = get_post_any_status(service, blog_id, post_id)
    post_raw = str(post.get("content") or "")
    post_patched = patch_html(post_raw)
    verify_store(post_patched)
    update_post_content(service, blog_id, post_id, post_patched, str(post.get("title") or "Loja"), post.get("labels"))
    if post_id not in list_post_ids(service, blog_id, "DRAFT"):
        raise RuntimeError(f"{title}: staging deixou de ser DRAFT.")
    verify_post = get_post_any_status(service, blog_id, post_id)
    verify_store(str(verify_post.get("content") or ""))

    page = service.pages().get(blogId=blog_id, pageId=page_id).execute()
    page_raw = str(page.get("content") or "")
    page_patched = patch_html(page_raw)
    verify_store(page_patched, require_page_marker=True)
    service.pages().update(blogId=blog_id, pageId=page_id, body={"title": page.get("title") or "LOJA", "content": page_patched}).execute()
    verify_page = service.pages().get(blogId=blog_id, pageId=page_id).execute()
    verify_store(str(verify_page.get("content") or ""), require_page_marker=True)

    public = public_fetch(target["page_url"])
    if "emporio-revisao-visual-20-modelo-final" not in public:
        raise RuntimeError(f"{title}: marcador público do Tema V20 ausente.")
    if lab and "Casa Prática Lab" not in public:
        raise RuntimeError("Casa Lab: identidade pública ausente.")
    print(f"TARGET_PASS | {title} | Page-target + staging DRAFT + painel V20 compacto")


def migrate_legacy(service, blog: dict, idx: int) -> None:
    title = str(blog.get("title") or "")
    blog_id = str(blog.get("blog_id") or "")
    post_id = str(blog.get("store_post_id") or "")
    page_url = str(blog.get("store_page_url") or "")
    if not (blog_id.isdigit() and post_id.isdigit() and page_url.startswith("https://")):
        raise RuntimeError(f"Inventário inválido em {title!r}.")
    print(f"TARGET_START | {idx:02d}/18 | {title}")

    if post_id not in list_post_ids(service, blog_id, "LIVE"):
        raise RuntimeError(f"{title}: Store Post não está LIVE antes da migração.")
    post = service.posts().get(blogId=blog_id, postId=post_id).execute()
    raw = str(post.get("content") or "")
    patched = patch_html(raw)
    verify_store(patched)
    update_post_content(service, blog_id, post_id, patched, str(post.get("title") or "Loja"), post.get("labels"))
    if post_id not in list_post_ids(service, blog_id, "LIVE"):
        raise RuntimeError(f"{title}: Store Post deixou de estar LIVE após a migração.")
    verify = service.posts().get(blogId=blog_id, postId=post_id).execute()
    verify_store(str(verify.get("content") or ""))

    public = public_fetch(page_url)
    if "emporio-revisao-visual-20-modelo-final" not in public:
        raise RuntimeError(f"{title}: Tema V20 público ausente.")
    if 'id="blogger-new-store-page-surface-fix"' in public:
        raise RuntimeError(f"{title}: surface-fix proibido detectado.")
    print(f"TARGET_PASS | {idx:02d}/18 | {title} | LIVE 20+12 + painel V20 compacto")


def run_lab() -> None:
    service = criar_servico_blogger()
    migrate_page_target(service, CASA_LAB, lab=True)
    print("BLOGGER_STORE_INFO_PANEL_V20_LAB_PASS")


def run_network() -> None:
    service = criar_servico_blogger()
    migrate_page_target(service, VIDA_PET, lab=False)
    inventory = json.loads((ROOT / "blogger_multi_store" / "data" / "NETWORK_STORE_INVENTORY_2026-11-02.json").read_text(encoding="utf-8"))
    blogs = inventory.get("blogs") or []
    if len(blogs) != 18:
        raise RuntimeError(f"Inventário legado inesperado: {len(blogs)}")
    for idx, blog in enumerate(blogs, 1):
        migrate_legacy(service, blog, idx)
    print("BLOGGER_STORE_INFO_PANEL_V20_NETWORK_PASS_19_19: Vida Pet + 18 legados atualizados; Casa Lab validado previamente em LAB.")


def main() -> int:
    scope = os.getenv("STORE_INFO_PANEL_SCOPE", "lab").strip().lower()
    if scope == "lab":
        run_lab()
        return 0
    if scope == "network":
        run_network()
        return 0
    raise RuntimeError(f"STORE_INFO_PANEL_SCOPE inválido: {scope!r}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"BLOGGER_STORE_INFO_PANEL_V20_FAILED: {exc}", file=sys.stderr)
        raise
