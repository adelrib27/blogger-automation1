#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "blogger_stores" / "data"
SCAN_DIR = DATA_DIR / "estilo_dia_a_dia_scan"
HISTORY_PATH = DATA_DIR / "estilo_dia_a_dia_rotation.json"
SELECTION_PATH = DATA_DIR / "estilo_dia_a_dia_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_estilo_dia_a_dia.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_estilo_dia_a_dia_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "4830103887652146866"
POST_ID = "3362829797679236320"
STORE_PAGE = "https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/p/loja.html"
STORE_POST_URL = "https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/2026/11/loja.html"
RECENT_DAYS = max(1, min(int(os.getenv("ESTILO_STORE_RECENT_DAYS", "14")), 90))

CATEGORY_META = {
    "Moda Feminina": ("Moda Feminina", "bls-moda-feminina", "Moda"),
    "Calcados & Conforto": ("Calçados & Conforto", "bls-calcados", "Calçados"),
    "Bolsas & Acessorios": ("Bolsas & Acessórios", "bls-bolsas-acessorios", "Acessórios"),
    "Cabelo & Styling": ("Cabelo & Styling", "bls-cabelo", "Cabelo"),
    "Cuidados Pessoais": ("Cuidados Pessoais", "bls-cuidados", "Cuidados"),
}

# O módulo Shopee congela estes caminhos no import. Importe-o com o perfil Estilo
# antes de carregar o motor-base já validado do Conecta.
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
from blogger_policy_guard import require_product_allowed  # noqa: E402

# Estado/alvo isolados do Estilo. Código é compartilhado; dados nunca são.
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


