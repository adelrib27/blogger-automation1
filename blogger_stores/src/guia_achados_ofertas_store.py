#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "blogger_stores" / "data"
SCAN_DIR = DATA_DIR / "guia_achados_ofertas_scan"
HISTORY_PATH = DATA_DIR / "guia_achados_ofertas_rotation.json"
SELECTION_PATH = DATA_DIR / "guia_achados_ofertas_selection.json"
CONFIG_PATH = ROOT / "config" / "shopee_guia_achados_ofertas.json"
INTENT_RULES_PATH = ROOT / "config" / "shopee_guia_achados_ofertas_intent_rules.json"
EXPECTED_APP_ID = "18352820579"
BLOG_ID = "1453188702831337099"
POST_ID = "3858461075334539445"
STORE_PAGE = "https://guia-de-achados-e-ofertas.blogspot.com/p/loja.html"
STORE_POST_URL = "https://guia-de-achados-e-ofertas.blogspot.com/2026/11/loja.html"
RECENT_DAYS = max(1, min(int(os.getenv("GUIA_ACHADOS_OFERTAS_STORE_RECENT_DAYS", "14")), 90))

CATEGORY_META = {
    "Casa & Organizacao": ("Casa & Organização", "bls-casa-organizacao", "Casa"),
    "Cozinha & Eletroportateis": ("Cozinha & Eletroportáteis", "bls-cozinha-eletroportateis", "Cozinha"),
    "Iluminacao & Decoracao": ("Iluminação & Decoração", "bls-iluminacao-decoracao", "Iluminação"),
    "Clima & Conforto": ("Clima & Conforto", "bls-clima-conforto", "Clima"),
    "Utilidades & Rotina": ("Utilidades & Rotina", "bls-utilidades-rotina", "Utilidades"),
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
        "carrinho organizador": ["bebe", "brinquedo", "controle remoto", "hot wheels", "ferramenta", "oficina", "carrinho de mao", "para pet"],
        "caixa organizadora": ["caixa de som", "caixa amplificada", "caixa eletrica", "caixa de ferramenta", "automotivo", "cesto", "para pet", "cachorro", "gato"],
        "sapateira organizadora": ["infantil", "boneca", "miniatura", "para pet", "cachorro", "gato"],
        "estante organizadora banheiro": ["miniatura", "casa de boneca", "brinquedo", "automotivo", "para pet", "cachorro", "gato", "porta papel", "porta-papel"],
        "air fryer digital": ["cesto avulso", "cesto reposicao", "forma", "papel", "silicone", "grade", "grelha", "resistencia", "peca", "acessorio", "kit acessorios"],
        "cafeteira eletrica": ["jarra avulsa", "jarra reposicao", "jarra de reposicao", "filtro avulso", "filtro reposicao", "filtro de reposicao", "capsula", "suporte", "peca", "acessorio", "cafeteira italiana", "prensa francesa"],
        "mixer eletrico portatil": ["lamina avulsa", "copo avulso", "haste avulsa", "peca reposicao", "acessorio", "brinquedo", "miniatura", "processador", "picador", "moedor", "3l", "3 litros"],
        "balanca cozinha digital": ["bateria avulsa", "bandeja avulsa", "suporte", "peca reposicao", "brinquedo", "miniatura"],
        "luminaria mesa recarregavel": ["lampada avulsa", "cupula avulsa", "suporte", "peca", "miniatura", "brinquedo"],
        "abajur led toque": ["cupula avulsa", "lampada avulsa", "suporte", "peca", "brinquedo", "miniatura"],
        "luminaria led sensor movimento": ["sensor avulso", "lampada avulsa", "fita led", "suporte", "peca", "brinquedo", "miniatura"],
        "fita led usb": ["controlador avulso", "controle avulso", "conector", "fonte avulsa", "cabo avulso", "perfil aluminio", "suporte", "peca"],
        "ventilador parede": ["helice avulsa", "grade avulsa", "capacitor", "suporte avulso", "controle remoto avulso", "motor avulso", "peca", "miniatura", "brinquedo", "limpeza ventilador", "escova ventilador"],
        "ventilador mesa": ["helice avulsa", "grade avulsa", "capacitor", "suporte avulso", "controle remoto avulso", "motor avulso", "peca", "miniatura", "brinquedo", "limpeza ventilador", "escova ventilador"],
        "climatizador ar": ["filtro avulso", "filtro reposicao", "filtro de reposicao", "refil", "peca", "acessorio", "automotivo", "limpeza", "higienizador", "mini refrigerador", "mini ventilador", "usb", "ar condicionado"],
        "umidificador usb": ["filtro avulso", "refil", "cotonete", "pavio", "peca", "acessorio", "brinquedo", "miniatura"],
        "garrafa termica 500ml": ["tampa reposicao", "tampa avulsa", "vedacao", "borracha", "canudo avulso", "capa", "suporte"],
        "mochila notebook impermeavel": ["capa para mochila", "capa chuva", "capa de chuva", "alca avulsa", "bolsa termica", "miniatura", "brinquedo"],
        "aspirador po portatil": ["filtro avulso", "filtro reposicao", "bico avulso", "mangueira avulsa", "bateria avulsa", "carregador avulso", "peca", "acessorio", "brinquedo", "miniatura"],
        "mop spray limpeza": ["refil", "pano avulso", "pano reposicao", "cabo avulso", "reservatorio avulso", "peca", "miniatura", "brinquedo"],
    }
    if any(term in title for term in blocks.get(key, [])):
        return False

    positive = {
        "carrinho organizador": lambda: "carrinho" in title and any(x in title for x in ["organizador", "organizadora", "multiuso"]),
        "caixa organizadora": lambda: "caixa" in title and any(x in title for x in ["organizadora", "organizador"]),
        "sapateira organizadora": lambda: "sapateira" in title and any(x in title for x in ["organizadora", "organizador", "multiuso", "prateleira"]),
        "estante organizadora banheiro": lambda: any(x in title for x in ["estante", "prateleira"]) and "banheiro" in title and any(x in title for x in ["organiz", "multiuso", "prateleira"]),
        "air fryer digital": lambda: any(x in title for x in ["air fryer", "airfryer", "fritadeira sem oleo"]) and "digital" in title,
        "cafeteira eletrica": lambda: "cafeteira" in title and "eletrica" in title,
        "mixer eletrico portatil": lambda: "mixer" in title and "eletric" in title and any(x in title for x in ["portatil", "mao"]),
        "balanca cozinha digital": lambda: "balanca" in title and "cozinha" in title and "digital" in title,
        "luminaria mesa recarregavel": lambda: "luminaria" in title and "mesa" in title and any(x in title for x in ["recarregavel", "usb"]),
        "abajur led toque": lambda: "abajur" in title and "led" in title and any(x in title for x in ["toque", "touch"]),
        "luminaria led sensor movimento": lambda: "luminaria" in title and "led" in title and "sensor" in title and "movimento" in title,
        "fita led usb": lambda: "fita" in title and "led" in title and "usb" in title,
        "ventilador parede": lambda: any(x in title for x in ["ventilador de parede", "ventilador parede"]),
        "ventilador mesa": lambda: any(x in title for x in ["ventilador de mesa", "ventilador mesa"]),
        "climatizador ar": lambda: "climatizador" in title and "ar" in title,
        "umidificador usb": lambda: "umidificador" in title and "usb" in title,
        "garrafa termica 500ml": lambda: "garrafa" in title and "termica" in title and any(x in title for x in ["500ml", "500 ml", "0,5l", "0.5l"]),
        "mochila notebook impermeavel": lambda: "mochila" in title and any(x in title for x in ["notebook", "laptop"]) and any(x in title for x in ["impermeavel", "resistente a agua"]),
        "aspirador po portatil": lambda: "aspirador" in title and "po" in title and any(x in title for x in ["portatil", "mao"]),
        "mop spray limpeza": lambda: "mop" in title and "spray" in title and any(x in title for x in ["limpeza", "limpar", "piso"]),
    }
    return positive[key]() if key in positive else False


