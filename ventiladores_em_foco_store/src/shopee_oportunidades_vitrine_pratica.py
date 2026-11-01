#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "ventiladores_em_foco_store"
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(MODULE_DIR / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))
import shopee_oportunidades_v23 as v23


def regression_checks(rules_doc):
    cases = [
        ("Ventilador de Mesa 40cm Turbo 6 Pás", "ventilador de mesa", True),
        ("Hélice para Ventilador de Mesa 40cm Reposição", "ventilador de mesa", False),
        ("Ventilador de Coluna Pedestal 40cm 3 Velocidades", "ventilador de coluna", True),
        ("Motor para Ventilador de Coluna", "ventilador de coluna", False),
        ("Ventilador de Parede 60cm Oscilante Industrial", "ventilador de parede", True),
        ("Grade para Ventilador de Parede 60cm", "ventilador de parede", False),
        ("Ventilador de Teto 3 Pás com Controle Remoto", "ventilador teto controle remoto", True),
        ("Controle Remoto Avulso para Ventilador de Teto", "ventilador teto controle remoto", False),
        ("Ventilador de Teto com Luminária LED", "ventilador teto com luminaria", True),
        ("Ventilador Torre Silencioso 3 Velocidades", "ventilador torre", True),
        ("Circulador de Ar Turbo 50cm", "circulador de ar", True),
        ("Capacitor para Circulador de Ar", "circulador de ar", False),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Ventiladores em Foco: " + repr(failures))
    print(f"Testes semânticos Ventiladores em Foco: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks = regression_checks
    print("=== VENTILADORES EM FOCO — SHOPEE OPORTUNIDADES ===")
    ranking = v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
