#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SAFE_WORKFLOWS = [
    ".github/workflows/air_fryers_store_safe.yml",
    ".github/workflows/cabelos_store_safe.yml",
    ".github/workflows/blogger_liquidificador_store_safe.yml",
    ".github/workflows/eletroportateis_store_safe.yml",
    ".github/workflows/limpeza_inteligente_store_safe.yml",
    ".github/workflows/ventiladores_store_safe.yml",
    ".github/workflows/vitrine_pratica_store_safe.yml",
    ".github/workflows/achados_casa_store_safe.yml",
    ".github/workflows/conecta_achados_store_safe.yml",
    ".github/workflows/estilo_dia_a_dia_store_safe.yml",
    ".github/workflows/casa_em_ordem_store_safe.yml",
    ".github/workflows/escolha_certa_online_store_safe.yml",
    ".github/workflows/achados_que_valem_store_safe.yml",
    ".github/workflows/guia_achados_ofertas_store_safe.yml",
    ".github/workflows/moda_ofertas_store_safe.yml",
    ".github/workflows/achadinhos_beleza_store_safe.yml",
    ".github/workflows/radar_tech_blogger_store_safe.yml",
    ".github/workflows/cozinha_sem_complicacao_store_safe.yml",
]
LIVE_WORKFLOWS = [
    ".github/workflows/air_fryers_store_autonomous.yml",
    ".github/workflows/cabelos_store_autonomous.yml",
    ".github/workflows/blogger_liquidificador_store_autonomous.yml",
    ".github/workflows/eletroportateis_store_autonomous.yml",
    ".github/workflows/limpeza_inteligente_store_autonomous.yml",
    ".github/workflows/ventiladores_store_autonomous.yml",
    ".github/workflows/vitrine_pratica_store_autonomous.yml",
    ".github/workflows/achados_casa_store_autonomous.yml",
    ".github/workflows/conecta_achados_store_autonomous.yml",
    ".github/workflows/estilo_dia_a_dia_store_autonomous.yml",
    ".github/workflows/casa_em_ordem_store_autonomous.yml",
    ".github/workflows/escolha_certa_online_store_autonomous.yml",
    ".github/workflows/achados_que_valem_store_autonomous.yml",
    ".github/workflows/guia_achados_ofertas_store_autonomous.yml",
    ".github/workflows/moda_ofertas_store_autonomous.yml",
    ".github/workflows/achadinhos_beleza_store_autonomous.yml",
    ".github/workflows/radar_tech_blogger_store_autonomous.yml",
    ".github/workflows/cozinha_sem_complicacao_store_autonomous.yml",
]

LEGACY_MANUAL_WORKFLOWS = {
    ".github/workflows/limpeza_store_autonomous.yml": "limpeza-inteligente-store-live",
    ".github/workflows/ventiladores_em_foco_store_autonomous.yml": "ventiladores-store-live",
}

SCAN_ROOTS = [
    "blogger_themes",
    "blogger_store_clone",
    "air_fryers_store/src",
    "cabelos_store/src",
    "blogger_product_store/src",
    "eletroportateis_store/src",
    "limpeza_inteligente_store/src",
    "limpeza_store/src",
    "ventiladores_store/src",
    "ventiladores_em_foco_store/src",
    "vitrine_pratica_store/src",
    "blogger_stores/src",
]

LEGACY_DOMAINS = [
    "ventilador-mondial-vsp-40-b.blogspot.com",
    "liquidificador-philips-walita-ri2242.blogspot.com",
]

TEXT_SUFFIXES = {".py", ".js", ".html", ".htm", ".xml", ".css", ".yml", ".yaml", ".json", ".md", ".txt"}


def fail(msg: str) -> None:
    raise SystemExit("BLOGGER_POLICY_REPO_AUDIT_FAIL: " + msg)


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        fail(f"arquivo obrigatório ausente: {rel}")
    return p.read_text(encoding="utf-8", errors="ignore")


