from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

live_path = ROOT / ".github/workflows/moda_ofertas_store_autonomous.yml"
auditor_path = ROOT / "src/blogger_policy_repo_audit.py"

live = live_path.read_text(encoding="utf-8")
old_on = '''on:
  workflow_dispatch:
  push:
    paths:
      - "blogger_stores/moda_ofertas_live_kickoff.txt"
'''
new_on = '''on:
  workflow_dispatch:
  schedule:
    - cron: "20 10 * * *"
      timezone: "America/Recife"
'''
if old_on not in live:
    raise SystemExit("Bloco temporário on/push do Moda não encontrado; abortando fail-closed.")
live = live.replace(old_on, new_on, 1)

old_gate = '              && grep -q "Moda, beleza e ofertas para renovar o dia a dia" /tmp/moda-ofertas-loja.html \\\n'
new_gate = old_gate + '''              && grep -Fq '<h3>Beleza &amp; Cuidados</h3>' /tmp/moda-ofertas-loja.html \\
              && grep -Fq 'href="#bls-moda-feminina">Ver moda feminina</a>' /tmp/moda-ofertas-loja.html \\
              && grep -Fq 'href="#bls-acessorios">Ver acessórios</a>' /tmp/moda-ofertas-loja.html \\
              && grep -Fq 'href="#bls-beleza-cuidados">Ver beleza</a>' /tmp/moda-ofertas-loja.html \\
              && grep -Fq 'href="#bls-moda-masculina">Ver moda masculina</a>' /tmp/moda-ofertas-loja.html \\
'''
if old_gate not in live:
    raise SystemExit("Gate público de identidade não encontrado; abortando fail-closed.")
live = live.replace(old_gate, new_gate, 1)

old_required = "              'Moda, beleza e ofertas para renovar o dia a dia',\n"
new_required = old_required + '''              '<h3>Beleza &amp; Cuidados</h3>',
              'href="#bls-moda-feminina">Ver moda feminina</a>',
              'href="#bls-acessorios">Ver acessórios</a>',
              'href="#bls-beleza-cuidados">Ver beleza</a>',
              'href="#bls-moda-masculina">Ver moda masculina</a>',
'''
if old_required not in live:
    raise SystemExit("Lista Python de identidade pública não encontrada; abortando fail-closed.")
live = live.replace(old_required, new_required, 1)
live = live.replace("# TEMP_FIRST_LIVE_KICKOFF_2026_11_02", "# SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02")
live_path.write_text(live, encoding="utf-8")

# Reforço permanente do auditor central.
auditor = auditor_path.read_text(encoding="utf-8")
if "def audit_moda_schedule()" not in auditor:
    anchor = "\ndef audit_legacy_writers_manual_only() -> None:\n"
    fn = r'''
def audit_moda_schedule() -> None:
    rel = ".github/workflows/moda_ofertas_store_autonomous.yml"
    text = read(rel)
    required = [
        "workflow_dispatch:",
        'cron: "20 10 * * *"',
        'timezone: "America/Recife"',
        "SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02",
        '<h3>Beleza &amp; Cuidados</h3>',
        'href="#bls-moda-feminina">Ver moda feminina</a>',
        'href="#bls-acessorios">Ver acessórios</a>',
        'href="#bls-beleza-cuidados">Ver beleza</a>',
        'href="#bls-moda-masculina">Ver moda masculina</a>',
    ]
    missing = [x for x in required if x not in text]
    if missing:
        fail(f"Moda e Ofertas sem schedule/gate visual canônico: {missing}")
    if re.search(r"(?m)^\s*push\s*:", text):
        fail("Moda e Ofertas voltou a ter gatilho push após promoção final")

'''
    if anchor not in auditor:
        raise SystemExit("Âncora para audit_moda_schedule não encontrada; abortando fail-closed.")
    auditor = auditor.replace(anchor, "\n" + fn + "def audit_legacy_writers_manual_only() -> None:\n", 1)

call_anchor = "    audit_guia_schedule()\n    audit_legacy_writers_manual_only()\n"
if call_anchor in auditor:
    auditor = auditor.replace(call_anchor, "    audit_guia_schedule()\n    audit_moda_schedule()\n    audit_legacy_writers_manual_only()\n", 1)
elif "    audit_moda_schedule()\n" not in auditor:
    raise SystemExit("Chamada do auditor Moda não pôde ser instalada; abortando fail-closed.")

auditor = auditor.replace(
    "Moda e Ofertas LIVE permanece manual até o primeiro PASS público",
    "Moda e Ofertas 10:20 protegido",
)
auditor_path.write_text(auditor, encoding="utf-8")

# Limpa ferramentas/gatilhos de rollout pontual. O SAFE kickoff permanente permanece.
cleanup = [
    ".github/workflows/moda_ofertas_identity_fix_once.yml",
    "blogger_stores/moda_ofertas_identity_fix_kickoff.txt",
    ".github/workflows/moda_ofertas_anchor_fix_once.yml",
    "blogger_stores/moda_ofertas_anchor_fix_kickoff.txt",
    "scripts/moda_ofertas_anchor_fix_once.py",
    ".github/workflows/moda_ofertas_semantic_fix_once.yml",
    "blogger_stores/moda_ofertas_semantic_fix_kickoff.txt",
    "scripts/moda_ofertas_semantic_fix_once.py",
    ".github/workflows/moda_ofertas_accessory_fix_once.yml",
    "blogger_stores/moda_ofertas_accessory_fix_kickoff.txt",
    "scripts/moda_ofertas_accessory_fix_once.py",
    "blogger_stores/moda_ofertas_live_kickoff.txt",
    ".github/workflows/moda_ofertas_schedule_finalize_once.yml",
    "blogger_stores/moda_ofertas_schedule_finalize_kickoff.txt",
    "scripts/finalize_moda_ofertas_schedule.py",
]
for rel in cleanup:
    p = ROOT / rel
    if p.exists():
        p.unlink()

print("MODA_OFERTAS_SCHEDULE_FINALIZE_READY")
