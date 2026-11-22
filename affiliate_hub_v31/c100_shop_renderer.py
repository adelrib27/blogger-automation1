"""V31 C100 — renderizador determinístico de Loja Blogger, C98+C99.

Entrada: shortlist READ ONLY do productOfferV2 e páginas/artigos realmente
existentes. Não consulta, converte, cria ou publica nada.
"""
from __future__ import annotations
import argparse
import html
import json
import re
import urllib.parse
from collections import Counter
from pathlib import Path

MIN_OFFERS=24
MAX_OFFERS=36
BUTTON_COLOR="#D83F00"
LABEL_BUTTON="Ver oferta na Shopee"
VALID_IMG_HOSTS=("shopee.com.br","susercontent.com")
VALID_OFFER_HOSTS=("s.shopee.com.br","shope.ee","shopee.com.br")
CSS_CTA="background:#D83F00;color:#fff;font-weight:750;border-radius:9px;padding:12px 14px;text-decoration:none;box-shadow:0 0 0 2px rgba(255,154,50,.26),0 4px 14px rgba(216,63,0,.30)"

def esc(v: object) -> str:
    return html.escape(str(v or ""),quote=True)

def hostname_ok(value: str, allowed: tuple[str,...]) -> bool:
    parts=urllib.parse.urlsplit(str(value))
    if parts.scheme!="https" or not parts.hostname: return False
    if parts.hostname in allowed: return True
    return any(parts.hostname.endswith("."+suffix) for suffix in allowed if "." in suffix)

def validate(items: list[dict]) -> None:
    if not (MIN_OFFERS<=len(items)<=MAX_OFFERS):
        raise ValueError(f"minimum {MIN_OFFERS} verified products required, got {len(items)}")
    keys=set();offers=set()
    for p in items:
        for f in ("shopId","itemId","name","image","offer","origin","category"):
            if not p.get(f): raise ValueError("missing "+f)
        key=(str(p["shopId"]),str(p["itemId"]))
        if not all(s.isdigit() for s in key) or key in keys: raise ValueError("duplicate or invalid listing key")
        keys.add(key)
        if not hostname_ok(p["image"],VALID_IMG_HOSTS): raise ValueError("image host invalid")
        if not hostname_ok(p["offer"],VALID_OFFER_HOSTS): raise ValueError("offer host invalid")
        origin=urllib.parse.urlsplit(str(p["origin"]))
        if origin.hostname!="shopee.com.br" or f"/product/{key[0]}/{key[1]}" not in origin.path:
            raise ValueError("origin path does not bind this listing")
        if p["offer"] in offers: raise ValueError("reused offer for different product")
        offers.add(p["offer"])
        if not (4<=float(p.get("rating") or 0)<=5): raise ValueError("rating insufficient")

def slug(value: str) -> str:
    import unicodedata
    value=unicodedata.normalize("NFKD",str(value)).lower()
    value="".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+","-",value).strip("-")[:60]

def normalize_title(v: str) -> str:
    value=" ".join(str(v).split())
    if len(value)>105:
        value=value[:106].rsplit(" ",1)[0]+"…"
    return value

def guide_links(data: dict) -> list[dict]:
    links=[]
    for entry in data.get("guides",[]):
        title=str(entry.get("title") or "").strip()[:90]
        url=str(entry.get("url") or "").strip()
        if not title or not url: continue
        u=urllib.parse.urlsplit(url)
        if u.scheme not in ("http","https") or not u.hostname or "blogspot.com" not in u.hostname: continue
        links.append({"title":title,"url":url})
    return links[:8]

