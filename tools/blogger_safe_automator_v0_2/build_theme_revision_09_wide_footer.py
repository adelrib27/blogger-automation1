#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-08-three-columns"
MARKER_NEW = "emporio-revisao-visual-09-wide-footer"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V9 WIDE HOME + FOOTER
   Escopo EXCLUSIVO: HOME.
   Preserva FeaturedPost, grade de 3 cards e item-view.
   ============================================================ */

/* Alarga cabeçalho, destaque e grade para uma largura editorial maior. */
body:not(.item-view) .centered-top-container,
body:not(.item-view) .ga-home-stage,
body:not(.item-view) .centered-bottom,
body:not(.item-view) .ga-home-footer{
  box-sizing:border-box!important;
  max-width:1220px!important;
  width:calc(100% - 36px)!important;
}

body:not(.item-view) .centered-top-container{
  margin-left:auto!important;
  margin-right:auto!important;
}

body:not(.item-view) .ga-home-stage{
  margin-left:auto!important;
  margin-right:auto!important;
}

body:not(.item-view) .centered-bottom{
  margin-left:auto!important;
  margin-right:auto!important;
}

/* O Arquivo deixa de ocupar espaço na home. */
body:not(.item-view) .sidebar-container{
  display:none!important;
}

/* Rodapé institucional da home. */
body:not(.item-view) .ga-home-footer{
  background:#ffffff!important;
  border:1px solid #dce4ee!important;
  border-radius:20px!important;
  box-shadow:0 12px 34px rgba(23,32,51,.06)!important;
  color:#425066!important;
  margin:34px auto 26px!important;
  overflow:hidden!important;
}

body:not(.item-view) .ga-home-footer-inner{
  display:grid!important;
  gap:34px!important;
  grid-template-columns:minmax(0,1.45fr) minmax(180px,.7fr) minmax(180px,.7fr)!important;
  padding:30px 34px 24px!important;
}

body:not(.item-view) .ga-home-footer-brand h3{
  color:#172033!important;
  font:900 24px/1.12 Ubuntu,Arial,sans-serif!important;
  letter-spacing:-.45px!important;
  margin:0 0 10px!important;
}

body:not(.item-view) .ga-home-footer-brand p{
  color:#728096!important;
  font:400 13.5px/1.6 Ubuntu,Arial,sans-serif!important;
  margin:0!important;
  max-width:560px!important;
}

body:not(.item-view) .ga-home-footer h4{
  color:#172033!important;
  font:800 13px/1.2 Ubuntu,Arial,sans-serif!important;
  letter-spacing:.04em!important;
  margin:2px 0 12px!important;
  text-transform:uppercase!important;
}

body:not(.item-view) .ga-home-footer-links{
  display:flex!important;
  flex-direction:column!important;
  gap:9px!important;
}

body:not(.item-view) .ga-home-footer a{
  color:#425066!important;
  font:700 13px/1.4 Ubuntu,Arial,sans-serif!important;
  text-decoration:none!important;
}

body:not(.item-view) .ga-home-footer a:hover{
  color:#175cd3!important;
}

body:not(.item-view) .ga-home-footer-bottom{
  align-items:center!important;
  border-top:1px solid #edf1f5!important;
  color:#8793a5!important;
  display:flex!important;
  font:400 12px/1.4 Ubuntu,Arial,sans-serif!important;
  justify-content:space-between!important;
  padding:14px 34px 16px!important;
}

body:not(.item-view) .ga-home-footer-bottom strong{
  color:#5f6c7d!important;
  font-weight:700!important;
}

@media screen and (max-width:900px){
  body:not(.item-view) .ga-home-footer-inner{
    grid-template-columns:1fr 1fr!important;
  }
  body:not(.item-view) .ga-home-footer-brand{
    grid-column:1/-1!important;
  }
}

