"""C127: investigação somente-leitura de redirecionamento TikTok e colagem de imagens.
Sem API de afiliado, D1, R2, CMS, criação de shortlinks ou publicação.
"""
from __future__ import annotations
import io,json,pathlib,urllib.request,urllib.error,urllib.parse
from PIL import Image,ImageOps,ImageDraw,ImageFont

ORIGINAL_URLS={
 "29":"https://vt.tiktok.com/ZS9UNndpjDsxQ-GACcI/",
 "25":"https://vt.tiktok.com/ZS9UNtSQoTWWq-a7gKh/",
 "24":"https://vt.tiktok.com/ZS9UNGSAnRA9S-q3vFI/",
}
WP={
 "29":"https://radartechbr.com.br/wp-content/uploads/2026/10/Arctic-Air-Cooler-portatil.jpg",
 "25":"https://radartechbr.com.br/wp-content/uploads/2026/10/Caixa-de-som-Kapbom-KA-8955.jpg",
 "24":"https://radartechbr.com.br/wp-content/uploads/2026/10/Luz-RGB-portatil-para-video-e-celular.jpg",
}
MANUAL={
 "29":[
 ("Shopee C126 item 23493283907","https://cf.shopee.com.br/file/sg-11134201-7rdwx-m0ak98sx50iudc")],
 "25":[
 ("Shopee C126 item 23694616922","https://cf.shopee.com.br/file/br-11134207-81z1k-mg69l6rb3213f3")],
 "24":[],
}
ART=pathlib.Path("c123_artifact/c123_radar_four_shopee_candidates.json")
OUT=pathlib.Path("c127_tiktok_visual_audit.json")

class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.events=[]
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        p=urllib.parse.urlsplit(newurl)
        self.events.append({"status":code,"host":p.hostname,"path":p.path[:160],
                            "query_keys":list(urllib.parse.parse_qs(p.query))[:18]})
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def trace_redirect(url):
    redirect=Redirects()
    opener=urllib.request.build_opener(redirect)
    out={"shortlink":url,"redirects":redirect.events}
    for method in ("HEAD","GET"):
        try:
            req=urllib.request.Request(url,method=method,headers={"User-Agent":"Mozilla/5.0"})
            with opener.open(req,timeout=12) as r:
                final=urllib.parse.urlsplit(r.geturl())
                if method=="GET":
                    r.read(100)
                out["method"]=method
                out["http_status"]=r.status
                out["final_host"]=final.hostname
                out["final_path"]=final.path[:180]
                out["final_query_keys"]=list(urllib.parse.parse_qs(final.query))[:18]
            break
        except urllib.error.HTTPError as e:
            out["error"]=f"HTTP_{e.code}"
        except (urllib.error.URLError,TimeoutError,ValueError,OSError) as e:
            out["error"]=type(e).__name__
    return out

def download_image(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or p.hostname not in {
      "radartechbr.com.br","cf.shopee.com.br","down-br.img.susercontent.com"}:
        return None
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=16) as r:
            raw=r.read(3000001)
        if len(raw)>3000000:return None
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            return im.convert("RGB").copy()
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError,OSError):
        return None

def main():
    data=json.loads(ART.read_text(encoding="utf-8"))["data"]
    traces={}
    for pid,url in ORIGINAL_URLS.items():
        traces[pid]=trace_redirect(url)
        print("C127_LINK="+json.dumps({"post_id":pid,**traces[pid]},ensure_ascii=False),flush=True)
    cols=6;cell_w=260;cell_h=280;row_h=300
    board=Image.new("RGB",(cols*cell_w,3*row_h),color="white")
    draw=ImageDraw.Draw(board)
    results={}
    for row_id,pid in enumerate(("29","25","24")):
        candidates=[("WP ORIGINAL",WP[pid])]
        candidates+=MANUAL[pid]
        if pid=="24":
            for item in data.get("24",{}).get("records",[])[:5]:
                candidates.append((f"Shopee {item['item_id']}",item["image_url"]))
        record=[]
        for col,(label,url) in enumerate(candidates[:cols]):
            im=download_image(url)
            x,y=col*cell_w,row_id*row_h
            draw.rectangle((x,y,x+cell_w-2,y+row_h-2),outline="#bbbbbb",width=1)
            draw.text((x+8,y+4),f"Post {pid} | {label}"[:42],fill="black")
            if im is not None:
                im.thumbnail((cell_w-14,cell_h-15))
                px=x+(cell_w-im.width)//2
                py=y+32+(cell_h-12-im.height)//2
                board.paste(im,(px,py))
            else:
                draw.text((x+10,y+60),"IMAGE FETCH FAILED",fill="red")
            record.append({"label":label,"source_url":url,"downloaded":im is not None})
        results[pid]=record
    board.save("c127_comparacao_3_artigos.png",optimize=True)
    OUT.write_text(json.dumps({
       "schema":"v31-c127-readonly/v1","tiktok_redirects":traces,
       "image_contact_sheet":"c127_comparacao_3_artigos.png",
       "images":results,
       "warnings":["No TikTok transaction, login or access tokens used",
                   "Photos alone cannot establish SKU / seller / exact variant",
                   "No changes to WordPress or R2"]
    },indent=2,ensure_ascii=False),encoding="utf-8")
    print("C127_READONLY_NO_CMS_WRITES_OR_CONVERSION",flush=True)

if __name__=="__main__":
    main()
