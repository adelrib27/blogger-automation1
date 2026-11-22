"""C96補: complementar a shortlist Café na Medida usando relevância, READ ONLY."""
from __future__ import annotations
import json, os, time
from collections import defaultdict
from datetime import datetime, timezone
from affiliate_hub_v31.cafe_loja_readonly import call, validate

SEARCHES=[
    ("Moedores","moedor de cafe manual"),
    ("Italianas","cafeteira italiana inox"),
    ("Chaleiras","chaleira eletrica inox"),
    ("Garrafas termicas","garrafa termica cafe"),
    ("Cafeteiras eletricas","cafeteira eletrica"),
    ("Espumadores","espumador de leite eletrico"),
    ("Cafe em graos","cafe em graos"),
    ("Prensas francesas","prensa francesa cafe"),
    ("Canecas termicas","caneca termica cafe"),
    ("Moedores","moedor de cafe eletrico"),
    ("Italianas","cafeteira italiana moka"),
    ("Chaleiras","chaleira de bico fino cafe"),
    ("Cafeteiras espresso","maquina cafe espresso"),
    ("Coadores","filtro coador de cafe inox"),
]
def main():
    app=os.environ.get("V31_EDITORIAL_SHOPEE_APP_ID","")
    secret=os.environ.get("V31_EDITORIAL_SHOPEE_APP_SECRET","")
    if not app or not secret: raise RuntimeError("Missing Shopee API credentials")
    bycat=defaultdict(list)
    seen=set()
    events=[]
    for category,keyword in SEARCHES:
        nodes,err=call(app,secret,category,keyword,1)
        if err:
            events.append({"category":category,"keyword":keyword,"error":err})
            if "10030" in err or "429" in err: break
            time.sleep(.7)
            continue
        filtered=0
        for n in nodes:
            item=validate(n,category)
            if not item: continue
            name=item["name"].lower()
            if category=="Espumadores" and ("suporte" in name or "base para" in name):
                continue
            if category=="Cafeteiras espresso" and ("italiana" in name or "moka" in name) and not ("máquina" in name or "maquina" in name): continue
            k=(item["shopId"],item["itemId"])
            if k in seen: continue
            seen.add(k)
            bycat[category].append(item)
            filtered+=1
        events.append({"category":category,"keyword":keyword,"received":len(nodes),"valid":filtered})
        time.sleep(.25)
    chosen=[]
    used=set()
    for cat in bycat:
        bycat[cat].sort(key=lambda x:x["score"],reverse=True)
    for rank in range(8):
        for cat,_ in SEARCHES:
            if len(chosen)>=70: break
            group=bycat[cat]
            if rank>=len(group): continue
            n=group[rank]
            k=(n["shopId"],n["itemId"])
            if k not in used:
                chosen.append(n);used.add(k)
    print("C96B_META="+json.dumps({
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "queries":len(events),"errors":[x for x in events if "error" in x],
        "query_outcomes":events,"unique_valid":len(seen),
        "emitted":len(chosen),"mode":"READ_ONLY",
        "converted":False,"stock_confirmed":False
    },ensure_ascii=False,separators=(",",":")))
    for n in chosen:
        print("C96B_OFFER="+json.dumps(n,ensure_ascii=False,separators=(",",":")))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
