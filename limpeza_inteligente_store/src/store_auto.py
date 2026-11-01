#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MODULE_DIR=ROOT/'limpeza_inteligente_store'; DATA_DIR=MODULE_DIR/'data'; HISTORY_PATH=DATA_DIR/'store_rotation.json'; LAST_SELECTION_PATH=DATA_DIR/'store_last_selection.json'; SCAN_DIR=DATA_DIR/'store_shopee_scan'
BLOG_ID=os.getenv('BLOGGER_BLOG_ID','7757953554206491487').strip(); PAGE_ID=os.getenv('BLOGGER_STORE_PAGE_ID','').strip(); ITEMS_PER_CATEGORY=max(1,min(int(os.getenv('BLOGGER_STORE_ITEMS_PER_CATEGORY','4')),8)); RECENT_DAYS=max(1,min(int(os.getenv('BLOGGER_STORE_RECENT_DAYS','1')),30)); DRY_RUN=os.getenv('BLOGGER_STORE_DRY_RUN','false').strip().lower() in {'1','true','yes','on'}
CATEGORY_SPECS=[('Robôs Aspiradores','Robôs Aspiradores','bls-robos-aspiradores'),('Aspiradores Verticais','Aspiradores Verticais','bls-aspiradores-verticais'),('Aspiradores Portáteis','Aspiradores Portáteis','bls-aspiradores-portateis'),('Mops & Limpeza Manual','Mops & Limpeza Manual','bls-mops-limpeza'),('Lavadoras & Higienização','Lavadoras & Higienização','bls-lavadoras-higienizacao')]
os.environ.setdefault('SHOPEE_OPPORTUNITIES_CONFIG',str(MODULE_DIR/'config/shopee_oportunidades.json')); os.environ.setdefault('SHOPEE_INTENT_RULES',str(MODULE_DIR/'config/shopee_intent_rules.json')); os.environ.setdefault('SHOPEE_OUTPUT_DIR',str(SCAN_DIR)); os.environ.setdefault('SHOPEE_CATEGORY','all'); os.environ.setdefault('SHOPEE_TOP_N','70')
sys.path.insert(0,str(ROOT/'src')); sys.path.insert(0,str(ROOT/'blogger_product_store/src')); sys.path.insert(0,str(MODULE_DIR/'src'))
from shopee_oportunidades_limpeza import regression_checks
spec=importlib.util.spec_from_file_location('validated_store_auto',ROOT/'blogger_product_store/src/store_auto.py'); base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
for name,value in {'MODULE_DIR':MODULE_DIR,'DATA_DIR':DATA_DIR,'HISTORY_PATH':HISTORY_PATH,'LAST_SELECTION_PATH':LAST_SELECTION_PATH,'SCAN_DIR':SCAN_DIR,'BLOG_ID':BLOG_ID,'PAGE_ID':PAGE_ID,'ITEMS_PER_CATEGORY':ITEMS_PER_CATEGORY,'RECENT_DAYS':RECENT_DAYS,'DRY_RUN':DRY_RUN,'CATEGORY_SPECS':CATEGORY_SPECS}.items(): setattr(base,name,value)
base.shopee_v23.run_regression_checks=regression_checks
START_MARKER=base.START_MARKER; END_MARKER=base.END_MARKER; now_local=base.now_local; choose_products=base.choose_products; render_store_block=base.render_store_block; validate_shape=base.validate_shape; valid_product=base.valid_product; criar_servico_blogger=base.criar_servico_blogger

def patch_runtime():
    for name,value in {'MODULE_DIR':MODULE_DIR,'DATA_DIR':DATA_DIR,'HISTORY_PATH':HISTORY_PATH,'LAST_SELECTION_PATH':LAST_SELECTION_PATH,'SCAN_DIR':SCAN_DIR,'BLOG_ID':BLOG_ID,'PAGE_ID':PAGE_ID,'ITEMS_PER_CATEGORY':ITEMS_PER_CATEGORY,'RECENT_DAYS':RECENT_DAYS,'DRY_RUN':DRY_RUN,'CATEGORY_SPECS':CATEGORY_SPECS}.items(): setattr(base,name,value)
    base.valid_product=globals()['valid_product']; base.criar_servico_blogger=globals()['criar_servico_blogger']; base.shopee_v23.run_regression_checks=regression_checks

def main():
    patch_runtime(); DATA_DIR.mkdir(parents=True,exist_ok=True)
    print('Blogger — Loja automática Limpeza Inteligente'); print('Modo:','DRY-RUN' if DRY_RUN else 'PUBLICAÇÃO')
    ranking=base.shopee_v23.scan_v23(); print('Ranking Shopee recebido:',len(ranking)); chosen=base.choose_products(ranking,base.load_history()); block=base.render_store_block(chosen); base.validate_shape(chosen,block)
    if DRY_RUN:
        base.validate_blogger_target(); data=base.snapshot(chosen,'DRY_RUN_OK'); print(f"DRY-RUN OK: {data['totalItems']} produtos únicos em {data['categoryCount']} categorias; Blogger não alterado."); return
    info=base.update_blogger(block,chosen); data=base.snapshot(chosen,'PUBLISHED',info); base.append_history(data); print(f"PUBLICAÇÃO OK: {data['totalItems']} produtos únicos; alvo Blogger {info.get('pageId')} verificado.")
if __name__=='__main__': main()
