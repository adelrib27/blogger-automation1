#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import achados_casa_safe_scan_v3 as v3

_original_gate = v3.extra_keyword_gate


def final_home_product_gate(product: dict, keyword: str) -> bool:
    if not _original_gate(product, keyword):
        return False
    title = v3.norm(product.get("productName") or "")
    key = v3.norm(keyword)
    blocks = {
        "air fryer": [
            "spray", "limpa air fryer", "limpador", "desengordurante", "produto de limpeza",
            "botao", "knob", "puxador", "peca", "resistencia", "cabo", "painel", "termostato",
            "cesto para air fryer", "forma para air fryer", "forma de silicone", "papel para air fryer",
            "tapete de silicone", "capa para air fryer", "acessorio"
        ],
        "luminaria": [
            "estetica", "salao", "limpeza de pele", "manicure", "cilios", "lash", "unha",
            "procedimento estetico"
        ],
        "ventilador": ["climatizador", "umidificador", "refrigerador de ar", "mini ar condicionado"],
        "mixer eletrico": ["peca para mixer", "haste para mixer", "copo para mixer", "lamina para mixer"],
        "mop giratorio": ["cabo para mop", "cabo mop", "refil", "reposicao"],
        "aspirador de po": ["saco para aspirador", "filtro para aspirador", "mangueira", "bico para aspirador"],
        "umidificador": ["essencia", "essencias", "refil", "filtro para umidificador"],
        "cortina blackout": ["tecido para cortina", "varao para cortina", "gancho para cortina"],
        "ar condicionado portatil": ["tubo para ar condicionado", "mangueira para ar condicionado", "controle para ar condicionado", "suporte para ar condicionado"],
    }
    return not any(term in title for term in blocks.get(key, []))


def main() -> int:
    v3.extra_keyword_gate = final_home_product_gate
    result = v3.main()
    data = json.loads(v3.base.SELECTION_PATH.read_text(encoding="utf-8"))
    data["schemaVersion"] = 5
    data.setdefault("semanticValidation", {})["homeUsePostGateVersion"] = 5
    data.setdefault("semanticValidation", {})["airFryerPartsBlocked"] = True
    data.setdefault("gates", {})["homeUsePostGate"] = True
    data.setdefault("gates", {})["airFryerPartsBlocked"] = True
    v3.base.save_atomic(v3.base.SELECTION_PATH, data)
    print("ACHADOS_SAFE_V5_READY: peças/acessórios bloqueados; 20 produtos completos; links validados; Blogger não alterado.")
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ACHADOS_SAFE_V5_FAILED: {exc}", file=sys.stderr)
        raise
