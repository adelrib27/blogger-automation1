#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from urllib.parse import urlparse

from criar_rascunho import criar_servico_blogger

SHARE_START = "<!-- BLOGGER_STORE_SHARE_CARD_START -->"
SHARE_END = "<!-- BLOGGER_STORE_SHARE_CARD_END -->"
SHARE_REGION_RE = re.compile(
    re.escape(SHARE_START) + r".*?" + re.escape(SHARE_END),
    re.S,
)


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def env_target() -> tuple[str, str, str]:
    blog_id = required_env("BLOGGER_BLOG_ID")
    page_id = required_env("BLOGGER_STORE_PAGE_ID")
    page_url = required_env("BLOGGER_STORE_PAGE_URL")
    if not (blog_id.isdigit() and page_id.isdigit()):
        raise RuntimeError("Blog/Page IDs precisam ser numéricos.")
    parsed = urlparse(page_url)
    if parsed.scheme != "https" or parsed.path != "/p/loja.html":
        raise RuntimeError(f"BLOGGER_STORE_PAGE_URL inválida: {page_url}")
    return blog_id, page_id, page_url


def share_card_html(page_url: str) -> str:
    canonical = html.escape(page_url, quote=True)
    js_url = json.dumps(page_url, ensure_ascii=False)
    return f'''{SHARE_START}
<style id="blogger-store-share-card-css">
#blogger-store-share-card{{box-sizing:border-box;width:min(1440px,calc(100vw - 48px));margin:16px auto 8px;display:flex;align-items:center;gap:10px;position:relative;z-index:4}}
#blogger-store-share-button{{appearance:none;-webkit-appearance:none;border:1px solid #dce4ee;background:#fff;margin:0;padding:10px 14px;display:inline-flex;align-items:center;justify-content:center;gap:8px;border-radius:14px;cursor:pointer;line-height:1;color:#729c0b;box-shadow:0 8px 24px rgba(23,32,51,.06);font:600 13px/1.2 Arial,Helvetica,sans-serif;white-space:nowrap}}
#blogger-store-share-button:hover,#blogger-store-share-button:focus-visible{{background:#f8faf7;border-color:#cbd8b4;outline:none;box-shadow:0 10px 28px rgba(23,32,51,.09)}}
#blogger-store-share-button svg{{display:block;width:20px;height:20px;fill:currentColor;flex:0 0 auto}}
#blogger-store-share-button .blogger-store-share-label{{color:#334155;line-height:1.2}}
#blogger-store-share-feedback{{color:#64748b;font:600 12px/1.4 Arial,Helvetica,sans-serif;min-height:17px}}
@media(max-width:700px){{#blogger-store-share-card{{width:calc(100vw - 16px);margin:10px auto 6px}}#blogger-store-share-button{{padding:9px 12px;border-radius:12px;font-size:12px}}#blogger-store-share-button svg{{width:19px;height:19px}}}}
</style>
<section id="blogger-store-share-card" aria-label="Compartilhar esta loja" data-blogger-store-share-card="1" data-share-compact="1">
  <button id="blogger-store-share-button" type="button" aria-label="Compartilhar" title="Compartilhar esta loja" data-share-url="{canonical}">
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M18 16.08c-.76 0-1.44.30-1.96.77L8.91 12.7a3.27 3.27 0 0 0 0-1.39l7.05-4.11A2.99 2.99 0 1 0 15 5c0 .23.03.45.08.66L8.03 9.77A3 3 0 1 0 8.03 14.23l7.12 4.16c-.04.20-.07.41-.07.61a2.92 2.92 0 1 0 2.92-2.92Z"/></svg>
    <span class="blogger-store-share-label">Compartilhar esta loja</span>
  </button>
  <span id="blogger-store-share-feedback" role="status" aria-live="polite"></span>
</section>
<script id="blogger-store-share-card-js">
(function(){{
  const button=document.getElementById('blogger-store-share-button');
  const feedback=document.getElementById('blogger-store-share-feedback');
  if(!button)return;
  const canonical={js_url};
  function message(text){{if(!feedback)return;feedback.textContent=text;window.setTimeout(()=>{{if(feedback.textContent===text)feedback.textContent='';}},2500);}}
  async function copyUrl(){{
    try{{
      if(navigator.clipboard&&window.isSecureContext){{await navigator.clipboard.writeText(canonical);message('Link copiado');return;}}
      const input=document.createElement('textarea');input.value=canonical;input.setAttribute('readonly','');input.style.position='fixed';input.style.opacity='0';document.body.appendChild(input);input.select();document.execCommand('copy');input.remove();message('Link copiado');
    }}catch(_err){{message('Copie o endereço da página para compartilhar');}}
  }}
  button.addEventListener('click',async function(){{
    try{{
      if(navigator.share){{await navigator.share({{title:document.title,url:canonical}});return;}}
    }}catch(err){{if(err&&err.name==='AbortError')return;}}
    await copyUrl();
  }});
}})();
</script>
{SHARE_END}'''


