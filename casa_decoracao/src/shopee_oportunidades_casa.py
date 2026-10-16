import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROOT_SRC = ROOT / "src"

# Isolamento total de configuracao e saidas do projeto Casa e Decoracao.
os.environ.setdefault(
    "SHOPEE_OPPORTUNITIES_CONFIG",
    str(ROOT / "casa_decoracao" / "config" / "shopee_oportunidades.json"),
)
os.environ.setdefault(
    "SHOPEE_INTENT_RULES",
    str(ROOT / "casa_decoracao" / "config" / "shopee_intent_rules.json"),
)
os.environ.setdefault(
    "SHOPEE_OUTPUT_DIR",
    str(ROOT / "casa_decoracao" / "data" / "shopee_oportunidades"),
)

if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))

import shopee_oportunidades_v23 as v23  # noqa: E402


def main() -> None:
    print("=== CASA E DECORACAO — SHOPEE OPORTUNIDADES ===")
    print("Projeto isolado do Radar Tech BR.")
    print("Destino de dados:", os.environ["SHOPEE_OUTPUT_DIR"])
    ranking = v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
