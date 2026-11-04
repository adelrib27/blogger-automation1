#!/usr/bin/env python3
"""Adapt fresh, already-policy-guarded V23 selection to Universal V31 page input.

No Shopee API calls, no Blogger writes, no credentials. Caller MUST supply a
real callable that re-runs central blogger_policy_guard.require_product_allowed
on each selected raw Shopee object; never infer compliance from the JSON alone.
"""
from __future__ import annotations
from datetime import datetime,timezone
from typing import Callable
from v31_store_safe import ContractError, need, validate_profile, validate_catalog, SCHEMA


def convert_selection(doc: dict, profile:dict, *, require_product_allowed:Callable|None,
                      now:datetime|None=None) -> dict:
    validate_profile(profile)
    need(callable(require_product_allowed),'Policy Guard central não foi fornecido')
    need(isinstance(doc,dict) and doc.get('schemaVersion')==1 and doc.get('status')=='SAFE_READY',
         'Seleção v23 sem status SAFE_READY')
    need(doc.get('publishReady') is True,'Seleção v23 não está pronta para publicação')
    need(doc.get('dryRun') is True,'Esperado arquivo da fase SAFE, antes da escrita')
    need(str(doc.get('blogId'))==profile['blog_id'],'Origem v23 pertence a outro blog')
    need(doc.get('totalItems')==profile['expected_products'] and doc.get('uniqueItemIds')==profile['expected_products'],
         'Contagem total/única divergente')
    when=doc.get('timestamp')
    need(isinstance(when,str),'Seleção v23 sem horário')
    try: stamp=datetime.fromisoformat(when.replace('Z','+00:00'))
    except ValueError as exc: raise ContractError('Timestamp v23 inválido') from exc
    need(stamp.tzinfo is not None,'Timezone v23 ausente')
    age=((now or datetime.now(timezone.utc))-stamp).total_seconds()
    need(-300<=age<=48*3600,'Seleção v23 não está fresca (máximo 48 h)')
    groups=doc.get('categories')
    need(isinstance(groups,dict) and list(groups)==profile['categories'],
         'Categorias v23 divergentes do nicho/perfil')
    need(sum(len(x) for x in groups.values() if isinstance(x,list))==profile['expected_products'],
         'Contagem das categorias divergente')
    aff=doc.get('affiliateLinkGeneration') or {}
    need(aff.get('method')=='generateShortLink' and aff.get('allResolvedToShopee') is True
         and aff.get('validatedCount')==profile['expected_products'],
         'Geração de links afiliados Shopee não verificada')
    semantic=doc.get('semanticValidation') or {}
    gates=doc.get('gates') or {}
    need(semantic.get('finalProductGate') is True and semantic.get('strictAccessoriesBlocked') is True,
         'Gate semântico v23 ausente')
    need(all(gates.get(x) is True for x in ['allLinksResolved','semanticRulesApplied','finalProductGate','failClosed']),
         'Gates da seleção v23 não aprovados')
    result=[]
    for category,items in groups.items():
        need(isinstance(items,list) and items,'Categoria v23 vazia')
        for p in items:
            need(isinstance(p,dict),'Produto v23 malformado')
            need(p.get('source')=='shopee_affiliate_open_api','Origem de item não é Shopee API')
            need(str(p.get('category'))==category,'Categoria do item divergente')
            require_product_allowed(p)
            result.append({
                'item_id':str(p.get('itemId') or ''), 'name':p.get('productName'),
                'category':category,'price_brl':p.get('priceMin'),
                'affiliate_url':p.get('affiliateUrl'), 'image_url':p.get('imageUrl') or None,
                'available':True,'policy_allowed':True,
                # Scores explicitly omitted until real affiliate commission facts
                # are independently verified in the ranking pipeline.
            })
    out={'schema':SCHEMA,'source':'shopee_affiliate_api',
         'generated_at':stamp.isoformat(),'blog_id':profile['blog_id'],'page_id':profile['page_id'],
         'policy_guard_validated':True,'shopee_links_verified':True,
         'commission_rank_verified':False,'products':result}
    validate_catalog(out,profile,clock=now)
    return out