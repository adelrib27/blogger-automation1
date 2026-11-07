#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-02-safe2"
MARKER_NEW = "emporio-revisao-visual-03-portal"

NAV = f"""
<div aria-label='Navegação principal' class='ga-static-nav ga-portal-nav' data-theme-build='{MARKER_NEW}'>
  <a class='ga-nav-home' href='https://guia-de-achados-e-ofertas.blogspot.com/'>Início</a>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/p/sobre.html'>Sobre</a>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/p/aviso-de-afiliados.html'>Afiliados</a>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/p/contato.html'>Contato</a>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/p/politica-de-privacidade.html'>Privacidade</a>
  <a href='https://guia-de-achados-e-ofertas.blogspot.com/p/termos-de-uso.html'>Termos</a>
</div>
"""

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — PORTAL HEADER V3
   Estrutura inspirada em portais editoriais/comerciais, mantendo
   o Emporio e os widgets nativos do Blogger.
   ============================================================ */
:root{
  --ga-ink:#172033;
  --ga-text:#425066;
  --ga-muted:#728096;
  --ga-line:#dce4ee;
  --ga-blue:#175cd3;
  --ga-blue-dark:#0f46a3;
  --ga-blue-soft:#eef5ff;
  --ga-gold:#f4a100;
  --ga-card:#ffffff;
  --ga-bg:#f4f7fb;
  --ga-shadow:0 16px 42px rgba(23,32,51,.10);
}

body{background:var(--ga-bg)!important;color:var(--ga-text)}
.page_body .centered{max-width:1240px!important;padding-top:24px!important}

/* Cabeçalho principal: marca à esquerda, páginas à direita */
.centered-top-container{
  background:var(--ga-card)!important;
  border:1px solid var(--ga-line)!important;
  border-top:4px solid var(--ga-blue)!important;
  border-radius:20px!important;
  box-shadow:var(--ga-shadow)!important;
  overflow:hidden!important;
}
.blog-name{
  display:grid!important;
  grid-template-columns:minmax(300px,.9fr) minmax(480px,1.1fr)!important;
  align-items:center!important;
  column-gap:34px!important;
  margin:0!important;
  padding:24px 28px 14px!important;
}
.blog-name .Header{grid-column:1;min-width:0}
.Header h1{
  color:var(--ga-ink)!important;
  font-size:34px!important;
  font-weight:900!important;
  letter-spacing:-.8px!important;
  line-height:1.04!important;
  margin:0!important;
}
.Header h1:after{
  background:var(--ga-gold);
  border-radius:50%;
  content:"";
  display:inline-block;
  height:9px;
  margin-left:8px;
  vertical-align:.12em;
  width:9px;
}
.Header p{
  color:var(--ga-muted)!important;
  font-size:13.5px!important;
  font-style:normal!important;
  line-height:1.55!important;
  margin:8px 0 0!important;
  max-width:560px;
}

/* O nav nativo permanece no XML, mas a lista antiga fica escondida. */
.top-nav{display:contents!important}
.top-nav #page_list_top{display:none!important}
.ga-static-nav.ga-portal-nav{
  align-items:center;
  border:0!important;
  display:flex!important;
  flex-wrap:wrap!important;
  gap:6px!important;
  grid-column:2;
  justify-content:flex-end;
  margin:0!important;
  padding:0!important;
}
.ga-static-nav.ga-portal-nav a{
  border:1px solid transparent;
  border-radius:10px;
  color:#334155!important;
  font-size:13.5px!important;
  font-weight:800!important;
  letter-spacing:0!important;
  padding:9px 11px!important;
  text-decoration:none!important;
  transition:background .16s ease,border-color .16s ease,color .16s ease,transform .16s ease;
}
.ga-static-nav.ga-portal-nav a:hover{
  background:var(--ga-blue-soft)!important;
  border-color:#d8e8ff!important;
  color:var(--ga-blue-dark)!important;
  transform:translateY(-1px);
}
.ga-static-nav.ga-portal-nav .ga-nav-home{
  background:var(--ga-blue)!important;
  border-color:var(--ga-blue)!important;
  color:#fff!important;
}

