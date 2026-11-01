#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from criar_rascunho import criar_servico_blogger  # noqa: E402

BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "9113728635217260884").strip()
POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "5189023277801568424").strip()
START = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_START -->"
END = "<!-- BLOGGER_LIQ_LAYOUT_PATCH_END -->"
STORE_URL = "https://air-fryers-em-foco.blogspot.com/p/loja.html"

BLOCK = f'''{START}
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
<script id="blogger-liq-header-loja-link">
document.addEventListener('DOMContentLoaded',function(){{const store='{STORE_URL}';const about=[...document.querySelectorAll('a[href$="/p/sobre.html"]')].find(a=>a.getBoundingClientRect().top<180);if(!about||!about.parentNode)return;const same=[...about.parentNode.querySelectorAll('a')].some(a=>/\/p\/loja\.html(?:$|[?#])/.test(a.href));if(same)return;const link=about.cloneNode(false);link.href=store;link.textContent='Loja';link.removeAttribute('aria-current');about.parentNode.insertBefore(link,about);}});
</script>
{END}'''

REPLACEMENTS = {
    "https://airfryer-elgin-cube-fry-42l.blogspot.com/p/loja.html": STORE_URL,
    "Achados práticos para casa, tecnologia, beleza e dia a dia": "Air fryers e cozinha prática",
    "Descubra produtos úteis para facilitar a rotina": "Encontre a air fryer ideal para sua rotina",
    "Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.": "Uma vitrine afiliada com air fryers e acessórios de cozinha selecionados automaticamente na Shopee.",
    "Cozinha e tecnologia": "Capacidade e praticidade",
    "Soluções práticas para cozinhar, conectar e organizar melhor": "Compare modelos maiores para diferentes rotinas e tamanhos de família",
    "A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.": "A seleção prioriza aparelhos completos e acessórios coerentes, bloqueando limpeza, peças e falsos positivos.",
    "#bls-cozinha-utilidades": "#bls-air-fryers-grandes",
    "#bls-tecnologia": "#bls-air-fryers",
    "Ver cozinha": "Ver modelos grandes",
    "Ver tecnologia": "Ver air fryers",
    "Beleza e praticidade": "Acessórios e preparo",
    "Achados reais para cuidados pessoais e rotina": "Acessórios úteis para preparar, proteger e aproveitar melhor",
    "Preço, frete, estoque e condições são confirmados no anúncio de destino. A vitrine não processa pagamento nem entrega.": "Preço, frete, estoque e compatibilidade são confirmados no anúncio de destino. A vitrine não processa pagamento nem entrega.",
    "#bls-beleza": "#bls-grelhas-cestos",
    "#bls-dia-a-dia": "#bls-utensilios-preparo",
    "Ver beleza": "Ver grelhas",
    "Ver dia a dia": "Ver preparo",
    "#bls-casa-organizacao": "#bls-air-fryers",
    "Casa &amp; Organização": "Air Fryers &amp; Fritadeiras",
    "Casa & Organização": "Air Fryers & Fritadeiras",
    "organização e soluções para o lar": "aparelhos completos e fritadeiras sem óleo",
    "Cozinha &amp; Utilidades": "Air Fryers Grandes &amp; Família",
    "Cozinha & Utilidades": "Air Fryers Grandes & Família",
    "itens úteis para a cozinha": "modelos maiores para diferentes rotinas",
    "Tecnologia &amp; Acessórios": "Formas &amp; Revestimentos",
    "Tecnologia & Acessórios": "Formas & Revestimentos",
    "conectividade e eletrônicos úteis": "formas, papéis e revestimentos compatíveis",
    "Beleza &amp; Cuidados": "Grelhas &amp; Cestos",
    "Beleza & Cuidados": "Grelhas & Cestos",
    "cuidados pessoais e beleza": "grelhas, racks e cestos compatíveis",
    "Dia a Dia &amp; Praticidade": "Utensílios &amp; Preparo",
    "Dia a Dia & Praticidade": "Utensílios & Preparo",
    "produtos úteis para a rotina": "pegadores, pincéis e termômetros culinários",
    "Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia": "Vitrine especializada em air fryers e cozinha prática",
}


def patch_store_layout() -> None:
    if not BLOG_ID or not POST_ID:
        raise RuntimeError("BLOGGER_BLOG_ID/BLOGGER_STORE_POST_ID ausente.")
    blogger = criar_servico_blogger()
    post = blogger.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    raw_original = str(post.get("content") or "")
    if "BLOGGER_LIQ_STORE_AUTO_START" not in raw_original or "BLOGGER_LIQ_HERO_AUTO_1_START" not in raw_original:
        raise RuntimeError("Post Loja sem marcadores esperados; conteúdo preservado.")
    raw = raw_original
    for old, new in REPLACEMENTS.items():
        raw = raw.replace(old, new)
    start_count, end_count = raw.count(START), raw.count(END)
    if start_count or end_count:
        if start_count != 1 or end_count != 1:
            raise RuntimeError("Marcadores do layout inconsistentes; post preservado.")
        a, b = raw.find(START), raw.find(END)
        if b <= a:
            raise RuntimeError("Ordem inválida dos marcadores do layout; post preservado.")
        raw = raw[:a] + BLOCK + raw[b + len(END):]
    else:
        raw = BLOCK + "\n" + raw
    if raw == raw_original:
        print("LAYOUT_AIR_FRYERS_ALREADY_OK")
        return
    body = {"title": post.get("title") or "Loja", "content": raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    blogger.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = blogger.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    v = str(verify.get("content") or "")
    required = [START, END, STORE_URL, "grid-template-columns:minmax(0,1fr)!important", '[id^="PopularPosts"]', "Air Fryers &amp; Fritadeiras", "Air Fryers Grandes &amp; Família", "Formas &amp; Revestimentos", "Grelhas &amp; Cestos", "Utensílios &amp; Preparo"]
    missing = [x for x in required if x not in v]
    if missing:
        raise RuntimeError(f"Falha na verificação do shell Air Fryers; ausentes={missing}")
    print("AIR_FRYERS_LAYOUT_AND_SHELL_OK")


if __name__ == "__main__":
    patch_store_layout()
