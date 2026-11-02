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
]

# Fluxos preservados para recuperação, mas proibidos de voltar a escrever
# automaticamente no mesmo Store Post dos writers canônicos.
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
        'cron: "5 8 * * *"',
        'timezone: "America/Recife"',
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
        "workflow_dispatch:",
        'cron: "20 8 * * *"',
        'timezone: "America/Recife"',
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
        "workflow_dispatch:",
        'cron: "50 9 * * *"',
        'timezone: "America/Recife"',
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
    # Bloqueia referências antigas executáveis nos pipelines ativos.
    # Linhas de assert negativo (ex.: ! grep -q "dominio-antigo") são permitidas,
    # pois servem justamente para provar que a saída pública não contém o legado.
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
    audit_legacy_writers_manual_only()
    audit_cookie_safety()
    audit_legacy_identity()
    print("BLOGGER_POLICY_REPO_AUDIT_PASS")
    print("SAFE/LIVE 14/14 protegidos; Casa em Ordem 08:05, Escolha Certa Online 08:20 e Achados que Valem 09:50 protegidos; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.")


if __name__ == "__main__":
    main()
