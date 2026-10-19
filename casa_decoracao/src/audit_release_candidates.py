import json
from pathlib import Path

from category_rotation import load_state
from quality_gate import quality

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "casa_decoracao" / "data" / "editorial_queue.json"
GENERATED = ROOT / "casa_decoracao" / "data" / "generated"
ROTATION = ROOT / "casa_decoracao" / "data" / "category_rotation.json"
HISTORY = ROOT / "casa_decoracao" / "data" / "publication_history.json"
OUT = ROOT / "casa_decoracao" / "data" / "release_audit.json"


def load(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def main():
    doc = load(QUEUE, {})
    rotation = load_state(ROTATION)
    history = load(HISTORY, {"items": []})
    rows = []
    for item in doc.get("items") or []:
        path = GENERATED / f"{int(item.get('id') or 0):03d}.json"
        article = load(path, {}) if path.exists() else {}
        gate = quality(article) if article else {
            "status": "NOT_GENERATED", "reasons": ["arquivo_gerado_ausente"], "warnings": [], "metrics": {}
        }
        rows.append({
            "id": item.get("id"),
            "shopee_item_id": item.get("shopee_item_id"),
            "category": item.get("category"),
            "product": item.get("product"),
            "queue_status": item.get("status"),
            "wordpress_post_id": item.get("wordpress_post_id"),
            "gate": gate,
        })
    summary = {
        "total": len(rows),
        "draft_ready": sum(r["gate"]["status"] == "DRAFT_READY" for r in rows),
        "rejected": sum(r["gate"]["status"] == "REJECTED" for r in rows),
        "not_generated": sum(r["gate"]["status"] == "NOT_GENERATED" for r in rows),
        "published_history": len(history.get("items") or []),
        "rotation_cycle": rotation.get("cycle"),
        "rotation_pending": rotation.get("pending_categories"),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "project": "Casa e Decoração",
        "policy_version": 3,
        "summary": summary,
        "items": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
