#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-03-portal"
MARKER_NEW = "emporio-revisao-visual-04-home-itemnav"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V4 HOME + ITEM NAV
   Mantém o artigo da V3 e corrige a composição do cabeçalho/home.
   ============================================================ */

/* O menu é movido por JS para imediatamente antes da busca. */
.ga-header-row{
  align-items:center!important;
  display:flex!important;
  gap:18px!important;
  min-width:0!important;
}
.ga-header-row .blog-name{
  display:block!important;
  flex:0 1 390px!important;
  grid-template-columns:none!important;
  min-width:280px!important;
  padding:0!important;
}
.ga-header-row .Header h1{
  font-size:28px!important;
  letter-spacing:-.55px!important;
  line-height:1.05!important;
  white-space:normal!important;
}
.ga-header-row .Header p{
  font-size:12.5px!important;
  line-height:1.45!important;
  margin-top:6px!important;
  max-width:430px!important;
}
.ga-header-row .ga-static-nav.ga-portal-nav{
  align-items:center!important;
  display:flex!important;
  flex:1 1 auto!important;
  flex-wrap:nowrap!important;
  gap:3px!important;
  justify-content:flex-end!important;
  margin:0!important;
  min-width:0!important;
  padding:0!important;
}
.ga-header-row .ga-static-nav.ga-portal-nav a{
  border-radius:8px!important;
  font-size:12px!important;
  padding:8px 8px!important;
  white-space:nowrap!important;
}
.ga-header-row .search{
  flex:0 0 245px!important;
  float:none!important;
  left:auto!important;
  margin:0!important;
  max-width:245px!important;
  position:relative!important;
  right:auto!important;
  top:auto!important;
  width:245px!important;
}
.ga-header-row .search form{
  min-height:40px!important;
}

/* Home: cabeçalho compacto e horizontal. */
body:not(.item-view) .centered-top-container{
  padding:16px 18px!important;
}
body:not(.item-view) .ga-header-row{
  width:100%!important;
}
body:not(.item-view) .ga-header-row .ga-static-nav.ga-portal-nav{
  justify-content:center!important;
}

/* Home: destaque fora da coluna estreita do layout Emporio. */
.ga-home-stage{
  box-sizing:border-box;
  margin:26px auto 30px!important;
  max-width:1040px!important;
  padding:0!important;
  width:calc(100% - 36px)!important;
}
.ga-home-stage:before{
  color:#64748b;
  content:"ACHADO EM DESTAQUE";
  display:block;
  font-size:11px;
  font-weight:900;
  letter-spacing:.11em;
  margin:0 0 10px 4px;
}
.ga-home-stage .FeaturedPost{
  border:1px solid #dce4ee!important;
  border-radius:22px!important;
  box-shadow:0 18px 48px rgba(23,32,51,.10)!important;
  margin:0!important;
  max-width:none!important;
  overflow:hidden!important;
  padding:0 0 22px!important;
  width:100%!important;
}
.ga-home-stage .FeaturedPost:before{
  display:none!important;
}
.ga-home-stage .FeaturedPost .snippet-thumbnail{
  background:#fff!important;
  border-bottom:1px solid #edf1f5!important;
  margin:0!important;
  min-height:0!important;
  overflow:hidden!important;
}
.ga-home-stage .FeaturedPost .snippet-thumbnail img{
  background:#fff!important;
  display:block!important;
  height:330px!important;
  margin:0 auto!important;
  max-width:100%!important;
  object-fit:contain!important;
  padding:18px!important;
  width:100%!important;
}
.ga-home-stage .FeaturedPost h3{
  margin:20px 26px 7px!important;
}
.ga-home-stage .FeaturedPost h3 a{
  font-size:24px!important;
  line-height:1.22!important;
}
.ga-home-stage .FeaturedPost .post-header,
.ga-home-stage .FeaturedPost .post-footer,
.ga-home-stage .FeaturedPost .post-summary{
  margin-left:26px!important;
  margin-right:26px!important;
}

/* Arquivo mais discreto na home. */
body:not(.item-view) .widget.BlogArchive{
  border-radius:12px!important;
  box-shadow:none!important;
  opacity:.92;
}

/* Artigos: preserva o miolo visual aprovado e apenas compõe o header. */
body.item-view .centered-top-container{
  border-radius:0 0 16px 16px!important;
  padding:10px 18px!important;
}
body.item-view .ga-header-row{
  min-height:48px!important;
  width:100%!important;
}
body.item-view .ga-header-row .blog-name{
  flex:0 1 360px!important;
  min-width:240px!important;
}
body.item-view .ga-header-row .Header h1{
  font-size:25px!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
  white-space:nowrap!important;
}
body.item-view .ga-header-row .Header p{display:none!important}
body.item-view .ga-header-row .ga-static-nav.ga-portal-nav{
  display:flex!important;
  justify-content:flex-end!important;
}
body.item-view .ga-header-row .search{
  flex-basis:230px!important;
  max-width:230px!important;
  width:230px!important;
}

@media screen and (max-width:1450px){
  .ga-header-row{gap:12px!important}
  .ga-header-row .blog-name{flex-basis:330px!important}
  .ga-header-row .ga-static-nav.ga-portal-nav a{font-size:11.5px!important;padding:7px 6px!important}
  body.item-view .ga-header-row .ga-static-nav.ga-portal-nav a:nth-last-child(-n+2){display:none!important}
}

