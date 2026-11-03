#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-01"
MARKER_NEW = "emporio-revisao-visual-02"
OLD_URL = "https://airfryer-gourmet-forma-de-vidro.blogspot.com/"
NEW_URL = "https://guia-de-achados-e-ofertas.blogspot.com/"

NAV = {
    "home": {"href": NEW_URL, "position": 0, "title": "Início"},
    "sobre": {"href": NEW_URL + "p/sobre.html", "position": 1, "title": "Sobre"},
    "afiliados": {"href": NEW_URL + "p/aviso-de-afiliados.html", "position": 2, "title": "Afiliados"},
    "contato": {"href": NEW_URL + "p/contato.html", "position": 3, "title": "Contato"},
    "privacidade": {"href": NEW_URL + "p/politica-de-privacidade.html", "position": 4, "title": "Privacidade"},
    "termos": {"href": NEW_URL + "p/termos-de-uso.html", "position": 5, "title": "Termos"},
}

EXTRA_CSS = r'''
/* Revisão Visual 02 — navegação, conteúdo e conversão */
.top-nav .PageList .overflowable-contents .container,
.top-nav .PageList ul{
  align-items:center;
}
.top-nav .PageList ul{
  gap:4px;
}
.top-nav .PageList ul li a{
  padding-left:14px!important;
  padding-right:14px!important;
  white-space:nowrap;
}

/* Leitura mais confortável em posts e páginas */
.item-view .post-body{
  font-size:17px!important;
  line-height:1.78!important;
}
.item-view .post-body h2{
  color:#171717!important;
  font-size:1.45em!important;
  font-weight:800!important;
  letter-spacing:-.02em;
  margin-top:2em!important;
}
.item-view .post-body ul,
.item-view .post-body ol{
  padding-left:1.35em!important;
}
.item-view .post-body li{
  margin:.5em 0;
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

/* CTAs de afiliado: funciona com qualquer plataforma usando rel=sponsored */
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
  transition:transform .16s ease,box-shadow .16s ease,background .16s ease;
}
.item-view .post-body a[rel~="sponsored"]:hover{
  background:#074985!important;
  box-shadow:0 12px 26px rgba(11,94,184,.22);
  transform:translateY(-1px);
}
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

/* Formulário de contato visível e integrado ao sidebar */
.sidebar-container .widget.ContactForm{
  display:block!important;
}
.widget.ContactForm .contact-form-button-submit{
  background:#0b5eb8!important;
  width:100%;
}
.widget.ContactForm .contact-form-button-submit:hover{
  background:#074985!important;
}

/* Páginas institucionais ficam com o mesmo acabamento editorial */
.item-view .post-body a:not([rel~="sponsored"]){
  text-decoration-thickness:1px;
  text-underline-offset:2px;
}
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description="Gera a Revisão Visual 02 do tema Emporio já validado.")
    p.add_argument("--theme-path", required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != "theme.xml":
        raise SystemExit("theme.xml não encontrado no caminho informado.")

    text = path.read_text(encoding="utf-8")

    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            "status": "THEME_REVISION_02_ALREADY_BUILT",
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "xml_valid": True,
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f"Marcador base esperado não encontrado: {MARKER_OLD}")

    text = text.replace(MARKER_OLD, MARKER_NEW, 1)
    text = text.replace(OLD_URL, NEW_URL)

    text = re.sub(
        r"(<b:widget id='Header1'[^>]*?title=')[^']*(' type='Header')",
        r"\1Guia de Achados &amp; Ofertas (Cabeçalho)\2",
        text,
        count=1,
    )

    nav_json = json.dumps(NAV, ensure_ascii=False, separators=(",", ":"))
    page_setting = (
        "<b:widget-setting name='pageListJson'><![CDATA["
        + nav_json
        + "]]></b:widget-setting>"
    )
    text, n = re.subn(
        r"<b:widget-setting name='pageListJson'><!\[CDATA\[.*?\]\]></b:widget-setting>",
        lambda _: page_setting,
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("pageListJson não foi localizado de forma única.")

    text, n = re.subn(
        r"<b:widget id='ContactForm1' locked='false' title='[^']*' type='ContactForm' visible='(?:true|false)'>",
        "<b:widget id='ContactForm1' locked='false' title='Fale conosco' type='ContactForm' visible='true'>",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("ContactForm1 não foi localizado de forma única.")

    if "Revisão Visual 02 — navegação, conteúdo e conversão" not in text:
        mobile_marker = "/* Mobile */"
        if mobile_marker not in text:
            raise SystemExit("Marcador CSS Mobile não encontrado.")
        text = text.replace(mobile_marker, EXTRA_CSS + "\n" + mobile_marker, 1)

    path.write_text(text, encoding="utf-8")
    ET.parse(path)

    print(json.dumps({
        "status": "THEME_REVISION_02_BUILT",
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "xml_valid": True,
        "public_marker": MARKER_NEW,
        "navigation_items": list(NAV.values()),
        "contact_form_visible": True,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
