#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "blogger_stores" / "data"
SCAN_DIR = DATA_DIR / "conecta_achados_scan"
HISTORY_PATH = DATA_DIR / "conecta_achados_rotation.json"
SELECTION_PATH = DATA_DIR / "conecta_achados_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_conecta_achados.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_conecta_achados_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "1719259388907013414"
POST_ID = "259394788951394758"
STORE_PAGE = "https://conectaachados.blogspot.com/p/loja.html"
STORE_POST_URL = "https://conectaachados.blogspot.com/2026/11/loja.html"
ITEMS_PER_CATEGORY = 4
RECENT_DAYS = max(1, min(int(os.getenv("CONECTA_STORE_RECENT_DAYS", "14")), 90))

CATEGORY_META = {
    "Casa & Organizacao": ("Casa & Organização", "bls-casa-organizacao", "Casa"),
    "Cozinha & Utilidades": ("Cozinha & Utilidades", "bls-cozinha-utilidades", "Cozinha"),
    "Tecnologia & Acessorios": ("Tecnologia & Acessórios", "bls-tecnologia", "Tecnologia"),
    "Beleza & Cuidados": ("Beleza & Cuidados", "bls-beleza", "Beleza"),
    "Dia a Dia & Praticidade": ("Dia a Dia & Praticidade", "bls-dia-a-dia", "Dia a dia"),
}

STORE_START = "<!-- BLOGGER_LIQ_STORE_AUTO_START -->"
STORE_END = "<!-- BLOGGER_LIQ_STORE_AUTO_END -->"
HERO_MARKERS = [
    ("<!-- BLOGGER_LIQ_HERO_AUTO_1_START -->", "<!-- BLOGGER_LIQ_HERO_AUTO_1_END -->"),
    ("<!-- BLOGGER_LIQ_HERO_AUTO_2_START -->", "<!-- BLOGGER_LIQ_HERO_AUTO_2_END -->"),
    ("<!-- BLOGGER_LIQ_HERO_AUTO_3_START -->", "<!-- BLOGGER_LIQ_HERO_AUTO_3_END -->"),
]

# Estes caminhos precisam estar no ambiente antes de importar o motor Shopee,
# porque o módulo compartilhado congela os paths no import.
os.environ["SHOPEE_OPPORTUNITIES_CONFIG"] = str(CONFIG_PATH)
os.environ["SHOPEE_INTENT_RULES"] = str(INTENT_RULES_PATH)
os.environ["SHOPEE_OUTPUT_DIR"] = str(SCAN_DIR)
os.environ["SHOPEE_CATEGORY"] = "all"
os.environ.setdefault("SHOPEE_TOP_N", "180")

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "radar_tech_br" / "src"))

import shopee_oportunidades_v23 as shopee_v23  # noqa: E402
from blogger_policy_guard import require_product_allowed  # noqa: E402
from criar_rascunho import criar_servico_blogger  # noqa: E402
from refresh_blogger_offer_links import generate_short_link, resolved_to_shopee  # noqa: E402


def now_local() -> datetime:
    return datetime.now(ZoneInfo("America/Recife"))


def norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def as_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def money(value) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return ""


def price_text(product: dict) -> str:
    pmin = product.get("priceMin")
    pmax = product.get("priceMax")
    if pmin is None:
        return "Confira o preço"
    if pmax is None:
        pmax = pmin
    try:
        a, b = float(pmin), float(pmax)
    except Exception:
        return "Confira o preço"
    return money(a) if abs(a - b) < 0.005 else f"A partir de {money(a)}"


def affiliate_url(product: dict) -> str:
    return str(product.get("affiliateUrl") or product.get("offerLink") or "").strip()


def published_recent_ids(history: dict) -> set[str]:
    cutoff = now_local() - timedelta(days=RECENT_DAYS)
    result: set[str] = set()
    for run in history.get("runs") or []:
        if str(run.get("source") or "") not in {"seed_from_current_blogger_store", "blogger_published"}:
            continue
        try:
            dt = datetime.fromisoformat(str(run.get("timestamp") or ""))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("America/Recife"))
        except Exception:
            continue
        if dt < cutoff:
            continue
        for item in run.get("items") or []:
            item_id = str(item.get("itemId") or "").strip()
            if item_id:
                result.add(item_id)
    return result


def last_published_ids(history: dict) -> set[str]:
    runs = history.get("runs") or []
    if not runs:
        return set()
    return {
        str(item.get("itemId") or "").strip()
        for item in (runs[-1].get("items") or [])
        if str(item.get("itemId") or "").strip()
    }


