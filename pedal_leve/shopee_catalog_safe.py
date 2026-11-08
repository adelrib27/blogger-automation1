#!/usr/bin/env python3
"""Somente consulta Shopee + curadoria fail-closed para nova loja Pedal Leve.
NUNCA altera Blogger ou GitHub; não grava credenciais, não publica ofertas.
"""
from __future__ import annotations
import hashlib, json, os, re, sys, time, unicodedata
import urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blogger_policy_guard import require_product_allowed

EXPECTED_BLOG_ID = "4073458513010284301"
API = "https://open-api.affiliate.shopee.com.br/graphql"
CATEGORIES = (
    ("Segurança e Visibilidade", ("farol bicicleta", "lanterna traseira bicicleta", "luz sinalizador bicicleta", "refletor bicicleta"),
     ("farol", "lanterna", "luz traseira", "refletor", "sinalizador", "pisca")),
    ("Manutenção e Ferramentas", ("bomba ar bicicleta", "kit remendo bicicleta", "lubrificante corrente bike", "ferramenta bicicleta"),
     ("bomba", "remendo", "reparo", "lubrificante", "ferramenta", "corrente", "calibrador")),
    ("Bolsas e Transporte", ("bolsa quadro bicicleta", "bolsa selim bicicleta", "alforje bike", "suporte celular guidão bicicleta"),
     ("bolsa", "alforje", "suporte", "bagageiro", "cesto", "estojo")),
    ("Conforto e Acessórios", ("luva ciclismo", "manopla bicicleta", "suporte caramanhola bicicleta", "selim bike"),
     ("luva", "manopla", "caramanhola", "selim", "garrafa", "squeeze", "pedal")),
)
CONTEXT = ("bicicleta", "bike", "ciclismo", "ciclista", "mtb", "pedal", "mountain bike", "ciclovia")
EXCLUDE = ("miniatura", "brinquedo", "chaveiro", "motocicleta", "moto ", "motoboy", "patinete", "boneca", "bicicleta ergometrica")

def norm(text: str) -> str:
    txt = unicodedata.normalize("NFKD", str(text or "").lower())
    return "".join(c for c in txt if not unicodedata.combining(c))

def fail(reason: str) -> None:
    raise RuntimeError("FAIL_CLOSED: " + reason)

def check_creds() -> tuple[str, str]:
    app = os.getenv("SHOPEE_APP_ID", "").strip()
    secret = os.getenv("SHOPEE_SECRET", "").strip()
    if not app or not secret:
        fail("credenciais Shopee ausentes")
    return app, secret

