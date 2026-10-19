import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
LEGACY_QUEUE = ROOT / "data" / "fase3" / "fila_dia.json"
OUT = ROOT / "radar_tech_br" / "data" / "editorial_queue.json"
LOCAL_TZ = ZoneInfo("America/Sao_Paulo")
ALLOWED_CATEGORIES = {
    "Tecnologia",
    "Casa & Decoração",
    "Cozinha & Utilidades",
    "Ferramentas & Automotivo",
    "Moda & Beleza",
}


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    target = os.getenv("RADAR_TARGET_SLOT", "").strip()
    if not target:
        raise SystemExit("RADAR_TARGET_SLOT ausente")

    queue = load(LEGACY_QUEUE, {})
    today = datetime.now(LOCAL_TZ).date().isoformat()
    if not queue:
        raise SystemExit("Fila diária do Radar ausente")
    if queue.get("project") != "Radar Tech BR":
        raise SystemExit("Fila pertence a outro projeto")
    if queue.get("date") != today:
        raise SystemExit(f"Fila desatualizada: {queue.get('date')} != {today}")
    if queue.get("complete") is not True:
        raise SystemExit("Fila diária incompleta; publicação bloqueada")
    slots = queue.get("slots") or []
    categories = {str(slot.get("category") or "") for slot in slots}
    if len(slots) != 5 or categories != ALLOWED_CATEGORIES:
        raise SystemExit("Fila inválida: esperado exatamente um slot para cada uma das cinco categorias")

    selected = next((slot for slot in slots if str(slot.get("time") or "") == target), None)
    if not selected:
        raise SystemExit(f"Slot inexistente na fila: {target}")
    if selected.get("status") == "PUBLICADO":
        raise SystemExit(f"Slot {target} já publicado hoje")

    product = selected.get("product") or {}
    required = {
        "itemId": product.get("itemId"),
        "productName": product.get("productName"),
        "offerLink": product.get("offerLink"),
        "imageUrl": product.get("imageUrl"),
        "category": selected.get("category"),
        "keyword": selected.get("keyword"),
    }
    missing = [name for name, value in required.items() if not str(value or "").strip()]
    if missing:
        raise SystemExit("Slot incompleto: " + ", ".join(missing))
    if not str(product.get("offerLink")).startswith("https://"):
        raise SystemExit("Link de afiliado inválido")
    if not str(product.get("imageUrl")).startswith("https://"):
        raise SystemExit("Imagem Shopee inválida")

    item = {
        "id": 1,
        "slot": target,
        "shopee_item_id": str(product.get("itemId")),
        "product": str(product.get("productName")).strip(),
        "affiliate_link": str(product.get("offerLink")).strip(),
        "image_url": str(product.get("imageUrl")).strip(),
        "shop_name": str(product.get("shopName") or "").strip(),
        "source_keyword": str(selected.get("keyword") or "").strip(),
        "category": str(selected.get("category") or "").strip(),
        "opportunity_score": product.get("opportunityScore"),
        "priority_tier": product.get("priorityTier"),
        "status": "PENDING",
        "rules": {
            "no_fake_testing": True,
            "no_invented_specs": True,
            "publication_requires_gate": True,
            "single_editorial_title": True,
            "featured_image_required": True,
        },
    }
    doc = {
        "version": 1,
        "project": "Radar Tech BR",
        "source": "data/fase3/fila_dia.json",
        "date": today,
        "target_slot": target,
        "total": 1,
        "items": [item],
    }
    save(OUT, doc)
    print(f"Slot preparado: {target} | {item['category']} | itemId={item['shopee_item_id']}")


if __name__ == "__main__":
    main()
