#!/usr/bin/env python3
"""Consulta SAFE de produtos reais Shopee para artigos/Loja do Violão do Começo V31.

Somente leitura de API Shopee. Nenhuma escrita Blogger. Sem credenciais em relatórios.
"""
from __future__ import annotations
import hashlib, html, json, os, sys, time, unicodedata
import urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from blogger_policy_guard import require_product_allowed

EXPECTED_BLOG_ID="370856880185231084"
CATS=(
  ("Cordas de Violão",("encordoamento violao nylon","cordas para violao nylon","jogo de cordas violao"),("corda","encordoamento")),
  ("Afinadores",("afinador cromatico violao","afinador digital violao","afinador clip violao"),("afinador","afinacao")),
  ("Capotrastes e Palhetas",("capotraste violao","palhetas para violao","capo traste violao"),("capotraste","capo traste","palheta")),
  ("Capas e Suportes",("capa violao acolchoada","suporte violao chao","suporte violao parede"),("capa","bag","suporte","case")),
)
API="https://open-api.affiliate.shopee.com.br/graphql"
OUT=ROOT/"violao_do_comeco"/"catalogo_shopee_safe.json"

def norm(s):
    s=unicodedata.normalize("NFKD",str(s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))

def query(app,secret,keyword,page):
    qry=("query ViolaoComeco { productOfferV2(keyword: "+
         json.dumps(keyword,ensure_ascii=False)+
         ", sortType: 2, page: "+str(page)+
         ", limit: 20) { nodes { itemId productName imageUrl offerLink priceMin priceMax shopName ratingStar sales } pageInfo { page hasNextPage } } }")
    body=json.dumps({"query":qry,"operationName":"ViolaoComeco"},separators=(",",":"),ensure_ascii=False)
    ts=int(time.time())
    sig=hashlib.sha256((app+str(ts)+body+secret).encode()).hexdigest()
    headers={"Authorization":"SHA256 Credential="+app+", Timestamp="+str(ts)+", Signature="+sig,
             "Content-Type":"application/json","Accept":"application/json"}
    req=urllib.request.Request(API,data=body.encode("utf8"),method="POST",headers=headers)
    with urllib.request.urlopen(req,timeout=30) as resp:
        if resp.status!=200:raise RuntimeError("Shopee HTTP !=200")
        payload=json.load(resp)
    if payload.get("errors"):raise RuntimeError("Shopee GraphQL error")
    nodes=(payload.get("data") or {}).get("productOfferV2") or {}
    if not isinstance(nodes.get("nodes"),list):raise RuntimeError("Shopee invalid nodes")
    return nodes["nodes"]

def product(raw,label,tokens):
    try:
        ident=str(raw.get("itemId") or "").strip()
        name=str(raw.get("productName") or "").strip()
        image=str(raw.get("imageUrl") or "").strip()
        link=str(raw.get("offerLink") or "").strip()
        price=float(raw.get("priceMin") or 0)
        if not (ident.isdecimal() and name and image.startswith("https://") and
            link.startswith("https://") and 0 < price < 100000):
            return None
        if not any(token in norm(name) for token in tokens):return None
        n=norm(name)
        excluded=("ukulele","cavaquinho","violino","violoncelo","teclado","piano","baixo eletrico","contra baixo","brinquedo","infantil","adesivo","enfeite","decorativo","maquiagem","mouse pad","guitarra eletrica","chaveiro")
        if any(term in n for term in excluded):return None
        if label in ("Cordas de Violão","Capotrastes e Palhetas","Capas e Suportes") and "violao" not in n:return None
        if label=="Afinadores" and "afinador" not in n:return None
        item={"itemId":ident,"productName":name,"imageUrl":image,"offerLink":link,
              "priceMin":round(price,2),"category":label}
        require_product_allowed(item)
        return item
    except (ValueError,TypeError,RuntimeError):return None

def main():
    app=os.getenv("SHOPEE_APP_ID","").strip()
    secret=os.getenv("SHOPEE_SECRET","").strip()
    if not app or not secret:raise RuntimeError("Credenciais Shopee ausentes")
    selected={}
    used=set()
    for label, keywords, tokens in CATS:
        pool={}
        for keyword in keywords:
            for page in (1,2):
                time.sleep(1.2)  # ritmo conservador da API oficial
                try:
                    items=query(app,secret,keyword,page)
                except RuntimeError as err:
                    if "GraphQL" not in str(err):raise
                    time.sleep(5)  # uma repetição limitada; falha fechada em erro persistente
                    items=query(app,secret,keyword,page)
                for row in items:
                    item=product(row,label,tokens)
                    if item:pool[item["itemId"]]=item
                if len(pool)>=6:break
            if len(pool)>=6:break
        candidates=sorted(pool.values(),key=lambda p:p["itemId"])
        choice=[]
        for item in candidates:
            if item["itemId"] in used:continue
            choice.append(item)
            used.add(item["itemId"])
            if len(choice)==4:break
        if len(choice)!=4:raise RuntimeError("FAIL_CLOSED: fewer than 4 valid items in "+label)
        selected[label]=choice
        print("SAFE_CATEGORY_OK",label,"products",len(choice),flush=True)
    if len(used)!=16:raise RuntimeError("FAIL_CLOSED: duplicate or missing products")
    # Dados de ofertas são públicos; o arquivo não inclui AppID/secret/tokens.
    report={"status":"SAFE_SHOPEE_API_PASS_NO_BLOGGER_WRITE",
      "blog_id":EXPECTED_BLOG_ID,"timestamp_utc":datetime.now(timezone.utc).isoformat(),
      "count":16,"category_counts":{k:len(v) for k,v in selected.items()},
      "products":selected}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    for label, products in selected.items():
        for p in products:
            print("SAFE_PRODUCT " + json.dumps(p, ensure_ascii=False, separators=(",", ":")), flush=True)
    print("SAFE_SHOPEE_API_PASS_NO_BLOGGER_WRITE 16 products for Violão do Começo",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("SAFE_SHOPEE_STOP",type(e).__name__,str(e)[:170],flush=True)
        raise SystemExit(2)