def audit_workflows() -> None:
    for rel in SAFE_WORKFLOWS:
        text = read(rel)
        required = ["blogger_policy_guard.py", "blogger_policy_guard_self_test.py", "require_product_allowed", "20/20"]
        missing = [x for x in required if x not in text]
        if missing:
            fail(f"SAFE sem Policy Guard completo: {rel}: {missing}")

    for rel in LIVE_WORKFLOWS:
        text = read(rel)
        required = [
            "blogger_policy_guard.py",
            "require_product_allowed",
            "require_store_html_allowed",
            "BLOGGER_POLICY_GUARD_PUBLIC_PASS",
            "expected_products=20",
            "expected_hero=12",
        ]
        missing = [x for x in required if x not in text]
        if missing:
            fail(f"LIVE sem Policy Guard público completo: {rel}: {missing}")


def audit_casa_schedule() -> None:
    rel = ".github/workflows/casa_em_ordem_store_autonomous.yml"
    text = read(rel)
    required = [
        'cron: "5 8 * * *"', 'timezone: "America/Recife"',
        "SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02",
        '<a class="bls-btn bls-btn-main" href="#bls-organizacao">Ver organização</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-quarto">Ver quarto</a>',
        '<a class="bls-btn bls-btn-main" href="#bls-banheiro">Ver banheiro</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-lavanderia">Ver lavanderia</a>',
    ]
    missing = [x for x in required if x not in text]
    if missing:
        fail(f"Casa em Ordem sem schedule/gate de navegação canônico: {missing}")


def audit_escolha_schedule() -> None:
    rel = ".github/workflows/escolha_certa_online_store_autonomous.yml"
    text = read(rel)
    required = [
        "workflow_dispatch:", 'cron: "20 8 * * *"', 'timezone: "America/Recife"',
        "SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02",
        '<a class="bls-btn bls-btn-main" href="#bls-organizacao">Ver organização</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-limpeza">Ver limpeza</a>',
        '<a class="bls-btn bls-btn-main" href="#bls-banheiro">Ver banheiro</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-decoracao-jardim">Ver decoração</a>',
    ]
    missing = [x for x in required if x not in text]
    if missing:
        fail(f"Escolha Certa Online sem schedule/gate de navegação canônico: {missing}")
    if re.search(r"(?m)^\s*push\s*:", text):
        fail("Escolha Certa Online voltou a ter gatilho push após promoção final")


def audit_achados_que_valem_schedule() -> None:
    rel = ".github/workflows/achados_que_valem_store_autonomous.yml"
    text = read(rel)
    required = [
        "workflow_dispatch:", 'cron: "50 9 * * *"', 'timezone: "America/Recife"',
        "SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02",
        '<a class="bls-btn bls-btn-main" href="#bls-cozinha-utilidades">Ver cozinha</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-ferramentas">Ver ferramentas</a>',
        '<a class="bls-btn bls-btn-main" href="#bls-tecnologia-conectividade">Ver tecnologia</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-audio-lazer">Ver áudio</a>',
    ]
    missing = [x for x in required if x not in text]
    if missing:
        fail(f"Achados que Valem sem schedule/gate de navegação canônico: {missing}")
    if re.search(r"(?m)^\s*push\s*:", text):
        fail("Achados que Valem voltou a ter gatilho push após promoção final")


def audit_guia_schedule() -> None:
    rel = ".github/workflows/guia_achados_ofertas_store_autonomous.yml"
    text = read(rel)
    required = [
        "workflow_dispatch:", 'cron: "5 10 * * *"', 'timezone: "America/Recife"',
        "SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02",
        '<a class="bls-btn bls-btn-main" href="#bls-cozinha-eletroportateis">Ver cozinha</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-iluminacao-decoracao">Ver iluminação</a>',
        '<a class="bls-btn bls-btn-main" href="#bls-clima-conforto">Ver clima</a>',
        '<a class="bls-btn bls-btn-soft" href="#bls-utilidades-rotina">Ver utilidades</a>',
    ]
    missing = [x for x in required if x not in text]
    if missing:
        fail(f"Guia de Achados & Ofertas sem schedule/gate de navegação canônico: {missing}")
    if re.search(r"(?m)^\s*push\s*:", text):
        fail("Guia de Achados & Ofertas voltou a ter gatilho push após promoção final")