/* Busca vira uma faixa larga logo abaixo da marca/menu. */
.centered-top-container .search{
  float:none!important;
  left:auto!important;
  margin:0 28px 18px!important;
  max-width:none!important;
  position:relative!important;
  right:auto!important;
  top:auto!important;
  width:auto!important;
}
.centered-top-container .search form{
  background:#fff!important;
  border:1px solid #cfd9e6!important;
  border-radius:13px!important;
  box-shadow:0 6px 18px rgba(23,32,51,.06)!important;
  margin:0!important;
  min-height:46px;
}
.centered-top-container .search input[type=text],
.centered-top-container .search input[type=search],
.centered-top-container .search .search-input{
  color:var(--ga-ink)!important;
  font-size:15px!important;
}
.search-expand-icon,.hamburger-menu .svg-icon-24{fill:var(--ga-blue)!important}

/* Home: card editorial/comercial mais forte. */
body:not(.item-view) #page_body .FeaturedPost{
  background:#fff!important;
  border:1px solid var(--ga-line)!important;
  border-radius:22px!important;
  box-shadow:0 18px 46px rgba(23,32,51,.11)!important;
  margin-bottom:28px!important;
  overflow:hidden!important;
  padding:0 0 24px!important;
  position:relative;
}
body:not(.item-view) #page_body .FeaturedPost:before{
  background:var(--ga-blue)!important;
  border-radius:999px;
  color:#fff;
  content:"DESTAQUE";
  font-size:11px;
  font-weight:900;
  left:18px;
  letter-spacing:.08em;
  padding:7px 10px;
  position:absolute;
  top:18px;
  z-index:3;
}
body:not(.item-view) .FeaturedPost .snippet-thumbnail{
  background:#eef2f7!important;
  border-radius:0!important;
  margin:0!important;
  overflow:hidden!important;
}
body:not(.item-view) .FeaturedPost .snippet-thumbnail img{
  display:block!important;
  height:clamp(300px,31vw,440px)!important;
  object-fit:cover!important;
  width:100%!important;
}
body:not(.item-view) .FeaturedPost h3{
  margin:22px 26px 7px!important;
}
body:not(.item-view) .FeaturedPost h3 a{
  color:var(--ga-ink)!important;
  font-size:26px!important;
  font-weight:900!important;
  letter-spacing:-.45px!important;
  line-height:1.22!important;
}
body:not(.item-view) .FeaturedPost .post-header,
body:not(.item-view) .FeaturedPost .post-footer,
body:not(.item-view) .FeaturedPost .post-summary{
  margin-left:26px!important;
  margin-right:26px!important;
}
body:not(.item-view) .FeaturedPost .post-header,
body:not(.item-view) .FeaturedPost .byline{color:var(--ga-muted)!important}

/* Cards das próximas postagens já preparados para quando o catálogo crescer. */
body:not(.item-view) .Blog .blog-posts .post-outer-container{
  border:1px solid var(--ga-line)!important;
  border-radius:18px!important;
  box-shadow:0 10px 30px rgba(23,32,51,.07)!important;
}
body:not(.item-view) .post-title a:hover{color:var(--ga-blue)!important}

/* Sidebar/arquivo deixa de parecer um bloco solto pesado. */
.sidebar-container .widget.BlogArchive,
.centered-bottom .widget.BlogArchive{
  background:#fff!important;
  border:1px solid var(--ga-line)!important;
  border-radius:14px!important;
  box-shadow:none!important;
}

/* Artigo: preserva os CTAs da V2 e melhora integração com a nova identidade. */
.item-view .post-title,.item-view .post-title a{color:var(--ga-ink)!important}
.item-view .post-body h2{color:var(--ga-ink)!important}
.item-view .post-body a[rel~="sponsored"]{
  background:var(--ga-blue)!important;
  border-color:var(--ga-blue)!important;
  box-shadow:0 9px 22px rgba(23,92,211,.18)!important;
}
.item-view .post-body a[rel~="sponsored"]:hover{background:var(--ga-blue-dark)!important}

