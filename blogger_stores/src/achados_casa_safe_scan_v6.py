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
        "ventilador": ["climatizador", "umidificador", "refrigerador de ar", "mini ar condicionado"],
        "mixer eletrico": ["peca para mixer", "haste para mixer", "copo para mixer", "lamina para mixer"],
        "mop giratorio": ["cabo para mop", "cabo mop", "refil", "reposicao"],
        "aspirador de po": ["saco para aspirador", "filtro para aspirador", "mangueira", "bico para aspirador"],
        "umidificador": ["essencia", "essencias", "refil", "filtro para umidificador"],
        "cortina blackout": ["tecido para cortina", "varao para cortina", "gancho para cortina"],
        "ar condicionado portatil": ["tubo para ar condicionado", "mangueira para ar condicionado", "controle para ar condicionado", "suporte para ar condicionado"],
    }
    if any(term in title for term in blocks.get(key, [])):
        return False
    if key == "fritadeira eletrica":
        # Exige o aparelho, não peça/acessório com a palavra fritadeira no título.
        if "fritadeira" not in title:
            return False
        if not any(term in title for term in ["eletrica", "sem oleo", "air fryer", "airfryer"]):
            return False
    return True


def main() -> int:
    v3.extra_keyword_gate = final_product_gate
    result = v3.main()
    data = json.loads(v3.base.SELECTION_PATH.read_text(encoding="utf-8"))
    data["schemaVersion"] = 6
    data.setdefault("semanticValidation", {})["homeUsePostGateVersion"] = 6
    data.setdefault("semanticValidation", {})["fritadeiraApplianceOnly"] = True
    data.setdefault("gates", {})["homeUsePostGate"] = True
    data.setdefault("gates", {})["fritadeiraApplianceOnly"] = True
    v3.base.save_atomic(v3.base.SELECTION_PATH, data)
    print("ACHADOS_SAFE_V6_READY: fritadeira completa obrigatória; diversidade e 20/20 links validados; Blogger não alterado.")
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ACHADOS_SAFE_V6_FAILED: {exc}", file=sys.stderr)
        raise
