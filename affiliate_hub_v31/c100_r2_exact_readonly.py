"""C100 R2 catalog -> exact Shopee Affiliate productOfferV2 READ ONLY.

Todos os produtos vêm de R2+taxonomia+source_policy_gate. A API deve
confirmar mesmo shopId:itemId, imagem, offerLink e comissão por listagem.
Não gera shortlinks, não usa D1, não escreve em R2 e não publica no CMS.
"""
from __future__ import annotations
import argparse, json, os, re, sqlite3, tempfile, time, pathlib, urllib.request, urllib.error, urllib.parse, math, unicodedata
from collections import Counter, defaultdict
from affiliate_hub_v31.r2_state import R2State
from affiliate_hub_v31.routing import sites
from affiliate_hub_v31.catalog import Catalog, host_allowed
from affiliate_hub_v31.source_policy_gate import source_safe_for_use
from affiliate_hub_v31.shopee_probe import authorization, ENDPOINT
from affiliate_hub_v31.c100_multi_store_readonly import listing_valid
from affiliate_hub_v31.cafe_loja_readonly import norm, num, rate

PROFILE_PATH=pathlib.Path(__file__).with_name("c100_store_profiles.json")
MAX_CANDIDATE_PER_SITE=80
MAX_CANDIDATE_PER_NICHE=60
MAX_ALIAS_PER_CALL=8
MAX_API_CALLS_PER_SITE=16
MAX_OFFERS=36
MIN_READY=24

def pool(db, catalog, site, route):
    paths=route.get("allowed_niches",[])
    by={}
    seen=set();sellers=Counter()
    sql="""SELECT p.product_key,p.title,p.origin_url,p.image_url,p.shop_id,p.item_id
         FROM products p JOIN product_taxonomy t ON p.product_key=t.product_key
         WHERE p.moderation='eligible' AND t.status='matched'
         AND t.category=? AND t.niche=?
         ORDER BY p.last_seen_utc DESC LIMIT 180"""
    for pair in paths:
        cat,niche=pair.split("/",1)
        rows=[]
        for key,title,origin,image,shop,item in db.execute(sql,(cat,niche)):
            shop=str(shop or "");item=str(item or "")
            if not shop.isdigit() or not item.isdigit() or (shop,item) in seen: continue
            if not isinstance(title,str) or not (17<=len(title)<=210):continue
            if not isinstance(image,str) or not image.startswith("https://"):continue
            if not host_allowed(origin):continue
            try:
                if not source_safe_for_use(catalog,key):continue
            except Exception:continue
            if sellers[shop]>=5:continue
            seen.add((shop,item));sellers[shop]+=1
            rows.append({"shopId":shop,"itemId":item,"r2_title":title,"source_category":pair})
            if len(rows)>=MAX_CANDIDATE_PER_NICHE:break
        by[pair]=rows
    candidates=[]
    # Intercalar famílias, não esgotar os 80 anúncios em só um nicho.
    for i in range(MAX_CANDIDATE_PER_NICHE):
        for pair in paths:
            if i<len(by.get(pair,[])): candidates.append(by[pair][i])
            if len(candidates)>=MAX_CANDIDATE_PER_SITE:return candidates
    return candidates

FIELDS=("itemId shopId productName productLink imageUrl offerLink priceMin "
        "ratingStar sales shopName shopType periodEndTime "
        "commissionRate sellerCommissionRate commission")

