#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import store_auto as base
from blogger_policy_guard import product_policy_check
from post_target_proxy import BloggerPostTargetProxy

_patch_path=Path(__file__).resolve().parent/'store_layout_patch.py'
_spec=importlib.util.spec_from_file_location('eletroportateis_store_layout_patch',_patch_path)
_layout=importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_layout)
patch_store_layout=_layout.patch_store_layout

POST_ID=os.getenv('BLOGGER_STORE_POST_ID','2599179962359747947').strip()
if not POST_ID:
    raise RuntimeError('BLOGGER_STORE_POST_ID ausente.')

_original=base.valid_product
def strict_valid_product(product):
    if not _original(product):
        return False
    return bool(product_policy_check(product).get('accepted'))

base.valid_product=strict_valid_product
_real=base.criar_servico_blogger
base.PAGE_ID=POST_ID
base.criar_servico_blogger=lambda: BloggerPostTargetProxy(_real())

if __name__=='__main__':
    if not base.DRY_RUN:
        patch_store_layout()
    base.main()
