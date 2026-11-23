#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-19-featured-editorial"
MARKER_NEW = "emporio-revisao-visual-20-modelo-final"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V20 MODELO FINAL
   Escopo: páginas de POST.
   Adiciona Artigos relacionados abaixo do artigo principal.
   ============================================================ */

body.item-view .ga-related-v20{
  background:#fff!important;
  border:1px solid #dce4ee!important;
  border-radius:18px!important;
  box-shadow:0 12px 30px rgba(23,32,51,.06)!important;
  box-sizing:border-box!important;
  margin:28px 0 10px!important;
  overflow:hidden!important;
  padding:24px!important;
  width:100%!important;
}

body.item-view .ga-related-v20 h2{
  color:#172033!important;
  font:900 22px/1.2 Ubuntu,Arial,sans-serif!important;
  letter-spacing:-.25px!important;
  margin:0 0 18px!important;
}

body.item-view .ga-related-v20-grid{
  display:grid!important;
  gap:16px!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
}

body.item-view .ga-related-v20-card{
  background:#fff!important;
  border:1px solid #e6ebf1!important;
  border-radius:14px!important;
  box-sizing:border-box!important;
  color:#172033!important;
  display:flex!important;
  flex-direction:column!important;
  min-width:0!important;
  overflow:hidden!important;
  text-decoration:none!important;
  transition:transform .16s ease,box-shadow .16s ease!important;
}

body.item-view .ga-related-v20-card:hover{
  box-shadow:0 10px 22px rgba(23,32,51,.09)!important;
  transform:translateY(-2px)!important;
}

body.item-view .ga-related-v20-media{
  aspect-ratio:1 / 1!important;
  background:#f7f9fc!important;
  display:block!important;
  overflow:hidden!important;
  width:100%!important;
}

body.item-view .ga-related-v20-media img{
  display:block!important;
  height:100%!important;
  object-fit:cover!important;
  object-position:center!important;
  width:100%!important;
}

body.item-view .ga-related-v20-body{
  display:flex!important;
  flex:1!important;
  flex-direction:column!important;
  padding:14px 14px 15px!important;
}

body.item-view .ga-related-v20-title{
  color:#172033!important;
  display:-webkit-box!important;
  font:800 14px/1.4 Ubuntu,Arial,sans-serif!important;
  -webkit-box-orient:vertical!important;
  -webkit-line-clamp:3!important;
  margin:0!important;
  overflow:hidden!important;
}

body.item-view .ga-related-v20-more{
  color:#175cd3!important;
  font:800 12px/1.3 Ubuntu,Arial,sans-serif!important;
  margin-top:auto!important;
  padding-top:12px!important;
}

