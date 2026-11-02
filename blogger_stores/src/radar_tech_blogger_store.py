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
SCAN_DIR = DATA_DIR / "radar_tech_blogger_scan"
HISTORY_PATH = DATA_DIR / "radar_tech_blogger_rotation.json"
SELECTION_PATH = DATA_DIR / "radar_tech_blogger_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_radar_tech_blogger.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_radar_tech_blogger_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "7487888217273188851"
POST_ID = "906894044295273477"
STORE_PAGE = "https://portalradartechbr.blogspot.com/p/loja.html"
STORE_POST_URL = "https://portalradartechbr.blogspot.com/2026/10/loja.html"
RECENT_DAYS = max(1, min(int(os.getenv("RADAR_TECH_BLOGGER_STORE_RECENT_DAYS", "14")), 90))
SYSTEM_ERROR_RETRIES = max(2, min(int(os.getenv("RADAR_TECH_BLOGGER_SHOPEE_SYSTEM_RETRIES", "4")), 6))

CATEGORY_META = {
    "Casa & Organizacao": ("Casa & Organização", "bls-casa-organizacao", "Casa"),
    "Cozinha & Utilidades": ("Cozinha & Utilidades", "bls-cozinha-utilidades", "Cozinha"),
    "Tecnologia & Acessorios": ("Tecnologia & Acessórios", "bls-tecnologia", "Tecnologia"),
    "Beleza & Cuidados": ("Beleza & Cuidados", "bls-beleza", "Beleza"),
    "Dia a Dia & Praticidade": ("Dia a Dia & Praticidade", "bls-dia-a-dia", "Dia a dia"),
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
    return _orig_render_store(data).replace("conecta-achados-store-auto-css", "radar-tech-blogger-store-auto-css")


def hero_css() -> str:
    return _orig_hero_css().replace("conecta-achados-hero-auto-css", "radar-tech-blogger-hero-auto-css")


base.render_store = render_store
base.hero_css = hero_css

IDENTITY_REPLACEMENTS = [
    ("Achados práticos para casa, tecnologia, beleza e dia a dia", "Portal Radar Tech — tecnologia e achados práticos para a rotina"),
    ("Radar Tech BR — tecnologia e achados práticos para a rotina", "Portal Radar Tech — tecnologia e achados práticos para a rotina"),
    ("Descubra produtos úteis para facilitar a rotina", "Tecnologia e produtos úteis selecionados para facilitar o dia a dia"),
    ("Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.", "Uma vitrine afiliada do Portal Radar Tech com tecnologia, casa, cozinha, cuidados e praticidade, selecionados automaticamente na Shopee."),
    ("Uma vitrine afiliada do Radar Tech BR com tecnologia, casa, cozinha, cuidados e praticidade, selecionados automaticamente na Shopee.", "Uma vitrine afiliada do Portal Radar Tech com tecnologia, casa, cozinha, cuidados e praticidade, selecionados automaticamente na Shopee."),
    ("Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia", "Vitrine Portal Radar Tech: tecnologia e produtos práticos para o dia a dia"),
    ("Vitrine Radar Tech BR: tecnologia e produtos práticos para o dia a dia", "Vitrine Portal Radar Tech: tecnologia e produtos práticos para o dia a dia"),
]


def transform_identity(raw: str) -> str:
    out = raw
    for old, new in IDENTITY_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def verify_identity(raw: str) -> None:
    required = [
        STORE_PAGE,
        "Portal Radar Tech — tecnologia e achados práticos para a rotina",
        "Tecnologia e produtos úteis selecionados para facilitar o dia a dia",
        "Casa &amp; Organização",
        "Cozinha &amp; Utilidades",
        "Tecnologia &amp; Acessórios",
        "Beleza &amp; Cuidados",
        "Dia a Dia &amp; Praticidade",
        "#bls-casa-organizacao",
        "#bls-cozinha-utilidades",
        "#bls-tecnologia",
        "#bls-beleza",
        "#bls-dia-a-dia",
        "blogger-liq-layout-wide-css",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Portal Radar Tech Blogger incompleta: {missing}")
    forbidden = [
        "Radar Tech BR — tecnologia e achados práticos para a rotina",
        "Uma vitrine afiliada do Radar Tech BR",
        "Vitrine Radar Tech BR:",
        "https://conectaachados.blogspot.com/p/loja.html",
        "https://achadosparacasa2026.blogspot.com/p/loja.html",
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        "https://moda-ofertas.blogspot.com/p/loja.html",
        "https://canal-attitude.blogspot.com/p/loja.html",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência antiga ou de outro blog no Portal Radar Tech: {bad}")


def write_identity(dry_run: bool) -> int:
    service, post = base.get_service_post()
    raw = str(post.get("content") or "")
    new_raw = transform_identity(raw)
    verify_identity(new_raw)
    if dry_run:
        print("RADAR_TECH_BLOGGER_IDENTITY_DRY_RUN_PASS: identidade Portal Radar Tech validada em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_identity(str(verify.get("content") or ""))
    print("RADAR_TECH_BLOGGER_IDENTITY_PASS: domínio, Page Loja, layout e identidade Portal Radar Tech confirmados.")
    return 0


def identity_check() -> int:
    _, post = base.get_service_post()
    verify_identity(str(post.get("content") or ""))
    print("RADAR_TECH_BLOGGER_IDENTITY_PASS: domínio, Page Loja, layout e identidade Portal Radar Tech confirmados.")
    return 0


def run_radar_semantic_regression() -> None:
    rules = json.loads(INTENT_RULES_PATH.read_text(encoding="utf-8"))
    cases = [
        ("Processador Picador De Alimentos Alça 3L Moedor De Carne Mixer Elétrico Cozinha Casa Alho 110v", "mixer eletrico", False),
        ("Mixer Vertical Elétrico 3 em 1 500W com Copo e Batedor", "mixer eletrico", True),
        ("Kit 5 Suporte Organizador de Vassoura Rodo Mop Utensílios de Parede Gancho Multiuso Adesivo Cozinha", "organizador cozinha", False),
        ("Organizador de Cozinha Prateleira para Temperos e Mantimentos", "organizador cozinha", True),
        ("Tomada De Parede Dupla USB E USB-C Carregador Rápido 4 Em 1 Bivolt", "carregador usb c", False),
        ("Carregador Rápido USB-C 20W PD Fonte Bivolt", "carregador usb c", True),
        ("Capa Térmica para Chapinha de Cabelo", "chapinha cabelo", False),
        ("Lizze Chapinha De Cabelo Profissional 480 Extreme", "chapinha cabelo", True),
        ("Fone com fio P2 Bluetooth para Celular", "fone bluetooth", False),
        ("Fone de Ouvido Sem Fio Bluetooth com Cancelamento de Ruído", "fone bluetooth", True),
        ("Lanterna Bluetooth com Caixa de Som Recarregável USB", "lanterna recarregavel", False),
        ("Mini Lanterna Tática LED Recarregável USB com Zoom", "lanterna recarregavel", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(shopee_v23.evaluate_keyword(title, keyword, rules).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise RuntimeError("Radar semantic regression failed: " + json.dumps(failures, ensure_ascii=False))
    print(f"RADAR_TECH_BLOGGER_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


def safe_scan() -> int:
    run_radar_semantic_regression()
    rc = base.safe_scan()
    data = base.load_json(SELECTION_PATH, {})
    semantic = dict(data.get("semanticValidation") or {})
    semantic["rulesFile"] = "config/shopee_radar_tech_blogger_intent_rules.json"
    semantic["profileVersion"] = 5
    semantic["profileName"] = "Portal Radar Tech Blogger"
    data["semanticValidation"] = semantic
    base.save_atomic(SELECTION_PATH, data)
    base.validate_selection(data)
    print("RADAR_TECH_BLOGGER_SAFE_READY: 20 produtos; 20 intenções; histórico e seleção exclusivos; Blogger não alterado.")
    return rc


def validate_only() -> int:
    run_radar_semantic_regression()
    products = base.validate_selection(base.load_json(SELECTION_PATH, {}))
    print(f"RADAR_TECH_BLOGGER_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def store_write(dry_run: bool) -> int:
    rc = base.write_store(dry_run)
    print("RADAR_TECH_BLOGGER_STORE_DRY_RUN_PASS" if dry_run else f"RADAR_TECH_BLOGGER_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return rc


def hero_write(dry_run: bool) -> int:
    rc = base.write_hero(dry_run)
    print("RADAR_TECH_BLOGGER_HERO_DRY_RUN_PASS" if dry_run else "RADAR_TECH_BLOGGER_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return rc


def persist() -> int:
    rc = base.persist_rotation()
    print("RADAR_TECH_BLOGGER_ROTATION_PERSIST_PASS: seleção validada registrada após PASS público.")
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
        print(f"RADAR_TECH_BLOGGER_STORE_FAILED: {exc}", file=sys.stderr)
        raise
