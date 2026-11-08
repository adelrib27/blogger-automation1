#!/usr/bin/env python3
"""Rotação fail-closed da Loja V31 exclusivamente no blog Pedal Leve."""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blogger_policy_guard import require_product_allowed
from criar_rascunho import criar_servico_blogger

BLOG_ID = "4073458513010284301"
BLOG_URL = "https://pedal-leve-mobilidade-urbana.blogspot.com/"
BLOG_TITLE = "Pedal Leve — Mobilidade e Ciclismo Urbano"
PAGE_ID = "7331621701388164614"
START = "<!-- UNIVERSAL_V31_STORE_AUTO_START -->"
END = "<!-- UNIVERSAL_V31_STORE_AUTO_END -->"
from shopee_catalog_safe import CATEGORIES, fetch as _shopee_fetch, validate as _shopee_validate

REPORT = ROOT / "pedal_leve" / "rotacao_ultimo_resultado.json"


def fail(message: str) -> None:
    raise RuntimeError("FAIL_CLOSED: " + message)


def normal(value: str) -> str:
    base = unicodedata.normalize("NFKD", str(value or "").lower())
    return "".join(c for c in base if not unicodedata.combining(c))


def ensure_credentials() -> tuple[str, str]:
    app = os.getenv("SHOPEE_APP_ID", "").strip()
    secret = os.getenv("SHOPEE_SECRET", "").strip()
    if not app or not secret:
        fail("Credenciais Shopee indisponíveis. Nenhuma escrita.")
    for k in ("BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN"):
        if not os.getenv(k, "").strip():
            fail("Credencial Blogger obrigatória ausente: " + k)
    return app, secret


def api_offers(app: str, secret: str, keyword: str, page: int) -> list[dict]:
    return _shopee_fetch(app, secret, keyword, page)

def to_product(row: dict, label: str, tokens: tuple[str, ...]) -> dict | None:
    return _shopee_validate(row, label, tokens)