@media screen and (max-width:900px){
  body.item-view .ga-related-v20-grid{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
}

@media screen and (max-width:620px){
  body.item-view .ga-related-v20{
    border-left:0!important;
    border-radius:0!important;
    border-right:0!important;
    padding:20px 16px!important;
  }
  body.item-view .ga-related-v20-grid{
    grid-template-columns:1fr!important;
  }
  body.item-view .ga-related-v20-card{
    display:grid!important;
    grid-template-columns:118px minmax(0,1fr)!important;
  }
  body.item-view .ga-related-v20-media{
    aspect-ratio:1 / 1!important;
    height:100%!important;
  }
}
'''

JS = r'''
<script type='text/javascript'>
//<![CDATA[
(function(){
  if(!document.body.classList.contains('item-view')) return;

  function norm(url){
    try{
      var u=new URL(url,location.href);
      u.hash='';u.search='';
      return u.href.replace(/\/$/,'');
    }catch(e){return String(url||'').replace(/[?#].*$/,'').replace(/\/$/,'');}
  }

  function htmlText(value){
    var d=document.createElement('div');
    d.innerHTML=value||'';
    return (d.textContent||'').replace(/\s+/g,' ').trim();
  }

  function entryUrl(entry){
    var links=entry && entry.link || [];
    for(var i=0;i<links.length;i++) if(links[i].rel==='alternate') return links[i].href||'';
    return '';
  }

  function entryImage(entry){
    if(entry && entry.media$thumbnail && entry.media$thumbnail.url){
      return entry.media$thumbnail.url.replace(/\/s\d+(-c)?\//,'/s640/');
    }
    var raw=(entry && entry.content && entry.content.$t) || (entry && entry.summary && entry.summary.$t) || '';
    if(raw){
      var doc=new DOMParser().parseFromString('<div>'+raw+'</div>','text/html');
      var img=doc.querySelector('img');
      if(img){
        return img.getAttribute('src') || img.getAttribute('data-src') || img.getAttribute('data-original') || '';
      }
    }
    return '';
  }

  function toItem(entry){
    return {
      url:entryUrl(entry),
      title:entry && entry.title ? htmlText(entry.title.$t) : '',
      image:entryImage(entry)
    };
  }

  function fetchFeed(url){
    return fetch(url,{credentials:'same-origin'})
      .then(function(r){if(!r.ok) throw new Error('HTTP '+r.status);return r.json();})
      .then(function(data){return (data.feed && data.feed.entry || []).map(toItem);})
      .catch(function(){return [];});
  }

  function labels(){
    var nodes=document.querySelectorAll('.post-labels a,a[rel="tag"],.labels a');
    var out=[];
    for(var i=0;i<nodes.length;i++){
      var t=(nodes[i].textContent||'').replace(/\s+/g,' ').trim();
      if(t && out.indexOf(t)<0) out.push(t);
      if(out.length>=2) break;
    }
    return out;
  }

  function dedupe(items){
    var seen={};
    var current=norm(location.href);
    var out=[];
    for(var i=0;i<items.length;i++){
      var it=items[i];
      var u=norm(it.url);
      if(!u || u===current || seen[u] || !it.title) continue;
      seen[u]=1;
      out.push(it);
    }
    return out;
  }

  function host(){
    var body=document.querySelector('.post-body');
    if(!body) return null;
    return body.closest('.post-outer-container') || body.closest('.post-outer') || body.closest('.post') || body;
  }

  function render(items){
    if(document.querySelector('.ga-related-v20')) return;
    items=dedupe(items).slice(0,3);
    if(!items.length) return;
    var anchor=host();
    if(!anchor || !anchor.parentNode) return;

    var section=document.createElement('section');
    section.className='ga-related-v20';
    section.setAttribute('aria-label','Artigos relacionados');

    var h=document.createElement('h2');
    h.textContent='Artigos relacionados';
    section.appendChild(h);

    var grid=document.createElement('div');
    grid.className='ga-related-v20-grid';

    for(var i=0;i<items.length;i++){
      var it=items[i];
      var a=document.createElement('a');
      a.className='ga-related-v20-card';
      a.href=it.url;

      var media=document.createElement('span');
      media.className='ga-related-v20-media';
      if(it.image){
        var img=document.createElement('img');
        img.src=it.image;
        img.alt=it.title;
        img.loading='lazy';
        img.decoding='async';
        media.appendChild(img);
      }

      var body=document.createElement('span');
      body.className='ga-related-v20-body';
      var title=document.createElement('span');
      title.className='ga-related-v20-title';
      title.textContent=it.title;
      var more=document.createElement('span');
      more.className='ga-related-v20-more';
      more.textContent='Ler artigo';
      body.appendChild(title);
      body.appendChild(more);

      a.appendChild(media);
      a.appendChild(body);
      grid.appendChild(a);
    }

    section.appendChild(grid);
    anchor.parentNode.insertBefore(section,anchor.nextSibling);
  }

  function build(){
    var labs=labels();
    var calls=[];
    for(var i=0;i<labs.length;i++){
      calls.push(fetchFeed('/feeds/posts/default/-/'+encodeURIComponent(labs[i])+'?alt=json&max-results=8'));
    }
    calls.push(fetchFeed('/feeds/posts/default?alt=json&max-results=12'));
    Promise.all(calls).then(function(groups){
      var merged=[];
      for(var i=0;i<groups.length;i++) merged=merged.concat(groups[i]);
      render(merged);
    });
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',build,{once:true});
  else build();
  setTimeout(build,800);
})();
//]]>
</script>
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p=argparse.ArgumentParser(description='V20 MODELO FINAL: adiciona Artigos relacionados nas páginas de post.')
    p.add_argument('--theme-path', required=True)
    args=p.parse_args()

    path=Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower()!='theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text=path.read_text(encoding='utf-8')
    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
          'status':'THEME_REVISION_20_ALREADY_BUILT','path':str(path),
          'size_bytes':path.stat().st_size,'sha256':sha256(path),
          'xml_valid':True,'public_marker':MARKER_NEW
        },ensure_ascii=False,indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V19 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

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
      'status':'THEME_REVISION_20_MODELO_FINAL_BUILT',
      'path':str(path),'size_bytes':path.stat().st_size,'sha256':sha256(path),'xml_valid':True,
      'public_marker':MARKER_NEW,
      'theme_status':'TEMA MODELO - aguardando validacao visual final',
      'scope':'post-related-articles-only',
      'related_articles_count':3,
      'related_priority':'labels-then-recent',
      'current_post_excluded':True,
      'home_changed':False,
      'static_pages_changed':False,
      'header_changed':False,
      'footer_changed':False
    },ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
