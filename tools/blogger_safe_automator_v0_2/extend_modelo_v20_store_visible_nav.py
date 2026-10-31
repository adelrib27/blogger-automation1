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
/* alvo primario validado: nav.ga-home-v6-nav */
nav a.ga-store-visible-nav-v20{
  background:linear-gradient(135deg,var(--ga-brand-primary,#0F8A5F),#F59E0B)!important;
  border-radius:8px!important;
  box-shadow:0 4px 12px rgba(15,23,42,.10)!important;
  color:#fff!important;
  font-weight:900!important;
  padding:7px 12px!important;
  text-decoration:none!important;
}
nav a.ga-store-visible-nav-v20:hover,
nav a.ga-store-visible-nav-v20.ga-store-current-v20{
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
  var PRIMARY_NAV_SELECTOR='nav.ga-home-v6-nav';
  var FALLBACK_DEDUPE_MARKER='BLOGGER_MODELO_V20_STORE_FALLBACK_DEDUPE';
  var INSTITUTIONAL={
    '/p/sobre.html':1,
    '/p/aviso-de-afiliados.html':1,
    '/p/contato.html':1,
    '/p/politica-de-privacidade.html':1,
    '/p/termos-de-uso.html':1
  };

  function pathOf(href){
    try{
      var p=new URL(href,location.href).pathname.replace(/\/+$/,'');
      return p || '/';
    }catch(e){return '';}
  }

  function isHeaderNav(nav){
    if(!nav || !nav.querySelectorAll) return false;
    if(nav.closest && nav.closest('footer,.ga-home-footer,.ga-post-footer')) return false;
    if(nav.classList && nav.classList.contains('top-nav')) return false;

    var links=nav.querySelectorAll('a[href]');
    var home=false;
    var institutionalCount=0;
    for(var i=0;i<links.length;i++){
      var a=links[i];
      var p=pathOf(a.getAttribute('href')||a.href);
      var text=(a.textContent||'').replace(/\s+/g,' ').trim().toLowerCase();
      if(p==='/' || text==='início' || text==='inicio') home=true;
      if(INSTITUTIONAL[p]) institutionalCount++;
    }
    return home && institutionalCount>=2;
  }

  function enhanceVisibleNav(nav){
    if(!isHeaderNav(nav)) return;

    var links=nav.querySelectorAll('a[href]');
    var home=null;
    var store=null;
    var duplicateStores=[];

    for(var i=0;i<links.length;i++){
      var a=links[i];
      var p=pathOf(a.getAttribute('href')||a.href);
      var text=(a.textContent||'').replace(/\s+/g,' ').trim().toLowerCase();
      if(!home && (p==='/' || text==='início' || text==='inicio')) home=a;
      if(p===STORE_PATH){
        if(!store) store=a;
        else duplicateStores.push(a);
      }
    }

    for(var d=0;d<duplicateStores.length;d++){
      var dup=duplicateStores[d];
      if(dup.parentNode) dup.parentNode.removeChild(dup);
    }

    if(!home) return;

    if(!store){
      store=document.createElement('a');
      store.href=STORE_PATH;
      store.textContent='LOJA';
      store.setAttribute('aria-label','Abrir Loja');
    }

    store.classList.add('ga-store-visible-nav-v20');
    store.setAttribute('data-ga-store-header-nav','BLOGGER_MODELO_V20_STORE_HEADER_NAV');
    if(pathOf(location.href)===STORE_PATH) store.classList.add('ga-store-current-v20');
    else store.classList.remove('ga-store-current-v20');

    var parent=home.parentNode;
    if(parent===nav){
      if(home.nextElementSibling!==store) nav.insertBefore(store,home.nextSibling);
    }else if(parent && parent.tagName && parent.tagName.toLowerCase()==='li' && parent.parentNode){
      var list=parent.parentNode;
      var storeLi=store.closest ? store.closest('li') : null;
      if(!storeLi){
        storeLi=document.createElement('li');
        storeLi.className='ga-store-header-li-v20';
        storeLi.appendChild(store);
      }
      if(parent.nextElementSibling!==storeLi) list.insertBefore(storeLi,parent.nextSibling);
    }
    nav.setAttribute('data-ga-store-header-enhanced','1');
  }

  function dedupeFallbackPageList(pageList){
    if(!pageList) return;
    var list=pageList.querySelector('ul');
    if(!list) return;

    var links=list.querySelectorAll('a[href]');
    var homeLi=null;
    var storeLi=null;
    var duplicates=[];

    for(var i=0;i<links.length;i++){
      var a=links[i];
      var p=pathOf(a.getAttribute('href')||a.href);
      var text=(a.textContent||'').replace(/\s+/g,' ').trim().toLowerCase();
      var li=a.closest ? a.closest('li') : a.parentNode;
      if(!li) continue;
      if(!homeLi && (p==='/' || text==='início' || text==='inicio')) homeLi=li;
      if(p===STORE_PATH){
        if(!storeLi) storeLi=li;
        else duplicates.push(li);
      }
    }

    for(var d=0;d<duplicates.length;d++){
      var dup=duplicates[d];
      if(dup.parentNode===list) list.removeChild(dup);
    }

    if(storeLi){
      storeLi.classList.add('ga-store-nav-v20');
      storeLi.setAttribute('data-ga-store-dedupe',FALLBACK_DEDUPE_MARKER);
      if(homeLi && homeLi.parentNode===list && homeLi.nextElementSibling!==storeLi){
        list.insertBefore(storeLi,homeLi.nextSibling);
      }
    }
  }

  function enhance(){
    var primary=document.querySelectorAll(PRIMARY_NAV_SELECTOR);
    for(var p=0;p<primary.length;p++) enhanceVisibleNav(primary[p]);

    var navs=document.querySelectorAll('nav');
    for(var i=0;i<navs.length;i++) enhanceVisibleNav(navs[i]);

    var pageLists=document.querySelectorAll('.centered-top-container .PageList');
    for(var j=0;j<pageLists.length;j++) dedupeFallbackPageList(pageLists[j]);
  }

  var scheduled=false;
  function scheduleEnhance(){
    if(scheduled) return;
    scheduled=true;
    setTimeout(function(){scheduled=false;enhance();},30);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',enhance,{once:true});
  else enhance();
  setTimeout(enhance,500);
  setTimeout(enhance,1500);
  setTimeout(enhance,3000);

  if(window.MutationObserver && document.documentElement){
    new MutationObserver(scheduleEnhance).observe(document.documentElement,{childList:true,subtree:true});
  }
})();
//]]>
</script>
""".strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(
        description="Garante LOJA nos menus visiveis e cabecalhos fixos do BLOGGER_MODELO_V20."
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
            "dynamic_header_nav_supported": True,
            "store_menu": STORE_PATH,
            "store_menu_position": "after-home",
            "store_menu_highlighted": True,
            "fallback_pagelist_deduplicated": True,
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
        "dynamic_header_nav_supported": True,
        "store_menu": STORE_PATH,
        "store_menu_position": "after-home",
        "store_menu_highlighted": True,
        "fallback_pagelist_deduplicated": True,
        "other_navigation_links_preserved": True,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
