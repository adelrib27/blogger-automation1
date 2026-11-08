#!/usr/bin/env python3
"""Shopee -> Blogger V31: rotação fail-closed somente Ateliê Criativo em Casa."""
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

BLOG_ID = "8888519348129960729"
BLOG_URL = "https://atelie-criativo-em-casa.blogspot.com/"
BLOG_TITLE = "Ateliê Criativo em Casa"
PAGE_ID = "2731790842719271847"
START = "<!-- UNIVERSAL_V31_STORE_AUTO_START -->"
END = "<!-- UNIVERSAL_V31_STORE_AUTO_END -->"
API = "https://open-api.affiliate.shopee.com.br/graphql"
CATEGORIES = (
    ("Papelaria Criativa", ("kit canetas coloridas", "caderno pontilhado", "adesivos scrapbook"),
      ("caneta", "marca texto", "caderno", "adesivo", "planner", "washi", "scrapbook")),
    ("Costura e Bordado", ("agulha de costura manual", "kit bordado iniciantes", "bastidor bordado",
                           "alfinete para costura", "kit linhas bordado"),
      ("agulha", "bordado", "bastidor", "tesoura de costura", "alfinete", "dedal", "passador de linha")),
    ("Crochê e Tricô", ("kit agulha croche", "kit croche", "fio amigurumi"),
      ("croche", "amigurumi", "trico", "agulha", "marcador ponto")),
    ("Organização do Ateliê", ("organizador miçangas artesanato", "caixa organizadora material artesanato",
                               "estojo canetas escolar", "organizador pincel desenho"),
      ("organizador", "organizadora", "estojo", "caixa", "compartimento", "gaveta")),
)

