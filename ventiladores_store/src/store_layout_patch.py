#!/usr/bin/env python3
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from criar_rascunho import criar_servico_blogger

BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "4473989735719981382").strip()
POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "1410775502611365606").strip()
START = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_START -->"
END = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_END -->"

BLOCK = f'''{START}
<style id="blogger-liq-layout-wide-css">
.post-body{{overflow:visible!important}}
body.ga-post-page:has(.bls-page) .centered-bottom{{display:grid!important;grid-template-columns:minmax(0,1fr)!important;grid-template-rows:auto!important;gap:0!important;margin-left:auto!important;margin-right:auto!important}}
body.ga-post-page:has(.bls-page) .main-container{{grid-column:1!important;grid-area:1 / 1!important;width:100%!important;max-width:none!important;min-width:0!important;margin:0!important}}
body.ga-post-page:has(.bls-page) .sidebar-container,
body:has(.bls-page) .sidebar-container,
body:has(.bls-page) .sidebar-container-container,
body:has(.bls-page) .main-container aside{{display:none!important}}
body:has(.bls-page) .main-container,
body:has(.bls-page) .main,
body:has(.bls-page) .blog-posts,
body:has(.bls-page) .post-outer-container:has(.bls-page),
body:has(.bls-page) .post-outer:has(.bls-page),
body:has(.bls-page) .post:has(.bls-page),
body:has(.bls-page) .post-body-container:has(.bls-page){{width:100%!important;max-width:none!important}}
body:has(.bls-page) .post-outer-container:has(.bls-page),
body:has(.bls-page) .post-outer:has(.bls-page),
body:has(.bls-page) .post:has(.bls-page),
body:has(.bls-page) .post-body-container:has(.bls-page){{background:transparent!important;border:0!important;box-shadow:none!important;overflow:visible!important;padding-top:0!important;padding-bottom:0!important;margin-top:0!important;margin-bottom:0!important}}
body:has(.bls-page) .post:has(.bls-page) .post-header,
body:has(.bls-page) .post:has(.bls-page) .post-title,
body:has(.bls-page) .post:has(.bls-page) .entry-title{{display:none!important}}
body:has(.bls-page) .post-body:has(.bls-page){{width:100%!important;max-width:none!important;margin:0!important;padding:0!important;overflow:visible!important}}
body:has(.bls-page) .PopularPosts,
body:has(.bls-page) .widget.PopularPosts,
body:has(.bls-page) [id^="PopularPosts"]{{display:none!important}}
.bls-page{{width:min(1440px,calc(100vw - 48px))!important;max-width:none!important;position:relative!important;left:50%!important;transform:translateX(-50%)!important;margin-top:32px!important;margin-bottom:0!important}}
@media(max-width:700px){{body.ga-post-page:has(.bls-page) .centered-bottom{{display:block!important}}.bls-page{{width:calc(100vw - 16px)!important;margin-top:16px!important}}}}
</style>
<script id="blogger-liq-header-loja-link">
document.addEventListener('DOMContentLoaded',function(){{
  const store='https://ventiladores-em-foco.blogspot.com/p/loja.html';
  const about=[...document.querySelectorAll('a[href$="/p/sobre.html"]')].find(a=>a.getBoundingClientRect().top<180);
  if(!about||!about.parentNode)return;
  const same=[...about.parentNode.querySelectorAll('a')].some(a=>/\/p\/loja\.html(?:$|[?#])/.test(a.href));
  if(same)return;
  const link=about.cloneNode(false);link.href=store;link.textContent='Loja';link.removeAttribute('aria-current');about.parentNode.insertBefore(link,about);
}});
</script>
{END}'''

