#!/usr/bin/env python3
"""SAFE: valida fotos renderizadas e responsividade. NENHUMA escrita em Blogger."""
import asyncio, json, os
from pathlib import Path
from playwright.async_api import async_playwright

BASE = "https://pedal-leve-mobilidade-urbana.blogspot.com"
STORE = BASE + "/p/loja.html"
ARTICLE = BASE + "/2026/11/ciclismo-urbano-para-iniciantes-guia.html"
REPORT = Path("pedal_leve/qa_browser_result.json")
async def open_retry(page, url):
    for i in range(7):
        try:
            res=await page.goto(url+"?pedal_browser_safe="+str(i),wait_until="domcontentloaded", timeout=27000)
            if res and res.status==200:
                return
            print("QA_BROWSER_HTTP_RETRY",i+1,res.status if res else None,flush=True)
        except Exception as e:
            print("QA_BROWSER_RETRY",i+1,type(e).__name__,flush=True)
        await asyncio.sleep(6)
    raise RuntimeError("FAIL_CLOSED: navegador nao recebeu HTTP200: "+url)

async def image_status(img):
    try:
        await img.scroll_into_view_if_needed(timeout=9000)
        await img.evaluate("""el => {
          if (!el.complete) { el.loading = 'eager'; }
        }""")
        for _ in range(12):
            x=await img.evaluate("el=>({loaded:el.complete && el.naturalWidth > 0,width:el.naturalWidth,height:el.naturalHeight,src:el.currentSrc||el.src})")
            if x["loaded"]: return x
            await asyncio.sleep(0.6)
        return x
    except Exception as e:
        return {"loaded":False,"error":type(e).__name__}

async def main():
    report={"blog_id":"4073458513010284301","mode":"PUBLIC_READONLY","results":[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        for viewport in [{"width":1440,"height":900},{"width":390,"height":844}]:
            page=await browser.new_page(viewport=viewport,locale="pt-BR",ignore_https_errors=False)
            await open_retry(page,STORE)
            await page.locator(".ub-product-card").first.wait_for(timeout=15000)
            cards=page.locator(".ub-product-card")
            count=await cards.count()
            imgs=page.locator(".ub-product-card img")
            loaded=[]
            for i in range(await imgs.count()):
                loaded.append(await image_status(imgs.nth(i)))
            width=await page.evaluate("({scroll:document.documentElement.scrollWidth,viewport:window.innerWidth})")
            data={"url":"store","viewport":viewport,"cards":count,"images":len(loaded),
                  "loaded_images":sum(int(x.get("loaded",False)) for x in loaded),
                  "failed_images":[i for i,x in enumerate(loaded) if not x.get("loaded",False)],
                  "width":width}
            report["results"].append(data)
            print("PEDAL_BROWSER_STORE",json.dumps(data,ensure_ascii=False),flush=True)
            if count!=16 or len(loaded)!=16 or data["loaded_images"]!=16 or width["scroll"]>width["viewport"]+4:
                raise RuntimeError("FAIL_CLOSED: 16 fotos visíveis ou responsividade do catálogo falhou")
            await open_retry(page,ARTICLE)
            await page.locator("article img").first.wait_for(timeout=15000)
            first=await image_status(page.locator("article img").first)
            a={"url":"article","viewport":viewport,"image_loaded":first.get("loaded",False)}
            report["results"].append(a)
            print("PEDAL_BROWSER_ARTICLE",json.dumps(a,ensure_ascii=False),flush=True)
            if not first.get("loaded"):raise RuntimeError("FAIL_CLOSED: imagem inicial do artigo não renderizou")
            await page.close()
        await browser.close()
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    print("PEDAL_BROWSER_VISUAL_PASS: desktop 1440 e mobile 390, 16 imagens em cada, thumbnail",flush=True)

if __name__=="__main__":
    asyncio.run(main())
