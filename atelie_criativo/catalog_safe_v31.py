#!/usr/bin/env python3
"""Consulta somente leitura de produtos Shopee para a curadoria do Ateliê Criativo em Casa (V31)."""
from __future__ import annotations
import hashlib
import json
import os
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blogger_policy_guard import require_product_allowed

API = "https://open-api.affiliate.shopee.com.br/graphql"
BLOG_ID = "8888519348129960729"
CATEGORIES = (
    ("Papelaria Criativa", ("kit canetas coloridas", "caderno pontilhado", "adesivos scrapbook"), ("caneta", "marca texto", "caderno", "adesivo", "planner", "washi", "scrapbook")),
    ("Costura e Bordado", ("kit costura", "kit bordado", "bastidor bordado"), ("costura", "bordado", "bastidor", "tesoura", "agulha", "linha")),
    ("Crochê e Tricô", ("kit agulha croche", "kit croche", "fio amigurumi"), ("croche", "amigurumi", "trico", "agulha", "marcador ponto")),
    ("Organização do Ateliê", ("caixa organizadora com divisorias", "organizador de mesa", "estojo organizador"), ("organizador", "organizadora", "estojo", "caixa", "compartimento", "gaveta")),
)
DEST = ROOT / "atelie_criativo" / "catalogo_produtos_safe.json"

def normalized(value: str) -> str:
    x = unicodedata.normalize("NFKD", str(value or "").lower())
    return "".join(c for c in x if not unicodedata.combining(c))

def api_products(app: str, secret: str, keyword: str, page: int) -> list:
    query = ("query AtelieCatalogo { productOfferV2(keyword: "
             + json.dumps(keyword, ensure_ascii=False)
             + ", sortType: 2, page: " + str(page)
             + ", limit: 20) { nodes { itemId productName imageUrl offerLink priceMin priceMax shopName ratingStar sales } pageInfo { page limit hasNextPage } } }")
    payload = json.dumps({"query":query,"operationName":"AtelieCatalogo"},ensure_ascii=False,separators=(",",":"))
    stamp = int(time.time())
    sign = hashlib.sha256((app + str(stamp) + payload + secret).encode("utf8")).hexdigest()
    auth = "SHA256 Credential=" + app + ", Timestamp=" + str(stamp) + ", Signature=" + sign
    req = urllib.request.Request(API, data=payload.encode("utf8"),method="POST",
        headers={"Authorization":auth,"Content-Type":"application/json","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=28) as resp:
            if resp.status != 200:
                raise RuntimeError("Shopee non-200")
            d = json.load(resp)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError("Shopee unavailable: " + type(e).__name__) from None
    if d.get("errors"):
        raise RuntimeError("Shopee returned GraphQL errors")
    data = (d.get("data") or {}).get("productOfferV2") or {}
    rows = data.get("nodes")
    if not isinstance(rows,list):
        raise RuntimeError("Shopee nodes invalid")
    return rows

def select() -> dict:
    app = os.getenv("SHOPEE_APP_ID","").strip()
    secret = os.getenv("SHOPEE_SECRET","").strip()
    if not app or not secret:
        raise RuntimeError("Shopee credentials unavailable")
    all_items = {}
    used = set()
    for label,keywords,tokens in CATEGORIES:
        pool = {}
        for keyword in keywords:
            for page in (1,2):
                for row in api_products(app,secret,keyword,page):
                    item = str(row.get("itemId") or "").strip()
                    name = str(row.get("productName") or "").strip()
                    url = str(row.get("offerLink") or "").strip()
                    image = str(row.get("imageUrl") or "").strip()
                    if not item.isdecimal() or not name or not any(t in normalized(name) for t in tokens):
                        continue
                    try:
                        price = float(row.get("priceMin") or 0)
                    except (ValueError,TypeError):
                        continue
                    if not (0 < price <= 100000):
                        continue
                    obj={"itemId":item,"productName":name,"offerLink":url,"imageUrl":image,
                         "priceMin":price,"category":label}
                    try:
                        require_product_allowed(obj)
                    except RuntimeError:
                        continue
                    pool[item]=obj
                if len(pool)>=8:
                    break
            if len(pool)>=8:
                break
        options=sorted(pool.values(),key=lambda p:p["itemId"])
        chosen=[p for p in options if p["itemId"] not in used][:4]
        if len(chosen)!=4:
            raise RuntimeError("Insufficient validated Shopee candidates for "+label)
        used.update(p["itemId"] for p in chosen)
        all_items[label]=chosen
        print("SHOPEE_SAFE_CATEGORY: %s count=4" % label,flush=True)
    if len(used)!=16:
        raise RuntimeError("Duplicate product ID in catalog")
    return all_items

def main() -> None:
    if os.getenv("GITHUB_EVENT_NAME") not in ("pull_request","workflow_dispatch"):
        raise RuntimeError("Catalog SAFE runs only on PR/manual")
    if "--self-test" in sys.argv:
        assert normalized("Agulhas de Crochê")=="agulhas de croche"
        assert len(CATEGORIES)==4
        print("CATALOG_SELF_TEST_PASS: 4 categories, 16 unique IDs contract")
        return
    products=select()
    doc={"status":"SAFE_READ_ONLY_SHOPEE_CATALOG","blog_id":BLOG_ID,
         "fetched_at_utc":datetime.now(timezone.utc).isoformat(),
         "categories":products,"products_total":sum(len(a) for a in products.values()),
         "writes_to_blogger":False}
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf8")
    print("CATALOG_SAFE_OK_NO_BLOGGER_WRITE: 16 products; private credentials not included",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("CATALOG_FAIL_CLOSED: "+str(exc),file=sys.stderr,flush=True)
        raise SystemExit(2)
