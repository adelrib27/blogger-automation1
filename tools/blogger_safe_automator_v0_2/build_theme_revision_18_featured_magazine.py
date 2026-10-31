#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-17-static-fullwidth"
MARKER_NEW = "emporio-revisao-visual-18-featured-magazine"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V18 FEATURED MAGAZINE
   Escopo EXCLUSIVO: Achado em destaque da HOME.
   Desktop: imagem à esquerda + conteúdo/resumo à direita.
   Mobile: volta para uma coluna.
   ============================================================ */

body:not(.item-view) .ga-home-stage .FeaturedPost{
  align-items:stretch!important;
  display:grid!important;
  gap:0!important;
  grid-template-columns:minmax(0,.92fr) minmax(0,1.08fr)!important;
  min-height:430px!important;
  overflow:hidden!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail{
  align-items:center!important;
  align-self:stretch!important;
  background:#fff!important;
  border-bottom:0!important;
  border-right:1px solid #edf1f5!important;
  box-sizing:border-box!important;
  display:flex!important;
  height:auto!important;
  justify-content:center!important;
  margin:0!important;
  min-height:430px!important;
  overflow:hidden!important;
  padding:28px!important;
  width:100%!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail img,
body:not(.item-view) .ga-home-stage .FeaturedPost img.ga-featured-v7-image{
  display:block!important;
  height:auto!important;
  margin:auto!important;
  max-height:370px!important;
  max-width:100%!important;
  object-fit:contain!important;
  width:auto!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-copy{
  align-content:center!important;
  box-sizing:border-box!important;
  display:flex!important;
  flex-direction:column!important;
  justify-content:center!important;
  min-width:0!important;
  padding:38px 42px 34px!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-copy h3{
  margin:0 0 10px!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-copy h3 a{
  color:#172033!important;
  font-size:27px!important;
  line-height:1.18!important;
  text-decoration:none!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-copy .post-header{
  color:#7a8798!important;
  margin:0 0 18px!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-summary{
  color:#4f5b6d!important;
  font:400 15px/1.68 Ubuntu,Arial,sans-serif!important;
  margin:0!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-summary p{
  margin:0 0 22px!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-more{
  align-items:center!important;
  align-self:flex-start!important;
  background:#175cd3!important;
  border-radius:10px!important;
  box-shadow:0 7px 18px rgba(23,92,211,.18)!important;
  color:#fff!important;
  display:inline-flex!important;
  font:800 14px/1 Ubuntu,Arial,sans-serif!important;
  min-height:42px!important;
  padding:0 18px!important;
  text-decoration:none!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-more:hover{
  background:#104aa9!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-copy .post-footer{
  margin:24px 0 0!important;
  width:100%!important;
}

/* Esconde um resumo nativo eventualmente gerado pelo Emporio para evitar duplicação. */
body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-copy > .post-summary:not(.ga-featured-v18-summary){
  display:none!important;
}

@media screen and (max-width:900px){
  body:not(.item-view) .ga-home-stage .FeaturedPost{
    display:block!important;
    min-height:0!important;
  }
  body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail{
    border-bottom:1px solid #edf1f5!important;
    border-right:0!important;
    height:330px!important;
    min-height:330px!important;
    padding:20px!important;
  }
  body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail img,
  body:not(.item-view) .ga-home-stage .FeaturedPost img.ga-featured-v7-image{
    max-height:290px!important;
  }
  body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-copy{
    padding:26px 26px 28px!important;
  }
}

@media screen and (max-width:700px){
  body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail{
    height:270px!important;
    min-height:270px!important;
    padding:14px!important;
  }
  body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail img,
  body:not(.item-view) .ga-home-stage .FeaturedPost img.ga-featured-v7-image{
    max-height:242px!important;
  }
  body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-copy{
    padding:22px 18px 24px!important;
  }
  body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-copy h3 a{
    font-size:22px!important;
  }
  body:not(.item-view) .ga-home-stage .FeaturedPost .ga-featured-v18-summary{
    font-size:14px!important;
  }
}
'''

JS = r'''
<script type='text/javascript'>
//<![CDATA[
(function(){
  if(location.pathname!=='/' && location.pathname!=='') return;

  function abs(url){
    try{return new URL(url,location.href).href;}catch(e){return url||'';}
  }

  function cleanText(value){
    return String(value||'').replace(/\s+/g,' ').trim();
  }

  function shorten(value,max){
    value=cleanText(value);
    if(value.length<=max) return value;
    var out=value.slice(0,max+1);
    var cut=out.lastIndexOf(' ');
    if(cut>max*.7) out=out.slice(0,cut);
    return out.replace(/[\s,;:.!?-]+$/,'')+'…';
  }

  function featuredNode(){
    return document.querySelector('.ga-home-stage .FeaturedPost, #page_body .FeaturedPost, .page_body .FeaturedPost');
  }

  function titleLink(featured){
    return featured && featured.querySelector('h3 a, .post-title a, a[href*="/20"]');
  }

  function buildStructure(featured){
    if(!featured) return null;
    var thumb=featured.querySelector('.snippet-thumbnail');
    var title=featured.querySelector('h3');
    if(!thumb || !title) return null;

    var copy=featured.querySelector('.ga-featured-v18-copy');
    if(!copy){
      copy=document.createElement('div');
      copy.className='ga-featured-v18-copy';
      if(thumb.nextSibling) featured.insertBefore(copy,thumb.nextSibling);
      else featured.appendChild(copy);
    }

    if(title.parentNode!==copy) copy.appendChild(title);

    var header=featured.querySelector('.post-header');
    if(header && header.parentNode!==copy) copy.appendChild(header);

    var nativeSummary=featured.querySelector('.post-summary');
    if(nativeSummary && !nativeSummary.classList.contains('ga-featured-v18-summary') && nativeSummary.parentNode!==copy){
      copy.appendChild(nativeSummary);
    }

    var summary=copy.querySelector('.ga-featured-v18-summary');
    if(!summary){
      summary=document.createElement('div');
      summary.className='ga-featured-v18-summary';
      copy.appendChild(summary);
    }

    var footer=featured.querySelector('.post-footer');
    if(footer && footer.parentNode!==copy) copy.appendChild(footer);

    return {copy:copy,summary:summary};
  }

  function renderSummary(featured,text){
    var parts=buildStructure(featured);
    if(!parts) return;
    var link=titleLink(featured);
    var url=link ? abs(link.getAttribute('href')) : '';

    parts.summary.innerHTML='';
    if(text){
      var p=document.createElement('p');
      p.textContent=shorten(text,360);
      parts.summary.appendChild(p);
    }
    if(url){
      var a=document.createElement('a');
      a.className='ga-featured-v18-more';
      a.href=url;
      a.textContent='Ver mais...';
      a.setAttribute('aria-label','Ver artigo completo');
      parts.summary.appendChild(a);
    }
  }

  function extractArticleText(doc){
    var body=doc.querySelector('.post-body, article .post-body, article, .post');
    if(!body) return '';
    var ps=body.querySelectorAll('p');
    var chunks=[];
    for(var i=0;i<ps.length;i++){
      var t=cleanText(ps[i].textContent);
      if(t.length<45) continue;
      if(/aviso de afiliados/i.test(t)) continue;
      chunks.push(t);
      if(chunks.join(' ').length>=420) break;
    }
    return chunks.join(' ');
  }

  function enhance(){
    var featured=featuredNode();
    if(!featured) return;
    buildStructure(featured);

    if(featured.getAttribute('data-ga-v18-ready')==='1') return;
    var link=titleLink(featured);
    var url=link ? abs(link.getAttribute('href')) : '';
    if(!url){
      renderSummary(featured,'');
      return;
    }

    featured.setAttribute('data-ga-v18-ready','1');
    fetch(url,{credentials:'same-origin'})
      .then(function(r){if(!r.ok) throw new Error('HTTP '+r.status);return r.text();})
      .then(function(html){
        var doc=new DOMParser().parseFromString(html,'text/html');
        renderSummary(featured,extractArticleText(doc));
      })
      .catch(function(){renderSummary(featured,'');});
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',enhance,{once:true});
  else enhance();
  setTimeout(enhance,350);
  setTimeout(enhance,1200);
})();
//]]>
</script>
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p=argparse.ArgumentParser(description='V18: transforma o Achado em destaque da home em layout editorial com imagem lateral, resumo e Ver mais.')
    p.add_argument('--theme-path', required=True)
    args=p.parse_args()

    path=Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower()!='theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text=path.read_text(encoding='utf-8')
    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
          'status':'THEME_REVISION_18_ALREADY_BUILT','path':str(path),
          'size_bytes':path.stat().st_size,'sha256':sha256(path),
          'xml_valid':True,'public_marker':MARKER_NEW
        },ensure_ascii=False,indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V17 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

    text=text.replace(MARKER_OLD,MARKER_NEW,1)
    mobile_marker='/* Mobile */'
    if mobile_marker not in text:
        raise SystemExit('Marcador CSS Mobile não encontrado.')
    text=text.replace(mobile_marker,CSS+'\n'+mobile_marker,1)

    if '</body>' not in text:
        raise SystemExit('Elemento </body> não encontrado para inserir script.')
    text=text.replace('</body>',JS+'\n</body>',1)

    path.write_text(text,encoding='utf-8')
    ET.parse(path)

    print(json.dumps({
      'status':'THEME_REVISION_18_FEATURED_MAGAZINE_BUILT',
      'path':str(path),'size_bytes':path.stat().st_size,'sha256':sha256(path),'xml_valid':True,
      'public_marker':MARKER_NEW,
      'scope':'home-featured-only',
      'featured_layout':'image-left-copy-right',
      'featured_excerpt_from_article':True,
      'featured_more_link':True,
      'home_cards_changed':False,
      'post_pages_changed':False,
      'static_pages_changed':False,
      'header_changed':False,
      'footer_changed':False
    },ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
