"""C126: consulta EXATA Shopee itemId (Arctic/Kapbom) e comparação com imagens WP.

Somente GET lógico productOfferV2. Sem generateShortLink, posts ou R2 writes.
Resultados são candidatos, jamais prova do vendedor histórico.
"""
from __future__ import annotations
import io,json,os,pathlib,time,urllib.request,urllib.error,urllib.parse
from PIL import Image,UnidentifiedImageError
import imagehash
from .shopee_probe import ENDPOINT,authorization

ITEMS={
    "29":[("1499661843","22499019427"),("309778123","23498870093"),("344939301","23493283907")],
    "25":[("1634402287","23694616922")],
}
WP_IMAGE={
    "29":"https://radartechbr.com.br/wp-content/uploads/2026/10/Arctic-Air-Cooler-portatil.jpg",
    "25":"https://radartechbr.com.br/wp-content/uploads/2026/10/Caixa-de-som-Kapbom-KA-8955.jpg",
}

def fetch(url,hosts):
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or p.hostname not in hosts:
        return None
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (V31-C126Safe)"})
    try:
        with urllib.request.urlopen(req,timeout=12) as r:
            raw=r.read(4*1024*1024+1)
            if len(raw)>4*1024*1024:return None
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            return im.convert("RGB").copy()
    except (ValueError,UnidentifiedImageError,urllib.error.URLError,OSError,TimeoutError):
        return None

def main():
    app=os.getenv("V31_EDITORIAL_SHOPEE_APP_ID","").strip()
    secret=os.getenv("V31_EDITORIAL_SHOPEE_APP_SECRET","").strip()
    if not app or not secret:raise SystemExit("C126_MISSING_API_CREDS")
    flat=[(post,shop,item) for post,sets in ITEMS.items() for shop,item in sets]
    fields="itemId shopId productName productLink imageUrl offerLink priceMin priceMax ratingStar shopName periodEndTime"
    aliases=" ".join(
       f"p{i}:productOfferV2(itemId:{item},page:1,limit:5){{nodes{{{fields}}}}}"
       for i,(post,shop,item) in enumerate(flat))
    query="query V31C126Exact {"+aliases+"}"
    body=json.dumps({"query":query,"operationName":"V31C126Exact"},separators=(",",":"))
    req=urllib.request.Request(ENDPOINT,data=body.encode(),method="POST",headers={
       "Authorization":authorization(app,secret,body,int(time.time())),
       "Content-Type":"application/json","Accept":"application/json",
       "User-Agent":"V31-C126-Exact-ReadOnly/1.0"})
    try:
       with urllib.request.urlopen(req,timeout=28) as r:
          raw=r.read(160000)
          if r.status!=200:raise RuntimeError("C126_NON200")
       payload=json.loads(raw)
    except urllib.error.HTTPError as e:
       payload={"errors":[{"extensions":{"code":"http_"+str(e.code)}}]}
    except (urllib.error.URLError,TimeoutError,ValueError):
       payload={"errors":[{"extensions":{"code":"transport_or_json"}}]}
    if payload.get("errors"):
       errors=[str(x.get("extensions",{}).get("code","graphql")) for x in payload["errors"]]
       print("C126_GRAPHQL_OR_NETWORK_ERROR="+json.dumps(errors),flush=True)
       data={"status":"API_TEMPORARY_OR_OTHER_ERROR","error_codes":errors,"candidates":[]}
    else:
       response=payload.get("data") or {}
       data={"status":"READ_ONLY_COMPLETED","candidates":[]}
       original={}
       for post,url in WP_IMAGE.items():
          im=fetch(url,{"radartechbr.com.br"})
          original[post]=(
             {"ph":imagehash.phash(im),"dh":imagehash.dhash(im),"ah":imagehash.average_hash(im)}
             if im is not None else None)
       for i,(post,expected_shop,expected_item) in enumerate(flat):
          block=response.get("p"+str(i)) or {}
          records=block.get("nodes",[]) if isinstance(block,dict) else []
          for node in records:
             shop,item=str(node.get("shopId") or ""),str(node.get("itemId") or "")
             if shop!=expected_shop or item!=expected_item:continue
             link=str(node.get("offerLink") or "")
             src=str(node.get("imageUrl") or "")
             pr=str(node.get("productLink") or "")
             if not link.startswith("https://s.shopee.com.br/") or f"/product/{shop}/{item}" not in pr:
                 continue
             entry={"post_id":post,"shop_id":shop,"item_id":item,
                    "title":str(node.get("productName") or "")[:230],
                    "image_url":src,"offer_link":link,"product_url":pr,
                    "shop_name":str(node.get("shopName") or "")[:100],
                    "rating_observed":node.get("ratingStar"),
                    "price_min_observed":node.get("priceMin"),
                    "price_max_observed":node.get("priceMax"),
                    "period_end":node.get("periodEndTime"),
                    "image_distances":None,"visually_identical":False}
             im=fetch(src,{"cf.shopee.com.br","down-br.img.susercontent.com"})
             h=original.get(post)
             if im is not None and h:
                p,d,a=imagehash.phash(im),imagehash.dhash(im),imagehash.average_hash(im)
                distances={"phash":int(p-h["ph"]),"dhash":int(d-h["dh"]),"ahash":int(a-h["ah"])}
                entry["image_distances"]=distances
                entry["visually_identical"]=distances["phash"]<=6 and distances["dhash"]<=9
             data["candidates"].append(entry)
       for post in ITEMS:
          matches=[x for x in data["candidates"] if x["post_id"]==post]
          print("C126_POST="+json.dumps({
            "post_id":post,"exact_candidates":len(matches),
            "strong_visual":sum(x["visually_identical"] for x in matches),
            "summary":[{"item_id":x["item_id"],"title":x["title"][:120],
                        "distance":x["image_distances"],"visual":x["visually_identical"]}
                       for x in matches]
          },ensure_ascii=False),flush=True)
    pathlib.Path("c126_exact_visual_results.json").write_text(
        json.dumps({"schema":"v31-c126-safe/v1","read_only":True,"result":data,
            "warnings":["No stock/price guaranteed from a single API snapshot",
                        "Offer link not yet verified by redirect",
                        "Image similarity does not prove original seller or variant"]},
                   ensure_ascii=False,indent=2),encoding="utf-8")
    print("C126_READ_ONLY_NO_CONVERSION_OR_PUBLICATION",flush=True)

if __name__=="__main__":
    main()
