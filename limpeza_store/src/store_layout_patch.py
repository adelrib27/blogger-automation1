#!/usr/bin/env python3
from __future__ import annotations
import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'src'))
from criar_rascunho import criar_servico_blogger
BLOG_ID=os.getenv('BLOGGER_BLOG_ID','7757953554206491487').strip(); POST_ID=os.getenv('BLOGGER_STORE_POST_ID','6383277011247909539').strip()
START='<!-- BLOGGER_LIQ_LAYOUT_PATCH_START -->'; END='<!-- BLOGGER_LIQ_LAYOUT_PATCH_END -->'
BLOCK=f'''{START}
<style id="blogger-liq-layout-wide-css">.post-body{{overflow:visible!important}}body.ga-post-page:has(.bls-page) .centered-bottom{{display:grid!important;grid-template-columns:minmax(0,1fr)!important;grid-template-rows:auto!important;gap:0!important;margin-left:auto!important;margin-right:auto!important}}body.ga-post-page:has(.bls-page) .main-container{{grid-column:1!important;grid-area:1 / 1!important;width:100%!important;max-width:none!important;min-width:0!important;margin:0!important}}body.ga-post-page:has(.bls-page) .sidebar-container,body:has(.bls-page) .sidebar-container,body:has(.bls-page) .sidebar-container-container,body:has(.bls-page) .main-container aside{{display:none!important}}body:has(.bls-page) .main-container,body:has(.bls-page) .main,body:has(.bls-page) .blog-posts,body:has(.bls-page) .post-outer-container:has(.bls-page),body:has(.bls-page) .post-outer:has(.bls-page),body:has(.bls-page) .post:has(.bls-page),body:has(.bls-page) .post-body-container:has(.bls-page){{width:100%!important;max-width:none!important}}body:has(.bls-page) .post-outer-container:has(.bls-page),body:has(.bls-page) .post-outer:has(.bls-page),body:has(.bls-page) .post:has(.bls-page),body:has(.bls-page) .post-body-container:has(.bls-page){{background:transparent!important;border:0!important;box-shadow:none!important;overflow:visible!important;padding-top:0!important;padding-bottom:0!important;margin-top:0!important;margin-bottom:0!important}}body:has(.bls-page) .post:has(.bls-page) .post-header,body:has(.bls-page) .post:has(.bls-page) .post-title,body:has(.bls-page) .post:has(.bls-page) .entry-title{{display:none!important}}body:has(.bls-page) .post-body:has(.bls-page){{width:100%!important;max-width:none!important;margin:0!important;padding:0!important;overflow:visible!important}}body:has(.bls-page) .PopularPosts,body:has(.bls-page) .widget.PopularPosts,body:has(.bls-page) [id^="PopularPosts"]{{display:none!important}}.bls-page{{width:min(1440px,calc(100vw - 48px))!important;max-width:none!important;position:relative!important;left:50%!important;transform:translateX(-50%)!important;margin-top:32px!important;margin-bottom:0!important}}@media(max-width:700px){{body.ga-post-page:has(.bls-page) .centered-bottom{{display:block!important}}.bls-page{{width:calc(100vw - 16px)!important;margin-top:16px!important}}}}</style>
<script id="blogger-liq-header-loja-link">document.addEventListener('DOMContentLoaded',function(){{const store='https://limpeza-inteligente.blogspot.com/p/loja.html';const about=[...document.querySelectorAll('a[href$="/p/sobre.html"]')].find(a=>a.getBoundingClientRect().top<180);if(!about||!about.parentNode)return;const same=[...about.parentNode.querySelectorAll('a')].some(a=>/\/p\/loja\.html(?:$|[?#])/.test(a.href));if(same)return;const link=about.cloneNode(false);link.href=store;link.textContent='Loja';link.removeAttribute('aria-current');about.parentNode.insertBefore(link,about);}});</script>
{END}'''
SHELL_REPLACEMENTS={
'Cntent':'Cntent',
'Achados práticos para casa, tecnologia, beleza e dia a dia':'Limpeza prática para casa e rotina',
'Descubra produtos úteis para facilitar a rotina':'Tecnologia e soluções para uma limpeza mais eficiente',
'Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.':'Uma vitrine afiliada com equipamentos e utensílios de limpeza selecionados automaticamente na Shopee.',
'Cozinha e tecnologia':'Aspiração para diferentes necessidades',
'Soluções práticas para cozinhar, conectar e organizar melhor':'Robôs, verticais e portáteis para o dia a dia',
'A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.':'A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando filtros, peças, refis e acessórios avulsos.',
'Beleza e praticidade':'Limpeza além da aspiração',
'Achados reais para cuidados pessoais e rotina':'Mops, lavadoras e higienização para completar a rotina',
'href="#bls-cozinha-utilidades">Ver cozinha':'href="#bls-aspiradores-verticais">Ver verticais',
'href="#bls-tecnologia">Ver tecnologia':'href="#bls-aspiradores-portateis">Ver portáteis',
'href="#bls-beleza">Ver beleza':'href="#bls-mops-limpeza">Ver mops',
'href="#bls-dia-a-dia">Ver dia a dia':'href="#bls-lavadoras-higienizacao">Ver higienização',
'<a class="bls-cat" href="#bls-casa-organizacao"><b>Casa &amp; Organização</b><small>organização e soluções para o lar</small></a>':'<a class="bls-cat" href="#bls-robos-aspiradores"><b>Robôs Aspiradores</b><small>automação para pisos e rotina</small></a>',
'<a class="bls-cat" href="#bls-cozinha-utilidades"><b>Cozinha &amp; Utilidades</b><small>itens úteis para a cozinha</small></a>':'<a class="bls-cat" href="#bls-aspiradores-verticais"><b>Aspiradores Verticais</b><small>praticidade para a limpeza diária</small></a>',
'<a class="bls-cat" href="#bls-tecnologia"><b>Tecnologia &amp; Acessórios</b><small>conectividade e eletrônicos úteis</small></a>':'<a class="bls-cat" href="#bls-aspiradores-portateis"><b>Aspiradores Portáteis</b><small>limpeza compacta para casa e carro</small></a>',
'<a class="bls-cat" href="#bls-beleza"><b>Beleza &amp; Cuidados</b><small>cuidados pessoais e beleza</small></a>':'<a class="bls-cat" href="#bls-mops-limpeza"><b>Mops &amp; Limpeza Manual</b><small>pisos e superfícies no dia a dia</small></a>',
'<a class="bls-cat" href="#bls-dia-a-dia"><b>Dia a Dia &amp; Praticidade</b><small>produtos úteis para a rotina</small></a>':'<a class="bls-cat" href="#bls-lavadoras-higienizacao"><b>Lavadoras &amp; Higienização</b><small>limpeza pesada e higienização</small></a>',
'Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia':'Limpeza Inteligente: soluções para diferentes tarefas'
}

