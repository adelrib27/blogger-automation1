#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-04-home-itemnav"
MARKER_NEW = "emporio-revisao-visual-05-exact-header"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V5 EXACT HEADER
   Ordem literal no desktop: MARCA -> MENU -> BUSCA.
   O corpo do artigo da V4 permanece intacto.
   ============================================================ */

/* Linha única do cabeçalho em desktop */
.centered-top-container .ga-exact-row{
  align-items:center!important;
  display:flex!important;
  gap:22px!important;
  min-height:68px!important;
  width:100%!important;
}
.centered-top-container .ga-exact-row .blog-name{
  display:block!important;
  flex:0 1 360px!important;
  margin:0!important;
  min-width:260px!important;
  padding:0!important;
}
.centered-top-container .ga-exact-row .Header h1{
  font-size:27px!important;
  letter-spacing:-.55px!important;
  line-height:1.04!important;
  margin:0!important;
  white-space:nowrap!important;
}
.centered-top-container .ga-exact-row .Header p{
  font-size:12px!important;
  line-height:1.4!important;
  margin:5px 0 0!important;
  max-width:360px!important;
}

/* Menu compartilhado entre home e páginas internas */
.ga-exact-nav{
  align-items:center!important;
  display:flex!important;
  flex:1 1 auto!important;
  flex-wrap:nowrap!important;
  gap:4px!important;
  justify-content:flex-start!important;
  margin:0!important;
  min-width:0!important;
  padding:0!important;
}
.ga-exact-nav a{
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
.ga-exact-nav a:hover{
  background:#eef5ff!important;
  border-color:#d8e8ff!important;
  color:#0f46a3!important;
}
.ga-exact-nav .ga-home-link{
  background:#175cd3!important;
  border-color:#175cd3!important;
  color:#fff!important;
}

/* Busca fixa à direita */
.centered-top-container .ga-exact-row .search{
  flex:0 0 245px!important;
  float:none!important;
  left:auto!important;
  margin:0!important;
  max-width:245px!important;
  order:3!important;
  position:relative!important;
  right:auto!important;
  top:auto!important;
  width:245px!important;
}
.centered-top-container .ga-exact-row .search form{min-height:40px!important}
.centered-top-container .ga-exact-row .blog-name{order:1!important}
.centered-top-container .ga-exact-row .ga-exact-nav{order:2!important}

/* Desliga o menu estático antigo depois que a V5 cria o menu certo. */
.ga-static-nav.ga-portal-nav{display:none!important}

/* HOME: mantém destaque amplo, mas sem deformar a composição do cabeçalho */
body:not(.item-view) .centered-top-container{
  padding:15px 20px!important;
}
body:not(.item-view) .ga-home-stage{
  margin:24px auto 30px!important;
  max-width:1040px!important;
  width:calc(100% - 36px)!important;
}
body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail img{
  height:330px!important;
  object-fit:contain!important;
  padding:16px!important;
}

/* POST: apenas cabeçalho. Corpo/hero do artigo permanece como na V4. */
body.item-view .centered-top-container{
  padding:10px 20px!important;
}
body.item-view .ga-exact-row{
  min-height:48px!important;
}
body.item-view .ga-exact-row .blog-name{
  flex-basis:330px!important;
  min-width:250px!important;
}
body.item-view .ga-exact-row .Header h1{
  font-size:24px!important;
  max-width:330px!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
}
body.item-view .ga-exact-row .Header p{display:none!important}
body.item-view .ga-exact-nav a{
  font-size:11.5px!important;
  padding:7px 6px!important;
}
body.item-view .ga-exact-row .search{
  flex-basis:230px!important;
  max-width:230px!important;
  width:230px!important;
}

@media screen and (max-width:1280px){
  .centered-top-container .ga-exact-row{gap:12px!important}
  .centered-top-container .ga-exact-row .blog-name{flex-basis:300px!important;min-width:220px!important}
  .centered-top-container .ga-exact-row .Header h1{font-size:24px!important}
  .ga-exact-nav a{font-size:11px!important;padding:7px 5px!important}
  .centered-top-container .ga-exact-row .search{flex-basis:220px!important;max-width:220px!important;width:220px!important}
}

@media screen and (max-width:980px){
  .centered-top-container .ga-exact-row{
    align-items:flex-start!important;
    flex-wrap:wrap!important;
  }
  .centered-top-container .ga-exact-row .blog-name{
    flex:1 1 calc(100% - 250px)!important;
    min-width:0!important;
  }
  .centered-top-container .ga-exact-row .search{
    flex:0 0 230px!important;
    max-width:230px!important;
    order:2!important;
    width:230px!important;
  }
  .centered-top-container .ga-exact-row .ga-exact-nav{
    flex:1 1 100%!important;
    order:3!important;
    overflow-x:auto!important;
    padding-top:4px!important;
  }
}

@media screen and (max-width:700px){
  .centered-top-container .ga-exact-row .blog-name{flex:1 1 100%!important}
  .centered-top-container .ga-exact-row .Header h1{font-size:23px!important;white-space:normal!important}
  .centered-top-container .ga-exact-row .ga-exact-nav{
    flex:1 1 100%!important;
    order:2!important;
    overflow-x:auto!important;
  }
  .centered-top-container .ga-exact-row .search{
    flex:1 1 100%!important;
    max-width:none!important;
    order:3!important;
    width:100%!important;
  }
}
'''

JS = r'''
<script type='text/javascript'>
//<![CDATA[
(function(){
  var links = [
    ['Início','https://guia-de-achados-e-ofertas.blogspot.com/','ga-home-link'],
    ['Sobre','https://guia-de-achados-e-ofertas.blogspot.com/p/sobre.html',''],
    ['Afiliados','https://guia-de-achados-e-ofertas.blogspot.com/p/aviso-de-afiliados.html',''],
    ['Contato','https://guia-de-achados-e-ofertas.blogspot.com/p/contato.html',''],
    ['Privacidade','https://guia-de-achados-e-ofertas.blogspot.com/p/politica-de-privacidade.html',''],
    ['Termos','https://guia-de-achados-e-ofertas.blogspot.com/p/termos-de-uso.html','']
  ];

  function buildNav(){
    var nav=document.createElement('nav');
    nav.className='ga-exact-nav';
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

  function arrangeExactHeader(){
    var root=document.querySelector('.centered-top-container');
    if(!root) return;
    var search=root.querySelector('.search');
    var brand=root.querySelector('.blog-name');
    if(!search || !brand) return;

    var row=search.parentElement;
    if(!row) return;
    row.classList.add('ga-exact-row');

    // Garante que a marca esteja dentro da mesma linha e em primeiro lugar.
    if(brand.parentElement!==row){
      row.insertBefore(brand,row.firstChild);
    }else if(row.firstElementChild!==brand){
      row.insertBefore(brand,row.firstChild);
    }

    // O Blogger não renderiza o menu estático na página interna; por isso
    // a V5 cria um menu real em todas as páginas, sem depender do PageList.
    var nav=row.querySelector(':scope > .ga-exact-nav');
    if(!nav){
      nav=buildNav();
      row.insertBefore(nav,search);
    }else if(nav.nextElementSibling!==search){
      row.insertBefore(nav,search);
    }
  }

  function apply(){ arrangeExactHeader(); }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',apply,{once:true});
  }else{
    apply();
  }
  setTimeout(apply,200);
  setTimeout(apply,800);
  setTimeout(apply,1800);
})();
//]]>
</script>
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p=argparse.ArgumentParser(description='Gera V5 com cabeçalho exato: marca, menu, busca.')
    p.add_argument('--theme-path',required=True)
    args=p.parse_args()

    path=Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower()!='theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text=path.read_text(encoding='utf-8')
    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({'status':'THEME_REVISION_05_ALREADY_BUILT','path':str(path),'size_bytes':path.stat().st_size,'sha256':sha256(path),'xml_valid':True,'public_marker':MARKER_NEW},ensure_ascii=False,indent=2))
        return 0
    if MARKER_OLD not in text:
        raise SystemExit(f'A V4 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

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
      'status':'THEME_REVISION_05_EXACT_HEADER_BUILT',
      'path':str(path),
      'size_bytes':path.stat().st_size,
      'sha256':sha256(path),
      'xml_valid':True,
      'public_marker':MARKER_NEW,
      'desktop_header_order':'brand-menu-search',
      'item_menu_created_independently':True,
      'post_body_preserved':True,
      'widget_state_modified':False,
      'native_theme':'Emporio preserved'
    },ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
