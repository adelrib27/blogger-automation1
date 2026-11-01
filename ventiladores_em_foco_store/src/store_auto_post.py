#!/usr/bin/env python3
from __future__ import annotations
import os
import re
import unicodedata
import store_auto as base
from post_target_proxy import BloggerPostTargetProxy
from store_layout_patch import patch_store_layout

POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "1410775502611365606").strip()
if not POST_ID:
    raise RuntimeError("BLOGGER_STORE_POST_ID ausente.")


def _norm(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", text).strip()


_original_valid_product = base.valid_product


def strict_valid_product(product):
    if not _original_valid_product(product):
        return False
    title = _norm(product.get("productName") or "")
    if not ("ventilador" in title or "circulador" in title):
        return False
    blocked = (
        "helice avulsa", "helice para ventilador", "motor para ventilador", "motor ventilador",
        "capacitor", "grade para ventilador", "grade ventilador", "peca ventilador",
        "pecas ventilador", "reposicao", "kit reparo", "rolamento", "eixo", "parafuso",
        "carcaca", "suporte avulso", "base avulsa", "botao ventilador", "placa ventilador",
        "controle remoto avulso", "controle para ventilador", "capa para ventilador",
        "adaptador para ventilador",
    )
    return not any(token in title for token in blocked)


base.valid_product = strict_valid_product
_real_factory = base.criar_servico_blogger
base.PAGE_ID = POST_ID
base.criar_servico_blogger = lambda: BloggerPostTargetProxy(_real_factory())

if __name__ == "__main__":
    patch_store_layout()
    base.main()
