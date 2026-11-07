#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-18-featured-magazine"
MARKER_NEW = "emporio-revisao-visual-19-featured-editorial"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V19 FEATURED EDITORIAL
   Escopo EXCLUSIVO: Achado em destaque da HOME.
   Corrige a estrutura do Emporio criando um bloco editorial próprio.
   ============================================================ */

body:not(.item-view) .ga-home-stage .FeaturedPost[data-ga-v19-ready="1"]{
  display:block!important;
  min-height:0!important;
  overflow:hidden!important;
}

/* Depois que o novo bloco estiver pronto, esconde somente a apresentação
   nativa do FeaturedPost. O widget continua existindo e escolhendo o post. */
body:not(.item-view) .ga-home-stage .FeaturedPost[data-ga-v19-ready="1"] > :not(.ga-featured-v19-layout){
  display:none!important;
}

body:not(.item-view) .ga-featured-v19-layout{
  align-items:stretch!important;
  display:grid!important;
  grid-template-columns:minmax(0,.46fr) minmax(0,.54fr)!important;
  min-height:430px!important;
  width:100%!important;
}

body:not(.item-view) .ga-featured-v19-media{
  align-items:center!important;
  background:#f7f9fc!important;
  border-right:1px solid #edf1f5!important;
  box-sizing:border-box!important;
  display:flex!important;
  justify-content:center!important;
  min-height:430px!important;
  overflow:hidden!important;
  padding:24px!important;
}

body:not(.item-view) .ga-featured-v19-media img{
  border-radius:14px!important;
  display:block!important;
  height:100%!important;
  max-height:382px!important;
  max-width:100%!important;
  object-fit:contain!important;
  object-position:center!important;
  width:100%!important;
}

body:not(.item-view) .ga-featured-v19-copy{
  box-sizing:border-box!important;
  display:flex!important;
  flex-direction:column!important;
  justify-content:center!important;
  min-width:0!important;
  padding:42px 46px 38px!important;
}

body:not(.item-view) .ga-featured-v19-title{
  color:#172033!important;
  font:900 30px/1.16 Ubuntu,Arial,sans-serif!important;
  letter-spacing:-.45px!important;
  margin:0 0 10px!important;
}

body:not(.item-view) .ga-featured-v19-title a{
  color:inherit!important;
  text-decoration:none!important;
}

body:not(.item-view) .ga-featured-v19-title a:hover{
  color:#175cd3!important;
}

body:not(.item-view) .ga-featured-v19-date{
  color:#7a8798!important;
  font:400 14px/1.4 Georgia,serif!important;
  font-style:italic!important;
  margin:0 0 22px!important;
}

body:not(.item-view) .ga-featured-v19-excerpt{
  color:#4f5b6d!important;
  font:400 16px/1.7 Ubuntu,Arial,sans-serif!important;
  margin:0 0 26px!important;
  max-width:620px!important;
}

body:not(.item-view) .ga-featured-v19-more{
  align-items:center!important;
  align-self:flex-start!important;
  background:#175cd3!important;
  border-radius:10px!important;
  box-shadow:0 7px 18px rgba(23,92,211,.18)!important;
  color:#fff!important;
  display:inline-flex!important;
  font:800 14px/1 Ubuntu,Arial,sans-serif!important;
  min-height:44px!important;
  padding:0 19px!important;
  text-decoration:none!important;
}

body:not(.item-view) .ga-featured-v19-more:hover{
  background:#104aa9!important;
}

@media screen and (max-width:900px){
  body:not(.item-view) .ga-featured-v19-layout{
    display:block!important;
    min-height:0!important;
  }
  body:not(.item-view) .ga-featured-v19-media{
    border-bottom:1px solid #edf1f5!important;
    border-right:0!important;
    min-height:340px!important;
    padding:20px!important;
  }
  body:not(.item-view) .ga-featured-v19-media img{
    height:300px!important;
    max-height:300px!important;
  }
  body:not(.item-view) .ga-featured-v19-copy{
    padding:28px 28px 30px!important;
  }
}

