#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-15-static-sidebar-top"
MARKER_NEW = "emporio-revisao-visual-16-static-wide-align"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V16 STATIC WIDE ALIGN
   Escopo: páginas estáticas /p/*.html.
   Alinha conteúdo + sidebar à largura visual do cabeçalho/rodapé.
   ============================================================ */

@media screen and (min-width:981px){
  /* O Emporio limita a largura pelo wrapper .centered; ampliamos o wrapper
     para a mesma medida editorial usada no rodapé. */
  body.ga-static-page .page_body > .centered,
  body.ga-static-page .page-body > .centered,
  body.ga-static-page .page_body .centered,
  body.ga-static-page .page-body .centered{
    box-sizing:border-box!important;
    margin-left:auto!important;
    margin-right:auto!important;
    max-width:1220px!important;
    width:calc(100% - 48px)!important;
  }

  body.ga-static-page .centered-bottom{
    align-items:start!important;
    box-sizing:border-box!important;
    display:grid!important;
    gap:28px!important;
    grid-template-columns:minmax(0,1fr) 320px!important;
    grid-template-rows:auto!important;
    margin:0!important;
    max-width:none!important;
    width:100%!important;
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

  /* Evita limites internos herdados do Emporio reduzirem o cartão da página. */
  body.ga-static-page .main-container .main,
  body.ga-static-page .main-container .Blog,
  body.ga-static-page .main-container .widget.Blog,
  body.ga-static-page .main-container .post-outer-container,
  body.ga-static-page .main-container .post-outer{
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
    max-width:320px!important;
    min-width:0!important;
    width:320px!important;
  }

  body.ga-static-page #PopularPosts1,
  body.ga-static-page .widget.PopularPosts{
    max-width:100%!important;
    width:100%!important;
  }
}

@media screen and (max-width:980px){
  body.ga-static-page .page_body > .centered,
  body.ga-static-page .page-body > .centered,
  body.ga-static-page .page_body .centered,
  body.ga-static-page .page-body .centered{
    width:calc(100% - 32px)!important;
  }
}

@media screen and (max-width:700px){
  body.ga-static-page .page_body > .centered,
  body.ga-static-page .page-body > .centered,
  body.ga-static-page .page_body .centered,
  body.ga-static-page .page-body .centered{
    width:100%!important;
  }
}
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description='V16: alinha a largura das páginas estáticas ao cabeçalho/rodapé.')
    p.add_argument('--theme-path', required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != 'theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text = path.read_text(encoding='utf-8')

    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            'status':'THEME_REVISION_16_ALREADY_BUILT',
            'path':str(path),
            'size_bytes':path.stat().st_size,
            'sha256':sha256(path),
            'xml_valid':True,
            'public_marker':MARKER_NEW
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V15 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

    text = text.replace(MARKER_OLD, MARKER_NEW, 1)

    mobile_marker = '/* Mobile */'
    if mobile_marker not in text:
        raise SystemExit('Marcador CSS Mobile não encontrado.')
    text = text.replace(mobile_marker, CSS + '\n' + mobile_marker, 1)

    path.write_text(text, encoding='utf-8')
    ET.parse(path)

    print(json.dumps({
        'status':'THEME_REVISION_16_STATIC_WIDE_ALIGN_BUILT',
        'path':str(path),
        'size_bytes':path.stat().st_size,
        'sha256':sha256(path),
        'xml_valid':True,
        'public_marker':MARKER_NEW,
        'scope':'static-pages-only',
        'static_wrapper_max_width_px':1220,
        'sidebar_width_px':320,
        'column_gap_px':28,
        'header_changed':False,
        'home_changed':False,
        'post_pages_changed':False,
        'contact_form_preserved':True,
        'static_footer_preserved':True
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
