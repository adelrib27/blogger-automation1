#!/usr/bin/env python3
"""LAB: exatamente uma consulta Shopee, contagem agregada, zero escritor Blogger.

Nunca imprimir IDs de contas, credenciais, URLs completas, produtos ou erros brutos.
Resultado de consulta GraphQL recusada NAO e considerado sucesso de atualizacao.
"""
from __future__ import annotations
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from replication_safe import GateError
from shopee_r2_safe import KEYWORDS, normalize, signed_query, trusted

CATEGORY = "Tecnologia"
KEYWORD = "mouse"


def strict_eligible(raw: dict) -> dict | None:
    try:
        item_id = str(raw.get("itemId", ""))
        title = str(raw.get("productName", "")).strip()
        link = str(raw.get("offerLink", ""))
        image = str(raw.get("imageUrl", ""))
        price = Decimal(str(raw.get("priceMin", "")))
        rating_value = raw.get("ratingStar")
        rating = Decimal(str(rating_value)) if rating_value is not None else None
        if not item_id.isdigit() or not (12 <= len(title) <= 190):
            return None
        if not trusted(link, affiliate=True) or not trusted(image, affiliate=False):
            return None
        if not price.is_finite() or not (Decimal("1") <= price <= Decimal("100000")):
            return None
        if rating is not None and (not rating.is_finite() or rating < Decimal("4")):
            return None
        if not any(re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", title.casefold())
                   for w in KEYWORDS[CATEGORY]):
            return None
        return {"item_id": item_id, "shop_id": str(raw.get("shopId", ""))}
    except (InvalidOperation, TypeError, ValueError):
        return None


def selected_count(candidates: list[dict], shop_cap: int) -> int:
    seen, shops = set(), {}
    count = 0
    for p in candidates:
        item_id = p["item_id"]
        shop_id = p["shop_id"]
        if item_id in seen:
            continue
        if shop_id and shops.get(shop_id, 0) >= shop_cap:
            continue
        count += 1
        seen.add(item_id)
        if shop_id:
            shops[shop_id] = shops.get(shop_id, 0) + 1
        if count >= 4:
            break
    return count


def main() -> int:
    app = os.environ.get("SHOPEE_APP_ID", "").strip()
    secret = os.environ.get("SHOPEE_SECRET", "").strip()
    baseline = {"kind": "SHOPEE_FILTERS_LIVE_READ_ONLY", "writes_blogger": False,
                "calls_shopee": 1, "full_store_update_attempted": False,
                "category": CATEGORY, "keyword": KEYWORD}
    if not app.isdigit() or not secret:
        print(json.dumps({**baseline, "status": "CREDENTIALS_UNAVAILABLE"}, ensure_ascii=False))
        return 2
    try:
        nodes = signed_query(KEYWORD, app, secret)
    except GateError:
        print(json.dumps({**baseline, "status": "API_BLOCKED_NO_UPDATE",
                          "strict_selected": 0, "relaxed_selected": 0}, ensure_ascii=False))
        return 0
    except Exception:
        print(json.dumps({**baseline, "status": "UNEXPECTED_QUERY_FAILURE_NO_UPDATE"}, ensure_ascii=False))
        return 2
    strict = [p for raw in nodes if (p := strict_eligible(raw))]
    relaxed = [p for raw in nodes if (p := normalize(raw, CATEGORY))]
    print(json.dumps({**baseline, "status": "API_NODES_RECEIVED_NO_UPDATE",
                      "received_nodes": len(nodes),
                      "strict_eligible": len(strict), "relaxed_eligible": len(relaxed),
                      "strict_selected": selected_count(strict, 2),
                      "relaxed_selected": selected_count(relaxed, 4)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
