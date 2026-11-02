#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import achados_casa_safe_scan_v3 as v3

_original_gate = v3.extra_keyword_gate


def final_product_gate(product: dict, keyword: str) -> bool:
    if not _original_gate(product, keyword):
        return False
    title = v3.norm(product.get("productName") or "")
    key = v3.norm(keyword)
    blocks = {
        "fritadeira eletrica": [
            "cesto", "forma", "papel", "tapete", "capa", "botao", "knob", "puxador", "peca",
            "resistencia", "cabo", "painel", "termostato", "spray", "limpador", "desengordurante",
            "acessorio", "pegador", "pinca", "pinça", "grade", "bandeja", "refil"
        ],
        "luminaria": ["estetica", "salao", "limpeza de pele", "manicure", "cilios", "lash", "unha", "procedimento estetico"],
        "ventilador de teto": [
            "cilios", "extensoes", "maquiagem", "carimbo", "impressao 3d", "confeitaria",
            "molde", "chaveiro", "adesivo", "topper", "ventoinha", "motor ventilador",
            "resistencia ventilador", "escova", "limpador", "espanador", "capa para ventilador",
            "grade para ventilador", "helice avulsa", "capacitor", "suporte para ventilador",
            "peca para ventilador", "cabo para ventilador"
        ],
        "ventilador de mesa": [
            "cilios", "extensoes", "maquiagem", "carimbo", "impressao 3d", "confeitaria",
            "molde", "chaveiro", "adesivo", "topper", "ventoinha", "motor ventilador",
            "resistencia ventilador", "escova", "limpador", "espanador", "capa para ventilador",
            "grade para ventilador", "helice avulsa", "capacitor", "suporte para ventilador",
            "peca para ventilador", "cabo para ventilador"
        ],
        "mixer eletrico": ["peca para mixer", "haste para mixer", "copo para mixer", "lamina para mixer"],
        "mop giratorio": ["cabo para mop", "cabo mop", "refil", "reposicao"],
        "aspirador de po": ["saco para aspirador", "filtro para aspirador", "mangueira", "bico para aspirador"],
        "umidificador": ["essencia", "essencias", "refil", "filtro para umidificador"],
        "cortina blackout": ["tecido para cortina", "varao para cortina", "gancho para cortina"],
    }
    if any(term in title for term in blocks.get(key, [])):
        return False

    if key == "fritadeira eletrica":
        if "fritadeira" not in title:
            return False
        if not any(term in title for term in ["eletrica", "sem oleo", "air fryer", "airfryer"]):
            return False

    if key == "ventilador de teto":
        if "ventilador" not in title or "teto" not in title:
            return False
        if not any(term in title for term in ["pas", "helices", "velocidades", "controle remoto", "silencioso", "bivolt", "w"]):
            return False

    if key == "ventilador de mesa":
        if "ventilador" not in title or "mesa" not in title:
            return False
        if not any(term in title for term in ["pas", "helices", "velocidades", "oscilante", "turbo", "30 cm", "40 cm", "50 cm", "w"]):
            return False

    return True


def run_achados_regression_checks(rules_doc: dict) -> None:
    """Regressão específica do perfil Achados v5.

    O motor v23 compartilhado ainda possui casos históricos para a palavra
    genérica "ventilador". O Achados não usa mais esse termo: usa apenas
    "ventilador de teto" e "ventilador de mesa" para reduzir ambiguidade.
    """
    evaluate = v3.base.shopee_v23.evaluate_keyword
    cases = [
        ("Carimbo Docinho VENTILADOR Impressão 3D Confeitaria Criativa", "ventilador de teto", False),
        ("Extensão de Cílios Forma Ventilador 5D Volume Russo", "ventilador de mesa", False),
        ("Escova Limpadora de Ventilador Tira Poeira", "ventilador de mesa", False),
        ("Ventilador de Teto 3 Pás Silencioso com Controle Remoto Bivolt", "ventilador de teto", True),
        ("Ventilador de Mesa 40 cm Turbo 6 Pás 3 Velocidades", "ventilador de mesa", True),
        ("Adaptador de Tomada de Porcelana para Secador Air Fryer 20A", "air fryer", False),
        ("Kit 6 Forma de Silicone para Fritadeira Air Fryer", "air fryer", False),
        ("Fritadeira Elétrica Air Fryer 5L Digital 1500W", "air fryer", True),
        ("Papa Bolinhas Elétrico Tira Pelos de Roupas Aparador", "aparador de pelos", False),
        ("Máquina de Barbear e Aparador Pelos Elétrico 3 em 1", "aparador de pelos", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(evaluate(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit(
            "Falha nos testes de regressão semântica Achados v5: "
            + json.dumps(failures, ensure_ascii=False)
        )
    print(f"Testes semânticos Achados v5: {len(cases)}/{len(cases)} OK")


def main() -> int:
    v3.extra_keyword_gate = final_product_gate
    # O scan_v23 chama esta função antes de consultar a API. Mantemos a
    # regressão obrigatória, mas alinhada ao perfil específico deste blog.
    v3.base.shopee_v23.run_regression_checks = run_achados_regression_checks
    result = v3.main()
    data = json.loads(v3.base.SELECTION_PATH.read_text(encoding="utf-8"))
    data["schemaVersion"] = 6
    semantic = data.setdefault("semanticValidation", {})
    semantic["homeUsePostGateVersion"] = 6
    semantic["fritadeiraApplianceOnly"] = True
    semantic["ceilingFanApplianceOnly"] = True
    semantic["tableFanApplianceOnly"] = True
    gates = data.setdefault("gates", {})
    gates["homeUsePostGate"] = True
    gates["fritadeiraApplianceOnly"] = True
    gates["ceilingFanApplianceOnly"] = True
    gates["tableFanApplianceOnly"] = True
    v3.base.save_atomic(v3.base.SELECTION_PATH, data)
    print("ACHADOS_SAFE_V6_READY: aparelhos completos obrigatórios para fritadeira, ventilador de teto e ventilador de mesa; diversidade e 20/20 links validados; Blogger não alterado.")
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ACHADOS_SAFE_V6_FAILED: {exc}", file=sys.stderr)
        raise
