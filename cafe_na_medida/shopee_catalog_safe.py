#!/usr/bin/env python3
"""Somente consulta Shopee + curadoria fail-closed para Café na Medida.
NUNCA altera Blogger ou GitHub; não grava credenciais, não publica ofertas.
"""
from __future__ import annotations
import hashlib, json, os, re, sys, time, unicodedata
import urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blogger_policy_guard import require_product_allowed

EXPECTED_BLOG_ID = "4820923154548273510"
API = "https://open-api.affiliate.shopee.com.br/graphql"
CATEGORIES = (
    ("Moedores e Moagem",
      ("moedor de cafe manual", "moedor de cafe eletrico", "moedor de graos cafe", "moinho de cafe"),
      ("moedor", "moinho", "moagem")),
    ("Coadores e Filtros",
      ("coador de cafe", "filtro de cafe reutilizavel", "suporte coador v60 cafe", "filtro papel para cafe"),
      ("coador", "filtro", "v60")),
    ("Prensas e Cafeteiras",
      ("prensa francesa cafe", "cafeteira italiana moka", "cafeteira prensa francesa", "cafeteira cafe"),
      ("prensa francesa", "cafeteira", "moka")),
    ("Chaleiras e Precisao",
      ("balanca para cafe", "chaleira bico fino cafe", "termometro cafe", "balanca cafe barista"),
      ("balanca", "chaleira", "termometro")),
)
CONTEXT = ("cafe", "coffee", "espresso", "barista", "v60", "moka", "prensa francesa", "coado")
EXCLUDE = ("miniatura", "brinquedo", "chaveiro", "decorativo", "boneca", "adesivo", "caneca decorativa", "poster", "enfeite", "aroma artificial", "perfume", "fantasia")

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
    query = ("query CafeCatalog { productOfferV2(keyword: " +
             json.dumps(term, ensure_ascii=False) + ", sortType: 2, page: " +
             str(page) + ", limit: 20) { nodes { itemId productName imageUrl offerLink "
             "priceMin priceMax shopName ratingStar sales } pageInfo { page limit hasNextPage } } }")
    body = json.dumps({"query": query, "operationName": "CafeCatalog"},
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
        # Registrar somente a classe da falha; nunca imprimir texto bruto de provedores.
        message = " ".join(str(e.get("message", "")) for e in data["errors"] if isinstance(e, dict)).lower()
        if any(x in message for x in ("credential", "signature", "unauthorized", "authentication", "10020", "auth")):
            kind = "AUTH"
        elif any(x in message for x in ("cannot query field", "unknown argument", "unknown type", "syntax error", "operation name")):
            kind = "SCHEMA"
        elif any(x in message for x in ("rate limit", "too many", "quota", "10023")):
            kind = "RATE_LIMIT"
        else:
            kind = "OTHER"
        fail("GraphQL bloqueado: classe=" + kind)
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
    base = {"itemId":"17", "productName":"Moedor de cafe manual com mos",
            "priceMin":"29.90", "imageUrl":"https://cf.shopee.com.br/file/exemplo",
            "offerLink":"https://s.shopee.com.br/exemplo"}
    if validate(base, CATEGORIES[0][0], CATEGORIES[0][2]) is None:
        fail("teste local deveria aceitar item")
    if validate(dict(base, productName="Moedor cafe brinquedo"), CATEGORIES[0][0], CATEGORIES[0][2]):
        fail("teste local deixou passar brinquedo")
    if validate(dict(base, offerLink="https://evil.example/link"), CATEGORIES[0][0], CATEGORIES[0][2]):
        fail("teste local deixou passar domínio externo")
    print("CAFE_SELF_TEST_PASS", flush=True)

def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    app, secret = check_creds()
    products = select(app, secret)
    # SAFE: não publicar URLs afiliadas, preços ou segredos nos logs do repositório.
    digest = hashlib.sha256(",".join(sorted(p["itemId"] for p in products)).encode("utf8")).hexdigest()
    print("CAFE_SHOPEE_SAFE_PASS_NO_WRITE " + json.dumps({
        "blog_id": EXPECTED_BLOG_ID, "count": len(products),
        "categories": [name for name, _, _ in CATEGORIES],
        "selection_sha256": digest
    }, ensure_ascii=False, separators=(",", ":")), flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc)[:500], file=sys.stderr)
        raise SystemExit(2)
