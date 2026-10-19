import json
from pathlib import Path

CATEGORY_ORDER = [
    "Decoração",
    "Organização",
    "Sala",
    "Quarto",
    "Cozinha",
    "Banheiro",
    "Área Externa",
    "Cama, Mesa e Banho",
]


def initial_state():
    return {
        "version": 1,
        "project": "Casa e Decoração",
        "cycle": 1,
        "order": list(CATEGORY_ORDER),
        "pending_categories": list(CATEGORY_ORDER),
        "last_published_category": "",
    }


def normalize_state(state):
    if not isinstance(state, dict):
        return initial_state()
    order = [x for x in state.get("order") or [] if x in CATEGORY_ORDER]
    if set(order) != set(CATEGORY_ORDER) or len(order) != len(CATEGORY_ORDER):
        order = list(CATEGORY_ORDER)
    pending = [x for x in state.get("pending_categories") or [] if x in order]
    # Empty pending means a completed cycle persisted between runs: start a new one.
    if not pending:
        pending = list(order)
        state["cycle"] = max(1, int(state.get("cycle") or 1)) + 1
    state["version"] = 1
    state["project"] = "Casa e Decoração"
    state["order"] = order
    state["pending_categories"] = pending
    state.setdefault("last_published_category", "")
    state["cycle"] = max(1, int(state.get("cycle") or 1))
    return state


def load_state(path):
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = initial_state()
    return normalize_state(data)


def save_state(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalize_state(state), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pending_categories(state):
    return list(normalize_state(dict(state)).get("pending_categories") or [])


def priority_key(item, state):
    category = str(item.get("category") or "")
    pending = pending_categories(state)
    order = list(state.get("order") or CATEGORY_ORDER)
    if category in pending:
        bucket = 0
        index = pending.index(category)
    elif category in order:
        bucket = 1
        index = order.index(category)
    else:
        bucket = 2
        index = 999
    score = item.get("opportunity_score")
    try:
        score = float(score)
    except (TypeError, ValueError):
        score = 0.0
    return (bucket, index, -score, int(item.get("id") or 0))


def order_items(items, state, pending_only=False):
    pending = set(pending_categories(state))
    rows = [item for item in items if not pending_only or str(item.get("category") or "") in pending]
    return sorted(rows, key=lambda item: priority_key(item, state))


def mark_published(state, category):
    state = normalize_state(dict(state))
    category = str(category or "")
    pending = state["pending_categories"]
    if category not in pending:
        raise RuntimeError(f"categoria fora do ciclo pendente: {category}")
    pending.remove(category)
    state["last_published_category"] = category
    if not pending:
        state["cycle"] += 1
        state["pending_categories"] = list(state["order"])
    return state


def self_test():
    s = initial_state()
    assert pending_categories(s) == CATEGORY_ORDER
    s = mark_published(s, "Decoração")
    assert s["pending_categories"][0] == "Organização"
    for category in CATEGORY_ORDER[1:]:
        s = mark_published(s, category)
    assert s["cycle"] == 2
    assert s["pending_categories"] == CATEGORY_ORDER
    rows = [
        {"id": 1, "category": "Cozinha", "opportunity_score": 90},
        {"id": 2, "category": "Decoração", "opportunity_score": 10},
        {"id": 3, "category": "Organização", "opportunity_score": 70},
    ]
    assert [r["category"] for r in order_items(rows, initial_state(), pending_only=True)] == [
        "Decoração", "Organização", "Cozinha"
    ]
    return True


if __name__ == "__main__":
    self_test()
    print("Category rotation Casa e Decoração: OK")
