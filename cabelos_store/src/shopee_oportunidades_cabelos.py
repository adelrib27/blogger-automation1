#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "cabelos_store"
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(MODULE_DIR / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))
import shopee_oportunidades_v23 as v23


def regression_checks(rules_doc):
    cases = [
        ("Máscara Capilar Hidratação Profunda 500g", "mascara capilar", True),
        ("Máscara Facial Hidratante", "mascara capilar", False),
        ("Máscara de Hidratação para Cabelos 1kg", "mascara hidratacao cabelo", True),
        ("Reconstrutor Capilar Queratina 250ml", "reconstrutor capilar", True),
        ("Minoxidil Tratamento Antiqueda", "reconstrutor capilar", False),
        ("Shampoo Capilar 500ml", "shampoo cabelo", True),
        ("Shampoo Veterinário para Cães", "shampoo cabelo", False),
        ("Condicionador para Cabelos 400ml", "condicionador cabelo", True),
        ("Kit Shampoo e Condicionador Cabelos", "kit shampoo condicionador", True),
        ("Leave-in Capilar Finalizador", "leave in cabelo", True),
        ("Creme para Pentear Cabelos Cacheados", "creme pentear cabelo", True),
        ("Óleo Capilar Finalizador Reparador", "oleo capilar finalizador", True),
        ("Óleo Essencial Aromaterapia", "oleo capilar finalizador", False),
        ("Secador de Cabelo 2000W 220V", "secador de cabelo", True),
        ("Difusor para Secador de Cabelo", "secador de cabelo", False),
        ("Escova Secadora 1200W para Cabelos", "escova secadora", True),
        ("Refil Escova Secadora", "escova secadora", False),
        ("Escova Modeladora Rotativa para Cabelos Bivolt", "escova modeladora cabelo", True),
        ("Pente Profissional para Cabelo", "pente cabelo", True),
        ("Pente para Máquina de Cortar", "pente cabelo", False),
        ("Escova Desembaraçadora para Cabelos", "escova desembaracadora", True),
        ("Touca de Cetim para Cabelos Dormir", "touca cetim cabelo", True),
        ("Touca Cirúrgica Descartável", "touca cetim cabelo", False),
    ]
    failures=[]
    for title, keyword, expected in cases:
        actual=bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title":title,"keyword":keyword,"expected":expected,"actual":actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Cabelos em Foco: " + repr(failures))
    print(f"Testes semânticos Cabelos em Foco: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks = regression_checks
    print("=== CABELOS EM FOCO — SHOPEE OPORTUNIDADES ===")
    ranking=v23.scan_v23()
    v23.print_v23(ranking)

if __name__ == "__main__":
    main()
