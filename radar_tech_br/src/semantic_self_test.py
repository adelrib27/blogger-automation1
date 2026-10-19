import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_SRC = ROOT / "src"
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))

import shopee_oportunidades_v23 as v23  # noqa: E402

RULES = ROOT / "config" / "shopee_intent_rules.json"


def main():
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    cases = [
        ("Ventilador Interno Painel Ar Grand Siena 1.4 2012 a 2016", "ventilador", False),
        ("Ventilador de Mesa Turbo 40cm 6 Pás", "ventilador", True),
        ("Cabo USB De Carregamento Rapido Tipo-C", "carregador rapido", False),
        ("Carregador Rápido Turbo USB-C para Tomada", "carregador rapido", True),
        ("Kit 6 Formas de Silicone para Air Fryer", "air fryer", False),
        ("Fritadeira Elétrica Air Fryer Digital", "air fryer", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(v23.evaluate_keyword(title, keyword, rules).get("accepted"))
        if actual != expected:
            failures.append((title, keyword, expected, actual))
    if failures:
        raise SystemExit("Falha no guard semântico Radar: " + repr(failures))
    print(f"Guard semântico Radar: {len(cases)}/{len(cases)} OK")


if __name__ == "__main__":
    main()
