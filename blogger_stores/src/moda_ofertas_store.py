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
SCAN_DIR = DATA_DIR / "moda_ofertas_scan"
HISTORY_PATH = DATA_DIR / "moda_ofertas_rotation.json"
SELECTION_PATH = DATA_DIR / "moda_ofertas_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_moda_ofertas.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_moda_ofertas_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "2858597309582499028"
POST_ID = "4871366557503134389"
STORE_PAGE = "https://moda-ofertas.blogspot.com/p/loja.html"
STORE_POST_URL = "https://moda-ofertas.blogspot.com/2026/10/loja.html"
RECENT_DAYS = max(1, min(int(os.getenv("MODA_OFERTAS_STORE_RECENT_DAYS", "14")), 90))
SYSTEM_ERROR_RETRIES = max(2, min(int(os.getenv("MODA_OFERTAS_SHOPEE_SYSTEM_RETRIES", "4")), 6))

CATEGORY_META = {
    "Moda Feminina": ("Moda Feminina", "bls-moda-feminina", "Moda feminina"),
    "Moda Masculina": ("Moda Masculina", "bls-moda-masculina", "Moda masculina"),
    "Calcados & Bolsas": ("Calçados & Bolsas", "bls-calcados-bolsas", "Calçados e bolsas"),
    "Acessorios": ("Acessórios", "bls-acessorios", "Acessórios"),
    "Beleza & Cuidados": ("Beleza & Cuidados", "bls-beleza-cuidados", "Beleza"),
}

# O módulo Shopee congela estes caminhos no import. Configure o perfil antes
# de carregar o motor-base validado do Conecta Achados.
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

# Estado e alvo são exclusivos do Moda e Ofertas. O código-base é compartilhado,
# mas seleção, histórico, config e Store Post nunca são compartilhados.
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

# A API Shopee vem apresentando o erro transitório 10000 em consultas isoladas.
# O motor-base não repete esse código; neste perfil fazemos retry limitado e
# fail-closed. Nenhum filtro semântico, comissão ou Policy Guard é relaxado.
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
            print(
                f"  retry Shopee System Error 10000: tentativa {attempt + 1}/"
                f"{SYSTEM_ERROR_RETRIES} em {delay}s"
            )
            time.sleep(delay)
    return last_response


shopee_v23.base.post_graphql = resilient_post_graphql


