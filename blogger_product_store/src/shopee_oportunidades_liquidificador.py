#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "blogger_product_store"
ROOT_SRC = ROOT / "src"

os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(MODULE_DIR / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))

import shopee_oportunidades_v23 as v23  # noqa: E402


def regression_checks(rules_doc):
    cases = [
        ("Liquidificador Philips Walita 1400W Copo 3L", "liquidificador", True),
        ("Copo para Liquidificador Philips Walita RI2242", "liquidificador", False),
        ("Mixer Elétrico 3 em 1 com Haste Inox", "mixer eletrico", True),
        ("Haste Avulsa para Mixer 3 em 1", "mixer eletrico", False),
        ("Multiprocessador de Alimentos 900W para Cozinha", "processador de alimentos", True),
        ("Processador Intel Core i5 para Computador", "processador de alimentos", False),
        ("Mini Triturador Elétrico de Alho e Cebola", "triturador eletrico", True),
        ("Triturador de Papel Elétrico para Escritório", "triturador eletrico", False),
        ("Espremedor Elétrico de Laranja e Limão", "espremedor eletrico", True),
        ("Alicate Espremedor para Tubo", "espremedor eletrico", False),
        ("Balança Digital de Cozinha para Alimentos", "balanca digital cozinha", True),
        ("Balança Corporal Digital para Banheiro", "balanca digital cozinha", False),
        ("Copo Medidor de Cozinha 1 Litro Graduado", "copo medidor cozinha", True),
        ("Copo para Liquidificador Philips Walita 3L", "copo medidor cozinha", False),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Liquidificador: " + repr(failures))
    print(f"Testes semânticos Liquidificador: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks = regression_checks
    print("=== BLOGGER LIQUIDIFICADOR — SHOPEE OPORTUNIDADES ===")
    print("5 categorias oficiais da vitrine automática.")
    ranking = v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
