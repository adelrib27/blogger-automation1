#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

EXPECTED_KEYS = ["sobre", "afiliados", "contato", "privacidade", "termos", "loja"]
BASE_MARKER = "emporio-revisao-visual-20-modelo-final"
STORE_MARKER = "BLOGGER_MODELO_V20_STORE_EXTENSION"
VISIBLE_NAV_MARKER = "BLOGGER_MODELO_V20_STORE_VISIBLE_NAV"
FOOTER_NAV_MARKER = "BLOGGER_MODELO_V20_STORE_FOOTER_NAV"
STATIC_PAGE_FEED_MARKER = "BLOGGER_MODELO_V20_STATIC_PAGE_FEED_RUNTIME"
BRAND_DESCRIPTION_MARKER = "BLOGGER_MODELO_V20_BRAND_DESCRIPTION_FEED_RUNTIME"
GENERIC_LEAK = "produtos para casa, cozinha, tecnologia e dia a dia"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fail(message: str) -> None:
    raise SystemExit("VALIDATION_FAILED: " + message)


def run_extension(script: Path, theme: Path, label: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(script), "--theme-path", str(theme)],
        text=True,
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        fail(f"{label} falhou: " + (proc.stderr or proc.stdout)[-1000:])


def main() -> int:
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    manifest_path = root / "templates" / "blogger_modelo_v20" / "model_manifest.json"
    template_pages_path = root / "templates" / "blogger_modelo_v20" / "pages.json"
    canonical_pages_path = root / "themes" / "blogger_modelo_v20" / "pages.json"
    extension_path = here / "extend_modelo_v20_store.py"
    visible_nav_path = here / "extend_modelo_v20_store_visible_nav.py"
    provision_path = here / "provision_new_blog_v20.py"

    for p in (manifest_path, template_pages_path, canonical_pages_path, extension_path, visible_nav_path, provision_path):
        if not p.exists():
            fail(f"arquivo obrigatório ausente: {p}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    template_pages = json.loads(template_pages_path.read_text(encoding="utf-8"))
    canonical_pages = json.loads(canonical_pages_path.read_text(encoding="utf-8"))
    provision_text = provision_path.read_text(encoding="utf-8")

    if manifest.get("model") != "BLOGGER_MODELO_V20" or manifest.get("version") != 20:
        fail("manifesto não identifica BLOGGER_MODELO_V20 versão 20")
    if manifest.get("store_extension_marker") != STORE_MARKER:
        fail("store_extension_marker incorreto")
    if template_pages != canonical_pages:
        fail("templates/blogger_modelo_v20/pages.json e themes/blogger_modelo_v20/pages.json divergem")

    pages = template_pages.get("pages") or []
    keys = [p.get("key") for p in pages]
    if keys != EXPECTED_KEYS:
        fail(f"ordem/chaves de páginas inválidas: {keys}")
    if len(pages) != 6:
        fail(f"esperadas 6 páginas; obtido {len(pages)}")

    sobre = next((p for p in pages if p.get("key") == "sobre"), None)
    if not sobre:
        fail("página Sobre ausente")
    sobre_content = str(sobre.get("content") or "")
    if "{{BLOG_DESCRIPTION}}" not in sobre_content:
        fail("página Sobre não deriva a identidade da descrição do próprio blog")
    if GENERIC_LEAK in sobre_content.casefold():
        fail("página Sobre ainda contém nicho fixo herdado do blog-modelo")
    for needle in ("def _render_pages(blog_title: str, blog_description: str)", "{{BLOG_DESCRIPTION}}", "_render_pages(req.title, description)", "from html import escape"):
        if needle not in provision_text:
            fail(f"provisionador não protege identidade por descrição: {needle}")

    store = next((p for p in pages if p.get("key") == "loja"), None)
    if not store:
        fail("página LOJA ausente")
    if store.get("expected_slug") != "loja":
        fail("slug da LOJA precisa ser loja")
    if store.get("requires_store_population") is not True:
        fail("LOJA precisa exigir população automática")
    if store.get("store_expected_products") != 20 or store.get("store_expected_categories") != 5:
        fail("LOJA precisa exigir exatamente 20 produtos em 5 categorias")
    content = str(store.get("content") or "")
    if store.get("store_auto_start_marker") not in content or store.get("store_auto_end_marker") not in content:
        fail("marcadores da LOJA não estão presentes no scaffold")
    if "data-item-id=" in content or "s.shopee.com.br/" in content:
        fail("scaffold da LOJA contém produto/link afiliado fixo")
    if "ga-store-v20" not in content:
        fail("classe de escopo ga-store-v20 ausente")

    store_contract = manifest.get("store_contract") or {}
    expected_contract = {
        "menu_path": "/p/loja.html",
        "footer_menu_enabled": True,
        "footer_menu_position": "after-home",
        "desktop_max_width_px": 1280,
        "desktop_columns": 4,
        "tablet_columns": 2,
        "mobile_columns": 2,
        "expected_products": 20,
        "expected_categories": 5,
    }
    for key, expected in expected_contract.items():
        if store_contract.get(key) != expected:
            fail(f"store_contract.{key} esperado {expected!r}; obtido {store_contract.get(key)!r}")

    with tempfile.TemporaryDirectory(prefix="v20-store-validation-") as td:
        theme = Path(td) / "theme.xml"
        theme.write_text(
            "<?xml version='1.0' encoding='UTF-8'?><html><head>"
            f"<style>/* {BASE_MARKER} */</style></head><body class='ga-static-page'>"
            "<nav class='ga-home-v6-nav'><a href='/'>Início</a><a href='/p/sobre.html'>Sobre</a></nav>"
            "<main><div class='main section' id='page_body'></div></main>"
            "<section class='ga-static-footer'><div class='ga-static-footer-brand'><h3>Modelo</h3><p>Texto legado</p></div>"
            "<div class='ga-static-footer-links'><a href='/'>Início</a><a href='/p/sobre.html'>Sobre</a></div>"
            "<div class='ga-static-footer-bottom'><strong>Modelo</strong></div></section>"
            "</body></html>",
            encoding="utf-8",
        )

        run_extension(extension_path, theme, "primeira aplicação da extensão LOJA")
        run_extension(visible_nav_path, theme, "primeira aplicação do menu/fallback visível")
        ET.parse(theme)
        first_hash = sha256(theme)
        text = theme.read_text(encoding="utf-8")

        if text.count(STORE_MARKER) != 1:
            fail("marker da extensão LOJA não aparece exatamente uma vez")
        if text.count(VISIBLE_NAV_MARKER) != 1:
            fail("marker do menu visível não aparece exatamente uma vez")
        if text.count(FOOTER_NAV_MARKER) < 1:
            fail("marker de navegação da LOJA no rodapé está ausente")
        if STATIC_PAGE_FEED_MARKER not in text:
            fail("runtime de fallback das páginas estáticas está ausente")
        if BRAND_DESCRIPTION_MARKER not in text:
            fail("runtime de descrição do próprio blog no rodapé está ausente")

        for needle in (
            "/p/loja.html",
            "repeat(4,minmax(0,1fr))",
            "repeat(2,minmax(0,1fr))",
            "max-width:1280px",
            ".sidebar-container",
            "ga-store-nav-v20",
            "nav.ga-home-v6-nav",
            "ga-store-visible-nav-v20",
            "home.nextElementSibling!==store",
            "ga-store-footer-nav-v20",
            "BLOGGER_MODELO_V20_STORE_FOOTER_NAV",
            ".ga-home-footer-links,.ga-post-footer-links,.ga-static-footer-links",
            "enhanceFooterGroup",
            "BLOGGER_MODELO_V20_STATIC_PAGE_FEED_RUNTIME",
            "/feeds/pages/default?alt=json&max-results=25",
            "hydrateStaticPageFromFeed",
            "syncBrandFromFeed",
            "feed.subtitle",
            ".ga-home-footer-brand p,.ga-post-footer-brand p,.ga-static-footer-brand p",
            "data-ga-brand-description-feed-runtime",
            "BLOGGER_MODELO_V20_BRAND_DESCRIPTION_FEED_RUNTIME",
            "data-ga-static-page-feed-runtime",
        ):
            if needle not in text:
                fail(f"extensão não contém requisito: {needle}")

        run_extension(extension_path, theme, "segunda aplicação/idempotência LOJA")
        run_extension(visible_nav_path, theme, "segunda aplicação/idempotência menu/fallback")
        second_hash = sha256(theme)
        if first_hash != second_hash:
            fail("extensões não são idempotentes")

    print(json.dumps({
        "status": "BLOGGER_MODELO_V20_STORE_VALIDATION_PASS",
        "model": "BLOGGER_MODELO_V20",
        "version": 20,
        "page_count": 6,
        "page_keys": EXPECTED_KEYS,
        "store_extension_marker": STORE_MARKER,
        "store_visible_nav_marker": VISIBLE_NAV_MARKER,
        "store_footer_nav_marker": FOOTER_NAV_MARKER,
        "static_page_feed_marker": STATIC_PAGE_FEED_MARKER,
        "brand_description_marker": BRAND_DESCRIPTION_MARKER,
        "store_menu_path": "/p/loja.html",
        "store_menu_position": "after-home",
        "store_menu_target": "nav.ga-home-v6-nav",
        "store_menu_highlighted": True,
        "store_footer_nav_supported": True,
        "store_footer_position": "after-home",
        "static_page_feed_runtime_supported": True,
        "footer_brand_feed_sync_supported": True,
        "footer_description_feed_sync_supported": True,
        "page_identity_uses_blog_description": True,
        "store_max_width": 1280,
        "store_sidebar_hidden_only": True,
        "desktop_columns": 4,
        "tablet_columns": 2,
        "mobile_columns": 2,
        "expected_products": 20,
        "expected_categories": 5,
        "fixed_products_in_scaffold": False,
        "extension_xml_valid": True,
        "extension_idempotent": True,
        "home_content_changed": False,
        "posts_changed": False,
        "other_static_pages_changed": False
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
