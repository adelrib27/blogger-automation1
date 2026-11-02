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
SCAN_DIR = DATA_DIR / "cozinha_sem_complicacao_scan"
HISTORY_PATH = DATA_DIR / "cozinha_sem_complicacao_rotation.json"
SELECTION_PATH = DATA_DIR / "cozinha_sem_complicacao_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_cozinha_sem_complicacao.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_cozinha_sem_complicacao_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "3552757910439359679"
POST_ID = "7888042807715084117"
STORE_PAGE = "https://cozinha-sem-complicacao.blogspot.com/p/loja.html"
STORE_POST_URL = "https://cozinha-sem-complicacao.blogspot.com/2026/10/loja.html"
RECENT_DAYS = max(1, min(int(os.getenv("COZINHA_SEM_COMPLICACAO_STORE_RECENT_DAYS", "14")), 90))
SYSTEM_ERROR_RETRIES = max(2, min(int(os.getenv("COZINHA_SEM_COMPLICACAO_SHOPEE_SYSTEM_RETRIES", "4")), 6))

CATEGORY_META = {
    "Eletroportateis": ("Eletroportáteis", "bls-eletroportateis", "Eletro"),
    "Panelas & Coccao": ("Panelas & Cocção", "bls-panelas", "Panelas"),
    "Organizacao & Pia": ("Organização & Pia", "bls-organizacao-cozinha", "Organização"),
    "Cafe & Bebidas": ("Café & Bebidas", "bls-cafe-bebidas", "Café"),
    "Utensilios & Preparo": ("Utensílios & Preparo", "bls-utensilios", "Utensílios"),
}

os.environ["SHOPEE_OPPORTUNITIES_CONFIG"] = str(CONFIG_PATH)
os.environ["SHOPEE_INTENT_RULES"] = str(INTENT_RULES_PATH)
os.environ["SHOPEE_OUTPUT_DIR"] = str(SCAN_DIR)
os.environ["SHOPEE_CATEGORY"] = "all"
os.environ.setdefault("SHOPEE_TOP_N", "500")

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
            print(f"retry Shopee System Error 10000: tentativa {attempt + 1}/{SYSTEM_ERROR_RETRIES} em {delay}s")
            time.sleep(delay)
    return last_response


shopee_v23.base.post_graphql = resilient_post_graphql

_orig_render_store = base.render_store
_orig_hero_css = base.hero_css


def render_store(data: dict) -> str:
    return _orig_render_store(data).replace("conecta-achados-store-auto-css", "cozinha-sem-complicacao-store-auto-css")


def hero_css() -> str:
    return _orig_hero_css().replace("conecta-achados-hero-auto-css", "cozinha-sem-complicacao-hero-auto-css")


base.render_store = render_store
base.hero_css = hero_css

IDENTITY_REPLACEMENTS = [
    ("Achados práticos para casa, tecnologia, beleza e dia a dia", "Cozinha Sem Complicação — utensílios, eletroportáteis e soluções práticas"),
    ("Portal Radar Tech — tecnologia e achados práticos para a rotina", "Cozinha Sem Complicação — utensílios, eletroportáteis e soluções práticas"),
    ("Descubra produtos úteis para facilitar a rotina", "Achados para cozinhar melhor e simplificar a rotina"),
    ("Tecnologia e produtos úteis selecionados para facilitar o dia a dia", "Achados para cozinhar melhor e simplificar a rotina"),
    ("Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.", "Uma vitrine afiliada do Cozinha Sem Complicação com eletroportáteis, panelas, organização, café e utensílios selecionados automaticamente na Shopee."),
    ("Uma vitrine afiliada do Portal Radar Tech com tecnologia, casa, cozinha, cuidados e praticidade, selecionados automaticamente na Shopee.", "Uma vitrine afiliada do Cozinha Sem Complicação com eletroportáteis, panelas, organização, café e utensílios selecionados automaticamente na Shopee."),
    ("Cozinha e tecnologia", "Eletroportáteis e preparo"),
    ("Soluções práticas para cozinhar, conectar e organizar melhor", "Equipamentos e utensílios para cozinhar com mais praticidade"),
    ("A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.", "A seleção prioriza produtos completos para preparo, cocção e organização, bloqueando peças, refis e falsos positivos."),
    ("Beleza e praticidade", "Café, organização e utensílios"),
    ("Achados reais para cuidados pessoais e rotina", "Pequenos itens que fazem diferença na cozinha"),
    ("Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia", "Vitrine Cozinha Sem Complicação: produtos úteis para preparar, organizar e servir"),
    ("Vitrine Portal Radar Tech: tecnologia e produtos práticos para o dia a dia", "Vitrine Cozinha Sem Complicação: produtos úteis para preparar, organizar e servir"),
    ("#bls-casa-organizacao", "#bls-eletroportateis"),
    ("#bls-cozinha-utilidades", "#bls-panelas"),
    ("#bls-tecnologia", "#bls-organizacao-cozinha"),
    ("#bls-beleza", "#bls-cafe-bebidas"),
    ("#bls-dia-a-dia", "#bls-utensilios"),
    ("Casa &amp; Organização", "Eletroportáteis"),
    ("Cozinha &amp; Utilidades", "Panelas &amp; Cocção"),
    ("Tecnologia &amp; Acessórios", "Organização &amp; Pia"),
    ("Beleza &amp; Cuidados", "Café &amp; Bebidas"),
    ("Dia a Dia &amp; Praticidade", "Utensílios &amp; Preparo"),
    ("organização e soluções para o lar", "equipamentos para agilizar o preparo"),
    ("itens úteis para a cozinha", "panelas e soluções para cocção"),
    ("conectividade e eletrônicos úteis", "organização de bancada, pia e mantimentos"),
    ("cuidados pessoais e beleza", "café, bebidas e conservação térmica"),
    ("produtos úteis para a rotina", "utensílios para cortar, medir e preparar"),
    ("Ver cozinha", "Ver panelas"),
    ("Ver tecnologia", "Ver organização"),
    ("Ver beleza", "Ver café"),
    ("Ver dia a dia", "Ver utensílios"),
]


