#!/usr/bin/env python3
"""Somente leitura: seleciona produtos verdadeiros para 26 blogs usando a conta Shopee afiliada.
FALHA sem publicar caso uma consulta obrigatoria nao ofereça produto valido.
"""
import os,time,json,hashlib,urllib.request,urllib.error,re,unicodedata
from urllib.parse import urlparse
API="https://open-api.affiliate.shopee.com.br/graphql"
# Apenas blogs reais ja inventariados. Cada par de buscas possui assunto editorial proprio.
TASKS=[
("4073458513010284301","Pedal Leve","bomba de ar bicicleta manometro","bomba ar bicicleta"),
("4169782185971307909","Mala Pronta","cadeado mala senha","cadeado viagem"),
("8888519348129960729","Atelie Criativo","base de corte artesanato","tapete de corte costura"),
("3644898524310766003","Jardim e Horta","regador plantas","regador jardim"),
("1637047917126642592","Achados da Rotina","suporte notebook mesa","suporte notebook"),
("4739187376492839837","Casa Leve","cesto organizador empilhavel","cesto organizador"),
("1426630233929943394","Achados para Casa","organizador cabos adesivo","organizador fios"),
("8052455848487624244","Vida Pet","tapete coletor areia gato","tapete areia gatos"),
("8930870316690519385","Casa Pratica Lab","pote hermetico cozinha","pote armazenamento cozinha"),
("8658632621591002634","Eletroportateis","sanduicheira eletrica","sanduicheira grill"),
("6319734511998091378","Cabelos em Foco","mascara morte subita lola 450g","morte subita lola"),
("4473989735719981382","Ventiladores em Foco","ventilador mondial vsp 40 b","ventilador mesa mondial 40"),
("9113728635217260884","Air Fryers em Foco","air fryer elgin cube fry 4.2l","elgin cube fry"),
("7757953554206491487","Limpeza Inteligente","robo aspirador wap robot w90","wap robot w90"),
("1719259388907013414","Conecta Achados","hub usb c multifuncional","adaptador usb c hub"),
("4830103887652146866","Estilo Dia a Dia","bolsa transversal feminina","bolsa tiracolo feminina"),
("4177382081459143374","Casa em Ordem","divisoria organizadora gaveta","organizador gaveta divisorias"),
("5151950717041967683","Escolha Certa Online","organizador sapatos","sapateira organizadora"),
("7527651041649593600","Achados que Valem","luminaria led recarregavel","luminaria mesa recarregavel"),
("1453188702831337099","Guia Achados Ofertas","balanca digital cozinha","balanca cozinha digital"),
("9144338307944682868","Vitrine Pratica","cabide multiuso","cabide organizador"),
("2858597309582499028","Moda e Ofertas","bolsa feminina transversal","bolsa feminina tiracolo"),
("2562496977098748229","Achadinhos Beleza","escova limpeza facial silicone","escova facial silicone"),
("7487888217273188851","Portal Radar Tech","teclado bluetooth","teclado bluetooth sem fio"),
("3552757910439359679","Cozinha Sem Complicacao","tabua de corte cozinha","tabua corte bambu"),
("5271798990390532475","Liquidificadores em Foco","liquidificador philips walita ri2242","philips walita ri2242")
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
