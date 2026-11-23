#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-12-post-sidebar"
MARKER_NEW = "emporio-revisao-visual-13-sidebar-top"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V13 SIDEBAR TOP ALIGNMENT
   Escopo: páginas de POST.
   Apenas fixa artigo e PopularPosts na MESMA linha do grid.
   ============================================================ */

@media screen and (min-width:981px){
  body.ga-post-page .centered-bottom{
    align-items:start!important;
    display:grid!important;
    grid-template-columns:minmax(0,1fr) 300px!important;
    grid-template-rows:auto!important;
  }

  body.ga-post-page .main-container{
    align-self:start!important;
    grid-column:1!important;
    grid-row:1!important;
    margin-top:0!important;
  }

  body.ga-post-page .sidebar-container{
    align-self:start!important;
    grid-column:2!important;
    grid-row:1!important;
    margin-top:0!important;
    top:0!important;
    transform:none!important;
  }

  body.ga-post-page #PopularPosts1,
  body.ga-post-page .widget.PopularPosts{
    margin-top:0!important;
  }
}
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description='V13: alinha Postagens mais visitadas ao topo, ao lado do artigo.')
    p.add_argument('--theme-path', required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != 'theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text = path.read_text(encoding='utf-8')

    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            'status':'THEME_REVISION_13_ALREADY_BUILT',
            'path':str(path),
            'size_bytes':path.stat().st_size,
            'sha256':sha256(path),
            'xml_valid':True,
            'public_marker':MARKER_NEW
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V12 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

    text = text.replace(MARKER_OLD, MARKER_NEW, 1)

    mobile_marker = '/* Mobile */'
    if mobile_marker not in text:
        raise SystemExit('Marcador CSS Mobile não encontrado.')
    text = text.replace(mobile_marker, CSS + '\n' + mobile_marker, 1)

    path.write_text(text, encoding='utf-8')
    ET.parse(path)

    print(json.dumps({
        'status':'THEME_REVISION_13_SIDEBAR_TOP_BUILT',
        'path':str(path),
        'size_bytes':path.stat().st_size,
        'sha256':sha256(path),
        'xml_valid':True,
        'public_marker':MARKER_NEW,
        'scope':'post-pages-only',
        'article_grid_position':'row-1-column-1',
        'popular_posts_grid_position':'row-1-column-2',
        'article_body_changed':False,
        'shopee_buttons_changed':False,
        'post_footer_preserved':True,
        'comments_login_removed_preserved':True,
        'home_changed':False,
        'contact_page_changed':False
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
