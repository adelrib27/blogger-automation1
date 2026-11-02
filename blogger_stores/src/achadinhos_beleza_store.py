#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "blogger_stores" / "data"
SCAN_DIR = DATA_DIR / "achadinhos_beleza_scan"
HISTORY_PATH = DATA_DIR / "achadinhos_beleza_rotation.json"
SELECTION_PATH = DATA_DIR / "achadinhos_beleza_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_achadinhos_beleza.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_achadinhos_beleza_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "2562496977098748229"
POST_ID = "7650631557624373238"
STORE_PAGE = "https://canal-attitude.blogspot.com/p/loja.html"
STORE_POST_URL = "https://canal-attitude.blogspot.com/2026/10/loja.html"
RECENT_DAYS = max(1, min(int(os.getenv("ACHADINHOS_BELEZA_STORE_RECENT_DAYS", "14")), 90))
SYSTEM_ERROR_RETRIES = max(2, min(int(os.getenv("ACHADINHOS_BELEZA_SHOPEE_SYSTEM_RETRIES", "4")), 6))

CATEGORY_META = {
    "Cabelos": ("Cabelos", "bls-cabelos", "Cabelos"),
    "Skincare": ("Skincare", "bls-skincare", "Skincare"),
    "Maquiagem": ("Maquiagem", "bls-maquiagem", "Maquiagem"),
    "Unhas": ("Unhas", "bls-unhas", "Unhas"),
    "Cuidados Pessoais": ("Cuidados Pessoais", "bls-cuidados-pessoais", "Cuidados"),
}

os.environ["SHOPEE_OPPORTUNITIES_CONFIG"] = str(CONFIG_PATH)
os.environ["SHOPEE_INTENT_RULES"] = str(INTENT_RULES_PATH)
os.environ["SHOPEE_OUTPUT_DIR"] = str(SCAN_DIR)
os.environ["SHOPEE_CATEGORY"] = "all"
os.environ.setdefault("SHOPEE_TOP_N", "180")

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "radar_tech_br" / "src"))
sys.path.insert(0, str(ROOT / "blogger_stores" / "src"))

import shopee_oportunidades_v23 as shopee_v23  # noqa: E402
import conecta_achados_store as base  # noqa: E402

base.SCAN_DIR = SCAN_DIR
base.HISTORY_PATH = HISTORY_PATH
base.SELECTION_PATH = SELECTION_PATH
base.CONFIG_PATH = CONFIG_PATH
base.INTENT_RULES_PATH = INTENT_RULES_PATH
base.EXPECTED_APP_ID = EXPECTED_APP_ID
base.BLOG_ID = BLOG_ID
base.POST_ID = POST_ID
base.STORE_PAGE = STORE_PAGE
base.STORE_POST_URL = STORE_POST_URL
base.RECENT_DAYS = RECENT_DAYS
base.CATEGORY_META = CATEGORY_META
base.shopee_v23 = shopee_v23

_orig_post_graphql = shopee_v23.base.post_graphql


def resilient_post_graphql(app_id: str, secret: str, query: str, retries: int = 3) -> dict:
    last_response: dict = {}
    for attempt in range(1, SYSTEM_ERROR_RETRIES + 1):
        response = _orig_post_graphql(app_id, secret, query, retries=retries)
        last_response = response
        errors = response.get("errors") or []
        codes = {str((error.get("extensions") or {}).get("code")) for error in errors}
        if "10000" not in codes:
            return response
        if attempt < SYSTEM_ERROR_RETRIES:
            delay = min(3 * attempt, 9)
            print(f"  retry Shopee System Error 10000: tentativa {attempt + 1}/{SYSTEM_ERROR_RETRIES} em {delay}s")
            time.sleep(delay)
    return last_response


shopee_v23.base.post_graphql = resilient_post_graphql


