#!/usr/bin/env python3
"""Valida invariantes estruturais do tema editorial independente do Blogger."""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "blogger_themes" / "TEMA-EDITORIAL-BLOGGER-INDEPENDENTE-V1.0.xml"


def main() -> int:
    if not THEME.exists():
        print(f"FALHA: tema não encontrado: {THEME}")
        return 1

    source = THEME.read_text(encoding="utf-8")
    try:
        ET.parse(THEME)
    except ET.ParseError as exc:
        print(f"FALHA: XML malformado: {exc}")
        return 1

    section_match = re.search(
        r"<b:section\s+id=['\"]page_body['\"][^>]*>\s*"
        r"<b:widget\s+id=['\"]Blog1['\"][^>]*>",
        source,
        re.S,
    )
    intro_start = source.find("<section class='home-intro'>")
    intro_end = source.find("</section>", intro_start) if intro_start >= 0 else -1
    intro_if_end = source.find("</b:if>", intro_end) if intro_end >= 0 else -1
    section_start = source.find("<b:section id='page_body'")

    checks = {
        "XML bem formado": True,
        "Blog1 associado à seção page_body": section_match is not None,
        "widget Blog1 usa versão 2": bool(re.search(
            r"<b:widget\b(?=[^>]*\bid=['\"]Blog1['\"])(?=[^>]*\bversion=['\"]2['\"])[^>]*>",
            source,
            re.S,
        )),
        "seção Blog1 fica fora do condicional exclusivo da home": (
            intro_if_end >= 0 and section_start > intro_if_end
        ),
        "home lista publicações dinamicamente": (
            "cond='data:view.isHomepage'" in source
            and "values='data:posts' var='post'" in source
        ),
        "cards usam permalink real de cada post": "expr:href='data:post.url'" in source,
        "imagem de capa usa a imagem do post": "data:post.firstImageUrl" in source,
        "artigo individual renderiza título e corpo": (
            "cond='data:view.isPost'" in source
            and "<h1><data:post.title/></h1>" in source
            and "<div class='article-content post-body'><data:post.body/></div>" in source
        ),
        "página institucional renderiza o conteúdo salvo": (
            "cond='data:view.isPage'" in source
            and "<div class='article-content post-body'><data:post.body/></div>" in source
        ),
        "paginação para listas longas": (
            "data:olderPageUrl" in source and "data:newerPageUrl" in source
        ),
        "metadados básicos e URL canônica": (
            "name='description'" in source
            and "property='og:title'" in source
            and "rel='canonical'" in source
        ),
        "layout responsivo e acessibilidade básica": (
            "name='viewport'" in source
            and "@media(max-width:600px)" in source
            and "skip-link" in source
            and "prefers-reduced-motion:reduce" in source
        ),
        "sem conteúdo específico de loja ou CTA comercial": not re.search(
            r"shopee|comprar agora|carrinho|preço do produto|oferta afiliada|link de afiliado",
            source,
            re.I,
        ),
        "sem URL externa hardcoded em href/src": not re.search(
            r"(?:href|src)=['\"]https?://",
            source,
            re.I,
        ),
    }

    failed = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f"{'OK' if passed else 'FALHA'} — {name}")

    if failed:
        print(f"\nValidação reprovada: {len(failed)} teste(s) falharam.")
        return 1

    print(f"\nValidação estrutural aprovada: {len(checks)} verificações passaram.")
    print("A renderização pública do Blogger ainda exige teste após instalar o XML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
