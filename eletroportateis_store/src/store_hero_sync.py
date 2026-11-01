#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; MODULE_DIR=ROOT/'eletroportateis_store'; DATA_DIR=MODULE_DIR/'data'; LAST_SELECTION_PATH=DATA_DIR/'store_last_selection.json'
BLOG_ID=os.getenv('BLOGGER_BLOG_ID','8658632621591002634').strip(); PAGE_ID=os.getenv('BLOGGER_STORE_PAGE_ID','').strip()
sys.path.insert(0,str(ROOT/'src')); sys.path.insert(0,str(ROOT/'blogger_product_store/src'))
spec=importlib.util.spec_from_file_location('validated_store_hero',ROOT/'blogger_product_store/src/store_hero_sync.py'); base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
base.MODULE_DIR=MODULE_DIR; base.DATA_DIR=DATA_DIR; base.LAST_SELECTION_PATH=LAST_SELECTION_PATH; base.BLOG_ID=BLOG_ID; base.PAGE_ID=PAGE_ID
HERO_MARKERS=base.HERO_MARKERS; render_card=base.render_card; render_region=base.render_region; locate=base.locate; load_selection=base.load_selection; criar_servico_blogger=base.criar_servico_blogger

def hero_sets(data):
    c=data.get('categories') or {}; required=['Air Fryers','Liquidificadores & Mixers','Processadores','Batedeiras','Cafeteiras & Outros Eletros']
    for key in required:
        if len(c.get(key) or []) != 4: raise RuntimeError(f'Seleção inválida para hero: {key}')
    slides=[
      [('Air Fryer',p) for p in c[required[0]]],
      [('Liquidificar',p) for p in c[required[1]][:2]]+[('Processar',p) for p in c[required[2]][:2]],
      [('Bater',p) for p in c[required[3]][:2]]+[('Outros eletros',p) for p in c[required[4]][:2]],
    ]
    ids=[str(p.get('itemId')) for slide in slides for _,p in slide]
    if len(ids)!=12 or len(set(ids))!=12: raise RuntimeError('Hero não contém 12 produtos únicos.')
    return slides

def main():
    base.MODULE_DIR=MODULE_DIR; base.DATA_DIR=DATA_DIR; base.LAST_SELECTION_PATH=LAST_SELECTION_PATH; base.BLOG_ID=BLOG_ID; base.PAGE_ID=PAGE_ID; base.criar_servico_blogger=globals()['criar_servico_blogger']
    data=base.load_selection(); slides=hero_sets(data)
    blocks=[base.render_region(*base.HERO_MARKERS[0],'Air Fryers em destaque',slides[0],include_css=True),base.render_region(*base.HERO_MARKERS[1],'Liquidificadores, mixers e processadores',slides[1]),base.render_region(*base.HERO_MARKERS[2],'Batedeiras, cafeteiras e outros eletros',slides[2])]
    blogger=base.criar_servico_blogger(); page=blogger.pages().get(blogId=BLOG_ID,pageId=base.page_id()).execute(); raw=str(page.get('content') or ''); original_len=len(raw)
    for (start,end),block in zip(base.HERO_MARKERS,blocks): a,b=base.locate(raw,start,end); raw=raw[:a]+block+raw[b:]
    if len(raw)<max(4500,int(original_len*.55)): raise RuntimeError('Proteção de integridade do hero.')
    blogger.pages().update(blogId=BLOG_ID,pageId=base.page_id(),body={'title':page.get('title') or 'Loja','content':raw}).execute(); vr=str(blogger.pages().get(blogId=BLOG_ID,pageId=base.page_id()).execute().get('content') or '')
    ids=[str(p.get('itemId')) for slide in slides for _,p in slide]; missing=[i for i in ids if f'data-hero-item-id="{i}"' not in vr]
    if missing or vr.count('data-hero-item-id=')!=12: raise RuntimeError(f'Hero inválido: {missing[:5]}')
    print('ELETROPORTATEIS_HERO_PASS: 12 cards únicos')
if __name__=='__main__': main()
