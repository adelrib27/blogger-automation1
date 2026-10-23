#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import unicodedata

import store_auto as base
from post_target_proxy import BloggerPostTargetProxy
from store_layout_patch import patch_store_layout

POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "8867555367475283866").strip()
if not POST_ID:
    raise RuntimeError("BLOGGER_STORE_POST_ID ausente.")


def _norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", text).strip()


_original_valid_product = base.valid_product


def strict_valid_product(product: dict) -> bool:
    """Guarda final de intenção para impedir acessórios disfarçados de produto principal."""
    if not _original_valid_product(product):
        return False

    title = _norm(product.get("productName") or "")

    if "liquidificador" in title:
        accessory_prefix = re.compile(
            r"^(?:kit\s+)?(?:copo|jarra|tampa|sobretampa|lamina|acoplamento|anel|escova|peca|motor)\b"
        )
        if accessory_prefix.search(title):
            return False
        if "compativel" in title and any(
            token in title for token in ("copo", "jarra", "tampa", "lamina", "acoplamento", "anel", "peca")
        ):
            return False

    if ("balanca" in title or "dosador" in title) and any(
        token in title for token in ("racao", "pet", "cachorro", "gato")
    ):
        return False

    return True


base.valid_product = strict_valid_product

_real_factory = base.criar_servico_blogger
base.PAGE_ID = POST_ID
base.criar_servico_blogger = lambda: BloggerPostTargetProxy(_real_factory())

if __name__ == "__main__":
    patch_store_layout()
    base.main()