@media screen and (max-width:700px){
  body:not(.item-view) .centered-top-container,
  body:not(.item-view) .ga-home-stage,
  body:not(.item-view) .centered-bottom,
  body:not(.item-view) .ga-home-footer{
    width:100%!important;
  }

  body:not(.item-view) .ga-home-footer{
    border-left:0!important;
    border-radius:0!important;
    border-right:0!important;
    margin-bottom:0!important;
  }

  body:not(.item-view) .ga-home-footer-inner{
    gap:24px!important;
    grid-template-columns:1fr!important;
    padding:26px 18px 20px!important;
  }

  body:not(.item-view) .ga-home-footer-brand{
    grid-column:auto!important;
  }

  body:not(.item-view) .ga-home-footer-bottom{
    align-items:flex-start!important;
    flex-direction:column!important;
    gap:6px!important;
    padding:14px 18px 18px!important;
  }
}
'''

JS = r'''
<script type='text/javascript'>
//<![CDATA[
(function(){
  if(location.pathname!=='/' && location.pathname!=='') return;

  function buildFooter(){
    if(document.querySelector('.ga-home-footer')) return;

    var centered=document.querySelector('.page_body .centered');
    var bottom=document.querySelector('.page_body .centered .centered-bottom');
    if(!centered || !bottom) return;

    var footer=document.createElement('section');
    footer.className='ga-home-footer';
    footer.setAttribute('aria-label','Rodapé do Guia de Achados & Ofertas');

    var year=(new Date()).getFullYear();
    footer.innerHTML=''
      +'<div class="ga-home-footer-inner">'
      +  '<div class="ga-home-footer-brand">'
      +    '<h3>Guia de Achados &amp; Ofertas</h3>'
      +    '<p>Achados, comparativos e dicas para ajudar você a escolher produtos para casa, cozinha, tecnologia e dia a dia com mais informação.</p>'
      +  '</div>'
      +  '<div>'
      +    '<h4>Navegação</h4>'
      +    '<div class="ga-home-footer-links">'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/">Início</a>'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/p/sobre.html">Sobre</a>'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/p/aviso-de-afiliados.html">Afiliados</a>'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/p/contato.html">Contato</a>'
      +    '</div>'
      +  '</div>'
      +  '<div>'
      +    '<h4>Informações</h4>'
      +    '<div class="ga-home-footer-links">'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/p/politica-de-privacidade.html">Política de Privacidade</a>'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/p/termos-de-uso.html">Termos de Uso</a>'
      +    '</div>'
      +  '</div>'
      +'</div>'
      +'<div class="ga-home-footer-bottom">'
      +  '<span>© '+year+' <strong>Guia de Achados &amp; Ofertas</strong></span>'
      +  '<span>Conteúdo independente com links de afiliados.</span>'
      +'</div>';

    if(bottom.nextSibling){
      centered.insertBefore(footer,bottom.nextSibling);
    }else{
      centered.appendChild(footer);
    }
  }

  function apply(){ buildFooter(); }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',apply,{once:true});
  }else{
    apply();
  }
  setTimeout(apply,300);
  setTimeout(apply,1200);
})();
//]]>
</script>
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description='Gera V9: home mais larga, remove Arquivo e cria rodapé institucional.')
    p.add_argument('--theme-path', required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != 'theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text = path.read_text(encoding='utf-8')

    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            'status':'THEME_REVISION_09_ALREADY_BUILT',
            'path':str(path),
            'size_bytes':path.stat().st_size,
            'sha256':sha256(path),
            'xml_valid':True,
            'public_marker':MARKER_NEW
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V8 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

    text = text.replace(MARKER_OLD, MARKER_NEW)

    mobile_marker = '/* Mobile */'
    if mobile_marker not in text:
        raise SystemExit('Marcador CSS Mobile não encontrado.')
    text = text.replace(mobile_marker, CSS + '\n' + mobile_marker, 1)

    if '</body>' not in text:
        raise SystemExit('Elemento </body> não encontrado.')
    text = text.replace('</body>', JS + '\n</body>', 1)

    path.write_text(text, encoding='utf-8')
    ET.parse(path)

    print(json.dumps({
        'status':'THEME_REVISION_09_WIDE_FOOTER_BUILT',
        'path':str(path),
        'size_bytes':path.stat().st_size,
        'sha256':sha256(path),
        'xml_valid':True,
        'public_marker':MARKER_NEW,
        'scope':'home-only',
        'home_max_width_px':1220,
        'archive_hidden_on_home':True,
        'custom_home_footer':True,
        'featured_post_changed':False,
        'three_column_grid_preserved':True,
        'item_view_changed':False,
        'header_structure_changed':False,
        'widget_state_modified':False,
        'native_theme':'Emporio preserved'
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
