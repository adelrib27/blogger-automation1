#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER_OLD = "emporio-revisao-visual-10-square-contact"
MARKER_NEW = "emporio-revisao-visual-11-post-finish"

CSS = r'''
/* ============================================================
   GUIA DE ACHADOS & OFERTAS — V11 POST FINISH
   Escopo: páginas de POST (/AAAA/MM/...).
   Preserva integralmente o corpo editorial já aprovado.
   Ajusta apenas PopularPosts, comentários/login e rodapé.
   ============================================================ */

/* Remove a área nativa de comentários/login somente nos posts. */
body.ga-post-page #comments,
body.ga-post-page .comments,
body.ga-post-page .comment-form,
body.ga-post-page .comment-thread,
body.ga-post-page iframe#comment-editor,
body.ga-post-page iframe.blogger-comment-from-post{
  display:none!important;
}

/* Sidebar: ganha espaço e deixa de criar rolagem horizontal. */
body.ga-post-page .sidebar-container{
  box-sizing:border-box!important;
  flex:0 0 340px!important;
  max-width:340px!important;
  min-width:300px!important;
  overflow:visible!important;
  width:340px!important;
}
body.ga-post-page #PopularPosts1,
body.ga-post-page .widget.PopularPosts{
  box-sizing:border-box!important;
  max-width:100%!important;
  overflow:hidden!important;
  width:100%!important;
}
body.ga-post-page #PopularPosts1 .widget-content,
body.ga-post-page #PopularPosts1 .popular-posts,
body.ga-post-page #PopularPosts1 .popular-posts-list,
body.ga-post-page .widget.PopularPosts .widget-content,
body.ga-post-page .widget.PopularPosts .popular-posts,
body.ga-post-page .widget.PopularPosts .popular-posts-list{
  box-sizing:border-box!important;
  max-width:100%!important;
  overflow:visible!important;
  width:100%!important;
}
body.ga-post-page #PopularPosts1 .popular-post,
body.ga-post-page .widget.PopularPosts .popular-post{
  box-sizing:border-box!important;
  display:block!important;
  margin:0!important;
  max-width:100%!important;
  overflow:hidden!important;
  padding:0 0 20px!important;
  width:100%!important;
}
body.ga-post-page #PopularPosts1 .popular-post + .popular-post,
body.ga-post-page .widget.PopularPosts .popular-post + .popular-post{
  border-top:1px solid #edf1f5!important;
  padding-top:20px!important;
}

/* Imagens proporcionais e previsíveis dentro da sidebar. */
body.ga-post-page #PopularPosts1 .post-thumbnail,
body.ga-post-page .widget.PopularPosts .post-thumbnail{
  aspect-ratio:16 / 10!important;
  box-sizing:border-box!important;
  display:block!important;
  height:auto!important;
  margin:0 0 12px!important;
  max-width:100%!important;
  overflow:hidden!important;
  width:100%!important;
}
body.ga-post-page #PopularPosts1 .post-thumbnail img,
body.ga-post-page .widget.PopularPosts .post-thumbnail img{
  display:block!important;
  height:100%!important;
  max-width:none!important;
  object-fit:cover!important;
  object-position:center!important;
  width:100%!important;
}
body.ga-post-page #PopularPosts1 .post-title,
body.ga-post-page .widget.PopularPosts .post-title{
  box-sizing:border-box!important;
  display:-webkit-box!important;
  font-size:14px!important;
  line-height:1.45!important;
  margin:0 0 8px!important;
  max-width:100%!important;
  overflow:hidden!important;
  overflow-wrap:anywhere!important;
  -webkit-box-orient:vertical!important;
  -webkit-line-clamp:3!important;
  white-space:normal!important;
  width:100%!important;
}
body.ga-post-page #PopularPosts1 .post-snippet,
body.ga-post-page .widget.PopularPosts .post-snippet{
  box-sizing:border-box!important;
  display:-webkit-box!important;
  font-size:13px!important;
  line-height:1.55!important;
  margin:0!important;
  max-width:100%!important;
  overflow:hidden!important;
  overflow-wrap:anywhere!important;
  -webkit-box-orient:vertical!important;
  -webkit-line-clamp:3!important;
  white-space:normal!important;
  width:100%!important;
}

/* Rodapé das páginas de post: mesmo desenho da home. */
body.ga-post-page .ga-post-footer{
  background:#ffffff!important;
  border:1px solid #dce4ee!important;
  border-radius:20px!important;
  box-shadow:0 12px 34px rgba(23,32,51,.06)!important;
  box-sizing:border-box!important;
  clear:both!important;
  color:#425066!important;
  display:block!important;
  margin:54px auto 28px!important;
  max-width:1220px!important;
  overflow:hidden!important;
  position:relative!important;
  width:calc(100% - 48px)!important;
  z-index:2!important;
}
body.ga-post-page .ga-post-footer .ga-home-footer-inner{
  display:grid!important;
  gap:34px!important;
  grid-template-columns:minmax(0,1.45fr) minmax(180px,.7fr) minmax(180px,.7fr)!important;
  padding:30px 34px 24px!important;
}
body.ga-post-page .ga-post-footer .ga-home-footer-brand h3{
  color:#172033!important;
  font:900 24px/1.12 Ubuntu,Arial,sans-serif!important;
  letter-spacing:-.45px!important;
  margin:0 0 10px!important;
}
body.ga-post-page .ga-post-footer .ga-home-footer-brand p{
  color:#728096!important;
  font:400 13.5px/1.6 Ubuntu,Arial,sans-serif!important;
  margin:0!important;
  max-width:560px!important;
}
body.ga-post-page .ga-post-footer h4{
  color:#172033!important;
  font:800 13px/1.2 Ubuntu,Arial,sans-serif!important;
  letter-spacing:.04em!important;
  margin:2px 0 12px!important;
  text-transform:uppercase!important;
}
body.ga-post-page .ga-post-footer-links{
  display:flex!important;
  flex-direction:column!important;
  gap:9px!important;
}
body.ga-post-page .ga-post-footer a{
  color:#425066!important;
  font:700 13px/1.4 Ubuntu,Arial,sans-serif!important;
  text-decoration:none!important;
}
body.ga-post-page .ga-post-footer a:hover{color:#175cd3!important}
body.ga-post-page .ga-post-footer .ga-home-footer-bottom{
  align-items:center!important;
  border-top:1px solid #edf1f5!important;
  color:#8793a5!important;
  display:flex!important;
  font:400 12px/1.4 Ubuntu,Arial,sans-serif!important;
  justify-content:space-between!important;
  padding:14px 34px 16px!important;
}
body.ga-post-page .ga-post-footer .ga-home-footer-bottom strong{
  color:#5f6c7d!important;
  font-weight:700!important;
}

@media screen and (max-width:1050px){
  body.ga-post-page .sidebar-container{
    flex-basis:300px!important;
    max-width:300px!important;
    width:300px!important;
  }
}
@media screen and (max-width:900px){
  body.ga-post-page .sidebar-container{
    max-width:none!important;
    min-width:0!important;
    width:100%!important;
  }
  body.ga-post-page .ga-post-footer .ga-home-footer-inner{
    grid-template-columns:1fr 1fr!important;
  }
  body.ga-post-page .ga-post-footer .ga-home-footer-brand{grid-column:1/-1!important}
}
@media screen and (max-width:700px){
  body.ga-post-page .ga-post-footer{
    border-left:0!important;
    border-radius:0!important;
    border-right:0!important;
    margin-bottom:0!important;
    width:100%!important;
  }
  body.ga-post-page .ga-post-footer .ga-home-footer-inner{
    gap:24px!important;
    grid-template-columns:1fr!important;
    padding:26px 18px 20px!important;
  }
  body.ga-post-page .ga-post-footer .ga-home-footer-brand{grid-column:auto!important}
  body.ga-post-page .ga-post-footer .ga-home-footer-bottom{
    align-items:flex-start!important;
    flex-direction:column!important;
    gap:6px!important;
    padding:14px 18px 18px!important;
  }
}
'''

