#!/usr/bin/env python3
"""Shopee V31: catálogo editorial SAFE isolado, sem escrita no Blogger.

Consulta autenticada real, no máximo 3 tentativas por blog apenas para erro
GraphQL 10000 (novo timestamp/assinatura a cada tentativa). Registra evidência
e até um candidato semântico por blog. Não altera outros workflows/Loja.
"""
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
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blogger_policy_guard import product_policy_check  # noqa: E402

APP_EXPECTED = "18352820579"
EXCLUDED_BLOG_ID = "9156820142401099679"
ENDPOINT = "https://open-api.affiliate.shopee.com.br/graphql"
OUT = ROOT / "diagnostics" / "data" / "editorial_v31_shopee_candidates_safe.json"

# Blog ID / consulta / tokens obrigatórios em título do anúncio (após normalização).
# Estes gates são preliminares: ainda requerem curadoria humana editorial e SAFE de artigo.
ROWS = (
("1426630233929943394", "organizador porta pendurar", "organizador&porta"),
("370856880185231084", "acessorios limpeza violao", "violao&limpeza|violao&flanela|violao&pano"),
("7487888217273188851", "suporte notebook ajustavel", "suporte&notebook"),
("4073458513010284301", "adaptador valvula presta schrader bicicleta", "adaptador&presta|presta&schrader"),
("4739187376492839837", "prateleira adesiva banheiro", "prateleira&adesiv"),
("8930870316690519385", "organizador tampa panela", "organizador&tampa&panela"),
("8658632621591002634", "processador alimentos compacto", "processador&alimentos|processador&comida|mini&processador"),
("1637047917126642592", "passa cabos mesa escritorio", "cabo&mesa|passa&cabos"),
("6319734511998091378", "toalha microfibra cabelo", "toalha&cabelo|toalha&microfibra"),
("4473989735719981382", "ventilador de coluna", "ventilador&coluna"),
("9113728635217260884", "papel perfurado air fryer", "papel&air&fryer|papel&airfryer"),
("7757953554206491487", "escova eletrica limpeza", "escova&eletric&limpeza"),
("1719259388907013414", "suporte celular carro", "suporte&celular&carro|suporte&celular&veicular"),
("4830103887652146866", "mochila casual trabalho", "mochila&casual|mochila&trabalho"),
("4177382081459143374", "organizador debaixo da pia", "organizador&pia|organizador&gabinete"),
("5151950717041967683", "cabide veludo conjunto", "cabide&veludo"),
("7527651041649593600", "trena laser digital", "trena&laser"),
("1453188702831337099", "timer digital cozinha", "timer&digital|temporizador&cozinha"),
("9144338307944682868", "suporte livro receita bancada", "suporte&livro|suporte&receita"),
("2858597309582499028", "calca jogger masculina", "calca&jogger"),
("2562496977098748229", "esponja maquiagem kit", "esponja&maquiagem"),
("3552757910439359679", "tapete secagem louca", "tapete&louca|tapete&secagem|tapete&escorredor"),
("5271798990390532475", "copo liquidificador reposicao", "copo&liquidificador"),
("8888519348129960729", "tesoura precisao artesanato", "tesoura&artesanato|tesoura&precisao"),
("4169782185971307909", "balanca digital mala viagem", "balanca&bagagem|balanca&mala"),
("8052455848487624244", "fonte agua gatos", "fonte&gato"),
("3644898524310766003", "substrato plantas vasos drenagem", "substrato&plantas|substrato&vasos|substrato&drenagem"),
)

def normalize(value):
    value = unicodedata.normalize("NFKD", str(value or "").lower())
    return "".join(c for c in value if not unicodedata.combining(c))

def semantic_ok(title, expression):
    t = normalize(title)
    return any(all(token in t for token in clause.split("&"))
               for clause in expression.split("|"))

def valid_url(value, kind):
    try:
        u = urlsplit(str(value or ""))
        if u.scheme != "https" or u.username or u.password or not u.hostname:
            return False
        host = u.hostname.lower()
        if kind == "offer":
            return host in {"s.shopee.com.br", "www.shopee.com.br", "shopee.com.br"}
        return host == "shopee.com.br" or host.endswith(".shopee.com.br")
    except ValueError:
        return False