def run_guia_regression_checks(rules_doc: dict) -> None:
    cases = [
        ("Carrinho de Bebê Organizador", "carrinho organizador", False),
        ("Carrinho Organizador Multiuso 3 Andares", "carrinho organizador", True),
        ("Caixa de Som Organizadora Bluetooth", "caixa organizadora", False),
        ("Caixa Organizadora Transparente Multiuso", "caixa organizadora", True),
        ("Sapateira Miniatura Casa de Boneca", "sapateira organizadora", False),
        ("Sapateira Organizadora Multiuso 5 Prateleiras", "sapateira organizadora", True),
        ("Porta Papel com Prateleira para Banheiro", "estante organizadora banheiro", False),
        ("Estante Organizadora Multiuso para Banheiro", "estante organizadora banheiro", True),
        ("Forma de Silicone para Air Fryer Digital", "air fryer digital", False),
        ("Air Fryer Digital 5L Fritadeira Sem Óleo", "air fryer digital", True),
        ("Jarra de Reposição para Cafeteira Elétrica", "cafeteira eletrica", False),
        ("Cafeteira Elétrica 30 Xícaras 127V", "cafeteira eletrica", True),
        ("Processador Picador 3L Mixer Elétrico", "mixer eletrico portatil", False),
        ("Mixer Elétrico Portátil de Mão 2 em 1", "mixer eletrico portatil", True),
        ("Bandeja Avulsa para Balança", "balanca cozinha digital", False),
        ("Balança Digital de Cozinha 10kg", "balanca cozinha digital", True),
        ("Lâmpada Avulsa para Luminária de Mesa", "luminaria mesa recarregavel", False),
        ("Luminária de Mesa LED Recarregável USB", "luminaria mesa recarregavel", True),
        ("Cúpula Avulsa para Abajur LED Touch", "abajur led toque", False),
        ("Abajur LED Touch Toque Recarregável", "abajur led toque", True),
        ("Sensor Avulso de Movimento para Luminária LED", "luminaria led sensor movimento", False),
        ("Luminária LED com Sensor de Movimento", "luminaria led sensor movimento", True),
        ("Controlador Avulso para Fita LED USB", "fita led usb", False),
        ("Fita LED RGB USB 5 Metros", "fita led usb", True),
        ("Suporte De Parede Porta Controle Remoto Ar Ventilador", "ventilador parede", False),
        ("Ventilador de Parede Oscilante 60cm", "ventilador parede", True),
        ("Ventilador Mini Portátil USB de Mão Suporte Mesa", "ventilador mesa", False),
        ("Ventilador de Mesa 40cm 6 Pás", "ventilador mesa", True),
        ("MINI Refrigerador De Ar Ventilador Umidificador Climatizador Ar USB", "climatizador ar", False),
        ("Climatizador de Ar 16 Litros Frio", "climatizador ar", True),
        ("Refil Filtro para Umidificador USB", "umidificador usb", False),
        ("Mini Umidificador USB Portátil", "umidificador usb", True),
        ("Tampa Reposição Garrafa Térmica 500ml", "garrafa termica 500ml", False),
        ("Garrafa Térmica Inox 500ml", "garrafa termica 500ml", True),
        ("Capa de Chuva para Mochila Notebook", "mochila notebook impermeavel", False),
        ("Mochila para Notebook Impermeável Executiva", "mochila notebook impermeavel", True),
        ("Filtro Reposição Aspirador de Pó Portátil", "aspirador po portatil", False),
        ("Aspirador de Pó Portátil de Mão Recarregável", "aspirador po portatil", True),
        ("Refil Pano para Mop Spray Limpeza", "mop spray limpeza", False),
        ("Mop Spray para Limpeza de Piso com Reservatório", "mop spray limpeza", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        accepted = bool(shopee_v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        actual = accepted and final_keyword_gate({"productName": title}, keyword)
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha na regressão semântica Guia de Achados & Ofertas: " + json.dumps(failures, ensure_ascii=False))
    print(f"GUIA_ACHADOS_OFERTAS_SEMANTIC_REGRESSION_PASS: {len(cases)}/{len(cases)}")


base.final_keyword_gate = final_keyword_gate
base.run_conecta_regression_checks = run_guia_regression_checks

_orig_render_store = base.render_store
_orig_hero_css = base.hero_css


def render_store(data: dict) -> str:
    return _orig_render_store(data).replace("conecta-achados-store-auto-css", "guia-achados-ofertas-store-auto-css")


def hero_css() -> str:
    return _orig_hero_css().replace("conecta-achados-hero-auto-css", "guia-achados-ofertas-hero-auto-css")


def build_hero(data: dict) -> list[str]:
    c = data.get("categories") or {}
    casa = c["Casa & Organizacao"]
    cozinha = c["Cozinha & Eletroportateis"]
    iluminacao = c["Iluminacao & Decoracao"]
    clima = c["Clima & Conforto"]
    utilidades = c["Utilidades & Rotina"]
    groups = [
        ("Casa e cozinha para comparar melhor", [(casa[0], "Casa & Organizacao"), (casa[1], "Casa & Organizacao"), (cozinha[0], "Cozinha & Eletroportateis"), (cozinha[1], "Cozinha & Eletroportateis")]),
        ("Iluminação e conforto para o ambiente", [(iluminacao[0], "Iluminacao & Decoracao"), (iluminacao[1], "Iluminacao & Decoracao"), (clima[0], "Clima & Conforto"), (clima[1], "Clima & Conforto")]),
        ("Utilidades práticas para a rotina", [(utilidades[0], "Utilidades & Rotina"), (utilidades[1], "Utilidades & Rotina"), (utilidades[2], "Utilidades & Rotina"), (utilidades[3], "Utilidades & Rotina")]),
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
    ("Achados práticos para casa, tecnologia, beleza e dia a dia", "Guias de compra para casa, cozinha, conforto e rotina"),
    ("Descubra produtos úteis para facilitar a rotina", "Achados úteis para comparar antes de comprar"),
    ("Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.", "Uma vitrine afiliada com organização, eletroportáteis, iluminação, climatização e utilidades, selecionados na Shopee com filtros de intenção."),
    ("Cozinha e tecnologia", "Cozinha e iluminação"),
    ("Soluções práticas para cozinhar, conectar e organizar melhor", "Compare eletroportáteis e soluções de iluminação para a casa"),
    ("Ver tecnologia", "Ver iluminação"),
    ("Beleza e praticidade", "Clima e rotina"),
    ("Achados reais para cuidados pessoais e rotina", "Conforto e utilidades para o dia a dia"),
    ("Ver beleza", "Ver clima"),
    ("Ver dia a dia", "Ver utilidades"),
    ("#bls-cozinha-utilidades", "#bls-cozinha-eletroportateis"),
    ("#bls-tecnologia", "#bls-iluminacao-decoracao"),
    ("#bls-beleza", "#bls-clima-conforto"),
    ("#bls-dia-a-dia", "#bls-utilidades-rotina"),
    ("Cozinha &amp; Utilidades", "Cozinha &amp; Eletroportáteis"),
    ("itens úteis para a cozinha", "air fryers, cafeteiras, mixers e balanças"),
    ("Tecnologia &amp; Acessórios", "Iluminação &amp; Decoração"),
    ("conectividade e eletrônicos úteis", "luminárias, abajures e iluminação funcional"),
    ("Beleza &amp; Cuidados", "Clima &amp; Conforto"),
    ("cuidados pessoais e beleza", "ventiladores, climatizadores e umidificadores"),
    ("Dia a Dia &amp; Praticidade", "Utilidades &amp; Rotina"),
    ("produtos úteis para a rotina", "garrafas, mochilas, aspiradores e mops"),
    ("Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia", "Vitrine de achados e ofertas para casa, cozinha, conforto e rotina"),
]


def transform_identity(raw: str) -> str:
    out = raw
    for old, new in IDENTITY_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def verify_identity(raw: str) -> None:
    required = [
        STORE_PAGE,
        "Guias de compra para casa, cozinha, conforto e rotina",
        "Achados úteis para comparar antes de comprar",
        "Casa &amp; Organização",
        "Cozinha &amp; Eletroportáteis",
        "Iluminação &amp; Decoração",
        "Clima &amp; Conforto",
        "Utilidades &amp; Rotina",
        '#bls-casa-organizacao', '#bls-cozinha-eletroportateis', '#bls-iluminacao-decoracao', '#bls-clima-conforto', '#bls-utilidades-rotina',
        "blogger-liq-layout-wide-css",
        '<a class="bls-btn bls-btn-main" href="#bls-cozinha-eletroportateis">Ver cozinha</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-iluminacao-decoracao">Ver iluminação</a>',
        '<a class="bls-btn bls-btn-main" href="#bls-clima-conforto">Ver clima</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-utilidades-rotina">Ver utilidades</a>',
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Identidade Guia de Achados & Ofertas incompleta: {missing}")
    forbidden = [
        "https://conectaachados.blogspot.com/p/loja.html",
        "https://achadosparacasa2026.blogspot.com/p/loja.html",
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        "https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/p/loja.html",
        "https://casa-em-ordem-pratica.blogspot.com/p/loja.html",
        "https://escolha-certa-online.blogspot.com/p/loja.html",
        "https://achados-que-valem.blogspot.com/p/loja.html",
        "Tecnologia &amp; Acessórios",
        "Beleza &amp; Cuidados",
        "Dia a Dia &amp; Praticidade",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Referência/identidade indevida no Guia de Achados & Ofertas: {bad}")


def write_identity(dry_run: bool) -> int:
    service, post = base.get_service_post()
    raw = str(post.get("content") or "")
    new_raw = transform_identity(raw)
    verify_identity(new_raw)
    if dry_run:
        print("GUIA_ACHADOS_OFERTAS_IDENTITY_DRY_RUN_PASS: identidade validada em memória; Blogger não alterado.")
        return 0
    body = {"title": post.get("title") or "Loja", "content": new_raw}
    if post.get("labels") is not None:
        body["labels"] = post.get("labels")
    service.posts().update(blogId=BLOG_ID, postId=POST_ID, body=body).execute()
    verify = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    verify_identity(str(verify.get("content") or ""))
    print("GUIA_ACHADOS_OFERTAS_IDENTITY_PASS: domínio, Page Loja, layout e nicho editorial corretos.")
    return 0


def identity_check() -> int:
    _, post = base.get_service_post()
    verify_identity(str(post.get("content") or ""))
    print("GUIA_ACHADOS_OFERTAS_IDENTITY_PASS: domínio, Page Loja, layout e nicho editorial corretos.")
    return 0


def safe_scan() -> int:
    rc = base.safe_scan()
    data = base.load_json(SELECTION_PATH, {})
    semantic = dict(data.get("semanticValidation") or {})
    semantic["rulesFile"] = "config/shopee_guia_achados_ofertas_intent_rules.json"
    semantic["profileVersion"] = 2
    semantic["profileName"] = "Guia de Achados & Ofertas"
    data["semanticValidation"] = semantic
    base.save_atomic(SELECTION_PATH, data)
    base.validate_selection(data)
    print("GUIA_ACHADOS_OFERTAS_SAFE_READY: 20 produtos; 20 intenções; histórico e seleção exclusivos; Blogger não alterado.")
    return rc


def validate_only() -> int:
    products = base.validate_selection(base.load_json(SELECTION_PATH, {}))
    print(f"GUIA_ACHADOS_OFERTAS_SELECTION_VALID_PASS: {len(products)}/20 produtos; 5 categorias x 4 intenções.")
    return 0


def store_write(dry_run: bool) -> int:
    rc = base.write_store(dry_run)
    print("GUIA_ACHADOS_OFERTAS_STORE_DRY_RUN_PASS" if dry_run else f"GUIA_ACHADOS_OFERTAS_POST_PUBLISH_PASS: 20 produtos; alvo Blogger {POST_ID} verificado.")
    return rc


def hero_write(dry_run: bool) -> int:
    rc = base.write_hero(dry_run)
    print("GUIA_ACHADOS_OFERTAS_HERO_DRY_RUN_PASS" if dry_run else "GUIA_ACHADOS_OFERTAS_HERO_PASS: 12 mini-cards únicos sincronizados.")
    return rc


def persist() -> int:
    rc = base.persist_rotation()
    print("GUIA_ACHADOS_OFERTAS_ROTATION_PERSIST_PASS: seleção validada registrada após PASS público.")
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
        print(f"GUIA_ACHADOS_OFERTAS_STORE_FAILED: {exc}", file=sys.stderr)
        raise