def patch_store_layout():
    blogger=criar_servico_blogger(); post=blogger.posts().get(blogId=BLOG_ID,postId=POST_ID).execute(); raw=str(post.get('content') or '')
    if 'BLOGGER_LIQ_STORE_AUTO_START' not in raw or 'BLOGGER_LIQ_HERO_AUTO_1_START' not in raw: raise RuntimeError('Post Loja sem marcadores esperados; layout preservado.')
    for old,new in SHELL_REPLACEMENTS.items(): raw=raw.replace(old,new)
    sc,ec=raw.count(START),raw.count(END)
    if sc or ec:
        if sc!=1 or ec!=1: raise RuntimeError('Marcadores do layout inconsistentes; post preservado.')
        a,b=raw.find(START),raw.find(END)
        if b<=a: raise RuntimeError('Ordem inválida dos marcadores do layout; post preservado.')
        updated=raw[:a]+BLOCK+raw[b+len(END):]
    else: updated=BLOCK+'\n'+raw
    if updated != str(post.get('content') or ''):
        body={'title':post.get('title') or 'Loja','content':updated}
        if post.get('labels') is not None: body['labels']=post.get('labels')
        blogger.posts().update(blogId=BLOG_ID,postId=POST_ID,body=body).execute()
    verify=str(blogger.posts().get(blogId=BLOG_ID,postId=POST_ID).execute().get('content') or '')
    required=(START,END,'BLOGGER_LIQ_STORE_AUTO_START','BLOGGER_LIQ_HERO_AUTO_1_START','https://limpeza-inteligente.blogspot.com/p/loja.html','[id^="PopularPosts"]','grid-template-columns:minmax(0,1fr)!important','href="#bls-robos-aspiradores"','href="#bls-lavadoras-higienizacao"','Limpeza Inteligente: soluções para diferentes tarefas')
    missing=[x for x in required if x not in verify]
    if missing: raise RuntimeError(f'Falha na verificação do layout/shell; ausentes={missing}')
    print('LAYOUT_WIDE_APPLIED'); print('STORE_TARGET_LIMPEZA_OK'); print('STORE_SHELL_NICHE_LIMPEZA_OK')

if __name__=='__main__': patch_store_layout()
