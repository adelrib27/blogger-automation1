#!/usr/bin/env python3
"""Consulta somente leitura Shopee Affiliate API: um produto real para cada um dos quatro artigos Café na Medida.

Não grava Blogger, GitHub, arquivos de seleção, nem secrets. Publicação ocorre apenas após readback manual.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from blogger_policy_guard import require_product_allowed
from shopee_oportunidades import post_graphql, product_query

BLOG_ID = "4820923154548273510"
API = "https://open-api.affiliate.shopee.com.br/graphql"
TARGETS = (
    ("coado", "8925550979772572350", ("coador de cafe v60", "coador de cafe")),
    ("moedor", "7369094207848867023", ("moedor de cafe manual", "moedor de cafe")),
    ("prensa", "429279097434589750", ("prensa francesa cafe", "cafeteira prensa francesa")),
    ("pilar", "2733395139323654230", ("balanca digital para cafe", "chaleira bico fino cafe")),
)
AFF_HOSTS = {"s.shopee.com.br", "shopee.com.br", "www.shopee.com.br"}
IMAGE_HOSTS = {"cf.shopee.com.br", "down-br.img.susercontent.com", "down-vn.img.susercontent.com"}

def fail(message: str) -> None:
    raise RuntimeError("FAIL_CLOSED: " + message)

def norm(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c))

def permitted(url: str, hosts: set[str]) -> bool:
    try:
        parsed = urllib.parse.urlparse(str(url))
        return parsed.scheme == "https" and parsed.hostname in hosts and not parsed.username and not parsed.password
    except ValueError:
        return False

def topic_matches(topic: str, name: str) -> bool:
    s = norm(name)
    banned = ("brinquedo", "miniatura", "enfeite", "decoracao", "caneca decorativa", "adesivo", "porta filtro", "suporte para filtro", "triturador de carne")
    if any(b in s for b in banned):
        return False
    if topic == "coado":
        return ("coador" in s and ("cafe" in s or "v60" in s)) or ("filtro de cafe" in s and "papel" in s)
    if topic == "moedor":
        return ("moedor" in s or "moinho" in s) and ("cafe" in s or "coffee" in s) and not any(x in s for x in ("carne", "alho", "temperos"))
    if topic == "prensa":
        return "prensa francesa" in s or "french press" in s
    if topic == "pilar":
        return ("balanca" in s and ("cafe" in s or "barista" in s)) or ("chaleira" in s and "bico fino" in s and ("cafe" in s or "barista" in s))
    return False

def select_one(topic: str, nodes: list[dict], used: set[str]) -> dict | None:
    for row in nodes:
        try:
            item = str(row.get("itemId") or "").strip()
            name = str(row.get("productName") or "").strip()
            offer = str(row.get("offerLink") or "").strip()
            image = str(row.get("imageUrl") or "").strip()
            price = float(row.get("priceMin") or 0)
            if not item.isdecimal() or item in used or not name or not topic_matches(topic, name):
                continue
            if not math.isfinite(price) or not (0 < price <= 10000):
                continue
            if not permitted(offer, AFF_HOSTS) or not permitted(image, IMAGE_HOSTS):
                continue
            product = {"itemId": item, "productName": name, "offerLink": offer,
                       "imageUrl": image, "priceMin": price}
            require_product_allowed(product)
            return {"itemId": item, "productName": name[:220], "offerLink": offer,
                    "imageUrl": image, "shopName": str(row.get("shopName") or "")[:100],
                    "priceMin": price}
        except (ValueError, TypeError, RuntimeError):
            continue
    return None

def query_api(app: str, secret: str, term: str) -> list[dict]:
    # Reutiliza o motor validado do projeto, inclusive listType e isAMSOffer.
    query = product_query(term, list_type=1, sort_type=2, limit=20, ams_only=False)
    data = post_graphql(app, secret, query, retries=1)
    if data.get("errors"):
        codes = sorted({str((err.get("extensions") or {}).get("code", "NONE"))
                        for err in data.get("errors", []) if isinstance(err, dict)})
        fail("GraphQL código(s)=" + ",".join(codes) + " keyword=" + term)
    nodes = ((data.get("data") or {}).get("productOfferV2") or {}).get("nodes")
    if not isinstance(nodes, list):
        fail("nodes ausentes ou tipo incorreto")
    return nodes

def self_test() -> None:
    sample = {"itemId":"123", "productName":"Moedor manual de cafe em inox",
              "offerLink":"https://s.shopee.com.br/AbcD123", "imageUrl":"https://cf.shopee.com.br/file/teste",
              "priceMin":"34.90", "shopName":"Exemplo"}
    if select_one("moedor", [sample], set()) is None:
        fail("moedor válido não foi aceito")
    if select_one("moedor", [dict(sample, productName="Moedor de carne")], set()):
        fail("falso positivo: moedor de carne")
    if select_one("moedor", [dict(sample, offerLink="https://example.com/produto")], set()):
        fail("host de afiliado não permitido")
    if select_one("moedor", [dict(sample, imageUrl="http://cf.shopee.com.br/file/teste")], set()):
        fail("imagem insegura não permitida")
    if select_one("moedor", [sample], {"123"}):
        fail("duplicata não bloqueada")
    print("CAFE_ARTICLE_SELF_TEST_PASS", flush=True)

def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    app, secret = os.getenv("SHOPEE_APP_ID","").strip(), os.getenv("SHOPEE_SECRET","").strip()
    if not app or not secret:
        fail("credenciais não disponíveis no ambiente de execução")
    used, selected = set(), []
    for topic, post_id, terms in TARGETS:
        candidate = None
        for term in terms:
            candidate = select_one(topic, query_api(app, secret, term), used)
            if candidate:
                break
        if not candidate:
            fail("nenhum item semanticamente válido para " + topic)
        used.add(candidate["itemId"])
        selected.append({"topic": topic, "postId": post_id, **candidate})
        print("CAFE_TOPIC_PASS " + topic + " itemId=" + candidate["itemId"], flush=True)
    if len(selected)!=4 or len(used)!=4:
        fail("seleção final inconsistente")
    # Estes quatro links serão publicados nos artigos. Nunca registrar credenciais nem headers.
    print("CAFE_ARTICLE_PRODUCTS_JSON=" + json.dumps({
        "blog_id": BLOG_ID, "products": selected
    }, ensure_ascii=False, separators=(",", ":")), flush=True)
    print("CAFE_ARTICLE_SHOPEE_SAFE_PASS_NO_BLOGGER_WRITE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc)[:380], file=sys.stderr)
        raise SystemExit(2)
