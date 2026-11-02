#!/usr/bin/env python3
from __future__ import annotations

import os
import re

from criar_rascunho import criar_servico_blogger

BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "1426630233929943394").strip()
POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "854861801599328533").strip()
DRY_RUN = os.getenv("ACHADOS_STORE_DRY_RUN", "true").strip().lower() in {"1", "true", "yes", "on"}
EXPECTED_BLOG_ID = "1426630233929943394"
EXPECTED_POST_ID = "854861801599328533"
STORE_PAGE = "https://achadosparacasa2026.blogspot.com/p/loja.html"

REPLACEMENTS = {
    "Achados práticos para casa, tecnologia, beleza e dia a dia": "Achados práticos para organizar, equipar e cuidar da casa",
    "Descubra produtos úteis para facilitar a rotina": "Achados úteis para deixar a casa mais prática",
    "Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.": "Uma vitrine afiliada focada em organização, cozinha, limpeza, decoração, conforto e bem-estar para a casa.",
    "Cozinha e tecnologia": "Cozinha, limpeza e lavanderia",
    "Soluções práticas para cozinhar, conectar e organizar melhor": "Soluções úteis para a rotina da casa",
    "A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.": "A seleção prioriza produtos completos e coerentes com cada categoria da casa, bloqueando peças, refis e falsos positivos.",
    '<a class="bls-btn bls-btn-soft" href="#bls-tecnologia">Ver tecnologia</a>': '<a class="bls-btn bls-btn-soft" href="#bls-limpeza-lavanderia">Ver limpeza</a>',
    "Beleza e praticidade": "Decoração, conforto e clima",
    "Achados reais para cuidados pessoais e rotina": "Mais conforto e praticidade em cada ambiente",
    "Preço, frete, estoque e condições são confirmados no anúncio de destino. A vitrine não processa pagamento nem entrega.": "Preço, frete, estoque e condições são confirmados no anúncio de destino. A vitrine não processa pagamento, estoque ou entrega.",
    '<a class="bls-btn bls-btn-main" href="#bls-beleza">Ver beleza</a>': '<a class="bls-btn bls-btn-main" href="#bls-decoracao-conforto">Ver decoração</a>',
    '<a class="bls-btn bls-btn-soft" href="#bls-dia-a-dia">Ver dia a dia</a>': '<a class="bls-btn bls-btn-soft" href="#bls-clima-bem-estar">Ver clima e conforto</a>',
    "Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia": "Vitrine de achados práticos para organização, cozinha, limpeza, decoração e conforto",
}

NEW_CATS = '<div class="bls-cats"><a class="bls-cat" href="#bls-organizacao-armazenamento"><b>Organização &amp; Armazenamento</b><small>soluções para guardar e organizar</small></a><a class="bls-cat" href="#bls-cozinha-utilidades"><b>Cozinha &amp; Utilidades</b><small>itens úteis para a rotina da cozinha</small></a><a class="bls-cat" href="#bls-limpeza-lavanderia"><b>Limpeza &amp; Lavanderia</b><small>praticidade para cuidar da casa</small></a><a class="bls-cat" href="#bls-decoracao-conforto"><b>Decoração &amp; Conforto</b><small>itens para ambientes mais agradáveis</small></a><a class="bls-cat" href="#bls-clima-bem-estar"><b>Clima &amp; Bem-estar</b><small>conforto térmico e bem-estar no lar</small></a></div>'


def patch(raw: str) -> str:
    out = raw
    for old, new in REPLACEMENTS.items():
        out = out.replace(old, new)
    out, count = re.subn(r'<div class="bls-cats">.*?</div>(?=</div></section>)', NEW_CATS, out, count=1, flags=re.S)
    if count != 1 and NEW_CATS not in out:
        raise RuntimeError("Não foi possível localizar a navegação de categorias da Loja.")
    return out


def verify(raw: str) -> None:
    required = [
        STORE_PAGE,
        "Achados úteis para deixar a casa mais prática",
        "Cozinha, limpeza e lavanderia",
        "Decoração, conforto e clima",
        '#bls-organizacao-armazenamento',
        '#bls-limpeza-lavanderia',
        '#bls-decoracao-conforto',
        '#bls-clima-bem-estar',
        "blogger-liq-layout-wide-css",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Patch de identidade incompleto: {missing}")
    forbidden = [
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        "https://liquidificadores-em-foco.blogspot.com/p/loja.html",
        '#bls-tecnologia',
        '#bls-beleza',
        '#bls-dia-a-dia',
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Identidade legada/genérica ainda presente: {bad}")


def main() -> int:
    if BLOG_ID != EXPECTED_BLOG_ID or POST_ID != EXPECTED_POST_ID:
        raise RuntimeError("Alvo Blogger do Achados para Casa não confere.")
    service = criar_servico_blogger()
    post = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    raw = str(post.get("content") or "")
    new_raw = patch(raw)
    verify(new_raw)
    if DRY_RUN:
        print("ACHADOS_CASA_LAYOUT_DRY_RUN_PASS: identidade e categorias validadas em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify_post = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify(str(verify_post.get("content") or ""))
    print("ACHADOS_CASA_LAYOUT_PASS: identidade do nicho casa e navegação da Loja confirmadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
