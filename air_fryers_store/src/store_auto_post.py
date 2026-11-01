#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import os
import re
import unicodedata
from pathlib import Path

import store_auto as base
from post_target_proxy import BloggerPostTargetProxy

# Carrega explicitamente o patch LOCAL desta Loja para evitar colisão com
# blogger_product_store/src/store_layout_patch.py já importado pelo motor base.
_patch_path = Path(__file__).resolve().parent / "store_layout_patch.py"
_patch_spec = importlib.util.spec_from_file_location("air_fryers_store_layout_patch", _patch_path)
if _patch_spec is None or _patch_spec.loader is None:
    raise RuntimeError("Não foi possível carregar o patch local da Loja Air Fryers.")
_patch_mod = importlib.util.module_from_spec(_patch_spec)
_patch_spec.loader.exec_module(_patch_mod)
patch_store_layout = _patch_mod.patch_store_layout

POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "5189023277801568424").strip()
if not POST_ID:
    raise RuntimeError("BLOGGER_STORE_POST_ID ausente.")


def _norm(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", text).strip()


_original_valid_product = base.valid_product

POLICY_BLOCKED = (
    "cerveja", "whisky", "vodka", "vinho alcoolico", "vinho alcoólico", "cigarro", "tabaco",
    "vape", "pod descartavel", "pod descartável", "nicotina", "cbd", "thc", "maconha",
    "cogumelo magico", "cogumelo mágico", "magic mushroom", "arma de fogo", "municao", "munição",
    "rifle", "pistola", "revolver", "revólver", "cassino", "aposta esportiva", "bet online",
    "anabolizante", "esteroide", "esteróide", "hormonio", "hormônio", "medicamento controlado",
    "remedio controlado", "remédio controlado", "emagrecedor proibido", "dnp",
)


def strict_valid_product(product):
    if not _original_valid_product(product):
        return False
    title = _norm(product.get("productName") or "")
    if not title:
        return False
    if any(token in title for token in POLICY_BLOCKED):
        return False
    return True


base.valid_product = strict_valid_product
_real_factory = base.criar_servico_blogger
base.PAGE_ID = POST_ID
base.criar_servico_blogger = lambda: BloggerPostTargetProxy(_real_factory())

if __name__ == "__main__":
    if not base.DRY_RUN:
        patch_store_layout()
    base.main()
