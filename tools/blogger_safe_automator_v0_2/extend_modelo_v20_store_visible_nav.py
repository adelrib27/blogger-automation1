#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_MARKER = "emporio-revisao-visual-20-modelo-final"
VISIBLE_NAV_MARKER = "BLOGGER_MODELO_V20_STORE_VISIBLE_NAV"
STORE_PATH = "/p/loja.html"

CSS = r"""
<style type='text/css'>
/* BLOGGER_MODELO_V20_STORE_VISIBLE_NAV */
.ga-home-v6-nav > a.ga-store-visible-nav-v20{
  background:linear-gradient(135deg,var(--ga-brand-primary,#0F8A5F),#F59E0B)!important;
  border-radius:8px!important;
  box-shadow:0 4px 12px rgba(15,23,42,.10)!important;
  color:#fff!important;
  font-weight:900!important;
  padding:7px 12px!important;
  text-decoration:none!important;
}
.ga-home-v6-nav > a.ga-store-visible-nav-v20:hover,
.ga-home-v6-nav > a.ga-store-visible-nav-v20.ga-store-current-v20{
  color:#fff!important;
  filter:brightness(.94)!important;
}
</style>
""".strip()

JS = r"""
<script type='text/javascript'>
//<![CDATA[
(function(){
  var STORE_PATH='/p/loja.html';

  function pathOf(href){
    try{
      var p=new URL(href,location.href).pathname.replace(/\/+$/,'');
      return p || '/';
    }catch(e){return '';}
  }

  function enhanceVisibleNav(nav){
    if(!nav) return;
    var links=nav.querySelectorAll('a[href]');
    var home=null;
    var store=null;

    for(var i=0;i<links.length;i++){
      var a=links[i];
      var p=pathOf(a.getAttribute('href')||a.href);
      var text=(a.textContent||'').replace(/\s+/g,' ').trim().toLowerCase();
      if(!home && (p==='/' || text==='início' || text==='inicio')) home=a;
      if(p===STORE_PATH) store=a;
    }

    if(!store){
      store=document.createElement('a');
      store.href=STORE_PATH;
      store.textContent='LOJA';
      store.setAttribute('aria-label','Abrir Loja');
    }

    store.classList.add('ga-store-visible-nav-v20');
    if(pathOf(location.href)===STORE_PATH) store.classList.add('ga-store-current-v20');
    else store.classList.remove('ga-store-current-v20');

    if(home && home.parentNode===nav){
      if(home.nextElementSibling!==store) nav.insertBefore(store,home.nextSibling);
    }else if(store.parentNode!==nav){
      nav.insertBefore(store,nav.firstChild);
    }
  }

  function enhance(){
    var navs=document.querySelectorAll('nav.ga-home-v6-nav');
    for(var i=0;i<navs.length;i++) enhanceVisibleNav(navs[i]);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',enhance,{once:true});
  else enhance();
  setTimeout(enhance,500);
  setTimeout(enhance,1500);
})();
//]]>
</script>
""".strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(
        description="Garante LOJA no menu customizado visível ga-home-v6-nav do BLOGGER_MODELO_V20."
    )
    p.add_argument("--theme-path", required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != "theme.xml":
        raise SystemExit("theme.xml não encontrado no caminho informado.")

    text = path.read_text(encoding="utf-8")
    if BASE_MARKER not in text:
        raise SystemExit(f"Tema não pertence ao V20 validado: marcador ausente {BASE_MARKER}")

    if VISIBLE_NAV_MARKER in text:
        ET.parse(path)
        print(json.dumps({
            "status": "BLOGGER_MODELO_V20_STORE_VISIBLE_NAV_ALREADY_APPLIED",
            "path": str(path),
            "sha256": sha256(path),
            "xml_valid": True,
            "visible_nav_marker": VISIBLE_NAV_MARKER,
            "visible_nav_selector": "nav.ga-home-v6-nav",
            "store_menu": STORE_PATH,
            "store_menu_position": "after-home",
            "store_menu_highlighted": True,
        }, ensure_ascii=False, indent=2))
        return 0

    if "</head>" not in text or "</body>" not in text:
        raise SystemExit("Tema sem </head> ou </body>; nenhuma alteração feita.")

    text = text.replace("</head>", CSS + "\n</head>", 1)
    text = text.replace("</body>", JS + "\n</body>", 1)
    path.write_text(text, encoding="utf-8")
    ET.parse(path)

    if text.count(VISIBLE_NAV_MARKER) != 1:
        raise SystemExit("Extensão de navegação visível não foi inserida exatamente uma vez.")

    print(json.dumps({
        "status": "BLOGGER_MODELO_V20_STORE_VISIBLE_NAV_APPLIED",
        "path": str(path),
        "sha256": sha256(path),
        "xml_valid": True,
        "visible_nav_marker": VISIBLE_NAV_MARKER,
        "visible_nav_selector": "nav.ga-home-v6-nav",
        "store_menu": STORE_PATH,
        "store_menu_position": "after-home",
        "store_menu_highlighted": True,
        "other_navigation_links_preserved": True,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
