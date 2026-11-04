#!/usr/bin/env python3
"""Auditoria pública read-only da LOJA V31 LAB; nenhum PUT, sem Blogger OAuth.

Compara identidade exata de 16 cards, fotos e links ao artefato SAFE Shopee V23
por uma consulta à URL canônica. Classifica HTTP 429 como PENDING (não PASS).
Não muda Blogger, histórico, workflows nem arquivos do repositório.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

START = '<!-- UNIVERSAL_V31_STORE_AUTO_START -->'
END = '<!-- UNIVERSAL_V31_STORE_AUTO_END -->'
LAB_BLOG_ID = '4739187376492839837'
LAB_PAGE_ID = '2446067640331732447'
LAB_URL = 'https://blog-teste-tema-worpress.blogspot.com/p/loja.html'
MAX_HTML_BYTES = 3_000_000


class VerificationError(ValueError):
    pass


class PublicThrottled(Exception):
    pass


def require(cond: bool, message: str) -> None:
    if not cond:
        raise VerificationError(message)


def digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def reference(profile: dict, selection: dict, actual_sha256: str) -> dict:
    require(isinstance(profile, dict) and isinstance(selection, dict), 'Perfil/seleção inválidos')
    require(profile.get('blog_id') == LAB_BLOG_ID and profile.get('page_id') == LAB_PAGE_ID,
            'Blog/Page ID fora do LAB permitido')
    require(profile.get('page_url') == LAB_URL and profile.get('mode') == 'SAFE',
            'URL canônica ou modo divergente')
    require(selection.get('schemaVersion') == 1 and selection.get('status') == 'SAFE_READY'
            and selection.get('publishReady') is True and selection.get('dryRun') is True,
            'Seleção não passou pelo SAFE')
    require(selection.get('blogId') == LAB_BLOG_ID, 'Seleção pertence a outro blog')
    require(re.fullmatch(r'[0-9a-f]{64}', actual_sha256 or '') is not None,
            'SHA256 do artefato inválido')
    require(selection.get('totalItems') == 16 and selection.get('uniqueItemIds') == 16
            and profile.get('expected_products') == 16, 'Contagem esperada não é 16')
    groups = selection.get('categories')
    cats = profile.get('categories')
    require(isinstance(groups, dict) and isinstance(cats, list) and list(groups) == cats,
            'Categorias divergem do LAB')
    meta = selection.get('affiliateLinkGeneration') or {}
    require(meta.get('allResolvedToShopee') is True and meta.get('validatedCount') == 16,
            'Links Shopee não foram validados na origem')
    gates = selection.get('gates') or {}
    require(gates.get('allLinksResolved') is True and gates.get('failClosed') is True,
            'Gates SAFE da origem não passaram')
    products = []
    for category, entries in groups.items():
        require(isinstance(entries, list) and len(entries) == profile.get('per_category', {}).get(category),
                'Quantidade de categoria divergente')
        for p in entries:
            require(isinstance(p, dict) and p.get('category') == category, 'Categoria no produto incorreta')
            iid, url, photo = str(p.get('itemId') or ''), p.get('affiliateUrl'), p.get('imageUrl')
            require(re.fullmatch(r'\d{4,25}', iid) is not None, 'Item ID inválido')
            for value, host in [(url,'s.shopee.com.br'), (photo,'cf.shopee.com.br')]:
                require(isinstance(value,str), 'URL obrigatória ausente')
                u=urlsplit(value)
                require(u.scheme=='https' and u.hostname==host and not u.username and not u.password,
                        'URL fora do domínio Shopee esperado')
            products.append({'id':iid,'link':url,'image':photo,'category':category})
    ids=[p['id'] for p in products]
    require(len(products) == 16 and len(set(ids)) == 16, 'Produtos da seleção duplicados')
    return {'products':products, 'selection_sha256':actual_sha256, 'expected_count':16}


class Cards(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards, self.links, self.images, self.categories = [],[],[],[]
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'article' and 'ub-product-card' in (a.get('class') or '').split():
            self.cards.append(a.get('data-item-id'))
            self.categories.append(a.get('data-category'))
        if tag == 'a' and 'ub-product-action' in (a.get('class') or '').split():
            self.links.append((a.get('href'),a.get('rel','')))
        if tag == 'img':
            self.images.append(a.get('src'))


def verify_html(html: str, expected: dict) -> dict:
    require(isinstance(html,str) and len(html)>1000, 'HTML público ausente/incompleto')
    require(html.count(START)==1 and html.count(END)==1, 'Marcadores públicos V31 ausentes ou duplicados')
    require('var userResumed = false;' in html and 'ub-v31-share' in html,
            'Tema V31 R1/carrossel/compartilhamento ausentes')
    a=html.index(START)+len(START); b=html.index(END)
    require(a<b,'Região dos produtos inválida')
    p=Cards();p.feed(html[a:b])
    products=expected['products']
    require(p.cards==[x['id'] for x in products], 'Catálogo público com IDs diferentes')
    require(p.categories==[x['category'] for x in products], 'Categorias do catálogo público divergentes')
    require(p.images==[x['image'] for x in products], 'Fotos públicas diferentes da seleção')
    require([u for u,_ in p.links]==[x['link'] for x in products], 'Links públicos diferentes da seleção')
    require(all('nofollow' in (rel or '').split() and 'sponsored' in (rel or '').split() for _,rel in p.links),
            'Atributos de afiliado incompletos')
    return {'status':'PUBLIC_EXACT_PASS','public_http':200,'cards':len(p.cards),
            'images':len(p.images),'links':len(p.links),'categories':len(set(p.categories)),
            'selection_sha256':expected['selection_sha256'],'public_html_sha256':digest(html.encode('utf-8'))}


def fetch_public(*, opener: Callable=urlopen) -> str:
    req=Request(LAB_URL, headers={'Accept':'text/html,application/xhtml+xml',
        'User-Agent':'BloggerAutomationV31LabPublicVerifier/1.0'})
    try:
        with opener(req,timeout=30) as response:
            require(int(response.status)==200,'Resposta pública não é HTTP 200')
            final=response.geturl()
            u=urlsplit(final)
            require(u.scheme=='https' and u.netloc==urlsplit(LAB_URL).netloc
                    and u.path=='/p/loja.html', 'Redirecionamento para URL fora do LAB')
            raw=response.read(MAX_HTML_BYTES+1)
            require(len(raw)<=MAX_HTML_BYTES, 'HTML público grande demais')
            return raw.decode('utf-8','replace')
    except HTTPError as exc:
        if exc.code in (429, 503):
            raise PublicThrottled(f'HTTP {exc.code}; aguardar janela do Blogger') from exc
        raise VerificationError('Falha HTTP pública: '+str(exc.code)) from exc
    except URLError as exc:
        raise PublicThrottled('Rede pública temporariamente indisponível') from exc


def run(selection_path:Path, profile_path:Path, sha_pin:str, *, opener: Callable=urlopen):
    binary=selection_path.read_bytes()
    require(digest(binary)==sha_pin,'Artefato Shopee não coincide com o SHA-256 aprovado')
    selection=json.loads(binary)
    profile=json.loads(profile_path.read_text(encoding='utf-8'))
    exp=reference(profile,selection,sha_pin)
    html=fetch_public(opener=opener)
    return verify_html(html,exp)


def main() -> int:
    parser=argparse.ArgumentParser(description='Auditoria pública read-only de LOJA V31 LAB')
    parser.add_argument('--selection',required=True,type=Path)
    parser.add_argument('--profile',required=True,type=Path)
    parser.add_argument('--selection-sha256',required=True)
    parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    result={'status':'PUBLIC_VERIFICATION_NOT_RUN'}
    code=2
    try:
        result=run(args.selection,args.profile,args.selection_sha256)
        code=0
    except PublicThrottled as exc:
        result={'status':'PUBLIC_PENDING_THROTTLED','reason':str(exc),
                'public_verified':False,'publication_attempted':False}
        code=75
    except Exception as exc:
        result={'status':'PUBLIC_VERIFICATION_FAILED','error_type':type(exc).__name__,
                'reason':str(exc)[:200],'public_verified':False,'publication_attempted':False}
        code=2
    args.report.parent.mkdir(parents=True,exist_ok=True)
    result['verified_at_utc']=datetime.now(timezone.utc).isoformat()
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    return code

if __name__=='__main__':
    raise SystemExit(main())