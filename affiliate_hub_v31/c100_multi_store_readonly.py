"""V31 C100 — consulta real à Shopee Affiliate API, sem nenhuma escrita.

Seleciona uma shortlist por tema para páginas Loja vazias. A saída é
uma PROPOSTA revisável; não prova estoque, SubID, margem líquida ou vendas.
"""
from __future__ import annotations
import argparse, json, math, re, time, urllib.parse
from pathlib import Path
from affiliate_hub_v31.cafe_loja_readonly import call, num, rate, norm

CONFIG = Path(__file__).with_name("c100_store_profiles.json")
MIN_RATING = 4.0
MIN_SALES = 10
MAX_PER_SHOP = 2
MAX_OFFERS = 36
MAX_QUERIES = 12
NEGATIVE_GENERIC = (
    "miniatura", "boneca", "brinquedo", "infantil", "crianca", "bebe", "fantasia",
    "capa protetora", "peca de reposicao", "refil avulso", "reposicao",
    "conserto", "manual pdf", "adesivo", "papel de parede", "cartaz",
)
NEGATIVE_APPLIANCE = (
    "copo avulso", "jarra avulsa", "tampa avulsa", "tampa para",
    "cesto avulso", "forma de silicone", "forma papel", "papel para",
    "grade de reposicao", "suporte para", "motor de reposicao",
    "alca avulsa", "acoplamento", "rotor", "resistencia para",
    "capacitor", "placa eletrica para", "helice avulsa",
    "capa para", "filtro de reposicao", "lampada para",
    "pecas para", "pinca para", "protetor para", "controle remoto",
    "ventilador veicular", "ventilador automotivo", "ventilador usb",
    "ventilador mini de mao", "air fryer de brinquedo",
)
PRIORITY_APPLIANCE = {"liquidificadores", "eletroportateis", "air_fryers", "ventiladores", "limpeza"}

def listing_valid(n, name, positive, site_key):
    if not isinstance(n,dict): return None
    title=str(n.get("productName") or "")
    t=norm(title)
    if len(t)<10 or any(x in t for x in NEGATIVE_GENERIC): return None
    if site_key in PRIORITY_APPLIANCE and any(x in t for x in NEGATIVE_APPLIANCE):
        return None
    if site_key=="cozinha_sem_complicacao" and "air fryer" in t:
        if any(z in t for z in ("tapete", "silicone", "forma", "papel", "grelha", "cesto", "protetor", "assadeira", "manta", "kit de acessorios")): return None
    if site_key=="air_fryers" and ("air fryer" in t or "fritadeira" in t):
        if any(z in t for z in ("tapete", "forma", "cesto", "grade", "papel", "silicone", "kit acessorios", "assadeira", "pelicula", "espeto", "grelha", "aluminio descartavel")): return None
        if not any(z in t for z in ("eletrica", "digital", "inox", "litro", "oven", "fritadeira", "britania", "mondial", "philco", "midea", "electrolux", "arno", "oster")): return None
    if site_key=="ventiladores":
        if any(z in t for z in ("helice", "grade", "motor", "componente", "peca", "ponta", "chave", "passador", "mini ventilador", "portatil usb", "clip", "clipe")): return None
    if site_key=="liquidificadores":
        if any(z in t for z in ("copo", "jarra", "lamina", "faca", "acoplamento", "tampa", "tampa", "peca", "motor")): return None
    if site_key in ("moda_ofertas","estilo_dia"):
        if any(z in t for z in ("masculino", "infantil", "menino", "menina", "para bebe", "roupa de boneca", "pijama infantil")): return None
    if site_key in ("achadinhos_beleza","cabelos"):
        if any(z in t for z in ("refil", "suporte de parede", "kit acessorios", "pente para", "acessorio", "para prancha", "para secador", "resistencia", "cabo reposicao", "motor", "escova dental")): return None
    try:
        if not re.search(r"\b(?:"+positive+r")\b", t): return None
    except re.error: return None
    shop,item=str(n.get("shopId") or ""),str(n.get("itemId") or "")
    if not shop.isdigit() or not item.isdigit() or int(shop)<1 or int(item)<1: return None
    image=str(n.get("imageUrl") or "")
    im=urllib.parse.urlsplit(image)
    if im.scheme!="https" or not (im.hostname or "").endswith(("shopee.com.br","susercontent.com")):
        return None
    origin=str(n.get("productLink") or "")
    u=urllib.parse.urlsplit(origin)
    if u.scheme!="https" or u.hostname!="shopee.com.br" or f"/product/{shop}/{item}" not in u.path:
        return None
    offer=str(n.get("offerLink") or "")
    a=urllib.parse.urlsplit(offer)
    if a.scheme!="https" or a.hostname not in ("s.shopee.com.br","shope.ee","shopee.com.br"): return None
    price=num(n.get("priceMin"));rating=num(n.get("ratingStar"));sales=num(n.get("sales"))
    if price<=0 or rating<MIN_RATING or sales<MIN_SALES: return None
    try: deadline=int(n.get("periodEndTime") or 0)
    except (ValueError,TypeError): deadline=0
    if deadline and deadline<int(time.time()): return None
    seller_rate=rate(n.get("sellerCommissionRate"))
    total_rate=rate(n.get("commissionRate"))
    amount=num(n.get("commission"))
    score=round(
        seller_rate*70 + total_rate*55 +
        min(amount,40)*0.27 + rating*1.3 + min(math.log1p(sales),12)*.4 +
        (2.0 if seller_rate>=.03 else 0) +
        (1.0 if "mall" in str(n.get("shopType") or "").lower() else 0),
        3
    )
    return {
        "shopId":shop,"itemId":item,"listing_key":f"{shop}:{item}",
        "name":title[:180],"image":image,"offer":offer,"origin":origin,
        "shop":str(n.get("shopName") or "")[:90],
        "shopType":str(n.get("shopType") or "")[:30],
        "rating":rating,"sales":int(sales),
        "sellerCommissionRate":seller_rate,
        "commissionRate":total_rate,
        "commissionEstimate":amount,
        "score":score,
        "category":name
    }