def final_keyword_gate(product: dict, keyword: str) -> bool:
    title = base.norm(product.get("productName") or "")
    key = base.norm(keyword)
    blocks = {
        "escova secadora": ["refil", "capa para escova", "suporte para escova", "peca para escova"],
        "secador de cabelo": ["difusor", "bico para secador", "suporte", "resistencia", "cabo para secador", "peca", "adaptador", "acessorio"],
        "chapinha cabelo": ["capa para chapinha", "suporte para chapinha", "bolsa para chapinha", "peca"],
        "modelador de cachos": ["suporte", "capa", "bolsa", "peca"],
        "protetor solar facial": ["corporal", "infantil", "kids", "labial", "capilar", "pet"],
        "hidratante facial": ["corporal", "mao", "pes", "capilar", "pet"],
        "sabonete facial": ["corporal", "intimo", "roupa", "pet"],
        "serum facial": ["capilar", "cabelo", "unhas", "pet"],
        "base maquiagem": ["base para unha", "base de unha", "esmalte", "gel uv", "organizador", "suporte"],
        "mascara de cilios": ["aplicador", "escova avulsa", "curvex", "cola", "cilios posticos"],
        "batom": ["porta batom", "organizador", "adesivo", "chaveiro", "miniatura"],
        "paleta de sombras": ["paleta de pintura", "aquarela", "artesanal", "infantil", "brinquedo"],
        "esmalte gel": ["removedor", "acetona", "porta esmalte", "organizador", "adesivo"],
        "kit manicure": ["adesivo", "decoracao", "brinquedo", "infantil"],
        "cabine uv unhas": ["miniatura", "suporte", "peca", "lampada avulsa"],
        "lixa eletrica unhas": ["refil", "broca avulsa", "lixa avulsa", "pedicure manual"],
        "barbeador eletrico": ["lamina de reposicao", "cabeca de reposicao", "capa", "suporte", "pet"],
        "depilador eletrico": ["cera", "linha depilatoria", "pinca", "creme depilatorio", "refil", "lamina de reposicao"],
        "escova limpeza facial": ["cabelo", "capilar", "dental", "dente", "roupa", "pet"],
        "massageador facial": ["corporal", "pes", "costas", "pescoco", "pet"],
    }
    if any(term in title for term in blocks.get(key, [])):
        return False
    positive = {
        "escova secadora": lambda: "escova" in title and any(x in title for x in ["secadora", "secador", "ar quente"]),
        "secador de cabelo": lambda: "secador" in title and any(x in title for x in ["cabelo", "cabelos"]),
        "chapinha cabelo": lambda: any(x in title for x in ["chapinha", "prancha"]) and any(x in title for x in ["cabelo", "cabelos", "alisadora", "alisador"]),
        "modelador de cachos": lambda: any(x in title for x in ["modelador", "babyliss", "ondulador"]) and any(x in title for x in ["cacho", "cachos", "cabelo", "cabelos"]),
        "protetor solar facial": lambda: any(x in title for x in ["protetor solar", "filtro solar"]) and any(x in title for x in ["facial", "rosto", "face"]),
        "hidratante facial": lambda: "hidratante" in title and any(x in title for x in ["facial", "rosto", "face"]),
        "sabonete facial": lambda: any(x in title for x in ["sabonete", "gel de limpeza"]) and any(x in title for x in ["facial", "rosto", "face"]),
        "serum facial": lambda: "serum" in title and any(x in title for x in ["facial", "rosto", "face"]),
        "base maquiagem": lambda: "base" in title and any(x in title for x in ["maquiagem", "liquida", "facial", "rosto"]),
        "mascara de cilios": lambda: any(x in title for x in ["mascara de cilios", "rimel"]),
        "batom": lambda: any(x in title for x in ["batom", "lip tint", "lipstick"]),
        "paleta de sombras": lambda: "paleta" in title and any(x in title for x in ["sombra", "sombras"]),
        "esmalte gel": lambda: "esmalte" in title and any(x in title for x in ["gel", "unha", "unhas"]),
        "kit manicure": lambda: "kit" in title and any(x in title for x in ["manicure", "unha", "unhas"]),
        "cabine uv unhas": lambda: any(x in title for x in ["cabine", "secador"]) and any(x in title for x in ["uv", "led"]) and any(x in title for x in ["unha", "unhas"]),
        "lixa eletrica unhas": lambda: "lixa" in title and any(x in title for x in ["eletrica", "motor", "broca"]) and any(x in title for x in ["unha", "unhas", "manicure"]),
        "barbeador eletrico": lambda: any(x in title for x in ["barbeador", "maquina de barbear"]) and any(x in title for x in ["eletrico", "recarregavel", "usb"]),
        "depilador eletrico": lambda: "depilador" in title and any(x in title for x in ["eletrico", "recarregavel", "usb"]),
        "escova limpeza facial": lambda: "escova" in title and any(x in title for x in ["facial", "rosto", "face", "limpeza"]),
        "massageador facial": lambda: "massageador" in title and any(x in title for x in ["facial", "rosto", "face"]),
    }
    return positive[key]() if key in positive else False


