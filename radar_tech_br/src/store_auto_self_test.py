#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ["RADAR_STORE_DRY_RUN"] = "true"
sys.path.insert(0, str(ROOT / "radar_tech_br" / "src"))
import store_auto as s  # noqa: E402


def product(i, category):
    return {
        "itemId": str(i),
        "productName": f"Produto teste {i} {category}",
        "offerLink": f"https://s.shopee.com.br/teste{i}",
        "imageUrl": f"https://img.test/{i}.jpg",
        "priceMin": 10 + i,
        "priceMax": 10 + i,
        "shopName": f"Loja {i}",
        "categories": [category],
    }


ranking = []
idx = 1
for key, _, _ in s.CATEGORY_SPECS:
    for _ in range(8):
        ranking.append(product(idx, key))
        idx += 1

chosen = s.choose_products(ranking, {"version": 1, "runs": []})
assert len(chosen) == 5
assert all(len(v) == 4 for v in chosen.values())
ids = [p["itemId"] for values in chosen.values() for p in values]
assert len(ids) == 20
assert len(set(ids)) == 20

block = s.render_store_block(chosen)
s.validate_shape(chosen, block)
assert block.count('rel="nofollow sponsored noopener"') == 20
assert block.count("data-item-id=") == 20
assert s.START_MARKER in block and s.END_MARKER in block
assert "Moda &amp; beleza" in block or "Moda & beleza" in block

history = {
    "version": 1,
    "runs": [{
        "timestamp": s.now_sp().isoformat(),
        "items": [
            {"category": category, "itemId": p["itemId"]}
            for category, values in chosen.items()
            for p in values
        ],
    }],
}
chosen2 = s.choose_products(ranking, history)
ids2 = {p["itemId"] for values in chosen2.values() for p in values}
assert not (set(ids) & ids2), "Rodízio recente falhou com pool 8/categoria."

try:
    s.choose_products(ranking[:3], {"version": 1, "runs": []})
    raise AssertionError("Deveria falhar com seleção incompleta.")
except RuntimeError:
    pass

assert s.brl(1234.5) == "R$ 1.234,50"
assert s.price_label({"priceMin": 99.9, "priceMax": 120}) == "A partir de R$ 99,90"
print("store_auto_self_test: 10/10 OK")
