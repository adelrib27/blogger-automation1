#!/usr/bin/env python3
"""Validação pública somente leitura (desktop/mobile) do Ateliê Criativo V31."""
from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "atelie_criativo" / "public_qa"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://atelie-criativo-em-casa.blogspot.com"
BLOG_ID = "8888519348129960729"
PAGE_URLS = {
    "home": BASE + "/",
    "loja": BASE + "/p/loja.html",
    "sobre": BASE + "/p/sobre.html",
    "contato": BASE + "/p/contato.html",
    "privacidade": BASE + "/p/politica-de-privacidade.html",
    "termos": BASE + "/p/termos-de-uso.html",
    "cookies": BASE + "/p/politica-de-cookies.html",
    "afiliados": BASE + "/p/transparencia-e-afiliados.html",
    "mensagem": BASE + "/p/mensagem-enviada.html",
}
POSTS = [
    BASE + "/2026/11/papelaria-criativa-para-iniciantes-como.html",
    BASE + "/2026/11/costura-mao-para-iniciantes-como.html",
    BASE + "/2026/11/croche-para-iniciantes-como-escolher.html",
    BASE + "/2026/11/atelie-de-artesanato-em-casa-guia.html",
    BASE + "/2026/11/como-organizar-papelaria-criativa-em.html",
    BASE + "/2026/11/como-guardar-agulhas-linhas-e-materiais.html",
    BASE + "/2026/11/como-organizar-fios-de-croche-agulhas-e.html",
    BASE + "/2026/11/como-montar-uma-bancada-de-artesanato.html",
]
if len(PAGE_URLS) != 9 or len(POSTS) != 8:
    raise RuntimeError("Lista de URLs de produção não corresponde ao plano")
for u in [*PAGE_URLS.values(),*POSTS]:
    if urlparse(u).hostname != "atelie-criativo-em-casa.blogspot.com":
        raise RuntimeError("Domínio externo inesperado em QA")

async def img_state(page, selector: str):
    return await page.evaluate("""async sel => {
        const nodes = [...document.querySelectorAll(sel)];
        await Promise.allSettled(nodes.map(async im => {
            im.loading = 'eager';
            try { await Promise.race([
                im.decode(),
                new Promise((_, reject) => setTimeout(() => reject('timeout'), 9000))
            ]); } catch (_) {}
        }));
        return nodes.map(im => ({
            ok: im.complete && im.naturalWidth > 0,
            alt: !!im.getAttribute('alt'),
            src: im.getAttribute('src') || '',
            width: im.naturalWidth
        }));
    }""", selector)

async def capture(browser, label: str, mobile: bool, report: dict):
    width = 390 if mobile else 1365
    height = 844 if mobile else 900
    context = await browser.new_context(
        viewport={"width":width,"height":height},
        is_mobile=mobile, has_touch=mobile,
        device_scale_factor=1,
        user_agent=None)
    page = await context.new_page()
    mode = "mobile" if mobile else "desktop"
    for slug,url in [("home",PAGE_URLS["home"]),("loja",PAGE_URLS["loja"]),
                     ("post", POSTS[2] if mobile else POSTS[0])]:
        entry={"name":slug,"mode":mode,"url":url}
        try:
            response=await page.goto(url,wait_until="domcontentloaded",timeout=48000)
            entry["status"]=response.status if response else None
            await page.wait_for_timeout(1600)
            entry["title"]=await page.title()
            entry["brand_present"]="Ateliê Criativo em Casa" in await page.content()
            if slug=="loja":
                cards=await page.locator(".ub-product-card").count()
                slides=await page.locator(".ac-store-slide").count()
                banner=await page.locator(".ub-store-status").all_text_contents()
                entry.update(cards=cards,slides=slides,banner=banner[:1],
                             images=await img_state(page,".ub-product-card img, .ac-store-slide img"))
                entry["all_product_images_loaded"]=len(entry["images"])==19 and all(
                    im["ok"] for im in entry["images"])
                entry["all_product_alts"]=all(im["alt"] for im in entry["images"])
                entry["no_mobile_page_overflow"]=await page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth + 2")
            if slug=="post":
                entry["post_images"]=await img_state(page,"article .ac-cover img, article .ac-product img")
            path=OUT/(mode+"-"+slug+".png")
            await page.screenshot(path=str(path),full_page=True,animations="disabled",timeout=48000)
            entry["screenshot"]=path.name
        except (PlaywrightTimeout, Exception) as exc:
            entry["error"]=type(exc).__name__+": "+str(exc)[:230]
        report["captures"].append(entry)
        print("PUBLIC_QA_VIEW:",mode,slug,"HTTP",entry.get("status"),"cards",entry.get("cards"),"slides",entry.get("slides"),"images",sum(im["ok"] for im in entry.get("images",[])),flush=True)
    await context.close()

async def main():
    report={"blog_id":BLOG_ID,"time_utc":datetime.now(timezone.utc).isoformat(),
            "read_only":True,"captures":[],"urls":{},"errors":[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        await capture(browser,"",False,report)
        await capture(browser,"",True,report)
        ctx=await browser.new_context()
        page=await ctx.new_page()
        for name,url in [*PAGE_URLS.items(),*[(str(i+1),u) for i,u in enumerate(POSTS)]]:
            try:
                response=await page.goto(url,wait_until="domcontentloaded",timeout=45000)
                code=response.status if response else None
                report["urls"][name]={"status":code,"url":url}
            except Exception as exc:
                report["urls"][name]={"error":type(exc).__name__,"url":url}
        await browser.close()
    shop=[x for x in report["captures"] if x["name"]=="loja"]
    for s in shop:
        if s.get("status") != 200 or s.get("cards") != 16 or s.get("slides") != 3:
            report["errors"].append("Loja na visualização "+s["mode"]+" com cards, slides ou HTTP inconsistentes")
        if not s.get("all_product_images_loaded"):
            report["errors"].append("Fotos Shopee de produtos não carregaram integralmente em "+s["mode"])
        if not s.get("all_product_alts"):
            report["errors"].append("Produto sem alt em "+s["mode"])
        if s["mode"]=="mobile" and not s.get("no_mobile_page_overflow"):
            report["errors"].append("Overflow horizontal detectado na Loja mobile")
    for x in report["captures"]:
        if x.get("status") != 200 or not x.get("brand_present"):
            report["errors"].append("HTTP ou marca divergente: "+x["mode"]+"/"+x["name"])
        if x["name"]=="post" and not all(y["ok"] for y in x.get("post_images", [])):
            report["errors"].append("Foto do artigo indisponível: "+x["mode"])
    for name,data in report["urls"].items():
        if data.get("status") != 200:
            report["errors"].append("URL pública não acessível: "+name)
    report["status"]="PUBLIC_QA_PASS" if not report["errors"] else "PUBLIC_QA_NEEDS_REVIEW"
    (OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"status":report["status"],"url_count":len(report["urls"]),
          "captures":len(report["captures"]),"errors":report["errors"]},ensure_ascii=False),flush=True)
    if report["errors"]:
        raise SystemExit(2)

if __name__ == "__main__":
    asyncio.run(main())
