#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "blogger_stores" / "data"
SCAN_DIR = DATA_DIR / "casa_em_ordem_scan"
HISTORY_PATH = DATA_DIR / "casa_em_ordem_rotation.json"
SELECTION_PATH = DATA_DIR / "casa_em_ordem_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_casa_em_ordem.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_casa_em_ordem_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "4177382081459143374"
POST_ID = "5566188787681469799"
STORE_PAGE = "https://casa-em-ordem-pratica.blogspot.com/p/loja.html"
STORE_POST_URL = "https://casa-em-ordem-pratica.blogspot.com/2026/11/loja.html"
RECENT_DAYS = max(1, min(int(os.getenv("CASA_ORDEM_STORE_RECENT_DAYS", "14")), 90))

CATEGORY_META = {
    "Organizacao & Armazenamento": ("Organização & Armazenamento", "bls-organizacao", "Organização"),
    "Quarto & Roupa de Cama": ("Quarto & Roupa de Cama", "bls-quarto", "Quarto"),
    "Banheiro & Organizacao": ("Banheiro & Organização", "bls-banheiro", "Banheiro"),
    "Lavanderia & Limpeza": ("Lavanderia & Limpeza", "bls-lavanderia", "Lavanderia"),
    "Decoracao & Conforto": ("Decoração & Conforto", "bls-decoracao", "Decoração"),
}

# O módulo Shopee congela estes caminhos no import. Carregue o perfil Casa em Ordem
# antes do motor-base validado do Conecta.
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

# Estado/alvo isolados. Código compartilhado, dados nunca compartilhados.
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
        "caixa organizadora": ["caixa de som", "caixa amplificada", "caixa eletrica", "ferramenta", "automotivo", "pet", "cachorro", "gato"],
        "cesto organizador": ["bicicleta", "moto", "automotivo", "air fryer", "fritadeira", "pet", "cachorro", "gato"],
        "sapateira organizadora": ["infantil", "boneca", "miniatura", "pet", "cachorro", "gato"],
        "carrinho organizador": ["bebe", "brinquedo", "controle remoto", "hot wheels", "ferramenta", "oficina", "pet"],
        "protetor colchao impermeavel": ["pet", "cachorro", "gato", "sofa", "travesseiro"],
        "capa colchao elastico": ["pet", "cachorro", "gato", "sofa", "travesseiro"],
        "saco organizador edredom": ["alimento", "lixo", "entulho", "pet"],
        "colmeia organizadora guarda roupa": ["abelha", "apicultura", "mel", "pet"],
        "suporte shampoo sem furo": ["celular", "automotivo", "carro", "moto", "refil", "pet"],
        "prateleira banheiro sem furo": ["miniatura", "boneca", "pet"],
        "porta papel higienico": ["refil", "papel higienico avulso", "pet"],
        "tapete banheiro antiderrapante": ["automotivo", "carro", "para pet", "cachorro", "gato"],
        "varal de chao": ["miniatura", "brinquedo", "boneca", "pet"],
        "cesto roupa suja": ["bicicleta", "moto", "pet", "cachorro", "gato"],
        "mop spray": ["refil", "pano avulso", "cabo avulso", "peca", "brinquedo", "miniatura"],
        "rodo limpeza": ["automotivo", "carro", "para-brisa", "parabrisa", "refil", "borracha avulsa", "pet"],
        "cortina blackout": ["tecido por metro", "tecido metro", "amostra", "miniatura", "boneca", "pet"],
        "tapete sala": ["automotivo", "carro", "banheiro", "para pet", "cachorro", "gato", "miniatura"],
        "capa almofada decorativa": ["enchimento", "almofada completa", "pet", "cachorro", "gato"],
        "manta sofa": ["pet", "cachorro", "gato", "manta termica", "manta asfaltica"],
    }
    if any(term in title for term in blocks.get(key, [])):
        return False

    positive = {
        "caixa organizadora": lambda: "caixa" in title and any(x in title for x in ["organizadora", "organizador"]),
        "cesto organizador": lambda: "cesto" in title and any(x in title for x in ["organizador", "organizadora", "organizacao"]),
        "sapateira organizadora": lambda: "sapateira" in title and any(x in title for x in ["organizadora", "organizador", "multiuso", "prateleira"]),
        "carrinho organizador": lambda: "carrinho" in title and any(x in title for x in ["organizador", "organizadora", "multiuso"]),
        "protetor colchao impermeavel": lambda: "protetor" in title and "colchao" in title and "impermeavel" in title,
        "capa colchao elastico": lambda: "capa" in title and "colchao" in title and "elastico" in title,
        "saco organizador edredom": lambda: "saco" in title and any(x in title for x in ["organizador", "organizadora"]) and any(x in title for x in ["edredom", "cobertor", "roupa de cama"]),
        "colmeia organizadora guarda roupa": lambda: "colmeia" in title and any(x in title for x in ["organizadora", "organizador"]) and any(x in title for x in ["guarda roupa", "gaveta", "roupas"]),
        "suporte shampoo sem furo": lambda: "suporte" in title and any(x in title for x in ["shampoo", "xampu"]) and any(x in title for x in ["sem furo", "adesivo", "adesiva", "ventosa"]),
        "prateleira banheiro sem furo": lambda: "prateleira" in title and "banheiro" in title and any(x in title for x in ["sem furo", "adesiva", "adesivo", "ventosa"]),
        "porta papel higienico": lambda: "porta" in title and "papel higienico" in title,
        "tapete banheiro antiderrapante": lambda: "tapete" in title and "banheiro" in title and any(x in title for x in ["antiderrapante", "anti derrapante"]),
        "varal de chao": lambda: "varal" in title and "chao" in title,
        "cesto roupa suja": lambda: "cesto" in title and any(x in title for x in ["roupa suja", "roupas sujas", "lavanderia"]),
        "mop spray": lambda: "mop" in title and any(x in title for x in ["spray", "reservatorio"]),
        "rodo limpeza": lambda: "rodo" in title and any(x in title for x in ["limpeza", "limpar", "piso", "chao"]),
        "cortina blackout": lambda: "cortina" in title and any(x in title for x in ["blackout", "blecaute"]),
        "tapete sala": lambda: "tapete" in title and "sala" in title,
        "capa almofada decorativa": lambda: "capa" in title and "almofada" in title and any(x in title for x in ["decorativa", "decorativo", "decoracao"]),
        "manta sofa": lambda: "manta" in title and "sofa" in title,
    }
    return positive[key]() if key in positive else False


