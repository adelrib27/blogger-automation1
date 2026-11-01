#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import unicodedata

import store_auto as base
from post_target_proxy import BloggerPostTargetProxy
from store_layout_patch import patch_store_layout

POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "115613719594316807").strip()
if not POST_ID:
    raise RuntimeError("BLOGGER_STORE_POST_ID ausente.")


def _norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", text).strip()


_original_valid_product = base.valid_product


def strict_valid_product(product: dict) -> bool:
    if not _original_valid_product(product):
        return False
    title = _norm(product.get("productName") or "")
    blocked = (
        "capa para sapateira", "forma air fryer", "forma para air fryer", "botao air fryer",
        "resistencia air fryer", "spray limpa air fryer", "pulseira para smartwatch",
        "pelicula smartwatch", "capa smartwatch", "case smartwatch", "capa para fone",
        "case para fone", "difusor para secador", "lamina para aparador",
        "refil escova secadora", "tampa para garrafa", "capa de chuva para mochila",
        "helice ventilador", "motor ventilador",
    )
    if any(x in title for x in blocked):
        return False
    if ("air fryer" in title or "fritadeira" in title) and any(x in title for x in ("forma", "cesto", "papel", "forro", "tapete", "botao", "resistencia", "peca", "acessorio")):
        return False
    if "smartwatch" in title and any(x in title for x in ("pulseira", "pelicula", "capa", "case", "carregador", "cabo", "protetor")):
        return False
    if "fone" in title and any(x in title for x in ("capa", "case", "estojo", "almofada", "ponteira")):
        return False
    return True


base.valid_product = strict_valid_product

_real_factory = base.criar_servico_blogger
base.PAGE_ID = POST_ID
base.criar_servico_blogger = lambda: BloggerPostTargetProxy(_real_factory())

if __name__ == "__main__":
    patch_store_layout()
    base.main()
