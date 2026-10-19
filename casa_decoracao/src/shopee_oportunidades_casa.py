import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(ROOT / "casa_decoracao" / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(ROOT / "casa_decoracao" / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(ROOT / "casa_decoracao" / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))

import shopee_oportunidades_v23 as v23  # noqa: E402


def regression_checks(rules_doc):
    cases = [
        ("Caminho de Mesa Bordado para Sala de Jantar", "caminho de mesa", True),
        ("Tecido Jacquard por Metro para Costura", "caminho de mesa", False),
        ("Caixa Organizadora Multiuso para Armário", "caixa organizadora", True),
        ("Caixa de Som Bluetooth Portátil", "caixa organizadora", False),
        ("Manta Decorativa para Sofá e Sala", "manta sofa", True),
        ("Manta Térmica Automotiva para Motor", "manta sofa", False),
        ("Travesseiro Macio para Quarto", "travesseiro", True),
        ("Fronha Avulsa para Travesseiro", "travesseiro", False),
        ("Escorredor de Louças para Pratos e Talheres", "escorredor de loucas", True),
        ("Escorredor de Macarrão Inox", "escorredor de loucas", False),
        ("Tapete Antiderrapante para Banheiro e Box", "tapete banheiro", True),
        ("Tapete Automotivo Universal", "tapete banheiro", False),
        ("Luminária Solar LED para Jardim Área Externa", "luminaria solar jardim", True),
        ("Luminária Automotiva LED 12V", "luminaria solar jardim", False),
        ("Protetor Impermeável de Colchão Queen", "protetor de colchao", True),
        ("Protetor de Travesseiro Impermeável", "protetor de colchao", False),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Casa: " + repr(failures))
    print(f"Testes semânticos Casa: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks = regression_checks
    print("=== CASA E DECORAÇÃO — SHOPEE OPORTUNIDADES ===")
    print("8 categorias oficiais com rotação editorial.")
    ranking = v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