JS = r'''
<script type='text/javascript'>
//<![CDATA[
(function(){
  var isPost=/^\/\d{4}\/\d{2}\//.test(location.pathname);
  if(!isPost) return;
  document.body.classList.add('ga-post-page');

  function removeComments(){
    var nodes=document.querySelectorAll('#comments,.comments,iframe#comment-editor,iframe.blogger-comment-from-post');
    for(var i=0;i<nodes.length;i++){
      var el=nodes[i];
      var root=el.closest('.comments') || el.closest('#comments') || el.closest('.comment-form') || el;
      if(root && root.parentNode) root.parentNode.removeChild(root);
    }

    /* Fallback para variações do Emporio em que o iframe vem sem wrapper estável. */
    var all=document.querySelectorAll('div,section');
    for(var j=0;j<all.length;j++){
      var t=(all[j].textContent||'').trim();
      if(t.indexOf('Para deixar um comentário')===0 && all[j].querySelector('iframe,button,a')){
        all[j].remove();
        break;
      }
    }
  }

  function buildFooter(){
    if(document.querySelector('.ga-post-footer')) return true;
    var host=document.querySelector('.page_body') || document.querySelector('.page-body') || document.body;
    if(!host) return false;

    var footer=document.createElement('section');
    footer.className='ga-post-footer';
    footer.setAttribute('aria-label','Rodapé do Guia de Achados & Ofertas');
    var year=(new Date()).getFullYear();
    footer.innerHTML=''
      +'<div class="ga-home-footer-inner">'
      +  '<div class="ga-home-footer-brand">'
      +    '<h3>Guia de Achados &amp; Ofertas</h3>'
      +    '<p>Achados, comparativos e dicas para ajudar você a escolher produtos para casa, cozinha, tecnologia e dia a dia com mais informação.</p>'
      +  '</div>'
      +  '<div>'
      +    '<h4>Navegação</h4>'
      +    '<div class="ga-home-footer-links">'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/">Início</a>'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/p/sobre.html">Sobre</a>'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/p/aviso-de-afiliados.html">Afiliados</a>'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/p/contato.html">Contato</a>'
      +    '</div>'
      +  '</div>'
      +  '<div>'
      +    '<h4>Informações</h4>'
      +    '<div class="ga-home-footer-links">'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/p/politica-de-privacidade.html">Política de Privacidade</a>'
      +      '<a href="https://guia-de-achados-e-ofertas.blogspot.com/p/termos-de-uso.html">Termos de Uso</a>'
      +    '</div>'
      +  '</div>'
      +'</div>'
      +'<div class="ga-home-footer-bottom">'
      +  '<span>© '+year+' <strong>Guia de Achados &amp; Ofertas</strong></span>'
      +  '<span>Conteúdo independente com links de afiliados.</span>'
      +'</div>';

    host.appendChild(footer);
    return true;
  }

  function apply(){
    removeComments();
    buildFooter();
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',apply,{once:true});
  else apply();
  setTimeout(apply,300);
  setTimeout(apply,1000);
  setTimeout(apply,2200);

  var until=Date.now()+5000;
  var observer=new MutationObserver(function(){
    removeComments();
    buildFooter();
    if(Date.now()>until) observer.disconnect();
  });
  observer.observe(document.documentElement,{childList:true,subtree:true});
  setTimeout(function(){observer.disconnect();apply();},5200);
})();
//]]>
</script>
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    p=argparse.ArgumentParser(description='V11: acabamento das páginas de post — PopularPosts, rodapé e remoção de comentários/login.')
    p.add_argument('--theme-path', required=True)
    args=p.parse_args()

    path=Path(args.theme_path).resolve()
    if not path.exists() or path.name.lower()!='theme.xml':
        raise SystemExit('theme.xml não encontrado no caminho informado.')

    text=path.read_text(encoding='utf-8')
    if MARKER_NEW in text:
        ET.parse(path)
        print(json.dumps({
          'status':'THEME_REVISION_11_ALREADY_BUILT',
          'path':str(path),'size_bytes':path.stat().st_size,'sha256':sha256(path),
          'xml_valid':True,'public_marker':MARKER_NEW
        },ensure_ascii=False,indent=2))
        return 0

    if MARKER_OLD not in text:
        raise SystemExit(f'A V10 validada não foi localizada. Marcador ausente: {MARKER_OLD}')

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
      'status':'THEME_REVISION_11_POST_FINISH_BUILT',
      'path':str(path),'size_bytes':path.stat().st_size,'sha256':sha256(path),'xml_valid':True,
      'public_marker':MARKER_NEW,
      'scope':'post-pages-only',
      'article_body_changed':False,
      'shopee_buttons_changed':False,
      'popular_posts_sidebar_adjusted':True,
      'horizontal_sidebar_scroll_removed':True,
      'comments_login_removed':True,
      'post_footer_added':True,
      'home_changed':False,
      'contact_page_changed':False
    },ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
