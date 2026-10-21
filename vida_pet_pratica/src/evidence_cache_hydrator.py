import json
from pathlib import Path

import d1_persistence as base

LAB_ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = LAB_ROOT / "state" / "evidence_cache.json"


def _loads(raw, default):
    try:
        return json.loads(raw or "")
    except Exception:
        return default


def hydrate_evidence_cache():
    products = base.rows(
        """
        SELECT item_id,product_name,evidence_status,evidence_checked_at,source_payload_json
        FROM editorial_products
        WHERE evidence_status='VERIFIED'
        ORDER BY item_id
        """
    )
    cache = {}
    source_count = 0
    for product in products:
        item_id = str(product.get("item_id") or "").strip()
        if not item_id:
            continue
        sources = []
        for row in base.rows(
            """
            SELECT evidence_id,identity_level,allowed_in_article,source_url,source_title,source_type,claim_text,checked_at,payload_json
            FROM editorial_evidence
            WHERE item_id=?
            ORDER BY checked_at DESC,evidence_id
            """,
            [item_id],
        ):
            payload = _loads(row.get("payload_json"), {})
            if not isinstance(payload, dict):
                payload = {}
            source = {
                "evidence_id": row.get("evidence_id") or payload.get("evidence_id"),
                "identity_level": row.get("identity_level") or payload.get("identity_level") or "UNKNOWN",
                "source_url": row.get("source_url") or payload.get("source_url") or "",
                "source_domain": row.get("source_type") or payload.get("source_domain") or "",
                "source_title": row.get("source_title") or payload.get("source_title") or "",
                "support_text": row.get("claim_text") or payload.get("support_text") or "",
                "allowed_in_article": bool(int(row.get("allowed_in_article") or 0)),
                "confidence": payload.get("confidence"),
                "reason": payload.get("reason") or "Persisted evidence from D1",
                "checked_at": row.get("checked_at"),
            }
            sources.append(source)
            source_count += 1
        source_payload = _loads(product.get("source_payload_json"), {})
        cache[item_id] = {
            "status": str(product.get("evidence_status") or ""),
            "evidence_checked_at": product.get("evidence_checked_at"),
            "product": {
                "itemId": item_id,
                "productName": product.get("product_name") or source_payload.get("productName") or "",
            },
            "source_payload": source_payload if isinstance(source_payload, dict) else {},
            "sources": sources,
        }
    base.save_json(CACHE_PATH, cache)
    print(json.dumps({
        "status": "D1_EVIDENCE_CACHE_HYDRATED",
        "products": len(cache),
        "sources": source_count,
        "wordpress_written": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    hydrate_evidence_cache()
