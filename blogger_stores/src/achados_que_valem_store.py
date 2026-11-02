#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "blogger_stores" / "data"
SCAN_DIR = DATA_DIR / "achados_que_valem_scan"
HISTORY_PATH = DATA_DIR / "achados_que_valem_rotation.json"
SELECTION_PATH = DATA_DIR / "achados_que_valem_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_achados_que_valem.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_achados_que_valem_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "7527651041649593600"
POST_ID = "953731363427123084"
STORE_PAGE = "https://achados-que-valem.blogspot.com/p/loja.html"
STORE_POST_URL = "https://achados-que-valem.blogspot.com/2026/11/loja.html"
RECENT_DAYS = max(1, min(int(os.getenv("ACHADOS_QUE_VALEM_STORE_RECENT_DAYS", "14")), 90))

CATEGORY_META = {
    "Casa & Organizacao": ("Casa & Organização", "bls-casa-organizacao", "Casa"),
    "Cozinha & Utilidades": ("Cozinha & Utilidades", "bls-cozinha-utilidades", "Cozinha"),
    "Ferramentas & Reparos": ("Ferramentas & Reparos", "bls-ferramentas", "Ferramentas"),
    "Tecnologia & Conectividade": ("Tecnologia & Conectividade", "bls-tecnologia-conectividade", "Tecnologia"),
    "Audio & Lazer": ("Áudio & Lazer", "bls-audio-lazer", "Áudio"),
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
        "parafusadeira impacto bateria": ["bateria avulsa", "carregador avulso", "broca avulsa", "adaptador avulso", "escova de carvao", "peca reposicao", "brinquedo", "miniatura"],
        "furadeira parafusadeira bateria": ["bateria avulsa", "carregador avulso", "broca avulsa", "mandril avulso", "adaptador", "peca reposicao", "brinquedo", "miniatura"],
        "kit ferramentas maleta": ["brinquedo", "infantil", "maquiagem", "manicure", "costura", "pintura artistica", "miniatura"],
        "jogo chaves catraca": ["brinquedo", "miniatura", "chaveiro"],
        "estante organizadora banheiro": ["miniatura", "boneca", "brinquedo", "automotivo", "para pet", "cachorro", "gato"],
        "caixa organizadora": ["caixa de som", "caixa amplificada", "caixa eletrica", "caixa de ferramenta", "automotivo", "cesto", "para pet", "cachorro", "gato"],
        "carrinho organizador": ["bebe", "brinquedo", "controle remoto", "hot wheels", "ferramenta", "oficina", "para pet"],
        "sapateira organizadora": ["infantil", "boneca", "miniatura", "para pet", "cachorro", "gato"],
        "escorredor loucas aco": ["peca", "reposicao", "miniatura", "brinquedo", "para pet"],
        "mixer eletrico": ["lamina avulsa", "copo avulso", "haste avulsa", "peca reposicao", "acessorio", "brinquedo", "miniatura"],
        "garrafa termica 500ml": ["tampa reposicao", "tampa avulsa", "vedacao", "borracha", "canudo avulso", "capa", "suporte"],
        "balanca cozinha digital": ["bateria avulsa", "bandeja avulsa", "suporte", "peca reposicao", "brinquedo", "miniatura"],
        "smartwatch chamadas bluetooth": ["pulseira avulsa", "pulseira para", "pelicula", "capa", "case", "carregador avulso", "cabo carregador"],
        "carregador usb c pd": ["cabo avulso", "somente cabo", "cabo usb", "case", "capa", "suporte", "adaptador de audio"],
        "fone bluetooth sem fio": ["cabo", "lightning", "p2", "com fio", "case", "capa", "estojo avulso", "almofada reposicao"],
        "hub usb c": ["cabo avulso", "case", "capa", "suporte", "placa avulsa", "conector avulso"],
        "caixa som bluetooth microfone": ["capa", "case", "suporte", "bateria avulsa", "placa reposicao", "miniatura", "brinquedo"],
        "microfone sem fio karaoke": ["cabo", "suporte", "espuma", "capa", "case", "receptor avulso", "placa reposicao", "brinquedo"],
        "mini projetor": ["suporte", "tela", "cabo", "controle remoto avulso", "lampada reposicao", "peca reposicao", "brinquedo"],
        "gamepad bluetooth": ["suporte", "capa", "case", "botao avulso", "analogico avulso", "peca reposicao"],
    }
    if any(term in title for term in blocks.get(key, [])):
        return False

    positive = {
        "parafusadeira impacto bateria": lambda: "parafusadeira" in title and "impacto" in title and "bateria" in title,
        "furadeira parafusadeira bateria": lambda: "furadeira" in title and "parafusadeira" in title and "bateria" in title,
        "kit ferramentas maleta": lambda: "kit" in title and "ferrament" in title and "maleta" in title and any(x in title for x in ["chave", "alicate", "soquete", "catraca"]),
        "jogo chaves catraca": lambda: any(x in title for x in ["jogo", "kit"]) and "chave" in title and "catraca" in title,
        "estante organizadora banheiro": lambda: any(x in title for x in ["estante", "prateleira"]) and "banheiro" in title and any(x in title for x in ["organiz", "multiuso", "prateleira"]),
        "caixa organizadora": lambda: "caixa" in title and any(x in title for x in ["organizadora", "organizador"]),
        "carrinho organizador": lambda: "carrinho" in title and any(x in title for x in ["organizador", "organizadora", "multiuso"]),
        "sapateira organizadora": lambda: "sapateira" in title and any(x in title for x in ["organizadora", "organizador", "multiuso", "prateleira"]),
        "escorredor loucas aco": lambda: "escorredor" in title and any(x in title for x in ["louca", "pratos"]) and any(x in title for x in ["aco", "inox", "carbono"]),
        "mixer eletrico": lambda: "mixer" in title and "eletric" in title,
        "garrafa termica 500ml": lambda: "garrafa" in title and "termica" in title and any(x in title for x in ["500ml", "500 ml", "0,5l", "0.5l"]),
        "balanca cozinha digital": lambda: "balanca" in title and "cozinha" in title and "digital" in title,
        "smartwatch chamadas bluetooth": lambda: any(x in title for x in ["smartwatch", "relogio inteligente"]) and "bluetooth" in title and any(x in title for x in ["chamada", "ligacao", "atender"]),
        "carregador usb c pd": lambda: any(x in title for x in ["carregador", "fonte"]) and any(x in title for x in ["usb-c", "usb c", "type-c", "type c"]) and any(x in title for x in [" pd", "pd ", "power delivery"]),
        "fone bluetooth sem fio": lambda: any(x in title for x in ["fone", "earbuds", "headset"]) and "bluetooth" in title and any(x in title for x in ["sem fio", "wireless", "tws"]),
        "hub usb c": lambda: "hub" in title and any(x in title for x in ["usb-c", "usb c", "type-c", "type c"]),
        "caixa som bluetooth microfone": lambda: any(x in title for x in ["caixa de som", "caixa som", "speaker"]) and "bluetooth" in title and "microfone" in title,
        "microfone sem fio karaoke": lambda: "microfone" in title and any(x in title for x in ["sem fio", "wireless"]),
        "mini projetor": lambda: "projetor" in title and any(x in title for x in ["mini", "portatil"]),
        "gamepad bluetooth": lambda: any(x in title for x in ["gamepad", "controle", "joystick"]) and "bluetooth" in title,
    }
    return positive[key]() if key in positive else False


