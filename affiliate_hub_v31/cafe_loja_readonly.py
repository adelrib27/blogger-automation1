"""C96 Café na Medida — curadoria Shopee READ ONLY, sem shortlinks nem CMS.

Não altera D1/R2, não cria produtos e não comprova disponibilidade de estoque.
Apenas oferece shortlist com imagem exata do anúncio e offerLink da conta.
"""
from __future__ import annotations
import json, math, os, re, time, unicodedata, urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from affiliate_hub_v31.aircon_discovery import request_page as aircon_request_page
from affiliate_hub_v31.shopee_probe import ENDPOINT, authorization
import urllib.request, urllib.error

KEYWORDS = [
    ("Moedores", "moedor de cafe"),
    ("Italianas", "cafeteira italiana"),
    ("Prensas francesas", "prensa francesa"),
    ("Coadores", "coador de cafe"),
    ("Cafeteiras espresso", "cafeteira espresso"),
    ("Chaleiras", "chaleira para cafe"),
    ("Balancas", "balanca digital cafe"),
    ("Espumadores", "espumador de leite"),
    ("Conservacao", "pote hermetico cafe"),
    ("Canecas termicas", "copo termico cafe"),
    ("Porta filtros", "porta filtro cafe"),
    ("Cafe em graos", "cafe especial graos"),
    ("Garrafas termicas", "garrafa termica cafe"),
    ("Cafeteiras eletricas", "cafeteira eletrica"),
]
MAX_CALLS = 16
MAX_RAW = 350_000
MAX_SELECTED = 40
MAX_PER_CATEGORY = 5
MAX_PER_SHOP = 3
BLOCKED = ("brinquedo", "miniatura", "adesivo", "fantasia", "boneco",
           "chaveiro", "camiseta", "camisa", "roupa", "caneca decorativa",
           "papel de parede", "display digital", "placa decorativa",
           "protetor de tela", "liquidificador", "pincel", "tinta",
           "capinha", "adesivo", "mascara facial", "sabonete",
           "maquina de costura", "capa para", "enfeite")
FIELDS = ("itemId shopId productName productLink imageUrl offerLink "
          "priceMin ratingStar sales shopName shopType periodEndTime "
          "commissionRate sellerCommissionRate shopeeCommissionRate commission")

def norm(v):
    v=unicodedata.normalize("NFKD",str(v or "").lower())
    v="".join(c for c in v if not unicodedata.combining(c))
    return re.sub(r"\s+"," ",re.sub("[^a-z0-9]+"," ",v)).strip()

def category_match(category, title):
    t=norm(title)
    if any(b in t for b in BLOCKED):
        return False
    if category=="Moedores": return ("moedor" in t or "moinho" in t) and ("cafe" in t or "graos" in t)
    if category=="Italianas": return ("cafeteira" in t or "moka" in t) and ("italiana" in t or "moka" in t)
    if category=="Prensas francesas": return "prensa francesa" in t or "french press" in t
    if category=="Coadores": return ("coador" in t or "dripper" in t) and ("cafe" in t or "v60" in t or "102" in t)
    if category=="Cafeteiras espresso": return "cafeteira" in t and ("espresso" in t or "expresso" in t)
    if category=="Chaleiras": return "chaleira" in t and ("cafe" in t or "bico" in t or "eletrica" in t)
    if category=="Balancas": return "balanca" in t and ("cafe" in t or "cozinha" in t or "precisao" in t or "digital" in t)
    if category=="Espumadores": return "espumador" in t and ("leite" in t or "cafe" in t)
    if category=="Conservacao": return ("pote" in t or "recipiente" in t) and ("cafe" in t or "hermetico" in t)
    if category=="Canecas termicas": return ("copo termico" in t or "caneca termica" in t) and "cafe" in t
    if category=="Porta filtros": return "porta" in t and "filtro" in t and "cafe" in t
    if category=="Cafe em graos": return "cafe" in t and ("graos" in t or "grao" in t)
    if category=="Garrafas termicas": return "garrafa termica" in t and ("cafe" in t or "inox" in t)
    if category=="Cafeteiras eletricas": return "cafeteira" in t and ("eletrica" in t or "programavel" in t or "digital" in t)
    return False

def rate(v):
    try:
        v=float(str(v or "0").replace(",",".").replace("%",""))
        return v/100.0 if v>1 else max(0.0,v)
    except ValueError: return 0.0

def num(v):
    try: return float(str(v or "0").replace(",","."))
    except ValueError: return 0.0