def request_exact(app,secret,chunk):
    query="query V31C100Exact { "+" ".join(
        "x"+str(i)+":productOfferV2(itemId:"+str(x["itemId"])+",page:1,limit:4){nodes{"+FIELDS+"}}"
        for i,x in enumerate(chunk)
    )+" }"
    body=json.dumps({"query":query,"operationName":"V31C100Exact"},separators=(",",":"))
    req=urllib.request.Request(ENDPOINT,method="POST",data=body.encode(),headers={
        "Authorization":authorization(app,secret,body,int(time.time())),
        "Content-Type":"application/json","Accept":"application/json",
        "User-Agent":"V31-C100-R2ExactReadOnly/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=27) as resp:
            raw=resp.read(131073)
            if len(raw)>131072:return {},"response_over_limit"
        doc=json.loads(raw)
    except urllib.error.HTTPError as exc:return {},"http:"+str(exc.code)
    except (TimeoutError,urllib.error.URLError,ValueError):return {},"transport_or_json"
    if doc.get("errors"):
        codes=[str(z.get("extensions",{}).get("code","graphql")) for z in doc["errors"] if isinstance(z,dict)]
        return doc.get("data") or {}, "graphql:"+",".join(codes[:2])
    return doc.get("data") or {},None

def source_category(name,source,site):
    title=norm(name)
    for label,keyword,rx in site["groups"]:
        if re.search(r"\b(?:"+rx+r")\b",title):
            return label
    raw=source.split("/")[-1].replace("_"," ").capitalize()
    return raw

def primary_product_guard(title: object, source_path: str, site_key: str) -> bool:
    """Rejeita produtos ACESSÓRIOS disfarçados de equipamentos inteiros.

    Aplicado após curadoria do R2 e antes de aprovar o mesmo anúncio na API.
    Funciona também em blogs abrangentes, usando o nicho original do R2.
    Não compara identidade entre vendedores por semelhança superficial.
    """
    t=norm(title)
    if not t:return False
    if source_path.endswith("/air_fryers") or site_key=="air_fryers":
        if not ("air fryer" in t or "airfryer" in t or "fritadeira" in t):
            return False
        if any(x in t for x in (
            "tapete", "forrar", "silicone para", "forma para", "papel para",
            "puxador", "cabo para", "cesto de reposicao", "peca para",
            "desengordurante", "limpador", "escova de limpeza", "tampa avulsa",
            "resistencia", "acessorio para", "industrial profissional tacho",
        )):return False
    if source_path.endswith("/liquidificadores") or site_key=="liquidificadores":
        if "liquidificador" not in t:return False
        if any(x in t for x in (
            "arraste motor", "motor e copo", "copo de liquidificador",
            "copo para liquidificador", "pecas para liquidificador",
            "tampa para liquidificador", "acoplamento", "lamina de reposicao",
            "engrenagem", "faca de liquidificador", "conjunto de reposicao",
        )):return False
    if source_path.endswith("/ventilacao") or site_key=="ventiladores":
        if "ventilador" not in t:return False
        if any(x in t for x in (
            "helice ventilador", "helice para ventilador",
            "botao ventilador", "grade de ventilador",
            "capacitor para ventilador", "controle remoto para ventilador",
            "motor para ventilador", "ventilador de refrigeracao alimentos",
            "resfriamento rapido para macarrao", "pecas para ventilador",
        )):return False
    if source_path.endswith("/moveis") or site_key=="moveis":
        if any(x in t for x in (
            "puxador para", "dobradica", "corredica para",
            "parafuso para", "adesivo para moveis", "capa para cadeira",
            "capa para sofa", "pe de reposicao", "pes para moveis",
            "sapata para", "rodizio avulso", "rodinha para",
            "kit reparo", "pe de mesa avulso", "miniatura de",
        )):return False
        if not any(x in t for x in (
            "mesa", "cadeira", "sofa", "poltrona", "estante",
            "guarda roupa", "guarda-roupa", "rack", "painel de tv",
            "comoda", "aparador", "armario", "escrivaninha",
            "gaveteiro", "cabeceira", "beliche", "sapateira",
            "criado mudo", "criado-mudo", "bancada",
        )):return False
    return True


def verify(node,source,site):
    # Reutiliza as regras HTTP, ID, origem, imagem, reputação e faturamento
    # do mesmo produto; taxonomia R2 já valida o nicho.
    result=listing_valid(node,source_category(node.get("productName"),source["source_category"],site),
                         r"[a-z0-9]+",site["key"])
    if not result:return None
    if str(result["shopId"])!=str(source["shopId"]) or str(result["itemId"])!=str(source["itemId"]):return None
    if not primary_product_guard(node.get("productName"),source["source_category"],site["key"]):
        return None
    result["category"]=source_category(node.get("productName"),source["source_category"],site)
    return result

def discover(site,route,db,catalog,app,secret):
    candidates=pool(db,catalog,site,route)
    accepted={};errors=[];calls=0;exact_found=0
    for offset in range(0,len(candidates),MAX_ALIAS_PER_CALL):
        if calls>=MAX_API_CALLS_PER_SITE:break
        batch=candidates[offset:offset+MAX_ALIAS_PER_CALL]
        response,err=request_exact(app,secret,batch);calls+=1
        if err and "10000" in err:
            time.sleep(.8)
            response,err=request_exact(app,secret,batch);calls+=1
        if err:errors.append({"offset":offset,"error":err})
        if err and ("10030" in err or "http:429" in err):break
        for i,src in enumerate(batch):
            nodes=((response or {}).get("x"+str(i)) or {}).get("nodes") or []
            same=[n for n in nodes if str(n.get("shopId"))==src["shopId"] and str(n.get("itemId"))==src["itemId"]]
            if len(same)!=1:continue
            exact_found+=1
            product=verify(same[0],src,site)
            if product:
                accepted[product["listing_key"]]=product
        time.sleep(.17)
    groups=defaultdict(list)
    for p in accepted.values():groups[p["category"]].append(p)
    for items in groups.values(): items.sort(key=lambda x:x["score"],reverse=True)
    selected=[];seen=set();names=set();shops=Counter()
    for step in range(MAX_OFFERS):
        if len(selected)>=MAX_OFFERS:break
        for cat in groups:
            if len(selected)>=MAX_OFFERS:break
            already=sum(x["category"]==cat for x in selected)
            if already>step:continue
            for p in groups[cat]:
                key=p["listing_key"];name=norm(p["name"])
                if key in seen or name in names or shops[p["shopId"]]>=2:continue
                selected.append(p);seen.add(key);names.add(name);shops[p["shopId"]]+=1
                break
    if len({p["category"] for p in selected})==1 and len(selected)>=MIN_READY:
        # Repartir em segmentos neutros, sem inventar atributos do produto.
        for i,p in enumerate(selected):
            p["category"]="Seleção inicial" if i<16 else "Mais opções"
    status=("READ_ONLY_READY_24_PLUS" if len(selected)>=MIN_READY else
           "PARTIAL_API_ERRORS" if errors else "INSUFFICIENT_QUALIFIED_OFFERS")
    return {
        "site_key":site["key"],"site_title":site["title"],
        "blog_id":site["blog"],"page_id":site["page"],"status":status,
        "r2_candidates":len(candidates),"api_exact_matches":exact_found,
        "eligible_live_offers":len(accepted),"selected_count":len(selected),
        "unique_sellers":len(shops),"seller_extra_ge_3pct":sum(p["sellerCommissionRate"]>=.03 for p in selected),
        "calls":calls,"errors":errors,"stock_confirmed":False,"subid_confirmed":False,
        "shopee_mutations":0,"products":selected
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--sites",required=True)
    args=parser.parse_args()
    keys=[k.strip() for k in args.sites.split(",") if k.strip()]
    profiles=json.loads(PROFILE_PATH.read_text(encoding="utf-8"))["sites"]
    selected=[p for p in profiles if p["key"] in keys]
    if not selected or len(selected)!=len(keys):raise ValueError("invalid sites")
    all_routes=sites()
    route_by_id={str(v["identifier"]):v for v in all_routes.values() if v["platform"]=="blogger"}
    app=os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID","")
    secret=os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET","")
    if not app or not secret:raise RuntimeError("Shopee account credentials missing")
    with tempfile.TemporaryDirectory() as td:
        path=pathlib.Path(td)/"c100_r2_ro.sqlite3"
        if not R2State.from_env().restore_to(path): raise RuntimeError("R2 snapshot unavailable")
        db=sqlite3.connect("file:"+str(path)+"?mode=ro",uri=True)
        catalog=Catalog.__new__(Catalog);catalog.db=db
        results=[]
        for site in selected:
            route=route_by_id.get(site["blog"])
            if not route:raise ValueError("site missing V31 route "+site["key"])
            data=discover(site,route,db,catalog,app,secret)
            print("C100_EXACT_SITE="+json.dumps({k:v for k,v in data.items() if k!="products"},ensure_ascii=False,separators=(",",":")))
            for p in data["products"]:
                print("C100_EXACT_OFFER="+json.dumps({"site_key":site["key"],**p},ensure_ascii=False,separators=(",",":")))
            results.append(data)
        db.close()
    output=pathlib.Path(os.environ.get("V31_C100_OUTPUT","c100_r2_exact_offers.json"))
    output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("C100_EXACT_READY_COUNT="+str(sum(d["status"]=="READ_ONLY_READY_24_PLUS" for d in results)))
    print("C100_R2_SHOPEE_READ_ONLY_NO_D1_NO_SHORTLINK_NO_CMS")

if __name__=="__main__":
    main()