def inject_share_card(raw: str, page_url: str) -> str:
    raw = SHARE_REGION_RE.sub("", raw).strip()
    anchor = '<div class="bls-page">'
    if raw.count(anchor) != 1:
        raise RuntimeError(f"Esperado exatamente 1 início .bls-page; encontrados={raw.count(anchor)}")
    return raw.replace(anchor, share_card_html(page_url) + "\n" + anchor, 1)


def verify_share_card(raw: str, page_url: str) -> None:
    required = [
        SHARE_START,
        SHARE_END,
        'id="blogger-store-share-card"',
        'data-blogger-store-share-card="1"',
        'data-share-compact="1"',
        'id="blogger-store-share-button"',
        'aria-label="Compartilhar"',
        'class="blogger-store-share-label"',
        "Compartilhar esta loja",
        'id="blogger-store-share-card-css"',
        'id="blogger-store-share-card-js"',
        "navigator.share",
        "navigator.clipboard",
        "width:min(1440px,calc(100vw - 48px))",
        "padding:10px 14px",
        "#729c0b",
        page_url,
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Cartão de compartilhamento compacto incompleto: {missing}")
    forbidden = ["min-height:128px", "width:min(890px", "padding:32px"]
    present = [token for token in forbidden if token in raw]
    if present:
        raise RuntimeError(f"Estilo legado gigante do share card reapareceu: {present}")
    if raw.count('id="blogger-store-share-card"') != 1:
        raise RuntimeError("Cartão de compartilhamento duplicado.")
    if raw.find('id="blogger-store-share-card"') > raw.find('<div class="bls-page">'):
        raise RuntimeError("Cartão de compartilhamento precisa ficar antes da vitrine .bls-page.")


def load_page():
    blog_id, page_id, page_url = env_target()
    service = criar_servico_blogger()
    page = service.pages().get(blogId=blog_id, pageId=page_id).execute()
    if str(page.get("title") or "").strip().casefold() != "loja":
        raise RuntimeError(f"Page LOJA inesperada: {page.get('title')!r}")
    if str(page.get("url") or "").rstrip("/") != page_url.rstrip("/"):
        raise RuntimeError(f"URL da Page LOJA diverge: {page.get('url')!r}")
    return service, page, blog_id, page_id, page_url


def apply(dry_run: bool) -> int:
    service, page, blog_id, page_id, page_url = load_page()
    raw = str(page.get("content") or "")
    new_raw = inject_share_card(raw, page_url)
    verify_share_card(new_raw, page_url)
    if dry_run:
        print("BLOGGER_STORE_SHARE_CARD_DRY_RUN_PASS: share compacto branco + ícone verde validado em memória.")
        return 0
    service.pages().update(
        blogId=blog_id,
        pageId=page_id,
        body={"title": page.get("title") or "LOJA", "content": new_raw},
    ).execute()
    verify = service.pages().get(blogId=blog_id, pageId=page_id).execute()
    verify_share_card(str(verify.get("content") or ""), page_url)
    print("BLOGGER_STORE_SHARE_CARD_LIVE_PASS: share compacto aplicado e relido na Page LOJA.")
    return 0


def verify() -> int:
    _, page, _, _, page_url = load_page()
    verify_share_card(str(page.get("content") or ""), page_url)
    print("BLOGGER_STORE_SHARE_CARD_VERIFY_PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["dry-run", "live", "verify"])
    args = parser.parse_args()
    return {
        "dry-run": lambda: apply(True),
        "live": lambda: apply(False),
        "verify": verify,
    }[args.command]()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"BLOGGER_STORE_SHARE_CARD_FAILED: {exc}", file=sys.stderr)
        raise