@media screen and (max-width:1050px){
  .blog-name{
    grid-template-columns:1fr!important;
    row-gap:14px!important;
  }
  .blog-name .Header,.ga-static-nav.ga-portal-nav{grid-column:1}
  .ga-static-nav.ga-portal-nav{justify-content:flex-start!important}
}

@media screen and (max-width:800px){
  .page_body .centered{padding-left:0!important;padding-right:0!important}
  .centered-top-container{border-left:0!important;border-radius:0!important;border-right:0!important}
  .blog-name{padding:20px 16px 12px!important}
  .Header h1{font-size:30px!important}
  .Header p{font-size:13px!important}
  .ga-static-nav.ga-portal-nav{
    flex-wrap:nowrap!important;
    justify-content:flex-start!important;
    margin-left:-4px!important;
    margin-right:-4px!important;
    overflow-x:auto!important;
    padding:3px 4px 8px!important;
  }
  .ga-static-nav.ga-portal-nav a{white-space:nowrap}
  .centered-top-container .search{margin:0 16px 16px!important}
  body:not(.item-view) #page_body .FeaturedPost{border-left:0!important;border-radius:0!important;border-right:0!important}
  body:not(.item-view) .FeaturedPost .snippet-thumbnail img{height:280px!important}
  body:not(.item-view) .FeaturedPost h3{margin:19px 18px 6px!important}
  body:not(.item-view) .FeaturedPost h3 a{font-size:22px!important}
  body:not(.item-view) .FeaturedPost .post-header,
  body:not(.item-view) .FeaturedPost .post-footer,
  body:not(.item-view) .FeaturedPost .post-summary{margin-left:18px!important;margin-right:18px!important}
}
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p = argparse.ArgumentParser(description="Gera a revisão visual 03 Portal sobre a V2 validada.")
    p.add_argument("--theme-path", required=True)
    args = p.parse_args()

    path = Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower() != "theme.xml":
        raise SystemExit("theme.xml não encontrado no caminho informado.")

    text = path.read_text(encoding="utf-8")
    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
            "status":"THEME_REVISION_03_ALREADY_BUILT",
            "path":str(path),
            "size_bytes":path.stat().st_size,
            "sha256":sha256(path),
            "xml_valid":True,
            "public_marker":MARKER_NEW,
        }, ensure_ascii=False, indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f"A V2 validada não foi localizada. Marcador ausente: {MARKER_OLD}")

    # Atualiza o marcador em todos os pontos onde a V2 o publicou.
    text = text.replace(MARKER_OLD, MARKER_NEW)

    # Substitui somente a navegação estática adicionada pela V2.
    nav_re = re.compile(
        r"<div aria-label='Navegação principal' class='ga-static-nav(?: ga-portal-nav)?' data-theme-build='[^']+'>.*?</div>",
        re.S,
    )
    text, nav_count = nav_re.subn(NAV.strip(), text, count=1)
    if nav_count != 1:
        raise SystemExit("Menu estático da V2 não foi localizado de forma única.")

    # A V3 é uma camada de override; não remove CSS validado da V2.
    mobile_marker = "/* Mobile */"
    if mobile_marker not in text:
        raise SystemExit("Marcador CSS Mobile não encontrado.")
    text = text.replace(mobile_marker, CSS + "\n" + mobile_marker, 1)

    path.write_text(text, encoding="utf-8")
    ET.parse(path)

    print(json.dumps({
        "status":"THEME_REVISION_03_PORTAL_BUILT",
        "path":str(path),
        "size_bytes":path.stat().st_size,
        "sha256":sha256(path),
        "xml_valid":True,
        "public_marker":MARKER_NEW,
        "header_layout":"brand-left-pages-right-search-below",
        "widget_state_modified":False,
        "native_theme":"Emporio preserved",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