def run_casa_regression_checks(rules_doc: dict) -> None:
    cases = [
        ("Caixa de Som Organizadora Bluetooth", "caixa organizadora", False),
        ("Caixa Organizadora Transparente Multiuso", "caixa organizadora", True),
        ("Cesto para Bicicleta Organizador", "cesto organizador", False),
        ("Cesto Organizador Multiuso para Casa", "cesto organizador", True),
        ("Sapateira Miniatura Casa de Boneca", "sapateira organizadora", False),
        ("Sapateira Organizadora Multiuso 5 Prateleiras", "sapateira organizadora", True),
        ("Carrinho de Bebê Organizador", "carrinho organizador", False),
        ("Carrinho Organizador Multiuso 3 Andares", "carrinho organizador", True),
        ("Protetor Impermeável de Sofá", "protetor colchao impermeavel", False),
        ("Protetor de Colchão Impermeável Casal", "protetor colchao impermeavel", True),
        ("Capa de Sofá com Elástico", "capa colchao elastico", False),
        ("Capa para Colchão com Elástico Queen", "capa colchao elastico", True),
        ("Saco a Vácuo para Alimentos", "saco organizador edredom", False),
        ("Saco Organizador para Edredom e Cobertor", "saco organizador edredom", True),
        ("Colmeia para Abelhas Apicultura", "colmeia organizadora guarda roupa", False),
        ("Colmeia Organizadora para Guarda Roupa e Gaveta", "colmeia organizadora guarda roupa", True),
        ("Suporte Automotivo para Celular sem Furo", "suporte shampoo sem furo", False),
        ("Suporte para Shampoo Banheiro Sem Furo Adesivo", "suporte shampoo sem furo", True),
        ("Prateleira Miniatura de Banheiro", "prateleira banheiro sem furo", False),
        ("Prateleira Banheiro Sem Furo Adesiva", "prateleira banheiro sem furo", True),
        ("Papel Higiênico Refil 12 Rolos", "porta papel higienico", False),
        ("Porta Papel Higiênico de Parede", "porta papel higienico", True),
        ("Tapete Automotivo Antiderrapante", "tapete banheiro antiderrapante", False),
        ("Tapete Banheiro Antiderrapante Absorvente", "tapete banheiro antiderrapante", True),
        ("Varal Miniatura Casa de Boneca", "varal de chao", False),
        ("Varal de Chão Dobrável com Abas", "varal de chao", True),
        ("Cesto de Bicicleta para Roupas", "cesto roupa suja", False),
        ("Cesto Roupa Suja Dobrável para Lavanderia", "cesto roupa suja", True),
        ("Refil Pano para Mop Spray", "mop spray", False),
        ("Mop Spray com Reservatório para Limpeza", "mop spray", True),
        ("Rodo Automotivo para Para-brisa", "rodo limpeza", False),
        ("Rodo para Limpeza de Piso e Chão", "rodo limpeza", True),
        ("Tecido Blackout por Metro", "cortina blackout", False),
        ("Cortina Blackout para Quarto e Sala", "cortina blackout", True),
        ("Tapete Automotivo para Carro", "tapete sala", False),
        ("Tapete para Sala de Estar Felpudo", "tapete sala", True),
        ("Almofada Completa com Enchimento", "capa almofada decorativa", False),
        ("Capa de Almofada Decorativa para Sala", "capa almofada decorativa", True),
        ("Manta Térmica Asfáltica", "manta sofa", False),
        ("Manta para Sofá Decorativa Macia", "manta sofa", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        accepted = bool(shopee_v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        actual = accepted and final_keyword_gate({"productName": title}, keyword)
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha na regressão semântica Casa em Ordem: " + json.dumps(failures, ensure_ascii=False))
    print(f"CASA_ORDEM_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


base.final_keyword_gate = final_keyword_gate
base.run_conecta_regression_checks = run_casa_regression_checks

_orig_render_store = base.render_store
_orig_hero_css = base.hero_css


def render_store(data: dict) -> str:
    return _orig_render_store(data).replace("conecta-achados-store-auto-css", "casa-em-ordem-store-auto-css")


def hero_css() -> str:
    return _orig_hero_css().replace("conecta-achados-hero-auto-css", "casa-em-ordem-hero-auto-css")


def build_hero(data: dict) -> list[str]:
    c = data.get("categories") or {}
    organizacao = c["Organizacao & Armazenamento"]
    quarto = c["Quarto & Roupa de Cama"]
    banheiro = c["Banheiro & Organizacao"]
    lavanderia = c["Lavanderia & Limpeza"]
    decoracao = c["Decoracao & Conforto"]
    groups = [
        ("Organização e quarto em destaque", [(organizacao[0], "Organizacao & Armazenamento"), (organizacao[1], "Organizacao & Armazenamento"), (quarto[0], "Quarto & Roupa de Cama"), (quarto[1], "Quarto & Roupa de Cama")]),
        ("Banheiro e lavanderia para a rotina", [(banheiro[0], "Banheiro & Organizacao"), (banheiro[1], "Banheiro & Organizacao"), (lavanderia[0], "Lavanderia & Limpeza"), (lavanderia[1], "Lavanderia & Limpeza")]),
        ("Decoração e conforto para completar a casa", [(decoracao[0], "Decoracao & Conforto"), (decoracao[1], "Decoracao & Conforto"), (decoracao[2], "Decoracao & Conforto"), (decoracao[3], "Decoracao & Conforto")]),
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
    ("Achados práticos para casa, tecnologia, beleza e dia a dia", "Organização, limpeza e conforto para uma casa em ordem"),
    ("Descubra produtos úteis para facilitar a rotina", "Soluções práticas para organizar, cuidar e aproveitar melhor a casa"),
    ("Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.", "Uma vitrine afiliada com organização, roupa de cama, banheiro, lavanderia, limpeza e decoração selecionadas automaticamente na Shopee."),
    ("Cozinha e tecnologia", "Organização e quarto"),
    ("Soluções práticas para cozinhar, conectar e organizar melhor", "Organizadores e itens para manter cada espaço no lugar"),
    ("A seleção prioriza produtos completos e coerentes com cada categoria, bloqueando peças, refis e falsos positivos.", "A seleção prioriza produtos completos e coerentes com organização doméstica, bloqueando peças, refis e falsos positivos."),
    ("Ver cozinha", "Ver organização"),
    ("Ver tecnologia", "Ver quarto"),
    ("Beleza e praticidade", "Banheiro, lavanderia e conforto"),
    ("Achados reais para cuidados pessoais e rotina", "Achados para limpar, guardar e deixar a rotina mais prática"),
    ("Ver beleza", "Ver banheiro"),
    ("Ver dia a dia", "Ver lavanderia"),
    ("#bls-casa-organizacao", "#bls-organizacao"),
    ("#bls-cozinha-utilidades", "#bls-quarto"),
    ("#bls-tecnologia", "#bls-banheiro"),
    ("#bls-beleza", "#bls-lavanderia"),
    ("#bls-dia-a-dia", "#bls-decoracao"),
    ("Casa &amp; Organização", "Organização &amp; Armazenamento"),
    ("organização e soluções para o lar", "caixas, cestos, sapateiras e carrinhos"),
    ("Cozinha &amp; Utilidades", "Quarto &amp; Roupa de Cama"),
    ("itens úteis para a cozinha", "proteção do colchão e organização de roupas"),
    ("Tecnologia &amp; Acessórios", "Banheiro &amp; Organização"),
    ("conectividade e eletrônicos úteis", "suportes, prateleiras e itens para banheiro"),
    ("Beleza &amp; Cuidados", "Lavanderia &amp; Limpeza"),
    ("cuidados pessoais e beleza", "varais, cestos e ferramentas de limpeza"),
    ("Dia a Dia &amp; Praticidade", "Decoração &amp; Conforto"),
    ("produtos úteis para a rotina", "cortinas, tapetes, capas e mantas"),
    ("Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia", "Vitrine de organização, limpeza e conforto para a casa"),
]


def transform_identity(raw: str) -> str:
    out = raw
    for old, new in IDENTITY_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def verify_identity(raw: str) -> None:
    required = [
        STORE_PAGE,
        "Organização, limpeza e conforto para uma casa em ordem",
        "Soluções práticas para organizar, cuidar e aproveitar melhor a casa",
        "Organização &amp; Armazenamento",
        "Quarto &amp; Roupa de Cama",
        "Banheiro &amp; Organização",
        "Lavanderia &amp; Limpeza",
        "Decoração &amp; Conforto",
        '#bls-organizacao',
        '#bls-quarto',
        '#bls-banheiro',
        '#bls-lavanderia',
        '#bls-decoracao',
        "blogger-liq-layout-wide-css",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Casa em Ordem incompleta: {missing}")
    forbidden = [
        "https://conectaachados.blogspot.com/p/loja.html",
        "https://achadosparacasa2026.blogspot.com/p/loja.html",
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        "https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/p/loja.html",
        "Tecnologia &amp; Acessórios",
        "Beleza &amp; Cuidados",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência/identidade indevida detectada no Casa em Ordem: {bad}")


def write_identity(dry_run: bool) -> int:
    service, post = base.get_service_post()
    raw = str(post.get("content") or "")
    new_raw = transform_identity(raw)
    verify_identity(new_raw)
    if dry_run:
        print("CASA_ORDEM_IDENTITY_DRY_RUN_PASS: identidade validada em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_identity(str(verify.get("content") or ""))
    print("CASA_ORDEM_IDENTITY_PASS: domínio, Page Loja, layout e nicho casa/organização corretos.")
    return 0


def identity_check() -> int:
    _, post = base.get_service_post()
    verify_identity(str(post.get("content") or ""))
    print("CASA_ORDEM_IDENTITY_PASS: domínio, Page Loja, layout e nicho casa/organização corretos.")
    return 0


def safe_scan() -> int:
    rc = base.safe_scan()
    data = base.load_json(SELECTION_PATH, {})
    semantic = dict(data.get("semanticValidation") or {})
    semantic["rulesFile"] = "config/shopee_casa_em_ordem_intent_rules.json"
    semantic["profileVersion"] = 1
    semantic["profileName"] = "Casa em Ordem"
    data["semanticValidation"] = semantic
    base.save_atomic(SELECTION_PATH, data)
    base.validate_selection(data)
    print("CASA_ORDEM_SAFE_READY: 20 produtos; 20 intenções; histórico e seleção exclusivos; Blogger não alterado.")
    return rc


def validate_only() -> int:
    products = base.validate_selection(base.load_json(SELECTION_PATH, {}))
    print(f"CASA_ORDEM_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def store_write(dry_run: bool) -> int:
    rc = base.write_store(dry_run)
    print("CASA_ORDEM_STORE_DRY_RUN_PASS" if dry_run else f"CASA_ORDEM_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return rc


def hero_write(dry_run: bool) -> int:
    rc = base.write_hero(dry_run)
    print("CASA_ORDEM_HERO_DRY_RUN_PASS" if dry_run else "CASA_ORDEM_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return rc


def persist() -> int:
    rc = base.persist_rotation()
    print("CASA_ORDEM_ROTATION_PERSIST_PASS: seleção validada registrada após PASS público.")
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
        print(f"CASA_ORDEM_STORE_FAILED: {exc}", file=sys.stderr)
        raise
