#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "blogger_stores" / "data"
SCAN_DIR = DATA_DIR / "escolha_certa_online_scan"
HISTORY_PATH = DATA_DIR / "escolha_certa_online_rotation.json"
SELECTION_PATH = DATA_DIR / "escolha_certa_online_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_escolha_certa_online.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_escolha_certa_online_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "5151950717041967683"
POST_ID = "5474604520207119855"
STORE_PAGE = "https://escolha-certa-online.blogspot.com/p/loja.html"
STORE_POST_URL = "https://escolha-certa-online.blogspot.com/2026/11/loja.html"
RECENT_DAYS = max(1, min(int(os.getenv("ESCOLHA_CERTA_STORE_RECENT_DAYS", "14")), 90))

CATEGORY_META = {
    "Banheiro & Acessorios": ("Banheiro & Acessórios", "bls-banheiro", "Banheiro"),
    "Cama & Enxoval": ("Cama & Enxoval", "bls-cama", "Cama"),
    "Organizacao & Utilidades": ("Organização & Utilidades", "bls-organizacao", "Organização"),
    "Decoracao & Jardim": ("Decoração & Jardim", "bls-decoracao-jardim", "Decoração"),
    "Limpeza & Praticidade": ("Limpeza & Praticidade", "bls-limpeza", "Limpeza"),
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


def final_keyword_gate(product: dict, keyword: str) -> bool:
    title = base.norm(product.get("productName") or "")
    key = base.norm(keyword)
    blocks = {
        "kit banheiro 5 pecas": ["miniatura", "boneca", "brinquedo", "automotivo", "carro", "para pet", "cachorro", "gato"],
        "kit acessorios banheiro inox": ["miniatura", "boneca", "brinquedo", "automotivo", "carro", "para pet", "cachorro", "gato"],
        "tapete banheiro antiderrapante": ["automotivo", "carro", "para pet", "cachorro", "gato"],
        "prateleira banheiro sem furo": ["miniatura", "boneca", "porta papel", "papel higienico", "suporte shampoo", "para pet"],
        "lencol 400 fios": ["fronha avulsa", "capa de almofada", "tecido por metro", "para pet", "cachorro", "gato"],
        "jogo cama casal": ["berco", "infantil", "solteiro", "para pet", "cachorro", "gato"],
        "protetor colchao impermeavel": ["sofa", "travesseiro", "para pet", "cachorro", "gato"],
        "colcha cobre leito": ["miniatura", "boneca", "tecido por metro", "para pet", "cachorro", "gato"],
        "caixa organizadora": ["caixa de som", "caixa amplificada", "caixa eletrica", "ferramenta", "automotivo", "cesto", "para pet", "cachorro", "gato"],
        "cesto organizador": ["bicicleta", "moto", "automotivo", "air fryer", "fritadeira", "para pet", "cachorro", "gato"],
        "sapateira organizadora": ["infantil", "boneca", "miniatura", "para pet", "cachorro", "gato"],
        "carrinho organizador": ["bebe", "brinquedo", "controle remoto", "hot wheels", "ferramenta", "oficina", "para pet"],
        "suporte madeira vaso": ["celular", "monitor", "notebook", "automotivo", "carro", "miniatura", "boneca", "para pet"],
        "vaso decorativo plantas": ["vaso sanitario", "miniatura", "boneca", "para pet"],
        "pedra decorativa jardim": ["joia", "anel", "colar", "pulseira", "aquario", "para pet"],
        "cachepo decorativo": ["miniatura", "boneca", "para pet", "cachorro", "gato"],
        "mop spray": ["refil", "pano avulso", "cabo avulso", "peca", "brinquedo", "miniatura"],
        "rodo limpeza": ["automotivo", "carro", "para-brisa", "parabrisa", "refil", "borracha avulsa", "para pet"],
        "escova limpeza banheiro": ["cabelo", "dente", "dental", "facial", "maquiagem", "para pet", "cachorro", "gato"],
        "varal de chao": ["miniatura", "brinquedo", "boneca", "para pet"],
    }
    if any(term in title for term in blocks.get(key, [])):
        return False

    positive = {
        "kit banheiro 5 pecas": lambda: "kit" in title and "banheiro" in title and any(x in title for x in ["5 pecas", "5pcs", "5 pcs", "cinco pecas"]),
        "kit acessorios banheiro inox": lambda: "kit" in title and "banheiro" in title and "inox" in title and any(x in title for x in ["acessorio", "acessorios"]),
        "tapete banheiro antiderrapante": lambda: "tapete" in title and "banheiro" in title and any(x in title for x in ["antiderrapante", "anti derrapante"]),
        "prateleira banheiro sem furo": lambda: "prateleira" in title and "banheiro" in title and any(x in title for x in ["sem furo", "adesiva", "adesivo", "ventosa"]),
        "lencol 400 fios": lambda: "lencol" in title and any(x in title for x in ["400 fios", "400fios"]),
        "jogo cama casal": lambda: any(x in title for x in ["jogo de cama", "jogo cama"]) and "casal" in title,
        "protetor colchao impermeavel": lambda: "protetor" in title and "colchao" in title and "impermeavel" in title,
        "colcha cobre leito": lambda: any(x in title for x in ["colcha", "cobre leito", "cobre-leito"]),
        "caixa organizadora": lambda: "caixa" in title and any(x in title for x in ["organizadora", "organizador"]),
        "cesto organizador": lambda: "cesto" in title and any(x in title for x in ["organizador", "organizadora", "organizacao"]),
        "sapateira organizadora": lambda: "sapateira" in title and any(x in title for x in ["organizadora", "organizador", "multiuso", "prateleira"]),
        "carrinho organizador": lambda: "carrinho" in title and any(x in title for x in ["organizador", "organizadora", "multiuso"]),
        "suporte madeira vaso": lambda: "suporte" in title and "madeira" in title and "vaso" in title,
        "vaso decorativo plantas": lambda: "vaso" in title and any(x in title for x in ["decorativo", "decorativa", "decoracao"]) and any(x in title for x in ["planta", "plantas", "flor", "flores"]),
        "pedra decorativa jardim": lambda: "pedra" in title and "jardim" in title and any(x in title for x in ["decorativa", "decorativas", "dolomita", "seixo", "branca", "brancas"]),
        "cachepo decorativo": lambda: "cachepo" in title and any(x in title for x in ["decorativo", "decorativa", "decoracao"]),
        "mop spray": lambda: "mop" in title and any(x in title for x in ["spray", "reservatorio"]),
        "rodo limpeza": lambda: "rodo" in title and any(x in title for x in ["limpeza", "limpar", "piso", "chao"]),
        "escova limpeza banheiro": lambda: "escova" in title and any(x in title for x in ["limpeza", "limpar"]) and any(x in title for x in ["banheiro", "box", "rejunte"]),
        "varal de chao": lambda: "varal" in title and "chao" in title,
    }
    return positive[key]() if key in positive else False


def run_escolha_regression_checks(rules_doc: dict) -> None:
    cases = [
        ("Kit Banheiro Miniatura 5 Peças Casa de Boneca", "kit banheiro 5 pecas", False),
        ("Kit Banheiro 5 Peças Completo", "kit banheiro 5 pecas", True),
        ("Kit Acessórios Automotivos Inox", "kit acessorios banheiro inox", False),
        ("Kit Acessórios Banheiro Inox 6 Peças", "kit acessorios banheiro inox", True),
        ("Tapete Automotivo Antiderrapante", "tapete banheiro antiderrapante", False),
        ("Tapete Banheiro Antiderrapante Absorvente", "tapete banheiro antiderrapante", True),
        ("Prateleira Porta Papel Banheiro", "prateleira banheiro sem furo", False),
        ("Prateleira Banheiro Sem Furo Adesiva", "prateleira banheiro sem furo", True),
        ("Fronha Avulsa 400 Fios", "lencol 400 fios", False),
        ("Lençol 400 Fios Casal Queen", "lencol 400 fios", True),
        ("Jogo Cama Solteiro 3 Peças", "jogo cama casal", False),
        ("Jogo de Cama Casal 4 Peças", "jogo cama casal", True),
        ("Protetor Impermeável de Sofá", "protetor colchao impermeavel", False),
        ("Protetor de Colchão Impermeável Casal", "protetor colchao impermeavel", True),
        ("Colcha Miniatura Casa de Boneca", "colcha cobre leito", False),
        ("Colcha Cobre Leito Casal Matelada", "colcha cobre leito", True),
        ("Caixa de Som Organizadora Bluetooth", "caixa organizadora", False),
        ("Caixa Organizadora Transparente Multiuso", "caixa organizadora", True),
        ("Cesto de Bicicleta Organizador", "cesto organizador", False),
        ("Cesto Organizador Multiuso para Casa", "cesto organizador", True),
        ("Sapateira Miniatura Casa de Boneca", "sapateira organizadora", False),
        ("Sapateira Organizadora Multiuso 5 Prateleiras", "sapateira organizadora", True),
        ("Carrinho de Bebê Organizador", "carrinho organizador", False),
        ("Carrinho Organizador Multiuso 3 Andares", "carrinho organizador", True),
        ("Suporte Madeira para Celular e Vaso", "suporte madeira vaso", False),
        ("Suporte de Madeira para Vaso de Plantas", "suporte madeira vaso", True),
        ("Vaso Sanitário Decorativo", "vaso decorativo plantas", False),
        ("Vaso Decorativo para Plantas e Flores", "vaso decorativo plantas", True),
        ("Pedra para Aquário Branca", "pedra decorativa jardim", False),
        ("Pedra Dolomita Branca Decorativa para Jardim", "pedra decorativa jardim", True),
        ("Cachepô Miniatura Casa de Boneca", "cachepo decorativo", False),
        ("Cachepô Decorativo para Sala e Jardim", "cachepo decorativo", True),
        ("Refil Pano para Mop Spray", "mop spray", False),
        ("Mop Spray com Reservatório para Limpeza", "mop spray", True),
        ("Rodo Automotivo para Para-brisa", "rodo limpeza", False),
        ("Rodo para Limpeza de Piso e Chão", "rodo limpeza", True),
        ("Escova Facial para Maquiagem", "escova limpeza banheiro", False),
        ("Escova para Limpeza de Banheiro Box e Rejunte", "escova limpeza banheiro", True),
        ("Varal Miniatura Casa de Boneca", "varal de chao", False),
        ("Varal de Chão Dobrável com Abas", "varal de chao", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        accepted = bool(shopee_v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        actual = accepted and final_keyword_gate({"productName": title}, keyword)
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha na regressão semântica Escolha Certa Online: " + json.dumps(failures, ensure_ascii=False))
    print(f"ESCOLHA_CERTA_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


base.final_keyword_gate = final_keyword_gate
base.run_conecta_regression_checks = run_escolha_regression_checks

_orig_render_store = base.render_store
_orig_hero_css = base.hero_css


def render_store(data: dict) -> str:
    return _orig_render_store(data).replace("conecta-achados-store-auto-css", "escolha-certa-online-store-auto-css")


def hero_css() -> str:
    return _orig_hero_css().replace("conecta-achados-hero-auto-css", "escolha-certa-online-hero-auto-css")


def build_hero(data: dict) -> list[str]:
    c = data.get("categories") or {}
    banheiro = c["Banheiro & Acessorios"]
    cama = c["Cama & Enxoval"]
    organizacao = c["Organizacao & Utilidades"]
    decoracao = c["Decoracao & Jardim"]
    limpeza = c["Limpeza & Praticidade"]
    groups = [
        ("Banheiro e cama em destaque", [(banheiro[0], "Banheiro & Acessorios"), (banheiro[1], "Banheiro & Acessorios"), (cama[0], "Cama & Enxoval"), (cama[1], "Cama & Enxoval")]),
        ("Organização e limpeza para a rotina", [(organizacao[0], "Organizacao & Utilidades"), (organizacao[1], "Organizacao & Utilidades"), (limpeza[0], "Limpeza & Praticidade"), (limpeza[1], "Limpeza & Praticidade")]),
        ("Decoração e jardim para escolher melhor", [(decoracao[0], "Decoracao & Jardim"), (decoracao[1], "Decoracao & Jardim"), (decoracao[2], "Decoracao & Jardim"), (decoracao[3], "Decoracao & Jardim")]),
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
    ("Achados práticos para casa, tecnologia, beleza e dia a dia", "Comparativos e achados para escolher melhor para a casa"),
    ("Descubra produtos úteis para facilitar a rotina", "Escolhas mais informadas para banheiro, cama, organização e decoração"),
    ("Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.", "Uma vitrine afiliada com produtos para banheiro, cama e enxoval, organização, decoração, jardim e limpeza, selecionados automaticamente na Shopee."),
    ("Cozinha e tecnologia", "Organização e limpeza"),
    ("Soluções práticas para cozinhar, conectar e organizar melhor", "Organize e cuide da casa com escolhas funcionais"),
    ("A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.", "A seleção prioriza produtos completos e coerentes com o uso doméstico, bloqueando peças, refis e falsos positivos."),
    ("Ver cozinha", "Ver organização"),
    ("Ver tecnologia", "Ver limpeza"),
    ("Beleza e praticidade", "Banheiro, cama e decoração"),
    ("Achados reais para cuidados pessoais e rotina", "Compare detalhes que mudam conforto, acabamento e uso"),
    ("Ver beleza", "Ver banheiro"),
    ("Ver dia a dia", "Ver decoração"),
    ("#bls-casa-organizacao", "#bls-banheiro"),
    ("#bls-cozinha-utilidades", "#bls-cama"),
    ("#bls-tecnologia", "#bls-organizacao"),
    ("#bls-beleza", "#bls-decoracao-jardim"),
    ("#bls-dia-a-dia", "#bls-limpeza"),
    ("Casa &amp; Organização", "Banheiro &amp; Acessórios"),
    ("organização e soluções para o lar", "kits, tapetes e acessórios funcionais"),
    ("Cozinha &amp; Utilidades", "Cama &amp; Enxoval"),
    ("itens úteis para a cozinha", "lençóis, jogos de cama e proteção do colchão"),
    ("Tecnologia &amp; Acessórios", "Organização &amp; Utilidades"),
    ("conectividade e eletrônicos úteis", "caixas, cestos, sapateiras e carrinhos"),
    ("Beleza &amp; Cuidados", "Decoração &amp; Jardim"),
    ("cuidados pessoais e beleza", "vasos, suportes, pedras e cachepôs"),
    ("Dia a Dia &amp; Praticidade", "Limpeza &amp; Praticidade"),
    ("produtos úteis para a rotina", "mops, rodos, escovas e varais"),
    ("Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia", "Vitrine de escolhas para banheiro, cama, organização, decoração e limpeza"),
]

NAV_REPLACEMENTS = [
    ('<a class="bls-btn bls-btn-main" href="#bls-cama">Ver organização</a>', '<a class="bls-btn bls-btn-main" href="#bls-organizacao">Ver organização</a>'),
    ('<a class="bls-btn bls-btn-soft" href="#bls-organizacao">Ver limpeza</a>', '<a class="bls-btn bls-btn-soft" href="#bls-limpeza">Ver limpeza</a>'),
    ('<a class="bls-btn bls-btn-main" href="#bls-decoracao-jardim">Ver banheiro</a>', '<a class="bls-btn bls-btn-main" href="#bls-banheiro">Ver banheiro</a>'),
    ('<a class="bls-btn bls-btn-soft" href="#bls-limpeza">Ver decoração</a>', '<a class="bls-btn bls-btn-soft" href="#bls-decoracao-jardim">Ver decoração</a>'),
]


def transform_identity(raw: str) -> str:
    out = raw
    for old, new in IDENTITY_REPLACEMENTS:
        out = out.replace(old, new)
    for old, new in NAV_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def verify_identity(raw: str) -> None:
    required = [
        STORE_PAGE,
        "Comparativos e achados para escolher melhor para a casa",
        "Escolhas mais informadas para banheiro, cama, organização e decoração",
        "Banheiro &amp; Acessórios",
        "Cama &amp; Enxoval",
        "Organização &amp; Utilidades",
        "Decoração &amp; Jardim",
        "Limpeza &amp; Praticidade",
        '#bls-banheiro', '#bls-cama', '#bls-organizacao', '#bls-decoracao-jardim', '#bls-limpeza',
        "blogger-liq-layout-wide-css",
        '<a class="bls-btn bls-btn-main" href="#bls-organizacao">Ver organização</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-limpeza">Ver limpeza</a>',
        '<a class="bls-btn bls-btn-main" href="#bls-banheiro">Ver banheiro</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-decoracao-jardim">Ver decoração</a>',
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Escolha Certa Online incompleta: {missing}")
    forbidden = [
        "https://conectaachados.blogspot.com/p/loja.html",
        "https://achadosparacasa2026.blogspot.com/p/loja.html",
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        "https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/p/loja.html",
        "https://casa-em-ordem-pratica.blogspot.com/p/loja.html",
        "Tecnologia &amp; Acessórios",
        "Beleza &amp; Cuidados",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência/identidade indevida no Escolha Certa Online: {bad}")


def write_identity(dry_run: bool) -> int:
    service, post = base.get_service_post()
    raw = str(post.get("content") or "")
    new_raw = transform_identity(raw)
    verify_identity(new_raw)
    if dry_run:
        print("ESCOLHA_CERTA_IDENTITY_DRY_RUN_PASS: identidade validada em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_identity(str(verify.get("content") or ""))
    print("ESCOLHA_CERTA_IDENTITY_PASS: domínio, Page Loja, layout e nicho editorial correto.")
    return 0


def identity_check() -> int:
    _, post = base.get_service_post()
    verify_identity(str(post.get("content") or ""))
    print("ESCOLHA_CERTA_IDENTITY_PASS: domínio, Page Loja, layout e nicho editorial correto.")
    return 0


def safe_scan() -> int:
    rc = base.safe_scan()
    data = base.load_json(SELECTION_PATH, {})
    semantic = dict(data.get("semanticValidation") or {})
    semantic["rulesFile"] = "config/shopee_escolha_certa_online_intent_rules.json"
    semantic["profileVersion"] = 1
    semantic["profileName"] = "Escolha Certa Online"
    data["semanticValidation"] = semantic
    base.save_atomic(SELECTION_PATH, data)
    base.validate_selection(data)
    print("ESCOLHA_CERTA_SAFE_READY: 20 produtos; 20 intenções; histórico e seleção exclusivos; Blogger não alterado.")
    return rc


def validate_only() -> int:
    products = base.validate_selection(base.load_json(SELECTION_PATH, {}))
    print(f"ESCOLHA_CERTA_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def store_write(dry_run: bool) -> int:
    rc = base.write_store(dry_run)
    print("ESCOLHA_CERTA_STORE_DRY_RUN_PASS" if dry_run else f"ESCOLHA_CERTA_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return rc


def hero_write(dry_run: bool) -> int:
    rc = base.write_hero(dry_run)
    print("ESCOLHA_CERTA_HERO_DRY_RUN_PASS" if dry_run else "ESCOLHA_CERTA_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return rc


def persist() -> int:
    rc = base.persist_rotation()
    print("ESCOLHA_CERTA_ROTATION_PERSIST_PASS: seleção validada registrada após PASS público.")
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
        print(f"ESCOLHA_CERTA_STORE_FAILED: {exc}", file=sys.stderr)
        raise