def render(data: dict, cfg: dict) -> str:
    offers=data["products"]
    validate(offers)
    site=data["site_key"]
    if site!=cfg["key"] or str(data["blog_id"])!=str(cfg["blog"]) or str(data["page_id"])!=str(cfg["page"]):
        raise ValueError("site identity mismatch")
    groups=list(dict.fromkeys(str(x["category"]) for x in offers))
    if len(groups)<2: raise ValueError("not enough category diversity")
    cats=Counter(str(x["category"]) for x in offers)
    pageid=str(cfg["page"])
    for x in offers:
        if len(str(x.get("name","")))>180: raise ValueError("title too long")
    nav="".join(f'<a href="#v31c100-{esc(slug(k))}" style="background:#f2e6d6;color:#51341f;border-radius:25px;padding:9px 13px;text-decoration:none;font-size:13px;font-weight:750">{esc(k)} ({cats[k]})</a>' for k in groups)
    buttons=[]
    seen=set()
    for p in offers:
        name=normalize_title(p["name"])
        cat=str(p["category"])
        identifier=f' id="v31c100-{slug(cat)}"' if cat not in seen else ""
        seen.add(cat)
        rating=round(float(p["rating"]),1)
        seller=str(p.get("shop") or "Vendedor na Shopee").strip()[:78]
        markup=(f'<article{identifier} class="v31-c100-card" style="min-width:0;display:flex;flex-direction:column;overflow:hidden;border:1px solid #e7dac9;border-radius:16px;background:#fff;box-shadow:0 6px 17px rgba(58,39,24,.06)">'
                f'<a href="{esc(p["offer"])}" rel="nofollow sponsored noopener noreferrer" target="_blank" style="display:block;background:#faf7f2;padding:12px;height:231px;box-sizing:border-box;overflow:hidden;text-align:center">'
                f'<img loading="lazy" decoding="async" width="350" height="350" src="{esc(p["image"])}" alt="Foto do anúncio: {esc(name)}" style="display:block;width:100%;height:205px!important;max-height:205px!important;object-fit:contain!important;object-position:center;border-radius:8px" /></a>'
                f'<div style="display:flex;flex:1;flex-direction:column;padding:14px;gap:9px">'
                f'<p style="font-size:12px;color:#7d5437;font-weight:700;margin:0">{esc(cat)} <span style="float:right;color:#95600e">★ {str(rating).replace(".",",")}</span></p>'
                f'<h4 style="font-size:16px;line-height:1.35;color:#39271b;margin:0">{esc(name)}</h4>'
                f'<p style="font-size:12px;color:#655748;margin:auto 0 0">Vendedor na Shopee: {esc(seller)}</p>'
                f'<a href="{esc(p["offer"])}" rel="nofollow sponsored noopener noreferrer" target="_blank" style="display:block;text-align:center;{CSS_CTA}">{LABEL_BUTTON}</a>'
                '</div></article>')
        buttons.append(markup)
    guides=guide_links(data)
    guide_html=("")
    if guides:
        guide_html=('<section style="margin:26px 0 12px"><h3 style="font-size:23px;color:#442d1d;margin:0 0 7px">Guias para escolher melhor</h3>'
            '<p style="font-size:14px;color:#6b5c4b;margin:0 0 14px">Compare características e modos de uso antes de comprar.</p>'
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,215px),1fr));gap:11px">'
            + "".join(f'<a href="{esc(g["url"])}" style="display:block;border:1px solid #e5dacd;border-radius:10px;padding:12px 14px;background:#fff;color:#146854;text-decoration:none;font-weight:700;font-size:13px">{esc(g["title"])}</a>' for g in guides)
            +"</div></section>")
    count=len(offers)
    date=str(data.get("generated_at_utc") or "22/11/2026")[:10]
    scoped=(f'<style id="v31-c100-page-style-{pageid}">'
       f'#post-body-{pageid} .ub-v29-photo-notice,#post-body-{pageid} #ub-v21-store-carousel,#post-body-{pageid} .ub-store-heading{{display:none!important}}'
       f'#post-body-{pageid} .v31-c100-card:target{{outline:3px solid #d98935;outline-offset:3px;scroll-margin-top:96px}}'
       f'@media(max-width:520px){{#post-body-{pageid} .v31-c100-grid{{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:9px!important}}'
       f'#post-body-{pageid} .v31-c100-card h4{{font-size:14px!important}}'
       f'#post-body-{pageid} .v31-c100-card img{{height:145px!important;max-height:145px!important}}'
       f'#post-body-{pageid} .v31-c100-card>a{{height:169px!important}}'
       f'#post-body-{pageid} .v31-c100-card>div{{padding:10px!important}}}}'
       '</style>')
    page=(scoped+'<section class="v31-c100-store" lang="pt-BR" style="max-width:1160px;margin:10px auto 45px;padding:0 12px;line-height:1.6;color:#33271c">'
        '<header style="background:linear-gradient(120deg,#fff2e2,#fffaf4);border:1px solid #e5d2b8;border-radius:19px;padding:clamp(20px,4vw,37px);margin:10px 0 24px">'
        f'<p style="margin:0 0 8px;font-size:12px;font-weight:800;letter-spacing:.1em;color:#92551b;text-transform:uppercase">{esc(cfg["title"])} · Seleção de produtos</p>'
        '<h2 style="font-size:clamp(25px,4vw,37px);line-height:1.18;color:#422b1a;margin:0 0 12px">Descubra produtos selecionados para o seu dia a dia</h2>'
        f'<p style="font-size:15px;max-width:780px;margin:0 0 12px">Explore {esc(", ".join(groups[:4]).lower())} e outras opções relacionadas ao tema deste blog. As fotos e ofertas são de anúncios reais de vendedores na Shopee, escolhidos com atenção à relevância e às avaliações.</p>'
        f'<p style="font-size:13px;color:#815d3f;margin:0">{count} produtos · {len(groups)} categorias · Consulta realizada em 22/11/2026. Podemos receber comissão por compras elegíveis; o blog não vende, não entrega e não garante estoque ou preços.</p></header>'
        f'<nav aria-label="Categorias de produtos" style="display:flex;gap:8px;flex-wrap:wrap;margin:0 0 23px">{nav}</nav>'
        '<section aria-label="Vitrine de produtos" class="v31-c100-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,215px),1fr));gap:16px;align-items:stretch">'
        + "\n".join(buttons) +'</section>'
        +guide_html+
        '<aside style="background:#fff9ef;border:1px solid #ebddc9;border-radius:13px;padding:19px 22px;margin:25px 0">'
        '<h3 style="font-size:21px;margin:0 0 7px;color:#432d1a">Antes de comprar</h3>'
        '<p style="font-size:14px;margin:0 0 8px">Confira a variante, capacidade, dimensões, voltagem (quando houver), preço, frete, prazo e avaliações atualizadas diretamente na Shopee. A presença nesta vitrine não significa teste pessoal do produto ou garantia de disponibilidade.</p>'
        '<p style="font-size:13px;margin:0">Esta página contém links patrocinados. O blog pode receber comissão em compras elegíveis, sem custo adicional necessariamente associado à indicação.</p>'
        '</aside></section>')
    if len(page)>200000 or len(re.findall(r'data:',page))>0: raise ValueError("unacceptable html")
    if page.count(LABEL_BUTTON)!=count or page.count('rel="nofollow sponsored noopener noreferrer"')!=count*2:
        raise ValueError("CTA mismatch")
    return page

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True)
    parser.add_argument("--site",required=True)
    parser.add_argument("--guides",default="")
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    payload=json.loads(Path(args.input).read_text(encoding="utf-8"))
    if isinstance(payload,list):
        rows=[x for x in payload if x["site_key"]==args.site]
        if len(rows)!=1: raise ValueError("site key missing or repeated in shortlist")
        data=rows[0]
    else: data=payload
    profiles=json.loads(Path(__file__).with_name("c100_store_profiles.json").read_text(encoding="utf-8"))["sites"]
    candidates=[x for x in profiles if x["key"]==args.site]
    if len(candidates)!=1: raise ValueError("site profile not found")
    if data.get("status")!="READ_ONLY_READY_24_PLUS": raise ValueError("shortlist not ready")
    if args.guides:
        guides=json.loads(Path(args.guides).read_text(encoding="utf-8"))
        data={**data,"guides":guides}
    result=render(data,candidates[0])
    Path(args.output).write_text(result,encoding="utf-8")
    print("C100_HTML_VERIFIED_SITE="+args.site+" SIZE="+str(len(result))+" PRODUCTS="+str(len(data["products"])))
if __name__=="__main__":
    main()