def call(app, secret, category, keyword, sort_type=5):
    params="keyword:"+json.dumps(keyword,ensure_ascii=False)+f", sortType:{sort_type}, page:1, limit:30"
    if sort_type==5: params+=", listType:1"
    query="query V31CafeReadonly { productOfferV2("+params+") { nodes { "+FIELDS+" } pageInfo { page limit hasNextPage } } }"
    body=json.dumps({"query":query,"operationName":"V31CafeReadonly"},ensure_ascii=False,separators=(",",":"))
    req=urllib.request.Request(ENDPOINT, method="POST",data=body.encode("utf-8"),headers={
        "Authorization":authorization(app,secret,body,int(time.time())),
        "Content-Type":"application/json","Accept":"application/json","User-Agent":"V31-Cafe-Store-Readonly/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=24) as response:
            raw=response.read(MAX_RAW+1)
            if len(raw)>MAX_RAW: return [], "response_too_large"
        doc=json.loads(raw)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return [],"transport_or_json"
    if doc.get("errors"):
        return [],"graphql:"+",".join(str(x.get("extensions",{}).get("code","?")) for x in doc["errors"][:2])
    block=(doc.get("data") or {}).get("productOfferV2")
    if not isinstance(block,dict) or not isinstance(block.get("nodes"),list):
        return [],"schema"
    return block["nodes"],None

def validate(n, category):
    if not isinstance(n,dict) or not category_match(category,n.get("productName")): return None
    shop,item=str(n.get("shopId") or ""),str(n.get("itemId") or "")
    if not shop.isdigit() or not item.isdigit() or int(shop)<1 or int(item)<1: return None
    link=str(n.get("productLink") or "")
    u=urllib.parse.urlsplit(link)
    if u.scheme!="https" or u.hostname!="shopee.com.br" or f"/product/{shop}/{item}" not in u.path: return None
    offer=str(n.get("offerLink") or "")
    o=urllib.parse.urlsplit(offer)
    if o.scheme!="https" or o.hostname not in ("s.shopee.com.br","shope.ee","shopee.com.br"): return None
    img=str(n.get("imageUrl") or "")
    i=urllib.parse.urlsplit(img)
    if i.scheme!="https" or not i.hostname or not (
        i.hostname.endswith(".shopee.com.br") or i.hostname.endswith(".susercontent.com") or
        i.hostname in ("cf.shopee.com.br","down-br.img.susercontent.com")
    ): return None
    if num(n.get("priceMin"))<=0: return None
    if num(n.get("ratingStar"))<4.0: return None
    if num(n.get("sales"))<10: return None
    end=int(num(n.get("periodEndTime")))
    if end>0 and end<int(time.time()): return None
    total,seller=rate(n.get("commissionRate")),rate(n.get("sellerCommissionRate"))
    amount=num(n.get("commission"))
    # Comissão extra do vendedor e valor por pedido, com peso para reputação e demanda.
    score=(total*65+seller*100+min(amount,40)*0.19
           +min(num(n.get("ratingStar")),5)*1.2
           +min(math.log1p(num(n.get("sales"))),12)*0.35
           + (2 if seller>=0.03 else 0))
    return {"category":category,"shopId":shop,"itemId":item,
            "name":str(n.get("productName") or "")[:170],
            "image":img,"offer":offer,"product":link,"shopName":str(n.get("shopName") or "")[:90],
            "shopType":str(n.get("shopType") or ""),
            "rating":num(n.get("ratingStar")),"sales":int(num(n.get("sales"))),
            "commissionRate":total,"sellerCommissionRate":seller,
            "commissionEstimate":amount,"score":round(score,4)}

def run():
    app=os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID","")
    secret=os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET","")
    if not (app and secret): raise RuntimeError("Missing Shopee environment credentials")
    all_by_cat=defaultdict(list)
    seen=set()
    errors=[]
    calls=0
    for cat,keyword in KEYWORDS:
        if calls>=MAX_CALLS: break
        calls+=1
        nodes,err=call(app,secret,cat,keyword,5)
        # Falhas momentâneas não representam catálogo vazio.
        if err and ("10000" in err or "graphql:?" in err):
            time.sleep(1.0)
            calls+=1
            nodes,err=call(app,secret,cat,keyword,1)
        if err:
            errors.append({"category":cat,"code":err})
            if "10030" in err or "429" in err: break
            continue
        for n in nodes:
            valid=validate(n,cat)
            if valid and (valid["shopId"],valid["itemId"]) not in seen:
                seen.add((valid["shopId"],valid["itemId"]))
                all_by_cat[cat].append(valid)
        time.sleep(.3)
    for cat in all_by_cat:
        all_by_cat[cat].sort(key=lambda n:n["score"],reverse=True)
    selected=[]
    shops=Counter()
    keys=set()
    for rank in range(MAX_PER_CATEGORY):
        for cat,_ in KEYWORDS:
            if len(selected)>=MAX_SELECTED: break
            for n in all_by_cat[cat]:
                if n["shopId"] in shops and shops[n["shopId"]]>=MAX_PER_SHOP: continue
                k=(n["shopId"],n["itemId"])
                if k in keys: continue
                # A seleção prioriza alto score, mas distribui itens por categoria.
                if len([x for x in selected if x["category"]==cat])>=rank+1: break
                selected.append(n)
                shops[n["shopId"]]+=1
                keys.add(k)
                break
    meta={"generated_at":datetime.now(timezone.utc).isoformat(),"mode":"SHOPEE_READ_ONLY",
          "requests":calls,"errors":errors,"available_category_counts":{c:len(all_by_cat[c]) for c,_ in KEYWORDS},
          "total_unique_candidates":len(seen),"selected_count":len(selected),
          "commissions_are_estimates_not_guaranteed":True,
          "stock_confirmed":False,"campaign_subid_present":False}
    print("C96_META="+json.dumps(meta,ensure_ascii=False,separators=(",",":")))
    for n in selected:
        print("C96_OFFER="+json.dumps(n,ensure_ascii=False,separators=(",",":")))
    if len(selected)<24:
        print("C96_INSUFFICIENT_VERIFIED_OFFERS; NO CMS CHANGE.")
        return 3
    print("C96_READ_ONLY_SUCCESS_NO_CONVERSION_NO_PUBLICATION")
    return 0

if __name__=="__main__":
    raise SystemExit(run())
