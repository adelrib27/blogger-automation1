#!/usr/bin/env python3
"""QA publico read-only V31: tema, paginas, posts, imagens e Loja desktop/mobile."""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BLOG="https://mala-pronta-viagem-pratica.blogspot.com"
BLOG_ID="4169782185971307909"
# Rotas representativas publicas. Demais paginas verificadas no Blogger API.
PAGES=("sobre","politica-de-privacidade","contato","loja")
# Um post comercial, um pilar e um cluster; 9 posts verificados pela API.
POSTS=(
  "necessaire-para-viajar-organize-higiene",
  "acessorios-de-viagem-guia-pratico-para",
  "bagagem-de-mao-como-conferir-medidas",
)
OUT=Path(__file__).resolve().parent/"qa_public"
OUT.mkdir(parents=True,exist_ok=True)
errors=[]
report={"blog_id":BLOG_ID,"domain":BLOG,"mode":"PUBLIC_READONLY","desktop":{},"mobile":{}}
def check(cond,message):
    if not cond:
        errors.append(message)
        print("QA_FAIL",message,flush=True)
def go(page,url,attempts=5):
    last=None
    for attempt in range(attempts):
        try:
            resp=page.goto(url+"?v31qacheck="+str(attempt),wait_until="domcontentloaded",timeout=25000)
            if resp and resp.status==200:
                page.wait_for_timeout(1800)
                return True
            last=f"HTTP {resp.status if resp else 'missing'}"
        except Exception as exc:
            last=type(exc).__name__
        page.wait_for_timeout(1800)
    print("PUBLIC_HTTP_FAIL",url,last,flush=True)
    errors.append("HTTP 200 indisponivel: "+url.split("/")[-1])
    return False
def images_loaded(page,query):
    els=page.locator(query)
    count=els.count()
    page.evaluate("""() => {document.querySelectorAll('img').forEach(img => {
       img.loading = 'eager'; img.setAttribute('loading','eager');
    })}""")
    page.wait_for_timeout(2300)
    # Simular rolagem real: captura full-page sozinha pode nao ativar lazy/intersection.
    for i in range(min(count,20)):
        try:
            els.nth(i).scroll_into_view_if_needed(timeout=7000)
            page.wait_for_timeout(180)
        except Exception as exc:
            print("SCROLL_WARNING",i,type(exc).__name__,flush=True)
    page.wait_for_timeout(1400)
    good=els.evaluate_all("(els) => els.filter(e => e.complete && e.naturalWidth > 0 && getComputedStyle(e).visibility !== 'hidden' && getComputedStyle(e).opacity !== '0').length")
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(500)
    return count,good
with sync_playwright() as engine:
    browser=engine.chromium.launch(headless=True,args=["--no-sandbox"])
    for mode,width,height in (("desktop",1366,768),("mobile",390,844)):
        page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
        if go(page,BLOG+"/"):
            html=page.content()
            check("Mala Pronta e Viagem Prática" in html,mode+" identidade divergente")
            check("ub-header" in html and "ub-footer" in html,mode+" Tema V31 nao identificado")
            check(page.locator("title").count()>0,mode+" title ausente")
            page.screenshot(path=str(OUT/(mode+"_home.png")),full_page=True)
        if go(page,BLOG+"/p/loja.html"):
            html=page.content()
            cards=page.locator(".ub-product-card").count()
            ids=page.locator(".ub-product-card").evaluate_all("(els)=>els.map(el=>el.getAttribute('data-item-id'))")
            imgs,good=images_loaded(page,".ub-product-card img")
            links=page.locator(".ub-product-card a[rel*='sponsored']").count()
            categories=page.locator(".ub-store-category").count()
            stamp=page.locator(".ub-store-status").count()
            report[mode]["store"]={"cards":cards,"unique":len(set(ids)),"images":imgs,"loaded_images":good,"links":links,"categories":categories,"banner":stamp}
            check(cards==16 and len(set(ids))==16,mode+" cards/IDs diferentes de 16")
            check(imgs==16 and good==16,mode+" imagens Shopee nao carregaram totalmente")
            check(links==16,mode+" links de afiliados diferentes de 16")
            check(categories==4 and stamp==1,mode+" categorias ou banner incorretos")
            page.screenshot(path=str(OUT/(mode+"_loja.png")),full_page=True)
        if mode=="desktop":
            for slug in PAGES:
                if slug=="loja":continue
                if not go(page,BLOG+"/p/"+slug+".html"):continue
                if slug=="contato":
                    ok=page.locator("form[action*='formsubmit.co']").count()==1
                    next_val=page.locator("form input[name='_next']").get_attribute("value") if ok else ""
                    check(ok and next_val==BLOG+"/p/mensagem-enviada.html","Formulario/_next de Contato incorreto")
            checked=[]
            for slug in POSTS:
                url=BLOG+"/2026/11/"+slug+".html"
                if not go(page,url):continue
                h=page.content()
                n,g=images_loaded(page,".post-body img")
                if n==0:
                    n,g=images_loaded(page,".mala-editorial img, .mala-pilar img, .mala-cluster img")
                check(n>=1 and g>=1,"Imagem principal sem carga: "+slug)
                checked.append({"slug":slug,"images":n,"loaded":g})
            report["desktop"]["posts"]=checked
        page.close()
    browser.close()
report["failures"]=errors
report["status"]="PUBLIC_QA_PASS" if not errors else "PUBLIC_QA_FAIL"
(OUT/"summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("PUBLIC_QA_REPORT",json.dumps(report,ensure_ascii=False),flush=True)
if errors:raise SystemExit(2)
print("PUBLIC_QA_PASS",flush=True)
