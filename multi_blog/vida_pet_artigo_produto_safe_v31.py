#!/usr/bin/env python3
"""Consulta Shopee SAFE para UMA pauta nova do Vida Pet Prática; não altera Blogger."""
import hashlib, json, os, time, urllib.request, urllib.error
from urllib.parse import urlparse

API="https://open-api.affiliate.shopee.com.br/graphql"
BLOG_ID="8052455848487624244"
KEYWORDS=["tapete lamber cachorro","tapete de lamber pet silicone","lick mat cachorro"]
def main():
    app=os.getenv("SHOPEE_APP_ID","").strip();secret=os.getenv("SHOPEE_SECRET","").strip()
    if not app or not secret: raise SystemExit("FAIL_CLOSED: CREDENCIAIS_AUSENTES")
    seen=set();found=[]
    for term in KEYWORDS:
        gql="query SafePetV31 { productOfferV2(keyword: "+json.dumps(term,ensure_ascii=False)+", sortType: 2, page: 1, limit: 20) { nodes { itemId productName imageUrl offerLink priceMin shopName } } }"
        body=json.dumps({"query":gql,"operationName":"SafePetV31"},separators=(",",":"),ensure_ascii=False)
        timestamp=str(int(time.time()))
        signature=hashlib.sha256((app+timestamp+body+secret).encode()).hexdigest()
        auth="SHA256 Credential="+app+", Timestamp="+timestamp+", Signature="+signature
        request=urllib.request.Request(API,method="POST",data=body.encode(),headers={"Authorization":auth,"Content-Type":"application/json","Accept":"application/json"})
        try:
            with urllib.request.urlopen(request,timeout=32) as response:
                if response.status!=200:raise RuntimeError("HTTP_NOT_200")
                data=json.load(response)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as exc:
            print("SAFE_PET_QUERY_UNAVAILABLE",term,type(exc).__name__,flush=True);continue
        if data.get("errors"):
            codes=[str((e.get("extensions") or {}).get("code")) for e in data["errors"][:2]]
            print("SAFE_PET_QUERY_GRAPHQL_ERROR",term,codes,flush=True);continue
        offers=((data.get("data") or {}).get("productOfferV2") or {}).get("nodes") or []
        for p in offers:
            iid=str(p.get("itemId") or "")
            title=str(p.get("productName") or "").strip()
            check=title.casefold()
            link=str(p.get("offerLink") or "")
            img=str(p.get("imageUrl") or "")
            try: price=float(p.get("priceMin") or 0)
            except (ValueError,TypeError):continue
            host=urlparse(link).hostname or ""
            img_host=urlparse(img).hostname or ""
            if (iid.isdecimal() and iid not in seen and 0 < price <= 400 and
                any(w in check for w in ("lamber","lambed","lick")) and
                any(w in check for w in ("cachorro","cães","cao","pet","gato","animal")) and
                host in {"s.shopee.com.br","shopee.com.br","www.shopee.com.br"} and
                img.startswith("https://") and
                (img_host.endswith(".shopee.com.br") or img_host in {"cf.shopee.com.br","down-br.img.susercontent.com"})):
                seen.add(iid)
                found.append({"blog_id":BLOG_ID,"id":iid,"name":title,"price":price,"image":img,"affiliate":link})
        print("SAFE_PET_TERM",term,"valid_total",len(found),flush=True)
        if len(found)>=3: break
    if not found:raise SystemExit("FAIL_CLOSED: SEM_PRODUTO_PET_VALIDO")
    for row in found[:5]: print("SAFE_PET_CANDIDATE",json.dumps(row,ensure_ascii=False),flush=True)
    print("SAFE_PET_CATALOG_PASS",len(found),flush=True)
if __name__=="__main__":main()
