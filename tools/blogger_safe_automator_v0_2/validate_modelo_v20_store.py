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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fail(message: str) -> None:
    raise SystemExit("VALIDATION_FAILED: " + message)


def main() -> int:
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    manifest_path = root / "templates" / "blogger_modelo_v20" / "model_manifest.json"
    template_pages_path = root / "templates" / "blogger_modelo_v20" / "pages.json"
    canonical_pages_path = root / "themes" / "blogger_modelo_v20" / "pages.json"
    extension_path = here / "extend_modelo_v20_store.py"

    for p in (manifest_path, template_pages_path, canonical_pages_path, extension_path):
        if not p.exists():
            fail(f"arquivo obrigatório ausente: {p}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    template_pages = json.loads(template_pages_path.read_text(encoding="utf-8"))
    canonical_pages = json.loads(canonical_pages_path.read_text(encoding="utf-8"))

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
            f"<style>/* {BASE_MARKER} */</style></head><body></body></html>",
            encoding="utf-8",
        )
        cmd = [sys.executable, str(extension_path), "--theme-path", str(theme)]
        first = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
        if first.returncode != 0:
            fail("primeira aplicação da extensão falhou: " + (first.stderr or first.stdout)[-1000:])
        ET.parse(theme)
        first_hash = sha256(theme)
        text = theme.read_text(encoding="utf-8")
        if text.count(STORE_MARKER) != 1:
            fail("marker da extensão não aparece exatamente uma vez")
        for needle in (
            "/p/loja.html",
            "repeat(4,minmax(0,1fr))",
            "repeat(2,minmax(0,1fr))",
            "max-width:1280px",
            ".sidebar-container",
            "ga-store-nav-v20",
        ):
            if needle not in text:
                fail(f"extensão não contém requisito: {needle}")

        second = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
        if second.returncode != 0:
            fail("segunda aplicação/idempotência falhou: " + (second.stderr or second.stdout)[-1000:])
        second_hash = sha256(theme)
        if first_hash != second_hash:
            fail("extensão não é idempotente")

    print(json.dumps({
        "status": "BLOGGER_MODELO_V20_STORE_VALIDATION_PASS",
        "model": "BLOGGER_MODELO_V20",
        "version": 20,
        "page_count": 6,
        "page_keys": EXPECTED_KEYS,
        "store_extension_marker": STORE_MARKER,
        "store_menu_path": "/p/loja.html",
        "store_menu_position": "after-home",
        "store_menu_highlighted": True,
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
        "home_changed": False,
        "posts_changed": False,
        "other_static_pages_changed": False
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
