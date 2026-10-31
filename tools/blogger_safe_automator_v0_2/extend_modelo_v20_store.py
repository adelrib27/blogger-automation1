#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_MARKER = "emporio-revisao-visual-20-modelo-final"
STORE_MARKER = "BLOGGER_MODELO_V20_STORE_EXTENSION"

CSS = r"""
<style type='text/css'>
/* BLOGGER_MODELO_V20_STORE_EXTENSION */
:root{
  --ga-store-orange:#F59E0B;
  --ga-store-green:#5C8F16;
  --ga-store-green-2:#76AD24;
  --ga-store-ink:#172033;
  --ga-store-muted:#64748B;
  --ga-store-line:#E5E7EB;
}

/* LOJA no menu global: destaque próprio e posição logo após Início. */
.centered-top-container .PageList li.ga-store-nav-v20 > a{
  background:linear-gradient(135deg,var(--ga-brand-primary,#0F8A5F),var(--ga-store-orange))!important;
  border-radius:8px!important;
  box-shadow:0 4px 12px rgba(15,23,42,.10)!important;
  color:#fff!important;
  font-weight:900!important;
  padding-left:12px!important;
  padding-right:12px!important;
}
.centered-top-container .PageList li.ga-store-nav-v20 > a:hover{
  filter:brightness(.94)!important;
  color:#fff!important;
}

/* A página LOJA é a única página estática que usa largura de vitrine e sem sidebar. */
@media screen and (min-width:981px){
  body.ga-static-page:has(.ga-store-v20) .centered-bottom,
  body.ga-static-page:has(.conecta-store) .centered-bottom{
    display:grid!important;
    gap:0!important;
    grid-template-columns:minmax(0,1fr)!important;
    left:50%!important;
    margin:0!important;
    max-width:1280px!important;
    position:relative!important;
    transform:translateX(-50%)!important;
    width:min(1280px,calc(100vw - 48px))!important;
  }

  body.ga-static-page:has(.ga-store-v20) .main-container,
  body.ga-static-page:has(.conecta-store) .main-container{
    grid-column:1!important;
    margin:0!important;
    max-width:none!important;
    min-width:0!important;
    width:100%!important;
  }

  body.ga-static-page:has(.ga-store-v20) .main-container .main,
  body.ga-static-page:has(.ga-store-v20) .main-container .Blog,
  body.ga-static-page:has(.ga-store-v20) .main-container .widget.Blog,
  body.ga-static-page:has(.ga-store-v20) .main-container .post-outer-container,
  body.ga-static-page:has(.ga-store-v20) .main-container .post-outer,
  body.ga-static-page:has(.ga-store-v20) .main-container .post,
  body.ga-static-page:has(.conecta-store) .main-container .main,
  body.ga-static-page:has(.conecta-store) .main-container .Blog,
  body.ga-static-page:has(.conecta-store) .main-container .widget.Blog,
  body.ga-static-page:has(.conecta-store) .main-container .post-outer-container,
  body.ga-static-page:has(.conecta-store) .main-container .post-outer,
  body.ga-static-page:has(.conecta-store) .main-container .post{
    box-sizing:border-box!important;
    max-width:none!important;
    min-width:0!important;
    width:100%!important;
  }

  body.ga-static-page:has(.ga-store-v20) .sidebar-container,
  body.ga-static-page:has(.conecta-store) .sidebar-container{
    display:none!important;
  }
}

/* Visual aprovado da vitrine. Compatível com o piloto Conecta e com o scaffold genérico V20. */
.ga-store-v20,.conecta-store{
  color:var(--ga-store-ink);
  font-family:Arial,Helvetica,sans-serif;
}
.ga-store-v20 *,.conecta-store *{box-sizing:border-box}
.ga-store-v20 .ca-hero,.conecta-store .ca-hero{
  background:linear-gradient(135deg,#F6FAEF 0%,#FFF 55%,#FFF7E8 100%);
  border:1px solid #E6EDDC;
  border-radius:22px;
  margin:0 0 26px;
  overflow:hidden;
  padding:34px 28px;
  position:relative;
}
.ga-store-v20 .ca-hero:after,.conecta-store .ca-hero:after{
  background:rgba(118,173,36,.12);
  border-radius:50%;
  content:"";
  height:190px;
  position:absolute;
  right:-70px;
  top:-70px;
  width:190px;
}
.ga-store-v20 .ca-eyebrow,.conecta-store .ca-eyebrow{
  align-items:center;
  background:#FFF;
  border:1px solid #DFE8D2;
  border-radius:999px;
  color:#4F7C13;
  display:inline-flex;
  font-size:12px;
  font-weight:800;
  gap:7px;
  letter-spacing:.04em;
  padding:7px 11px;
  text-transform:uppercase;
}
.ga-store-v20 .ca-hero h1,.conecta-store .ca-hero h1{
  color:var(--ga-store-ink)!important;
  font-size:clamp(28px,4vw,42px)!important;
  line-height:1.08!important;
  margin:14px 0 10px!important;
}
.ga-store-v20 .ca-hero>p,.conecta-store .ca-hero>p{
  color:#4B5563;
  font-size:16px;
  line-height:1.65;
  margin:0 auto 18px;
  max-width:720px;
}
.ga-store-v20 .ca-stats,.conecta-store .ca-stats{
  display:flex;
  flex-wrap:wrap;
  gap:9px;
  justify-content:center;
  margin:18px 0;
}
.ga-store-v20 .ca-stat,.conecta-store .ca-stat{
  background:#FFF;
  border:1px solid #E2E8F0;
  border-radius:12px;
  box-shadow:0 4px 14px rgba(15,23,42,.04);
  color:#334155;
  font-size:13px;
  font-weight:700;
  padding:9px 12px;
}
.ga-store-v20 .ca-note,.conecta-store .ca-note{
  background:rgba(255,255,255,.82);
  border:1px solid var(--ga-store-line);
  border-radius:12px;
  color:var(--ga-store-muted);
  display:block;
  font-size:12px;
  line-height:1.55;
  margin:16px auto 0;
  max-width:760px;
  padding:12px 14px;
}
.ga-store-v20 .ca-category,.conecta-store .ca-category{margin:26px 0 34px}
.ga-store-v20 .ca-cathead,.conecta-store .ca-cathead{
  align-items:center;
  border-bottom:2px solid #EDF2E7;
  display:flex;
  gap:12px;
  justify-content:space-between;
  margin:0 0 13px;
  padding:0 2px 10px;
}
.ga-store-v20 .ca-cathead h2,.ga-store-v20>h2,
.conecta-store .ca-cathead h2,.conecta-store>h2{
  color:#1F2937!important;
  font-size:23px!important;
  line-height:1.2!important;
  margin:0!important;
}
.ga-store-v20 .ca-cathead h2:before,.ga-store-v20>h2:before,
.conecta-store .ca-cathead h2:before,.conecta-store>h2:before{
  background:linear-gradient(var(--ga-store-green-2),var(--ga-store-orange));
  border-radius:9px;
  content:"";
  display:inline-block;
  height:22px;
  margin-right:9px;
  vertical-align:-3px;
  width:5px;
}
.ga-store-v20 .ca-catcount,.conecta-store .ca-catcount{
  background:#F1F7E9;
  border-radius:999px;
  color:var(--ga-store-green);
  font-size:12px;
  font-weight:800;
  padding:6px 9px;
}
.ga-store-v20 .ca-grid,.conecta-store .ca-grid{
  display:grid!important;
  gap:16px!important;
  grid-template-columns:repeat(4,minmax(0,1fr))!important;
  margin:0 0 32px!important;
}
.ga-store-v20 .ca-card,.conecta-store .ca-card{
  background:#FFF!important;
  border:1px solid var(--ga-store-line)!important;
  border-radius:18px!important;
  box-shadow:0 4px 16px rgba(15,23,42,.06)!important;
  display:flex!important;
  flex-direction:column!important;
  min-width:0!important;
  padding:11px!important;
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease!important;
}
.ga-store-v20 .ca-card:hover,.conecta-store .ca-card:hover{
  border-color:#CDDDBA!important;
  box-shadow:0 12px 28px rgba(15,23,42,.11)!important;
  transform:translateY(-3px);
}
.ga-store-v20 .ca-card img,.conecta-store .ca-card img{
  aspect-ratio:1/1!important;
  background:#F8FAFC!important;
  border-radius:13px!important;
  object-fit:cover!important;
  width:100%!important;
}
.ga-store-v20 .ca-card h3,.conecta-store .ca-card h3{
  color:var(--ga-store-ink)!important;
  display:-webkit-box;
  font-family:Arial,Helvetica,sans-serif!important;
  font-size:15px!important;
  -webkit-box-orient:vertical;
  -webkit-line-clamp:3;
  line-height:1.35!important;
  margin:11px 2px 7px!important;
  min-height:61px;
  overflow:hidden;
}
.ga-store-v20 .ca-card p,.conecta-store .ca-card p{
  color:var(--ga-store-muted)!important;
  font-family:Arial,Helvetica,sans-serif!important;
  font-size:12.5px!important;
  line-height:1.4!important;
  margin:3px 2px!important;
}
.ga-store-v20 .ca-card p strong,.conecta-store .ca-card p strong{
  color:#111827!important;
  display:block;
  font-size:16px!important;
  line-height:1.25!important;
  margin-top:3px;
}
.ga-store-v20 .ca-card a,.conecta-store .ca-card a{
  background:linear-gradient(135deg,var(--ga-brand-primary,var(--ga-store-green)),var(--ga-store-green-2))!important;
  border-radius:11px!important;
  box-shadow:0 5px 14px rgba(92,143,22,.20)!important;
  color:#FFF!important;
  display:block!important;
  font-size:13px!important;
  font-weight:800!important;
  margin-top:auto!important;
  padding:11px 10px!important;
  text-align:center!important;
  text-decoration:none!important;
}
.ga-store-v20 .ca-card a:hover,.conecta-store .ca-card a:hover{filter:brightness(.96)}
.ga-store-v20 .ca-foot,.conecta-store .ca-foot{
  background:#F8FAFC;
  border:1px solid var(--ga-store-line);
  border-radius:14px;
  color:var(--ga-store-muted);
  font-size:12px;
  line-height:1.6;
  margin:4px 0 0;
  padding:14px 16px;
  text-align:center;
}

@media screen and (max-width:980px){
  .ga-store-v20 .ca-grid,.conecta-store .ca-grid{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
  .ga-store-v20 .ca-hero,.conecta-store .ca-hero{padding:26px 18px}
  .ga-store-v20 .ca-card h3,.conecta-store .ca-card h3{min-height:auto}
}

@media screen and (max-width:480px){
  .ga-store-v20 .ca-grid,.conecta-store .ca-grid{
    gap:8px!important;
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
  .ga-store-v20 .ca-category,.conecta-store .ca-category{margin:20px 0 26px}
  .ga-store-v20 .ca-card,.conecta-store .ca-card{
    border-radius:12px!important;
    padding:7px!important;
  }
  .ga-store-v20 .ca-card img,.conecta-store .ca-card img{border-radius:9px!important}
  .ga-store-v20 .ca-card h3,.conecta-store .ca-card h3{
    font-size:12px!important;
    -webkit-line-clamp:3;
    line-height:1.25!important;
    margin:7px 1px 5px!important;
    min-height:45px;
  }
  .ga-store-v20 .ca-card p,.conecta-store .ca-card p{
    font-size:10.5px!important;
    line-height:1.3!important;
    margin:2px 1px!important;
  }
  .ga-store-v20 .ca-card p strong,.conecta-store .ca-card p strong{
    font-size:13px!important;
    line-height:1.2!important;
  }
  .ga-store-v20 .ca-card a,.conecta-store .ca-card a{
    border-radius:8px!important;
    font-size:11px!important;
    line-height:1.2!important;
    padding:9px 5px!important;
  }
  .ga-store-v20 .ca-cathead,.conecta-store .ca-cathead{
    gap:6px;
    margin-bottom:9px;
    padding-bottom:8px;
  }
  .ga-store-v20 .ca-cathead h2,.ga-store-v20>h2,
  .conecta-store .ca-cathead h2,.conecta-store>h2{
    font-size:18px!important;
  }
  .ga-store-v20 .ca-catcount,.conecta-store .ca-catcount{
    font-size:10px;
    padding:5px 7px;
  }
  .ga-store-v20 .ca-stats,.conecta-store .ca-stats{
    gap:6px;
    justify-content:flex-start;
  }
  .ga-store-v20 .ca-stat,.conecta-store .ca-stat{
    font-size:11px;
    padding:7px 8px;
  }
  .ga-store-v20 .ca-hero,.conecta-store .ca-hero{
    border-radius:16px;
    padding:22px 14px;
    text-align:left!important;
  }
  .ga-store-v20 .ca-hero h1,.conecta-store .ca-hero h1{font-size:26px!important}
  .ga-store-v20 .ca-hero>p,.conecta-store .ca-hero>p{
    font-size:14px;
    margin-left:0;
  }
  .ga-store-v20 .ca-note,.conecta-store .ca-note{
    font-size:11px;
    padding:10px;
    text-align:left;
  }
  .ga-store-v20 .ca-foot,.conecta-store .ca-foot{
    font-size:11px;
    padding:11px;
  }
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

  function enhanceOne(pageList){
    if(!pageList) return;
    var list=pageList.querySelector('ul');
    if(!list) return;

    var links=pageList.querySelectorAll('a[href]');
    var storeLi=null;
    var homeLi=null;

    for(var i=0;i<links.length;i++){
      var a=links[i];
      var p=pathOf(a.getAttribute('href')||a.href);
      var text=(a.textContent||'').replace(/\s+/g,' ').trim().toLowerCase();
      var li=a.closest ? a.closest('li') : a.parentNode;
      if(p===STORE_PATH && li) storeLi=li;
      if((p==='/' || text==='início' || text==='inicio') && li && !homeLi) homeLi=li;
    }

    if(!storeLi){
      storeLi=document.createElement('li');
      var link=document.createElement('a');
      link.href=STORE_PATH;
      link.textContent='LOJA';
      link.setAttribute('aria-label','Abrir Loja');
      storeLi.appendChild(link);
    }

    storeLi.classList.add('ga-store-nav-v20');

    if(pathOf(location.href)===STORE_PATH){
      storeLi.classList.add('selected');
    }

    if(homeLi && homeLi.parentNode===list){
      if(homeLi.nextSibling!==storeLi){
        list.insertBefore(storeLi,homeLi.nextSibling);
      }
    }else if(storeLi.parentNode!==list){
      list.insertBefore(storeLi,list.firstChild);
    }
  }

  function enhance(){
    var pageLists=document.querySelectorAll('.centered-top-container .PageList');
    for(var i=0;i<pageLists.length;i++) enhanceOne(pageLists[i]);
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',enhance,{once:true});
  }else{
    enhance();
  }
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
        description="Aplica ao BLOGGER_MODELO_V20 a extensão validada da LOJA (menu + vitrine 4/2/2)."
    )
    p.add_argument("--theme-path", required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != "theme.xml":
        raise SystemExit("theme.xml não encontrado no caminho informado.")

    text = path.read_text(encoding="utf-8")
    if BASE_MARKER not in text:
        raise SystemExit(f"Tema não pertence ao V20 validado: marcador ausente {BASE_MARKER}")

    if STORE_MARKER in text:
        ET.parse(path)
        print(json.dumps({
            "status": "BLOGGER_MODELO_V20_STORE_EXTENSION_ALREADY_APPLIED",
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "xml_valid": True,
            "base_marker": BASE_MARKER,
            "store_marker": STORE_MARKER,
            "store_menu": "/p/loja.html",
            "desktop_columns": 4,
            "tablet_columns": 2,
            "mobile_columns": 2,
            "store_max_width": 1280,
            "store_sidebar_hidden_only": True,
        }, ensure_ascii=False, indent=2))
        return 0

    if "</head>" not in text:
        raise SystemExit("Elemento </head> não encontrado.")
    if "</body>" not in text:
        raise SystemExit("Elemento </body> não encontrado.")

    text = text.replace("</head>", CSS + "\n</head>", 1)
    text = text.replace("</body>", JS + "\n</body>", 1)

    path.write_text(text, encoding="utf-8")
    ET.parse(path)

    if text.count(STORE_MARKER) != 1:
        raise SystemExit("Extensão LOJA não foi inserida exatamente uma vez.")

    print(json.dumps({
        "status": "BLOGGER_MODELO_V20_STORE_EXTENSION_APPLIED",
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "xml_valid": True,
        "base_marker": BASE_MARKER,
        "store_marker": STORE_MARKER,
        "store_menu": "/p/loja.html",
        "store_menu_position": "after-home",
        "store_menu_highlighted": True,
        "store_scope": "loja-only",
        "store_max_width": 1280,
        "store_sidebar_hidden_only": True,
        "desktop_columns": 4,
        "tablet_columns": 2,
        "mobile_columns": 2,
        "other_static_pages_changed": False,
        "post_pages_changed": False,
        "home_changed": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
