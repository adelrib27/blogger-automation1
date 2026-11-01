#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import os
import re
import unicodedata
from pathlib import Path

import store_auto as base
from post_target_proxy import BloggerPostTargetProxy

# Carrega explicitamente o patch deste blog. O store_auto adiciona o motor comum
# ao sys.path, então um import simples pode resolver para o módulo genérico.
_LOCAL_LAYOUT = Path(__file__).resolve().with_name("store_layout_patch.py")
_spec = importlib.util.spec_from_file_location("ventiladores_em_foco_store_layout_patch", _LOCAL_LAYOUT)
_layout = importlib.util.module_from_spec(_spec)
if not _spec or not _spec.loader:
    raise RuntimeError("Não foi possível carregar o layout patch local de Ventiladores em Foco.")
_spec.loader.exec_module(_layout)
patch_store_layout = _layout.patch_store_layout

POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "1410775502611365606").strip()
if not POST_ID:
    raise RuntimeError("BLOGGER_STORE_POST_ID ausente.")


def _norm(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", text).strip()


_original_valid_product = base.valid_product

# Peças/acessórios que podem aparecer antes da palavra “ventilador” no título e
# escapar de bloqueios por frase exata (ex.: “Hélice Ventilador...”, “Base Ventilador...”).
_COMPONENT_PREFIXES = (
    "helice ", "base ", "capa ", "motor ", "capacitor ", "grade ",
    "controle ", "suporte ", "rolamento ", "eixo ", "parafuso ",
    "carcaca ", "placa ", "botao ", "adaptador ", "peca ", "pecas ",
)


def strict_valid_product(product):
    if not _original_valid_product(product):
        return False
    title = _norm(product.get("productName") or "")
    if not ("ventilador" in title or "circulador" in title):
        return False

    # Bloqueia títulos cujo objeto principal é claramente uma peça/acessório.
    if title.startswith(_COMPONENT_PREFIXES):
        return False

    blocked = (
        "helice avulsa", "helice para ventilador", "helice ventilador",
        "motor para ventilador", "motor ventilador", "capacitor",
        "grade para ventilador", "grade ventilador", "peca ventilador",
        "pecas ventilador", "reposicao", "kit reparo", "rolamento", "eixo", "parafuso",
        "carcaca", "suporte avulso", "base avulsa", "base ventilador",
        "botao ventilador", "placa ventilador", "controle remoto avulso",
        "controle para ventilador", "capa para ventilador", "capa ventilador",
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
