#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import os
import re
import unicodedata
from pathlib import Path
import store_auto as base
from blogger_policy_guard import product_policy_check
from post_target_proxy import BloggerPostTargetProxy

_patch_path=Path(__file__).resolve().parent/'store_layout_patch.py'
_spec=importlib.util.spec_from_file_location('limpeza_store_layout_patch',_patch_path)
if _spec is None or _spec.loader is None: raise RuntimeError('Não foi possível carregar o patch local da Limpeza Inteligente.')
_mod=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mod); patch_store_layout=_mod.patch_store_layout
POST_ID=os.getenv('BLOGGER_STORE_POST_ID','6383277011247909539').strip()
if not POST_ID: raise RuntimeError('BLOGGER_STORE_POST_ID ausente.')
_original=base.valid_product


def _norm(value):
    text=unicodedata.normalize('NFKD',str(value or ''))
    text=''.join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r'\s+',' ',text).strip()


_ACCESSORY_PREFIXES=(
    'saco coletor','saco para aspirador','filtro ','bico ','mangueira ','bateria ',
    'carregador ','escova lateral','escova central','motor ','tanque ','reservatorio avulso',
    'cabo avulso','cabo para mop','refil ','kit reparo','peca ','pecas ','suporte para aspirador',
)
_ACCESSORY_TERMS=(
    'reposicao','substituicao','compativel com aspirador','para extratora','para aspirador de po',
    'acessorio para aspirador','acessorio aspirador','engate rapido','conector para lavadora',
    'mangueira avulsa','bico avulso','pistola avulsa','filtro hepa reposicao',
)
_TOY_TERMS=('brinquedo','infantil','para meninas','para meninos','faxina divertida','carrinho rosa com aspirador')
_CHEMICAL_TERMS=(
    'pesticida','inseticida','veneno','raticida','herbicida','acido muriatico','soda caustica',
    'cloro concentrado','desinfetante hospitalar','mata virus','mata bacterias','germicida',
)


def strict_valid_product(product):
    if not _original(product): return False
    if not bool(product_policy_check(product).get('accepted')): return False
    title=_norm(product.get('productName') or '')
    if not title: return False
    if title.startswith(_ACCESSORY_PREFIXES): return False
    if any(term in title for term in _ACCESSORY_TERMS): return False
    if any(term in title for term in _TOY_TERMS): return False
    if any(term in title for term in _CHEMICAL_TERMS): return False
    return True

base.valid_product=strict_valid_product
_real=base.criar_servico_blogger; base.PAGE_ID=POST_ID; base.criar_servico_blogger=lambda: BloggerPostTargetProxy(_real())
if __name__=='__main__':
    if not base.DRY_RUN: patch_store_layout()
    base.main()
