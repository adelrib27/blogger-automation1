#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

TOKEN = "{{BLOG_TITLE}}"


def main() -> int:
    p = argparse.ArgumentParser(description="Renderiza as páginas institucionais do BLOGGER_MODELO_V20.")
    p.add_argument("--pages-template", required=True)
    p.add_argument("--blog-title", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    src = Path(args.pages_template).resolve()
    out = Path(args.output).resolve()
    data = json.loads(src.read_text(encoding="utf-8"))
    if data.get("model") != "BLOGGER_MODELO_V20":
        raise SystemExit("Arquivo de páginas não pertence ao BLOGGER_MODELO_V20.")
    if data.get("inherit_posts") is not False:
        raise SystemExit("Modelo inválido: inherit_posts precisa ser false.")

    title = args.blog_title.strip()
    rendered = []
    for page in data.get("pages", []):
        content = str(page.get("content", "")).replace(TOKEN, title)
        if TOKEN in content:
            raise SystemExit(f"Token não resolvido na página {page.get('key')}")
        rendered.append({
            "key": page["key"],
            "title": page["title"],
            "expected_slug": page["expected_slug"],
            "publish": bool(page.get("publish", True)),
            "requires_theme_contact_runtime": bool(page.get("requires_theme_contact_runtime", False)),
            "content": content,
        })

    payload = {
        "model": "BLOGGER_MODELO_V20",
        "blog_title": title,
        "inherit_posts": False,
        "pages": rendered,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": "BLOGGER_MODELO_V20_PAGES_RENDERED",
        "output": str(out),
        "page_count": len(rendered),
        "page_keys": [p["key"] for p in rendered],
        "inherit_posts": False,
        "contact_form_included": any(p["key"] == "contato" and p["requires_theme_contact_runtime"] for p in rendered),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