def run_beauty_regression_checks(rules_doc: dict) -> None:
    cases = [
        ("Refil para Escova Secadora", "escova secadora", False), ("Escova Secadora de Cabelo 1200W", "escova secadora", True),
        ("Difusor Universal para Secador de Cabelo", "secador de cabelo", False), ("Secador de Cabelo Profissional 2000W", "secador de cabelo", True),
        ("Capa Térmica para Chapinha Cabelo", "chapinha cabelo", False), ("Chapinha Prancha de Cabelo Alisadora Bivolt", "chapinha cabelo", True),
        ("Suporte para Babyliss Modelador de Cachos", "modelador de cachos", False), ("Modelador de Cachos Babyliss 25mm", "modelador de cachos", True),
        ("Protetor Solar Corporal FPS 50", "protetor solar facial", False), ("Protetor Solar Facial FPS 60", "protetor solar facial", True),
        ("Hidratante Corporal 400ml", "hidratante facial", False), ("Hidratante Facial Ácido Hialurônico", "hidratante facial", True),
        ("Sabonete Corporal Líquido", "sabonete facial", False), ("Sabonete Facial Gel de Limpeza para o Rosto", "sabonete facial", True),
        ("Sérum Capilar Reparador", "serum facial", False), ("Sérum Facial Vitamina C para o Rosto", "serum facial", True),
        ("Base de Unha Fortalecedora", "base maquiagem", False), ("Base Líquida Maquiagem Facial Alta Cobertura", "base maquiagem", True),
        ("Aplicador para Máscara de Cílios", "mascara de cilios", False), ("Máscara de Cílios Rímel Volume", "mascara de cilios", True),
        ("Porta Batom Organizador", "batom", False), ("Batom Matte Longa Duração", "batom", True),
        ("Paleta de Pintura Aquarela", "paleta de sombras", False), ("Paleta de Sombras Maquiagem 18 Cores", "paleta de sombras", True),
        ("Removedor de Esmalte Gel", "esmalte gel", False), ("Esmalte Gel UV para Unhas", "esmalte gel", True),
        ("Adesivo de Unhas Kit Manicure", "kit manicure", False), ("Kit Manicure Profissional para Unhas", "kit manicure", True),
        ("Lâmpada Avulsa para Cabine UV Unhas", "cabine uv unhas", False), ("Cabine UV LED Secador para Unhas", "cabine uv unhas", True),
        ("Broca Avulsa para Lixa Elétrica Unhas", "lixa eletrica unhas", False), ("Lixa Elétrica para Unhas Manicure Motor Profissional", "lixa eletrica unhas", True),
        ("Lâmina de Reposição para Barbeador Elétrico", "barbeador eletrico", False), ("Barbeador Elétrico Recarregável USB", "barbeador eletrico", True),
        ("Creme Depilatório Corporal", "depilador eletrico", False), ("Depilador Elétrico Recarregável USB", "depilador eletrico", True),
        ("Escova Dental Elétrica Limpeza", "escova limpeza facial", False), ("Escova Limpeza Facial para o Rosto", "escova limpeza facial", True),
        ("Massageador Corporal para Costas", "massageador facial", False), ("Massageador Facial para Rosto", "massageador facial", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        accepted = bool(shopee_v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        actual = accepted and final_keyword_gate({"productName": title}, keyword)
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha na regressão semântica Achadinhos de Beleza: " + json.dumps(failures, ensure_ascii=False))
    print(f"ACHADINHOS_BELEZA_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


base.final_keyword_gate = final_keyword_gate
base.run_conecta_regression_checks = run_beauty_regression_checks

_orig_render_store = base.render_store
_orig_hero_css = base.hero_css


def render_store(data: dict) -> str:
    return _orig_render_store(data).replace("conecta-achados-store-auto-css", "achadinhos-beleza-store-auto-css")


def hero_css() -> str:
    return _orig_hero_css().replace("conecta-achados-hero-auto-css", "achadinhos-beleza-hero-auto-css")


def build_hero(data: dict) -> list[str]:
    c = data.get("categories") or {}
    cabelos, skincare, maquiagem, unhas, cuidados = c["Cabelos"], c["Skincare"], c["Maquiagem"], c["Unhas"], c["Cuidados Pessoais"]
    groups = [
        ("Cabelos e skincare em destaque", [(cabelos[0], "Cabelos"), (cabelos[1], "Cabelos"), (skincare[0], "Skincare"), (skincare[1], "Skincare")]),
        ("Maquiagem e unhas para completar a rotina", [(maquiagem[0], "Maquiagem"), (maquiagem[1], "Maquiagem"), (unhas[0], "Unhas"), (unhas[2], "Unhas")]),
        ("Cuidados pessoais selecionados", [(cuidados[0], "Cuidados Pessoais"), (cuidados[1], "Cuidados Pessoais"), (cuidados[2], "Cuidados Pessoais"), (cuidados[3], "Cuidados Pessoais")]),
    ]
    slides = []
    for idx, (title, items) in enumerate(groups):
        prefix = hero_css() if idx == 0 else ""
        cards = "".join(base.hero_card(product, category) for product, category in items)
        slides.append(prefix + f'<div class="blh-card"><strong>{base.esc(title)}</strong><div class="blh-grid">{cards}</div></div>')
    return slides


base.render_store = render_store
base.hero_css = hero_css
base.build_hero = build_hero

IDENTITY_REPLACEMENTS = [
    ("Achados práticos para casa, tecnologia, beleza e dia a dia", "Beleza, autocuidado e achadinhos para sua rotina"),
    ("Descubra produtos úteis para facilitar a rotina", "Descubra achados de beleza para cuidar de você todos os dias"),
    ("Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.", "Uma vitrine afiliada com cabelos, skincare, maquiagem, unhas e cuidados pessoais selecionados automaticamente na Shopee."),
    ("Cozinha e tecnologia", "Skincare e maquiagem"),
    ("Soluções práticas para cozinhar, conectar e organizar melhor", "Cuidados para pele e maquiagem em uma seleção mais focada"),
    ("A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.", "A seleção prioriza produtos de beleza coerentes com cada intenção, bloqueando peças, refis, acessórios e falsos positivos."),
    ("Ver cozinha", "Ver skincare"), ("Ver tecnologia", "Ver maquiagem"),
    ("Beleza e praticidade", "Cabelos e cuidados"),
    ("Achados reais para cuidados pessoais e rotina", "Ferramentas e cuidados para cabelo, unhas e autocuidado"),
    ("Ver beleza", "Ver cabelos"), ("Ver dia a dia", "Ver cuidados pessoais"),
    ('href="#bls-casa-organizacao"', 'href="#bls-cabelos"'), ('href="#bls-cozinha-utilidades"', 'href="#bls-skincare"'),
    ('href="#bls-tecnologia"', 'href="#bls-maquiagem"'), ('href="#bls-beleza"', 'href="#bls-unhas"'), ('href="#bls-dia-a-dia"', 'href="#bls-cuidados-pessoais"'),
    ("Casa &amp; Organização", "Cabelos"), ("organização e soluções para o lar", "secadores, escovas, chapinhas e modeladores"),
    ("Cozinha &amp; Utilidades", "Skincare"), ("itens úteis para a cozinha", "proteção solar, hidratação, limpeza e séruns"),
    ("Tecnologia &amp; Acessórios", "Maquiagem"), ("conectividade e eletrônicos úteis", "bases, máscaras, batons e sombras"),
    ('<a class="bls-cat" href="#bls-unhas"><b>Beleza &amp; Cuidados</b><small>cuidados pessoais e beleza</small></a>', '<a class="bls-cat" href="#bls-unhas"><b>Unhas</b><small>esmaltes, manicure, cabine UV e lixas elétricas</small></a>'),
    ("Dia a Dia &amp; Praticidade", "Cuidados Pessoais"), ("produtos úteis para a rotina", "barbear, depilação e cuidados faciais"),
    ("Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia", "Vitrine de beleza, autocuidado e achadinhos para o dia a dia"),
]


def transform_identity(raw: str) -> str:
    out = raw
    for old, new in IDENTITY_REPLACEMENTS:
        out = out.replace(old, new)
    out = out.replace('<a class="bls-btn bls-btn-main" href="#bls-unhas">Ver cabelos</a>', '<a class="bls-btn bls-btn-main" href="#bls-cabelos">Ver cabelos</a>')
    return out


def verify_identity(raw: str) -> None:
    required = [STORE_PAGE, "Beleza, autocuidado e achadinhos para sua rotina", "Descubra achados de beleza para cuidar de você todos os dias", "Cabelos", "Skincare", "Maquiagem", "Unhas", "Cuidados Pessoais", "#bls-cabelos", "#bls-skincare", "#bls-maquiagem", "#bls-unhas", "#bls-cuidados-pessoais", "blogger-liq-layout-wide-css", '<h3>Cuidados Pessoais</h3>', 'href="#bls-skincare">Ver skincare</a>', 'href="#bls-maquiagem">Ver maquiagem</a>', 'href="#bls-cabelos">Ver cabelos</a>', 'href="#bls-cuidados-pessoais">Ver cuidados pessoais</a>']
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Achadinhos de Beleza incompleta: {missing}")
    forbidden = ["https://conectaachados.blogspot.com/p/loja.html", "https://achadosparacasa2026.blogspot.com/p/loja.html", "https://vitrine-pratica.blogspot.com/p/loja.html", "https://moda-ofertas.blogspot.com/p/loja.html"]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência de outro blog detectada no Achadinhos de Beleza: {bad}")


def write_identity(dry_run: bool) -> int:
    service, post = base.get_service_post()
    raw = str(post.get("content") or "")
    new_raw = transform_identity(raw)
    verify_identity(new_raw)
    if dry_run:
        print("ACHADINHOS_BELEZA_IDENTITY_DRY_RUN_PASS: identidade validada em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_identity(str(verify.get("content") or ""))
    print("ACHADINHOS_BELEZA_IDENTITY_PASS: domínio, Page Loja, layout e nicho beleza corretos.")
    return 0


def identity_check() -> int:
    _, post = base.get_service_post()
    verify_identity(str(post.get("content") or ""))
    print("ACHADINHOS_BELEZA_IDENTITY_PASS: domínio, Page Loja, layout e nicho beleza corretos.")
    return 0


def safe_scan() -> int:
    rc = base.safe_scan()
    data = base.load_json(SELECTION_PATH, {})
    semantic = dict(data.get("semanticValidation") or {})
    semantic["rulesFile"] = "config/shopee_achadinhos_beleza_intent_rules.json"
    semantic["profileVersion"] = 1
    semantic["profileName"] = "Achadinhos de Beleza"
    semantic["shopeeSystemErrorRetries"] = SYSTEM_ERROR_RETRIES
    data["semanticValidation"] = semantic
    base.save_atomic(SELECTION_PATH, data)
    base.validate_selection(data)
    print("ACHADINHOS_BELEZA_SAFE_READY: 20 produtos; 20 intenções; histórico e seleção exclusivos; Blogger não alterado.")
    return rc


def validate_only() -> int:
    products = base.validate_selection(base.load_json(SELECTION_PATH, {}))
    print(f"ACHADINHOS_BELEZA_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def store_write(dry_run: bool) -> int:
    rc = base.write_store(dry_run)
    print("ACHADINHOS_BELEZA_STORE_DRY_RUN_PASS" if dry_run else f"ACHADINHOS_BELEZA_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return rc


def hero_write(dry_run: bool) -> int:
    rc = base.write_hero(dry_run)
    print("ACHADINHOS_BELEZA_HERO_DRY_RUN_PASS" if dry_run else "ACHADINHOS_BELEZA_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return rc


def persist() -> int:
    rc = base.persist_rotation()
    print("ACHADINHOS_BELEZA_ROTATION_PERSIST_PASS: seleção validada registrada após PASS público.")
    return rc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["safe", "validate", "identity-dry-run", "identity-live", "identity", "store-dry-run", "store-live", "hero-dry-run", "hero-live", "persist"])
    args = parser.parse_args()
    return {"safe": safe_scan, "validate": validate_only, "identity-dry-run": lambda: write_identity(True), "identity-live": lambda: write_identity(False), "identity": identity_check, "store-dry-run": lambda: store_write(True), "store-live": lambda: store_write(False), "hero-dry-run": lambda: hero_write(True), "hero-live": lambda: hero_write(False), "persist": persist}[args.command]()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ACHADINHOS_BELEZA_STORE_FAILED: {exc}", file=sys.stderr)
        raise
