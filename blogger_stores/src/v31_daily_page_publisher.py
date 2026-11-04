#!/usr/bin/env python3
"""V31 LAB Page publisher SAFE: does not publish unless explicitly enabled.

Requires a V23 SAFE_READY Shopee selection from THIS EXACT LAB, re-runs central
blogger_policy_guard for each item, preserves page outside the marked region,
backups BEFORE writes, and validates Blogger readback and public HTML.

No scheduled/autonomous execution yet. --apply requires human-reviewed SHA and
literal confirm; never claim GitHub cron is enabled by this tool.
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
import time
from urllib.parse import urlsplit
import urllib.request

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'v31_core'))
from v31_store_safe import (AUTO_START,AUTO_END,ContractError,need,render_store,
                            validate_profile,patch_page,verify_rendered)
from v31_from_v23_selection import convert_selection
# LAB-only identity lock; must not be widened to other blogs implicitly.
LAB_ID = "4739187376492839837"
PAGE_ID = "2446067640331732447"
PAGE_URL = "https://blog-teste-tema-worpress.blogspot.com/p/loja.html"
OPEN = '<div id="cp-loja">'
CLOSE = '</div>'

def digest(value: str) -> str:
    return sha256(value.encode('utf-8')).hexdigest()

CONFIRM = 'PUBLISH V31 LAB STORE FROM VERIFIED SHOPEE'
MIN_PHOTOS = 16

class PageScan(HTMLParser):
    def __init__(self):
        super().__init__();self.cards=[];self.links=[];self.images=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if d.get('id') is not None:self.ids.append(d['id'])
        if tag=='article' and 'ub-product-card' in (d.get('class') or '').split():self.cards.append(d.get('data-item-id'))
        if tag=='a' and 'ub-product-action' in (d.get('class') or '').split():self.links.append(d.get('href'))
        if tag=='img':self.images.append(d.get('src'))

def inspect_mutable_page(page: dict, profile: dict) -> tuple[str,dict]:
    need(str(page.get('id'))==PAGE_ID and str(page.get('blog',{}).get('id',LAB_ID))==LAB_ID,'ID Blogger divergente')
    need(str(page.get('title','')).strip().casefold()=='loja','Titulo da Page diferente de LOJA')
    need(str(page.get('url') or PAGE_URL)==PAGE_URL,'URL da Page divergiu')
    raw=page.get('content')
    need(isinstance(raw,str) and 6000<len(raw)<180000,'HTML da Page invalido')
    need(raw.startswith(OPEN) and raw.endswith(CLOSE),'Contrato cp-loja divergente')
    need(raw.count(AUTO_START)==1 and raw.count(AUTO_END)==1,'Faltam marcadores de atualizacao V31')
    need(raw.index(AUTO_START)<raw.index(AUTO_END),'Ordem dos marcadores invalida')
    need('<script' not in raw.lower(),'Script na Page inesperado; inspecao manual')
    parser=PageScan();parser.feed(raw)
    need(parser.ids.count('cp-loja')==1 and parser.ids.count('ub-store-grid')==1,
         'Contêiner/grade V31 ausente ou duplicada')
    need(len(parser.cards)==profile['expected_products'] and len(parser.links)==profile['expected_products'],
         'Quantidade no alvo mudou; bloqueado')
    need(len(set(parser.cards))==len(parser.cards),'Cards repetidos na Page')
    need(all(u and urlsplit(u).scheme=='https' and urlsplit(u).hostname=='s.shopee.com.br' for u in parser.links),
         'Links externos encontrados na Page atual')
    return raw,{'cards':len(parser.cards),'affiliate_links':len(parser.links),
                'photos':len(parser.images),'sha256':digest(raw)}

def validate_diff(original: str,new: str) -> None:
    """Verifies exact unchanged bytes outside existing Auto markers."""
    need(original.count(AUTO_START)==new.count(AUTO_START)==1,'Marcador inicio ausente')
    need(original.count(AUTO_END)==new.count(AUTO_END)==1,'Marcador fim ausente')
    need(original.split(AUTO_START)[0]==new.split(AUTO_START)[0], 'Prefixo da LOJA foi alterado')
    need(original.split(AUTO_END)[1]==new.split(AUTO_END)[1], 'Sufixo da LOJA foi alterado')

def prepare_page(original: str, selection: dict, profile: dict, *, clock=None) -> tuple[str,dict]:
    validate_profile(profile)
    need(profile['blog_id']==LAB_ID and profile['page_id']==PAGE_ID,'Perfil nao e do LAB autorizado')
    fragment=render_store(selection,profile,clock=clock)
    proof=verify_rendered(fragment,selection,profile)
    need(proof['photos']==profile['expected_products']==MIN_PHOTOS,
         'Todas as 16 fotografias Shopee sao obrigatorias para a primeira publicacao')
    new=patch_page(original,fragment,expected_sha256=digest(original))
    validate_diff(original,new)
    need(new!=original,'Nenhuma mudanca no HTML; nao executar PUT redundante')
    return new,proof

def public_check(profile: dict, expected_products: int) -> dict:
    req=urllib.request.Request(PAGE_URL+'?v31_daily_verify='+str(time.time_ns()),headers={
        'Cache-Control':'no-cache','User-Agent':'BloggerV31DailyStorePublicVerifier/1.0'})
    with urllib.request.urlopen(req,timeout=35) as r:
        status=int(r.status);html=r.read(3_000_000).decode('utf-8','replace')
    need(status==200,'Pagina publica LOJA nao retornou HTTP 200')
    need(AUTO_START in html and AUTO_END in html,'Marcadores publicos V31 ausentes')
    need('var userResumed = false;' in html and 'ub-v31-share' in html,'Tema V31 R1 nao detectado')
    count=len(re.findall(r'class="ub-product-card"',html))
    links=len(re.findall(r'href="https://s\.shopee\.com\.br/',html))
    need(count==expected_products and links==expected_products,'Contagem publica divergiu')
    return {'status':'PASS','http':status,'cards':count,'affiliate_links':links,'theme':'V31_R1'}

def create_service(repo_root: Path):
    sys.path.insert(0,str(repo_root.resolve()/'src'))
    from criar_rascunho import criar_servico_blogger
    return criar_servico_blogger()

def require_guard(repo_root: Path):
    sys.path.insert(0,str(repo_root.resolve()/'src'))
    from blogger_policy_guard import require_product_allowed
    return require_product_allowed

def fetch_page(service):
    return service.pages().get(blogId=LAB_ID,pageId=PAGE_ID).execute()

def execute(service, profile:dict, selection:dict, args) -> dict:
    page=fetch_page(service)
    original,before=inspect_mutable_page(page,profile)
    candidate,rendered=prepare_page(original,selection,profile)
    summary={'status':'V31_DAILY_LAB_SAFE_READY','blog_id':LAB_ID,'page_id':PAGE_ID,
             'publications_performed':False,'current':before,'candidate_sha256':digest(candidate),
             'candidate':rendered}
    if not args.apply:return summary
    need(args.confirm==CONFIRM,'Confirmação literal obrigatoria')
    need(args.expected_sha==digest(original),'SHA origem difere do plano SAFE; abortar')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder=args.backup_dir.resolve()/('v31-lab-daily-'+stamp+'-'+digest(original)[:10])
    need(not folder.exists(),'Backup dessa operacao ja existe')
    folder.mkdir(parents=True,exist_ok=False)
    backup=folder/'LOJA_ANTES_ATUALIZACAO.html'
    backup.write_text(original,encoding='utf-8',newline='')
    need(backup.read_text(encoding='utf-8')==original,'Backup incompleto; nenhum PUT')
    (folder/'preflight.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Re-fetch prevents blind overwrites if a parallel edit occurred; this is NOT atomic CAS.
    again=fetch_page(service)
    latest,_=inspect_mutable_page(again,profile)
    need(digest(latest)==digest(original) and again.get('etag')==page.get('etag'),
         'Alteracao paralela identificada, ABORTADO antes do PUT')
    req=service.pages().update(blogId=LAB_ID,pageId=PAGE_ID,
                               body={'title':page['title'],'content':candidate})
    if again.get('etag'):req.headers['If-Match']=str(again.get('etag'))
    req.execute()
    after=fetch_page(service)
    raw,_=inspect_mutable_page(after,profile)
    need(raw==candidate,'Readback Blogger divergente: nao repetir ou fazer rollback cego')
    proof=public_check(profile,profile['expected_products'])
    summary.update({'status':'V31_LAB_DAILY_UPDATE_READBACK_PUBLIC_PASS',
                    'publications_performed':True,'public':proof,'backup_path':str(backup)})
    (folder/'resultado.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return summary

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',type=Path,required=True,help='Repo que contem o Policy Guard central')
    p.add_argument('--v23-selection',type=Path,required=True,help='Selecao Shopee real SAFE_READY do mesmo LAB')
    p.add_argument('--profile',type=Path,default=HERE/'perfil_lab_v31_SAFE.json')
    p.add_argument('--backup-dir',type=Path,default=Path('C:/Blogger-Automator/backups'))
    p.add_argument('--apply',action='store_true',help='Somente primeira publicacao manual aprovada')
    p.add_argument('--confirm',default='')
    p.add_argument('--expected-sha',default='')
    args=p.parse_args()
    try:
        profile=validate_profile(json.loads(args.profile.read_text(encoding='utf-8')))
        need(profile['blog_id']==LAB_ID and profile['page_id']==PAGE_ID,'Perfil LAB incorreto')
        raw=json.loads(args.v23_selection.read_text(encoding='utf-8'))
        catalog=convert_selection(raw,profile,require_product_allowed=require_guard(args.repo_root))
        result=execute(create_service(args.repo_root),profile,catalog,args)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except Exception as exc:
        print(json.dumps({'status':'V31_DAILY_FAIL_CLOSED','error_type':type(exc).__name__,
                          'message':str(exc)[:210]},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())