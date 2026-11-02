#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "src" / "blogger_policy_repo_audit.py"
MOTOR = ROOT / "blogger_stores" / "src" / "cozinha_sem_complicacao_store.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_FAIL {label}: esperado 1 match, encontrado {count}")
    return text.replace(old, new, 1)


motor = MOTOR.read_text(encoding="utf-8")
motor = replace_once(
    motor,
    '        ("Espátula de Silicone para Cozinha", "espatula silicone", True),\n    ]',
    '        ("Espátula de Silicone para Cozinha", "espatula silicone", True),\n'
    '        ("Escova de Limpeza Multifuncional Flexível Para Garrafas Mamadeiras Liquidificador De Silicone", "liquidificador", False),\n'
    '        ("Interruptor Forno Eletrico Fischer Gourmet Grill 44L", "grill eletrico", False),\n'
    '        ("Cafeteira De Prensa Francesa 600ml Manual Premium Filtro Inox Café Chá Espumador de Leite", "espumador de leite", False),\n'
    '        ("Oleo Mineral Grau Usp para Selar e hidratar Tabua De corte Carne Churrasco 500 ml", "tabua de corte", False),\n'
    '    ]',
    "regressao-44",
)
motor = replace_once(
    motor,
    '    semantic["profileVersion"] = 2',
    '    semantic["profileVersion"] = 3',
    "profile-version-3",
)
MOTOR.write_text(motor, encoding="utf-8")

audit = AUDIT.read_text(encoding="utf-8")
audit = replace_once(
    audit,
    '    ".github/workflows/radar_tech_blogger_store_safe.yml",\n]',
    '    ".github/workflows/radar_tech_blogger_store_safe.yml",\n'
    '    ".github/workflows/cozinha_sem_complicacao_store_safe.yml",\n]',
    "safe-18",
)
audit = replace_once(
    audit,
    '    ".github/workflows/radar_tech_blogger_store_autonomous.yml",\n]',
    '    ".github/workflows/radar_tech_blogger_store_autonomous.yml",\n'
    '    ".github/workflows/cozinha_sem_complicacao_store_autonomous.yml",\n]',
    "live-18",
)
controlled_func = '''\n\ndef audit_cozinha_controlled() -> None:\n    rel = ".github/workflows/cozinha_sem_complicacao_store_autonomous.yml"\n    text = read(rel)\n    required = [\n        "workflow_dispatch:",\n        'blogger_stores/cozinha_sem_complicacao_live_kickoff.txt',\n        "CONTROLLED_LIVE_NO_SCHEDULE_2026_11_02",\n        "PUBLIC_RATE_LIMIT_RETRY_2026_11_02",\n        "Cozinha Sem Complicação — utensílios, eletroportáteis e soluções práticas",\n        '<h3>Eletroportáteis</h3>',\n        '<h3>Panelas &amp; Cocção</h3>',\n        '<h3>Organização &amp; Pia</h3>',\n        '<h3>Café &amp; Bebidas</h3>',\n        '<h3>Utensílios &amp; Preparo</h3>',\n        "Escova de Limpeza Multifuncional Flexível Para Garrafas Mamadeiras Liquidificador De Silicone",\n        "Interruptor Forno Eletrico Fischer Gourmet Grill 44L",\n        "Cafeteira De Prensa Francesa 600ml Manual Premium Filtro Inox Café Chá Espumador de Leite",\n        "Oleo Mineral Grau Usp para Selar e hidratar Tabua De corte Carne Churrasco 500 ml",\n    ]\n    missing = [x for x in required if x not in text]\n    if missing:\n        fail(f"Cozinha Sem Complicação LIVE controlado sem gates obrigatórios: {missing}")\n    if not re.search(r"(?m)^\\s*push\\s*:", text):\n        fail("Cozinha Sem Complicação LIVE controlado sem gatilho de kickoff")\n    if re.search(r"(?m)^\\s*schedule\\s*:", text):\n        fail("Cozinha Sem Complicação recebeu schedule antes da validação pública")\n'''
audit = replace_once(
    audit,
    '\n\ndef audit_legacy_writers_manual_only() -> None:',
    controlled_func + '\n\ndef audit_legacy_writers_manual_only() -> None:',
    "cozinha-controlled-func",
)
audit = replace_once(
    audit,
    '    audit_radar_schedule()\n    audit_legacy_writers_manual_only()',
    '    audit_radar_schedule()\n    audit_cozinha_controlled()\n    audit_legacy_writers_manual_only()',
    "cozinha-controlled-call",
)
audit = replace_once(
    audit,
    '    print("SAFE/LIVE 17/17 protegidos; schedules validados até Portal Radar Tech Blogger 10:50 America/Recife; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.")',
    '    print("SAFE/LIVE 18/18 protegidos; Cozinha Sem Complicação em LIVE controlado sem schedule; schedules finais validados até Portal Radar Tech Blogger 10:50 America/Recife; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.")',
    "audit-summary-18-controlled",
)
AUDIT.write_text(audit, encoding="utf-8")

print("COZINHA_CONTROLLED_PATCH_PASS: motor com regressão 44 e auditor central 18/18 controlado")
