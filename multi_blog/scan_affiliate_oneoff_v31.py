#!/usr/bin/env python3
"""Somente leitura: seleciona produtos verdadeiros para 26 blogs usando a conta Shopee afiliada.
FALHA sem publicar caso uma consulta obrigatoria nao ofereça produto valido.
"""
import os,time,json,hashlib,urllib.request,urllib.error,re,unicodedata
from urllib.parse import urlparse
API="https://open-api.affiliate.shopee.com.br/graphql"
# Apenas blogs reais ja inventariados. Cada par de buscas possui assunto editorial proprio.
TASKS=[
("1426630233929943394","Achados para Casa","presilha organizadora cabos","clips organizador fios"),
("4473989735719981382","Ventiladores em Foco","ventilador mondial vsp40b","ventilador de mesa mondial vsp40"),
("1637047917126642592","Achados da Rotina","suporte para notebook aluminio ajustavel","base ajustavel notebook"),
("9113728635217260884","Air Fryers em Foco","fritadeira eletrica elgin cube fry 4l","airfryer elgin 4,2 litros"),
("2858597309582499028","Moda e Ofertas","bolsa tote feminina grande","bolsa shopper feminina")
]
def fail(msg):raise RuntimeError("FAIL_CLOSED:"+msg)
def norm(x):
 x=unicodedata.normalize("NFKD",str(x).lower())
 return "".join(c for c in x if not unicodedata.combining(c))
def query(term,app,secret):
 gql="query ScanV31 { productOfferV2(keyword: "+json.dumps(term,ensure_ascii=False)+", sortType: 2, page: 1, limit: 20) { nodes { itemId productName imageUrl offerLink priceMin shopName } } }"
 body=json.dumps({"query":gql,"operationName":"ScanV31"},ensure_ascii=False,separators=(",",":"))
 ts=str(int(time.time()))
 signature=hashlib.sha256((app+ts+body+secret).encode()).hexdigest()
 request=urllib.request.Request(API,data=body.encode(),headers={"Authorization":"SHA256 Credential="+app+", Timestamp="+ts+", Signature="+signature,"Content-Type":"application/json","Accept":"application/json"},method="POST")
 try:
  with urllib.request.urlopen(request,timeout=32) as response:
   data=json.load(response)
 except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
  print("CATALOG_HTTP_FAIL",term,type(e).__name__,getattr(e,"code",""),flush=True);return []
 if data.get("errors"):
  codes=[(x.get("extensions") or {}).get("code") for x in data["errors"][:2]]
  print("CATALOG_GRAPHQL_FAIL",term,codes,flush=True);return []
 return ((data.get("data") or {}).get("productOfferV2") or {}).get("nodes") or []
def good(r,term):
 try:
  name=str(r.get("productName") or "").strip();id=str(r.get("itemId") or "")
  link=str(r.get("offerLink") or "");im=str(r.get("imageUrl") or "")
  price=float(r.get("priceMin") or 0)
  if not(id.isdecimal() and len(name)>10 and 0<price<=15000):return False
  if not (link.startswith("https://") and im.startswith("https://")):return False
  if urlparse(link).hostname not in ("s.shopee.com.br","shopee.com.br","www.shopee.com.br"):return False
  if not (urlparse(im).hostname or "").endswith("shopee.com.br"):return False
  token=norm(term).split()
  title=norm(name)
  return sum(t in title for t in token)>=min(2,len(token))
 except (TypeError,ValueError):return False
def main():
 app=os.getenv("SHOPEE_APP_ID","").strip();secret=os.getenv("SHOPEE_SECRET","").strip()
 if not app or not secret:fail("credenciais ausentes")
 found=[]
 for n,(bid,blog,kw1,kw2) in enumerate(TASKS,1):
  selected=None
  for kw in (kw1,kw2):
   rows=query(kw,app,secret)
   choices=[r for r in rows if good(r,kw)]
   if choices:
    r=choices[0]
    selected={"blog_id":bid,"blog":blog,"keyword":kw,"item_id":str(r["itemId"]),"name":str(r["productName"]).strip(),"price_brl":float(r["priceMin"]),"image":str(r["imageUrl"]),"affiliate":str(r["offerLink"])}
    break
   time.sleep(2)
  if selected:
   found.append(selected)
   print("CATALOG_ITEM",json.dumps(selected,ensure_ascii=False,separators=(",",":")),flush=True)
  else:print("CATALOG_UNAVAILABLE",bid,blog,flush=True)
  time.sleep(2)
 print("CATALOG_SUMMARY",json.dumps({"total":len(TASKS),"found":len(found),"missing":[x[0] for x in TASKS if x[0] not in {p["blog_id"] for p in found}]},separators=(",",":")),flush=True)
 if not found:fail("API sem produto validado")
if __name__=="__main__":main()