SHELL_REPLACEMENTS = {
    "Achados práticos para casa, tecnologia, beleza e dia a dia": "Ventilação para casa, trabalho e dia a dia",
    "Descubra produtos úteis para facilitar a rotina": "Encontre o ventilador certo para cada ambiente",
    "Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.": "Uma vitrine afiliada com ventiladores selecionados automaticamente na Shopee para diferentes ambientes e necessidades.",
    "Cozinha e tecnologia": "Conforto em diferentes ambientes",
    "Soluções práticas para cozinhar, conectar e organizar melhor": "Modelos de torre e teto para refrescar melhor",
    "A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.": "A seleção prioriza ventiladores completos e coerentes com cada categoria, bloqueando peças, suportes e falsos positivos.",
    "Beleza e praticidade": "Ventilação versátil",
    "Achados reais para cuidados pessoais e rotina": "Parede, circuladores e portáteis para cada uso",
    'href="#bls-cozinha-utilidades">Ver cozinha': 'href="#bls-torre">Ver torre',
    'href="#bls-tecnologia">Ver tecnologia': 'href="#bls-teto">Ver teto',
    'href="#bls-beleza">Ver beleza': 'href="#bls-parede">Ver parede',
    'href="#bls-dia-a-dia">Ver dia a dia': 'href="#bls-circuladores-portateis">Ver portáteis',
    '<a class="bls-cat" href="#bls-casa-organizacao"><b>Casa &amp; Organização</b><small>organização e soluções para o lar</small></a>': '<a class="bls-cat" href="#bls-mesa-coluna"><b>Mesa &amp; Coluna</b><small>para quarto, sala e escritório</small></a>',
    '<a class="bls-cat" href="#bls-cozinha-utilidades"><b>Cozinha &amp; Utilidades</b><small>itens úteis para a cozinha</small></a>': '<a class="bls-cat" href="#bls-torre"><b>Torre</b><small>design vertical e ventilação silenciosa</small></a>',
    '<a class="bls-cat" href="#bls-tecnologia"><b>Tecnologia &amp; Acessórios</b><small>conectividade e eletrônicos úteis</small></a>': '<a class="bls-cat" href="#bls-teto"><b>Teto</b><small>ventilação fixa para ambientes</small></a>',
    '<a class="bls-cat" href="#bls-beleza"><b>Beleza &amp; Cuidados</b><small>cuidados pessoais e beleza</small></a>': '<a class="bls-cat" href="#bls-parede"><b>Parede</b><small>potência para áreas amplas</small></a>',
    '<a class="bls-cat" href="#bls-dia-a-dia"><b>Dia a Dia &amp; Praticidade</b><small>produtos úteis para a rotina</small></a>': '<a class="bls-cat" href="#bls-circuladores-portateis"><b>Circuladores &amp; Portáteis</b><small>mobilidade e circulação de ar</small></a>',
    "Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia": "Ventiladores em foco para diferentes ambientes"
}


def patch_store_layout() -> None:
    if not BLOG_ID or not POST_ID:
        raise RuntimeError("BLOGGER_BLOG_ID/BLOGGER_STORE_POST_ID ausente.")
    blogger = criar_servico_blogger()
    post = blogger.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    raw = str(post.get("content") or "")
    if "BLOGGER_LIQ_STORE_AUTO_START" not in raw or "BLOGGER_LIQ_HERO_AUTO_1_START" not in raw:
        raise RuntimeError("Post Loja sem marcadores esperados; layout preservado.")

    for old, new in SHELL_REPLACEMENTS.items():
        raw = raw.replace(old, new)

    sc, ec = raw.count(START), raw.count(END)
    if sc or ec:
        if sc != 1 or ec != 1:
            raise RuntimeError("Marcadores do layout inconsistentes; post preservado.")
        a, b = raw.find(START), raw.find(END)
        if b <= a:
            raise RuntimeError("Ordem inválida dos marcadores do layout; post preservado.")
        updated = raw[:a] + BLOCK + raw[b + len(END):]
    else:
        updated = BLOCK + "\n" + raw

    current = str(post.get("content") or "")
    if updated != current:
        body = {"title": post.get("title") or "Loja", "content": updated}
        if post.get("labels") is not None:
            body["labels"] = post.get("labels")
        blogger.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()

    verify = str(blogger.posts().get(blogId=BLOG_ID, postId=POST_ID).execute().get("content") or "")
    required = (
        START, END, "BLOGGER_LIQ_STORE_AUTO_START", "BLOGGER_LIQ_HERO_AUTO_1_START",
        "https://ventiladores-em-foco.blogspot.com/p/loja.html", '[id^="PopularPosts"]',
        "grid-template-columns:minmax(0,1fr)!important", 'href="#bls-mesa-coluna"',
        'href="#bls-torre"', 'href="#bls-teto"', 'href="#bls-parede"',
        'href="#bls-circuladores-portateis"', "Ventiladores em foco para diferentes ambientes"
    )
    missing = [x for x in required if x not in verify]
    if missing:
        raise RuntimeError(f"Falha na verificação do layout/shell; ausentes={missing}")
    print("LAYOUT_WIDE_APPLIED")
    print("STORE_TARGET_VENTILADORES_OK")
    print("POPULAR_POSTS_HIDDEN_ON_STORE_OK")
    print("STORE_VIEWPORT_CENTERED_OK")
    print("STORE_SHELL_NICHE_VENTILADORES_OK")


if __name__ == "__main__":
    patch_store_layout()
