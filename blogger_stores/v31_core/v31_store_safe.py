#!/usr/bin/env python3
"""V31 R1: pure, fail-closed daily Store rendering/patch planning.

NO Blogger/Shopee IO, credentials, workflow mutation or publication in this module.
Uses the validated Universal V31 page's 'ub-product-card' contract. Only the
content inside the explicitly provisioned marker pair is eligible for replacement.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit
import json
import re

AUTO_START = '<!-- UNIVERSAL_V31_STORE_AUTO_START -->'
AUTO_END = '<!-- UNIVERSAL_V31_STORE_AUTO_END -->'
PAGE_START = '<!-- UNIVERSAL_V31_PAGE_CONTRACT_START -->'
PAGE_END = '<!-- UNIVERSAL_V31_PAGE_CONTRACT_END -->'
SCHEMA = 'universal-v31-catalog-v1'
THEME_SHA256 = 'f020fa390e5b8dc67c717546eed52cb3006c228e77d3f0911005edeb77ce767c'
POLICY_TEXT = ('Aviso de afiliados: podemos receber comissão sem custo adicional para você. '
               'Preços e disponibilidade devem ser conferidos na loja de destino.')

class ContractError(ValueError):
    pass


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ContractError(message)


def url_ok(url: str, *, kind: str) -> bool:
    try:
        x = urlsplit(url)
    except ValueError:
        return False
    if x.scheme != 'https' or x.username or x.password or x.port or x.fragment:
        return False
    host = (x.hostname or '').lower()
    if kind == 'affiliate':
        return host == 's.shopee.com.br' and bool(x.path.strip('/'))
    if kind == 'image':
        return host == 'cf.shopee.com.br' or host == 'down-br.img.susercontent.com' or host.endswith('.img.susercontent.com')
    if kind == 'blog':
        return host.endswith('.blogspot.com') and x.path == '/p/loja.html' and not x.query
    return False


def decimal_brl(value) -> Decimal:
    need(not isinstance(value, bool) and isinstance(value, (int, float, str, Decimal)), 'Preço não numérico')
    try:
        n = Decimal(str(value))
    except InvalidOperation as exc:
        raise ContractError('Preço inválido') from exc
    need(n.is_finite() and Decimal('0') < n <= Decimal('1000000'), 'Preço fora do intervalo')
    need(n.as_tuple().exponent >= -2, 'Preço com precisão inválida')
    return n


def validate_profile(profile: dict) -> dict:
    need(isinstance(profile, dict), 'Perfil inválido')
    bid, pid = str(profile.get('blog_id', '')), str(profile.get('page_id', ''))
    url = str(profile.get('page_url', ''))
    need(bid.isdigit() and pid.isdigit(), 'Blog ID / Page ID ausentes')
    need(url_ok(url,kind='blog'), 'URL canônica da página LOJA inválida')
    need(url.split('/')[2] == str(profile.get('blog_host', '')).lower(), 'Host do blog divergente')
    cats = profile.get('categories')
    need(isinstance(cats,list) and 1 <= len(cats) <= 12, 'Categorias inválidas')
    need(all(isinstance(c,str) and 1 <= len(c.strip()) <= 60 for c in cats), 'Nome de categoria inválido')
    need(len(set(cats))==len(cats), 'Categoria duplicada')
    count = profile.get('expected_products')
    need(type(count) is int and 4 <= count <= 100, 'Contagem esperada precisa ser 4..100')
    need(profile.get('mode') == 'SAFE', 'O adaptador não executa modo de escrita')
    return profile


def validate_catalog(data: dict, profile: dict, *, allow_fixture: bool = False, clock: datetime | None = None) -> list[dict]:
    validate_profile(profile)
    need(isinstance(data,dict) and data.get('schema')==SCHEMA, 'Esquema de catálogo incompatível')
    need(str(data.get('blog_id'))==profile['blog_id'] and str(data.get('page_id'))==profile['page_id'],
         'Catálogo tenta alterar outro blog ou página')
    source=data.get('source')
    need(source=='shopee_affiliate_api' or (allow_fixture and source=='fixture_offline'), 'Origem Shopee ausente/não comprovada')
    if source == 'shopee_affiliate_api':
        need(data.get('policy_guard_validated') is True and data.get('shopee_links_verified') is True,
             'Gate de Policy Guard / links Shopee não confirmado pelo pipeline')
        when=data.get('generated_at')
        need(isinstance(when,str), 'Hora da consulta Shopee ausente')
        try:
            stamp=datetime.fromisoformat(when.replace('Z','+00:00'))
        except ValueError as exc:
            raise ContractError('Horário de coleta inválido') from exc
        need(stamp.tzinfo is not None,'Horário sem timezone')
        now=clock or datetime.now(timezone.utc)
        age=(now-stamp).total_seconds()
        need(-300 <= age <= 48*3600, 'Seleção Shopee expirada ou futura')
    products=data.get('products')
    need(isinstance(products,list) and len(products)==profile['expected_products'], 'Quantidade incorreta de produtos')
    ids=set(); groups={x:0 for x in profile['categories']}
    for p in products:
        need(isinstance(p,dict), 'Produto não é objeto')
        pid=str(p.get('item_id',''))
        need(bool(re.fullmatch(r'\d{4,25}',pid)) and pid not in ids, 'Item ID inválido ou duplicado')
        ids.add(pid)
        name=p.get('name'); cat=p.get('category'); offer=p.get('affiliate_url'); img=p.get('image_url')
        need(isinstance(name,str) and 3<=len(name.strip())<=180 and '<' not in name,'Nome inválido')
        need(cat in groups, 'Categoria fora do nicho permitido')
        groups[cat]+=1
        need(isinstance(offer,str) and url_ok(offer,kind='affiliate'),'Link de afiliado fora da Shopee')
        need(img is None or img=='' or (isinstance(img,str) and url_ok(img,kind='image')),'Imagem fora dos domínios permitidos')
        decimal_brl(p.get('price_brl'))
        need(p.get('available') is not False and p.get('policy_allowed') is True,'Produto indisponível ou não aprovado')
        score=p.get('carousel_score')
        if score is not None:
            need(source=='shopee_affiliate_api' and data.get('commission_rank_verified') is True,
                 'Score comercial precisa vir de processo Shopee verificado')
            need(not isinstance(score,bool),'Score inválido')
            try: s=Decimal(str(score))
            except InvalidOperation as e: raise ContractError('Score inválido') from e
            need(s.is_finite() and 0<=s<=100 and s.as_tuple().exponent>=-2,'Score fora de 0..100')
    need(all(n>0 for n in groups.values()),'Uma categoria está sem produtos')
    if 'per_category' in profile:
        need(groups == profile['per_category'],'Distribuição por categoria divergente')
    return products


def category_slug(cat: str) -> str:
    # HTML IDs are stable, deliberately numeric; avoid locale/slugs as input.
    raise ContractError('Use category IDs from the explicit profile')


def render_store(data: dict, profile: dict, *, allow_fixture: bool = False, clock: datetime | None = None) -> str:
    products = validate_catalog(data,profile,allow_fixture=allow_fixture,clock=clock)
    nav = []
    for i,c in enumerate(profile['categories'],start=1):
        nav.append(f'<a href="#ub-cat-{i}">{escape(c)}</a>')
    cards=[];seen_cats=set()
    for p in products:
        pid=str(p['item_id']); name=escape(p['name'].strip()); cat=escape(p['category'])
        url=escape(p['affiliate_url'], quote=True)
        src=p.get('image_url') or ''
        img=(f'<img src="{escape(src,quote=True)}" alt="{name}" loading="lazy" decoding="async"/>'
             if src else '<span class="ub-store-noimage" role="img" aria-label="Imagem indisponível">Imagem indisponível</span>')
        score=p.get('carousel_score');score_attr=''
        if score is not None:score_attr=f' data-ub-carousel-score="{Decimal(str(score)):.2f}"'
        cat_anchor=''
        if p['category'] not in seen_cats:
            seen_cats.add(p['category']);cat_anchor=f' id="ub-cat-{profile["categories"].index(p["category"])+1}"'
        cards.append(
            f'<article class="ub-product-card" data-item-id="{pid}" data-category="{cat}"{score_attr}{cat_anchor}>'
            f'<div class="ub-product-image">{img}</div>'
            f'<div class="ub-product-body"><span class="ub-product-tag">{cat}</span>'
            f'<h2 class="ub-product-title">{name}</h2>'
            f'<div class="ub-product-price-row"><span class="ub-product-price">R$ {str(decimal_brl(p["price_brl"]).quantize(Decimal("0.01"))).replace(".",",")}</span></div>'
            f'<div class="ub-product-meta"><span>Shopee</span><span>Consulte a oferta</span></div>'
            f'<a class="ub-product-action" href="{url}" rel="nofollow sponsored noopener" target="_blank">Ver oferta na Shopee</a>'
            '</div></article>')
    return (f'<nav class="ub-store-category-nav" aria-label="Categorias da loja" style="display:flex;flex-wrap:wrap;gap:12px;margin:0 0 16px">{" ".join(nav)}</nav>\n'
            f'<div class="ub-store-grid" id="ub-store-grid">{"".join(cards)}</div>\n'
            f'<p class="ub-store-affiliate-disclosure">{escape(POLICY_TEXT)}</p>')


def initial_page(data: dict, profile: dict, *, allow_fixture:bool = False) -> str:
    html=render_store(data,profile,allow_fixture=allow_fixture)
    return f'{PAGE_START}\n<div id="cp-loja">\n{AUTO_START}\n{html}\n{AUTO_END}\n</div>\n{PAGE_END}'


def patch_page(original: str, replacement: str, *, expected_sha256: str) -> str:
    """Optimistic guard + two unique markers, no modifications beyond marked region."""
    need(sha256(original.encode('utf-8')).hexdigest()==expected_sha256,'Página foi editada em paralelo: abortado')
    need(original.count(AUTO_START)==1 and original.count(AUTO_END)==1,'Marcadores V31 ausentes/duplicados')
    start=original.index(AUTO_START)+len(AUTO_START)
    end=original.index(AUTO_END)
    need(start<=end,'Marcadores V31 invertidos')
    need(original.count('id="cp-loja"')==1,'Container LOJA ausente/duplicado')
    need('<script' not in replacement.lower(),'Script não permitido na região gerada')
    return original[:start]+'\n'+replacement+'\n'+original[end:]


class StoreParser(HTMLParser):
    def __init__(self):
        super().__init__();self.cards=[];self.links=[];self.images=[];self.scores=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='article' and 'ub-product-card' in (a.get('class') or '').split():
            self.cards.append(a.get('data-item-id'))
            if 'data-ub-carousel-score' in a:self.scores.append(a['data-ub-carousel-score'])
        if tag=='a' and 'ub-product-action' in (a.get('class') or '').split():
            self.links.append((a.get('href'),a.get('rel','')))
        if tag=='img':self.images.append(a.get('src'))


def verify_rendered(html: str, data: dict, profile: dict, *, allow_fixture: bool=False) -> dict:
    products=validate_catalog(data,profile,allow_fixture=allow_fixture)
    parser=StoreParser();parser.feed(html)
    expected_ids=[str(p['item_id']) for p in products]
    need(parser.cards==expected_ids, 'Contagem ou sequência de cards divergiu')
    need([u for u,_ in parser.links]==[p['affiliate_url'] for p in products], 'Links renderizados divergiram')
    need(all('nofollow' in rel and 'sponsored' in rel for _,rel in parser.links), 'Atributo sponsored/nofollow ausente')
    need(all(url_ok(x,kind='image') for x in parser.images),'Imagem renderizada fora dos domínios')
    need(html.count(POLICY_TEXT)==1, 'Aviso de afiliados ausente ou duplicado')
    need('id="ub-store-grid"' in html,'Grade V31 ausente')
    need(len(parser.scores)==sum(p.get('carousel_score') is not None for p in products),'Scores divergentes')
    return {'cards':len(parser.cards),'affiliate_links':len(parser.links),'photos':len(parser.images),
            'categories':len(set(p['category'] for p in products)),'scores':len(parser.scores),
            'sha256':sha256(html.encode('utf-8')).hexdigest()}


def prepare_safe(data:dict,profile:dict,original:str|None=None,*,allow_fixture:bool=False)->dict:
    """Returns candidate HTML + evidence; never writes to Blogger or GitHub."""
    fragment=render_store(data,profile,allow_fixture=allow_fixture)
    result=(initial_page(data,profile,allow_fixture=allow_fixture) if original is None
            else patch_page(original,fragment,expected_sha256=sha256(original.encode('utf-8')).hexdigest()))
    checks=verify_rendered(fragment,data,profile,allow_fixture=allow_fixture)
    return {'status':'V31_SAFE_CANDIDATE_ONLY_NO_PUBLICATION','profile_blog_id':profile['blog_id'],
            'profile_page_id':profile['page_id'],'source':data.get('source'),'check':checks,'html':result}