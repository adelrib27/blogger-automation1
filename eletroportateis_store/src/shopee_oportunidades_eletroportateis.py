#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "eletroportateis_store"
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(MODULE_DIR / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))
import shopee_oportunidades_v23 as v23


def regression_checks(rules_doc):
    cases = [
        ("Air Fryer Fritadeira Elétrica 5L 1500W 220V", "fritadeira eletrica", True),
        ("Kit Forma Air Fryer Silicone", "air fryer", False),
        ("Air Fryer Forno Oven 12L 1800W 127V", "air fryer forno", True),
        ("Liquidificador 1400W 15 Velocidades", "liquidificador", True),
        ("Copo para Liquidificador 3L", "liquidificador", False),
        ("Mixer Elétrico 3 em 1 800W", "mixer 3 em 1", True),
        ("Haste Avulsa para Mixer", "mixer eletrico", False),
        ("Processador de Alimentos 900W para Cozinha", "processador de alimentos", True),
        ("Lâmina Original Multiprocessador", "multiprocessador", False),
        ("Batedeira Planetária 700W 12 Velocidades", "batedeira planetaria", True),
        ("Tigela Avulsa para Batedeira", "batedeira eletrica", False),
        ("Cafeteira Elétrica 30 Xícaras 800W", "cafeteira eletrica", True),
        ("Jarra Avulsa para Cafeteira", "cafeteira eletrica", False),
        ("Sanduicheira Elétrica Grill 750W", "sanduicheira eletrica", True),
        ("Chaleira Elétrica 1,8L 1500W", "chaleira eletrica", True),
    ]
    failures=[]
    for title, keyword, expected in cases:
        actual=bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title":title,"keyword":keyword,"expected":expected,"actual":actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Eletroportáteis: " + repr(failures))
    print(f"Testes semânticos Eletroportáteis: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks=regression_checks
    print("=== ELETROPORTÁTEIS NA COZINHA — SHOPEE OPORTUNIDADES ===")
    ranking=v23.scan_v23(); v23.print_v23(ranking)

if __name__ == "__main__": main()
