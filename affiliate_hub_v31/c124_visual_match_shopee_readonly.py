"""C124 — comparação de imagens de candidatos Shopee e imagens WP, READ ONLY.

É evidência de similaridade visual, NÃO confirmação de vendedor, variante,
estoque ou campanha. Nunca publica, muda CTA ou converte links.
"""
from __future__ import annotations
import io
import json
import pathlib
import urllib.error
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import imagehash
from PIL import Image, UnidentifiedImageError

INPUT = pathlib.Path("c123_artifact/c123_radar_four_shopee_candidates.json")
OUT = pathlib.Path("c124_image_matching_results.json")
WP = {
 "28":"https://radartechbr.com.br/wp-content/uploads/2026/10/Scanner-OBD2-Bluetooth.jpg",
 "24":"https://radartechbr.com.br/wp-content/uploads/2026/10/Luz-RGB-portatil-para-video-e-celular.jpg",
}
MAX_IMAGE_BYTES = 5*1024*1024

def fetch_image(url: str, trusted: set[str]):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!="https" or parsed.hostname not in trusted:
        return None,"UNTRUSTED_IMAGE_URL"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (V31-safe-editorial-image-check)"})
    try:
        with urllib.request.urlopen(req,timeout=12) as r:
            chunk=r.read(MAX_IMAGE_BYTES+1)
            if len(chunk)>MAX_IMAGE_BYTES or len(chunk)<100:
                return None,"SIZE_OR_EMPTY"
        with Image.open(io.BytesIO(chunk)) as im:
            im.load()
            if im.width>8000 or im.height>8000:
                return None,"EXTREME_DIMENSIONS"
            return (im.convert("RGB").copy()),None
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,
            ValueError,UnidentifiedImageError,OSError):
        return None,"IMAGE_FETCH_OR_DECODE_ERROR"

def metrics(im):
    return {"phash":imagehash.phash(im),"dhash":imagehash.dhash(im),
            "ahash":imagehash.average_hash(im),"size":[im.width,im.height]}

def compare(item):
    post_id,record,base = item
    photo,error=fetch_image(record["image_url"],{"cf.shopee.com.br","down-br.img.susercontent.com"})
    if error:
        return {"shop_id":record["shop_id"],"item_id":record["item_id"],
                "title":record["title"],"fetch_error":error}
    h=metrics(photo)
    ds={name:int(h[name]-base[name]) for name in ("phash","dhash","ahash")}
    return {
      "shop_id":record["shop_id"],"item_id":record["item_id"],
      "title":record["title"],"image_url":record["image_url"],
      "offer_link":record["offer_link"],"size":h["size"],
      "distances":ds,"visual_similarity_score":round(
          (64-ds["phash"])*0.5+(64-ds["dhash"])*0.35+(64-ds["ahash"])*0.15,1),
      "match_strong":ds["phash"]<=6 and ds["dhash"]<=9,
      "match_exact_hash":ds["phash"]==0 and ds["dhash"]==0
    }

def main():
    data=json.loads(INPUT.read_text(encoding="utf-8"))["data"]
    result={}
    for post_id,wp_url in WP.items():
        im,error=fetch_image(wp_url,{"radartechbr.com.br"})
        if error:
            result[post_id]={"status":error,"candidates":[]}
            print("C124_POST="+json.dumps({"id":post_id,"status":error}),flush=True)
            continue
        base=metrics(im)
        records=data.get(post_id,{}).get("records",[])[:25]
        rows=[]
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures={executor.submit(compare,(post_id,item,base)):item for item in records}
            for future in as_completed(futures):
                rows.append(future.result())
        rows.sort(key=lambda r:(not r.get("match_strong",False),
                                 -r.get("visual_similarity_score",-1)))
        result[post_id]={"status":"VISUAL_COMPARISON_ONLY",
                         "wp_image_dimensions":base["size"],
                         "total_candidates":len(records),
                         "images_downloaded":sum("distances" in r for r in rows),
                         "strong_matches":sum(r.get("match_strong",False) for r in rows),
                         "candidates":rows}
        print("C124_POST="+json.dumps({
            "id":post_id,"status":"VISUAL_COMPARISON_ONLY",
            "wp_image_dimensions":base["size"],
            "downloaded":result[post_id]["images_downloaded"],
            "strong_matches":result[post_id]["strong_matches"],
            "top":[{k:r.get(k) for k in ("item_id","shop_id","title","distances","match_strong","fetch_error")}
                   for r in rows[:5]]
        },ensure_ascii=False),flush=True)
    OUT.write_text(json.dumps({
        "schema":"v31-c124-image-comparison-readonly/v1",
        "candidates":result,
        "guardrails":["Perceptual hash is not proof of identical SKU or seller",
                      "No WordPress modification or affiliate conversion",
                      "One must check campaign tracking and product variant separately"]
    },ensure_ascii=False,indent=2),encoding="utf-8")
    print("C124_READONLY_NO_CMS_WRITES",flush=True)

if __name__=="__main__":
    main()
