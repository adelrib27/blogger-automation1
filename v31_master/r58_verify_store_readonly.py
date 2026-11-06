#!/usr/bin/env python3
"""R58 authenticated verification only: Blogger LOJA, pages, editorials, public HTML."""
from __future__ import annotations
import json, sys, urllib.request, urllib.parse
from pathlib import Path
import r58_rotate_store as writer
import r58_store_policy as policy

BASE="https://lab-v31-r58-shopee-e2e-20261106.blogspot.com"
PAGES={
 "Sobre":("4330493101782559572","/p/sobre.html"),
 "Contato":("8642485791986631414","/p/contato.html"),
 "Política de Privacidade":("223485400474715031","/p/politica-de-privacidade.html"),
 "Termos de Uso":("2862183582058934423","/p/termos-de-uso.html"),
 "Aviso de Afiliados":("6443676382450783375","/p/aviso-de-afiliados.html")}
POSTS={
 "3893198167585505550":"21797631048",
 "8886363878493152260":"22392992790",
 "1086696355631937197":"22597307453"}

def authorized_get(url,token):
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+token,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=25) as res:
        if res.status!=200:raise RuntimeError("BLOGGER_GET_HTTP_NON200")
        return json.loads(res.read(400_000))

def main()->int:
    state=policy.validate_state(json.loads(Path("v31_master/state/lab_r58_rotation.json").read_text(encoding="utf-8")))
    tok=writer.oauth_token()
    page=writer.api_page(tok)
    html=writer.validate_page(page)
    info=policy.validate_store_html(html)
    if info["sha256"]!=state["html_sha256"] or info["items"]!=state["item_ids"]:
        raise RuntimeError("R58_STORE_STATE_MISMATCH")
    if 'id="r58-links-editoriais"' not in html or html.count("/2026/11/")<3:
        raise RuntimeError("R58_STORE_MISSING_EDITORIAL_LINKS")
    for title,(pid,path) in PAGES.items():
        p=authorized_get("https://www.googleapis.com/blogger/v3/blogs/"+policy.BLOG_ID+"/pages/"+pid,tok)
        if str(p.get("id"))!=pid or p.get("title")!=title or not str(p.get("url","")).endswith(path) or not p.get("published"):
            raise RuntimeError("R58_PAGE_IDENTITY_GUARD")
    for post_id,item_id in POSTS.items():
        p=authorized_get("https://www.googleapis.com/blogger/v3/blogs/"+policy.BLOG_ID+"/posts/"+post_id,tok)
        if (str(p.get("id"))!=post_id or not p.get("published") or
            f'data-shopee-item="{item_id}"' not in str(p.get("content","")) or
            "/p/loja.html" not in str(p.get("content",""))):
            raise RuntimeError("R58_POST_IDENTITY_GUARD")
    if state["rotation_enabled"] or state["allow_auto_write"]:
        raise RuntimeError("R58_UNEXPECTED_AUTO_WRITE_ENABLED")
    print(json.dumps({"status":"R58_READONLY_PUBLICATION_INVENTORY_PASS",
        "blog_id":policy.BLOG_ID,"pages":6,"posts":3,"store_products":16,
        "affiliate_links":32,"writes":0,"auto_rotation_enabled":False},ensure_ascii=False))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as e:
        print(json.dumps({"status":"R58_FAIL_CLOSED","reason_type":type(e).__name__,"writes":0}))
        raise SystemExit(2)
