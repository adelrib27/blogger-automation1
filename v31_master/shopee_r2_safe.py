#!/usr/bin/env python3
"""Shopee Affiliate API -> verified V31 R2 candidate. SAFE: NEVER writes Blogger.

Secrets are read only from environment; no raw response/error/secret logging.
HTML and JSON artifacts are generated for review, never published automatically.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

from replication_safe import load_profile, GateError

ENDPOINT = "https://open-api.affiliate.shopee.com.br/graphql"
REQUIRED = 16
KEYWORDS = {
    "Casa e Organização": ("organizador", "caixa", "estante", "prateleira", "sapateira", "gaveta"),
    "Cozinha": ("cozinha", "air fryer", "cafeteira", "panela", "utensilio", "liquidificador", "mixer"),
    "Tecnologia": ("usb", "carregador", "notebook", "mouse", "teclado", "fone", "suporte"),
    "Utilidades": ("garrafa", "termica", "luminaria", "led", "mop", "limpeza", "aspirador"),
}

def trusted(url: str, *, affiliate: bool) -> bool:
    try:
        p = urlsplit(url)
        if p.scheme != "https" or not p.hostname or p.username or p.password:
            return False
        if p.port not in (None, 443):
            return False
        host = p.hostname.lower()
        suffixes = (".shopee.com.br", "shopee.com.br", ".shope.ee", "shope.ee") if affiliate else (
            ".susercontent.com", "susercontent.com", ".shopee.com.br",
            "shopee.com.br", ".shopeeusercontent.com", "shopeeusercontent.com")
        return any(host == x or (x.startswith(".") and host.endswith(x)) for x in suffixes)
    except (ValueError, TypeError):
        return False

class ShopeeGraphQLError(GateError):
    def __init__(self, errors: object):
        super().__init__("GraphQL retornou erro; não usar resposta parcial")
        codes = []
        if isinstance(errors, list):
            for error in errors[:5]:
                if not isinstance(error, dict):
                    continue
                extension = error.get("extensions")
                code = extension.get("code", error.get("code")) if isinstance(extension, dict) else error.get("code")
                if type(code) is int and 0 <= code <= 999999:
                    codes.append(code)
                elif isinstance(code, str) and re.fullmatch(r"[0-9]{1,6}", code):
                    codes.append(int(code))
        self.system_error = isinstance(errors, list) and len(errors) == len(codes) and set(codes) == {10000}
        self.codes = tuple(codes)


def query_commercial(keyword: str, app_id: str, secret: str) -> list[dict]:
    try:
        return signed_query(keyword, app_id, secret)
    except ShopeeGraphQLError as error:
        if not error.system_error:
            raise
    print(json.dumps({"status": "SHOPEE_RETRY", "graphql_error_codes": [10000], "delay_seconds": 8}))
    time.sleep(8)
    return signed_query(keyword, app_id, secret)


def signed_query(keyword: str, app_id: str, secret: str) -> list[dict]:
    k = json.dumps(keyword, ensure_ascii=False)
    # LAB SAFE: consulta mínima documentada e observada como funcional em 1 execução
    # 12/11/2026. NÃO presume que resolve o erro intermitente GraphQL 10000.
    # Campos necessários ao motor: não exigir ordenação/listType no servidor.
    query = ("query V31R2Safe { productOfferV2(keyword: " + k +
             ", page: 1, limit: 20) { nodes {"
             " itemId productName offerLink imageUrl priceMin shopId ratingStar sales commissionRate"
             " } } }")
    body = json.dumps({"query": query, "operationName": "V31R2Safe"}, ensure_ascii=False,
                      separators=(",", ":"))
    stamp = int(time.time())
    digest = hashlib.sha256((app_id + str(stamp) + body + secret).encode("utf-8")).hexdigest()
    req = urllib.request.Request(ENDPOINT, method="POST", data=body.encode("utf-8"),
                                 headers={
                                     "Authorization": f"SHA256 Credential={app_id}, Timestamp={stamp}, Signature={digest}",
                                     "Content-Type": "application/json", "Accept": "application/json",
                                     "User-Agent": "BloggerAutomation-V31R2-SAFE/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            if res.status != 200:
                raise GateError("HTTP Shopee não aprovado")
            raw = res.read(600_000)
    except Exception as exc:
        raise GateError("Falha ao consultar Shopee; nenhum dado publicado") from None
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError):
        raise GateError("Resposta Shopee inválida") from None
    if not isinstance(data, dict):
        raise GateError("Resposta Shopee inválida")
    errors = data.get("errors")
    if errors:
        raise ShopeeGraphQLError(errors)
    payload = data.get("data")
    offers = payload.get("productOfferV2") if isinstance(payload, dict) else None
    nodes = offers.get("nodes") if isinstance(offers, dict) else None
    if not isinstance(nodes, list):
        raise GateError("Nodes da Shopee ausentes")
    return nodes

def fold_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return " ".join("".join(c for c in normalized if not unicodedata.combining(c)).split())


def match_any(title: str, terms: list[str] | tuple[str, ...]) -> bool:
    return any(re.search(r"(?<!\w)" + re.escape(term) + r"\w*", title) for term in terms)


def load_commercial_profile(path: Path) -> dict:
    profile = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(profile, dict) or profile.get("schema") != "v31-shopee-commercial/v1":
        raise GateError("Perfil comercial inválido")
    target = profile.get("target")
    store = profile.get("store")
    if (not isinstance(target, dict) or not isinstance(store, dict)
            or not re.fullmatch(r"[0-9]{10,22}", str(target.get("blog_id", "")))
            or not re.fullmatch(r"https://[a-z0-9-]+\.blogspot\.com/", str(target.get("url", "")))
            or not re.fullmatch(r"[0-9]{10,22}", str(store.get("page_id", "")))
            or store.get("page_path") != "/p/loja.html"):
        raise GateError("Destino comercial inválido")
    categories = store.get("categories")
    if not isinstance(categories, list) or len(categories) != 4:
        raise GateError("Perfil comercial exige quatro categorias")
    names = set()
    for category in categories:
        name = category.get("name") if isinstance(category, dict) else None
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80 or fold_title(name) in names:
            raise GateError("Categoria comercial inválida ou duplicada")
        names.add(fold_title(name))
        for field in ("terms", "include"):
            terms = category.get(field)
            if not isinstance(terms, list) or not 1 <= len(terms) <= 4:
                raise GateError("Termos comerciais ausentes ou fora do limite")
            if not all(isinstance(term, str) and 2 <= len(term.strip()) <= 100 for term in terms):
                raise GateError("Termo comercial inválido")
        exclude = category.get("exclude", [])
        if (not isinstance(exclude, list) or len(exclude) > 12
                or not all(isinstance(term, str) and 2 <= len(term.strip()) <= 100 for term in exclude)):
            raise GateError("Exclusão comercial inválida")
    return profile


def normalize(item: dict, category: str, *, criteria: dict | None = None) -> dict | None:
    try:
        item_id = str(item.get("itemId", ""))
        title = str(item.get("productName", "")).strip()
        link, image = str(item.get("offerLink", "")), str(item.get("imageUrl", ""))
        price = Decimal(str(item.get("priceMin", "")))
        rating_raw = item.get("ratingStar")
        rating = Decimal(str(rating_raw)) if rating_raw is not None else None
        sales = max(0, int(item.get("sales") or 0))
        # LAB SAFE: aceita titulos curtos, preservando itemId identificavel.
        if not item_id.isdigit() or len(title) < 8 or len(title) > 190:
            return None
        if not trusted(link, affiliate=True) or not trusted(image, affiliate=False):
            return None
        if not price.is_finite() or not (Decimal("1") <= price <= Decimal("100000")):
            return None
        # LAB SAFE: nota 3,5+; negativos, NaN e notas acima de 5 continuam bloqueados.
        if rating is not None and (not rating.is_finite() or not (Decimal("3.5") <= rating <= Decimal("5"))):
            return None
        # LAB SAFE: tolerancia a acentos e plural/sufixo no termo, mantendo fronteira de palavra.
        if criteria is None:
            folded = "".join(c for c in unicodedata.normalize("NFKD", title.casefold())
                             if not unicodedata.combining(c))
            if not match_any(folded, KEYWORDS[category]):
                return None
        else:
            folded = fold_title(title)
            if not match_any(folded, [fold_title(term) for term in criteria["include"]]):
                return None
            if match_any(folded, [fold_title(term) for term in criteria.get("exclude", [])]):
                return None
        return {"item_id": item_id, "title": title, "offer_link": link,
                "image": image, "price": str(price), "rating": str(rating) if rating else None,
                "sales": sales, "category": category, "shop_id": str(item.get("shopId", ""))}
    except (InvalidOperation, TypeError, ValueError, KeyError):
        return None

def choose(profile: dict, by_category: dict[str, list[dict]]) -> list[dict]:
    chosen, seen_items, shops = [], set(), {}
    categories = profile["store"]["categories"]
    if set(by_category) != {x["name"] for x in categories}:
        raise GateError("Categorias não correspondem ao perfil")
    commercial = profile.get("schema") == "v31-shopee-commercial/v1"
    for category in categories:
        name = category["name"]
        criteria = category if commercial else None
        candidates = [p for x in by_category[name] if (p := normalize(x, name, criteria=criteria))]
        candidates.sort(key=lambda a: (-a["sales"], a["item_id"]))
        selected = []
        for p in candidates:
            if p["item_id"] in seen_items:
                continue
            shop = p["shop_id"]
            # LAB SAFE: expande limite de vendedor de 2 para 4, sem permitir loja unica dominar 16.
            if shop and shops.get(shop, 0) >= 4:
                continue
            selected.append(p)
            seen_items.add(p["item_id"])
            if shop:
                shops[shop] = shops.get(shop, 0) + 1
            if len(selected) == 4:
                break
        if len(selected) != 4:
            if commercial:
                raise GateError(f"Categoria sem quatro ofertas verificadas: {name} ({len(selected)}/4)")
            raise GateError("Categoria sem quatro ofertas verificadas")
        chosen.extend(selected)
    if len(chosen) != REQUIRED or len(seen_items) != REQUIRED:
        raise GateError("16 ofertas únicas obrigatórias")
    return chosen

def render(products: list[dict], *, lab_url: str) -> str:
    if len(products) != REQUIRED or len({p["item_id"] for p in products}) != REQUIRED:
        raise GateError("render exige 16 produtos únicos")
    out = ("<!-- V31_R56_STORE_AUTO_START -->\n" + render_cards(products, lab_only=True)
           + "\n<!-- V31_R56_STORE_AUTO_END -->")
    if (out.count('class="ub-product-card"') != REQUIRED or
            out.count('data-item-id="') != REQUIRED or
            out.count('rel="nofollow sponsored noopener"') != REQUIRED * 2):
        raise GateError("HTML não passou no contrato 16/16")
    return out


def render_cards(products: list[dict], *, lab_only: bool = False) -> str:
    esc = lambda x: html.escape(str(x), quote=True)
    lab_attribute = ' data-lab-only="true"' if lab_only else ''
    parts = ['<section class="ub-store-r56" data-v31-source="shopee-api"' + lab_attribute + '>',
             '<h2>Ofertas selecionadas da Shopee</h2>',
             '<p>Preços e disponibilidade podem mudar. Confira na Shopee antes de comprar.</p>']
    for cat in dict.fromkeys(p["category"] for p in products):
        parts += ['<section class="ub-store-category"><h3>' + esc(cat) + '</h3>',
                  '<div class="ub-store-grid">']
        for p in products:
            if p["category"] != cat:
                continue
            rating = '<span class="ub-product-rating">Avaliação: ' + esc(p["rating"]) + '</span>' if p["rating"] else ''
            price = Decimal(p["price"])
            brl = f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            parts.append(
                '<article class="ub-product-card" data-item-id="' + esc(p["item_id"]) + '">'
                '<a class="ub-product-image" href="' + esc(p["offer_link"]) + '" target="_blank" rel="nofollow sponsored noopener">'
                '<img alt="' + esc(p["title"]) + '" src="' + esc(p["image"]) + '" loading="lazy"/></a>'
                '<div class="ub-product-body"><span class="ub-product-tag">' + esc(cat) + '</span>'
                '<h4 class="ub-product-title">' + esc(p["title"]) + '</h4>'
                '<div class="ub-product-price-row"><strong class="ub-product-price">' + brl + '</strong></div>'
                + rating +
                '<a class="ub-product-action" href="' + esc(p["offer_link"]) + '" target="_blank" rel="nofollow sponsored noopener">Ver oferta na Shopee</a>'
                '</div></article>')
        parts += ['</div></section>']
    disclosure = "Este laboratório" if lab_only else "Este blog"
    parts += ['<p class="ub-store-note">' + disclosure
              + ' pode receber comissão por compras elegíveis realizadas pelos links de afiliado, sem custo extra pela utilização do link.</p>',
              '</section>']
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    profiles = ap.add_mutually_exclusive_group()
    profiles.add_argument("--profile", default=str(Path(__file__).parent / "profiles" / "lab_r2_v31_r52_r55.json"))
    profiles.add_argument("--commercial-profile", type=Path)
    ap.add_argument("--check-commercial-profile", action="store_true")
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    profile = (load_commercial_profile(args.commercial_profile) if args.commercial_profile
               else load_profile(Path(args.profile)))
    if args.check_commercial_profile:
        if not args.commercial_profile:
            ap.error("--check-commercial-profile exige --commercial-profile")
        print(json.dumps({"status": "V31_COMMERCIAL_PROFILE_OK", "writes_blogger": False,
                          "blog_id": profile["target"]["blog_id"]}))
        return 0
    if args.self_test:
        assert trusted("https://s.shopee.com.br/abc", affiliate=True)
        assert not trusted("https://s.shopee.com.br.evil.com/abc", affiliate=True)
        assert not trusted("http://s.shopee.com.br/abc", affiliate=True)
        assert normalize({"itemId": "1", "productName": "Carregador USB de parede para notebook",
                          "offerLink": "https://s.shopee.com.br/123",
                          "imageUrl": "https://down-br.img.susercontent.com/abc",
                          "priceMin": "52.9", "ratingStar": "4.7"}, "Tecnologia")
        print(json.dumps({"status": "V31_R56_OFFLINE_SELFTEST_OK", "writes_blogger": False}))
        return 0
    if args.out_dir is None:
        raise GateError("--out-dir é obrigatório")
    app_id, secret = os.environ.get("SHOPEE_APP_ID", "").strip(), os.environ.get("SHOPEE_SECRET", "").strip()
    if not re.fullmatch(r"[0-9]+", app_id) or not secret:
        raise GateError("Credenciais não disponíveis no ambiente seguro")
    from store_stock_commission_safe import commission_eligible, select_verified

    query = query_commercial if args.commercial_profile else signed_query
    groups = {}
    successful_searches = 0
    skipped_searches = 0
    for cat in profile["store"]["categories"]:
        seen, all_nodes = set(), []
        category_searches = category_errors = received_nodes = 0
        for keyword in cat["terms"]:
            try:
                nodes = query(keyword, app_id, secret)
            except ShopeeGraphQLError as error:
                if not args.commercial_profile or not error.system_error:
                    raise
                skipped_searches += 1
                category_errors += 1
                continue
            successful_searches += 1
            category_searches += 1
            received_nodes += len(nodes)
            for raw in nodes:
                if not isinstance(raw, dict):
                    raise GateError("Oferta Shopee inválida")
                rid = str(raw.get("itemId", ""))
                if args.commercial_profile and not commission_eligible(raw, verified_affiliate_response=True):
                    continue
                if rid not in seen:
                    all_nodes.append(raw)
                    seen.add(rid)
        name = cat["name"]
        groups[name] = all_nodes
        if args.commercial_profile:
            valid = sum(normalize(row, name, criteria=cat) is not None for row in all_nodes)
            print(json.dumps({"status": "SHOPEE_CATEGORY_SUMMARY", "category": name,
                              "successful_searches": category_searches,
                              "skipped_system_errors": category_errors,
                              "received_nodes": received_nodes,
                              "unique_positive_commission": len(all_nodes),
                              "eligible_before_catalog_selection": valid}))
    if args.commercial_profile:
        print(json.dumps({"status": "SHOPEE_COLLECTION_SUMMARY",
                          "successful_searches": successful_searches,
                          "skipped_system_errors": skipped_searches}))
        if not successful_searches:
            raise GateError("Nenhuma resposta válida da Shopee")
    # Gate comercial V31: comissao positiva verificada no retorno da API
    # sem taxa percentual minima e sem exigir comissao extra do vendedor.
    products = select_verified(profile, groups)
    content = render(products, lab_url=profile["target"]["url"])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if any(args.out_dir.iterdir()):
        raise GateError("Diretório de saída deve estar vazio")
    (args.out_dir / "v31_r2_store.html").write_text(content, encoding="utf-8")
    catalog = {"blog_id": profile["target"]["blog_id"], "count": 16, "products": products}
    if args.commercial_profile:
        catalog["page_id"] = profile["store"]["page_id"]
        catalog["store_url"] = profile["target"]["url"].rstrip("/") + profile["store"]["page_path"]
    (args.out_dir / "v31_r2_products.json").write_text(
        json.dumps(catalog,
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "V31_R56_SHOPEE_SAFE_FETCH_OK_NO_BLOGGER_WRITES",
                      "blog_id": profile["target"]["blog_id"], "products": 16,
                      "categories": 4, "writes_blogger": False}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        result = {"status": "V31_R56_SHOPEE_SAFE_FAIL_CLOSED",
                  "reason_type": type(exc).__name__, "writes_blogger": False}
        if isinstance(exc, ShopeeGraphQLError):
            result["graphql_error_codes"] = exc.codes
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(2)
