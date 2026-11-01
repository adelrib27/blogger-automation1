#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os
from pathlib import Path
import store_auto as base
from blogger_policy_guard import product_policy_check
from post_target_proxy import BloggerPostTargetProxy
POST_ID=os.getenv('BLOGGER_STORE_POST_ID','6383277011247909539').strip()
if not POST_ID: raise RuntimeError('BLOGGER_STORE_POST_ID ausente.')
_original=base.valid_product
def strict_valid_product(product):
    if not _original(product): return False
    return bool(product_policy_check(product).get('accepted'))
base.valid_product=strict_valid_product
_real=base.criar_servico_blogger; base.PAGE_ID=POST_ID; base.criar_servico_blogger=lambda: BloggerPostTargetProxy(_real())
if __name__=='__main__': base.main()
