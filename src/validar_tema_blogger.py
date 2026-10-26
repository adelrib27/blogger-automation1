#!/usr/bin/env python3
"""Valida invariantes estruturais do tema mestre do Blogger sem chamadas externas."""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "blogger_themes" / "BASE-VISUAL-SHOPEE-BLOGGER-MESTRE-V3.0.xml"


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

    checks = {
        "widget Blog1 presente": "id='Blog1'" in source and "type='Blog'" in source,
        "home lista posts dinâmicos": "cond='data:view.isHomepage'" in source and "values='data:posts' var='post'" in source,
        "link de card usa permalink do post": "expr:href='data:post.url'" in source,
        "artigo individual renderiza o corpo": "cond='data:view.isPost'" in source and "<div class='post-body'><data:post.body/></div>" in source,
        "página institucional renderiza o corpo": "cond='data:view.isPage'" in source and "<data:post.body/>" in source,
        "paginação disponível": "data:olderPageUrl" in source and "data:newerPageUrl" in source,
        "título do blog dinâmico": "<data:blog.title/>" in source,
        "widget principal não é ocultado": not re.search(r"#(?:page_body|Blog1)\s*\{\s*display\s*:\s*none", source, re.I),
        "sem marca/modelo específico": not re.search(r"liquidificador|britânia|britania|blq1300p|air\s*fryer", source, re.I),
        "sem URL de artigo/afiliado hardcoded": not re.search(r"(?:href|src)=['\"]https?://", source, re.I),
    }

    failed = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f"{'OK' if passed else 'FALHA'} — {name}")

    if failed:
        print(f"\nValidação reprovada: {len(failed)} teste(s) falharam.")
        return 1

    print(f"\nValidação aprovada: {len(checks)} verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
