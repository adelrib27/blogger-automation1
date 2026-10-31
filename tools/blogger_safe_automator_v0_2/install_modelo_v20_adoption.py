#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

MARKER = "emporio-revisao-visual-20-modelo-final"
STORE_MARKER = "BLOGGER_MODELO_V20_STORE_EXTENSION"
SOURCE_TITLE = "Guia de Achados & Ofertas"
SOURCE_URL = "https://guia-de-achados-e-ofertas.blogspot.com/"


def run(cmd: list[str]) -> None:
    print("\n>>> " + " ".join(f'"{x}"' if " " in x else x for x in cmd), flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Adota o TEMA MODELO V20 em um blog existente, preservando todos os posts.")
    p.add_argument("--expected-blog-id", required=True)
    p.add_argument("--blog-title", required=True)
    p.add_argument("--blog-url", required=True)
    p.add_argument("--palette", default="auto")
    p.add_argument("--confirm", required=True)
    args = p.parse_args()

    if args.confirm != "ADOPT MODEL V20":
        raise SystemExit('Confirmação inválida. Use exatamente: ADOPT MODEL V20')

    here = Path(__file__).resolve().parent
    root = here.parents[1]
    python = sys.executable

    source_theme = root / "themes" / "blogger_emporio_v1_0" / "generated" / "theme.xml"
    template_theme = root / "themes" / "blogger_modelo_v20" / "theme.xml.tpl"
    # apply_theme_safe.py intentionally requires the upload file to be named
    # exactly "theme.xml". Keep each blog isolated in its own rendered folder.
    rendered_theme = root / "themes" / "blogger_modelo_v20" / "rendered" / str(args.expected_blog_id) / "theme.xml"
    backup_theme = root.parent / "backups" / "blogger" / args.expected_blog_id / "theme-before-modelo-v20-adoption.xml"

    freeze = here / "freeze_modelo_v20_theme.py"
    render = here / "render_modelo_v20_theme.py"
    extend_store = here / "extend_modelo_v20_store.py"
    backup = here / "backup_theme_auto.py"
    apply = here / "apply_theme_auto.py"

    for required in (source_theme, freeze, render, extend_store, backup, apply):
        if not required.exists():
            raise SystemExit(f"Arquivo obrigatório ausente: {required}")

    if not template_theme.exists():
        template_theme.parent.mkdir(parents=True, exist_ok=True)
        run([
            python, str(freeze),
            "--source-theme", str(source_theme),
            "--source-title", SOURCE_TITLE,
            "--source-url", SOURCE_URL,
            "--output-template", str(template_theme),
        ])
    else:
        print(f"Template V20 já existe: {template_theme}")

    rendered_theme.parent.mkdir(parents=True, exist_ok=True)
    run([
        python, str(render),
        "--template-theme", str(template_theme),
        "--blog-title", args.blog_title,
        "--blog-url", args.blog_url,
        "--output-theme", str(rendered_theme),
        "--palette", args.palette,
    ])

    # Extensão oficial da LOJA: idempotente, isolada à página /p/loja.html e
    # aplicada antes do backup/upload para que toda adoção V20 use o padrão validado.
    run([
        python, str(extend_store),
        "--theme-path", str(rendered_theme),
    ])

    backup_theme.parent.mkdir(parents=True, exist_ok=True)
    run([
        python, str(backup),
        "--expected-blog-id", args.expected_blog_id,
        "--output", str(backup_theme),
    ])

    run([
        python, str(apply),
        "--expected-blog-id", args.expected_blog_id,
        "--theme-path", str(rendered_theme),
        "--backup-path", str(backup_theme),
        "--public-url", args.blog_url,
        "--public-marker", MARKER,
        "--confirm", "APPLY THEME",
    ])

    rendered_text = rendered_theme.read_text(encoding="utf-8")
    if STORE_MARKER not in rendered_text:
        raise SystemExit("Adoção V20 terminou sem a extensão LOJA no tema renderizado.")

    print(json.dumps({
        "status": "BLOGGER_MODELO_V20_ADOPTED",
        "blog_id": args.expected_blog_id,
        "blog_title": args.blog_title,
        "blog_url": args.blog_url,
        "palette": args.palette,
        "template_theme": str(template_theme),
        "rendered_theme": str(rendered_theme),
        "backup_theme": str(backup_theme),
        "public_marker": MARKER,
        "store_extension_marker": STORE_MARKER,
        "store_menu_path": "/p/loja.html",
        "store_menu_position": "after-home",
        "store_menu_highlighted": True,
        "store_layout": {"max_width": 1280, "desktop_columns": 4, "tablet_columns": 2, "mobile_columns": 2},
        "store_sidebar_hidden_only": True,
        "existing_posts_policy": "PRESERVE_ALL",
        "posts_deleted": False,
        "posts_copied_from_reference": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