def discover_site(site, app, secret):
    result={}
    events=[]
    total_calls=0
    for name, keyword, pattern in site["groups"]:
        found=[]
        exhausted=False
        for sort_mode in (1,5):
            if total_calls>=MAX_QUERIES: break
            nodes,err=call(app,secret,name,keyword,sort_mode)
            total_calls+=1
            if err:
                events.append({"category":name,"keyword":keyword,"sort_mode":sort_mode,"error":err})
                if "10030" in err or "429" in err:
                    exhausted=True
                    break
                time.sleep(.35)
                continue
            accepted=0
            for n in nodes:
                candidate=listing_valid(n,name,pattern,site["key"])
                if candidate:
                    found.append(candidate)
                    accepted+=1
            events.append({"category":name,"keyword":keyword,"sort_mode":sort_mode,
                           "received":len(nodes),"accepted":accepted})
            if sort_mode==1 and accepted>=22:
                # Bastante variedade já disponível; evitar chamada redundante.
                break
            time.sleep(.20)
        result[name]=found
        if exhausted or total_calls>=MAX_QUERIES: break
    clean={}
    for name,products in result.items():
        for p in products:
            k=p["listing_key"]
            if k not in clean or p["score"]>clean[k]["score"]:
                clean[k]=p
    groups={name:[] for name,_,_ in site["groups"]}
    for p in clean.values():
        groups[p["category"]].append(p)
    for cat in groups:
        groups[cat].sort(key=lambda x:x["score"],reverse=True)
    selected=[];used=set();names=set();shops={}
    # Uma rodada de cada categoria, depois outras rodadas, evitando que
    # apenas uma categoria ocupe a Loja.
    for pass_num in range(12):
        for cat in groups:
            if len(selected)>=MAX_OFFERS: break
            if len([x for x in selected if x["category"]==cat])>pass_num: continue
            for p in groups[cat]:
                k=p["listing_key"]
                normalized=norm(p["name"])
                if k in used or normalized in names or shops.get(p["shopId"],0)>=MAX_PER_SHOP:
                    continue
                if len([x for x in selected if x["category"]==cat])<pass_num: continue
                selected.append(p);used.add(k);names.add(normalized)
                shops[p["shopId"]]=shops.get(p["shopId"],0)+1
                break
    status="READ_ONLY_READY_24_PLUS" if len(selected)>=24 else (
        "PARTIAL_API_ERRORS" if any("error" in e for e in events) else "INSUFFICIENT_QUALIFIED_OFFERS"
    )
    return {
        "status":status,"site_key":site["key"],"blog_id":site["blog"],"page_id":site["page"],
        "site_title":site["title"],"requests":total_calls,"traces":events,
        "unique_valid_offers":len(clean),"selected_count":len(selected),
        "unique_sellers":len(shops),
        "seller_extra_ge_3pct":sum(x["sellerCommissionRate"]>=.03 for x in selected),
        "stock_confirmed":False,"subid_confirmed":False,
        "offer_links_mutated":False,"products":selected
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--sites",required=True,help="site keys separated by comma")
    args=parser.parse_args()
    config=json.loads(CONFIG.read_text(encoding="utf-8"))
    keys={x.strip() for x in args.sites.split(",") if x.strip()}
    profiles=[s for s in config["sites"] if s["key"] in keys]
    if not profiles or keys!={s["key"] for s in profiles}: raise SystemExit("Invalid site_keys")
    import os
    app=os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID","")
    secret=os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET","")
    if not app or not secret: raise SystemExit("Shopee credential env missing")
    batch=[]
    for site in profiles:
        data=discover_site(site,app,secret)
        safe={k:v for k,v in data.items() if k!="products"}
        print("C100_SITE="+json.dumps(safe,ensure_ascii=False,separators=(",",":")))
        for p in data["products"]:
            print("C100_OFFER="+json.dumps({"site_key":site["key"],**p},ensure_ascii=False,separators=(",",":")))
        batch.append({"site_key":site["key"],**data})
        time.sleep(.4)
    target=os.environ.get("V31_C100_OUTPUT","c100_sites.json")
    Path(target).write_text(json.dumps(batch,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("C100_READ_ONLY_NO_CONVERSION_NO_CMS_WRITES")
    print("C100_READY_COUNT="+str(sum(x["status"]=="READ_ONLY_READY_24_PLUS" for x in batch)))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
