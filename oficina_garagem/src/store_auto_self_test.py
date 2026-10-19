#!/usr/bin/env python3
from __future__ import annotations

from datetime import timedelta
import store_auto as store


def product(category: str, index: int, *, price_min="10.00", price_max="10.00") -> dict:
    return {"itemId": f"{category.replace(' ', '')}-{index}", "productName": f"Produto teste {category} {index}", "shopName": f"Loja {index}", "priceMin": price_min, "priceMax": price_max, "offerLink": f"https://s.shopee.com.br/teste-{index}", "imageUrl": f"https://cf.shopee.com.br/file/teste-{index}-{category}", "categories": [category]}


def build_ranking(extra: int = 1) -> list[dict]:
    rows = []
    for key, _, _ in store.CATEGORY_SPECS:
        for i in range(1, store.ITEMS_PER_CATEGORY + extra + 1):
            rows.append(product(key, i))
    return rows


def assert_raises(fn, text: str) -> None:
    try:
        fn()
    except Exception as exc:
        assert text in str(exc), (text, str(exc))
    else:
        raise AssertionError(f"Era esperado erro contendo: {text}")


def main() -> None:
    tests = 0
    ranking = build_ranking()
    chosen = store.choose_products(ranking, {"version": 1, "runs": []})
    assert len(chosen) == 6 and all(len(v) == 4 for v in chosen.values()); tests += 1
    ids = [p["itemId"] for values in chosen.values() for p in values]
    assert len(ids) == len(set(ids)) == 24; tests += 1
    first_key = store.CATEGORY_SPECS[0][0]
    recent_id = ranking[0]["itemId"]
    history = {"version": 1, "runs": [{"timestamp": (store.now_local() - timedelta(hours=1)).isoformat(), "items": [{"category": first_key, "itemId": recent_id}]}]}
    rotated = store.choose_products(ranking, history)
    assert recent_id not in [p["itemId"] for p in rotated[first_key]][:4]; tests += 1
    block = store.render_store_block(chosen)
    assert block.count("data-item-id=") == 24 and block.count('rel="nofollow sponsored noopener"') == 24; tests += 1
    store.validate_shape(chosen, block); tests += 1
    assert store.price_label(product("Ferramentas", 90, price_min="145.20", price_max="145.20")) == "R$ 145,20"
    assert store.price_label(product("Ferramentas", 91, price_min="24.99", price_max="34.99")) == "A partir de R$ 24,99"; tests += 1
    good = product("Ferramentas", 1); assert store.valid_product(good)
    bad = dict(good); bad["priceMin"] = "0"; assert not store.valid_product(bad); tests += 1
    sample = "antes\n" + store.START_MARKER + "\nmiolo\n" + store.END_MARKER + "\ndepois"
    start, end = store.locate_region(sample); assert sample[start:end].startswith(store.START_MARKER) and sample[start:end].endswith(store.END_MARKER); tests += 1
    assert_raises(lambda: store.locate_region("sem marcadores"), "Marcadores da vitrine Oficina"); tests += 1
    short = []
    for key, _, _ in store.CATEGORY_SPECS:
        count = 3 if key == first_key else 4
        for i in range(1, count + 1): short.append(product(key, i))
    assert_raises(lambda: store.choose_products(short, {"version": 1, "runs": []}), "sem candidatos suficientes"); tests += 1
    duplicated = build_ranking()
    overlap = dict(duplicated[0]); overlap["categories"] = [first_key, store.CATEGORY_SPECS[1][0]]; duplicated.insert(0, overlap)
    selected = store.choose_products(duplicated, {"version": 1, "runs": []})
    selected_ids = [p["itemId"] for values in selected.values() for p in values]
    assert len(selected_ids) == len(set(selected_ids)); tests += 1
    assert block.count(store.START_MARKER) == 1 and block.count(store.END_MARKER) == 1; tests += 1
    print(f"Oficina store self-test: {tests}/{tests} OK")


if __name__ == "__main__":
    main()
