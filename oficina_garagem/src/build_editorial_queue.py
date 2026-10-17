import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "oficina_garagem" / "data" / "shopee_oportunidades" / "intent_report.json"
CONFIG = ROOT / "oficina_garagem" / "config" / "shopee_oportunidades.json"
OUT = ROOT / "oficina_garagem" / "data" / "editorial_queue.json"
MAX_PER_KEYWORD = 1

KEYWORD_LABELS = {
    "parafusadeira": "Parafusadeira",
    "furadeira": "Furadeira",
    "jogo de chaves": "Jogo de chaves",
    "jogo de soquetes": "Jogo de soquetes",
    "alicate universal": "Alicate universal",
    "multimetro digital": "Multímetro digital",
    "compressor de ar portatil": "Compressor de ar portátil",
    "torquimetro": "Torquímetro",
    "suporte celular carro": "Suporte de celular para carro",
    "aspirador automotivo": "Aspirador automotivo",
    "organizador porta malas": "Organizador de porta-malas",
    "painel ferramentas": "Painel para ferramentas",
    "caixa ferramentas": "Caixa de ferramentas",
    "estante metalica garagem": "Estante metálica para garagem",
    "maleta ferramentas": "Maleta de ferramentas",
    "pano microfibra automotivo": "Pano de microfibra automotivo",
    "escova limpeza automotiva": "Escova de limpeza automotiva",
    "lavadora alta pressao": "Lavadora de alta pressão",
    "oculos de protecao": "Óculos de proteção",
    "luva de protecao": "Luva de proteção",
    "protetor auricular": "Protetor auricular",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value):
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


def product_fingerprint(value):
    value = norm(value)
    value = re.sub(r"\b\d+(?:[.,]\d+)?(?:v|w|mah|ah|mm|cm|m|kg|g|l|ml|psi|bar|nm|pecas|peças)?\b", " ", value)
    noise = {"oferta", "premium", "profissional", "original", "novo", "super", "mega", "kit"}
    tokens = [t for t in value.split() if t not in noise]
    return " ".join(tokens[:18])


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


def keyword_label(keyword):
    return KEYWORD_LABELS.get(norm(keyword), str(keyword).strip().capitalize())


def topic_for(keyword, category):
    label = keyword_label(keyword)
    if category == "Segurança e Proteção":
        return f"{label}: o que verificar em especificações, certificações e adequação antes de comprar"
    if any(term in norm(keyword) for term in ("torquimetro", "multimetro", "compressor", "lavadora")):
        return f"{label}: critérios para comparar modelos sem assumir especificações não confirmadas"
    if category in {"Organização de Garagem", "Acessórios Automotivos"}:
        return f"{label}: o que medir e conferir para escolher um modelo adequado"
    return f"{label}: o que conferir antes de comprar e quais limitações considerar"


def main():
    if not REPORT.exists():
        raise SystemExit(f"Relatório Shopee ausente: {REPORT}")
    report, config = load(REPORT), load(CONFIG)
    mapping = category_map(config)
    items = []
    seen_ids = set()
    seen_products = set()
    keyword_counts = Counter()
    skipped = Counter()

    for row in report.get("ranking") or []:
        item_id = str(row.get("itemId") or "").strip()
        product = str(row.get("productName") or "").strip()
        link = str(row.get("offerLink") or "").strip()
        keywords = [str(x) for x in (row.get("intentMatchedKeywords") or []) if str(x).strip()]
        if not item_id or not product or not link.startswith("https://") or not keywords:
            skipped["incompleto"] += 1
            continue
        if item_id in seen_ids:
            skipped["item_id_duplicado"] += 1
            continue
        fingerprint = product_fingerprint(product)
        if fingerprint and fingerprint in seen_products:
            skipped["produto_quase_duplicado"] += 1
            continue
        keyword = keywords[0]
        keyword_key = norm(keyword)
        if keyword_counts[keyword_key] >= MAX_PER_KEYWORD:
            skipped["limite_por_intencao"] += 1
            continue
        raw_category = mapping.get(keyword_key, "")
        if not raw_category:
            skipped["categoria_nao_mapeada"] += 1
            continue
        category = display_category(raw_category)
        items.append({
            "id": len(items) + 1,
            "shopee_item_id": item_id,
            "product": product,
            "affiliate_link": link,
            "shop_name": row.get("shopName"),
            "source_keyword": keyword,
            "editorial_label": keyword_label(keyword),
            "category": category,
            "topic": topic_for(keyword, category),
            "opportunity_score": row.get("opportunityScore"),
            "priority_tier": row.get("priorityTier"),
            "status": "PENDING",
            "rules": {"no_fake_testing": True, "no_invented_specs": True, "draft_only": True, "safety_review": category == "Segurança e Proteção"}
        })
        seen_ids.add(item_id)
        if fingerprint:
            seen_products.add(fingerprint)
        keyword_counts[keyword_key] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "version": 4,
        "project": "Oficina & Garagem",
        "source": "Shopee intent_report v2.3",
        "max_per_keyword": MAX_PER_KEYWORD,
        "total": len(items),
        "skipped": dict(skipped),
        "items": items
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fila criada: {OUT} | itens={len(items)} | descartes={dict(skipped)}")
    if not items:
        raise SystemExit("Nenhum item elegível para a fila editorial.")


if __name__ == "__main__":
    main()