def transform_identity(raw: str) -> str:
    out = raw
    for old, new in IDENTITY_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def verify_identity(raw: str) -> None:
    required = [
        STORE_PAGE,
        "Cozinha Sem Complicação — utensílios, eletroportáteis e soluções práticas",
        "Achados para cozinhar melhor e simplificar a rotina",
        "Eletroportáteis",
        "Panelas &amp; Cocção",
        "Organização &amp; Pia",
        "Café &amp; Bebidas",
        "Utensílios &amp; Preparo",
        "#bls-eletroportateis",
        "#bls-panelas",
        "#bls-organizacao-cozinha",
        "#bls-cafe-bebidas",
        "#bls-utensilios",
        "blogger-liq-layout-wide-css",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Cozinha Sem Complicação incompleta: {missing}")
    forbidden = [
        "Portal Radar Tech — tecnologia e achados práticos para a rotina",
        "Achados práticos para casa, tecnologia, beleza e dia a dia",
        "Casa &amp; Organização",
        "Tecnologia &amp; Acessórios",
        "Beleza &amp; Cuidados",
        "Dia a Dia &amp; Praticidade",
        "https://conectaachados.blogspot.com/p/loja.html",
        "https://portalradartechbr.blogspot.com/p/loja.html",
        "https://achadosparacasa2026.blogspot.com/p/loja.html",
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        "https://canal-attitude.blogspot.com/p/loja.html",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência genérica/antiga ou de outro blog em Cozinha Sem Complicação: {bad}")


def write_identity(dry_run: bool) -> int:
    service, post = base.get_service_post()
    raw = str(post.get("content") or "")
    new_raw = transform_identity(raw)
    verify_identity(new_raw)
    if dry_run:
        print("COZINHA_SEM_COMPLICACAO_IDENTITY_DRY_RUN_PASS: identidade validada em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_identity(str(verify.get("content") or ""))
    print("COZINHA_SEM_COMPLICACAO_IDENTITY_PASS: domínio, Page Loja, layout e identidade confirmados.")
    return 0


def identity_check() -> int:
    _, post = base.get_service_post()
    verify_identity(str(post.get("content") or ""))
    print("COZINHA_SEM_COMPLICACAO_IDENTITY_PASS: domínio, Page Loja, layout e identidade confirmados.")
    return 0


def run_semantic_regression() -> None:
    rules = json.loads(INTENT_RULES_PATH.read_text(encoding="utf-8"))
    cases = [
        ("Forma de Silicone para Air Fryer", "fritadeira eletrica", False),
        ("Fritadeira Elétrica Air Fryer 5L Sem Óleo", "fritadeira eletrica", True),
        ("Copo para Liquidificador 2 Litros", "liquidificador", False),
        ("Liquidificador 1200W 3L 12 Velocidades", "liquidificador", True),
        ("Processador Picador De Alimentos 3L Moedor De Carne Mixer Elétrico", "mixer eletrico", False),
        ("Mixer Elétrico 3 em 1 500W", "mixer eletrico", True),
        ("Lâmina para Processador de Alimentos", "processador alimentos", False),
        ("Processador de Alimentos Elétrico 1000W", "processador alimentos", True),
        ("Borracha para Panela de Pressão", "panela de pressao", False),
        ("Panela de Pressão 4,5L Alumínio", "panela de pressao", True),
        ("Protetor de Panela em Feltro Kit 6", "jogo de panelas", False),
        ("Jogo de Panelas 5 Peças Antiaderente", "jogo de panelas", True),
        ("Tampa para Frigideira 24cm", "frigideira antiaderente", False),
        ("Frigideira Antiaderente 24cm", "frigideira antiaderente", True),
        ("Chapa de Reposição para Grill", "grill eletrico", False),
        ("Grill Elétrico Antiaderente 1000W", "grill eletrico", True),
        ("Tapete Escorredor de Louças", "escorredor de loucas", False),
        ("Escorredor de Louças Aço para 13 Pratos", "escorredor de loucas", True),
        ("Organizador de Vassoura Rodo Mop para Cozinha", "organizador cozinha", False),
        ("Organizador de Cozinha para Temperos e Mantimentos", "organizador cozinha", True),
        ("Tampa avulsa para Pote Hermético", "pote hermetico", False),
        ("Kit Potes Herméticos para Mantimentos", "pote hermetico", True),
        ("Etiqueta para Porta Temperos", "porta temperos", False),
        ("Kit Porta Temperos Organizador de Condimentos", "porta temperos", True),
        ("Jarra para Cafeteira Elétrica", "cafeteira eletrica", False),
        ("Cafeteira Elétrica 30 Cafés", "cafeteira eletrica", True),
        ("Base para Chaleira Elétrica", "chaleira eletrica", False),
        ("Chaleira Elétrica Inox 1,8L", "chaleira eletrica", True),
        ("Haste avulsa para Espumador", "espumador de leite", False),
        ("Espumador de Leite Elétrico para Café", "espumador de leite", True),
        ("Tampa de Reposição para Garrafa Térmica", "garrafa termica", False),
        ("Garrafa Térmica 1 Litro Inox", "garrafa termica", True),
        ("Afiador de Faca Chef", "faca chef", False),
        ("Faca Chef 8 Polegadas para Cozinha", "faca chef", True),
        ("Tábua Decorativa de Parede", "tabua de corte", False),
        ("Tábua de Corte para Cozinha Carne e Legumes", "tabua de corte", True),
        ("Balança Corporal Digital", "balanca cozinha", False),
        ("Balança Digital de Cozinha para Alimentos", "balanca cozinha", True),
        ("Espátula de Silicone para Maquiagem", "espatula silicone", False),
        ("Espátula de Silicone para Cozinha", "espatula silicone", True),
        ("Escova de Limpeza Multifuncional Flexível Para Garrafas Mamadeiras Liquidificador De Silicone", "liquidificador", False),
        ("Interruptor Forno Eletrico Fischer Gourmet Grill 44L", "grill eletrico", False),
        ("Cafeteira De Prensa Francesa 600ml Manual Premium Filtro Inox Café Chá Espumador de Leite", "espumador de leite", False),
        ("Oleo Mineral Grau Usp para Selar e hidratar Tabua De corte Carne Churrasco 500 ml", "tabua de corte", False),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(shopee_v23.evaluate_keyword(title, keyword, rules).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise RuntimeError("Cozinha semantic regression failed: " + json.dumps(failures, ensure_ascii=False))
    print(f"COZINHA_SEM_COMPLICACAO_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


def _run_kitchen_regression_for_base(_rules_doc: dict) -> None:
    run_semantic_regression()


def safe_scan() -> int:
    run_semantic_regression()
    base.run_conecta_regression_checks = _run_kitchen_regression_for_base
    rc = base.safe_scan()
    data = base.load_json(SELECTION_PATH, {})
    semantic = dict(data.get("semanticValidation") or {})
    semantic["rulesFile"] = "config/shopee_cozinha_sem_complicacao_intent_rules.json"
    semantic["profileVersion"] = 3
    semantic["profileName"] = "Cozinha Sem Complicação"
    data["semanticValidation"] = semantic
    base.save_atomic(SELECTION_PATH, data)
    base.validate_selection(data)
    print("COZINHA_SEM_COMPLICACAO_SAFE_READY: 20 produtos; 20 intenções; histórico e seleção exclusivos; Blogger não alterado.")
    return rc


def validate_only() -> int:
    run_semantic_regression()
    products = base.validate_selection(base.load_json(SELECTION_PATH, {}))
    print(f"COZINHA_SEM_COMPLICACAO_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def store_write(dry_run: bool) -> int:
    rc = base.write_store(dry_run)
    print("COZINHA_SEM_COMPLICACAO_STORE_DRY_RUN_PASS" if dry_run else f"COZINHA_SEM_COMPLICACAO_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return rc


def hero_write(dry_run: bool) -> int:
    rc = base.write_hero(dry_run)
    print("COZINHA_SEM_COMPLICACAO_HERO_DRY_RUN_PASS" if dry_run else "COZINHA_SEM_COMPLICACAO_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return rc


def persist() -> int:
    rc = base.persist_rotation()
    print("COZINHA_SEM_COMPLICACAO_ROTATION_PERSIST_PASS: seleção validada registrada após PASS público.")
    return rc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=[
        "safe", "validate", "identity-dry-run", "identity-live", "identity",
        "store-dry-run", "store-live", "hero-dry-run", "hero-live", "persist"
    ])
    args = parser.parse_args()
    return {
        "safe": safe_scan,
        "validate": validate_only,
        "identity-dry-run": lambda: write_identity(True),
        "identity-live": lambda: write_identity(False),
        "identity": identity_check,
        "store-dry-run": lambda: store_write(True),
        "store-live": lambda: store_write(False),
        "hero-dry-run": lambda: hero_write(True),
        "hero-live": lambda: hero_write(False),
        "persist": persist,
    }[args.command]()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"COZINHA_SEM_COMPLICACAO_STORE_FAILED: {exc}", file=sys.stderr)
        raise
