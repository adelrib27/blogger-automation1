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
        ("Robô Aspirador Inteligente 3 em 1 Automático", "robo aspirador inteligente", True),
        ("Desinfetante para Robô Aspirador 1 Litro", "robo aspirador inteligente", False),
        ("Mop Pano Almofada para Robô Aspirador", "robo aspirador inteligente", False),
        ("Tanque Substituição 2 em 1 para Robot Vacuum Aspirador", "robot vacuum aspirador", False),
        ("Aspirador Vertical 1250W Completo", "aspirador vertical", True),
        ("Suporte de Parede Para Aspirador Vertical", "aspirador vertical", False),
        ("Aspirador Vertical 2 em 1 Portátil 1200W", "aspirador vertical 2 em 1", True),
        ("Filtro para Aspirador Vertical 2 em 1", "aspirador vertical 2 em 1", False),
        ("Aspirador Vassoura Vertical 1000W", "aspirador vassoura", True),
        ("Suporte para Aspirador Vassoura", "aspirador vassoura", False),
        ("Aspirador Vertical Potente 1600W", "aspirador vertical potente", True),
        ("Motor 1600W para Aspirador Vertical Potente", "aspirador vertical potente", False),
        ("Aspirador Portátil Recarregável Sem Fio", "aspirador portatil recarregavel", True),
        ("Bico Avulso para Aspirador Portátil", "aspirador portatil recarregavel", False),
        ("Mop Giratório com Balde Centrífuga", "mop giratorio com balde", True),
        ("Cabo Mop Giratório Completo 140cm", "mop giratorio com balde", False),
        ("Mop Spray Completo com Reservatório", "mop spray completo", True),
        ("Refil para Mop Spray", "mop spray completo", False),
        ("Lavadora de Alta Pressão Completa 1800W", "lavadora alta pressao completa", True),
        ("Engate Rápido com Espigão para Lavadora de Alta Pressão", "lavadora alta pressao completa", False),
        ("Extratora Limpeza Estofado Sofá Carpete", "extratora limpeza estofado", True),
        ("Produto Químico Shampoo para Extratora", "extratora limpeza estofado", False),
        ("Limpador a Vapor Portátil Multiuso", "limpador a vapor portatil", True),
        ("Pano Reposição Limpador a Vapor", "limpador a vapor portatil", False),
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
