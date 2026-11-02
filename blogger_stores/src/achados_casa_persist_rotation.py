#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from achados_casa_publish_post import validate_selection

ROOT = Path(__file__).resolve().parents[2]
SELECTION_PATH = ROOT / "blogger_stores" / "data" / "achados_casa_selection.json"
HISTORY_PATH = ROOT / "blogger_stores" / "data" / "achados_casa_rotation.json"
BLOG_ID = "1426630233929943394"


def load(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def signature(items: list[dict]) -> tuple[str, ...]:
    return tuple(sorted(str(item.get("itemId") or "") for item in items))


def main() -> int:
    selection = load(SELECTION_PATH, {})
    validate_selection(selection)
    categories = selection.get("categories") or {}
    items = [
        {"category": category, "itemId": str(product.get("itemId") or "")}
        for category, products in categories.items()
        for product in products
    ]
    if len(items) != 20 or len(set(item["itemId"] for item in items)) != 20:
        raise RuntimeError("Persistência bloqueada: seleção não possui 20 IDs únicos.")

    history = load(HISTORY_PATH, {"version": 1, "blogId": BLOG_ID, "runs": []})
    if str(history.get("blogId") or BLOG_ID) != BLOG_ID:
        raise RuntimeError("Persistência bloqueada: histórico pertence a outro blog.")
    history["version"] = 1
    history["blogId"] = BLOG_ID
    runs = list(history.get("runs") or [])
    if runs:
        last = runs[-1]
        if str(last.get("source") or "") == "blogger_published" and signature(last.get("items") or []) == signature(items):
            print("ACHADOS_CASA_ROTATION_NOOP: seleção já registrada como última publicação.")
            return 0

    runs.append({
        "timestamp": datetime.now(ZoneInfo("America/Recife")).isoformat(),
        "source": "blogger_published",
        "selectionSchemaVersion": int(selection.get("schemaVersion") or 0),
        "items": items,
    })
    history["runs"] = runs[-120:]
    save_atomic(HISTORY_PATH, history)
    print("ACHADOS_CASA_ROTATION_PERSIST_PASS: 20 produtos registrados após validação pública.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