def final_keyword_gate(product: dict, keyword: str) -> bool:
    title = base.norm(product.get("productName") or "")
    key = base.norm(keyword)
    blocks = {
        "vestido feminino": ["infantil", "menina", "bebe", "pet", "cachorro", "boneca", "fantasia"],
        "conjunto feminino": ["infantil", "menina", "bebe", "pet", "cachorro", "boneca"],
        "saia midi": ["infantil", "menina", "bebe", "pet", "cachorro", "boneca", "fantasia"],
        "blusa feminina": ["infantil", "menina", "bebe", "pet", "cachorro", "boneca"],
        "tenis feminino": ["infantil", "menina", "bebe", "cadarco", "palmilha", "chaveiro", "miniatura", "pet"],
        "sandalia feminina": ["infantil", "menina", "bebe", "tira de reposicao", "chaveiro", "miniatura", "pet"],
        "sapatilha feminina": ["infantil", "menina", "bebe", "aquatica", "natacao", "ballet infantil", "pet"],
        "chinelo feminino": ["infantil", "menina", "bebe", "chaveiro", "miniatura", "pet"],
        "bolsa feminina": ["bolsa termica", "ferramenta", "primeiros socorros", "remedio", "pet", "cachorro"],
        "mochila feminina": ["infantil", "menina", "bebe", "pet", "cachorro", "mochila de hidratacao"],
        "carteira feminina": ["carteira de trabalho", "carteira profissional", "documento", "chaveiro", "miniatura", "pet"],
        "cinto feminino": ["cinto de seguranca", "automotivo", "ferramenta", "academia", "lombar", "pet", "cachorro"],
        "escova secadora": ["refil", "capa para escova", "suporte para escova", "peca para escova"],
        "secador de cabelo": ["difusor", "bico para secador", "suporte para secador", "resistencia para secador", "cabo para secador", "peca para secador"],
        "chapinha cabelo": ["capa para chapinha", "suporte para chapinha", "bolsa para chapinha", "peca para chapinha"],
        "modelador de cachos": ["luva para modelador", "capa para modelador", "suporte para modelador", "refil", "peca"],
        "aparador corporal": ["papa bolinhas", "tira pelos de roupa", "removedor de pelos de roupa", "pet", "cachorro", "gato", "lamina de reposicao"],
        "barbeador eletrico": ["lamina de reposicao", "cabeca de reposicao", "capa para barbeador", "suporte para barbeador", "pet"],
        "depilador eletrico": ["cera", "linha depilatoria", "pinca", "creme depilatorio", "refil", "lamina de reposicao"],
        "escova facial eletrica": ["refil", "cabeca de reposicao", "esponja avulsa", "cabo avulso", "suporte para escova"],
    }
    if any(term in title for term in blocks.get(key, [])):
        return False

    female = ["feminino", "feminina", "mulher", "mulheres"]
    positive = {
        "vestido feminino": lambda: "vestido" in title and any(x in title for x in female),
        "conjunto feminino": lambda: "conjunto" in title and any(x in title for x in female),
        "saia midi": lambda: "saia" in title and "midi" in title,
        "blusa feminina": lambda: "blusa" in title and any(x in title for x in female),
        "tenis feminino": lambda: "tenis" in title and any(x in title for x in female),
        "sandalia feminina": lambda: "sandalia" in title and any(x in title for x in female),
        "sapatilha feminina": lambda: "sapatilha" in title and any(x in title for x in female + ["casual"]),
        "chinelo feminino": lambda: "chinelo" in title and any(x in title for x in female),
        "bolsa feminina": lambda: "bolsa" in title and any(x in title for x in female),
        "mochila feminina": lambda: "mochila" in title and any(x in title for x in female),
        "carteira feminina": lambda: "carteira" in title and any(x in title for x in female),
        "cinto feminino": lambda: "cinto" in title and any(x in title for x in female),
        "escova secadora": lambda: "escova" in title and any(x in title for x in ["secadora", "secador", "ar quente"]),
        "secador de cabelo": lambda: "secador" in title and any(x in title for x in ["cabelo", "cabelos"]),
        "chapinha cabelo": lambda: any(x in title for x in ["chapinha", "prancha"]) and any(x in title for x in ["cabelo", "cabelos", "alisadora", "alisador"]),
        "modelador de cachos": lambda: any(x in title for x in ["modelador", "babyliss"]) and any(x in title for x in ["cachos", "cacho", "cabelo", "cabelos"]),
        "aparador corporal": lambda: "aparador" in title and any(x in title for x in ["corporal", "corpo", "pelos", "pelo", "body groomer"]),
        "barbeador eletrico": lambda: any(x in title for x in ["barbeador", "maquina de barbear"]) and any(x in title for x in ["eletrico", "recarregavel", "usb"]),
        "depilador eletrico": lambda: "depilador" in title and any(x in title for x in ["eletrico", "recarregavel", "usb"]),
        "escova facial eletrica": lambda: any(x in title for x in ["escova facial", "escova de limpeza facial"]) and any(x in title for x in ["eletrica", "recarregavel", "usb", "sonica"]),
    }
    return positive[key]() if key in positive else False


