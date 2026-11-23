"""C123: quatro pesquisas direcionadas na Shopee Affiliate Open API.

Não converte links, não publica, não grava no R2 e não usa credenciais fora
do ambiente seguro do GitHub. Resultados exigem revisão de identidade.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from .shopee_probe import ENDPOINT, authorization

QUERIES = (
    ("29", "Arctic Air Cooler"),
    ("28", "scanner OBD2 Bluetooth"),
    ("25", "Kapbom KA-8955"),
    ("24", "Luz RGB portátil LED 3200K"),
)
LIMIT = 25
MAX_BYTES = 200_000

def normalize(value):
    s=unicodedata.normalize("NFKD",str(value or "").lower())
    s="".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]","",s)

def identity_hint(post_id, name):
    n=normalize(name)
    if post_id=="29":
        return "MODEL_TERMS" if "arctic" in n and "cooler" in n else "AMBIGUOUS"
    if post_id=="28":
        return "MODEL_TERMS" if ("obd2" in n or "elm327" in n) and "bluetooth" in n else "AMBIGUOUS"
    if post_id=="25":
        return "MODEL_TERMS" if "kapbom" in n and "ka8955" in n else "AMBIGUOUS"
    if post_id=="24":
        return "MODEL_TERMS" if "rgb" in n and "3200" in n and "6500" in n else "AMBIGUOUS"
    return "AMBIGUOUS"

def verify_node(n):
    try:
        shop,item=str(n.get("shopId") or ""),str(n.get("itemId") or "")
        url=str(n.get("productLink") or "")
        affiliate=str(n.get("offerLink") or "")
        image=str(n.get("imageUrl") or "")
        product=urllib.parse.urlsplit(url)
        offer=urllib.parse.urlsplit(affiliate)
        picture=urllib.parse.urlsplit(image)
        return (shop.isdigit() and item.isdigit()
                and product.scheme=="https" and product.hostname=="shopee.com.br"
                and f"/product/{shop}/{item}" in product.path
                and offer.scheme=="https" and offer.hostname in ("s.shopee.com.br","shopee.com.br","shope.ee")
                and picture.scheme=="https" and bool(picture.hostname))
    except (ValueError,TypeError,AttributeError):
        return False

def one_query(app,secret,post_id,keyword):
    query=("query V31C123RadarFour { productOfferV2("
           "keyword:"+json.dumps(keyword,ensure_ascii=False)
           +f", sortType:1, page:1, limit:{LIMIT}) "
           "{nodes{itemId shopId productName productLink imageUrl offerLink "
           "priceMin priceMax ratingStar shopName commissionRate "
           "periodEndTime} pageInfo{page limit hasNextPage}} }")
    body=json.dumps({"query":query,"operationName":"V31C123RadarFour"},separators=(",",":"),ensure_ascii=False)
    req=urllib.request.Request(ENDPOINT,method="POST",data=body.encode("utf-8"),
       headers={"Authorization":authorization(app,secret,body,int(time.time())),
                "Content-Type":"application/json","Accept":"application/json",
                "User-Agent":"V31-C123-Radar-ReadOnly/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            data=r.read(MAX_BYTES+1)
            if r.status!=200 or len(data)>MAX_BYTES:
                return {"status":"HTTP_OR_SIZE_ERROR"}
        doc=json.loads(data)
    except urllib.error.HTTPError as e:
        return {"status":"HTTP_ERROR","http_code":e.code}
    except (urllib.error.URLError,TimeoutError,ValueError,UnicodeDecodeError):
        return {"status":"NETWORK_OR_JSON_ERROR"}
    if doc.get("errors"):
        codes=[str(e.get("extensions",{}).get("code","graphql"))
               for e in doc.get("errors",[]) if isinstance(e,dict)]
        return {"status":"GRAPHQL_ERROR","codes":codes[:4]}
    block=(doc.get("data") or {}).get("productOfferV2")
    if not isinstance(block,dict) or not isinstance(block.get("nodes"),list):
        return {"status":"SCHEMA_ERROR"}
    accepted=[]
    for n in block["nodes"]:
        if not isinstance(n,dict) or not verify_node(n):
            continue
        try:
            expired=int(n.get("periodEndTime") or 0)>0 and int(n["periodEndTime"])<int(time.time())
        except (TypeError,ValueError):
            expired=True
        accepted.append({
            "shop_id":str(n["shopId"]),"item_id":str(n["itemId"]),
            "title":str(n.get("productName") or "")[:240],
            "product_url":n["productLink"],"offer_link":n["offerLink"],
            "image_url":n["imageUrl"],"shop_name":str(n.get("shopName") or "")[:100],
            "price_min_observed":n.get("priceMin"),"price_max_observed":n.get("priceMax"),
            "rating_observed":n.get("ratingStar"),"commission_observed":n.get("commissionRate"),
            "period_end":n.get("periodEndTime"),"expired":expired,
            "identity_hint":identity_hint(post_id,n.get("productName"))
        })
    accepted.sort(key=lambda n:(n["identity_hint"]!="MODEL_TERMS", n["expired"],n["title"]))
    return {"status":"READ_ONLY_CANDIDATES", "keyword":keyword,
            "returned_count":len(block["nodes"]), "validated_records":len(accepted),
            "has_next_page":bool((block.get("pageInfo") or {}).get("hasNextPage")),
            "exact_model_hints":sum(n["identity_hint"]=="MODEL_TERMS" for n in accepted),
            "records":accepted[:20]}

def main():
    app=os.getenv("V31_EDITORIAL_SHOPEE_APP_ID","").strip()
    secret=os.getenv("V31_EDITORIAL_SHOPEE_APP_SECRET","").strip()
    if not app or not secret:
        raise SystemExit("C123_CREDENTIALS_MISSING")
    result={}
    for i,(post_id,keyword) in enumerate(QUERIES):
        if i:
            time.sleep(2)
        result[post_id]=one_query(app,secret,post_id,keyword)
        status=result[post_id]["status"]
        print("C123_POST="+json.dumps({
            "id":post_id,"keyword":keyword,"status":status,
            "returned_count":result[post_id].get("returned_count"),
            "valid":result[post_id].get("validated_records"),
            "model_hints":result[post_id].get("exact_model_hints"),
            "error_codes":result[post_id].get("codes")
        },ensure_ascii=False),flush=True)
        if status in ("GRAPHQL_ERROR","HTTP_ERROR") and (
            "10030" in result[post_id].get("codes",[]) or
            result[post_id].get("http_code")==429):
            print("C123_STOP_RATE_LIMIT_OR_ACCOUNT_LIMIT",flush=True)
            for later_id,_ in QUERIES[i+1:]:
                result[later_id]={"status":"NOT_QUERIED_RATE_LIMIT"}
            break
    pathlib.Path("c123_radar_four_shopee_candidates.json").write_text(
        json.dumps({"schema":"v31-c123-shopee-readonly/v1",
                    "not_verified_to_be_the_original_products":True,
                    "campaign_required":"radarwp",
                    "offer_link_affiliate_account_must_be_checked":True,
                    "data":result},ensure_ascii=False,indent=2),encoding="utf-8")
    print("C123_READONLY_NO_CONVERSION_NO_PUBLICATION",flush=True)

if __name__=="__main__":
    main()