def fetch(app: str, secret: str, term: str, page: int) -> list[dict]:
    query = ("query PedalCatalog { productOfferV2(keyword: " +
             json.dumps(term, ensure_ascii=False) + ", sortType: 2, page: " +
             str(page) + ", limit: 20) { nodes { itemId productName imageUrl offerLink "
             "priceMin priceMax shopName ratingStar sales } pageInfo { page limit hasNextPage } } }")
    body = json.dumps({"query": query, "operationName": "PedalCatalog"},
                      ensure_ascii=False, separators=(",", ":"))
    ts = str(int(time.time()))
    sign = hashlib.sha256((app + ts + body + secret).encode("utf8")).hexdigest()
    auth = "SHA256 Credential=" + app + ", Timestamp=" + ts + ", Signature=" + sign
    req = urllib.request.Request(API, data=body.encode("utf8"), method="POST",
          headers={"Authorization": auth, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=28) as response:
            if response.status != 200:
                fail("Shopee HTTP não 200")
            data = json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        fail("consulta API indisponível: " + type(exc).__name__)
    if data.get("errors"):
        fail("GraphQL informou erro; não selecionar produtos")
    offers = (data.get("data") or {}).get("productOfferV2") or {}
    if not isinstance(offers.get("nodes"), list):
        fail("Shopee sem nodes válidos")
    return offers["nodes"]

def validate(row: dict, category: str, terms: tuple[str, ...]) -> dict | None:
    try:
        item = str(row.get("itemId") or "").strip()
        name = str(row.get("productName") or "").strip()
        title = norm(name)
        price = float(row.get("priceMin") or 0)
        image = str(row.get("imageUrl") or "").strip()
        link = str(row.get("offerLink") or "").strip()
        if (not item.isdecimal() or not name or not 0 < price <= 10000
            or not image.startswith("https://") or not link.startswith("https://")
            or not any(x in title for x in terms)
            or not any(x in title for x in CONTEXT)
            or any(x in title for x in EXCLUDE)
            or re.search(r"\bmotos?\b|moto/|motocicl", title)):
            return None
        # Evita que um selim com detalhe refletivo seja catalogado como iluminação.
        if category == "Segurança e Visibilidade" and any(x in title for x in ("selim", "banco", "manopla", "luva")):
            return None
        product = {"itemId": item, "productName": name, "priceMin": price,
                   "imageUrl": image, "offerLink": link, "category": category,
                   "shopName": str(row.get("shopName") or "").strip()[:140]}
        require_product_allowed(product)
        return product
    except (ValueError, TypeError, RuntimeError):
        return None

def select(app: str, secret: str) -> list[dict]:
    """Tenta quatro tipos de produto por categoria; sem catálogo mínimo, STOP."""
    used: set[str] = set()
    selected: list[dict] = []
    for category, keywords, terms in CATEGORIES:
        pool: dict[str, dict] = {}
        per_keyword: list[dict] = []
        selected_in_cat: set[str] = set()
        for word in keywords:
            candidates: list[dict] = []
            for page in (1, 2):
                for row in fetch(app, secret, word, page):
                    product = validate(row, category, terms)
                    if product and product["itemId"] not in used:
                        pool[product["itemId"]] = product
                        candidates.append(product)
                if candidates:
                    break
            # Uma oferta diferente por busca sempre que a API permitir.
            pick = next((x for x in candidates if x["itemId"] not in selected_in_cat), None)
            if pick:
                per_keyword.append(pick)
                selected_in_cat.add(pick["itemId"])
        if len(pool) < 4:
            fail("menos de quatro produtos semanticamente válidos para " + category)
        picks = list(per_keyword)
        for p in pool.values():
            if len(picks) >= 4:
                break
            if p["itemId"] not in selected_in_cat:
                picks.append(p)
                selected_in_cat.add(p["itemId"])
        picks = picks[:4]
        if len(picks) != 4 or len({p["itemId"] for p in picks} & used):
            fail("diversidade ou exclusividade insuficiente para " + category)
        selected.extend(picks)
        used.update(p["itemId"] for p in picks)
        print("CATEGORY_SAFE_PASS", category, "selected", len(picks),
              "candidates", len(pool), "unique_queries", len(per_keyword), flush=True)
    if len(selected) != 16 or len(used) != 16:
        fail("precisa de 16 ofertas únicas")
    return selected

def self_test() -> None:
    base = {"itemId":"17", "productName":"Farol LED para bicicleta USB",
            "priceMin":"29.90", "imageUrl":"https://cf.shopee.com.br/file/exemplo",
            "offerLink":"https://s.shopee.com.br/exemplo"}
    if validate(base, CATEGORIES[0][0], CATEGORIES[0][2]) is None:
        fail("teste local deveria aceitar item")
    if validate(dict(base, productName="Farol para motocicleta"), CATEGORIES[0][0], CATEGORIES[0][2]):
        fail("teste local deixou passar moto")
    if validate(dict(base, offerLink="https://evil.example/link"), CATEGORIES[0][0], CATEGORIES[0][2]):
        fail("teste local deixou passar domínio externo")
    print("PEDAL_SELF_TEST_PASS", flush=True)

def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    app, secret = check_creds()
    products = select(app, secret)
    # São links comerciais que serão publicados; não imprimir ID/segredo da API.
    print("PEDAL_CATALOG_JSON=" + json.dumps({
        "blog_id": EXPECTED_BLOG_ID, "count": len(products), "products": products
    }, ensure_ascii=False, separators=(",", ":")), flush=True)
    print("PEDAL_SHOPEE_SAFE_PASS_NO_WRITE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc)[:500], file=sys.stderr)
        raise SystemExit(2)