def request_id(headers):
    for key in ("x-request-id", "x-shopee-request-id", "x-trace-id"):
        val = headers.get(key) if headers is not None else None
        if val and re.fullmatch(r"[A-Za-z0-9.:_-]{1,128}", str(val)):
            return str(val)
    return None

def safe_msg(value):
    return re.sub(r"[^A-Za-z0-9 ,.:;_\[\]()/-]", "", str(value or ""))[:120]

def request_once(app, secret, keyword):
    term = json.dumps(keyword, ensure_ascii=False)
    query = ("query EditorialCatalogSAFE { productOfferV2(keyword: " + term +
             ", sortType: 2, page: 1, limit: 8) { nodes { itemId productName imageUrl offerLink priceMin } } }")
    body = json.dumps({"query": query, "operationName": "EditorialCatalogSAFE"},
                      ensure_ascii=False, separators=(",", ":"))
    ts = str(int(time.time()))
    signature = hashlib.sha256((app + ts + body + secret).encode("utf-8")).hexdigest()
    req = urllib.request.Request(
        ENDPOINT, data=body.encode("utf-8"), method="POST",
        headers={
            "Authorization": f"SHA256 Credential={app}, Timestamp={ts}, Signature={signature}",
            "Content-Type": "application/json", "Accept": "application/json",
            "User-Agent": "EditorialV31-Shopee-Safe/1.0",
        })
    try:
        with urllib.request.urlopen(req, timeout=28) as resp:
            status, headers, raw = resp.status, resp.headers, resp.read(400001)
    except urllib.error.HTTPError as exc:
        status, headers, raw = exc.code, exc.headers, exc.read(400001)
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"status": "NETWORK_STOP", "exception": type(exc).__name__}, []
    record = {"http": status, "request_id": request_id(headers)}
    if len(raw) > 400000:
        return dict(record, status="SIZE_STOP"), []
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        return dict(record, status="NONJSON_STOP"), []
    if not isinstance(doc, dict):
        return dict(record, status="FORMAT_STOP"), []
    errors = doc.get("errors") or []
    if errors:
        err = errors[0] if isinstance(errors[0], dict) else {}
        ext = err.get("extensions") or {}
        code = ext.get("code") if isinstance(ext, dict) else None
        return dict(record, status="GRAPHQL_STOP", code=code,
                    message=safe_msg(err.get("message"))), []
    root = (doc.get("data") or {}).get("productOfferV2") or {}
    nodes = root.get("nodes") if isinstance(root, dict) else None
    if status != 200 or not isinstance(nodes, list):
        return dict(record, status="INVALID_NODES_STOP"), []
    return dict(record, status="PASS", received=len(nodes)), nodes

def retry_query(app, secret, keyword, pause_fn=time.sleep, request_fn=request_once):
    history = []
    for attempt in range(1, 4):
        outcome, nodes = request_fn(app, secret, keyword)
        history.append(dict(outcome, attempt=attempt))
        if outcome.get("status") == "PASS":
            return history, nodes
        # Only 10000 supports limited retry; all other failure codes are fail-closed.
        if str(outcome.get("code")) != "10000" or attempt == 3:
            break
        pause_fn((3, 7)[attempt - 1])
    return history, []


def niche_product_check(blog_id, name):
    """Evita correspondencias literais que nao resolvem a pauta editorial."""
    title = normalize(name)
    if blog_id == "8930870316690519385":
        # Descansos/apoiadores de bancada nao organizam tampas no armario.
        return not any(part in title for part in ("apoiador", "descanso para colher", "suporte colher"))
    if blog_id == "8658632621591002634":
        # Este nicho cobre eletroportateis, nao mini processadores manuais.
        if "manual" in title or "de corda" in title:
            return False
        return any(part in title for part in ("eletric", "motor", "recarregavel", "usb", "110v", "127v", "220v", "bivolt"))
    if blog_id == "1453188702831337099":
        # Timer de um eletrodomestico nao e temporizador digital avulso.
        return not any(part in title for part in ("cafeteira", "microondas", "forno", "fritadeira", "air fryer", "batedeira"))
    return True

