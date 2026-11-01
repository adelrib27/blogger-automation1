#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "air_fryers_store"
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(MODULE_DIR / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))
import shopee_oportunidades_v23 as v23


def regression_checks(rules_doc):
    cases = [
        ("Air Fryer Digital 5L 1500W Sem Óleo", "air fryer", True),
        ("Forma de Silicone para Air Fryer 20cm", "air fryer", False),
        ("Fritadeira Elétrica Air Fryer 4L 1400W", "fritadeira eletrica", True),
        ("Cesto de Reposição para Fritadeira Elétrica", "fritadeira eletrica", False),
        ("Air Fryer Oven Forno 12L Digital", "air fryer oven", True),
        ("Forma para Air Fryer Oven", "air fryer oven", False),
        ("Forma Silicone Air Fryer Reutilizável", "forma silicone air fryer", True),
        ("Forma de Gelo Silicone", "forma silicone air fryer", False),
        ("Papel Descartável para Air Fryer 100 Unidades", "papel air fryer", True),
        ("Papel Presente Decorativo", "papel air fryer", False),
        ("Grelha Rack para Air Fryer Inox", "grelha air fryer", True),
        ("Grade para Ventilador", "grelha air fryer", False),
        ("Cesto Compatível com Air Fryer 5L", "cesto air fryer", True),
        ("Cesto Organizador de Roupas", "cesto air fryer", False),
        ("Pegador Pinça Silicone Cozinha 30cm", "pegador silicone cozinha", True),
        ("Pinça para Sobrancelha", "pegador silicone cozinha", False),
        ("Pincel Silicone Culinário para Cozinha", "pincel silicone cozinha", True),
        ("Pincel de Maquiagem Silicone", "pincel silicone cozinha", False),
        ("Termômetro Culinário Digital para Carne", "termometro culinario", True),
        ("Termômetro Corporal Digital Febre", "termometro culinario", False),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Air Fryers em Foco: " + repr(failures))
    print(f"Testes semânticos Air Fryers em Foco: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks = regression_checks
    print("=== AIR FRYERS EM FOCO — SHOPEE OPORTUNIDADES ===")
    ranking = v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
