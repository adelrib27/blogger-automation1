#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "blogger_stores" / "data"
SCAN_DIR = DATA_DIR / "vida_pet_pratica_scan"
HISTORY_PATH = DATA_DIR / "vida_pet_pratica_rotation.json"
SELECTION_PATH = DATA_DIR / "vida_pet_pratica_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_vida_pet_pratica.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_vida_pet_pratica_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "8052455848487624244"
POST_ID = "7332800716046515902"
STORE_PAGE = "https://vida-pet-pratica.blogspot.com/p/loja.html"
STORE_POST_URL = "https://vida-pet-pratica.blogspot.com/2026/11/loja.html"
RECENT_DAYS = max(1, min(int(os.getenv("VIDA_PET_PRATICA_STORE_RECENT_DAYS", "14")), 90))

CATEGORY_META = {
    "Passeio & Transporte": ("Passeio & Transporte", "bls-passeio-transporte", "Passeio"),
    "Alimentacao & Rotina": ("Alimentação & Rotina", "bls-alimentacao-rotina", "Alimentação"),
    "Higiene & Organizacao": ("Higiene & Organização", "bls-higiene-organizacao", "Higiene"),
    "Conforto & Descanso": ("Conforto & Descanso", "bls-conforto-descanso", "Conforto"),
    "Brinquedos & Enriquecimento": ("Brinquedos & Enriquecimento", "bls-brinquedos-enriquecimento", "Brinquedos"),
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

GLOBAL_POLICY_BLOCKS = [
    "medicamento", "remedio", "farmaco", "veterinario", "clinico", "terapeutico",
    "antipulga", "anti pulga", "pulgas e carrapatos", "carrapaticida", "vermifugo",
    "suplemento", "vitamina", "probiotico", "cicatrizante", "antibiotico", "anti inflamatorio",
    "insulina", "seringa", "termometro", "oximetro", "nebulizador", "inalador",
    "medidor glicose", "glicosimetro", "colar elizabetano", "pos cirurgico",
    "choque eletrico", "coleira de choque", "adestramento eletrico",
]


def final_keyword_gate(product: dict, keyword: str) -> bool:
    title = base.norm(product.get("productName") or "")
    if any(term in title for term in GLOBAL_POLICY_BLOCKS):
        return False
    return bool(title and base.norm(keyword))


def run_pet_regression_checks(rules_doc: dict) -> None:
    cases = [
        ("Peitoral Ajustável para Cachorro Pet Porte Médio", "peitoral cachorro", True),
        ("Peitoral Humano Esportivo", "peitoral cachorro", False),
        ("Guia para Cachorro Pet 1,5m com Mosquetão", "guia cachorro", True),
        ("Guia Turístico de Viagem", "guia cachorro", False),
        ("Caixa de Transporte Pet para Cães e Gatos", "caixa transporte pet", True),
        ("Caixa Organizadora Transparente", "caixa transporte pet", False),
        ("Bolsa Transporte Pet Cães Gatos Ventilada", "bolsa transporte pet", True),
        ("Bolsa Feminina Grande", "bolsa transporte pet", False),
        ("Comedouro Pet Inox Antiderrapante", "comedouro pet inox", True),
        ("Suporte Avulso para Comedouro Inox", "comedouro pet inox", False),
        ("Fonte Bebedouro Automático Elétrico para Gato Pet", "bebedouro pet automatico", True),
        ("Filtro Avulso Bebedouro Automático Pet", "bebedouro pet automatico", False),
        ("Tapete para Comedouro Pet Ração Impermeável", "tapete comedouro pet", True),
        ("Tapete Higiênico Pet 30 Unidades", "tapete comedouro pet", False),
        ("Pote Porta Ração Hermético Pet 10kg", "pote racao hermetico pet", True),
        ("Comedouro Automático Pet", "pote racao hermetico pet", False),
        ("Tapete Higiênico Cachorro Pet Super Absorvente", "tapete higienico cachorro", True),
        ("Fralda Descartável Pet", "tapete higienico cachorro", False),
        ("Coletor de Fezes Cachorro Pet Porta Saquinho", "coletor fezes cachorro", True),
        ("Refil Saquinho para Coletor Fezes Cachorro", "coletor fezes cachorro", False),
        ("Escova Removedora de Pelos Pet Cães e Gatos", "escova removedora pelos pet", True),
        ("Escova Secadora de Cabelo Humano", "escova removedora pelos pet", False),
        ("Organizador de Acessórios Pet para Cachorro", "organizador acessorios pet", True),
        ("Organizador de Maquiagem", "organizador acessorios pet", False),
        ("Cama Cachorro Pet Lavável Macia", "cama cachorro lavavel", True),
        ("Capa Avulsa para Cama Cachorro", "cama cachorro lavavel", False),
        ("Cama Gato Pet Confortável", "cama gato", True),
        ("Cama Infantil Boneca", "cama gato", False),
        ("Manta Pet Cachorro Gato Macia", "manta pet", True),
        ("Manta Casal Sofá", "manta pet", False),
        ("Toca Gato Pet Iglu Lavável", "toca gato", True),
        ("Toca Infantil Barraca", "toca gato", False),
        ("Brinquedo Mordedor Cachorro Pet Borracha", "brinquedo mordedor cachorro", True),
        ("Mordedor Bebê Silicone", "brinquedo mordedor cachorro", False),
        ("Bola Interativa Pet Cachorro Gato", "bola interativa pet", True),
        ("Bola de Futebol Infantil", "bola interativa pet", False),
        ("Varinha Gato Brinquedo Interativo com Pena", "varinha gato brinquedo", True),
        ("Vara de Pesca Telescópica", "varinha gato brinquedo", False),
        ("Arranhador Gato Pet Sisal Torre", "arranhador gato", True),
        ("Refil Sisal para Arranhador Gato", "arranhador gato", False),
        ("Peitoral Veterinário Pós Cirúrgico para Cachorro", "peitoral cachorro", False),
        ("Comedouro Pet Inox com Suplemento Vitamínico", "comedouro pet inox", False),
    ]
    failures = []
    for title, keyword, expected in cases:
        semantic = bool(shopee_v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        actual = semantic and final_keyword_gate({"productName": title}, keyword)
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha na regressão semântica Vida Pet Prática: " + json.dumps(failures, ensure_ascii=False))
    print(f"VIDA_PET_PRATICA_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


base.final_keyword_gate = final_keyword_gate
base.run_conecta_regression_checks = run_pet_regression_checks
_orig_render_store = base.render_store
_orig_hero_css = base.hero_css


def render_store(data: dict) -> str:
    return _orig_render_store(data).replace("conecta-achados-store-auto-css", "vida-pet-pratica-store-auto-css")


def hero_css() -> str:
    return _orig_hero_css().replace("conecta-achados-hero-auto-css", "vida-pet-pratica-hero-auto-css")


def build_hero(data: dict) -> list[str]:
    c = data.get("categories") or {}
    passeio = c["Passeio & Transporte"]
    alimentacao = c["Alimentacao & Rotina"]
    higiene = c["Higiene & Organizacao"]
    conforto = c["Conforto & Descanso"]
    brinquedos = c["Brinquedos & Enriquecimento"]
    groups = [
        ("Passeio e alimentação para comparar", [(passeio[0], "Passeio & Transporte"), (passeio[1], "Passeio & Transporte"), (alimentacao[0], "Alimentacao & Rotina"), (alimentacao[1], "Alimentacao & Rotina")]),
        ("Higiene e conforto na rotina", [(higiene[0], "Higiene & Organizacao"), (higiene[1], "Higiene & Organizacao"), (conforto[0], "Conforto & Descanso"), (conforto[1], "Conforto & Descanso")]),
        ("Brinquedos e enriquecimento", [(brinquedos[0], "Brinquedos & Enriquecimento"), (brinquedos[1], "Brinquedos & Enriquecimento"), (brinquedos[2], "Brinquedos & Enriquecimento"), (brinquedos[3], "Brinquedos & Enriquecimento")]),
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


def transform_identity(raw: str) -> str:
    return raw


def verify_identity(raw: str) -> None:
    required = [
        STORE_PAGE, "Acessórios e rotina para cães e gatos", "Achados pet para comparar com mais segurança",
        "Passeio &amp; Transporte", "Alimentação &amp; Rotina", "Higiene &amp; Organização",
        "Conforto &amp; Descanso", "Brinquedos &amp; Enriquecimento",
        "#bls-passeio-transporte", "#bls-alimentacao-rotina", "#bls-higiene-organizacao",
        "#bls-conforto-descanso", "#bls-brinquedos-enriquecimento", "blogger-liq-layout-wide-css",
        "Não publicamos medicamentos, suplementos ou dispositivos veterinários/de saúde.",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Vida Pet Prática incompleta: {missing}")
    forbidden = [
        "casa-pratica-lab-20261102.blogspot.com", "conectaachados.blogspot.com",
        "Casa &amp; Organização", "Cozinha &amp; Eletroportáteis", "Tecnologia &amp; Acessórios",
        "Beleza &amp; Cuidados", "Clima &amp; Conforto", "Utilidades &amp; Rotina",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência/identidade indevida no Vida Pet Prática: {bad}")


def safe_scan() -> int:
    rc = base.safe_scan()
    data = base.load_json(SELECTION_PATH, {})
    semantic = dict(data.get("semanticValidation") or {})
    semantic.update({
        "rulesFile": "config/shopee_vida_pet_pratica_intent_rules.json",
        "profileVersion": 2,
        "profileName": "Vida Pet Prática",
        "regulatedPetHealthExcluded": True,
    })
    data["semanticValidation"] = semantic
    base.save_atomic(SELECTION_PATH, data)
    base.validate_selection(data)
    print("VIDA_PET_PRATICA_SAFE_READY: 20 produtos; 20 intenções; saúde/veterinária excluída; Blogger não alterado.")
    return rc


def validate_only() -> int:
    products = base.validate_selection(base.load_json(SELECTION_PATH, {}))
    print(f"VIDA_PET_PRATICA_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def persist() -> int:
    rc = base.persist_rotation()
    print("VIDA_PET_PRATICA_ROTATION_PERSIST_PASS: seleção registrada somente após PASS público.")
    return rc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["safe", "validate", "persist"])
    args = parser.parse_args()
    return {"safe": safe_scan, "validate": validate_only, "persist": persist}[args.command]()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VIDA_PET_PRATICA_STORE_FAILED: {exc}", file=sys.stderr)
        raise
