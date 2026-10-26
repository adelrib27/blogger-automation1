#!/usr/bin/env python3
"""Valida a versão editorial derivada do tema Blogger funcional Achados para Casa V2."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "blogger_themes" / "TEMA-EDITORIAL-BLOGGER-ACHADOS-V1.0.xml"


def main() -> int:
    if not THEME.exists():
        print(f"FALHA — tema não encontrado: {THEME}")
        return 1

    source = THEME.read_text(encoding="utf-8")
    try:
        ET.parse(THEME)
    except ET.ParseError as exc:
        print(f"FALHA — XML malformado: {exc}")
        return 1

    blog_start = source.find("<b:widget id='Blog1'")
    blog_end = source.find("</b:widget>", blog_start) if blog_start >= 0 else -1
    blog_widget = source[blog_start:blog_end] if blog_start >= 0 and blog_end >= 0 else ""

    checks = {
        "XML bem formado": True,
        "Base Contempo 1.3.3 preservada": "b:templateVersion='1.3.3'" in source,
        "Widget nativo Blog1 presente": bool(re.search(
            r"<b:widget\b(?=[^>]*\bid='Blog1')(?=[^>]*\btype='Blog')[^>]*>",
            source,
            re.S,
        )),
        "Blog1 delega a renderização ao Blogger": "<b:include name='super.main'/>" in blog_widget,
        "Widget de destaque da página inicial preservado": (
            "id='FeaturedPost1'" in source
            and "cond='data:view.isHomepage'" in source
            and "name='showPostTitle'>true" in source
        ),
        "Links de artigos usam rota genérica": "<a href='/search?max-results=10'>Artigos</a>" in source,
        "Nome e descrição do blog são dinâmicos": (
            "<strong><data:blog.title/></strong>" in source
            and "<data:blog.description/>" in source
        ),
        "Sem URL ou nome fixo do Achados para Casa": (
            "achadosparacasa2026.blogspot.com" not in source
            and "Achados para Casa" not in source
        ),
        "Sem categorias específicas fixadas no menu": not any(
            term in source for term in ("Cozinha", "Quarto", "Banheiro", "Organização", "Casa e Decoração")
        ),
        "Sem CSS específico de produto": "produto-principal-contextual" not in source,
        "Sem links para páginas institucionais ainda não criadas": not any(
            path in source for path in (
                "/p/sobre.html", "/p/contato.html",
                "/p/politica-de-privacidade.html", "/p/termos-de-uso.html"
            )
        ),
        "Divulgação de afiliados condicional mantida": (
            "Quando houver links de afiliados" in source
        ),
        "Layout responsivo e viewport": (
            "name='viewport'" in source and "max-width:800px" in source
        ),
        "Permalinks nativos dos posts preservados": "data:post.url" in blog_widget,
    }

    for name, passed in checks.items():
        print(f"{'OK' if passed else 'FALHA'} — {name}")

    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        print(f"\nValidação reprovada: {len(failed)} teste(s) falharam.")
        return 1

    print(f"\nValidação estrutural aprovada: {len(checks)} verificações passaram.")
    print("Isso não substitui a instalação manual e a conferência da home e de um permalink no Blogger.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
