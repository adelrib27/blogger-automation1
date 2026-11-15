"""Classificação conservadora de categorias e nichos, sem chamada a API.

A classificação precede a conversão. Produtos não classificados, ambíguos
ou com bloqueios semânticos não entram na fila de links.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

TAXONOMY_PATH = Path(__file__).with_name("taxonomy.json")


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


@lru_cache(maxsize=512)
def phrase_regex(phrase: str):
    value = normalize(phrase)
    if not value or len(value) > 120:
        raise ValueError("Expressão de nicho inválida")
    # Borda de token impede "mop" corresponder em "amop" e "batom" em "batomera".
    return re.compile(r"(?<![a-z0-9])" + re.escape(value).replace(r"\ ", r"\s+") + r"(?![a-z0-9])")


@dataclass(frozen=True)
class Classification:
    category: str
    niche: str
    status: str
    reason: str
    version: str


@lru_cache(maxsize=1)
def rules() -> tuple[str, tuple]:
    doc = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    version = doc.get("version")
    if not isinstance(version, str) or not version.startswith("v31-editorial-taxonomy-"):
        raise ValueError("Versão inválida da taxonomia")
    compiled = []
    seen = set()
    for entry in doc.get("niches", []):
        cat, niche = entry["category"], entry["niche"]
        if not re.fullmatch(r"[a-z0-9_]{2,40}", cat) or not re.fullmatch(r"[a-z0-9_]{2,50}", niche):
            raise ValueError("Chave de categoria/nicho inválida")
        if (cat, niche) in seen:
            raise ValueError("Duplicata de nicho")
        seen.add((cat, niche))
        inc = entry.get("terms") or []
        exc = entry.get("exclude") or []
        if not inc or not all(isinstance(t, str) and normalize(t) for t in inc + exc):
            raise ValueError("Lista de termos inválida")
        compiled.append((cat, niche, tuple(phrase_regex(x) for x in inc),
                         tuple(phrase_regex(x) for x in exc)))
    if not compiled:
        raise ValueError("Taxonomia vazia")
    return version, tuple(compiled)


def classify_title(title: str) -> Classification:
    version, compiled = rules()
    norm = normalize(title)
    if not norm:
        return Classification("", "", "review", "empty_title", version)
    matched = []
    excluded = False
    for category, niche, positive, negative in compiled:
        if any(pattern.search(norm) for pattern in positive):
            if any(pattern.search(norm) for pattern in negative):
                excluded = True
            else:
                matched.append((category, niche))
    if excluded:
        return Classification("", "", "review", "excluded_accessory_or_semantics", version)
    if not matched:
        return Classification("", "", "review", "unclassified", version)
    if len(matched) > 1:
        return Classification("", "", "review", "ambiguous_niches", version)
    cat, niche = matched[0]
    return Classification(cat, niche, "matched", "exact_phrase", version)