@media screen and (max-width:1100px){
  .ga-header-row{
    align-items:flex-start!important;
    flex-wrap:wrap!important;
  }
  .ga-header-row .blog-name{flex:1 1 100%!important;min-width:0!important}
  .ga-header-row .ga-static-nav.ga-portal-nav{
    flex:1 1 calc(100% - 270px)!important;
    justify-content:flex-start!important;
    overflow-x:auto!important;
  }
  .ga-header-row .search{flex:0 0 250px!important;max-width:250px!important;width:250px!important}
  body.item-view .ga-header-row .ga-static-nav.ga-portal-nav a:nth-last-child(-n+2){display:inline-block!important}
}

@media screen and (max-width:800px){
  body:not(.item-view) .centered-top-container,
  body.item-view .centered-top-container{padding:14px 14px!important}
  .ga-header-row{gap:10px!important}
  .ga-header-row .Header h1{font-size:24px!important}
  .ga-header-row .ga-static-nav.ga-portal-nav{
    flex:1 1 100%!important;
    order:2!important;
    overflow-x:auto!important;
    padding-bottom:4px!important;
  }
  .ga-header-row .search{
    flex:1 1 100%!important;
    max-width:none!important;
    order:3!important;
    width:100%!important;
  }
  .ga-home-stage{margin-top:18px!important;width:100%!important}
  .ga-home-stage:before{margin-left:16px!important}
  .ga-home-stage .FeaturedPost{border-left:0!important;border-radius:0!important;border-right:0!important}
  .ga-home-stage .FeaturedPost .snippet-thumbnail img{height:270px!important;padding:12px!important}
  .ga-home-stage .FeaturedPost h3{margin-left:18px!important;margin-right:18px!important}
  .ga-home-stage .FeaturedPost .post-header,
  .ga-home-stage .FeaturedPost .post-footer,
  .ga-home-stage .FeaturedPost .post-summary{margin-left:18px!important;margin-right:18px!important}
}
'''

JS = r'''
<script type='text/javascript'>
//<![CDATA[
(function(){
  function arrangeHeader(){
    var root=document.querySelector('.centered-top-container');
    var nav=document.querySelector('.ga-static-nav.ga-portal-nav');
    if(!root || !nav) return;

    var search=root.querySelector('.search');
    if(!search) return;

    var row=search.parentElement;
    if(!row) return;
    row.classList.add('ga-header-row');

    // Move o menu para ficar imediatamente antes da busca.
    if(nav.parentElement!==row || nav.nextElementSibling!==search){
      row.insertBefore(nav, search);
    }
  }

  function arrangeHome(){
    if(location.pathname!=='/' && location.pathname!=='') return;
    if(document.querySelector('.ga-home-stage')) return;

    var featured=document.querySelector('#page_body .FeaturedPost, .page_body .FeaturedPost');
    var centered=document.querySelector('#page_body .centered, .page_body .centered');
    if(!featured || !centered) return;

    var stage=document.createElement('section');
    stage.className='ga-home-stage';
    stage.setAttribute('aria-label','Achado em destaque');

    var anchor=centered.querySelector('.centered-bottom');
    if(anchor){
      centered.insertBefore(stage, anchor);
    }else{
      centered.appendChild(stage);
    }
    stage.appendChild(featured);
  }

  function apply(){
    arrangeHeader();
    arrangeHome();
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded', apply, {once:true});
  }else{
    apply();
  }
  setTimeout(apply, 300);
  setTimeout(apply, 1200);
})();
//]]>
</script>
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description="Gera V4: home ampla e menu no cabeçalho dos artigos.")
    p.add_argument("--theme-path", required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != "theme.xml":
        raise SystemExit("theme.xml não encontrado no caminho informado.")

    text = path.read_text(encoding="utf-8")
    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            "status":"THEME_REVISION_04_ALREADY_BUILT",
            "path":str(path),
            "size_bytes":path.stat().st_size,
            "sha256":sha256(path),
            "xml_valid":True,
            "public_marker":MARKER_NEW,
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f"A V3 validada não foi localizada. Marcador ausente: {MARKER_OLD}")

    text = text.replace(MARKER_OLD, MARKER_NEW)

    mobile_marker = "/* Mobile */"
    if mobile_marker not in text:
        raise SystemExit("Marcador CSS Mobile não encontrado.")
    text = text.replace(mobile_marker, CSS + "\n" + mobile_marker, 1)

    if "</body>" not in text:
        raise SystemExit("Elemento </body> não encontrado.")
    text = text.replace("</body>", JS + "\n</body>", 1)

    path.write_text(text, encoding="utf-8")
    ET.parse(path)

    print(json.dumps({
        "status":"THEME_REVISION_04_HOME_ITEMNAV_BUILT",
        "path":str(path),
        "size_bytes":path.stat().st_size,
        "sha256":sha256(path),
        "xml_valid":True,
        "public_marker":MARKER_NEW,
        "home_layout":"featured-wide-stage",
        "item_header":"menu-before-search",
        "post_body_preserved":True,
        "widget_state_modified":False,
        "native_theme":"Emporio preserved",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