def select_products(app: str, secret: str, previous_ids: set[str]) -> dict[str, list[dict]]:
    # Por categoria, dar chance a cada família de consulta e priorizar itens novos.
    selected: dict[str, list[dict]] = {}
    used: set[str] = set()
    day = int(time.time() // 86400)
    for idx, (label, keywords, tokens) in enumerate(CATEGORIES):
        pool: dict[str, dict] = {}
        per_query: list[dict] = []
        for kw_idx, keyword in enumerate(keywords):
            candidates: list[dict] = []
            page = (day + idx + kw_idx) % 3 + 1
            for requested in ([page, 1] if page != 1 else [1, 2]):
                for row in api_offers(app, secret, keyword, requested):
                    p = to_product(row, label, tokens)
                    if p and p["itemId"] not in used:
                        pool[p["itemId"]] = p
                        candidates.append(p)
                if len(candidates) >= 4:
                    break
            choices = sorted(candidates, key=lambda p: (p["itemId"] in previous_ids, p["itemId"]))
            pick = next((p for p in choices if p["itemId"] not in {q["itemId"] for q in per_query}), None)
            if pick:
                per_query.append(pick)
        if len(pool) < 4:
            fail("Menos de quatro ofertas válidas para " + label)
        chosen = list(per_query)[:4]
        already = {p["itemId"] for p in chosen}
        for p in sorted(pool.values(), key=lambda p: (p["itemId"] in previous_ids, p["itemId"])):
            if len(chosen) >= 4:
                break
            if p["itemId"] not in already:
                chosen.append(p)
                already.add(p["itemId"])
        if len(chosen) != 4:
            fail("Quatro produtos distintos não disponíveis para " + label)
        selected[label] = chosen
        used.update(p["itemId"] for p in chosen)
    if len(used) != 16:
        fail("Rotação resultou em catálogo duplicado ou incompleto")
    return selected

def page_check(blogger) -> dict:
    b = blogger.blogs().get(blogId=BLOG_ID).execute()
    if str(b.get("id")) != BLOG_ID or b.get("name") != BLOG_TITLE or b.get("url") != BLOG_URL:
        fail("Blog ID, título ou URL divergente")
    page = blogger.pages().get(blogId=BLOG_ID, pageId=PAGE_ID).execute()
    raw = str(page.get("content") or "")
    state = str(page.get("status") or "").lower()
    live_ok = state == "live" or (
        not state and page.get("url") == BLOG_URL + "p/loja.html" and bool(page.get("published"))
    )
    if str(page.get("id")) != PAGE_ID or page.get("title") != "LOJA" or not live_ok:
        fail("Página LOJA ID, título ou publicação divergentes")
    if raw.count(START) != 1 or raw.count(END) != 1 or raw.find(START) >= raw.find(END):
        fail("Marcadores da região rotativa ausentes, repetidos ou invertidos")
    if raw.count('class="ub-product-card"') != 16 or raw.count('id="adr-store-v31-css"') != 1:
        fail("Cards ou CSS padrão V31 divergentes")
    region = raw.split(START, 1)[1].split(END, 1)[0]
    if region.count('class="pl-store-carousel"') != 1 or region.count('class="pl-store-slide"') != 3:
        fail("Carrossel fora da região controlada ou quantidade de slides incorreta")
    if region.count('class="ub-store-status"') != 1:
        fail("Carimbo da última seleção da Loja inválido")
    for label, _, _ in CATEGORIES:
        if region.count('data-category="' + html.escape(label, quote=True) + '"') != 4:
            fail("Distribuição de quatro produtos por categoria incorreta: " + label)
    return page


def render_card(p: dict, category: str, stamp: str) -> str:
    e = lambda s: html.escape(str(s), quote=True)
    price = "R$ " + ("%.2f" % p["priceMin"]).replace(".", ",")
    return ('<article class="ub-product-card" data-item-id="' + e(p["itemId"]) +
        '" data-category="' + e(category) + '"><div class="ub-product-image"><img src="' +
        e(p["imageUrl"]) + '" alt="' + e(p["productName"]) +
        '" loading="lazy" decoding="async"/></div><div class="ub-product-body">' +
        '<span class="ub-product-tag">' + e(category) + '</span><h3 class="ub-product-title">' +
        e(p["productName"]) + '</h3><p class="ub-product-price">Preço de referência da seleção ' +
        e(stamp) + ': ' + e(price) + '</p><a class="ub-product-action" href="' +
        e(p["offerLink"]) +
        '" target="_blank" rel="nofollow sponsored noopener">Conferir oferta na Shopee</a></div></article>')


def build_content(original: str, selections: dict[str, list[dict]], stamp: str) -> str:
    original_area = original.split(START, 1)[1].split(END, 1)[0]
    css = re.search(r'<style id="adr-store-v31-css">[\s\S]*?</style>', original_area)
    hero_css = re.search(r'<style>#pl-loja \.pl-store-carousel[\s\S]*?</style>', original_area)
    if not css or not hero_css:
        fail("CSS padrão do tema da Loja ou carrossel ausente")
    e = lambda s: html.escape(str(s), quote=True)
    picks = (
        (selections["Segurança e Visibilidade"][0], "Visibilidade para o percurso",
         "Compare farol, sinalização e características do anúncio."),
        (selections["Manutenção e Ferramentas"][0], "Cuide da sua bicicleta",
         "Bomba, reparos e ferramentas compatíveis para a rotina."),
        (selections["Bolsas e Transporte"][0], "Objetos bem acomodados",
         "Bolsas e suportes que não interfiram na condução."),
    )
    slides = []
    for i, (p, title, detail) in enumerate(picks, start=1):
        slides.append(
            '<article class="pl-store-slide" id="pl-slide-' + str(i) + '"><div>'
            '<span>Em destaque</span><h2>' + e(title) + '</h2><p>' + e(detail) +
            '</p><a href="' + e(p["offerLink"]) +
            '" rel="nofollow sponsored noopener" target="_blank">Conhecer produto na Shopee</a>'
            '</div><img src="' + e(p["imageUrl"]) + '" alt="' +
            e(p["productName"]) + '" loading="lazy" decoding="async"/></article>'
        )
    hero = (
        hero_css.group(0) + '\n' +
        '<div class="pl-store-carousel" role="region" aria-roledescription="carrossel" '
        'aria-label="Destaques do Pedal Leve">' + ''.join(slides) + '</div>' +
        '<nav class="pl-store-controls" aria-label="Escolha o destaque">' +
        ''.join('<a href="#pl-slide-%s">Destaque %s</a>' % (i, i) for i in range(1, 4)) + '</nav>'
    )
    nav = '<nav class="ub-store-nav" aria-label="Navegação das categorias">' + " · ".join(
        '<a href="#pl-cat-%s">%s</a>' % (i + 1, e(c[0]))
        for i, c in enumerate(CATEGORIES)) + "</nav>"
    sections = []
    for i, (label, _, _) in enumerate(CATEGORIES):
        cards = "\n".join(render_card(p, label, stamp) for p in selections[label])
        sections.append('<section class="ub-store-category" id="pl-cat-' + str(i + 1) +
            '"><h2>' + e(label) + '</h2><div class="ub-store-grid">' +
            cards + '</div></section>')
    dt = datetime.strptime(stamp, "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc)
    local = dt.astimezone(ZoneInfo("America/Recife")).strftime("%d/%m/%Y às %H:%M")
    banner = (
        '<p class="ub-store-status" role="status" style="border-left:4px solid #367e5e;'
        'background:#eef8f2;color:#3a5a4a;padding:15px 16px;margin:18px 0 24px;'
        'font-size:14px;">Vitrine atualizada em <time datetime="' + dt.isoformat() + '">' +
        local + ' (Recife) · ' + stamp + '</time> · produtos selecionados via API Shopee · preços e disponibilidade '
        'podem mudar no marketplace.</p>'
    )
    region = START + '\n' + hero + '\n' + css.group(0) + '\n' + banner + '\n' + nav + '\n' + '\n'.join(sections) + '\n' + END
    updated = original[:original.find(START)] + region + original[original.find(END) + len(END):]
    changed_area = updated.split(START, 1)[1].split(END, 1)[0]
    if (updated.count(START) != 1 or updated.count(END) != 1
            or changed_area.count('class="ub-product-card"') != 16
            or changed_area.count('class="pl-store-slide"') != 3
            or changed_area.count('class="ub-store-status"') != 1):
        fail("HTML V31 rotacionado inválido")
    return updated


def public_check(stamp: str) -> bool:
    """Exige HTML público 200, 16 cards, 3 slides e carimbo da execução atual."""
    url = BLOG_URL + "p/loja.html?rotacao_v31=" + urllib.parse.quote(stamp)
    for attempt in range(12):
        http_status = 0
        cards, slides, stamped = 0, 0, False
        try:
            req = urllib.request.Request(url + "-" + str(attempt),
                                         headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=18) as resp:
                http_status = resp.status
                public_html = resp.read().decode("utf8", errors="replace")
            cards = public_html.count('class="ub-product-card"')
            slides = public_html.count('class="pl-store-slide"')
            stamped = stamp in public_html and 'class="ub-store-status"' in public_html
            if http_status == 200 and cards >= 16 and slides >= 3 and stamped:
                print("PUBLIC_VERIFY_PASS: HTTP 200, 16+ produtos, 3 slides, carimbo real")
                return True
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            print("PUBLIC_VERIFY_RETRY: rede/HTTP " + type(exc).__name__)
        print("PUBLIC_VERIFY_RETRY: tentativa=%s http=%s cards=%s slides=%s stamp=%s" % (
            attempt + 1, http_status, cards, slides, stamped))
        if attempt < 11:
            time.sleep(8)
    return False


def report(status: str, ids: list[str], changed: int) -> None:
    doc = {"status": status, "blog_id": BLOG_ID, "page_id": PAGE_ID,
           "time_utc": datetime.now(timezone.utc).isoformat(), "products": len(ids),
           "changed_ids": changed, "item_ids": ids}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps({k: v for k, v in doc.items() if k != "item_ids"}, ensure_ascii=False))


def self_test() -> None:
    # Testa integridade do shell, contagens e preservação fora de marcadores.
    fixture = ('<p>antes</p>' + START +
        '<style>#pl-loja .pl-store-carousel{display:flex}</style>' +
        '<div class="pl-store-carousel">' +
        ''.join('<article class="pl-store-slide" id="pl-slide-%s">x</article>' % i for i in range(1,4)) +
        '</div><style id="adr-store-v31-css">a{color:#333}</style>' + END + '<p>depois</p>')
    data = {cat: [
        {"itemId": str(i*4+n+1), "productName": "Farol bike teste",
         "imageUrl": "https://cf.shopee.com.br/file/example",
         "offerLink": "https://s.shopee.com.br/example", "priceMin": 12.99}
        for n in range(4)] for i, (cat, _, _) in enumerate(CATEGORIES)}
    html = build_content(fixture, data, "2026-11-08 09:00 UTC")
    region = html.split(START,1)[1].split(END,1)[0]
    if (not html.startswith("<p>antes</p>") or not html.endswith("<p>depois</p>")
        or region.count('class="ub-product-card"') != 16
        or region.count('class="pl-store-slide"') != 3
        or region.count('class="ub-store-status"') != 1
        or "2026-11-08 09:00 UTC" not in region):
        fail("Self-test do renderer falhou")
    if to_product({"itemId":"5","productName":"Farol LED bicicleta",
                   "offerLink":"https://evil.example/x",
                   "imageUrl":"https://cf.shopee.com.br/file/example",
                   "priceMin":"19"}, "Segurança e Visibilidade", ("farol",)) is not None:
        fail("Guard permitiu domínio inválido")
    print("PEDAL_ROTATION_SELF_TEST_PASS: 16 cards, 3 slides e guard")

def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    app, secret = ensure_credentials()
    is_live = os.getenv("PEDAL_STORE_DRY_RUN", "true").strip().lower() == "false"
    if is_live and (os.getenv("GITHUB_REF") != "refs/heads/main" or os.getenv("GITHUB_EVENT_NAME") not in ("schedule", "push", "workflow_dispatch")):
        fail("LIVE só é permitido na branch main e eventos aprovados")
    blogger = criar_servico_blogger()
    page = page_check(blogger)
    original = str(page.get("content") or "")
    previous_ids = set(re.findall(r'class="ub-product-card" data-item-id="(\d+)"', original))
    if len(previous_ids) != 16:
        fail("Lista de IDs anterior inconsistente")
    selection = select_products(app, secret, previous_ids)
    ids = [p["itemId"] for group in selection.values() for p in group]
    changed = len(set(ids) - previous_ids)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    updated = build_content(original, selection, stamp)
    if not is_live:
        report("SAFE_OK_NO_WRITE", ids, changed)
        return
    if not changed:
        report("NO_ROTATION_CANDIDATES_UNCHANGED", ids, 0)
        return
    # Reler imediatamente antes da escrita e recusar se houver edição paralela.
    again = page_check(blogger)
    if str(again.get("content") or "") != original or again.get("etag") != page.get("etag"):
        fail("Conteúdo da LOJA alterado em paralelo")
    req = blogger.pages().update(blogId=BLOG_ID, pageId=PAGE_ID,
                                 body={"title": "LOJA", "content": updated})
    if page.get("etag"):
        req.headers["If-Match"] = page["etag"]
    req.execute()
    verified = page_check(blogger)
    if verified.get("content") != updated:
        fail("Blogger API não confirmou HTML atualizado")
    if not public_check(stamp):
        fail("Escrita API confirmada, mas a renderização pública ainda não confirmou; requer inspeção")
    report("LIVE_API_AND_PUBLIC_PASS", ids, changed)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ROTATION_STOP: " + str(e)[:500], file=sys.stderr)
        raise SystemExit(2)
