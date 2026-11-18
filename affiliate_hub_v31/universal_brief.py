"""Brief editorial genérico para assunto fornecido NA CRIAÇÃO do blog.

Não presume nichos, atributos, preço, avaliação ou dados comerciais.
O título é apenas proposta para revisão; a redação original/publicação
permanecem a cargo do gerador Blogger/WordPress autorizado.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata

ANGLES = ("criterios", "comparacao", "uso", "cuidados", "perguntas",
          "vantagens_limites", "escolha", "alternativas")
MAX_TITLE=120


class UniversalBriefError(ValueError):
    pass


def _plain(s: str) -> str:
    s=unicodedata.normalize("NFKD",s.casefold())
    s="".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9]+"," ",s)).strip()


def create_universal_brief(*, topic: str, product_title: str,
                           product_key: str, article_index: int) -> dict:
    if (not isinstance(topic,str) or not topic.strip() or len(topic)>160 or
        not isinstance(product_title,str) or not product_title.strip() or
        not isinstance(product_key,str) or not 3<=len(product_key)<=150 or
        type(article_index) is not int or not 1<=article_index<=24):
        raise UniversalBriefError("invalid_brief_input")
    keyword=" ".join(topic.split())
    angle=ANGLES[(article_index-1)%len(ANGLES)]
    subject=" ".join(product_title.split())
    prefix=keyword[:64].rstrip(" -:,")
    if not prefix:
        raise UniversalBriefError("invalid_keyword")
    suffix=f" — {subject}"
    room=MAX_TITLE-len(prefix)-len("Guia: ")-len(suffix)
    if room<0:
        suffix=suffix[:max(0,MAX_TITLE-len(prefix)-len("Guia: "))].rstrip(" -:,")
    title=f"Guia: {prefix}{suffix}"
    if len(title)>MAX_TITLE or not _plain(prefix):
        raise UniversalBriefError("invalid_generated_title")
    digest=hashlib.sha256(
        f"{product_key}|{angle}|{article_index}".encode()).hexdigest()[:12]
    slug="-".join(_plain(title).split())[:95].strip("-")+"-"+digest
    return {
        "proposed_title":title,
        "keyword":prefix,
        "topic":keyword,
        "angle":angle,
        "slug":slug,
        "editorial_status":"REVIEW_REQUIRED",
        "product_specs_verified":False,
        "original_article_required":True,
        "can_publish":False,
    }
