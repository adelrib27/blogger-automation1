#!/usr/bin/env python3
from __future__ import annotations
import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'src'))
from criar_rascunho import criar_servico_blogger
BLOG_ID=os.getenv('BLOGGER_BLOG_ID','8658632621591002634').strip(); POST_ID=os.getenv('BLOGGER_STORE_POST_ID','2599179962359747947').strip()
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
<script id="blogger-liq-header-loja-link">document.addEventListener('DOMContentLoaded',function(){{const store='https://eletroportateis-na-cozinha.blogspot.com/p/loja.html';const about=[...document.querySelectorAll('a[href$="/p/sobre.html"]')].find(a=>a.getBoundingClientRect().top<180);if(!about||!about.parentNode)return;const same=[...about.parentNode.querySelectorAll('a')].some(a=>/\/p\/loja\.html(?:$|[?#])/.test(a.href));if(same)return;const link=about.cloneNode(false);link.href=store;link.textContent='Loja';link.removeAttribute('aria-current');about.parentNode.insertBefore(link,about);}});</script>
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
      'Achados práticos para casa, tecnologia, beleza e dia a dia':'Eletroportáteis para facilitar sua rotina na cozinha',
      'Descubra produtos úteis para facilitar a rotina':'Descubra eletroportáteis para preparar, servir e cozinhar melhor',
      'Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.':'Uma vitrine afiliada com eletroportáteis para cozinha, selecionados automaticamente na Shopee.',
      'Cozinha e tecnologia':'Preparo e versatilidade',
      'Soluções práticas para cozinhar, conectar e organizar melhor':'Liquidificar, processar e agilizar receitas',
      'A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.':'A seleção prioriza aparelhos completos para preparo de alimentos, com peças e reposições bloqueadas.',
      '>Ver cozinha<':'>Ver liquidificadores<',
      '>Ver tecnologia<':'>Ver processadores<',
      'Beleza e praticidade':'Massas, cafés e lanches',
      'Achados reais para cuidados pessoais e rotina':'Batedeiras, cafeteiras e outros eletros para a cozinha',
      '>Ver beleza<':'>Ver batedeiras<',
      '>Ver dia a dia<':'>Ver outros eletros<',
      'Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia':'Vitrine de eletroportáteis para cozinha',
      'Casa &amp; Organização':'Air Fryers','Cozinha &amp; Utilidades':'Liquidificadores &amp; Mixers','Tecnologia &amp; Acessórios':'Processadores','Beleza &amp; Cuidados':'Batedeiras','Dia a Dia &amp; Praticidade':'Cafeteiras &amp; Outros Eletros',
      '#bls-casa-organizacao':'#bls-air-fryers','#bls-cozinha-utilidades':'#bls-liquidificadores-mixers','#bls-tecnologia':'#bls-processadores','#bls-beleza':'#bls-batedeiras','#bls-dia-a-dia':'#bls-cafeteiras-outros',
      'organização e soluções para o lar':'fritadeiras e preparo sem óleo','itens úteis para a cozinha':'liquidificar, bater e misturar','conectividade e eletrônicos úteis':'processar, triturar e agilizar receitas','cuidados pessoais e beleza':'bolos, massas e preparos','produtos úteis para a rotina':'cafés, lanches e bebidas quentes'
    }
    for x,y in repl.items(): raw=raw.replace(x,y)
    body={'title':post.get('title') or 'Loja','content':raw}
    if post.get('labels') is not None: body['labels']=post.get('labels')
    blogger.posts().update(blogId=BLOG_ID,postId=POST_ID,body=body).execute(); verify=str(blogger.posts().get(blogId=BLOG_ID,postId=POST_ID).execute().get('content') or '')
    required=(START,END,'grid-template-columns:minmax(0,1fr)!important','https://eletroportateis-na-cozinha.blogspot.com/p/loja.html','href="#bls-air-fryers"','href="#bls-liquidificadores-mixers"','href="#bls-processadores"','href="#bls-batedeiras"','href="#bls-cafeteiras-outros"','Vitrine de eletroportáteis para cozinha')
    for token in required:
        if token not in verify: raise RuntimeError('Falha layout/identidade: '+token)
    forbidden=('liquidificadores-em-foco.blogspot.com','href="#bls-casa-organizacao"','Achados reais para cuidados pessoais e rotina')
    for token in forbidden:
        if token in verify: raise RuntimeError('Herança indevida ainda presente: '+token)
    print('ELETROPORTATEIS_LAYOUT_IDENTITY_PASS')
if __name__=='__main__': patch_store_layout()
