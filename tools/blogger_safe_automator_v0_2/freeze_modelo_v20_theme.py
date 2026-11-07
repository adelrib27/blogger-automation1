#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER = "emporio-revisao-visual-20-modelo-final"
TITLE_TOKEN = "__BLOG_TITLE__"
URL_TOKEN = "__BLOG_URL__"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normalize_url(value: str) -> str:
    value = value.strip().rstrip("/")
    return value + "/"


def main() -> int:
    p = argparse.ArgumentParser(description="Congela a V20 validada como template limpo e reutilizável.")
    p.add_argument("--source-theme", required=True)
    p.add_argument("--source-title", required=True)
    p.add_argument("--source-url", required=True)
    p.add_argument("--output-template", required=True)
    args = p.parse_args()

    src = Path(args.source_theme).resolve()
    out = Path(args.output_template).resolve()
    if not src.exists():
        raise SystemExit("Tema-fonte não encontrado.")

    text = src.read_text(encoding="utf-8")
    if MARKER not in text:
        raise SystemExit(f"Tema-fonte não é a V20 validada: marcador ausente {MARKER}")

    source_title = args.source_title.strip()
    source_url = normalize_url(args.source_url)
    source_url_no_slash = source_url.rstrip("/")

    # Remove identidade fixa do blog-modelo. O Blogger continuará usando dados dinâmicos
    # onde o tema já usa data:blog.*, e nossos blocos customizados passam a usar tokens.
    text = text.replace(source_title, TITLE_TOKEN)
    text = text.replace(source_url, URL_TOKEN + "/")
    text = text.replace(source_url_no_slash, URL_TOKEN)

    # Proteção: nenhum URL público do blog-fonte pode restar.
    if "guia-de-achados-e-ofertas.blogspot.com" in text:
        raise SystemExit("Ainda restou URL fixa do blog-modelo no template.")

    # O tema não deve carregar conteúdo de produto/post como configuração estática.
    forbidden = [
        "Airfryer Gourmet com Forma de Vidro",
        "Luminária retrô LED recarregável",
        "Cafeteira elétrica para até 30 xícaras",
        "Carrinho organizador de aço com 3 prateleiras",
        "s.shopee.com.br/",
    ]
    leftovers = [item for item in forbidden if item in text]
    if leftovers:
        raise SystemExit("Conteúdo de post/produto encontrado no template: " + ", ".join(leftovers))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    # Tokens não são XML inválido; continuam texto normal, portanto validamos estrutura.
    ET.parse(out)

    print(json.dumps({
        "status": "BLOGGER_MODELO_V20_THEME_FROZEN",
        "source": str(src),
        "output": str(out),
        "size_bytes": out.stat().st_size,
        "sha256": sha256(out),
        "xml_valid": True,
        "marker": MARKER,
        "title_token": TITLE_TOKEN,
        "url_token": URL_TOKEN,
        "posts_embedded": False,
        "source_identity_removed": True,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
