#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

TOKEN = "{{BLOG_TITLE}}"


def main() -> int:
    p = argparse.ArgumentParser(description="Renderiza as páginas do BLOGGER_MODELO_V20, incluindo a LOJA automatizada.")
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
            "requires_store_population": bool(page.get("requires_store_population", False)),
            "store_expected_products": page.get("store_expected_products"),
            "store_expected_categories": page.get("store_expected_categories"),
            "store_auto_start_marker": page.get("store_auto_start_marker"),
            "store_auto_end_marker": page.get("store_auto_end_marker"),
            "content": content,
        })

    if len(rendered) != 6:
        raise SystemExit(f"Modelo V20 precisa renderizar exatamente 6 páginas; obtido {len(rendered)}.")
    store = next((p for p in rendered if p["key"] == "loja"), None)
    if not store or not store["requires_store_population"]:
        raise SystemExit("Modelo V20 inválido: página LOJA automatizada ausente.")
    if store["store_expected_products"] != 20 or store["store_expected_categories"] != 5:
        raise SystemExit("Contrato da LOJA inválido: esperado 20 produtos em 5 categorias.")
    if not store["store_auto_start_marker"] or not store["store_auto_end_marker"]:
        raise SystemExit("Contrato da LOJA inválido: marcadores automáticos ausentes.")

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
        "store_scaffold_included": True,
        "store_expected_products": 20,
        "store_expected_categories": 5,
        "store_layout": {"desktop_columns": 4, "tablet_columns": 2, "mobile_columns": 2},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