REPORT = ROOT / "achados_da_rotina" / "rotacao_ultimo_resultado.json"


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
    q = "query AtelieCriativo { productOfferV2(keyword: " + json.dumps(keyword, ensure_ascii=False) + ", sortType: 2, page: " + str(page) + ", limit: 20) { nodes { itemId productName imageUrl offerLink priceMin priceMax shopName ratingStar sales } pageInfo { page limit hasNextPage } } }"
    payload = json.dumps({"query": q, "operationName": "AtelieCriativo"}, separators=(",", ":"), ensure_ascii=False)
    stamp = int(time.time())
    digest = hashlib.sha256((app + str(stamp) + payload + secret).encode("utf8")).hexdigest()
    auth = "SHA256 Credential=" + app + ", Timestamp=" + str(stamp) + ", Signature=" + digest
    req = urllib.request.Request(API, method="POST", data=payload.encode("utf8"), headers={"Authorization": auth, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=28) as response:
            if response.status != 200:
                fail("Shopee HTTP distinto de 200")
            data = json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        fail("Consulta Shopee indisponível: " + type(exc).__name__)
    if data.get("errors"):
        fail("Shopee retornou erros GraphQL. Não atualizar a Loja.")
    nodes = (data.get("data") or {}).get("productOfferV2") or {}
    if not isinstance(nodes.get("nodes"), list):
        fail("Resposta Shopee sem lista de ofertas válida")
    return nodes["nodes"]


def to_product(row: dict, label: str, tokens: tuple[str, ...]) -> dict | None:
    try:
        item = str(row.get("itemId") or "").strip()
        name = str(row.get("productName") or "").strip()
        n = normal(name)
        link = str(row.get("offerLink") or "").strip()
        img = str(row.get("imageUrl") or "").strip()
        if not (item.isdecimal() and name and link.startswith("https://") and img.startswith("https://")):
            return None
        if not any(t in n for t in tokens):
            return None
        # Seleção semântica para artesanato: não confundir "sem costura" de roupas com insumos.
        blocked = ("calcinha", "cueca", "bermuda", "roupa intima", "tanga", "lingerie", "sutia",
                   "vestido", "short feminino", "biquini", "moda feminina")
        if any(term in n for term in blocked):
            return None
        if label == "Costura e Bordado" and not any(t in n for t in (
                "agulha", "bordado", "bastidor", "alfinete", "dedal", "passador de linha", "tesoura de costura")):
            return None
        if label == "Organização do Ateliê" and not any(t in n for t in (
                "micanga", "artesanato", "caneta", "pincel", "papelaria", "escolar",
                "bijuteria", "pedraria", "linha", "costura")):
            return None
        price = float(row.get("priceMin") or 0)
        if price <= 0 or price > 100000:
            return None
        product = {"itemId": item, "productName": name, "offerLink": link,
                   "imageUrl": img, "priceMin": price, "category": label}
        require_product_allowed(product)
        return product
    except (ValueError, TypeError, RuntimeError):
        return None


def select_products(app: str, secret: str, previous_ids: set[str]) -> dict[str, list[dict]]:
    # Página de descoberta muda diariamente; evita repetição quando houver ofertas válidas.
    slot = int(time.time() // 86400)
    selected: dict[str, list[dict]] = {}
    used: set[str] = set()
    for idx, (label, keywords, tokens) in enumerate(CATEGORIES):
        pool: dict[str, dict] = {}
        page = (slot + idx) % 3 + 1
        for keyword in keywords:
            for requested in ([page, 1] if page != 1 else [1, 2]):
                for row in api_offers(app, secret, keyword, requested):
                    p = to_product(row, label, tokens)
                    if p:
                        pool[p["itemId"]] = p
                if len(pool) >= 10:
                    break
            if len(pool) >= 10:
                break
        choices = list(pool.values())
        choices.sort(key=lambda p: (p["itemId"] in previous_ids, p["itemId"]))
        if len(choices) < 4:
            fail("Candidatos Shopee insuficientes e relevantes para " + label)
        chosen = []
        for p in choices:
            if p["itemId"] in used:
                continue
            chosen.append(p)
            used.add(p["itemId"])
            if len(chosen) == 4:
                break
        if len(chosen) != 4:
            fail("Não há quatro produtos distintos e seguros para " + label)
        selected[label] = chosen
    if len(used) != 16:
        fail("Catálogo com número de produtos únicos divergente de 16")
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
    if region.count('class="ac-store-carousel"') != 1 or region.count('class="ac-store-slide"') != 3:
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
    hero_css = re.search(r'<style>#ac-loja \.ac-store-carousel[\s\S]*?</style>', original_area)
    if not css or not hero_css:
        fail("CSS padrão do tema da Loja ou carrossel ausente")
    e = lambda s: html.escape(str(s), quote=True)
    picks = (
        (selections["Papelaria Criativa"][0], "Papelaria para criar",
         "Canetas, marcadores e materiais para desenvolver seus projetos."),
        (selections["Crochê e Tricô"][0], "Crochê e trabalhos manuais",
         "Agulhas e acessórios para praticar novas técnicas."),
        (selections["Organização do Ateliê"][0], "Ateliê organizado",
         "Materiais identificados e espaço para trabalhar com praticidade."),
    )
    slides = []
    for i, (p, title, detail) in enumerate(picks, start=1):
        slides.append(
            '<article class="ac-store-slide" id="ac-slide-' + str(i) + '"><div>'
            '<span>Em destaque</span><h2>' + e(title) + '</h2><p>' + e(detail) +
            '</p><a href="' + e(p["offerLink"]) +
            '" rel="nofollow sponsored noopener" target="_blank">Conhecer produto na Shopee</a>'
            '</div><img src="' + e(p["imageUrl"]) + '" alt="' +
            e(p["productName"]) + '" loading="lazy" decoding="async"/></article>'
        )
    hero = (
        hero_css.group(0) + '\n' +
        '<div class="ac-store-carousel" role="region" aria-roledescription="carrossel" '
        'aria-label="Destaques do Ateliê Criativo">' + ''.join(slides) + '</div>' +
        '<nav class="ac-store-controls" aria-label="Escolha o destaque">' +
        ''.join('<a href="#ac-slide-%s">Destaque %s</a>' % (i, i) for i in range(1, 4)) + '</nav>'
    )
    nav = '<nav class="ub-store-nav" aria-label="Navegação das categorias">' + " · ".join(
        '<a href="#ac-cat-%s">%s</a>' % (i + 1, e(c[0]))
        for i, c in enumerate(CATEGORIES)) + "</nav>"
    sections = []
    for i, (label, _, _) in enumerate(CATEGORIES):
        cards = "\n".join(render_card(p, label, stamp) for p in selections[label])
        sections.append('<section class="ub-store-category" id="ac-cat-' + str(i + 1) +
            '"><h2>' + e(label) + '</h2><div class="ub-store-grid">' +
            cards + '</div></section>')
    dt = datetime.strptime(stamp, "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc)
    local = dt.astimezone(ZoneInfo("America/Recife")).strftime("%d/%m/%Y às %H:%M")
    banner = (
        '<p class="ub-store-status" role="status" style="border-left:4px solid #367e5e;'
        'background:#eef8f2;color:#3a5a4a;padding:15px 16px;margin:18px 0 24px;'
        'font-size:14px;">Vitrine atualizada em <time datetime="' + dt.isoformat() + '">' +
        local + '</time> · produtos selecionados via API Shopee · preços e disponibilidade '
        'podem mudar no marketplace.</p>'
    )
    region = START + '\n' + hero + '\n' + css.group(0) + '\n' + banner + '\n' + nav + '\n' + '\n'.join(sections) + '\n' + END
    updated = original[:original.find(START)] + region + original[original.find(END) + len(END):]
    changed_area = updated.split(START, 1)[1].split(END, 1)[0]
    if (updated.count(START) != 1 or updated.count(END) != 1
            or changed_area.count('class="ub-product-card"') != 16
            or changed_area.count('class="ac-store-slide"') != 3
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
            slides = public_html.count('class="ac-store-slide"')
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
    fixture = ('<p>antes</p>' + START +
        '<style>#ac-loja .ac-store-carousel{display:flex}</style>' +
        '<div class="ac-store-carousel" role="region">' +
        ''.join('<article class="ac-store-slide" id="ac-slide-%s">x</article>' % i for i in range(1,4)) +
        '</div><style id="adr-store-v31-css">a{color:#333}</style>' + END + '<p>depois</p>')
    cats = {cat: [
        {"itemId": str(n), "productName": "Agulhas exemplo",
         "imageUrl": "https://cf.shopee.com.br/file/example",
         "offerLink": "https://s.shopee.com.br/example", "priceMin": 1.99}
        for n in range(i*4+1, i*4+5)]
        for i, (cat, _, _) in enumerate(CATEGORIES)}
    result = build_content(fixture, cats, "2026-11-08 09:00 UTC")
    region = result.split(START,1)[1].split(END,1)[0]
    if (not result.startswith("<p>antes</p>") or not result.endswith("<p>depois</p>")
        or region.count('class="ub-product-card"') != 16
        or region.count('class="ac-store-slide"') != 3
        or "08/11/2026 às 06:00" not in region):
        fail("Self-test renderizador ou fuso horário diário falhou")
    if to_product({"itemId":"5","productName":"Kit de caneta comum",
                   "offerLink":"https://evil.example/x",
                   "imageUrl":"https://cf.shopee.com.br/file/example",
                   "priceMin":"19"}, "Papelaria Criativa", ("caneta",)) is not None:
        fail("Policy guard não bloqueou link externo")
    if to_product({"itemId":"6","productName":"Agulha em kit de calcinhas sem costura",
                   "offerLink":"https://s.shopee.com.br/example",
                   "imageUrl":"https://cf.shopee.com.br/file/example",
                   "priceMin":"19"}, "Costura e Bordado", ("agulha",)) is not None:
        fail("Filtro do nicho não bloqueou vestuário")
    print("SELF_TEST_PASS: 16 cards, 3 slides, 4 categorias, imagem e link guard")


def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    app, secret = ensure_credentials()
    is_live = os.getenv("ATELIE_STORE_DRY_RUN", "true").strip().lower() == "false"
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
