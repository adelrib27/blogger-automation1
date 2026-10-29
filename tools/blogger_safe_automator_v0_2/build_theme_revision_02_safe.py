#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

OLD_URL = "https://airfryer-gourmet-forma-de-vidro.blogspot.com/"
NEW_URL = "https://guia-de-achados-e-ofertas.blogspot.com/"
MARKER = "emporio-revisao-visual-02-safe2"

STATIC_NAV = f"""
<div aria-label='Navegação principal' class='ga-static-nav' data-theme-build='{MARKER}'>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/'>Início</a>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/p/sobre.html'>Sobre</a>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/p/aviso-de-afiliados.html'>Afiliados</a>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/p/contato.html'>Contato</a>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/p/politica-de-privacidade.html'>Privacidade</a>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/p/termos-de-uso.html'>Termos</a>
</div>
"""

EXTRA_CSS = r'''
/* Revisão Visual 02 SAFE2 — sem alterar estado interno de widgets */
.top-nav #page_list_top{display:none!important}
.ga-static-nav{
  border-top:1px solid #e1e7ed;
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  margin:18px 28px 0;
  padding:12px 0 2px;
}
.ga-static-nav a{
  border-radius:999px;
  color:#43564a!important;
  font-size:14px;
  font-weight:700;
  padding:9px 13px;
  text-decoration:none!important;
}
.ga-static-nav a:hover{background:#eef4ef;color:#1f5132!important}
.item-view .post-body{font-size:17px!important;line-height:1.78!important}
.item-view .post-body h2{
  color:#171717!important;
  font-size:1.45em!important;
  font-weight:800!important;
  letter-spacing:-.02em;
  margin-top:2em!important;
}
.item-view .post-body > p:first-child img{
  background:#fff;
  border:1px solid #dce5ee;
  border-radius:18px;
  box-sizing:border-box;
  display:block;
  margin:0 auto 24px;
  max-height:560px;
  object-fit:contain;
  padding:10px;
  width:auto;
}
.item-view .post-body a[rel~="sponsored"]{
  background:#0b5eb8!important;
  border:1px solid #0b5eb8!important;
  border-radius:12px;
  box-shadow:0 8px 20px rgba(11,94,184,.16);
  color:#fff!important;
  display:inline-block;
  font-weight:800!important;
  line-height:1.25;
  margin:6px 0;
  padding:13px 18px;
  text-decoration:none!important;
}
.item-view .post-body a[rel~="sponsored"]:hover{background:#074985!important}
.item-view .post-body p > small{
  background:#f5f7f9;
  border:1px solid #e1e7ed;
  border-radius:12px;
  box-sizing:border-box;
  color:#65717d!important;
  display:block;
  font-size:12.5px!important;
  line-height:1.55;
  margin-top:26px;
  padding:14px 16px;
}
@media screen and (max-width:800px){
  .ga-static-nav{margin:12px 16px 0;overflow-x:auto;flex-wrap:nowrap;padding-bottom:8px}
  .ga-static-nav a{white-space:nowrap}
}
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description="Gera revisão 02 SAFE2 a partir da V1 aceita pelo Blogger.")
    p.add_argument("--base-theme", required=True)
    p.add_argument("--output-theme", required=True)
    args = p.parse_args()

    src = Path(args.base_theme).resolve()
    out = Path(args.output_theme).resolve()
    if not src.exists():
        raise SystemExit("Tema-base não encontrado.")

    text = src.read_text(encoding="utf-8")
    if "emporio-revisao-visual-01" not in text:
        raise SystemExit("O backup informado não contém a revisão visual 01 esperada.")

    text = text.replace(OLD_URL, NEW_URL)
    text = re.sub(
        r"(<b:widget id='Header1'[^>]*?title=')[^']*(' type='Header')",
        r"\1Guia de Achados &amp; Ofertas (Cabeçalho)\2",
        text,
        count=1,
    )

    # Não altera PageList1 nem ContactForm1. Insere navegação HTML simples
    # dentro do <nav class='top-nav' role='navigation'> já existente no Emporio.
    nav_pattern = r"(<nav\b[^>]*\brole='navigation'[^>]*>)(.*?)(</nav>)"
    text, n = re.subn(
        nav_pattern,
        lambda m: m.group(1) + m.group(2) + STATIC_NAV + m.group(3),
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("Navegação Emporio não localizada para inserção segura do menu.")

    mobile_marker = "/* Mobile */"
    if mobile_marker not in text:
        raise SystemExit("Marcador CSS Mobile não encontrado.")
    text = text.replace(mobile_marker, EXTRA_CSS + "\n" + mobile_marker, 1)

    # Marcador também no head para validação pública redundante.
    if "<head>" not in text:
        raise SystemExit("Elemento <head> não encontrado.")
    text = text.replace(
        "<head>",
        "<head>\n    <meta content='" + MARKER + "' name='x-theme-build-v2'/>",
        1,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    ET.parse(out)

    print(json.dumps({
        "status": "THEME_REVISION_02_SAFE2_BUILT",
        "base_theme": str(src),
        "path": str(out),
        "size_bytes": out.stat().st_size,
        "sha256": sha256(out),
        "xml_valid": True,
        "public_marker": MARKER,
        "widget_state_modified": False,
        "static_navigation": True,
        "nav_anchor": "top-nav",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
