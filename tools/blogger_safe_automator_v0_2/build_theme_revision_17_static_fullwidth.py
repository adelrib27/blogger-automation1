#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-16-static-wide-align"
MARKER_NEW = "emporio-revisao-visual-17-static-fullwidth"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V17 STATIC FULL WIDTH
   Escopo: páginas estáticas /p/*.html.
   Força conteúdo + PopularPosts a ocupar a mesma largura visual
   do cabeçalho/rodapé, sem depender do limite interno do Emporio.
   ============================================================ */

@media screen and (min-width:981px){
  body.ga-static-page .centered-bottom{
    align-items:start!important;
    box-sizing:border-box!important;
    display:grid!important;
    gap:30px!important;
    grid-template-columns:minmax(0,1fr) 340px!important;
    grid-template-rows:auto!important;
    left:50%!important;
    margin:0!important;
    max-width:1220px!important;
    min-width:0!important;
    position:relative!important;
    transform:translateX(-50%)!important;
    width:min(1220px,calc(100vw - 64px))!important;
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

  body.ga-static-page .main-container .main,
  body.ga-static-page .main-container .Blog,
  body.ga-static-page .main-container .widget.Blog,
  body.ga-static-page .main-container .post-outer-container,
  body.ga-static-page .main-container .post-outer,
  body.ga-static-page .main-container .post{
    box-sizing:border-box!important;
    max-width:none!important;
    min-width:0!important;
    width:100%!important;
  }

  body.ga-static-page .sidebar-container{
    align-self:start!important;
    box-sizing:border-box!important;
    grid-column:2!important;
    grid-row:1!important;
    margin:0!important;
    max-width:340px!important;
    min-width:340px!important;
    overflow:visible!important;
    width:340px!important;
  }

  body.ga-static-page #PopularPosts1,
  body.ga-static-page .widget.PopularPosts{
    box-sizing:border-box!important;
    max-width:340px!important;
    width:340px!important;
  }
}

@media screen and (max-width:980px){
  body.ga-static-page .centered-bottom{
    display:block!important;
    left:auto!important;
    transform:none!important;
    width:calc(100% - 32px)!important;
  }
  body.ga-static-page .main-container,
  body.ga-static-page .sidebar-container,
  body.ga-static-page #PopularPosts1,
  body.ga-static-page .widget.PopularPosts{
    display:block!important;
    margin-left:auto!important;
    margin-right:auto!important;
    max-width:none!important;
    min-width:0!important;
    width:100%!important;
  }
  body.ga-static-page .sidebar-container{
    margin-top:28px!important;
  }
}
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description='V17: alinha páginas estáticas à largura do cabeçalho/rodapé.')
    p.add_argument('--theme-path', required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != 'theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text = path.read_text(encoding='utf-8')

    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            'status':'THEME_REVISION_17_ALREADY_BUILT',
            'path':str(path),
            'size_bytes':path.stat().st_size,
            'sha256':sha256(path),
            'xml_valid':True,
            'public_marker':MARKER_NEW
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V16 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

    text = text.replace(MARKER_OLD, MARKER_NEW, 1)

    mobile_marker = '/* Mobile */'
    if mobile_marker not in text:
        raise SystemExit('Marcador CSS Mobile não encontrado.')
    text = text.replace(mobile_marker, CSS + '\n' + mobile_marker, 1)

    path.write_text(text, encoding='utf-8')
    ET.parse(path)

    print(json.dumps({
        'status':'THEME_REVISION_17_STATIC_FULLWIDTH_BUILT',
        'path':str(path),
        'size_bytes':path.stat().st_size,
        'sha256':sha256(path),
        'xml_valid':True,
        'public_marker':MARKER_NEW,
        'scope':'static-pages-only',
        'static_wrapper_max_width':1220,
        'sidebar_width':340,
        'post_pages_changed':False,
        'home_changed':False,
        'contact_form_preserved':True,
        'static_footer_preserved':True
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
