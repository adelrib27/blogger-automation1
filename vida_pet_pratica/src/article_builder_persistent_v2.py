import os

import article_builder_v1 as builder
import automation_core_persistent_v2 as persistent_core


def persistent_candidate_from_item(item, history, max_similarity, max_results):
    item_id = str(item.get("itemId") or "")
    if os.getenv("VIDAPET_FORCE_EVERGREEN", "").strip() == "1":
        return None, {
            "itemId": item_id,
            "stage": "EVERGREEN_QUEUE_EXHAUSTED",
            "reasons": ["persistent_evergreen_queue_exhausted"],
        }
    known_ids = {str(row.get("itemId") or "") for row in persistent_core.known_products(history)}
    if item_id in known_ids:
        return None, {
            "itemId": item_id,
            "stage": "KNOWN_PRODUCT_DEFERRED",
            "reasons": ["new_products_first"],
        }
    return persistent_core.candidate_from_item(
        item,
        history,
        max_similarity,
        max_results,
        status="VERIFIED_READY_CANDIDATE",
        angle_status_prefix="NEW_PRODUCT_FAILOVER_",
    )


builder.candidate_from_item = persistent_candidate_from_item

# SAFE Builder V5 aplica prompt, sanitização, Fact/Quality Gate e anti-duplicação,
# e chama builder.main() ao ser importado.
import article_builder_safe_v5  # noqa: E402,F401