def run_achados_que_valem_regression_checks(rules_doc: dict) -> None:
    cases = [
        ("Bateria Avulsa para Parafusadeira de Impacto", "parafusadeira impacto bateria", False),
        ("Parafusadeira de Impacto 48V com 2 Baterias", "parafusadeira impacto bateria", True),
        ("Mandril Avulso para Furadeira Parafusadeira", "furadeira parafusadeira bateria", False),
        ("Furadeira Parafusadeira 21V com Bateria", "furadeira parafusadeira bateria", True),
        ("Kit Ferramentas Infantil com Maleta", "kit ferramentas maleta", False),
        ("Kit Ferramentas com Maleta Chaves Alicate e Soquetes", "kit ferramentas maleta", True),
        ("Chaveiro Mini Catraca", "jogo chaves catraca", False),
        ("Jogo de Chaves e Soquetes com Catraca", "jogo chaves catraca", True),
        ("Estante Miniatura para Casa de Boneca", "estante organizadora banheiro", False),
        ("Estante Organizadora Multiuso para Banheiro", "estante organizadora banheiro", True),
        ("Caixa de Som Organizadora Bluetooth", "caixa organizadora", False),
        ("Caixa Organizadora Transparente Multiuso", "caixa organizadora", True),
        ("Carrinho de Bebê Organizador", "carrinho organizador", False),
        ("Carrinho Organizador Multiuso 3 Andares", "carrinho organizador", True),
        ("Sapateira Miniatura Casa de Boneca", "sapateira organizadora", False),
        ("Sapateira Organizadora Multiuso 5 Prateleiras", "sapateira organizadora", True),
        ("Peça de Reposição para Escorredor", "escorredor loucas aco", False),
        ("Escorredor de Louças em Aço Carbono 13 Pratos", "escorredor loucas aco", True),
        ("Lâmina Avulsa para Mixer Elétrico", "mixer eletrico", False),
        ("Mixer Elétrico Portátil 2 em 1", "mixer eletrico", True),
        ("Tampa Reposição Garrafa Térmica 500ml", "garrafa termica 500ml", False),
        ("Garrafa Térmica Inox 500ml", "garrafa termica 500ml", True),
        ("Bandeja Avulsa para Balança", "balanca cozinha digital", False),
        ("Balança Digital de Cozinha 10kg", "balanca cozinha digital", True),
        ("Pulseira para Smartwatch Bluetooth", "smartwatch chamadas bluetooth", False),
        ("Smartwatch Bluetooth com Chamadas e Atender Ligações", "smartwatch chamadas bluetooth", True),
        ("Cabo USB-C PD 100W Avulso", "carregador usb c pd", False),
        ("Carregador Fonte USB-C PD 35W", "carregador usb c pd", True),
        ("Fone Lightning com Fio", "fone bluetooth sem fio", False),
        ("Fone Bluetooth TWS Sem Fio", "fone bluetooth sem fio", True),
        ("Cabo Avulso para Hub USB-C", "hub usb c", False),
        ("Hub USB-C Type-C 7 em 1", "hub usb c", True),
        ("Capa para Caixa de Som Bluetooth", "caixa som bluetooth microfone", False),
        ("Caixa de Som Bluetooth com 2 Microfones", "caixa som bluetooth microfone", True),
        ("Suporte para Microfone Sem Fio", "microfone sem fio karaoke", False),
        ("Microfone Sem Fio Wireless para Karaoke", "microfone sem fio karaoke", True),
        ("Tela para Mini Projetor", "mini projetor", False),
        ("Mini Projetor Portátil Full HD", "mini projetor", True),
        ("Capa para Gamepad Bluetooth", "gamepad bluetooth", False),
        ("Gamepad Bluetooth Controle para Celular", "gamepad bluetooth", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        accepted = bool(shopee_v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        actual = accepted and final_keyword_gate({"productName": title}, keyword)
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha na regressão semântica Achados que Valem: " + json.dumps(failures, ensure_ascii=False))
    print(f"ACHADOS_QUE_VALEM_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


base.final_keyword_gate = final_keyword_gate
base.run_conecta_regression_checks = run_achados_que_valem_regression_checks

_orig_render_store = base.render_store
_orig_hero_css = base.hero_css


def render_store(data: dict) -> str:
    return _orig_render_store(data).replace("conecta-achados-store-auto-css", "achados-que-valem-store-auto-css")


def hero_css() -> str:
    return _orig_hero_css().replace("conecta-achados-hero-auto-css", "achados-que-valem-hero-auto-css")


def build_hero(data: dict) -> list[str]:
    c = data.get("categories") or {}
    casa = c["Casa & Organizacao"]
    cozinha = c["Cozinha & Utilidades"]
    ferramentas = c["Ferramentas & Reparos"]
    tecnologia = c["Tecnologia & Conectividade"]
    audio = c["Audio & Lazer"]
    groups = [
        ("Casa e cozinha que valem a comparação", [(casa[0], "Casa & Organizacao"), (casa[1], "Casa & Organizacao"), (cozinha[0], "Cozinha & Utilidades"), (cozinha[1], "Cozinha & Utilidades")]),
        ("Ferramentas e tecnologia para escolher melhor", [(ferramentas[0], "Ferramentas & Reparos"), (ferramentas[1], "Ferramentas & Reparos"), (tecnologia[0], "Tecnologia & Conectividade"), (tecnologia[1], "Tecnologia & Conectividade")]),
        ("Áudio e lazer com utilidade real", [(audio[0], "Audio & Lazer"), (audio[1], "Audio & Lazer"), (audio[2], "Audio & Lazer"), (audio[3], "Audio & Lazer")]),
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
    ("Achados práticos para casa, tecnologia, beleza e dia a dia", "Comparativos e achados para comprar melhor e gastar com mais critério"),
    ("Descubra produtos úteis para facilitar a rotina", "Produtos úteis que merecem entrar na comparação"),
    ("Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.", "Uma vitrine afiliada com casa, cozinha, ferramentas, tecnologia e lazer, selecionados automaticamente na Shopee com filtros de intenção."),
    ("Cozinha e tecnologia", "Cozinha e ferramentas"),
    ("Soluções práticas para cozinhar, conectar e organizar melhor", "Compare soluções práticas para equipar, reparar e organizar a rotina"),
    ("Ver tecnologia", "Ver ferramentas"),
    ("Beleza e praticidade", "Tecnologia e lazer"),
    ("Achados reais para cuidados pessoais e rotina", "Conectividade, áudio e entretenimento com utilidade real"),
    ("Ver beleza", "Ver tecnologia"),
    ("Ver dia a dia", "Ver áudio"),
    ("#bls-tecnologia", "#bls-ferramentas"),
    ("#bls-beleza", "#bls-tecnologia-conectividade"),
    ("#bls-dia-a-dia", "#bls-audio-lazer"),
    ("Tecnologia &amp; Acessórios", "Ferramentas &amp; Reparos"),
    ("conectividade e eletrônicos úteis", "parafusadeiras, kits e ferramentas para reparos"),
    ("Beleza &amp; Cuidados", "Tecnologia &amp; Conectividade"),
    ("cuidados pessoais e beleza", "smartwatches, carregadores, fones e hubs"),
    ("Dia a Dia &amp; Praticidade", "Áudio &amp; Lazer"),
    ("produtos úteis para a rotina", "caixas de som, microfones, projetores e controles"),
    ("Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia", "Vitrine de produtos que valem comparar para casa, ferramentas, tecnologia e lazer"),
]


def transform_identity(raw: str) -> str:
    out = raw
    for old, new in IDENTITY_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def verify_identity(raw: str) -> None:
    required = [
        STORE_PAGE,
        "Comparativos e achados para comprar melhor e gastar com mais critério",
        "Produtos úteis que merecem entrar na comparação",
        "Casa &amp; Organização",
        "Cozinha &amp; Utilidades",
        "Ferramentas &amp; Reparos",
        "Tecnologia &amp; Conectividade",
        "Áudio &amp; Lazer",
        '#bls-casa-organizacao', '#bls-cozinha-utilidades', '#bls-ferramentas', '#bls-tecnologia-conectividade', '#bls-audio-lazer',
        "blogger-liq-layout-wide-css",
        '<a class="bls-btn bls-btn-main" href="#bls-cozinha-utilidades">Ver cozinha</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-ferramentas">Ver ferramentas</a>',
        '<a class="bls-btn bls-btn-main" href="#bls-tecnologia-conectividade">Ver tecnologia</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-audio-lazer">Ver áudio</a>',
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Achados que Valem incompleta: {missing}")
    forbidden = [
        "https://conectaachados.blogspot.com/p/loja.html",
        "https://achadosparacasa2026.blogspot.com/p/loja.html",
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        "https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/p/loja.html",
        "https://casa-em-ordem-pratica.blogspot.com/p/loja.html",
        "https://escolha-certa-online.blogspot.com/p/loja.html",
        "Beleza &amp; Cuidados",
        "Dia a Dia &amp; Praticidade",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência/identidade indevida no Achados que Valem: {bad}")


def write_identity(dry_run: bool) -> int:
    service, post = base.get_service_post()
    raw = str(post.get("content") or "")
    new_raw = transform_identity(raw)
    verify_identity(new_raw)
    if dry_run:
        print("ACHADOS_QUE_VALEM_IDENTITY_DRY_RUN_PASS: identidade validada em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_identity(str(verify.get("content") or ""))
    print("ACHADOS_QUE_VALEM_IDENTITY_PASS: domínio, Page Loja, layout e nicho editorial correto.")
    return 0


def identity_check() -> int:
    _, post = base.get_service_post()
    verify_identity(str(post.get("content") or ""))
    print("ACHADOS_QUE_VALEM_IDENTITY_PASS: domínio, Page Loja, layout e nicho editorial correto.")
    return 0


def safe_scan() -> int:
    rc = base.safe_scan()
    data = base.load_json(SELECTION_PATH, {})
    semantic = dict(data.get("semanticValidation") or {})
    semantic["rulesFile"] = "config/shopee_achados_que_valem_intent_rules.json"
    semantic["profileVersion"] = 1
    semantic["profileName"] = "Achados que Valem"
    data["semanticValidation"] = semantic
    base.save_atomic(SELECTION_PATH, data)
    base.validate_selection(data)
    print("ACHADOS_QUE_VALEM_SAFE_READY: 20 produtos; 20 intenções; histórico e seleção exclusivos; Blogger não alterado.")
    return rc


def validate_only() -> int:
    products = base.validate_selection(base.load_json(SELECTION_PATH, {}))
    print(f"ACHADOS_QUE_VALEM_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def store_write(dry_run: bool) -> int:
    rc = base.write_store(dry_run)
    print("ACHADOS_QUE_VALEM_STORE_DRY_RUN_PASS" if dry_run else f"ACHADOS_QUE_VALEM_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return rc


def hero_write(dry_run: bool) -> int:
    rc = base.write_hero(dry_run)
    print("ACHADOS_QUE_VALEM_HERO_DRY_RUN_PASS" if dry_run else "ACHADOS_QUE_VALEM_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return rc


def persist() -> int:
    rc = base.persist_rotation()
    print("ACHADOS_QUE_VALEM_ROTATION_PERSIST_PASS: seleção validada registrada após PASS público.")
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
        print(f"ACHADOS_QUE_VALEM_STORE_FAILED: {exc}", file=sys.stderr)
        raise
