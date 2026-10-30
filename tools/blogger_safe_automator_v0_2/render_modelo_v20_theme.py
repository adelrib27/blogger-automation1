#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
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
    p = argparse.ArgumentParser(description="Renderiza o TEMA MODELO V20 para um blog novo.")
    p.add_argument("--template-theme", required=True)
    p.add_argument("--blog-title", required=True)
    p.add_argument("--blog-url", required=True)
    p.add_argument("--output-theme", required=True)
    args = p.parse_args()

    src = Path(args.template_theme).resolve()
    out = Path(args.output_theme).resolve()
    if not src.exists():
        raise SystemExit("Template V20 não encontrado.")

    text = src.read_text(encoding="utf-8")
    if MARKER not in text:
        raise SystemExit(f"Template não contém o marcador V20: {MARKER}")
    if TITLE_TOKEN not in text or URL_TOKEN not in text:
        raise SystemExit("Template não contém os tokens de identidade esperados.")

    title = args.blog_title.strip()
    url = normalize_url(args.blog_url)
    text = text.replace(TITLE_TOKEN, title)
    text = text.replace(URL_TOKEN + "/", url)
    text = text.replace(URL_TOKEN, url.rstrip("/"))

    if TITLE_TOKEN in text or URL_TOKEN in text:
        raise SystemExit("Renderização incompleta: tokens ainda presentes.")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    ET.parse(out)

    print(json.dumps({
        "status": "BLOGGER_MODELO_V20_THEME_RENDERED",
        "template": str(src),
        "output": str(out),
        "blog_title": title,
        "blog_url": url,
        "size_bytes": out.stat().st_size,
        "sha256": sha256(out),
        "xml_valid": True,
        "marker": MARKER,
        "inherits_posts": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