def audit_moda_schedule() -> None:
    rel = ".github/workflows/moda_ofertas_store_autonomous.yml"
    text = read(rel)
    required = [
        "workflow_dispatch:", 'cron: "20 10 * * *"', 'timezone: "America/Recife"',
        "SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02",
        '<h3>Beleza &amp; Cuidados</h3>',
        'href="#bls-moda-feminina">Ver moda feminina</a>',
        'href="#bls-acessorios">Ver acessórios</a>',
        'href="#bls-beleza-cuidados">Ver beleza</a>',
        'href="#bls-moda-masculina">Ver moda masculina</a>',
        "Suporte De Parede Multifuncional", "SHOTH FEMININO ALFAIATARIA",
        "Bolsa Feminina Kit Sacola Bag + Mini Tote + Carteira + Necessaire",
    ]
    missing = [x for x in required if x not in text]
    if missing:
        fail(f"Moda e Ofertas sem schedule/gate visual/semântico canônico: {missing}")
    if re.search(r"(?m)^\s*push\s*:", text):
        fail("Moda e Ofertas voltou a ter gatilho push após promoção final")


def audit_achadinhos_schedule() -> None:
    rel = ".github/workflows/achadinhos_beleza_store_autonomous.yml"
    text = read(rel)
    required = [
        "workflow_dispatch:", 'cron: "35 10 * * *"', 'timezone: "America/Recife"',
        "SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02",
        '<h3>Cuidados Pessoais</h3>',
        'href="#bls-skincare">Ver skincare</a>',
        'href="#bls-maquiagem">Ver maquiagem</a>',
        'href="#bls-cabelos">Ver cabelos</a>',
        'href="#bls-cuidados-pessoais">Ver cuidados pessoais</a>',
        "Cortador de Biscoitis / Massinha / Biscuit",
        "Kit Pancake Branco + Batom  Preto Halloween", "Capa Térmica para Chapinha",
    ]
    missing = [x for x in required if x not in text]
    if missing:
        fail(f"Achadinhos de Beleza sem schedule/gate visual/semântico canônico: {missing}")
    if re.search(r"(?m)^\s*push\s*:", text):
        fail("Achadinhos de Beleza voltou a ter gatilho push após promoção final")


def audit_radar_schedule() -> None:
    rel = ".github/workflows/radar_tech_blogger_store_autonomous.yml"
    text = read(rel)
    required = [
        "workflow_dispatch:",
        'cron: "50 10 * * *"',
        'timezone: "America/Recife"',
        "SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02",
        "PUBLIC_HTML_ENTITY_NORMALIZATION_2026_11_02",
        "Portal Radar Tech — tecnologia e achados práticos para a rotina",
        '<h3>Casa &amp; Organização</h3>',
        '<h3>Cozinha &amp; Utilidades</h3>',
        '<h3>Tecnologia &amp; Acessórios</h3>',
        '<h3>Beleza &amp; Cuidados</h3>',
        '<h3>Dia a Dia &amp; Praticidade</h3>',
        "Processador Picador De Alimentos Alça 3L Moedor De Carne Mixer Elétrico",
        "Kit 5 Suporte Organizador de Vassoura Rodo Mop",
        "Tomada De Parede Dupla USB E USB-C Carregador Rápido",
        "Capa Térmica para Chapinha",
    ]
    missing = [x for x in required if x not in text]
    if missing:
        fail(f"Portal Radar Tech Blogger sem schedule/gates finais obrigatórios: {missing}")
    if re.search(r"(?m)^\s*push\s*:", text):
        fail("Portal Radar Tech Blogger voltou a ter gatilho push após promoção final")


