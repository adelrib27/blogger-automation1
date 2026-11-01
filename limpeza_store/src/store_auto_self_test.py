#!/usr/bin/env python3
import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.environ['BLOGGER_STORE_DRY_RUN']='true'
sys.path.insert(0,str(ROOT/'limpeza_store/src'))
import store_auto as s

def product(i,category):
    return {'itemId':str(i),'productName':f'Produto teste {i} {category}','offerLink':f'https://s.shopee.com.br/teste{i}','imageUrl':f'https://cf.shopee.com.br/file/teste{i}','priceMin':10+i,'priceMax':10+i,'shopName':f'Loja {i}','categories':[category]}
ranking=[]; idx=1
for key,_,_ in s.CATEGORY_SPECS:
    for _ in range(8): ranking.append(product(idx,key)); idx+=1
chosen=s.choose_products(ranking,{'version':1,'runs':[]})
assert len(chosen)==5 and all(len(v)==4 for v in chosen.values())
ids=[p['itemId'] for values in chosen.values() for p in values]; assert len(ids)==20 and len(set(ids))==20
block=s.render_store_block(chosen); s.validate_shape(chosen,block); assert block.count('rel="nofollow sponsored noopener"')==20; assert block.count('data-item-id=')==20
history={'version':1,'runs':[{'timestamp':s.now_local().isoformat(),'items':[{'category':category,'itemId':p['itemId']} for category,values in chosen.items() for p in values]}]}
chosen2=s.choose_products(ranking,history); ids2={p['itemId'] for values in chosen2.values() for p in values}; assert not(set(ids)&ids2)
try:
    s.choose_products(ranking[:3],{'version':1,'runs':[]}); raise AssertionError('Deveria falhar com seleção incompleta.')
except RuntimeError: pass
print('limpeza_store_self_test: PASS')
