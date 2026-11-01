#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import os
from pathlib import Path

import store_auto as base
from blogger_policy_guard import product_policy_check
from post_target_proxy import BloggerPostTargetProxy

_patch_path = Path(__file__).resolve().parent / "store_layout_patch.py"
_patch_spec = importlib.util.spec_from_file_location("ventiladores_store_layout_patch", _patch_path)
if _patch_spec is None or _patch_spec.loader is None:
    raise RuntimeError("Não foi possível carregar o patch local da Loja Ventiladores.")
_patch_mod = importlib.util.module_from_spec(_patch_spec)
_patch_spec.loader.exec_module(_patch_mod)
patch_store_layout = _patch_mod.patch_store_layout

POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "1410775502611365606").strip()
if not POST_ID:
    raise RuntimeError("BLOGGER_STORE_POST_ID ausente.")

_original_valid_product = base.valid_product


def strict_valid_product(product):
    if not _original_valid_product(product):
        return False
    return bool(product_policy_check(product).get("accepted"))


base.valid_product = strict_valid_product
_real_factory = base.criar_servico_blogger
base.PAGE_ID = POST_ID
base.criar_servico_blogger = lambda: BloggerPostTargetProxy(_real_factory())

if __name__ == "__main__":
    if not base.DRY_RUN:
        patch_store_layout()
    base.main()
