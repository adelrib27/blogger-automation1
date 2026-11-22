"""V31 — descoberta BROAD-FIRST de ar-condicionados pela Shopee Affiliate API.

Apenas READ ONLY: nenhuma mutation de afiliado, nenhuma publicação e nenhum
pedido de reserva D1. Pesquisa generica antes de decidir qual anuncio divulgar.

A resposta da API indica oferta afiliada, NAO estoque comprovado.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from affiliate_hub_v31.shopee_probe import ENDPOINT, authorization

PRIMARY_KEYWORD = "ar condicionado"
ALTERNATIVE_KEYWORDS = ("ar condicionado split", "ar condicionado inverter", "ar condicionado de janela")
MAX_PAGES_PER_KEYWORD = 2
PAGE_SIZE = 30
MAX_QUERIES = 4
MAX_RESPONSE_BYTES = 131_072
HISTORY_PATH = Path(__file__).with_name("aircon_editorial_history.json")

PRODUCT = re.compile(r"\b(?:ar condicionado|condicionador de ar)\b")
ACCESSORY = re.compile(
    r"\b(?:controle remoto|controle universal|capa(?:s)?|suporte(?:s)?|"
    r"peca(?:s)?|placa(?:s)?|tubo(?:s)?|tubulacao|"
    r"mangueira(?:s)?|sensor(?:es)?|kit de instalacao|"
    r"kit instalacao|limpeza|higienizacao|"
    r"filtro(?:s)?|compressor(?:es)?|miniatura|adesivo(?:s)?|"
    r"brinquedo|climatizador|umidificador|ventilador|resfriador|"
    r"refrescador|refil|adaptador|refrigerante|"
    r"base para|cabo(?:s)?|valvula(?:s)?|radiador|moldura|vedacao|espuma|"
    r"atuador(?:es)?|engrenagem|conexao|painel de ar|"
    r"comando de ar|saida de ar|ar forcado|"
    r"evaporadora avulsa|condensadora avulsa|"
    r"ar condicionado automotivo|automotivo|veicular|"
    r"para carro|para toyota|para porsche|para ford|"
    r"para peugeot|para fiat|vw up|ford fusion|"
    r"ar condicionado de carro|r134a)\b"
)
CAPACITY = re.compile(r"\b(7[.,]?500|9[.,]?000|10[.,]?000|12[.,]?000|18[.,]?000|"
                      r"22[.,]?000|24[.,]?000|30[.,]?000|36[.,]?000)\s*(?:btu|btus)?\b")
BRANDS = ("midea","lg","samsung","gree","elgin","daikin","philco","tcl",
          "consul","springer","carrier","electrolux","agratto","hisense",
          "fujitsu","panasonic","hitachi","aiwa","fontaine","komeco")


def normalize(value: object) -> str:
    txt = unicodedata.normalize("NFKD", str(value or "").lower())
    txt = "".join(char for char in txt if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", txt)).strip()


def is_whole_air_conditioner(title: object) -> bool:
    txt = normalize(title)
    if not PRODUCT.search(txt) or ACCESSORY.search(txt):
        return False
    if re.search(r"\b(?:mini|usb|pessoal|de mesa|evaporativo|"
                 r"evaporadora usada|condensadora usada|motor|"
                 r"compativel com carro|siena|fiesta|cayenne)\b", txt):
        return False
    capacity = bool(CAPACITY.search(txt))
    appliance_form = bool(re.search(r"\b(?:split|inverter|janela|portatil|"
                                    r"quente e frio|hi wall)\b",txt))
    brand = any(re.search(r"\b"+re.escape(b)+r"\b",txt) for b in BRANDS)
    # Qualquer capacidade pode ser candidata: nao limitar a 9k/12k.
    # O numero com BTUs e so uma evidencia de aparelho real.
    explicit_btu = bool(re.search(r"\b[0-9]{3,6}\s?btu(?:s)?\b",txt))
    return (capacity or explicit_btu) and (appliance_form or brand)

def listing_key(node: dict) -> str:
    shop, item = str(node.get("shopId") or ""), str(node.get("itemId") or "")
    if not shop.isdigit() or not item.isdigit():
        raise ValueError("listing id missing")
    return f"{shop}:{item}"


def valid_listing(node: dict) -> bool:
    if not isinstance(node, dict) or not is_whole_air_conditioner(node.get("productName")):
        return False
    try:
        shop, item = listing_key(node).split(":")
        if int(shop) <= 0 or int(item) <= 0:
            return False
        price = float(node.get("priceMin") or 0)
        if price <= 0:
            return False
        deadline = int(node.get("periodEndTime") or 0)
        if deadline > 0 and deadline < int(time.time()):
            return False
        image, link, offer = (
            str(node.get(k) or "") for k in ("imageUrl","productLink","offerLink")
        )
        if not image.startswith("https://"):
            return False
        u = urllib.parse.urlsplit(link)
        if u.scheme != "https" or u.hostname != "shopee.com.br":
            return False
        if "/product/" not in u.path:
            return False
        if f"/product/{shop}/{item}" not in u.path:
            return False
        o = urllib.parse.urlsplit(offer)
        if o.scheme != "https" or o.hostname not in (
            "s.shopee.com.br","shope.ee","shopee.com.br"
        ):
            return False
    except (ValueError, TypeError, OverflowError):
        return False
    return True


def make_identity(node: dict) -> str:
    """Do not merge sellers unless exact technical variant is identifiable."""
    name = normalize(node.get("productName"))
    brand = next((b for b in BRANDS if re.search(r"\b"+re.escape(b)+r"\b",name)), "")
    cap = CAPACITY.search(name)
    voltage = re.search(r"\b(110|127|220|240)\s?v(?:olts?)?\b", name)
    cycle = "quente-frio" if re.search(r"\bquente e frio\b|\bqf\b", name) else (
        "frio" if re.search(r"\bfrio\b",name) else ""
    )
    # Um anuncio sem codigo completo segue distinto. "12000BTU" ou
    # o numero da loja nunca sao prova de identidade entre vendedores.
    tokens = re.findall(r"\b(?=[a-z0-9]{7,18}\b)(?=[a-z0-9]*[a-z])(?=[a-z0-9]*\d)[a-z0-9]+\b",name)
    model_codes = [t for t in tokens if t not in {"12000btus","9000btus","18000btus",
                   "220volts","127volts","12000btu","9000btu","18000btu"}]
    if brand and cap and voltage and cycle and model_codes:
        return "model:"+"|".join((brand,model_codes[0],normalize(cap.group(1)),
                                  voltage.group(1),cycle))
    return "listing:"+listing_key(node)


def load_history() -> tuple[set[str],set[str]]:
    if not HISTORY_PATH.exists():
        return set(),set()
    doc = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    return set(doc.get("published_listing_keys",[])),set(doc.get("published_identity_keys",[]))


def request_page(app: str, secret: str, keyword: str, page: int) -> dict:
    # Literal keyword parametrizada como STRING GraphQL segura.
    query = (
        "query V31AirconGenericSearch { productOfferV2("
        "keyword:"+json.dumps(keyword,ensure_ascii=False)+
        f", sortType:1, page:{page}, limit:{PAGE_SIZE}) "
        "{ nodes { itemId shopId productName productLink imageUrl "
        "offerLink priceMin ratingStar sales shopName periodEndTime } "
        "pageInfo { page limit hasNextPage } } }"
    )
    body=json.dumps({"query":query,"operationName":"V31AirconGenericSearch"},
                    separators=(",",":"),ensure_ascii=False)
    req=urllib.request.Request(
        ENDPOINT,method="POST",data=body.encode("utf-8"),
        headers={"Authorization":authorization(app,secret,body,int(time.time())),
                 "Content-Type":"application/json","Accept":"application/json",
                 "User-Agent":"V31-Aircon-Generic-ReadOnly/1.0"}
    )
    try:
        with urllib.request.urlopen(req,timeout=23) as resp:
            raw=resp.read(MAX_RESPONSE_BYTES+1)
            if resp.status!=200 or len(raw)>MAX_RESPONSE_BYTES:
                return {"error":"http_or_size","code":str(resp.status)}
        doc=json.loads(raw)
    except urllib.error.HTTPError as exc:
        return {"error":"http","code":str(exc.code)}
    except (urllib.error.URLError,TimeoutError,ValueError,UnicodeDecodeError):
        return {"error":"network_or_json"}
    if not isinstance(doc,dict):
        return {"error":"json_not_object"}
    if doc.get("errors"):
        codes=[str(x.get("extensions",{}).get("code","graphql"))
               for x in doc["errors"] if isinstance(x,dict)]
        return {"error":"graphql","codes":codes[:3]}
    block=(doc.get("data") or {}).get("productOfferV2")
    if not isinstance(block,dict) or not isinstance(block.get("nodes"),list):
        return {"error":"schema"}
    return {"nodes":block["nodes"],"pageInfo":block.get("pageInfo") or {}}


def discover(app: str, secret: str) -> dict:
    known_listings,known_models=load_history()
    seen=set()
    candidates=[]
    traces=[]
    queries=0
    for keyword in (PRIMARY_KEYWORD,*ALTERNATIVE_KEYWORDS):
        if queries>=MAX_QUERIES:
            break
        got_results=False
        for page in range(1,MAX_PAGES_PER_KEYWORD+1):
            if queries>=MAX_QUERIES:
                break
            queries+=1
            data=request_page(app,secret,keyword,page)
            if "error" in data:
                # Pare para rate limit; erro de sistema não é resultado vazio.
                traces.append({"keyword":keyword,"page":page,"error":data["error"],
                               "codes":data.get("codes",[]),"http":data.get("code")})
                if "10030" in data.get("codes",[]) or data.get("code")=="429":
                    return {"status":"RATE_LIMIT","traces":traces,"queries":queries,
                            "candidates":candidates}
                break
            nodes=data["nodes"]
            got_results=got_results or bool(nodes)
            valid=0
            for n in nodes:
                if not valid_listing(n):
                    continue
                valid+=1
                k=listing_key(n)
                if k in seen:
                    continue
                seen.add(k)
                ident=make_identity(n)
                candidates.append({
                    "listing_key":k,"identity_key":ident,
                    "name":str(n["productName"])[:180],
                    "shop_name":str(n.get("shopName") or "")[:100],
                    "is_previously_published_listing":k in known_listings,
                    "may_repeat_published_model":ident in known_models,
                    "product_link":n["productLink"],"image_url":n["imageUrl"],
                    "affiliate_offer_link":n["offerLink"],
                    # Preço apenas para filtro, nunca expor valor como promessa.
                    "stock_confirmed":False,
                    "needs_editorial_model_check":True,
                })
            traces.append({"keyword":keyword,"page":page,"returned":len(nodes),
                           "whole_appliances":valid,"has_next":
                           bool(data["pageInfo"].get("hasNextPage"))})
            if page==1 and valid==0:
                # Ampla encontrou apenas acessorios: nao gastar pagina 2.
                break
            if not nodes or not data["pageInfo"].get("hasNextPage"):
                break
        # Se a busca ampla trouxer produtos elegíveis, usar paginação
        # ao invés de desperdiçar chamadas repetindo a mesma intenção.
        if candidates:
            break
        if got_results:
            # A keyword pode ter trazido só acessórios: tentar sinônimos.
            continue
    novel=[n for n in candidates if not n["is_previously_published_listing"] and
           not n["may_repeat_published_model"]]
    return {"status":"READ_ONLY_CANDIDATES" if novel else
            ("NO_NEW_EDITORIAL_CANDIDATES" if candidates else "NO_VALID_CANDIDATES"),
            "queries":queries,"traces":traces,"candidates":candidates,
            "new_listing_candidates":len(novel),
            "warning":"Affiliate API offer does NOT prove stock; no publishing/conversion."}


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--dry-run",action="store_true")
    args=parser.parse_args()
    if args.dry_run:
        samples=[
          ("Ar Condicionado Split Inverter Midea 18000 BTUs 220V",True),
          ("Ar-condicionado janela Consul 7500 BTUs Frio",True),
          ("Ar condicionado portátil 12000 BTUs Springer",True),
          ("Controle Remoto Ar Condicionado LG",False),
          ("Capa de Ar Condicionado Split 9000 BTUs",False),
          ("Mini Ar Condicionado Climatizador USB",False),
          ("Suporte para Ar Condicionado Split",False),
          ("Ar Condicionado Oribreeze, Resfriador de Ar Portatil",False),
          ("102 Pcs R134A Valvula de Nucleo Ar Condicionado Automotivo",False),
          ("Comando de Ar Condicionado do Painel VW Up",False),
          ("Ar Condicionado Split Inverter Midea 18000 BTUs 220V",True),
          ("Ar Condicionado Janela Consul 7500 BTUs",True),
          ("Ar Condicionado Split Elgin 24000 BTUs",True),
          ("Evaporadora Ar Condicionado Ford Fusion",False),
          ("Caixa Evaporadora ar com Ar Condicionado Peugeot",False),
          ("Conexao de compressor Ar Condicionado Fiat",False),
          ("Moldura Para Ar Condicionado de Janela 30000BTUs",False),
          ("Tira Veda Espuma Para Ar Condicionado Janela Split Portatil 21000BTU",False)
        ]
        for title,expected in samples:
            assert is_whole_air_conditioner(title)==expected,(title,expected)
        print("C93_GENERIC_DISCOVERY_PURE_TEST_PASS")
        return 0
    app=os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID","")
    secret=os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET","")
    if not app or not secret:
        print("C93_MISSING_CREDENTIALS")
        return 2
    result=discover(app,secret)
    path=os.environ.get("V31_AIRCON_CANDIDATE_PATH","").strip()
    if path:
        from datetime import datetime,timezone
        snapshot={
            "site_key":"blogger_ar_condicionado_sem_duvidas",
            "generated_at_utc":datetime.now(timezone.utc).isoformat(),
            "mode":"SAFE_READ_ONLY_REVIEW_NO_PUBLICATION",
            "primary_keyword":PRIMARY_KEYWORD,
            **result,
        }
        Path(path).write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+"\n",
                              encoding="utf-8")
        print("C93_ARTIFACT_WRITTEN="+path)
    print("C93_DISCOVERY_SUMMARY="+json.dumps(
        {k:v for k,v in result.items() if k!="candidates"},ensure_ascii=False))
    for n in result["candidates"][:12]:
        # Não imprimir link de afiliado ou custo privado nos logs.
        print("C93_CANDIDATE="+json.dumps({
            k:n[k] for k in ("listing_key","identity_key","name",
              "is_previously_published_listing","may_repeat_published_model",
              "stock_confirmed","needs_editorial_model_check")
        },ensure_ascii=False))
    print("C93_READ_ONLY_NO_D1_NO_LINK_MUTATION_NO_PUBLICATION")
    return 0 if result["status"] not in ("RATE_LIMIT",) else 3


if __name__=="__main__":
    raise SystemExit(main())