def audit_cozinha_schedule() -> None:
    rel = ".github/workflows/cozinha_sem_complicacao_store_autonomous.yml"
    text = read(rel)
    required = [
        "workflow_dispatch:",
        'cron: "5 11 * * *"',
        'timezone: "America/Recife"',
        "SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02",
        "PUBLIC_RATE_LIMIT_RETRY_2026_11_02",
        "Cozinha Sem Complicação — utensílios, eletroportáteis e soluções práticas",
        '<h3>Eletroportáteis</h3>',
        '<h3>Panelas &amp; Cocção</h3>',
        '<h3>Organização &amp; Pia</h3>',
        '<h3>Café &amp; Bebidas</h3>',
        '<h3>Utensílios &amp; Preparo</h3>',
        "Escova de Limpeza Multifuncional Flexível Para Garrafas Mamadeiras Liquidificador De Silicone",
        "Interruptor Forno Eletrico Fischer Gourmet Grill 44L",
        "Cafeteira De Prensa Francesa 600ml Manual Premium Filtro Inox Café Chá Espumador de Leite",
        "Oleo Mineral Grau Usp para Selar e hidratar Tabua De corte Carne Churrasco 500 ml",
    ]
    missing = [x for x in required if x not in text]
    if missing:
        fail(f"Cozinha Sem Complicação sem schedule/gates finais obrigatórios: {missing}")
    if re.search(r"(?m)^\s*push\s*:", text):
        fail("Cozinha Sem Complicação voltou a ter gatilho push após promoção final")


def audit_legacy_writers_manual_only() -> None:
    for rel, canonical_group in LEGACY_MANUAL_WORKFLOWS.items():
        text = read(rel)
        low = text.lower()
        if "legacy manual / recovery" not in low:
            fail(f"writer legado sem marca explícita de recovery: {rel}")
        if "workflow_dispatch:" not in text:
            fail(f"writer legado sem acionamento manual: {rel}")
        if re.search(r"(?m)^\s*schedule\s*:", text):
            fail(f"writer legado voltou a ter schedule automático: {rel}")
        if re.search(r"(?m)^\s*push\s*:", text):
            fail(f"writer legado voltou a ter gatilho push automático: {rel}")
        if f"group: {canonical_group}" not in text:
            fail(f"writer legado sem concurrency compartilhada com canônico: {rel}")


def iter_scan_files():
    for root_rel in SCAN_ROOTS:
        base = ROOT / root_rel
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES and "__pycache__" not in p.parts:
                yield p


def audit_cookie_safety() -> None:
    disable_re = re.compile(r"cookiechoices\s*=\s*\{\s*\}", re.I)
    selectors = (".cookie-choices-info", "#cookieChoiceInfo", ".cookieChoicesInfo")
    for p in iter_scan_files():
        raw = p.read_text(encoding="utf-8", errors="ignore")
        if disable_re.search(raw):
            fail(f"tentativa de desativar aviso nativo de cookies em {p.relative_to(ROOT)}")
        low = raw.lower()
        for selector in selectors:
            pos = low.find(selector.lower())
            while pos >= 0:
                window = low[pos:pos + 500]
                if "display:none" in window or "display: none" in window:
                    fail(f"aviso nativo de cookies ocultado em {p.relative_to(ROOT)}: {selector}")
                pos = low.find(selector.lower(), pos + 1)


def audit_legacy_identity() -> None:
    active = SAFE_WORKFLOWS + LIVE_WORKFLOWS
    for rel in active:
        text = read(rel)
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            negative_assert = stripped.startswith("! grep") or stripped.startswith("!grep")
            if negative_assert:
                continue
            for domain in LEGACY_DOMAINS:
                if domain in line:
                    fail(f"domínio legado em workflow ativo: {rel}:{lineno}: {domain}")


def main() -> None:
    audit_workflows()
    audit_casa_schedule()
    audit_escolha_schedule()
    audit_achados_que_valem_schedule()
    audit_guia_schedule()
    audit_moda_schedule()
    audit_achadinhos_schedule()
    audit_radar_schedule()
    audit_cozinha_schedule()
    audit_legacy_writers_manual_only()
    audit_cookie_safety()
    audit_legacy_identity()
    print("BLOGGER_POLICY_REPO_AUDIT_PASS")
    print("SAFE/LIVE 18/18 protegidos; schedules finais validados até Cozinha Sem Complicação 11:05 America/Recife; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.")


if __name__ == "__main__":
    main()
