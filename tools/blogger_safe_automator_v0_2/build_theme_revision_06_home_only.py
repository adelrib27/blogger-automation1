#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-05-exact-header"
MARKER_NEW = "emporio-revisao-visual-06-home-only"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V6 HOME ONLY
   IMPORTANTE: nenhum seletor desta camada altera body.item-view.
   A postagem/cabeçalho interno da V5 permanece congelado.
   ============================================================ */

body:not(.item-view) .centered-top-container{
  box-sizing:border-box!important;
  margin:18px auto 0!important;
  max-width:1180px!important;
  padding:0!important;
  width:calc(100% - 36px)!important;
}

body:not(.item-view) .ga-home-v6-row{
  align-items:center!important;
  box-sizing:border-box!important;
  display:flex!important;
  gap:20px!important;
  min-height:88px!important;
  padding:16px 22px!important;
  width:100%!important;
}

body:not(.item-view) .ga-home-v6-row .blog-name{
  display:block!important;
  flex:0 1 340px!important;
  grid-template-columns:none!important;
  margin:0!important;
  min-width:280px!important;
  padding:0!important;
}

body:not(.item-view) .ga-home-v6-row .Header h1{
  font-size:27px!important;
  letter-spacing:-.55px!important;
  line-height:1.05!important;
  margin:0!important;
  white-space:nowrap!important;
}

body:not(.item-view) .ga-home-v6-row .Header p{
  color:#667085!important;
  font-size:12.5px!important;
  font-style:normal!important;
  line-height:1.42!important;
  margin:6px 0 0!important;
  max-width:340px!important;
}

body:not(.item-view) .ga-home-v6-nav{
  align-items:center!important;
  display:flex!important;
  flex:1 1 auto!important;
  flex-wrap:nowrap!important;
  gap:4px!important;
  justify-content:center!important;
  margin:0!important;
  min-width:0!important;
  padding:0!important;
}

body:not(.item-view) .ga-home-v6-nav a{
  border:1px solid transparent!important;
  border-radius:8px!important;
  color:#334155!important;
  font-size:12px!important;
  font-weight:800!important;
  line-height:1!important;
  padding:8px 8px!important;
  text-decoration:none!important;
  white-space:nowrap!important;
}

body:not(.item-view) .ga-home-v6-nav a:hover{
  background:#eef5ff!important;
  border-color:#d8e8ff!important;
  color:#0f46a3!important;
}

body:not(.item-view) .ga-home-v6-nav .ga-home-link{
  background:#175cd3!important;
  border-color:#175cd3!important;
  color:#fff!important;
}