def select_candidate(nodes, expression, blog_id):
    for row in nodes:
        if not isinstance(row, dict):
            continue
        ident = str(row.get("itemId") or "").strip()
        name = str(row.get("productName") or "").strip()
        image, offer = str(row.get("imageUrl") or ""), str(row.get("offerLink") or "")
        if not (ident.isdecimal() and len(name) >= 12 and
                semantic_ok(name, expression) and niche_product_check(blog_id, name) and valid_url(image, "image") and
                valid_url(offer, "offer")):
            continue
        product = {
            "itemId": ident, "productName": name[:260], "imageUrl": image,
            "offerLink": offer,
        }
        if not product_policy_check(product)["accepted"]:
            continue
        return product
    return None

def self_test():
    assert len(ROWS) == 27
    assert EXCLUDED_BLOG_ID not in [row[0] for row in ROWS]
    assert len(set(row[0] for row in ROWS)) == 27
    assert semantic_ok("Kit Toalha Microfibra para Cabelo", "toalha&cabelo")
    assert not semantic_ok("Pano de cozinha", "toalha&cabelo")
    assert not niche_product_check("8930870316690519385", "Apoiador de Tampa de Panela e Colher AIME Organizador Cozinha Moderno")
    assert not niche_product_check("8658632621591002634", "Mini Processador de Alimentos Manual Formato Compacto")
    assert not niche_product_check("1453188702831337099", "Cafeteira Elétrica Digital com Timer")
    assert niche_product_check("8658632621591002634", "Mini Processador Eletrico de Alimentos 127v")
    assert not valid_url("https://evil.example", "offer")
    calls = [({"status": "GRAPHQL_STOP", "code": 10000}, []),
             ({"status": "PASS", "received": 1}, [{"itemId": "5"}])]
    slept = []
    def fake(_a, _s, _k):
        return calls.pop(0)
    hist, nodes = retry_query("a", "s", "k", slept.append, fake)
    assert len(hist) == 2 and slept == [3] and nodes
    calls = [({"status": "GRAPHQL_STOP", "code": 10020}, [])]
    hist, nodes = retry_query("a", "s", "k", slept.append, fake)
    assert len(hist) == 1 and not nodes
    print("EDITORIAL_RETRY_SELF_TEST_PASS_27_BLOGS", flush=True)

def main():
    if "--self-test" in sys.argv:
        self_test()
        return 0
    app, secret = (os.getenv("SHOPEE_APP_ID") or "").strip(), (os.getenv("SHOPEE_SECRET") or "").strip()
    if app != APP_EXPECTED or not secret:
        print("FAIL_CLOSED_APP_ID_OR_SECRET", flush=True)
        return 2
    max_blogs = int(os.getenv("EDITORIAL_SAFE_SCAN_COUNT", "3"))
    if not 1 <= max_blogs <= 27:
        print("FAIL_CLOSED_INVALID_SCAN_COUNT", flush=True)
        return 2
    items = []
    for index, (bid, keyword, accept) in enumerate(ROWS[:max_blogs]):
        if index:
            time.sleep(2.5)
        history, nodes = retry_query(app, secret, keyword)
        candidate = select_candidate(nodes, accept, bid)
        # Source-backed commercial data stays in GitHub artifact; stdout only metadata.
        result = {"blog_id": bid, "keyword": keyword, "history": history,
                  "status": "CANDIDATE_REQUIRES_EDITORIAL_REVIEW" if candidate else "BLOCKED_NO_VALID_CANDIDATE",
                  "candidate": candidate}
        items.append(result)
        print("BLOG_SCAN " + json.dumps({"blog_id": bid, "status": result["status"],
              "tries": len(history), "http": history[-1].get("http"),
              "graphql_code": history[-1].get("code"),
              "request_id": history[-1].get("request_id"),
              "itemId": candidate["itemId"] if candidate else None}, ensure_ascii=False), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"schema": "editorial-v31-affiliate-safe/v1",
         "count_checked": max_blogs, "excluded_blog_id": EXCLUDED_BLOG_ID,
         "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "no_blogger_write": True, "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("EDITORIAL_SAFE_SCAN_DONE " + json.dumps({
        "checked": max_blogs,
        "candidates": sum(item["candidate"] is not None for item in items),
        "blocked": sum(item["candidate"] is None for item in items),
        "artifact": "editorial_v31_shopee_candidates_safe.json",
        "live_publications": 0,
    }), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
