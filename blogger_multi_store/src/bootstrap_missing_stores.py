#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(os.getenv('BLOGGER_MULTI_STORE_BOOTSTRAP_CONFIG', ROOT / 'blogger_multi_store' / 'config' / 'bootstrap_missing_stores.json'))
sys.path.insert(0, str(ROOT / 'src'))
from criar_rascunho import criar_servico_blogger  # noqa: E402


def render(store: dict) -> str:
    cards = []
    for p in store.get('products') or []:
        item_id = html.escape(str(p.get('item_id') or ''), quote=True)
        name = html.escape(str(p.get('name') or '').strip())
        offer = html.escape(str(p.get('offer') or '').strip(), quote=True)
        image = str(p.get('image') or '').strip()
        if not offer.startswith('http') or not name:
            raise RuntimeError(f"Produto-semente inválido em {store.get('slug')}")
        if image.startswith('http'):
            media = f'<a class="bms-img" href="{offer}" target="_blank" rel="nofollow sponsored noopener"><img src="{html.escape(image, quote=True)}" alt="{name}" loading="lazy" decoding="async"></a>'
        else:
            media = '<div class="bms-img bms-noimg"><span>Imagem disponível na oferta</span></div>'
        cards.append(
            f'<article class="bms-card" data-item-id="{item_id}">{media}<h3>{name}</h3>'
            f'<a class="bms-btn" href="{offer}" target="_blank" rel="nofollow sponsored noopener">Ver oferta na Shopee</a></article>'
        )
    if not cards:
        raise RuntimeError(f"Loja {store.get('slug')} sem produtos-semente")
    title = html.escape(str(store.get('title') or 'Loja'))
    intro = html.escape(str(store.get('intro') or 'Seleção de produtos com ofertas reais da Shopee.'))
    slug = html.escape(str(store.get('slug') or ''), quote=True)
    css = '.bms-wrap{max-width:1160px;margin:0 auto;font-family:Arial,sans-serif;color:#17212b}.bms-hero{padding:28px;border:1px solid #dfe7e2;border-radius:22px;background:#f6faf8;margin-bottom:20px}.bms-hero h2{margin:0 0 8px;font-size:31px}.bms-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.bms-card{border:1px solid #e4e7ec;border-radius:17px;background:#fff;padding:13px}.bms-img{display:flex;align-items:center;justify-content:center;aspect-ratio:1/1;border-radius:13px;overflow:hidden;background:#f7f7f5;color:#667085;text-align:center;font-size:12px}.bms-img img{width:100%;height:100%;object-fit:contain}.bms-card h3{font-size:14px;line-height:1.35;min-height:2.7em}.bms-btn{display:inline-block;margin-top:9px;padding:10px 12px;border-radius:8px;background:#0F8A5F;color:#fff!important;text-decoration:none;font-weight:700;font-size:13px}.bms-foot{margin-top:20px;color:#667085;font-size:12px}@media(max-width:900px){.bms-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:520px){.bms-grid{grid-template-columns:1fr}}'
    return (
        '<!-- BLOGGER_MULTI_STORE_AUTO_START -->'
        f'<style id="blogger-multi-store-css">{css}</style>'
        f'<div class="bms-wrap" data-store-v1="{slug}"><section class="bms-hero"><h2>{title}</h2><p>{intro}</p>'
        '<p><small><strong>Transparência:</strong> esta loja contém links de afiliado Shopee. Compras elegíveis podem gerar comissão para o site. Preços, estoque, frete, variantes e condições podem mudar; confirme sempre na oferta atual.</small></p></section>'
        f'<div class="bms-grid">{"".join(cards)}</div>'
        '<p class="bms-foot">Seleção inicial criada somente com ofertas reais previamente validadas no projeto. O conteúdo poderá ser substituído pelo motor autônomo de rotação após validação.</p></div>'
        '<!-- BLOGGER_MULTI_STORE_AUTO_END -->'
    )


def list_live_posts(blogger, blog_id: str) -> list[dict]:
    return blogger.posts().list(blogId=blog_id, maxResults=100, status=['LIVE']).execute().get('items', []) or []


def list_live_pages(blogger, blog_id: str) -> list[dict]:
    return blogger.pages().list(blogId=blog_id, maxResults=100, status=['LIVE']).execute().get('items', []) or []


def exact_loja(items: list[dict]) -> dict | None:
    for item in items:
        if str(item.get('title') or '').strip().lower() == 'loja':
            return item
    return None


def ensure_store(blogger, store: dict) -> dict:
    bid = str(store['blog_id'])
    slug = str(store.get('slug') or bid)
    post = exact_loja(list_live_posts(blogger, bid))
    created_post = False
    if not post:
        post = blogger.posts().insert(
            blogId=bid,
            isDraft=False,
            body={'title': 'Loja', 'content': render(store), 'labels': ['Loja']},
        ).execute()
        created_post = True
        time.sleep(1.2)
    post_id = str(post.get('id') or '')
    post_url = str(post.get('url') or '')
    if not post_id or not post_url.startswith('http'):
        raise RuntimeError(f'{slug}: post Loja sem id/url')

    verify_post = blogger.posts().get(blogId=bid, postId=post_id).execute()
    if str(verify_post.get('title') or '').strip().lower() != 'loja':
        raise RuntimeError(f'{slug}: validação do post Loja falhou')

    page = exact_loja(list_live_pages(blogger, bid))
    created_page = False
    if not page:
        redir = (
            f'<meta http-equiv="refresh" content="0;url={html.escape(post_url, quote=True)}">'
            f'<link rel="canonical" href="{html.escape(post_url, quote=True)}">'
            f'<p>Abrindo a <a href="{html.escape(post_url, quote=True)}">Loja</a>…</p>'
            f'<script>window.location.replace({json.dumps(post_url)});</script>'
        )
        page = blogger.pages().insert(
            blogId=bid,
            isDraft=False,
            body={'title': 'Loja', 'content': redir},
        ).execute()
        created_page = True
        time.sleep(1.2)
    page_id = str(page.get('id') or '')
    page_url = str(page.get('url') or '')
    if not page_id or not page_url.startswith('http'):
        raise RuntimeError(f'{slug}: página Loja sem id/url')
    verify_page = blogger.pages().get(blogId=bid, pageId=page_id).execute()
    if str(verify_page.get('title') or '').strip().lower() != 'loja':
        raise RuntimeError(f'{slug}: validação da página Loja falhou')

    return {
        'slug': slug,
        'blog_id': bid,
        'post_id': post_id,
        'post_url': post_url,
        'page_id': page_id,
        'page_url': page_url,
        'created_post': created_post,
        'created_page': created_page,
    }


def main() -> int:
    cfg = json.loads(CONFIG.read_text(encoding='utf-8'))
    stores = cfg.get('stores') or []
    if not stores:
        raise RuntimeError('Config sem lojas')
    blogger = criar_servico_blogger()
    results = []
    for store in stores:
        result = ensure_store(blogger, store)
        results.append(result)
        print('PASS', json.dumps(result, ensure_ascii=False))
        time.sleep(1.0)
    out = ROOT / 'blogger_multi_store' / 'data' / 'bootstrap_result.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'version': 1, 'results': results}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'BOOTSTRAP_MULTI_STORE_PASS stores={len(results)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