def valid_candidate(product: dict) -> bool:
    return bool(
        str(product.get("itemId") or "").strip()
        and str(product.get("productName") or "").strip()
        and str(product.get("shopName") or "").strip()
        and str(product.get("imageUrl") or "").startswith("http")
        and str(product.get("productLink") or "").startswith("http")
        and as_float(product.get("priceMin")) > 0
    )


def group_candidates(ranking: list[dict], category_names: list[str]) -> dict[str, list[dict]]:
    grouped = {name: [] for name in category_names}
    seen = {name: set() for name in category_names}
    for product in ranking:
        if not valid_candidate(product):
            continue
        item_id = str(product.get("itemId") or "").strip()
        for category in [str(c or "").strip() for c in (product.get("categories") or [])]:
            if category in grouped and item_id not in seen[category]:
                grouped[category].append(product)
                seen[category].add(item_id)
    return grouped


def final_keyword_gate(product: dict, keyword: str) -> bool:
    title = norm(product.get("productName") or "")
    key = norm(keyword)
    blocks = {
        "fritadeira eletrica": ["forma", "papel", "cesto", "capa", "grade", "resistencia", "puxador", "botao", "acessorio", "tapete"],
        "mixer eletrico": ["haste para mixer", "copo para mixer", "lamina para mixer", "peca para mixer"],
        "fone bluetooth": ["capa para fone", "case para fone", "estojo para fone", "almofada para fone", "cabo para fone"],
        "smartwatch": ["pulseira", "pelicula", "carregador para smartwatch", "capa para smartwatch", "bracelete"],
        "carregador usb c": ["cabo usb", "cabo type", "conector avulso"],
        "caixa de som bluetooth": ["capa para caixa", "suporte para caixa", "placa para caixa", "bateria para caixa"],
        "aparador de pelos": ["papa bolinhas", "roupa", "roupas", "lamina de reposicao"],
        "escova secadora": ["capa para escova", "suporte para escova", "peca para escova"],
        "secador de cabelo": ["difusor", "bico para secador", "suporte para secador", "resistencia para secador", "cabo para secador"],
        "chapinha cabelo": ["capa para chapinha", "suporte para chapinha", "bolsa para chapinha"],
        "mochila notebook": ["capa para notebook", "adesivo para mochila"],
        "garrafa termica": ["tampa para garrafa", "vedacao", "anel de vedacao", "canudo avulso"],
        "lanterna recarregavel": ["suporte para lanterna", "bateria para lanterna", "capa para lanterna", "lampada para lanterna"],
        "guarda chuva automatico": ["capa para guarda chuva", "suporte para guarda chuva", "miniatura", "chaveiro"],
    }
    if any(term in title for term in blocks.get(key, [])):
        return False
    positive = {
        "fritadeira eletrica": lambda: "fritadeira" in title and any(x in title for x in ["eletrica", "air fryer", "airfryer", "sem oleo"]),
        "fone bluetooth": lambda: any(x in title for x in ["fone", "headphone", "earbuds"]) and any(x in title for x in ["bluetooth", "sem fio", "wireless"]),
        "smartwatch": lambda: any(x in title for x in ["smartwatch", "relogio inteligente"]),
        "carregador usb c": lambda: any(x in title for x in ["carregador", "fonte"]) and any(x in title for x in ["usb c", "type c", "pd", "power delivery"]),
        "caixa de som bluetooth": lambda: any(x in title for x in ["caixa de som", "speaker"]) and any(x in title for x in ["bluetooth", "sem fio", "wireless"]),
        "aparador de pelos": lambda: any(x in title for x in ["aparador", "maquina de barbear", "barbeador eletrico"]),
        "escova secadora": lambda: "escova" in title and any(x in title for x in ["secadora", "secador", "ar quente"]),
        "secador de cabelo": lambda: "secador" in title and any(x in title for x in ["cabelo", "cabelos"]),
        "chapinha cabelo": lambda: any(x in title for x in ["chapinha", "prancha"]) and any(x in title for x in ["cabelo", "cabelos", "alisadora", "alisador"]),
        "mochila notebook": lambda: "mochila" in title and any(x in title for x in ["notebook", "laptop", "executiva", "trabalho"]),
        "garrafa termica": lambda: "garrafa" in title and "termica" in title,
        "lanterna recarregavel": lambda: "lanterna" in title and any(x in title for x in ["recarregavel", "usb"]),
        "guarda chuva automatico": lambda: "guarda chuva" in title and any(x in title for x in ["automatico", "abre fecha", "abertura automatica"]),
    }
    return positive[key]() if key in positive else True