def final_keyword_gate(product: dict, keyword: str) -> bool:
    title = base.norm(product.get("productName") or "")
    key = base.norm(keyword)

    blocks = {
        "vestido feminino": ["infantil", "menina", "bebe", "pet", "cachorro", "boneca", "fantasia"],
        "conjunto feminino": ["infantil", "menina", "bebe", "pet", "cachorro", "boneca"],
        "saia midi": ["infantil", "menina", "bebe", "pet", "cachorro", "boneca", "fantasia"],
        "blusa feminina": ["infantil", "menina", "bebe", "pet", "cachorro", "boneca"],
        "camiseta masculina": ["infantil", "menino", "bebe", "pet", "cachorro", "boneco"],
        "camisa polo masculina": ["infantil", "menino", "bebe", "pet", "cachorro", "boneco"],
        "bermuda masculina": ["infantil", "menino", "bebe", "pet", "cachorro", "boneco"],
        "calca masculina": ["infantil", "menino", "bebe", "pet", "cachorro", "boneco"],
        "tenis feminino": ["infantil", "menina", "bebe", "cadarco", "palmilha", "chaveiro", "miniatura", "pet"],
        "sandalia feminina": ["infantil", "menina", "bebe", "tira de reposicao", "chaveiro", "miniatura", "pet"],
        "bolsa feminina": ["bolsa termica", "necessaire", "porta maquiagem", "estojo", "ferramenta", "primeiros socorros", "remedio", "pet", "cachorro"],
        "mochila feminina": ["infantil", "menina", "bebe", "pet", "cachorro", "mochila de hidratacao"],
        "carteira feminina": ["kit bolsa", "kit 2 bolsa", "kit com bolsa", "bolsa + carteira", "carteira de trabalho", "carteira profissional", "documento", "chaveiro", "miniatura", "pet"],
        "cinto feminino": ["short", "shorts", "calca", "saia", "vestido", "macacao", "conjunto", "cinto de seguranca", "automotivo", "ferramenta", "academia", "lombar", "pet", "cachorro"],
        "oculos de sol feminino": ["estojo para oculos", "capa para oculos", "cordao para oculos", "corrente para oculos", "chaveiro", "miniatura", "infantil", "menina", "bebe", "pet"],
        "relogio feminino": ["pulseira avulsa", "pulseira para relogio", "capa para relogio", "pelicula", "carregador", "infantil", "menina", "bebe", "chaveiro", "miniatura", "pet"],
        "escova secadora": ["refil", "capa para escova", "suporte para escova", "peca para escova"],
        "secador de cabelo": ["difusor", "bico para secador", "suporte para secador", "resistencia para secador", "cabo para secador", "peca para secador"],
        "barbeador eletrico": ["lamina de reposicao", "cabeca de reposicao", "capa para barbeador", "suporte para barbeador", "pet"],
        "depilador eletrico": ["cera", "linha depilatoria", "pinca", "creme depilatorio", "refil", "lamina de reposicao"],
    }
    if any(term in title for term in blocks.get(key, [])):
        return False

    female = ["feminino", "feminina", "mulher", "mulheres"]
    male = ["masculino", "masculina", "homem", "homens"]
    positive = {
        "vestido feminino": lambda: "vestido" in title and any(x in title for x in female),
        "conjunto feminino": lambda: "conjunto" in title and any(x in title for x in female),
        "saia midi": lambda: "saia" in title and "midi" in title,
        "blusa feminina": lambda: "blusa" in title and any(x in title for x in female),
        "camiseta masculina": lambda: "camiseta" in title and any(x in title for x in male),
        "camisa polo masculina": lambda: "polo" in title and any(x in title for x in male),
        "bermuda masculina": lambda: "bermuda" in title and any(x in title for x in male),
        "calca masculina": lambda: "calca" in title and any(x in title for x in male),
        "tenis feminino": lambda: "tenis" in title and any(x in title for x in female),
        "sandalia feminina": lambda: "sandalia" in title and any(x in title for x in female),
        "bolsa feminina": lambda: "bolsa" in title and any(x in title for x in female),
        "mochila feminina": lambda: "mochila" in title and any(x in title for x in female),
        "carteira feminina": lambda: "carteira" in title and any(x in title for x in female),
        "cinto feminino": lambda: "cinto" in title and any(x in title for x in female),
        "oculos de sol feminino": lambda: "oculos de sol" in title and any(x in title for x in female),
        "relogio feminino": lambda: any(x in title for x in ["relogio", "smartwatch"]) and any(x in title for x in female),
        "escova secadora": lambda: "escova" in title and any(x in title for x in ["secadora", "secador", "ar quente"]),
        "secador de cabelo": lambda: "secador" in title and any(x in title for x in ["cabelo", "cabelos"]),
        "barbeador eletrico": lambda: any(x in title for x in ["barbeador", "maquina de barbear"]) and any(x in title for x in ["eletrico", "recarregavel", "usb"]),
        "depilador eletrico": lambda: "depilador" in title and any(x in title for x in ["eletrico", "recarregavel", "usb"]),
    }
    return positive[key]() if key in positive else False


