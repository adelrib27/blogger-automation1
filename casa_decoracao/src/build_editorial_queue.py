import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from category_rotation import CATEGORY_ORDER, load_state, order_items

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "casa_decoracao" / "data" / "shopee_oportunidades" / "intent_report.json"
RANKING = ROOT / "casa_decoracao" / "data" / "shopee_oportunidades" / "ranking.json"
CONFIG = ROOT / "casa_decoracao" / "config" / "shopee_oportunidades.json"
OUT = ROOT / "casa_decoracao" / "data" / "editorial_queue.json"
HISTORY = ROOT / "casa_decoracao" / "data" / "publication_history.json"
ROTATION = ROOT / "casa_decoracao" / "data" / "category_rotation.json"
MAX_PER_KEYWORD = 1

CATEGORY_DISPLAY = {
    "Decoracao": "Decoração",
    "Organizacao": "Organização",
    "Sala": "Sala",
    "Quarto": "Quarto",
    "Cozinha": "Cozinha",
    "Banheiro": "Banheiro",
    "Area Externa": "Área Externa",
    "Cama Mesa Banho": "Cama, Mesa e Banho",
}


def load(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def norm(value):
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


def product_fingerprint(value):
    value = norm(value)
    value = re.sub(r"\b\d+(?:[.,]\d+)?(?:v|w|mah|ah|mm|cm|m|kg|g|l|ml|pecas)?\b", " ", value)
    noise = {
        "oferta", "premium", "profissional", "original", "novo", "nova", "super", "mega", "kit",
        "frete", "gratis", "pronta", "entrega", "casa", "decoracao",
    }
    tokens = [t for t in value.split() if t not in noise]
    return " ".join(tokens[:18])


def token_similarity(a, b):
    sa = set(product_fingerprint(a).split())
    sb = set(product_fingerprint(b).split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(1, min(len(sa), len(sb)))


def category_map(config):
    out = {}
    for raw_category, keywords in (config.get("categories") or {}).items():
        display = CATEGORY_DISPLAY.get(raw_category)
        if not display:
            continue
        for keyword in keywords:
            out[norm(keyword)] = display
    return out


def ranking_details():
    doc = load(RANKING, {})
    rows = doc.get("ranking") if isinstance(doc, dict) else []
    out = {}
    for row in rows or []:
        item_id = str(row.get("itemId") or "").strip()
        if item_id:
            out[item_id] = row
    return out


def publication_memory():
    doc = load(HISTORY, {"items": []})
    rows = doc.get("items") if isinstance(doc, dict) else []
    ids = set()
    products = []
    for row in rows or []:
        item_id = str(row.get("shopee_item_id") or "").strip()
        if item_id:
            ids.add(item_id)
        product = str(row.get("product") or "").strip()
        if product:
            products.append(product)
    return ids, products


def previous_state():
    doc = load(OUT, {"items": []})
    rows = doc.get("items") if isinstance(doc, dict) else []
    by_item = {}
    max_id = 0
    for row in rows or []:
        try:
            max_id = max(max_id, int(row.get("id") or 0))
        except (TypeError, ValueError):
            pass
        item_id = str(row.get("shopee_item_id") or "").strip()
        if item_id:
            by_item[item_id] = row
    return by_item, max_id


def main():
    if not REPORT.exists():
        raise SystemExit(f"Relatório Shopee ausente: {REPORT}")

    report = load(REPORT, {})
    config = load(CONFIG, {})
    details = ranking_details()
    mapping = category_map(config)
    published_ids, published_products = publication_memory()
    previous, next_id = previous_state()
    rotation = load_state(ROTATION)

    items = []
    seen_ids = set()
    seen_products = []
    keyword_counts = Counter()
    skipped = Counter()

    for row in report.get("ranking") or []:
        item_id = str(row.get("itemId") or "").strip()
        product = str(row.get("productName") or "").strip()
        link = str(row.get("offerLink") or "").strip()
        keywords = [str(x).strip() for x in (row.get("intentMatchedKeywords") or []) if str(x).strip()]
        if not item_id or not product or not link.startswith("https://") or not keywords:
            skipped["incompleto"] += 1
            continue
        if item_id in published_ids:
            skipped["produto_ja_publicado"] += 1
            continue
        if item_id in seen_ids:
            skipped["item_id_duplicado"] += 1
            continue
        if any(token_similarity(product, old) >= 0.82 for old in published_products):
            skipped["produto_semelhante_ja_publicado"] += 1
            continue
        if any(token_similarity(product, old) >= 0.88 for old in seen_products):
            skipped["produto_quase_duplicado"] += 1
            continue

        keyword = keywords[0]
        keyword_key = norm(keyword)
        if keyword_counts[keyword_key] >= MAX_PER_KEYWORD:
            skipped["limite_por_intencao"] += 1
            continue
        category = mapping.get(keyword_key, "")
        if category not in CATEGORY_ORDER:
            skipped["categoria_nao_mapeada"] += 1
            continue

        detail = details.get(item_id) or {}
        image_url = str(detail.get("imageUrl") or "").strip()
        if not image_url.startswith("https://"):
            skipped["imagem_invalida"] += 1
            continue

        old = previous.get(item_id) or {}
        if old:
            stable_id = int(old.get("id") or 0)
            if stable_id <= 0:
                next_id += 1
                stable_id = next_id
        else:
            next_id += 1
            stable_id = next_id

        item = {
            "id": stable_id,
            "shopee_item_id": item_id,
            "product": product,
            "affiliate_link": link,
            "image_url": image_url,
            "shop_name": row.get("shopName"),
            "source_keyword": keyword,
            "category": category,
            "opportunity_score": row.get("opportunityScore"),
            "priority_tier": row.get("priorityTier"),
            "status": str(old.get("status") or "PENDING"),
            "rules": {
                "no_fake_testing": True,
                "no_invented_specs": True,
                "publication_requires_gate": True,
                "single_editorial_title": True,
                "category_rotation_required": True,
            },
        }
        for field in (
            "topic", "editorial_title", "quality", "last_error", "generation_attempts",
            "publication_attempts", "wordpress_post_id", "wordpress_url", "featured_media", "seo_synced",
        ):
            if field in old:
                item[field] = old[field]
        items.append(item)
        seen_ids.add(item_id)
        seen_products.append(product)
        keyword_counts[keyword_key] += 1

    # Rotação é prioridade editorial: categorias ainda pendentes vêm antes das já cobertas no ciclo.
    items = order_items(items, rotation, pending_only=False)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "version": 3,
        "project": "Casa e Decoração",
        "source": "Shopee intent_report v2.3 + ranking details + publication history",
        "editorial_policy": "produto real -> rotação entre 8 categorias -> título editorial -> Qwen3 -> CTA contextual -> imagem real -> gate -> publicação",
        "category_rotation_cycle": rotation.get("cycle"),
        "category_rotation_pending": rotation.get("pending_categories"),
        "max_per_keyword": MAX_PER_KEYWORD,
        "total": len(items),
        "skipped": dict(skipped),
        "items": items,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Fila Casa criada: itens={len(items)} | ciclo={rotation.get('cycle')} | pendentes={rotation.get('pending_categories')} | descartes={dict(skipped)}")
    if not items:
        raise SystemExit("Nenhum item elegível para a fila editorial do Casa e Decoração.")


if __name__ == "__main__":
    main()
