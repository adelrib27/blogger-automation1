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
nav a.ga-store-visible-nav-v20{background:linear-gradient(135deg,var(--ga-brand-primary,#0F8A5F),#F59E0B)!important;border-radius:8px!important;box-shadow:0 4px 12px rgba(15,23,42,.10)!important;color:#fff!important;font-weight:900!important;padding:7px 12px!important;text-decoration:none!important}
nav a.ga-store-visible-nav-v20:hover,nav a.ga-store-visible-nav-v20.ga-store-current-v20{color:#fff!important;filter:brightness(.94)!important}
.ga-home-footer a.ga-store-footer-nav-v20,.ga-post-footer a.ga-store-footer-nav-v20,.ga-static-footer a.ga-store-footer-nav-v20{font-weight:900!important}
.ga-static-page-feed-host-v20{width:100%;min-width:0}.ga-static-page-feed-runtime{margin:0 auto;max-width:100%}.ga-static-page-feed-runtime .post-title{color:var(--ga-ink,#172033);font-family:Arial,Helvetica,sans-serif;font-size:clamp(28px,4vw,38px);line-height:1.15;margin:0 0 22px}.ga-static-page-feed-runtime .post-body{min-width:0}
</style>
""".strip()

JS = r"""
<script type='text/javascript'>
//<![CDATA[
(function(){
  var STORE_PATH='/p/loja.html',PRIMARY_NAV_SELECTOR='nav.ga-home-v6-nav';
  var FALLBACK_DEDUPE_MARKER='BLOGGER_MODELO_V20_STORE_FALLBACK_DEDUPE';
  var FOOTER_DEDUPE_MARKER='BLOGGER_MODELO_V20_STORE_FOOTER_NAV';
  var STATIC_PAGE_FEED_MARKER='BLOGGER_MODELO_V20_STATIC_PAGE_FEED_RUNTIME';
  var PAGE_FEED='/feeds/pages/default?alt=json&max-results=25';
  var HOST_ID='ga-static-feed-host-v20';
  var feedState={loading:false,loaded:false,data:null};
  var INSTITUTIONAL={'/p/sobre.html':1,'/p/aviso-de-afiliados.html':1,'/p/contato.html':1,'/p/politica-de-privacidade.html':1,'/p/termos-de-uso.html':1};

  function pathOf(href){try{var p=new URL(href,location.href).pathname.replace(/\/+$/,'');return p||'/';}catch(e){return '';}}
  function isHeaderNav(nav){
    if(!nav||!nav.querySelectorAll||(nav.closest&&nav.closest('footer,.ga-home-footer,.ga-post-footer,.ga-static-footer'))||(nav.classList&&nav.classList.contains('top-nav'))) return false;
    var links=nav.querySelectorAll('a[href]'),home=false,count=0;
    for(var i=0;i<links.length;i++){var p=pathOf(links[i].getAttribute('href')||links[i].href),t=(links[i].textContent||'').replace(/\s+/g,' ').trim().toLowerCase();if(p==='/'||t==='início'||t==='inicio') home=true;if(INSTITUTIONAL[p]) count++;}
    return home&&count>=2;
  }
  function enhanceVisibleNav(nav){
    if(!isHeaderNav(nav)) return;var links=nav.querySelectorAll('a[href]'),home=null,store=null,dups=[];
    for(var i=0;i<links.length;i++){var a=links[i],p=pathOf(a.getAttribute('href')||a.href),t=(a.textContent||'').replace(/\s+/g,' ').trim().toLowerCase();if(!home&&(p==='/'||t==='início'||t==='inicio')) home=a;if(p===STORE_PATH){if(!store) store=a;else dups.push(a);}}
    for(var d=0;d<dups.length;d++) if(dups[d].parentNode) dups[d].parentNode.removeChild(dups[d]);if(!home) return;
    if(!store){store=document.createElement('a');store.href=STORE_PATH;store.textContent='LOJA';store.setAttribute('aria-label','Abrir Loja');}
    store.classList.add('ga-store-visible-nav-v20');store.setAttribute('data-ga-store-header-nav','BLOGGER_MODELO_V20_STORE_HEADER_NAV');
    if(pathOf(location.href)===STORE_PATH) store.classList.add('ga-store-current-v20');else store.classList.remove('ga-store-current-v20');
    var parent=home.parentNode;if(parent===nav){if(home.nextElementSibling!==store) nav.insertBefore(store,home.nextSibling);}else if(parent&&parent.tagName&&parent.tagName.toLowerCase()==='li'&&parent.parentNode){var list=parent.parentNode,li=store.closest?store.closest('li'):null;if(!li){li=document.createElement('li');li.className='ga-store-header-li-v20';li.appendChild(store);}if(parent.nextElementSibling!==li) list.insertBefore(li,parent.nextSibling);}nav.setAttribute('data-ga-store-header-enhanced','1');
  }
  function dedupeFallbackPageList(pageList){
    if(!pageList) return;var list=pageList.querySelector('ul');if(!list) return;var links=list.querySelectorAll('a[href]'),home=null,store=null,dups=[];
    for(var i=0;i<links.length;i++){var a=links[i],p=pathOf(a.getAttribute('href')||a.href),t=(a.textContent||'').replace(/\s+/g,' ').trim().toLowerCase(),li=a.closest?a.closest('li'):a.parentNode;if(!li) continue;if(!home&&(p==='/'||t==='início'||t==='inicio')) home=li;if(p===STORE_PATH){if(!store) store=li;else dups.push(li);}}
    for(var d=0;d<dups.length;d++) if(dups[d].parentNode===list) list.removeChild(dups[d]);if(store){store.classList.add('ga-store-nav-v20');store.setAttribute('data-ga-store-dedupe',FALLBACK_DEDUPE_MARKER);if(home&&home.parentNode===list&&home.nextElementSibling!==store) list.insertBefore(store,home.nextSibling);}
  }
  function enhanceFooterGroup(group){
    if(!group||!group.querySelectorAll) return;var links=group.querySelectorAll('a[href]'),home=null,store=null,dups=[];
    for(var i=0;i<links.length;i++){var a=links[i],p=pathOf(a.getAttribute('href')||a.href),t=(a.textContent||'').replace(/\s+/g,' ').trim().toLowerCase();if(!home&&(p==='/'||t==='início'||t==='inicio')) home=a;if(p===STORE_PATH){if(!store) store=a;else dups.push(a);}}
    if(!home) return;for(var d=0;d<dups.length;d++) if(dups[d].parentNode) dups[d].parentNode.removeChild(dups[d]);if(!store){store=document.createElement('a');store.href=STORE_PATH;store.textContent='LOJA';store.setAttribute('aria-label','Abrir Loja');}
    store.classList.add('ga-store-footer-nav-v20');store.setAttribute('data-ga-store-footer-nav',FOOTER_DEDUPE_MARKER);if(home.nextElementSibling!==store) group.insertBefore(store,home.nextSibling);group.setAttribute('data-ga-store-footer-enhanced','1');
  }
  function entryPath(entry){var links=(entry&&entry.link)||[];for(var i=0;i<links.length;i++) if(links[i]&&links[i].rel==='alternate'&&links[i].href) return pathOf(links[i].href);return '';}
  function syncBrandFromFeed(feed){
    var title=feed&&feed.title&&feed.title.$t?String(feed.title.$t).trim():'';if(!title) return;var nodes=document.querySelectorAll('.ga-home-footer-brand h3,.ga-post-footer-brand h3,.ga-static-footer-brand h3,.ga-home-footer-bottom strong,.ga-post-footer-bottom strong,.ga-static-footer-bottom strong');for(var i=0;i<nodes.length;i++) nodes[i].textContent=title;document.documentElement.setAttribute('data-ga-brand-feed-runtime',STATIC_PAGE_FEED_MARKER);
  }
  function stableHost(target){
    var host=document.getElementById(HOST_ID);if(host) return host;if(!target||!target.parentNode) return null;
    host=document.createElement('div');host.id=HOST_ID;host.className='ga-static-page-feed-host-v20';host.setAttribute('data-ga-static-page-feed-host',STATIC_PAGE_FEED_MARKER);target.parentNode.insertBefore(host,target.nextSibling);return host;
  }
  function hydrateStaticPageFromFeed(feed){
    if(!document.body||!document.body.classList.contains('ga-static-page')) return;var target=document.getElementById('page_body');if(!target) return;
    var current=pathOf(location.href),entries=(feed&&feed.entry)||[],match=null;for(var i=0;i<entries.length;i++) if(entryPath(entries[i])===current){match=entries[i];break;}if(!match||!match.content||!match.content.$t) return;
    var host=stableHost(target);if(!host) return;var title=match.title&&match.title.$t?String(match.title.$t):'',wrapper=document.createElement('div');wrapper.className='widget Blog ga-static-page-feed-runtime';wrapper.setAttribute('data-ga-static-page-feed-runtime',STATIC_PAGE_FEED_MARKER);
    var article=document.createElement('article');article.className='post-outer-container post';if(title){var h1=document.createElement('h1');h1.className='post-title entry-title';h1.textContent=title;article.appendChild(h1);}var body=document.createElement('div');body.className='post-body entry-content';body.innerHTML=String(match.content.$t);article.appendChild(body);wrapper.appendChild(article);
    host.innerHTML='';host.appendChild(wrapper);target.style.display='none';target.setAttribute('data-ga-static-page-feed-runtime','delegated');document.documentElement.setAttribute('data-ga-static-page-feed-source','canonical-host');
  }
  function applyFeed(feed){if(!feed) return;syncBrandFromFeed(feed);hydrateStaticPageFromFeed(feed);}
  function ensureFeedRuntime(){
    if(feedState.loaded){applyFeed(feedState.data);return;}if(feedState.loading||!window.fetch) return;feedState.loading=true;
    fetch(PAGE_FEED,{credentials:'same-origin'}).then(function(r){if(!r.ok) throw new Error('page-feed-'+r.status);return r.json();}).then(function(data){feedState.loading=false;feedState.loaded=true;feedState.data=(data&&data.feed)?data.feed:null;applyFeed(feedState.data);}).catch(function(){feedState.loading=false;document.documentElement.setAttribute('data-ga-static-page-feed-error','1');});
  }
  function enhance(){
    var primary=document.querySelectorAll(PRIMARY_NAV_SELECTOR);for(var p=0;p<primary.length;p++) enhanceVisibleNav(primary[p]);var navs=document.querySelectorAll('nav');for(var i=0;i<navs.length;i++) enhanceVisibleNav(navs[i]);var lists=document.querySelectorAll('.centered-top-container .PageList');for(var j=0;j<lists.length;j++) dedupeFallbackPageList(lists[j]);var foot=document.querySelectorAll('.ga-home-footer-links,.ga-post-footer-links,.ga-static-footer-links');for(var f=0;f<foot.length;f++) enhanceFooterGroup(foot[f]);ensureFeedRuntime();
  }
  var scheduled=false;function scheduleEnhance(){if(scheduled) return;scheduled=true;setTimeout(function(){scheduled=false;enhance();},30);}if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',enhance,{once:true});else enhance();setTimeout(enhance,500);setTimeout(enhance,1500);setTimeout(enhance,3000);if(window.MutationObserver&&document.documentElement) new MutationObserver(scheduleEnhance).observe(document.documentElement,{childList:true,subtree:true});
})();
//]]>
</script>
""".strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description="Garante LOJA nos menus, rodapes e corpo canonico das paginas estaticas do BLOGGER_MODELO_V20.")
    p.add_argument("--theme-path", required=True)
    args = p.parse_args()
    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != "theme.xml": raise SystemExit("theme.xml não encontrado no caminho informado.")
    text = path.read_text(encoding="utf-8")
    if BASE_MARKER not in text: raise SystemExit(f"Tema não pertence ao V20 validado: marcador ausente {BASE_MARKER}")
    if VISIBLE_NAV_MARKER in text:
        ET.parse(path);print(json.dumps({"status":"BLOGGER_MODELO_V20_STORE_VISIBLE_NAV_ALREADY_APPLIED","path":str(path),"sha256":sha256(path),"xml_valid":True,"visible_nav_marker":VISIBLE_NAV_MARKER,"visible_nav_selector":"nav.ga-home-v6-nav","dynamic_header_nav_supported":True,"store_menu":STORE_PATH,"store_menu_position":"after-home","store_menu_highlighted":True,"store_footer_nav_supported":True,"store_footer_position":"after-home","static_page_feed_runtime_supported":True,"footer_brand_feed_sync_supported":True,"stable_static_page_host_supported":True,"fallback_pagelist_deduplicated":True},ensure_ascii=False,indent=2));return 0
    if "</head>" not in text or "</body>" not in text: raise SystemExit("Tema sem </head> ou </body>; nenhuma alteração feita.")
    text=text.replace("</head>",CSS+"\n</head>",1).replace("</body>",JS+"\n</body>",1);path.write_text(text,encoding="utf-8");ET.parse(path)
    if text.count(VISIBLE_NAV_MARKER)!=1: raise SystemExit("Extensão de navegação visível não foi inserida exatamente uma vez.")
    print(json.dumps({"status":"BLOGGER_MODELO_V20_STORE_VISIBLE_NAV_APPLIED","path":str(path),"sha256":sha256(path),"xml_valid":True,"visible_nav_marker":VISIBLE_NAV_MARKER,"visible_nav_selector":"nav.ga-home-v6-nav","dynamic_header_nav_supported":True,"store_menu":STORE_PATH,"store_menu_position":"after-home","store_menu_highlighted":True,"store_footer_nav_supported":True,"store_footer_position":"after-home","static_page_feed_runtime_supported":True,"footer_brand_feed_sync_supported":True,"stable_static_page_host_supported":True,"fallback_pagelist_deduplicated":True,"other_navigation_links_preserved":True},ensure_ascii=False,indent=2));return 0


if __name__ == "__main__": raise SystemExit(main())
