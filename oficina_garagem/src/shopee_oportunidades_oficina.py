import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(ROOT / "oficina_garagem" / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(ROOT / "oficina_garagem" / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(ROOT / "oficina_garagem" / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))

import shopee_oportunidades_v23 as v23  # noqa: E402


def regression_checks(rules_doc):
    cases = [
        ("Parafusadeira Furadeira 21V com Maleta", "parafusadeira", True),
        ("Kit Bits Pontas para Parafusadeira 30 Peças", "parafusadeira", False),
        ("Furadeira de Impacto com Empunhadura", "furadeira", True),
        ("Jogo Brocas para Furadeira 12 Peças", "furadeira", False),
        ("Aspirador de Pó Portátil Automotivo para Carro", "aspirador automotivo", True),
        ("Filtro Hepa para Aspirador Automotivo", "aspirador automotivo", False),
        ("Óculos de Proteção Transparente para Trabalho", "oculos de protecao", True),
        ("Óculos de Sol Polarizado UV400", "oculos de protecao", False),
        ("Painel Pegboard para Ferramentas Oficina", "painel ferramentas", True),
        ("Painel Decorativo Festa Garagem", "painel ferramentas", False),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Oficina: " + repr(failures))
    print(f"Testes semânticos Oficina: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks = regression_checks
    print("=== OFICINA & GARAGEM — SHOPEE OPORTUNIDADES ===")
    print("Isolado de Radar Tech BR e Casa e Decoração.")
    ranking = v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
