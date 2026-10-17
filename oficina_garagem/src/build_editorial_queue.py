import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "oficina_garagem" / "data" / "shopee_oportunidades" / "intent_report.json"
CONFIG = ROOT / "oficina_garagem" / "config" / "shopee_oportunidades.json"
OUT = ROOT / "oficina_garagem" / "data" / "editorial_queue.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value):
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


def category_map(config):
    out = {}
    for category, keywords in (config.get("categories") or {}).items():
        for keyword in keywords:
            out[norm(keyword)] = category
    return out


def display_category(raw):
    return {
        "Manutencao": "Manutenção", "Acessorios Automotivos": "Acessórios Automotivos",
        "Organizacao de Garagem": "Organização de Garagem", "Limpeza e Conservacao": "Limpeza e Conservação",
        "Seguranca e Protecao": "Segurança e Proteção"
    }.get(raw, raw)


def topic_for(product, keyword, category):
    if category == "Segurança e Proteção":
        return f"{product}: o que verificar em especificações, certificações e adequação antes de comprar"
    if any(term in norm(keyword) for term in ("torquimetro", "multimetro", "compressor", "lavadora")):
        return f"{product}: critérios para comparar modelos sem assumir especificações não confirmadas"
    if category in {"Organização de Garagem", "Acessórios Automotivos"}:
        return f"{product}: o que medir e conferir para escolher um modelo adequado"
    return f"{product}: o que conferir antes de comprar e quais limitações considerar"


def main():
    if not REPORT.exists():
        raise SystemExit(f"Relatório Shopee ausente: {REPORT}")
    report, config = load(REPORT), load(CONFIG)
    mapping = category_map(config)
    items, seen = [], set()
    for row in report.get("ranking") or []:
        item_id = str(row.get("itemId") or "").strip()
        product = str(row.get("productName") or "").strip()
        link = str(row.get("offerLink") or "").strip()
        keywords = [str(x) for x in (row.get("intentMatchedKeywords") or []) if str(x).strip()]
        if not item_id or not product or not link.startswith("https://") or item_id in seen or not keywords:
            continue
        keyword = keywords[0]
        raw_category = mapping.get(norm(keyword), "")
        if not raw_category:
            continue
        category = display_category(raw_category)
        items.append({
            "id": len(items) + 1,
            "shopee_item_id": item_id,
            "product": product,
            "affiliate_link": link,
            "shop_name": row.get("shopName"),
            "source_keyword": keyword,
            "category": category,
            "topic": topic_for(product, keyword, category),
            "opportunity_score": row.get("opportunityScore"),
            "priority_tier": row.get("priorityTier"),
            "status": "PENDING",
            "rules": {"no_fake_testing": True, "no_invented_specs": True, "draft_only": True, "safety_review": category == "Segurança e Proteção"}
        })
        seen.add(item_id)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"version": 1, "project": "Oficina & Garagem", "source": "Shopee intent_report v2.3", "total": len(items), "items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fila criada: {OUT} | itens={len(items)}")
    if not items:
        raise SystemExit("Nenhum item elegível para a fila editorial.")


if __name__ == "__main__":
    main()
