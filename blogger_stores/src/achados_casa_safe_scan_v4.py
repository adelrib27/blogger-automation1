#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import achados_casa_safe_scan_v3 as v3

_original_gate = v3.extra_keyword_gate


def home_use_gate(product: dict, keyword: str) -> bool:
    if not _original_gate(product, keyword):
        return False
    title = v3.norm(product.get("productName") or "")
    key = v3.norm(keyword)
    blocks = {
        "air fryer": ["spray", "limpa air fryer", "limpador", "desengordurante", "produto de limpeza"],
        "luminaria": ["estetica", "salao", "limpeza de pele", "manicure", "cilios", "lash", "unha", "procedimento estetico"],
        "ventilador": ["climatizador", "umidificador", "refrigerador de ar", "mini ar condicionado"],
        "mixer eletrico": ["peca para mixer", "haste para mixer", "copo para mixer"],
    }
    return not any(term in title for term in blocks.get(key, []))


def main() -> int:
    v3.extra_keyword_gate = home_use_gate
    result = v3.main()
    data = json.loads(v3.base.SELECTION_PATH.read_text(encoding="utf-8"))
    data["schemaVersion"] = 4
    data.setdefault("semanticValidation", {})["homeUsePostGateVersion"] = 4
    data.setdefault("gates", {})["homeUsePostGate"] = True
    v3.base.save_atomic(v3.base.SELECTION_PATH, data)
    print("ACHADOS_SAFE_V4_READY: gate de uso doméstico aplicado; seleção pronta apenas após curadoria final.")
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ACHADOS_SAFE_V4_FAILED: {exc}", file=sys.stderr)
        raise
