import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import automation

BASE_DIR = HERE.parent
CONFIG_PATH = BASE_DIR / "config.json"
OUTPUT_PATH = BASE_DIR / "data" / "batch_10_products.json"
STATE_PATH = BASE_DIR / "data" / "state.json"


def main():
    config = automation.load_json(CONFIG_PATH, {})
    state = automation.load_json(
        STATE_PATH,
        {"keyword_cursor": 0, "used_item_ids": [], "history": []},
    )
    used = {str(x) for x in state.get("used_item_ids", [])}
    min_rating = float(config.get("min_rating", 4.0))
    limit = max(10, min(int(config.get("shopee_limit", 20)), 50))

    pools = []
    seen = set(used)

    for group in config.get("query_groups") or []:
        label = str(group.get("label") or "").strip()
        group_candidates = []

        for keyword in group.get("keywords") or []:
            keyword = str(keyword or "").strip()
            if not keyword:
                continue

            print(f"Shopee API: {label} / {keyword}")
            products = automation.fetch_shopee_products(keyword, limit)

            for product in products:
                item_id = str(product.get("itemId") or "").strip()
                name = str(product.get("productName") or "").strip()
                link = str(product.get("offerLink") or "").strip()
                image = str(product.get("imageUrl") or "").strip()
                rating = automation.parse_float(product.get("ratingStar"))

                if not item_id or not name or not link or not image:
                    continue
                if item_id in seen:
                    continue
                if rating and rating < min_rating:
                    continue

                candidate = dict(product)
                candidate["category"] = label
                candidate["source_keyword"] = keyword
                candidate["score"] = round(automation.product_score(product), 4)
                group_candidates.append(candidate)
                seen.add(item_id)

        group_candidates.sort(key=lambda p: p.get("score", 0), reverse=True)
        pools.append(group_candidates)

    selected = []
    index = 0
    while len(selected) < 10:
        added = False
        for pool in pools:
            if index < len(pool):
                selected.append(pool[index])
                added = True
                if len(selected) >= 10:
                    break
        if not added:
            break
        index += 1

    if len(selected) < 10:
        raise RuntimeError(
            f"Foram encontrados apenas {len(selected)} produtos elegíveis; 10 são necessários."
        )

    payload = {
        "blog_id": str(config.get("blog_id") or ""),
        "blog_title": str(config.get("blog_title") or "Conecta Achados"),
        "count": len(selected),
        "products": selected,
    }
    automation.save_json(OUTPUT_PATH, payload)

    print("EXTRAÇÃO BATCH 10: PASSOU")
    for idx, product in enumerate(selected, start=1):
        print(
            f"{idx}. [{product.get('category')}] "
            f"{product.get('productName')} | itemId={product.get('itemId')}"
        )


if __name__ == "__main__":
    main()
