#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-07-featured-fix"
MARKER_NEW = "emporio-revisao-visual-08-three-columns"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V8 THREE COLUMNS
   Escopo EXCLUSIVO: grade de posts da HOME abaixo do destaque.
   Preserva cabeçalho, FeaturedPost e todas as páginas internas.
   ============================================================ */

/* A home usa toda a largura editorial; o Arquivo desce para baixo. */
body:not(.item-view) .centered-bottom{
  display:block!important;
  margin-left:auto!important;
  margin-right:auto!important;
  max-width:1040px!important;
  padding:0!important;
  width:calc(100% - 36px)!important;
}

body:not(.item-view) .centered-bottom .main-container,
body:not(.item-view) .centered-bottom .main,
body:not(.item-view) #page_body,
body:not(.item-view) #Blog1{
  float:none!important;
  margin:0!important;
  max-width:none!important;
  width:100%!important;
}

/* Três cards lado a lado no desktop. */
body:not(.item-view) #Blog1 .blog-posts{
  align-items:stretch!important;
  display:grid!important;
  gap:18px!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  margin:0!important;
  width:100%!important;
}

body:not(.item-view) #Blog1 .post-outer-container{
  box-sizing:border-box!important;
  height:100%!important;
  margin:0!important;
  min-width:0!important;
  width:100%!important;
}

body:not(.item-view) #Blog1 .post-outer,
body:not(.item-view) #Blog1 .post-wrapper{
  box-sizing:border-box!important;
  height:100%!important;
  margin:0!important;
  width:100%!important;
}

/* Miniaturas padronizadas: mesma proporção visual, sem distorcer. */
body:not(.item-view) #Blog1 .post-wrapper .snippet-thumbnail-container,
body:not(.item-view) #Blog1 .post-wrapper .snippet-thumbnail{
  background-color:#eef3f8!important;
  height:190px!important;
  min-height:190px!important;
  max-height:190px!important;
  overflow:hidden!important;
  width:100%!important;
}

body:not(.item-view) #Blog1 .post-wrapper .snippet-thumbnail{
  background-position:center center!important;
  background-repeat:no-repeat!important;
  background-size:cover!important;
}

/* Conteúdo dos cards com alturas mais coerentes. */
body:not(.item-view) #Blog1 .post-wrapper .post{
  box-sizing:border-box!important;
  padding:18px 16px!important;
}

body:not(.item-view) #Blog1 .post-wrapper .post-title-container{
  min-height:52px!important;
}

body:not(.item-view) #Blog1 .post-wrapper .post-title a{
  font-size:15px!important;
  line-height:1.42!important;
}

body:not(.item-view) #Blog1 .post-wrapper .header-buttons-byline{
  margin-top:12px!important;
}

/* Pager ocupa toda a largura da grade. */
body:not(.item-view) #Blog1 #blog-pager{
  grid-column:1/-1!important;
  width:100%!important;
}

/* Arquivo permanece disponível, mas não rouba uma coluna dos cards. */
body:not(.item-view) .sidebar-container{
  float:none!important;
  margin:28px 0 0!important;
  max-width:300px!important;
  overflow:visible!important;
  width:300px!important;
}

body:not(.item-view) .sidebar-container .widget{
  margin-bottom:0!important;
}

@media screen and (max-width:1050px){
  body:not(.item-view) #Blog1 .blog-posts{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
}

@media screen and (max-width:700px){
  body:not(.item-view) .centered-bottom{
    width:100%!important;
  }

  body:not(.item-view) #Blog1 .blog-posts{
    gap:16px!important;
    grid-template-columns:1fr!important;
  }

  body:not(.item-view) #Blog1 .post-wrapper .snippet-thumbnail-container,
  body:not(.item-view) #Blog1 .post-wrapper .snippet-thumbnail{
    height:220px!important;
    min-height:220px!important;
    max-height:220px!important;
  }

  body:not(.item-view) .sidebar-container{
    box-sizing:border-box!important;
    margin:24px 14px 0!important;
    max-width:none!important;
    width:calc(100% - 28px)!important;
  }
}
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description="Gera V8: três cards horizontais na home com miniaturas padronizadas.")
    p.add_argument("--theme-path", required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != "theme.xml":
        raise SystemExit("theme.xml não encontrado no caminho informado.")

    text = path.read_text(encoding="utf-8")

    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            "status": "THEME_REVISION_08_ALREADY_BUILT",
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "xml_valid": True,
            "public_marker": MARKER_NEW,
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f"A V7 validada não foi localizada. Marcador ausente: {MARKER_OLD}")

    text = text.replace(MARKER_OLD, MARKER_NEW)

    mobile_marker = "/* Mobile */"
    if mobile_marker not in text:
        raise SystemExit("Marcador CSS Mobile não encontrado.")

    text = text.replace(mobile_marker, CSS + "\n" + mobile_marker, 1)
    path.write_text(text, encoding="utf-8")
    ET.parse(path)

    print(json.dumps({
        "status": "THEME_REVISION_08_THREE_COLUMNS_BUILT",
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "xml_valid": True,
        "public_marker": MARKER_NEW,
        "scope": "home-blog-grid-only",
        "desktop_columns": 3,
        "tablet_columns": 2,
        "mobile_columns": 1,
        "card_thumbnail_height_px": 190,
        "thumbnail_fit": "background-size: cover",
        "featured_post_changed": False,
        "item_view_changed": False,
        "header_changed": False,
        "widget_state_modified": False,
        "native_theme": "Emporio preserved",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