def run_conecta_regression_checks(rules_doc: dict) -> None:
    cases = [
        ("Kit 6 Formas Silicone para Air Fryer", "fritadeira eletrica", False),
        ("Fritadeira Elétrica Air Fryer 5L 1500W", "fritadeira eletrica", True),
        ("Capa Silicone para Fone Bluetooth", "fone bluetooth", False),
        ("Fone Bluetooth TWS Sem Fio", "fone bluetooth", True),
        ("Pulseira Silicone para Smartwatch 44mm", "smartwatch", False),
        ("Smartwatch Relógio Inteligente Tela AMOLED", "smartwatch", True),
        ("Cabo USB C 2 Metros Turbo", "carregador usb c", False),
        ("Carregador USB C PD 35W Fonte Turbo", "carregador usb c", True),
        ("Papa Bolinhas Tira Pelos de Roupa Elétrico", "aparador de pelos", False),
        ("Máquina de Barbear Aparador de Pelos 3 em 1", "aparador de pelos", True),
        ("Difusor Universal para Secador de Cabelo", "secador de cabelo", False),
        ("Secador de Cabelo 2000W Profissional", "secador de cabelo", True),
        ("Tampa Reposição Garrafa Térmica", "garrafa termica", False),
        ("Garrafa Térmica Inox 1 Litro", "garrafa termica", True),
        ("Bateria Reposição para Lanterna", "lanterna recarregavel", False),
        ("Lanterna Recarregável USB LED", "lanterna recarregavel", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        accepted = bool(shopee_v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        actual = accepted and final_keyword_gate({"productName": title}, keyword)
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha na regressão semântica Conecta: " + json.dumps(failures, ensure_ascii=False))
    print(f"CONECTA_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


def choose_one_per_keyword(ranking: list[dict], config: dict, blocked_ids: set[str], last_ids: set[str]):
    categories = config.get("categories") or {}
    grouped = group_candidates(ranking, list(categories))
    chosen: dict[str, list[dict]] = {}
    coverage: dict[str, list[str]] = {}
    used: set[str] = set()
    fallback_ids: list[str] = []
    carry_ids: list[str] = []

    for category, keywords in categories.items():
        picks = []
        covered = []
        pool = grouped.get(category) or []
        for keyword in keywords:
            selected = None
            phases = [
                ("new", lambda iid: iid not in blocked_ids),
                ("fallback_older", lambda iid: iid not in last_ids),
                ("carry_forward_last", lambda iid: iid in last_ids),
            ]
            for mode, allowed in phases:
                for product in pool:
                    item_id = str(product.get("itemId") or "").strip()
                    matched = [str(v) for v in (product.get("intentMatchedKeywords") or product.get("keywords") or [])]
                    if keyword not in matched or not item_id or item_id in used or not allowed(item_id):
                        continue
                    if not final_keyword_gate(product, keyword):
                        continue
                    selected = dict(product)
                    selected["selectedSourceKeyword"] = keyword
                    selected["rotationSelectionMode"] = mode
                    if mode == "fallback_older":
                        fallback_ids.append(item_id)
                        print(f"ROTATION_FALLBACK: {category} / {keyword} / {item_id}")
                    elif mode == "carry_forward_last":
                        carry_ids.append(item_id)
                        print(f"ROTATION_CARRY_FORWARD: {category} / {keyword} / {item_id}")
                    break
                if selected is not None:
                    break
            if selected is None:
                raise RuntimeError(f"SAFE bloqueado: sem produto válido para '{keyword}' em '{category}'.")
            picks.append(selected)
            covered.append(keyword)
            used.add(str(selected.get("itemId")))
        if len(picks) != 4 or len(set(covered)) != 4:
            raise RuntimeError(f"SAFE bloqueado: cobertura incompleta em {category}: {covered}")
        chosen[category] = picks
        coverage[category] = covered

    if len(used) != 20:
        raise RuntimeError(f"SAFE bloqueado: {len(used)} IDs únicos; esperado 20.")
    return chosen, coverage, fallback_ids, carry_ids


def generate_links(chosen: dict[str, list[dict]], app_id: str, secret: str):
    normalized: dict[str, list[dict]] = {}
    checks: dict[str, dict] = {}
    seen = set()
    index = 0
    for category, products in chosen.items():
        normalized[category] = []
        for product in products:
            index += 1
            item_id = str(product.get("itemId") or "").strip()
            if item_id in seen:
                raise RuntimeError(f"Item duplicado: {item_id}")
            seen.add(item_id)
            origin = str(product.get("productLink") or "").strip()
            short = generate_short_link(app_id, secret, origin)
            ok, final_url, status = resolved_to_shopee(short)
            if not ok:
                raise RuntimeError(f"Link Shopee não resolveu: item={item_id} final={final_url} status={status}")
            normalized[category].append({
                "itemId": item_id,
                "productName": str(product.get("productName") or "").strip(),
                "shopName": str(product.get("shopName") or "").strip(),
                "priceMin": product.get("priceMin"),
                "priceMax": product.get("priceMax"),
                "imageUrl": str(product.get("imageUrl") or "").strip(),
                "productLink": origin,
                "affiliateUrl": short,
                "offerLink": short,
                "category": category,
                "sourceKeyword": str(product.get("selectedSourceKeyword") or ""),
                "rotationSelectionMode": str(product.get("rotationSelectionMode") or "new"),
                "source": "shopee_affiliate_open_api",
                "discoveredAt": now_local().isoformat(),
            })
            checks[item_id] = {"shortLink": short, "resolvedUrl": final_url, "httpStatus": status}
            print(f"[{index:02d}/20] {category} — {item_id}: semântica e link validados.")
            time.sleep(0.10)
    if len(seen) != 20 or len(checks) != 20:
        raise RuntimeError("Validação de links incompleta.")
    return normalized, checks


def safe_scan() -> int:
    app_id = required_env("SHOPEE_APP_ID")
    secret = required_env("SHOPEE_SECRET")
    if app_id != EXPECTED_APP_ID:
        raise RuntimeError("SHOPEE_APP_ID não corresponde ao AppID autorizado do projeto.")

    config = load_json(CONFIG_PATH, {})
    categories = config.get("categories") or {}
    if len(categories) != 5 or any(len(v) != 4 for v in categories.values()):
        raise RuntimeError("Config inválida: esperado 5 categorias × 4 intenções.")
    rules_doc = load_json(INTENT_RULES_PATH, {})
    run_conecta_regression_checks(rules_doc)
    shopee_v23.run_regression_checks = run_conecta_regression_checks

    history = load_json(HISTORY_PATH, {"version": 1, "blogId": BLOG_ID, "runs": []})
    if str(history.get("blogId") or BLOG_ID) != BLOG_ID:
        raise RuntimeError("Histórico pertence a outro blog.")
    blocked = published_recent_ids(history)
    last_ids = last_published_ids(history)
    print(f"Conecta Achados — SAFE. IDs bloqueados: {len(blocked)}; última rodada: {len(last_ids)}")

    ranking = shopee_v23.scan_v23()
    print(f"Ranking Shopee recebido: {len(ranking)}")
    chosen, coverage, fallback_ids, carry_ids = choose_one_per_keyword(ranking, config, blocked, last_ids)
    normalized, checks = generate_links(chosen, app_id, secret)
    ids = [item["itemId"] for values in normalized.values() for item in values]

    selection = {
        "schemaVersion": 1,
        "status": "SAFE_READY",
        "publishReady": True,
        "dryRun": True,
        "blogId": BLOG_ID,
        "timestamp": now_local().isoformat(),
        "itemsPerCategory": 4,
        "categoryCount": 5,
        "totalItems": 20,
        "uniqueItemIds": len(set(ids)),
        "recentWindowDays": RECENT_DAYS,
        "blockedPublishedIdsCount": len(blocked),
        "lastPublishedIdsCount": len(last_ids),
        "categories": normalized,
        "keywordCoverage": coverage,
        "rotationFallback": {
            "policy": "fresh_then_older_then_last_only_if_no_valid_alternative",
            "olderItemIds": fallback_ids,
            "carryForwardLastItemIds": carry_ids,
        },
        "affiliateLinkGeneration": {
            "method": "generateShortLink",
            "appId": EXPECTED_APP_ID,
            "validatedCount": len(checks),
            "allResolvedToShopee": True,
        },
        "semanticValidation": {
            "rulesFile": "config/shopee_conecta_achados_intent_rules.json",
            "profileVersion": 1,
            "strictAccessoriesBlocked": True,
            "oneProductPerKeyword": True,
            "finalProductGate": True,
        },
        "gates": {
            "fiveCategories": len(normalized) == 5,
            "fourPerCategory": all(len(v) == 4 for v in normalized.values()),
            "twentyUnique": len(ids) == 20 and len(set(ids)) == 20,
            "allLinksResolved": len(checks) == 20,
            "semanticRulesApplied": True,
            "finalProductGate": True,
            "failClosed": True,
        },
    }
    if not all(selection["gates"].values()):
        raise RuntimeError(f"SAFE bloqueado: gates finais falharam: {selection['gates']}")
    save_atomic(SELECTION_PATH, selection)
    print(f"CONECTA_SAFE_READY: 20 produtos; 20 intenções; links 20/20; fallback={len(fallback_ids)}; carry={len(carry_ids)}; Blogger não alterado.")
    return 0


def validate_selection(data: dict) -> list[dict]:
    if int(data.get("schemaVersion") or 0) != 1:
        raise RuntimeError("Seleção Conecta precisa estar em schemaVersion=1.")
    if data.get("status") != "SAFE_READY" or data.get("publishReady") is not True:
        raise RuntimeError("Seleção não está SAFE_READY/publishReady.")
    if str(data.get("blogId") or "") != BLOG_ID:
        raise RuntimeError("blogId da seleção não corresponde ao Conecta Achados.")
    if int(data.get("categoryCount") or 0) != 5 or int(data.get("totalItems") or 0) != 20 or int(data.get("uniqueItemIds") or 0) != 20:
        raise RuntimeError("Seleção não contém 5 categorias / 20 produtos únicos.")
    link_meta = data.get("affiliateLinkGeneration") or {}
    if str(link_meta.get("appId") or "") != EXPECTED_APP_ID or int(link_meta.get("validatedCount") or 0) != 20 or link_meta.get("allResolvedToShopee") is not True:
        raise RuntimeError("Links afiliados não estão validados 20/20.")
    semantic = data.get("semanticValidation") or {}
    if not all(semantic.get(k) is True for k in ["strictAccessoriesBlocked", "oneProductPerKeyword", "finalProductGate"]):
        raise RuntimeError("Gates semânticos do Conecta incompletos.")
    gates = data.get("gates") or {}
    if not gates or not all(bool(v) for v in gates.values()):
        raise RuntimeError(f"Gates SAFE inválidos: {gates}")
    categories = data.get("categories") or {}
    if set(categories) != set(CATEGORY_META) or any(len(categories.get(k) or []) != 4 for k in CATEGORY_META):
        raise RuntimeError(f"Categorias inesperadas/incompletas: {list(categories)}")
    coverage = data.get("keywordCoverage") or {}
    if set(coverage) != set(CATEGORY_META) or any(len(set(coverage.get(k) or [])) != 4 for k in CATEGORY_META):
        raise RuntimeError("Cobertura de 20 intenções incompleta.")
    products = [p for key in CATEGORY_META for p in (categories.get(key) or [])]
    ids = [str(p.get("itemId") or "").strip() for p in products]
    if len(ids) != 20 or len(set(ids)) != 20 or any(not iid for iid in ids):
        raise RuntimeError("itemIds inválidos ou duplicados.")
    for product in products:
        require_product_allowed(product)
        if not affiliate_url(product).startswith("https://"):
            raise RuntimeError(f"Link afiliado inválido: {product.get('itemId')}")
        if not str(product.get("imageUrl") or "").startswith("https://"):
            raise RuntimeError(f"Imagem inválida: {product.get('itemId')}")
        keyword = str(product.get("sourceKeyword") or "")
        if not final_keyword_gate(product, keyword):
            raise RuntimeError(f"Gate final reprovou item {product.get('itemId')} / {keyword}")
    return products


def get_service_post():
    env_blog = os.getenv("BLOGGER_BLOG_ID", BLOG_ID).strip()
    env_post = os.getenv("BLOGGER_STORE_POST_ID", POST_ID).strip()
    if env_blog != BLOG_ID or env_post != POST_ID:
        raise RuntimeError(f"Alvo Blogger incorreto: blog={env_blog} post={env_post}")
    service = criar_servico_blogger()
    post = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    return service, post


def render_store(data: dict) -> str:
    css = """<style id="conecta-achados-store-auto-css">
.bls-store-status{margin:0 0 16px;padding:12px 16px;border-left:4px solid #e65c20;background:#fff5ef;color:#667085;font-size:12px;line-height:1.5}.bls-store-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.bls-panel{min-width:0;border:1px solid #e3e6ea;border-radius:22px;background:#fff;padding:22px;box-shadow:0 9px 28px rgba(17,24,39,.06)}.bls-panel:last-child{grid-column:1/-1}.bls-panel-head{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:18px;padding-bottom:13px;border-bottom:1px solid #eef0f2}.bls-panel-head span{font-size:10px;font-weight:900;letter-spacing:.11em;text-transform:uppercase;color:#e65c20}.bls-panel-head h3{margin:0;font-size:26px;line-height:1;font-weight:900;color:#17212b;text-align:right}.bls-products{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 14px}.bls-panel:last-child .bls-products{grid-template-columns:repeat(4,minmax(0,1fr))}.bls-product{display:block;min-width:0;text-decoration:none;color:#17212b;position:relative;z-index:2;pointer-events:auto!important;cursor:pointer!important}.bls-product>*{pointer-events:none!important}.bls-product-cta{display:flex;align-items:center;justify-content:center;margin-top:9px;padding:9px 10px;border-radius:8px;background:#ee4d2d;color:#fff;font-size:11px;font-weight:900;line-height:1.15;text-align:center}.bls-product-img{display:block;width:100%;aspect-ratio:1/1;border-radius:16px;overflow:hidden;background:#f7f7f5;border:1px solid #e9ecef}.bls-product-img img{display:block;width:100%;height:100%;object-fit:contain;transition:transform .25s ease}.bls-product:hover .bls-product-img img{transform:scale(1.025)}.bls-product-name{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.7em;margin-top:10px;font-size:13px;line-height:1.35}.bls-product strong{display:block;margin-top:6px;color:#17212b;font-size:16px}.bls-product small{display:block;margin-top:3px;color:#747d82;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.bls-panel-foot{margin-top:17px;padding-top:12px;border-top:1px solid #eef0f2;color:#81898e;font-size:10px;line-height:1.45}@media(max-width:900px){.bls-store-grid{grid-template-columns:1fr}.bls-panel:last-child{grid-column:auto}.bls-panel:last-child .bls-products{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){.bls-panel{padding:17px;border-radius:17px}.bls-panel-head{display:block}.bls-panel-head h3{margin-top:5px;text-align:left;font-size:24px}.bls-products,.bls-panel:last-child .bls-products{grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 10px}.bls-product-name{font-size:12px}.bls-product strong{font-size:14px}}
</style>"""
    try:
        stamp = datetime.fromisoformat(str(data.get("timestamp") or "")).strftime("%d/%m/%Y às %H:%M")
    except Exception:
        stamp = "agora"
    out = [css, f'<p class="bls-store-status">Vitrine selecionada em {esc(stamp)} · preços e disponibilidade podem mudar na Shopee.</p>', '<div class="bls-store-grid">']
    categories = data.get("categories") or {}
    for key, (label, panel_id, _) in CATEGORY_META.items():
        out.append(f'<article class="bls-panel" id="{esc(panel_id)}"><div class="bls-panel-head"><span>Seleção da categoria</span><h3>{esc(label)}</h3></div><div class="bls-products">')
        for product in categories.get(key) or []:
            iid = str(product.get("itemId") or "").strip()
            name = str(product.get("productName") or "").strip()
            shop = str(product.get("shopName") or "").strip()
            image = str(product.get("imageUrl") or "").strip()
            url = affiliate_url(product)
            out.append(f'<a class="bls-product" data-item-id="{esc(iid)}" href="{esc(url)}" target="_blank" rel="nofollow sponsored noopener"><span class="bls-product-img"><img src="{esc(image)}" alt="{esc(name)}" loading="lazy" decoding="async"></span><span class="bls-product-name">{esc(name)}</span><strong>{esc(price_text(product))}</strong><small>{esc(shop)}</small><span class="bls-product-cta">Ver oferta na Shopee</span></a>')
        out.append('</div><div class="bls-panel-foot">Atualização automática · confirme preço e disponibilidade na Shopee</div></article>')
    out.append('</div>')
    return ''.join(out)


def replace_region(raw: str, start: str, end: str, content: str) -> str:
    if raw.count(start) != 1 or raw.count(end) != 1:
        raise RuntimeError(f"Marcadores ausentes/duplicados: {start}")
    a, b = raw.find(start), raw.find(end)
    if b <= a:
        raise RuntimeError(f"Ordem inválida dos marcadores: {start}")
    return raw[:a + len(start)] + "\n" + content + "\n" + raw[b:]


def verify_store_html(raw: str, data: dict) -> None:
    products = [p for key in CATEGORY_META for p in ((data.get("categories") or {}).get(key) or [])]
    ids = [str(p.get("itemId") or "") for p in products]
    if raw.count("data-item-id=") != 20 or len(set(ids)) != 20:
        raise RuntimeError("Store inválida: esperado 20 cards únicos.")
    if any(f'data-item-id="{iid}"' not in raw for iid in ids):
        raise RuntimeError("Store inválida: item selecionado ausente.")
    if raw.count('rel="nofollow sponsored noopener"') < 20:
        raise RuntimeError("Store inválida: rel afiliado incompleto.")
    for _, panel_id, _ in CATEGORY_META.values():
        if f'id="{panel_id}"' not in raw:
            raise RuntimeError(f"Painel ausente: {panel_id}")


def write_store(dry_run: bool) -> int:
    data = load_json(SELECTION_PATH, {})
    validate_selection(data)
    service, post = get_service_post()
    raw = str(post.get("content") or "")
    new_raw = replace_region(raw, STORE_START, STORE_END, render_store(data))
    verify_store_html(new_raw, data)
    if dry_run:
        print("CONECTA_STORE_DRY_RUN_PASS: 20 produtos validados em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_store_html(str(verify.get("content") or ""), data)
    print(f"CONECTA_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return 0


def hero_css() -> str:
    return """<style id="conecta-achados-hero-auto-css">
.blh-card{width:min(520px,96%);background:#fff;border:1px solid rgba(17,24,39,.12);border-radius:22px;padding:24px;box-shadow:0 22px 48px rgba(17,24,39,.15)}.blh-card>strong{display:block;margin-bottom:13px;font-size:27px;line-height:1.06;color:#17212b;font-weight:900}.blh-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px}.blh-product{display:block;min-width:0;overflow:hidden;border:1px solid #e2e6ea;border-radius:14px;background:#fff;text-decoration:none;color:#17212b;box-shadow:0 6px 15px rgba(17,24,39,.07);transition:transform .2s ease,box-shadow .2s ease}.blh-product:hover{transform:translateY(-2px);box-shadow:0 10px 22px rgba(17,24,39,.13)}.blh-product-img{display:block;width:100%;height:112px;background:#f7f7f5;overflow:hidden}.blh-product-img img{display:block;width:100%;height:100%;object-fit:contain}.blh-product-meta{display:flex;align-items:center;justify-content:space-between;gap:6px;padding:8px 9px;min-height:35px}.blh-product-meta b{min-width:0;font:900 10px/1.15 Arial,sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.blh-product-meta small{flex:none;font:800 9px/1.1 Arial,sans-serif;color:#e65c20;white-space:nowrap}@media(max-width:620px){.blh-card{padding:16px}.blh-card>strong{font-size:23px}.blh-product-img{height:96px}.blh-product-meta{display:block}.blh-product-meta small{display:block;margin-top:3px}}
</style>"""


def hero_card(product: dict, category: str) -> str:
    require_product_allowed(product)
    _, _, label = CATEGORY_META[category]
    iid = str(product.get("itemId") or "")
    name = str(product.get("productName") or "")
    return f'<a class="blh-product" data-hero-item-id="{esc(iid)}" href="{esc(affiliate_url(product))}" target="_blank" rel="nofollow sponsored noopener" title="{esc(name)}"><span class="blh-product-img"><img src="{esc(product.get("imageUrl"))}" alt="{esc(name)}" loading="lazy" decoding="async"></span><span class="blh-product-meta"><b>{esc(label)}</b><small>{esc(price_text(product))}</small></span></a>'


def build_hero(data: dict) -> list[str]:
    c = data.get("categories") or {}
    casa, coz = c["Casa & Organizacao"], c["Cozinha & Utilidades"]
    tech, beleza, dia = c["Tecnologia & Acessorios"], c["Beleza & Cuidados"], c["Dia a Dia & Praticidade"]
    groups = [
        ("Casa e cozinha em destaque", [(casa[0], "Casa & Organizacao"), (casa[1], "Casa & Organizacao"), (coz[0], "Cozinha & Utilidades"), (coz[1], "Cozinha & Utilidades")]),
        ("Tecnologia e cuidados para a rotina", [(tech[0], "Tecnologia & Acessorios"), (tech[1], "Tecnologia & Acessorios"), (beleza[0], "Beleza & Cuidados"), (beleza[1], "Beleza & Cuidados")]),
        ("Praticidade para o dia a dia", [(dia[0], "Dia a Dia & Praticidade"), (dia[1], "Dia a Dia & Praticidade"), (dia[2], "Dia a Dia & Praticidade"), (dia[3], "Dia a Dia & Praticidade")]),
    ]
    slides = []
    for idx, (title, items) in enumerate(groups):
        prefix = hero_css() if idx == 0 else ""
        cards = ''.join(hero_card(product, category) for product, category in items)
        slides.append(prefix + f'<div class="blh-card"><strong>{esc(title)}</strong><div class="blh-grid">{cards}</div></div>')
    return slides


def verify_hero(raw: str, slides: list[str]) -> None:
    if raw.count("data-hero-item-id=") != 12:
        raise RuntimeError("Hero inválido: esperado 12 mini-cards.")
    ids = re.findall(r'data-hero-item-id="([^"]+)"', ''.join(slides))
    if len(ids) != 12 or len(set(ids)) != 12 or any(f'data-hero-item-id="{iid}"' not in raw for iid in ids):
        raise RuntimeError("Hero inválido: IDs ausentes ou duplicados.")
    if raw.count('rel="nofollow sponsored noopener"') < 32:
        raise RuntimeError("Hero inválido: rel afiliado incompleto.")


def write_hero(dry_run: bool) -> int:
    data = load_json(SELECTION_PATH, {})
    validate_selection(data)
    slides = build_hero(data)
    service, post = get_service_post()
    raw = str(post.get("content") or "")
    new_raw = raw
    for (start, end), slide in zip(HERO_MARKERS, slides):
        new_raw = replace_region(new_raw, start, end, slide)
    verify_hero(new_raw, slides)
    if dry_run:
        print("CONECTA_HERO_DRY_RUN_PASS: 12 mini-cards validados em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_hero(str(verify.get("content") or ""), slides)
    print("CONECTA_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return 0


def identity_guard() -> int:
    _, post = get_service_post()
    raw = str(post.get("content") or "")
    required = [
        STORE_PAGE,
        "Achados práticos para casa, tecnologia, beleza e dia a dia",
        "Casa &amp; Organização",
        "Cozinha &amp; Utilidades",
        "Tecnologia &amp; Acessórios",
        "Beleza &amp; Cuidados",
        "Dia a Dia &amp; Praticidade",
        '#bls-casa-organizacao',
        '#bls-cozinha-utilidades',
        '#bls-tecnologia',
        '#bls-beleza',
        '#bls-dia-a-dia',
        "blogger-liq-layout-wide-css",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Conecta incompleta: {missing}")
    forbidden = [
        "https://achadosparacasa2026.blogspot.com/p/loja.html",
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        "https://liquidificadores-em-foco.blogspot.com/p/loja.html",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência de outro blog detectada: {bad}")
    print("CONECTA_IDENTITY_PASS: domínio, Page Loja, layout e 5 categorias corretos.")
    return 0


def persist_rotation() -> int:
    selection = load_json(SELECTION_PATH, {})
    validate_selection(selection)
    items = [
        {"category": category, "itemId": str(product.get("itemId") or "")}
        for category, products in (selection.get("categories") or {}).items()
        for product in products
    ]
    if len(items) != 20 or len(set(x["itemId"] for x in items)) != 20:
        raise RuntimeError("Persistência bloqueada: seleção não possui 20 IDs únicos.")
    history = load_json(HISTORY_PATH, {"version": 1, "blogId": BLOG_ID, "runs": []})
    if str(history.get("blogId") or BLOG_ID) != BLOG_ID:
        raise RuntimeError("Persistência bloqueada: histórico pertence a outro blog.")
    runs = list(history.get("runs") or [])
    signature = tuple(sorted(x["itemId"] for x in items))
    if runs:
        last_sig = tuple(sorted(str(x.get("itemId") or "") for x in (runs[-1].get("items") or [])))
        if str(runs[-1].get("source") or "") == "blogger_published" and last_sig == signature:
            print("CONECTA_ROTATION_NOOP: seleção já registrada.")
            return 0
    runs.append({
        "timestamp": now_local().isoformat(),
        "source": "blogger_published",
        "selectionSchemaVersion": int(selection.get("schemaVersion") or 0),
        "items": items,
    })
    history["version"] = 1
    history["blogId"] = BLOG_ID
    history["runs"] = runs[-120:]
    save_atomic(HISTORY_PATH, history)
    print("CONECTA_ROTATION_PERSIST_PASS: 20 produtos registrados após validação pública.")
    return 0


def validate_only() -> int:
    data = load_json(SELECTION_PATH, {})
    products = validate_selection(data)
    print(f"CONECTA_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["safe", "validate", "store-dry-run", "store-live", "hero-dry-run", "hero-live", "identity", "persist"])
    args = parser.parse_args()
    return {
        "safe": safe_scan,
        "validate": validate_only,
        "store-dry-run": lambda: write_store(True),
        "store-live": lambda: write_store(False),
        "hero-dry-run": lambda: write_hero(True),
        "hero-live": lambda: write_hero(False),
        "identity": identity_guard,
        "persist": persist_rotation,
    }[args.command]()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"CONECTA_STORE_FAILED: {exc}", file=sys.stderr)
        raise
