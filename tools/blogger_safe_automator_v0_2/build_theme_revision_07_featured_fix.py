#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-06-home-only"
MARKER_NEW = "emporio-revisao-visual-07-featured-fix"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V7 FEATURED FIX
   Escopo EXCLUSIVO: card de destaque da HOME.
   Não altera item-view, cabeçalho, menu ou corpo dos artigos.
   ============================================================ */

body:not(.item-view) .ga-home-stage{
  margin:22px auto 30px!important;
  max-width:1040px!important;
  width:calc(100% - 36px)!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost{
  background:#fff!important;
  border:1px solid #dce4ee!important;
  border-radius:20px!important;
  box-shadow:0 14px 34px rgba(23,32,51,.08)!important;
  overflow:hidden!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail{
  align-items:center!important;
  background:#fff!important;
  border-bottom:1px solid #edf1f5!important;
  box-sizing:border-box!important;
  display:flex!important;
  height:300px!important;
  justify-content:center!important;
  min-height:300px!important;
  overflow:hidden!important;
  padding:14px!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail img,
body:not(.item-view) .ga-home-stage .FeaturedPost img.ga-featured-v7-image{
  display:block!important;
  height:100%!important;
  margin:0 auto!important;
  max-height:272px!important;
  max-width:100%!important;
  object-fit:contain!important;
  padding:0!important;
  width:auto!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost h3{
  margin:18px 26px 6px!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost h3 a{
  font-size:23px!important;
  line-height:1.22!important;
}

body:not(.item-view) .ga-home-stage .FeaturedPost .post-header,
body:not(.item-view) .ga-home-stage .FeaturedPost .post-footer,
body:not(.item-view) .ga-home-stage .FeaturedPost .post-summary{
  margin-left:26px!important;
  margin-right:26px!important;
}

@media screen and (max-width:700px){
  body:not(.item-view) .ga-home-stage{width:100%!important}
  body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail{
    height:240px!important;
    min-height:240px!important;
    padding:10px!important;
  }
  body:not(.item-view) .ga-home-stage .FeaturedPost .snippet-thumbnail img,
  body:not(.item-view) .ga-home-stage .FeaturedPost img.ga-featured-v7-image{
    max-height:220px!important;
  }
  body:not(.item-view) .ga-home-stage .FeaturedPost h3{
    margin-left:18px!important;
    margin-right:18px!important;
  }
}
'''

JS = r'''
<script type='text/javascript'>
//<![CDATA[
(function(){
  if(location.pathname!=='/' && location.pathname!=='') return;

  function absoluteUrl(url){
    try { return new URL(url, location.href).href; }
    catch(e) { return url || ''; }
  }

  function validImageSrc(value){
    if(!value) return false;
    value=String(value).trim();
    if(!value || value.indexOf('data:image/gif')===0) return false;
    if(value==='about:blank') return false;
    return true;
  }

  function existingImage(featured){
    var imgs=featured.querySelectorAll('img');
    for(var i=0;i<imgs.length;i++){
      var img=imgs[i];
      var src=img.getAttribute('src') || img.getAttribute('data-src') || img.getAttribute('data-original') || img.getAttribute('data-lazy-src');
      if(validImageSrc(src)) return {img:img,src:absoluteUrl(src)};
    }
    return null;
  }

  function ensureThumb(featured){
    var thumb=featured.querySelector('.snippet-thumbnail');
    if(!thumb){
      thumb=document.createElement('div');
      thumb.className='snippet-thumbnail ga-featured-v7-thumb';
      featured.insertBefore(thumb,featured.firstChild);
    }
    return thumb;
  }

  function placeImage(featured, src, alt){
    if(!validImageSrc(src)) return false;
    var thumb=ensureThumb(featured);
    var img=thumb.querySelector('img.ga-featured-v7-image') || thumb.querySelector('img');
    if(!img){
      img=document.createElement('img');
      thumb.appendChild(img);
    }
    img.classList.add('ga-featured-v7-image');
    img.setAttribute('src',absoluteUrl(src));
    img.setAttribute('loading','eager');
    img.setAttribute('decoding','async');
    if(alt) img.setAttribute('alt',alt);
    return true;
  }

  function postUrl(featured){
    var titleLink=featured.querySelector('h3 a, .post-title a, a[href*="/20"]');
    return titleLink ? absoluteUrl(titleLink.getAttribute('href')) : '';
  }

  function fetchArticleImage(featured){
    if(featured.getAttribute('data-ga-v7-fetching')==='1' || featured.getAttribute('data-ga-v7-ready')==='1') return;
    var url=postUrl(featured);
    if(!url) return;
    featured.setAttribute('data-ga-v7-fetching','1');

    fetch(url,{credentials:'same-origin'})
      .then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.text(); })
      .then(function(html){
        var doc=new DOMParser().parseFromString(html,'text/html');
        var selectors=[
          '.post-body img',
          'article img',
          '.post img',
          'img[src*="susercontent"]',
          'img'
        ];
        var found=null;
        for(var i=0;i<selectors.length && !found;i++){
          var nodes=doc.querySelectorAll(selectors[i]);
          for(var j=0;j<nodes.length;j++){
            var node=nodes[j];
            var src=node.getAttribute('src') || node.getAttribute('data-src') || node.getAttribute('data-original') || node.getAttribute('data-lazy-src');
            if(validImageSrc(src)){
              found={src:absoluteUrl(src),alt:node.getAttribute('alt') || ''};
              break;
            }
          }
        }
        if(found && placeImage(featured,found.src,found.alt)){
          featured.setAttribute('data-ga-v7-ready','1');
        }
      })
      .catch(function(){ /* fail closed: mantém o card sem alterar outras áreas */ })
      .finally(function(){ featured.removeAttribute('data-ga-v7-fetching'); });
  }

  function repairFeatured(){
    var featured=document.querySelector('.ga-home-stage .FeaturedPost, #page_body .FeaturedPost, .page_body .FeaturedPost');
    if(!featured) return;

    var existing=existingImage(featured);
    if(existing){
      placeImage(featured,existing.src,existing.img.getAttribute('alt') || '');
      featured.setAttribute('data-ga-v7-ready','1');
      return;
    }

    fetchArticleImage(featured);
  }

  function apply(){ repairFeatured(); }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',apply,{once:true});
  }else{
    apply();
  }
  setTimeout(apply,350);
  setTimeout(apply,1200);
  setTimeout(apply,2600);
})();
//]]>
</script>
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description='Gera V7: corrige somente imagem/tamanho do destaque da home.')
    p.add_argument('--theme-path', required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != 'theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text = path.read_text(encoding='utf-8')
    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            'status':'THEME_REVISION_07_ALREADY_BUILT',
            'path':str(path),
            'size_bytes':path.stat().st_size,
            'sha256':sha256(path),
            'xml_valid':True,
            'public_marker':MARKER_NEW
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V6 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

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
        'status':'THEME_REVISION_07_FEATURED_FIX_BUILT',
        'path':str(path),
        'size_bytes':path.stat().st_size,
        'sha256':sha256(path),
        'xml_valid':True,
        'public_marker':MARKER_NEW,
        'scope':'home-featured-only',
        'item_view_changed':False,
        'header_changed':False,
        'featured_image_strategy':'existing-image-or-fetch-first-article-image',
        'featured_height_px':300,
        'native_theme':'Emporio preserved'
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
