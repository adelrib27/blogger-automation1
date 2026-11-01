#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "vitrine_pratica_store"
ROOT_SRC = ROOT / "src"

os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(MODULE_DIR / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))

import shopee_oportunidades_v23 as v23


def regression_checks(rules_doc):
    cases = [
        ("Caixa Organizadora Grande Dobrável para Quarto e Casa", "caixa organizadora", True),
        ("Sapateira Organizadora 5 Andares para Quarto", "sapateira organizadora", True),
        ("Capa para Sapateira Organizadora", "sapateira organizadora", False),
        ("Organizador de Banheiro Prateleira para Shampoo", "organizador banheiro", True),
        ("Fritadeira Elétrica Air Fryer 5L 1500W Sem Óleo", "fritadeira eletrica", True),
        ("Kit Forma Air Fryer + Pegador", "fritadeira eletrica", False),
        ("Botão Air Fryer Reposição", "fritadeira eletrica", False),
        ("Mixer Elétrico de Mão 3 em 1 500W", "mixer eletrico", True),
        ("Haste Avulsa para Mixer", "mixer eletrico", False),
        ("Escorredor de Louças 13 Pratos Aço", "escorredor de loucas", True),
        ("Smartwatch Relógio Inteligente AMOLED Bluetooth", "smartwatch", True),
        ("Pulseira para Smartwatch Silicone", "smartwatch", False),
        ("Fone Bluetooth Sem Fio TWS", "fone bluetooth", True),
        ("Case para Fone Bluetooth", "fone bluetooth", False),
        ("Carregador USB C Fonte 20W Tipo C", "carregador usb c", True),
        ("Cabo USB C 2 Metros", "carregador usb c", False),
        ("Secador de Cabelo Profissional 2000W", "secador de cabelo", True),
        ("Difusor para Secador de Cabelo", "secador de cabelo", False),
        ("Aparador de Pelos Barba Corpo Recarregável", "aparador de pelos", True),
        ("Lâmina para Aparador de Pelos", "aparador de pelos", False),
        ("Escova Secadora Modeladora 1200W", "escova secadora", True),
        ("Refil Escova Secadora", "escova secadora", False),
        ("Garrafa Térmica Inox 1 Litro", "garrafa termica", True),
        ("Tampa para Garrafa Térmica", "garrafa termica", False),
        ("Mochila Escolar Executiva Impermeável", "mochila", True),
        ("Capa de Chuva para Mochila", "mochila", False),
        ("Ventilador Portátil USB de Mesa Recarregável", "ventilador portatil", True),
        ("Hélice Ventilador Portátil Reposição", "ventilador portatil", False),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Vitrine Prática: " + repr(failures))
    print(f"Testes semânticos Vitrine Prática: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks = regression_checks
    print("=== VITRINE PRÁTICA — SHOPEE OPORTUNIDADES ===")
    print("5 categorias oficiais da vitrine automática.")
    ranking = v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
