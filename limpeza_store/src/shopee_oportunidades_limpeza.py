#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "limpeza_store"
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(MODULE_DIR / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))
import shopee_oportunidades_v23 as v23


def regression_checks(rules_doc):
    cases = [
        ("Robô Aspirador Inteligente 3 em 1 Automático", "robo aspirador", True),
        ("Filtro HEPA para Robô Aspirador", "robo aspirador", False),
        ("Aspirador Vertical 2 em 1 1200W", "aspirador vertical", True),
        ("Filtro para Aspirador Vertical", "aspirador vertical", False),
        ("Aspirador Portátil Recarregável para Carro", "aspirador portatil", True),
        ("Bico Avulso para Aspirador Portátil", "aspirador portatil", False),
        ("Mop Giratório com Balde Centrífuga", "mop giratorio", True),
        ("Refil para Mop Giratório", "mop giratorio", False),
        ("Mop Spray com Reservatório para Piso", "mop spray", True),
        ("Cabo Avulso Mop Spray", "mop spray", False),
        ("Lavadora de Alta Pressão 1800W", "lavadora alta pressao", True),
        ("Mangueira Avulsa Lavadora Alta Pressão", "lavadora alta pressao", False),
        ("Extratora para Limpeza de Sofá e Carpete", "extratora limpeza", True),
        ("Produto Químico para Extratora Limpeza", "extratora limpeza", False),
        ("Limpador a Vapor Portátil Multiuso", "limpador a vapor", True),
        ("Pano Reposição Limpador a Vapor", "limpador a vapor", False),
    ]
    failures=[]
    for title, keyword, expected in cases:
        actual=bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title":title,"keyword":keyword,"expected":expected,"actual":actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Limpeza Inteligente: " + repr(failures))
    print(f"Testes semânticos Limpeza Inteligente: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks = regression_checks
    print("=== LIMPEZA INTELIGENTE — SHOPEE OPORTUNIDADES ===")
    ranking=v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
