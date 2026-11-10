#!/usr/bin/env python3
"""Gera links de afiliado pela conta Shopee do usuário para quatro anúncios públicos confirmados.

SAFE: apenas mutação de geração de shortLink Shopee, sem editar Blogger, GitHub, lojas nem estado persistente.
"""
from __future__ import annotations
import json
import os
import sys
import urllib.parse

from refresh_blogger_offer_links import generate_short_link

BLOG_ID = "4820923154548273510"
TARGETS = (
    ("coado", "8925550979772572350", "58255557635", "https://shopee.com.br/product/736567489/58255557635",
     "Porta Filtro Café 102 e 103 Suporte Moderno para Coador de Papel"),
    ("moedor", "7369094207848867023", "22494405073", "https://shopee.com.br/product/1454930884/22494405073",
     "Moedor de Café Manual com Ajuste de Moagem Grosso e Fino Compacto"),
    ("prensa", "429279097434589750", "53415510560", "https://shopee.com.br/product/1373441778/53415510560",
     "Prensa Francesa Cafeteira de Vidro 600ml com Filtro Removível"),
    ("pilar", "2733395139323654230", "54557028525", "https://shopee.com.br/product/332059670/54557028525",
     "Chaleira Elétrica Inox 1,8L para aquecer água")
)
ALLOWED = {"s.shopee.com.br", "shopee.com.br", "www.shopee.com.br"}

def fail(s: str) -> None:
    raise RuntimeError("FAIL_CLOSED: " + s)

def origin_is_valid(origin: str, item_id: str) -> bool:
    p = urllib.parse.urlparse(origin)
    return p.scheme == "https" and p.hostname in {"shopee.com.br", "www.shopee.com.br"} and p.path.endswith("/" + item_id)

def affiliate_is_valid(url: str) -> bool:
    p = urllib.parse.urlparse(url)
    return p.scheme == "https" and p.hostname in ALLOWED and not p.username and not p.password

def self_test() -> None:
    for topic, post_id, item_id, origin, title in TARGETS:
        if not topic or not post_id.isdecimal() or not item_id.isdecimal() or not origin_is_valid(origin, item_id) or not title:
            fail("alvo do artigo inconsistente")
    if len(set(t[2] for t in TARGETS)) != 4:
        fail("itemIds duplicados")
    if affiliate_is_valid("https://other.example/item"):
        fail("aceitou host externo")
    print("CAFE_SHORTLINK_SELF_TEST_PASS", flush=True)

def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    app = os.getenv("SHOPEE_APP_ID", "").strip()
    secret = os.getenv("SHOPEE_SECRET", "").strip()
    if not app or not secret:
        fail("credenciais ausentes")
    rows = []
    for topic, post_id, item_id, origin, title in TARGETS:
        try:
            link = generate_short_link(app, secret, origin)
        except Exception as exc:
            # Erros do provedor nunca são reproduzidos nos logs; não imprimir headers, body ou secrets.
            fail("geração de link falhou para " + topic + ": " + type(exc).__name__)
        if not affiliate_is_valid(link):
            fail("domínio/HTTPS inválido para " + topic)
        rows.append({"topic":topic, "postId":post_id, "itemId":item_id,
                     "productName":title, "originUrl":origin, "offerLink":link})
        print("CAFE_GENERATED_AFFILIATE_LINK_OK topic=" + topic,flush=True)
    if len(rows)!=4:
        fail("não foram gerados quatro links")
    print("CAFE_ARTICLE_GENERATED_LINKS_JSON=" + json.dumps({
        "blog_id":BLOG_ID,"items":rows
    },ensure_ascii=False,separators=(",",":")),flush=True)
    print("CAFE_LINKS_SAFE_NO_BLOGGER_WRITE",flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc)[:240],file=sys.stderr)
        raise SystemExit(2)
