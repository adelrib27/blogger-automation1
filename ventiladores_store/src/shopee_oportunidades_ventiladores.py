#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "ventiladores_store"
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(MODULE_DIR / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))
import shopee_oportunidades_v23 as v23


def regression_checks(rules_doc):
    cases = [
        ("Ventilador de Mesa 40cm 6 Pás 127V", "ventilador de mesa", True),
        ("Hélice para Ventilador de Mesa 40cm", "ventilador de mesa", False),
        ("Mini Ventilador de Mão USB para Mesa", "ventilador de mesa", False),
        ("Ventilador de Coluna Pedestal 40cm", "ventilador de coluna", True),
        ("Motor para Ventilador de Coluna", "ventilador de coluna", False),
        ("Base Ventilador de Coluna Pedestal 50cm", "ventilador de coluna", False),
        ("Ventilador Torre Digital com Controle", "ventilador torre", True),
        ("Capa para Ventilador Torre", "ventilador torre", False),
        ("Ventilador Residencial Modelos Teto Torre Mesa", "ventilador torre", False),
        ("Ventilador de Teto com Controle Remoto", "ventilador de teto", True),
        ("Capacitor para Ventilador de Teto", "ventilador de teto", False),
        ("Ventilador de Teto LED com Luz e Controle", "ventilador teto led", True),
        ("Lâmpada LED Avulsa para Ventilador de Teto", "ventilador teto led", False),
        ("Ventilador de Parede 60cm Industrial", "ventilador de parede", True),
        ("Grade para Ventilador de Parede", "ventilador de parede", False),
        ("Suporte para Ventilador de Parede 60cm", "ventilador de parede", False),
        ("Exaustor Ventilador de Parede Industrial", "ventilador parede industrial", False),
        ("Circulador de Ar Turbo 50cm", "circulador de ar", True),
        ("Motor Reposição Circulador de Ar", "circulador de ar", False),
        ("Climatizador Umidificador Circulador de Ar", "circulador de ar", False),
        ("Ventilador Portátil Recarregável USB", "ventilador portatil recarregavel", True),
        ("Somente Cabo USB para Ventilador Portátil", "ventilador portatil recarregavel", False),
        ("Mini Climatizador Ventilador Portátil Recarregável", "ventilador portatil recarregavel", False),
        ("Ventilador USB de Mesa Silencioso", "ventilador usb de mesa", True),
        ("Hélice Mini USB de Reposição", "ventilador usb de mesa", False),
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
