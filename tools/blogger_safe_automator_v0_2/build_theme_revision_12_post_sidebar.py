#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-11-post-finish"
MARKER_NEW = "emporio-revisao-visual-12-post-sidebar"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V12 POST SIDEBAR
   Escopo: páginas de POST.
   Corrige apenas a posição de "Postagens mais visitadas".
   Mantém artigo, botões Shopee, rodapé e remoção de comentários.
   ============================================================ */

/* Em desktop, força a estrutura artigo + sidebar lado a lado. */
body.ga-post-page .centered-bottom{
  align-items:start!important;
  box-sizing:border-box!important;
  display:grid!important;
  gap:28px!important;
  grid-template-columns:minmax(0,1fr) 300px!important;
  margin-left:auto!important;
  margin-right:auto!important;
  max-width:1220px!important;
  width:calc(100% - 48px)!important;
}

body.ga-post-page .main-container{
  box-sizing:border-box!important;
  grid-column:1!important;
  margin:0!important;
  max-width:none!important;
  min-width:0!important;
  width:100%!important;
}

body.ga-post-page .sidebar-container{
  align-self:start!important;
  box-sizing:border-box!important;
  display:block!important;
  float:none!important;
  grid-column:2!important;
  margin:0!important;
  max-width:300px!important;
  min-width:0!important;
  overflow:visible!important;
  position:relative!important;
  width:300px!important;
}

body.ga-post-page #PopularPosts1,
body.ga-post-page .widget.PopularPosts{
  margin:0!important;
  max-width:100%!important;
  width:100%!important;
}

/* Corrige a coluna de links do rodapé V11, sem alterar seu desenho. */
body.ga-post-page .ga-post-footer .ga-home-footer-links{
  display:flex!important;
  flex-direction:column!important;
  gap:9px!important;
}

@media screen and (max-width:980px){
  body.ga-post-page .centered-bottom{
    display:block!important;
    width:calc(100% - 32px)!important;
  }
  body.ga-post-page .main-container,
  body.ga-post-page .sidebar-container{
    display:block!important;
    margin-left:auto!important;
    margin-right:auto!important;
    max-width:none!important;
    width:100%!important;
  }
  body.ga-post-page .sidebar-container{
    margin-top:28px!important;
  }
}

@media screen and (max-width:700px){
  body.ga-post-page .centered-bottom{
    width:100%!important;
  }
}
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description='V12: mantém Postagens mais visitadas ao lado do artigo em desktop.')
    p.add_argument('--theme-path', required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != 'theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text = path.read_text(encoding='utf-8')

    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            'status':'THEME_REVISION_12_ALREADY_BUILT',
            'path':str(path),
            'size_bytes':path.stat().st_size,
            'sha256':sha256(path),
            'xml_valid':True,
            'public_marker':MARKER_NEW
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V11 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

    text = text.replace(MARKER_OLD, MARKER_NEW, 1)

    mobile_marker = '/* Mobile */'
    if mobile_marker not in text:
        raise SystemExit('Marcador CSS Mobile não encontrado.')
    text = text.replace(mobile_marker, CSS + '\n' + mobile_marker, 1)

    path.write_text(text, encoding='utf-8')
    ET.parse(path)

    print(json.dumps({
        'status':'THEME_REVISION_12_POST_SIDEBAR_BUILT',
        'path':str(path),
        'size_bytes':path.stat().st_size,
        'sha256':sha256(path),
        'xml_valid':True,
        'public_marker':MARKER_NEW,
        'scope':'post-pages-only',
        'article_body_changed':False,
        'shopee_buttons_changed':False,
        'popular_posts_sidebar_position':'right-of-article-desktop',
        'comments_login_removed_preserved':True,
        'post_footer_preserved':True,
        'home_changed':False,
        'contact_page_changed':False
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
