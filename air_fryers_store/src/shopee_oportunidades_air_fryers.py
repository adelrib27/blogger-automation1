#!/usr/bin/env python3
import os
import re
import sys
import unicodedata
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

_ORIGINAL_EVALUATE_KEYWORD = v23.evaluate_keyword


def _norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", text).strip()


def _capacities_liters(title: str) -> list[float]:
    text = _norm(title).replace(",", ".")
    values = []
    # Exige fronteira numérica para que 3,6 L nunca seja interpretado como 6 L.
    for match in re.finditer(r"(?<!\d)(\d{1,2}(?:\.\d+)?)\s*(?:l\b|litro\b|litros\b)", text):
        try:
            value = float(match.group(1))
        except ValueError:
            continue
        if 0.5 <= value <= 30:
            values.append(value)
    return values


def evaluate_keyword_strict_capacity(title, keyword, rules_doc):
    result = dict(_ORIGINAL_EVALUATE_KEYWORD(title, keyword, rules_doc))
    if not result.get("accepted"):
        return result

    key = _norm(keyword)
    capacities = _capacities_liters(title)

    if key == "air fryer 6 litros" and not any(6.0 <= value < 7.0 for value in capacities):
        return {"accepted": False, "score": 0.0, "reason": "capacidade_6l_nao_confirmada", "matched": [], "missing": ["6.x L"]}

    if key == "air fryer 8 litros" and not any(8.0 <= value < 9.0 for value in capacities):
        return {"accepted": False, "score": 0.0, "reason": "capacidade_8l_nao_confirmada", "matched": [], "missing": ["8.x L"]}

    if key == "air fryer grande" and not any(value >= 5.0 for value in capacities):
        return {"accepted": False, "score": 0.0, "reason": "capacidade_familia_nao_confirmada", "matched": [], "missing": [">=5 L"]}

    return result


# O scanner usa evaluate_keyword internamente; a adaptação fica restrita a este blog.
v23.evaluate_keyword = evaluate_keyword_strict_capacity


def regression_checks(rules_doc):
    cases = [
        ("Air Fryer Digital 5L 1500W Sem Óleo", "air fryer", True),
        ("Limpa Air Fryer Spray Desengordurante", "air fryer", False),
        ("Adaptador Tomada para Air Fryer", "air fryer", False),
        ("Forma de Silicone para Air Fryer 20cm", "air fryer", False),
        ("Fritadeira Elétrica Air Fryer 4L 1400W", "fritadeira eletrica", True),
        ("Cesto de Reposição para Fritadeira Elétrica", "fritadeira eletrica", False),
        ("Air Fryer 6 Litros Digital 1700W", "air fryer 6 litros", True),
        ("Air Fryer 6,5L Digital 1700W", "air fryer 6 litros", True),
        ("Fritadeira Air fryer 3,6 Litros Telefunken EasyFryer", "air fryer 6 litros", False),
        ("Prateleira Suporte para Air Fryer 6 Litros", "air fryer 6 litros", False),
        ("Fritadeira Air Fryer 8L 1800W Família", "air fryer 8 litros", True),
        ("Air Fryer 8,5L Digital Família", "air fryer 8 litros", True),
        ("Air Fryer Fritadeira Grande 4,8 Litros", "air fryer 8 litros", False),
        ("Kit 2 Formas de Silicone Para AirFryer Tamanho Grande 4 - 8 Litros", "air fryer 8 litros", False),
        ("Capa para Air Fryer Fritadeira Elétrica Grande 8 Litros com Laço", "air fryer 8 litros", False),
        ("Air Fryer Grande 7L Digital", "air fryer grande", True),
        ("Air Fryer 5L Grande Família", "air fryer grande", True),
        ("Air Fryer 4,5L Grande Capacidade Ideal Família", "air fryer grande", False),
        ("Kit 2 Formas de Silicone Para AirFryer Fritadeira Elétrica Tamanho Grande", "air fryer grande", False),
        ("Capa para Air Fryer Fritadeira Elétrica Grande 8 Litros", "air fryer grande", False),
        ("Nicho Suporte Air Fryer Grande", "air fryer grande", False),
        ("Forma Silicone Air Fryer Reutilizável", "forma silicone air fryer", True),
        ("Forma de Gelo Silicone", "forma silicone air fryer", False),
        ("Papel Descartável para Air Fryer 100 Unidades", "papel air fryer", True),
        ("Papel Presente Decorativo", "papel air fryer", False),
        ("Grelha Rack para Air Fryer Inox", "grelha air fryer", True),
        ("Forma de Silicone para Air Fryer Protetor de Grelha", "grelha air fryer", False),
        ("Desengordurante Power Limpa Grelha Air Fryer 500ml", "grelha air fryer", False),
        ("Limpador Desengordurante Grelha Air Fryer Pisos Gorduras Pesadas", "grelha air fryer", False),
        ("Prateleira Suporte para Air Fryer", "grelha air fryer", False),
        ("Cesto Compatível Reposição Air Fryer 5L", "cesto compativel air fryer", True),
        ("Forma Silicone Protetor de Cesto Air Fryer", "cesto compativel air fryer", False),
        ("Cesto Organizador de Roupas", "cesto compativel air fryer", False),
        ("Rack Grelha Air Fryer 2 Andares", "rack air fryer", True),
        ("Forma Silicone Protetor de Grelha Rack Air Fryer", "rack air fryer", False),
        ("Limpa Grelha Churras Spray Limpeza Air Fryer", "rack air fryer", False),
        ("Rack Prateleira de Cozinha para Air Fryer", "rack air fryer", False),
        ("Pegador Pinça Silicone Cozinha 30cm", "pegador silicone cozinha", True),
        ("Filtro de Café com Pegador de Silicone", "pegador silicone cozinha", False),
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
    print("=== AIR FRYERS EM FOCO — SHOPEE OPORTUNIDADES V5 ===")
    ranking = v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