def run_estilo_regression_checks(rules_doc: dict) -> None:
    cases = [
        ("Vestido Pet para Cachorro Feminino", "vestido feminino", False),
        ("Vestido Feminino Midi Casual", "vestido feminino", True),
        ("Conjunto Infantil Menina Verão", "conjunto feminino", False),
        ("Conjunto Feminino Cropped e Saia", "conjunto feminino", True),
        ("Palmilha para Tênis Feminino", "tenis feminino", False),
        ("Tênis Feminino Casual Confortável", "tenis feminino", True),
        ("Sapatilha Aquática Feminina Natação", "sapatilha feminina", False),
        ("Sapatilha Feminina Casual Conforto", "sapatilha feminina", True),
        ("Bolsa Térmica Feminina Alimentos", "bolsa feminina", False),
        ("Bolsa Feminina Transversal Casual", "bolsa feminina", True),
        ("Cinto de Segurança Feminino Automotivo", "cinto feminino", False),
        ("Cinto Feminino Couro Ajustável", "cinto feminino", True),
        ("Difusor Universal para Secador de Cabelo", "secador de cabelo", False),
        ("Secador de Cabelo Profissional 2000W", "secador de cabelo", True),
        ("Papa Bolinhas Aparador de Pelos de Roupa", "aparador corporal", False),
        ("Aparador Corporal de Pelos Recarregável", "aparador corporal", True),
        ("Cera para Depilação Elétrica", "depilador eletrico", False),
        ("Depilador Elétrico Feminino Recarregável", "depilador eletrico", True),
        ("Refil Cabeça para Escova Facial Elétrica", "escova facial eletrica", False),
        ("Escova Facial Elétrica Sônica Recarregável", "escova facial eletrica", True)
    ]
    failures = []
    for title, keyword, expected in cases:
        accepted = bool(shopee_v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        actual = accepted and final_keyword_gate({"productName": title}, keyword)
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha na regressão semântica Estilo: " + json.dumps(failures, ensure_ascii=False))
    print(f"ESTILO_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


base.final_keyword_gate = final_keyword_gate
base.run_conecta_regression_checks = run_estilo_regression_checks

_orig_render_store = base.render_store
_orig_hero_css = base.hero_css


def render_store(data: dict) -> str:
    return _orig_render_store(data).replace("conecta-achados-store-auto-css", "estilo-dia-a-dia-store-auto-css")


def hero_css() -> str:
    return _orig_hero_css().replace("conecta-achados-hero-auto-css", "estilo-dia-a-dia-hero-auto-css")


def build_hero(data: dict) -> list[str]:
    c = data.get("categories") or {}
    moda = c["Moda Feminina"]
    calcados = c["Calcados & Conforto"]
    bolsas = c["Bolsas & Acessorios"]
    cabelo = c["Cabelo & Styling"]
    cuidados = c["Cuidados Pessoais"]
    groups = [
        ("Moda e calçados em destaque", [(moda[0], "Moda Feminina"), (moda[1], "Moda Feminina"), (calcados[0], "Calcados & Conforto"), (calcados[1], "Calcados & Conforto")]),
        ("Bolsas e acessórios para completar o look", [(bolsas[0], "Bolsas & Acessorios"), (bolsas[1], "Bolsas & Acessorios"), (bolsas[2], "Bolsas & Acessorios"), (bolsas[3], "Bolsas & Acessorios")]),
        ("Cabelo e cuidados para a rotina", [(cabelo[0], "Cabelo & Styling"), (cabelo[1], "Cabelo & Styling"), (cuidados[0], "Cuidados Pessoais"), (cuidados[1], "Cuidados Pessoais")]),
    ]
    slides = []
    for idx, (title, items) in enumerate(groups):
        prefix = hero_css() if idx == 0 else ""
        cards = ''.join(base.hero_card(product, category) for product, category in items)
        slides.append(prefix + f'<div class="blh-card"><strong>{base.esc(title)}</strong><div class="blh-grid">{cards}</div></div>')
    return slides


base.render_store = render_store
base.hero_css = hero_css
base.build_hero = build_hero


IDENTITY_REPLACEMENTS = [
    ("Achados práticos para casa, tecnologia, beleza e dia a dia", "Moda, beleza e acessórios para o dia a dia"),
    ("Descubra produtos úteis para facilitar a rotina", "Estilo prático para vestir, cuidar e combinar melhor"),
    ("Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.", "Uma vitrine afiliada com moda, calçados, bolsas, acessórios e cuidados pessoais selecionados automaticamente na Shopee."),
    ("Cozinha e tecnologia", "Moda e acessórios"),
    ("Soluções práticas para cozinhar, conectar e organizar melhor", "Peças e complementos para compor looks com praticidade"),
    ("A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.", "A seleção prioriza itens coerentes com moda, beleza e acessórios, bloqueando peças de reposição e falsos positivos."),
    ("Ver cozinha", "Ver moda"),
    ("Ver tecnologia", "Ver acessórios"),
    ("Beleza e praticidade", "Cabelo e cuidados"),
    ("Achados reais para cuidados pessoais e rotina", "Ferramentas de beleza e cuidados para a rotina"),
    ("Ver beleza", "Ver cabelo"),
    ("Ver dia a dia", "Ver cuidados"),
    ("#bls-casa-organizacao", "#bls-moda-feminina"),
    ("#bls-cozinha-utilidades", "#bls-calcados"),
    ("#bls-tecnologia", "#bls-bolsas-acessorios"),
    ("#bls-beleza", "#bls-cabelo"),
    ("#bls-dia-a-dia", "#bls-cuidados"),
    ("Casa &amp; Organização", "Moda Feminina"),
    ("organização e soluções para o lar", "vestidos, conjuntos, saias e blusas"),
    ("Cozinha &amp; Utilidades", "Calçados &amp; Conforto"),
    ("itens úteis para a cozinha", "tênis, sandálias e opções para a rotina"),
    ("Tecnologia &amp; Acessórios", "Bolsas &amp; Acessórios"),
    ("conectividade e eletrônicos úteis", "bolsas, mochilas, carteiras e cintos"),
    ("Beleza &amp; Cuidados", "Cabelo &amp; Styling"),
    ("cuidados pessoais e beleza", "secagem, alisamento e modelagem"),
    ("Dia a Dia &amp; Praticidade", "Cuidados Pessoais"),
    ("produtos úteis para a rotina", "aparadores e aparelhos de cuidado pessoal"),
    ("Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia", "Vitrine de moda, beleza e acessórios para o dia a dia"),
]


def transform_identity(raw: str) -> str:
    out = raw
    for old, new in IDENTITY_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def verify_identity(raw: str) -> None:
    required = [
        STORE_PAGE,
        "Moda, beleza e acessórios para o dia a dia",
        "Estilo prático para vestir, cuidar e combinar melhor",
        "Moda Feminina",
        "Calçados &amp; Conforto",
        "Bolsas &amp; Acessórios",
        "Cabelo &amp; Styling",
        "Cuidados Pessoais",
        '#bls-moda-feminina',
        '#bls-calcados',
        '#bls-bolsas-acessorios',
        '#bls-cabelo',
        '#bls-cuidados',
        "blogger-liq-layout-wide-css",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Estilo incompleta: {missing}")
    forbidden = [
        "https://conectaachados.blogspot.com/p/loja.html",
        "https://achadosparacasa2026.blogspot.com/p/loja.html",
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        "https://liquidificadores-em-foco.blogspot.com/p/loja.html",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência de outro blog detectada no Estilo: {bad}")


def write_identity(dry_run: bool) -> int:
    service, post = base.get_service_post()
    raw = str(post.get("content") or "")
    new_raw = transform_identity(raw)
    verify_identity(new_raw)
    if dry_run:
        print("ESTILO_IDENTITY_DRY_RUN_PASS: identidade validada em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_identity(str(verify.get("content") or ""))
    print("ESTILO_IDENTITY_PASS: domínio, Page Loja, layout e nicho moda/beleza corretos.")
    return 0


def identity_check() -> int:
    _, post = base.get_service_post()
    verify_identity(str(post.get("content") or ""))
    print("ESTILO_IDENTITY_PASS: domínio, Page Loja, layout e nicho moda/beleza corretos.")
    return 0


def safe_scan() -> int:
    rc = base.safe_scan()
    data = base.load_json(SELECTION_PATH, {})
    semantic = dict(data.get("semanticValidation") or {})
    semantic["rulesFile"] = "config/shopee_estilo_dia_a_dia_intent_rules.json"
    semantic["profileVersion"] = 1
    semantic["profileName"] = "Estilo no Dia a Dia"
    data["semanticValidation"] = semantic
    base.save_atomic(SELECTION_PATH, data)
    base.validate_selection(data)
    print("ESTILO_SAFE_READY: 20 produtos; 20 intenções; histórico e seleção exclusivos; Blogger não alterado.")
    return rc


def validate_only() -> int:
    products = base.validate_selection(base.load_json(SELECTION_PATH, {}))
    print(f"ESTILO_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def store_write(dry_run: bool) -> int:
    rc = base.write_store(dry_run)
    print("ESTILO_STORE_DRY_RUN_PASS" if dry_run else f"ESTILO_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return rc


def hero_write(dry_run: bool) -> int:
    rc = base.write_hero(dry_run)
    print("ESTILO_HERO_DRY_RUN_PASS" if dry_run else "ESTILO_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return rc


def persist() -> int:
    rc = base.persist_rotation()
    print("ESTILO_ROTATION_PERSIST_PASS: seleção validada registrada após PASS público.")
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
        print(f"ESTILO_STORE_FAILED: {exc}", file=sys.stderr)
        raise
