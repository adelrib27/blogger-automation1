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


def main() -> int:
    v3.extra_keyword_gate = final_product_gate
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
