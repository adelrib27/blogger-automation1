#!/usr/bin/env python3
from __future__ import annotations
import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'src'))
from criar_rascunho import criar_servico_blogger
BLOG_ID=os.getenv('BLOGGER_BLOG_ID','7757953554206491487').strip(); POST_ID=os.getenv('BLOGGER_STORE_POST_ID','6383277011247909539').strip()
START='<!-- BLOGGER_LIQ_LAYOUT_PATCH_START -->'; END='<!-- BLOGGER_LIQ_LAYOUT_PATCH_END -->'
BLOCK=f'''{START}
<style id="blogger-liq-layout-wide-css">
.post-body{{overflow:visible!important}}
body.ga-post-page:has(.bls-page) .centered-bottom{{display:grid!important;grid-template-columns:minmax(0,1fr)!important;grid-template-rows:auto!important;gap:0!important;margin-left:auto!important;margin-right:auto!important}}
body.ga-post-page:has(.bls-page) .main-container{{grid-column:1!important;grid-area:1 / 1!important;width:100%!important;max-width:none!important;min-width:0!important;margin:0!important}}
body.ga-post-page:has(.bls-page) .sidebar-container,body:has(.bls-page) .sidebar-container,body:has(.bls-page) .sidebar-container-container,body:has(.bls-page) .main-container aside{{display:none!important}}
body:has(.bls-page) .main-container,body:has(.bls-page) .main,body:has(.bls-page) .blog-posts,body:has(.bls-page) .post-outer-container:has(.bls-page),body:has(.bls-page) .post-outer:has(.bls-page),body:has(.bls-page) .post:has(.bls-page),body:has(.bls-page) .post-body-container:has(.bls-page){{width:100%!important;max-width:none!important}}
body:has(.bls-page) .post-outer-container:has(.bls-page),body:has(.bls-page) .post-outer:has(.bls-page),body:has(.bls-page) .post:has(.bls-page),body:has(.bls-page) .post-body-container:has(.bls-page){{background:transparent!important;border:0!important;box-shadow:none!important;overflow:visible!important;padding-top:0!important;padding-bottom:0!important;margin-top:0!important;margin-bottom:0!important}}
body:has(.bls-page) .post:has(.bls-page) .post-header,body:has(.bls-page) .post:has(.bls-page) .post-title,body:has(.bls-page) .post:has(.bls-page) .entry-title{{display:none!important}}
body:has(.bls-page) .post-body:has(.bls-page){{width:100%!important;max-width:none!important;margin:0!important;padding:0!important;overflow:visible!important}}
body:has(.bls-page) .PopularPosts,body:has(.bls-page) .widget.PopularPosts,body:has(.bls-page) [id^="PopularPosts"]{{display:none!important}}
.bls-page{{width:min(1440px,calc(100vw - 48px))!important;max-width:none!important;position:relative!important;left:50%!important;transform:translateX(-50%)!important;margin-top:32px!important;margin-bottom:0!important}}
@media(max-width:700px){{body.ga-post-page:has(.bls-page) .centered-bottom{{display:block!important}}.bls-page{{width:calc(100vw - 16px)!important;margin-top:16px!important}}}}
</style>
<script id="blogger-liq-header-loja-link">document.addEventListener('DOMContentLoaded',function(){{const store='https://limpeza-inteligente.blogspot.com/p/loja.html';const about=[...document.querySelectorAll('a[href$="/p/sobre.html"]')].find(a=>a.getBoundingClientRect().top<180);if(!about||!about.parentNode)return;const same=[...about.parentNode.querySelectorAll('a')].some(a=>/\/p\/loja\.html(?:$|[?#])/.test(a.href));if(same)return;const link=about.cloneNode(false);link.href=store;link.textContent='Loja';link.removeAttribute('aria-current');about.parentNode.insertBefore(link,about);}});</script>
{END}'''

def patch_store_layout():
    blogger=criar_servico_blogger(); post=blogger.posts().get(blogId=BLOG_ID,postId=POST_ID).execute(); raw=str(post.get('content') or '')
    if 'BLOGGER_LIQ_STORE_AUTO_START' not in raw or 'BLOGGER_LIQ_HERO_AUTO_1_START' not in raw: raise RuntimeError('Post Loja sem marcadores esperados; preservado.')
    sc,ec=raw.count(START),raw.count(END)
    if sc or ec:
        if sc!=1 or ec!=1: raise RuntimeError('Marcadores do layout inconsistentes.')
        a,b=raw.find(START),raw.find(END); raw=raw[:a]+BLOCK+raw[b+len(END):]
    else: raw=BLOCK+'\n'+raw
    repl={
      'Achados práticos para casa, tecnologia, beleza e dia a dia':'Limpeza prática para casa e rotina',
      'Descubra produtos úteis para facilitar a rotina':'Tecnologia e soluções para uma limpeza mais eficiente',
      'Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.':'Uma vitrine afiliada com equipamentos e utensílios de limpeza selecionados automaticamente na Shopee.',
      'Casa &amp; Organização':'Robôs Aspiradores','Cozinha &amp; Utilidades':'Aspiradores Verticais','Tecnologia &amp; Acessórios':'Aspiradores Portáteis','Beleza &amp; Cuidados':'Mops &amp; Limpeza Manual','Dia a Dia &amp; Praticidade':'Lavadoras &amp; Higienização',
      '#bls-casa-organizacao':'#bls-robos-aspiradores','#bls-cozinha-utilidades':'#bls-aspiradores-verticais','#bls-tecnologia':'#bls-aspiradores-portateis','#bls-beleza':'#bls-mops-limpeza','#bls-dia-a-dia':'#bls-lavadoras-higienizacao',
      'organização e soluções para o lar':'automação para pisos e rotina','itens úteis para a cozinha':'praticidade para a limpeza diária','conectividade e eletrônicos úteis':'limpeza compacta para casa e carro','cuidados pessoais e beleza':'pisos e superfícies no dia a dia','produtos úteis para a rotina':'limpeza pesada e higienização',
      'Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia':'Limpeza Inteligente: soluções para diferentes tarefas'
    }
    for x,y in repl.items(): raw=raw.replace(x,y)
    body={'title':post.get('title') or 'Loja','content':raw}
    if post.get('labels') is not None: body['labels']=post.get('labels')
    blogger.posts().update(blogId=BLOG_ID,postId=POST_ID,body=body).execute(); verify=str(blogger.posts().get(blogId=BLOG_ID,postId=POST_ID).execute().get('content') or '')
    required=(START,END,'grid-template-columns:minmax(0,1fr)!important','https://limpeza-inteligente.blogspot.com/p/loja.html','href="#bls-robos-aspiradores"','href="#bls-aspiradores-verticais"','href="#bls-aspiradores-portateis"','href="#bls-mops-limpeza"','href="#bls-lavadoras-higienizacao"')
    for token in required:
        if token not in verify: raise RuntimeError('Falha layout/identidade: '+token)
    print('LIMPEZA_LAYOUT_PASS')
if __name__=='__main__': patch_store_layout()