@media screen and (max-width:700px){
  body:not(.item-view) .ga-featured-v19-media{
    min-height:280px!important;
    padding:14px!important;
  }
  body:not(.item-view) .ga-featured-v19-media img{
    height:250px!important;
    max-height:250px!important;
  }
  body:not(.item-view) .ga-featured-v19-copy{
    padding:23px 18px 25px!important;
  }
  body:not(.item-view) .ga-featured-v19-title{
    font-size:23px!important;
  }
  body:not(.item-view) .ga-featured-v19-excerpt{
    font-size:14px!important;
    line-height:1.65!important;
  }
}
'''

JS = r'''
<script type='text/javascript'>
//<![CDATA[
(function(){
  if(location.pathname!=='/' && location.pathname!=='') return;

  function clean(value){
    return String(value||'').replace(/\s+/g,' ').trim();
  }

  function abs(url){
    try{return new URL(url,location.href).href;}catch(e){return url||'';}
  }

  function shorten(value,max){
    value=clean(value);
    if(value.length<=max) return value;
    var out=value.slice(0,max+1);
    var cut=out.lastIndexOf(' ');
    if(cut>max*.72) out=out.slice(0,cut);
    return out.replace(/[\s,;:.!?-]+$/,'')+'…';
  }

  function imageSrc(img){
    if(!img) return '';
    var src=img.getAttribute('src') || img.getAttribute('data-src') || img.getAttribute('data-original') || img.getAttribute('data-lazy-src') || '';
    if(!src || src.indexOf('data:image/gif')===0 || src==='about:blank') return '';
    return abs(src);
  }

  function extractText(doc){
    var body=doc.querySelector('.post-body, article .post-body, article, .post');
    if(!body) return '';
    var ps=body.querySelectorAll('p');
    var chunks=[];
    for(var i=0;i<ps.length;i++){
      var t=clean(ps[i].textContent);
      if(t.length<50) continue;
      if(/aviso de afiliados/i.test(t)) continue;
      chunks.push(t);
      if(chunks.join(' ').length>=430) break;
    }
    return shorten(chunks.join(' '),390);
  }

  function extractImage(doc){
    var selectors=['.post-body img','article img','.post img','img[src*="susercontent"]'];
    for(var i=0;i<selectors.length;i++){
      var nodes=doc.querySelectorAll(selectors[i]);
      for(var j=0;j<nodes.length;j++){
        var src=imageSrc(nodes[j]);
        if(src) return {src:src,alt:nodes[j].getAttribute('alt')||''};
      }
    }
    return null;
  }

  function featured(){
    return document.querySelector('.ga-home-stage .FeaturedPost, #page_body .FeaturedPost, .page_body .FeaturedPost');
  }

  function nativeData(root){
    var link=root.querySelector('h3 a, .post-title a, a[href*="/20"]');
    var img=root.querySelector('.snippet-thumbnail img, img.ga-featured-v7-image, img');
    var header=root.querySelector('.post-header');
    return {
      url:link ? abs(link.getAttribute('href')) : '',
      title:link ? clean(link.textContent) : '',
      date:header ? clean(header.textContent) : '',
      image:imageSrc(img),
      alt:img ? (img.getAttribute('alt')||'') : ''
    };
  }

  function build(root,data){
    var layout=root.querySelector('.ga-featured-v19-layout');
    if(!layout){
      layout=document.createElement('div');
      layout.className='ga-featured-v19-layout';
      root.appendChild(layout);
    }

    layout.innerHTML='';

    var media=document.createElement('div');
    media.className='ga-featured-v19-media';
    var img=document.createElement('img');
    img.setAttribute('loading','eager');
    img.setAttribute('decoding','async');
    img.alt=data.alt || data.title || 'Imagem do achado em destaque';
    if(data.image) img.src=data.image;
    media.appendChild(img);

    var copy=document.createElement('div');
    copy.className='ga-featured-v19-copy';

    var h=document.createElement('h2');
    h.className='ga-featured-v19-title';
    var titleLink=document.createElement('a');
    titleLink.href=data.url || '#';
    titleLink.textContent=data.title || 'Achado em destaque';
    h.appendChild(titleLink);
    copy.appendChild(h);

    if(data.date){
      var date=document.createElement('div');
      date.className='ga-featured-v19-date';
      date.textContent=data.date;
      copy.appendChild(date);
    }

    var excerpt=document.createElement('p');
    excerpt.className='ga-featured-v19-excerpt';
    excerpt.textContent=data.excerpt || 'Confira os detalhes, pontos de atenção e informações completas deste achado.';
    copy.appendChild(excerpt);

    if(data.url){
      var more=document.createElement('a');
      more.className='ga-featured-v19-more';
      more.href=data.url;
      more.textContent='Ver mais...';
      more.setAttribute('aria-label','Ver artigo completo: '+(data.title||''));
      copy.appendChild(more);
    }

    layout.appendChild(media);
    layout.appendChild(copy);
    root.setAttribute('data-ga-v19-ready','1');
    return img;
  }

  function enhance(){
    var root=featured();
    if(!root || root.getAttribute('data-ga-v19-loading')==='1') return;

    var data=nativeData(root);
    if(!data.url || !data.title) return;

    root.setAttribute('data-ga-v19-loading','1');
    var renderedImg=build(root,data);

    fetch(data.url,{credentials:'same-origin'})
      .then(function(r){if(!r.ok) throw new Error('HTTP '+r.status);return r.text();})
      .then(function(html){
        var doc=new DOMParser().parseFromString(html,'text/html');
        var text=extractText(doc);
        var found=extractImage(doc);
        var excerpt=root.querySelector('.ga-featured-v19-excerpt');
        if(excerpt && text) excerpt.textContent=text;
        if(found && renderedImg){
          renderedImg.src=found.src;
          if(found.alt) renderedImg.alt=found.alt;
        }
      })
      .catch(function(){ /* Mantém os dados nativos já renderizados. */ })
      .finally(function(){root.removeAttribute('data-ga-v19-loading');});
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',enhance,{once:true});
  else enhance();
  setTimeout(enhance,350);
  setTimeout(enhance,1200);
  setTimeout(enhance,2600);
})();
//]]>
</script>
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p=argparse.ArgumentParser(description='V19: corrige definitivamente o destaque editorial da home com layout próprio.')
    p.add_argument('--theme-path', required=True)
    args=p.parse_args()

    path=Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower()!='theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text=path.read_text(encoding='utf-8')
    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
          'status':'THEME_REVISION_19_ALREADY_BUILT','path':str(path),
          'size_bytes':path.stat().st_size,'sha256':sha256(path),
          'xml_valid':True,'public_marker':MARKER_NEW
        },ensure_ascii=False,indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V18 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

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
      'status':'THEME_REVISION_19_FEATURED_EDITORIAL_BUILT',
      'path':str(path),'size_bytes':path.stat().st_size,'sha256':sha256(path),'xml_valid':True,
      'public_marker':MARKER_NEW,
      'scope':'home-featured-only',
      'featured_layout':'custom-direct-child-editorial-grid',
      'featured_image_position':'left',
      'featured_excerpt_from_article':True,
      'featured_more_link':True,
      'native_featured_visual_hidden_only_after_custom_ready':True,
      'home_cards_changed':False,
      'post_pages_changed':False,
      'static_pages_changed':False,
      'header_changed':False,
      'footer_changed':False
    },ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
