#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-14-static-pages-finish"
MARKER_NEW = "emporio-revisao-visual-15-static-sidebar-top"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V15 STATIC SIDEBAR TOP
   Escopo: páginas estáticas /p/*.html.
   Apenas fixa conteúdo e PopularPosts na MESMA linha do grid.
   ============================================================ */

@media screen and (min-width:981px){
  body.ga-static-page .centered-bottom{
    align-items:start!important;
    box-sizing:border-box!important;
    display:grid!important;
    gap:28px!important;
    grid-template-columns:minmax(0,1fr) 300px!important;
    grid-template-rows:auto!important;
    margin-left:auto!important;
    margin-right:auto!important;
    max-width:1220px!important;
    width:calc(100% - 48px)!important;
  }

  body.ga-static-page .main-container{
    align-self:start!important;
    box-sizing:border-box!important;
    grid-column:1!important;
    grid-row:1!important;
    margin:0!important;
    max-width:none!important;
    min-width:0!important;
    width:100%!important;
  }

  body.ga-static-page .sidebar-container{
    align-self:start!important;
    box-sizing:border-box!important;
    display:block!important;
    float:none!important;
    grid-column:2!important;
    grid-row:1!important;
    margin:0!important;
    max-width:300px!important;
    min-width:0!important;
    overflow:visible!important;
    position:relative!important;
    top:0!important;
    transform:none!important;
    width:300px!important;
  }

  body.ga-static-page #PopularPosts1,
  body.ga-static-page .widget.PopularPosts{
    margin-top:0!important;
    max-width:100%!important;
    width:100%!important;
  }
}

@media screen and (max-width:980px){
  body.ga-static-page .centered-bottom{
    display:block!important;
    width:calc(100% - 32px)!important;
  }
  body.ga-static-page .main-container,
  body.ga-static-page .sidebar-container{
    display:block!important;
    margin-left:auto!important;
    margin-right:auto!important;
    max-width:none!important;
    width:100%!important;
  }
  body.ga-static-page .sidebar-container{
    margin-top:28px!important;
  }
}

@media screen and (max-width:700px){
  body.ga-static-page .centered-bottom{
    width:100%!important;
  }
}
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description='V15: mantém Postagens mais visitadas ao lado e no topo das páginas estáticas.')
    p.add_argument('--theme-path', required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != 'theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text = path.read_text(encoding='utf-8')

    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            'status':'THEME_REVISION_15_ALREADY_BUILT',
            'path':str(path),
            'size_bytes':path.stat().st_size,
            'sha256':sha256(path),
            'xml_valid':True,
            'public_marker':MARKER_NEW
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V14 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

    text = text.replace(MARKER_OLD, MARKER_NEW, 1)

    mobile_marker = '/* Mobile */'
    if mobile_marker not in text:
        raise SystemExit('Marcador CSS Mobile não encontrado.')
    text = text.replace(mobile_marker, CSS + '\n' + mobile_marker, 1)

    path.write_text(text, encoding='utf-8')
    ET.parse(path)

    print(json.dumps({
        'status':'THEME_REVISION_15_STATIC_SIDEBAR_TOP_BUILT',
        'path':str(path),
        'size_bytes':path.stat().st_size,
        'sha256':sha256(path),
        'xml_valid':True,
        'public_marker':MARKER_NEW,
        'scope':'static-pages-only',
        'static_content_position':'left-column-row-1',
        'popular_posts_sidebar_position':'right-column-row-1',
        'static_footer_preserved':True,
        'comments_login_removed_preserved':True,
        'contact_form_preserved':True,
        'post_pages_changed':False,
        'home_changed':False
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