def run_moda_regression_checks(rules_doc: dict) -> None:
    cases = [
        ("Vestido Pet para Cachorro Feminino", "vestido feminino", False),
        ("Vestido Feminino Midi Casual", "vestido feminino", True),
        ("Conjunto Infantil Menina Verão", "conjunto feminino", False),
        ("Conjunto Feminino Cropped e Saia", "conjunto feminino", True),
        ("Saia Midi Infantil Menina", "saia midi", False),
        ("Saia Midi Feminina Cintura Alta", "saia midi", True),
        ("Blusa Infantil Menina Feminina", "blusa feminina", False),
        ("Blusa Feminina Manga Curta", "blusa feminina", True),
        ("Camiseta Infantil Menino Masculina", "camiseta masculina", False),
        ("Camiseta Masculina Básica Algodão", "camiseta masculina", True),
        ("Camisa Polo Infantil Menino", "camisa polo masculina", False),
        ("Camisa Polo Masculina Casual", "camisa polo masculina", True),
        ("Bermuda Infantil Menino Masculina", "bermuda masculina", False),
        ("Bermuda Masculina Sarja Casual", "bermuda masculina", True),
        ("Calça Infantil Menino Masculina", "calca masculina", False),
        ("Calça Masculina Jeans Slim", "calca masculina", True),
        ("Palmilha para Tênis Feminino", "tenis feminino", False),
        ("Tênis Feminino Casual Confortável", "tenis feminino", True),
        ("Tira de Reposição Sandália Feminina", "sandalia feminina", False),
        ("Sandália Feminina Confortável", "sandalia feminina", True),
        ("Bolsa Térmica Feminina Alimentos", "bolsa feminina", False),
        ("Bolsa Feminina Transversal Casual", "bolsa feminina", True),
        ("Mochila Infantil Menina Feminina", "mochila feminina", False),
        ("Mochila Feminina Casual Reforçada", "mochila feminina", True),
        ("Kit Bolsa + Carteira Feminina", "carteira feminina", False),
        ("Carteira Feminina Compacta", "carteira feminina", True),
        ("Short Feminino com Cinto", "cinto feminino", False),
        ("Cinto Feminino Couro Ajustável", "cinto feminino", True),
        ("Estojo para Óculos de Sol Feminino", "oculos de sol feminino", False),
        ("Óculos de Sol Feminino UV400", "oculos de sol feminino", True),
        ("Pulseira para Relógio Feminino", "relogio feminino", False),
        ("Relógio Feminino Analógico Casual", "relogio feminino", True),
        ("Refil para Escova Secadora", "escova secadora", False),
        ("Escova Secadora de Cabelo 1200W", "escova secadora", True),
        ("Difusor Universal para Secador de Cabelo", "secador de cabelo", False),
        ("Secador de Cabelo Profissional 2000W", "secador de cabelo", True),
        ("Lâmina de Reposição para Barbeador Elétrico", "barbeador eletrico", False),
        ("Barbeador Elétrico Recarregável USB", "barbeador eletrico", True),
        ("Cera para Depilador Elétrico", "depilador eletrico", False),
        ("Depilador Elétrico Feminino Recarregável", "depilador eletrico", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        accepted = bool(shopee_v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        actual = accepted and final_keyword_gate({"productName": title}, keyword)
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha na regressão semântica Moda e Ofertas: " + json.dumps(failures, ensure_ascii=False))
    print(f"MODA_OFERTAS_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


base.final_keyword_gate = final_keyword_gate
base.run_conecta_regression_checks = run_moda_regression_checks

_orig_render_store = base.render_store
_orig_hero_css = base.hero_css


def render_store(data: dict) -> str:
    return _orig_render_store(data).replace("conecta-achados-store-auto-css", "moda-ofertas-store-auto-css")


def hero_css() -> str:
    return _orig_hero_css().replace("conecta-achados-hero-auto-css", "moda-ofertas-hero-auto-css")


def build_hero(data: dict) -> list[str]:
    c = data.get("categories") or {}
    feminina = c["Moda Feminina"]
    masculina = c["Moda Masculina"]
    calcados = c["Calcados & Bolsas"]
    acessorios = c["Acessorios"]
    beleza = c["Beleza & Cuidados"]
    groups = [
        ("Moda feminina e masculina em destaque", [(feminina[0], "Moda Feminina"), (feminina[1], "Moda Feminina"), (masculina[0], "Moda Masculina"), (masculina[1], "Moda Masculina")]),
        ("Calçados, bolsas e acessórios para completar o look", [(calcados[0], "Calcados & Bolsas"), (calcados[2], "Calcados & Bolsas"), (acessorios[0], "Acessorios"), (acessorios[2], "Acessorios")]),
        ("Beleza e cuidados para a rotina", [(beleza[0], "Beleza & Cuidados"), (beleza[1], "Beleza & Cuidados"), (beleza[2], "Beleza & Cuidados"), (beleza[3], "Beleza & Cuidados")]),
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
    ("Achados práticos para casa, tecnologia, beleza e dia a dia", "Moda, beleza e ofertas para renovar o dia a dia"),
    ("Descubra produtos úteis para facilitar a rotina", "Encontre peças, acessórios e cuidados que combinam com você"),
    ("Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.", "Uma vitrine afiliada com moda feminina e masculina, calçados, bolsas, acessórios e beleza selecionados automaticamente na Shopee."),
    ("Cozinha e tecnologia", "Moda e acessórios"),
    ("Soluções práticas para cozinhar, conectar e organizar melhor", "Opções para vestir, combinar e completar o look"),
    ("A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.", "A seleção prioriza itens coerentes com moda, acessórios e beleza, bloqueando peças de reposição e falsos positivos."),
    ("Ver cozinha", "Ver moda feminina"),
    ("Ver tecnologia", "Ver acessórios"),
    ("Beleza e praticidade", "Beleza e cuidados"),
    ("Achados reais para cuidados pessoais e rotina", "Achados para cabelo, barbear e cuidados pessoais"),
    ("Ver beleza", "Ver beleza"),
    ("Ver dia a dia", "Ver moda masculina"),
    ("#bls-casa-organizacao", "#bls-moda-feminina"),
    ("#bls-cozinha-utilidades", "#bls-moda-masculina"),
    ("#bls-tecnologia", "#bls-calcados-bolsas"),
    ("#bls-beleza", "#bls-acessorios"),
    ("#bls-dia-a-dia", "#bls-beleza-cuidados"),
    ("Casa &amp; Organização", "Moda Feminina"),
    ("organização e soluções para o lar", "vestidos, conjuntos, saias e blusas"),
    ("Cozinha &amp; Utilidades", "Moda Masculina"),
    ("itens úteis para a cozinha", "camisetas, polos, bermudas e calças"),
    ("Tecnologia &amp; Acessórios", "Calçados &amp; Bolsas"),
    ("conectividade e eletrônicos úteis", "tênis, sandálias, bolsas e mochilas"),
    ('<a class="bls-cat" href="#bls-acessorios"><b>Beleza &amp; Cuidados</b><small>cuidados pessoais e beleza</small></a>', '<a class="bls-cat" href="#bls-acessorios"><b>Acessórios</b><small>carteiras, cintos, óculos e relógios</small></a>'),
    ("Dia a Dia &amp; Praticidade", "Beleza &amp; Cuidados"),
    ("produtos úteis para a rotina", "cabelo, barbear e cuidados pessoais"),
    ("Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia", "Vitrine de moda, acessórios e beleza com ofertas para o dia a dia"),
]


def transform_identity(raw: str) -> str:
    out = raw
    for old, new in IDENTITY_REPLACEMENTS:
        out = out.replace(old, new)

    # Normalizações idempotentes: preservam a categoria final de beleza e
    # mantêm texto/âncora dos CTAs do hero semanticamente alinhados.
    out = out.replace(
        '<article class="bls-panel" id="bls-beleza-cuidados"><div class="bls-panel-head"><span>Seleção da categoria</span><h3>Acessórios</h3>',
        '<article class="bls-panel" id="bls-beleza-cuidados"><div class="bls-panel-head"><span>Seleção da categoria</span><h3>Beleza &amp; Cuidados</h3>',
    )
    out = out.replace(
        '<a class="bls-btn bls-btn-main" href="#bls-moda-masculina">Ver moda feminina</a>',
        '<a class="bls-btn bls-btn-main" href="#bls-moda-feminina">Ver moda feminina</a>',
    )
    out = out.replace(
        '<a class="bls-btn bls-btn-soft" href="#bls-calcados-bolsas">Ver acessórios</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-acessorios">Ver acessórios</a>',
    )
    out = out.replace(
        '<a class="bls-btn bls-btn-main" href="#bls-acessorios">Ver beleza</a>',
        '<a class="bls-btn bls-btn-main" href="#bls-beleza-cuidados">Ver beleza</a>',
    )
    out = out.replace(
        '<a class="bls-btn bls-btn-soft" href="#bls-beleza-cuidados">Ver moda masculina</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-moda-masculina">Ver moda masculina</a>',
    )
    return out


def verify_identity(raw: str) -> None:
    required = [
        STORE_PAGE,
        "Moda, beleza e ofertas para renovar o dia a dia",
        "Encontre peças, acessórios e cuidados que combinam com você",
        "Moda Feminina",
        "Moda Masculina",
        "Calçados &amp; Bolsas",
        "Acessórios",
        "Beleza &amp; Cuidados",
        "#bls-moda-feminina",
        "#bls-moda-masculina",
        "#bls-calcados-bolsas",
        "#bls-acessorios",
        "#bls-beleza-cuidados",
        "blogger-liq-layout-wide-css",
    '<h3>Beleza &amp; Cuidados</h3>',
    'href="#bls-moda-feminina">Ver moda feminina</a>',
    'href="#bls-acessorios">Ver acessórios</a>',
    'href="#bls-beleza-cuidados">Ver beleza</a>',
    'href="#bls-moda-masculina">Ver moda masculina</a>',
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Moda e Ofertas incompleta: {missing}")
    forbidden = [
        "https://conectaachados.blogspot.com/p/loja.html",
        "https://achadosparacasa2026.blogspot.com/p/loja.html",
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        "https://liquidificadores-em-foco.blogspot.com/p/loja.html",
        "https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/p/loja.html",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência de outro blog detectada no Moda e Ofertas: {bad}")


def write_identity(dry_run: bool) -> int:
    service, post = base.get_service_post()
    raw = str(post.get("content") or "")
    new_raw = transform_identity(raw)
    verify_identity(new_raw)
    if dry_run:
        print("MODA_OFERTAS_IDENTITY_DRY_RUN_PASS: identidade validada em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_identity(str(verify.get("content") or ""))
    print("MODA_OFERTAS_IDENTITY_PASS: domínio, Page Loja, layout e nicho moda/beleza corretos.")
    return 0


def identity_check() -> int:
    _, post = base.get_service_post()
    verify_identity(str(post.get("content") or ""))
    print("MODA_OFERTAS_IDENTITY_PASS: domínio, Page Loja, layout e nicho moda/beleza corretos.")
    return 0


def safe_scan() -> int:
    rc = base.safe_scan()
    data = base.load_json(SELECTION_PATH, {})
    semantic = dict(data.get("semanticValidation") or {})
    semantic["rulesFile"] = "config/shopee_moda_ofertas_intent_rules.json"
    semantic["profileVersion"] = 1
    semantic["profileName"] = "Moda e Ofertas"
    semantic["shopeeSystemErrorRetries"] = SYSTEM_ERROR_RETRIES
    data["semanticValidation"] = semantic
    base.save_atomic(SELECTION_PATH, data)
    base.validate_selection(data)
    print("MODA_OFERTAS_SAFE_READY: 20 produtos; 20 intenções; histórico e seleção exclusivos; Blogger não alterado.")
    return rc


def validate_only() -> int:
    products = base.validate_selection(base.load_json(SELECTION_PATH, {}))
    print(f"MODA_OFERTAS_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def store_write(dry_run: bool) -> int:
    rc = base.write_store(dry_run)
    print("MODA_OFERTAS_STORE_DRY_RUN_PASS" if dry_run else f"MODA_OFERTAS_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return rc


def hero_write(dry_run: bool) -> int:
    rc = base.write_hero(dry_run)
    print("MODA_OFERTAS_HERO_DRY_RUN_PASS" if dry_run else "MODA_OFERTAS_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return rc


def persist() -> int:
    rc = base.persist_rotation()
    print("MODA_OFERTAS_ROTATION_PERSIST_PASS: seleção validada registrada após PASS público.")
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
        print(f"MODA_OFERTAS_STORE_FAILED: {exc}", file=sys.stderr)
        raise