body:not(.item-view) .ga-home-v6-row .search{
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

body:not(.item-view) .ga-home-v6-row .search form{
  margin:0!important;
  min-height:40px!important;
}

/* Na home existe exatamente um menu: o V6. */
body:not(.item-view) .ga-static-nav,
body:not(.item-view) .ga-exact-nav{
  display:none!important;
}
body:not(.item-view) .ga-home-v6-nav{display:flex!important}

/* Destaque: mantém o stage já validado, mas corrige proporção e leitura. */
body:not(.item-view) .ga-home-stage{
  margin:24px auto 32px!important;
  max-width:1040px!important;
  width:calc(100% - 36px)!important;
}
body:not(.item-view) .ga-home-stage .FeaturedPost{
  border-radius:20px!important;
  overflow:hidden!important;
}
body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail{
  background-color:#fff!important;
  min-height:300px!important;
}
body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail img{
  display:block!important;
  height:330px!important;
  margin:0 auto!important;
  max-width:100%!important;
  object-fit:contain!important;
  padding:14px!important;
  width:100%!important;
}
body:not(.item-view) .ga-home-stage .FeaturedPost h3{
  margin:20px 26px 7px!important;
}
body:not(.item-view) .ga-home-stage .FeaturedPost h3 a{
  font-size:23px!important;
  line-height:1.22!important;
}

@media screen and (max-width:1050px){
  body:not(.item-view) .ga-home-v6-row{
    align-items:flex-start!important;
    flex-wrap:wrap!important;
  }
  body:not(.item-view) .ga-home-v6-row .blog-name{
    flex:1 1 calc(100% - 270px)!important;
    min-width:0!important;
  }
  body:not(.item-view) .ga-home-v6-row .search{
    flex:0 0 245px!important;
  }
  body:not(.item-view) .ga-home-v6-nav{
    flex:1 1 100%!important;
    justify-content:flex-start!important;
    order:3!important;
    overflow-x:auto!important;
  }
}

@media screen and (max-width:700px){
  body:not(.item-view) .centered-top-container{
    margin-top:0!important;
    width:100%!important;
  }
  body:not(.item-view) .ga-home-v6-row{
    gap:10px!important;
    padding:14px!important;
  }
  body:not(.item-view) .ga-home-v6-row .blog-name,
  body:not(.item-view) .ga-home-v6-row .search,
  body:not(.item-view) .ga-home-v6-nav{
    flex:1 1 100%!important;
    max-width:none!important;
    width:100%!important;
  }
  body:not(.item-view) .ga-home-v6-row .Header h1{
    font-size:23px!important;
    white-space:normal!important;
  }
  body:not(.item-view) .ga-home-v6-nav{
    justify-content:flex-start!important;
    overflow-x:auto!important;
  }
  body:not(.item-view) .ga-home-stage{
    width:100%!important;
  }
  body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail img{
    height:270px!important;
  }
}
'''

JS = r'''
<script type='text/javascript'>
//<![CDATA[
(function(){
  if(location.pathname!=='/' && location.pathname!=='') return;

  var links=[
    ['Início','https://guia-de-achados-e-ofertas.blogspot.com/','ga-home-link'],
    ['Sobre','https://guia-de-achados-e-ofertas.blogspot.com/p/sobre.html',''],
    ['Afiliados','https://guia-de-achados-e-ofertas.blogspot.com/p/aviso-de-afiliados.html',''],
    ['Contato','https://guia-de-achados-e-ofertas.blogspot.com/p/contato.html',''],
    ['Privacidade','https://guia-de-achados-e-ofertas.blogspot.com/p/politica-de-privacidade.html',''],
    ['Termos','https://guia-de-achados-e-ofertas.blogspot.com/p/termos-de-uso.html','']
  ];

  function buildNav(){
    var nav=document.createElement('nav');
    nav.className='ga-home-v6-nav';
    nav.setAttribute('aria-label','Navegação principal');
    links.forEach(function(x){
      var a=document.createElement('a');
      a.textContent=x[0];
      a.href=x[1];
      if(x[2]) a.className=x[2];
      nav.appendChild(a);
    });
    return nav;
  }

  function restoreInlineBackgrounds(scope){
    if(!scope) return;
    var nodes=scope.querySelectorAll('[style]');
    Array.prototype.forEach.call(nodes,function(el){
      var bg=el.style.backgroundImage;
      if(bg && bg!=='none'){
        el.style.setProperty('background-image',bg,'important');
        el.style.setProperty('background-position','center','important');
        el.style.setProperty('background-repeat','no-repeat','important');
        el.style.setProperty('background-size','contain','important');
      }
    });
  }

  function arrangeHomeHeader(){
    var root=document.querySelector('.centered-top-container');
    if(!root) return;
    var brand=root.querySelector('.blog-name');
    var search=root.querySelector('.search');
    if(!brand || !search) return;

    // Remove todos os menus criados pelas revisões anteriores somente na home.
    var old=root.querySelectorAll('.ga-exact-nav,.ga-static-nav,.ga-home-v6-nav');
    Array.prototype.forEach.call(old,function(n){ if(n.parentNode) n.parentNode.removeChild(n); });

    var row=root.querySelector('.ga-home-v6-row');
    if(!row){
      row=document.createElement('div');
      row.className='ga-home-v6-row';
      root.insertBefore(row,root.firstChild);
    }

    row.appendChild(brand);
    row.appendChild(buildNav());
    row.appendChild(search);
  }

  function fixFeatured(){
    var featured=document.querySelector('.ga-home-stage .FeaturedPost, #page_body .FeaturedPost, .page_body .FeaturedPost');
    if(!featured) return;
    restoreInlineBackgrounds(featured);

    // Alguns layouts do Emporio usam lazy-src/data-src em vez de src imediato.
    var imgs=featured.querySelectorAll('img');
    Array.prototype.forEach.call(imgs,function(img){
      if(!img.getAttribute('src') || img.getAttribute('src').indexOf('data:')===0){
        var candidate=img.getAttribute('data-src') || img.getAttribute('data-original') || img.getAttribute('data-lazy-src');
        if(candidate) img.setAttribute('src',candidate);
      }
    });
  }

  function apply(){
    arrangeHomeHeader();
    fixFeatured();
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',apply,{once:true});
  }else{
    apply();
  }

  setTimeout(apply,300);
  setTimeout(apply,1000);
  setTimeout(apply,2200);

  var stopAt=Date.now()+5000;
  var observer=new MutationObserver(function(){
    if(Date.now()>stopAt){ observer.disconnect(); return; }
    apply();
  });
  observer.observe(document.documentElement,{childList:true,subtree:true});
  setTimeout(function(){ observer.disconnect(); apply(); },5200);
})();
//]]>
</script>
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p=argparse.ArgumentParser(description='Gera V6 com alterações exclusivas da página inicial.')
    p.add_argument('--theme-path',required=True)
    args=p.parse_args()

    path=Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower()!='theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text=path.read_text(encoding='utf-8')
    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
          'status':'THEME_REVISION_06_ALREADY_BUILT',
          'path':str(path),'size_bytes':path.stat().st_size,
          'sha256':sha256(path),'xml_valid':True,'public_marker':MARKER_NEW
        },ensure_ascii=False,indent=2))
        return 0
    if MARKER_OLD not in text:
        raise SystemExit(f'A V5 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

    text=text.replace(MARKER_OLD,MARKER_NEW)
    mobile_marker='/* Mobile */'
    if mobile_marker not in text:
        raise SystemExit('Marcador CSS Mobile não encontrado.')
    text=text.replace(mobile_marker,CSS+'\n'+mobile_marker,1)
    if '</body>' not in text:
        raise SystemExit('Elemento </body> não encontrado.')
    text=text.replace('</body>',JS+'\n</body>',1)

    path.write_text(text,encoding='utf-8')
    ET.parse(path)

    print(json.dumps({
      'status':'THEME_REVISION_06_HOME_ONLY_BUILT',
      'path':str(path),'size_bytes':path.stat().st_size,
      'sha256':sha256(path),'xml_valid':True,
      'public_marker':MARKER_NEW,
      'scope':'home-only',
      'item_view_changed':False,
      'home_menu':'single-brand-menu-search',
      'featured_image_repair':True,
      'widget_state_modified':False,
      'native_theme':'Emporio preserved'
    },ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
