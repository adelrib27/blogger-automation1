import json
import os

from affiliate_hub_v31.reuse_policy import can_queue_reuse
from affiliate_hub_v31.queue_identity import highest_reserved_id
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "oficina_garagem" / "data" / "shopee_oportunidades" / "intent_report.json"
RANKING = ROOT / "oficina_garagem" / "data" / "shopee_oportunidades" / "ranking.json"
CONFIG = ROOT / "oficina_garagem" / "config" / "shopee_oportunidades.json"
OUT = ROOT / "oficina_garagem" / "data" / "editorial_queue.json"
HISTORY = ROOT / "oficina_garagem" / "data" / "publication_history.json"
MAX_PER_KEYWORD = 1
REUSE_ENABLED = os.environ.get('V31_EDITORIAL_PRODUCT_REUSE_ENABLED', 'false').lower() == 'true'

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


def load(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


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
        "Manutencao": "Manutenção",
        "Acessorios Automotivos": "Acessórios Automotivos",
        "Organizacao de Garagem": "Organização de Garagem",
        "Limpeza e Conservacao": "Limpeza e Conservação",
        "Seguranca e Protecao": "Segurança e Proteção",
    }.get(raw, raw)


def keyword_label(keyword):
    return KEYWORD_LABELS.get(norm(keyword), str(keyword).strip().capitalize())


def ranking_details():
    if not RANKING.exists():
        return {}
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
    fingerprints = set()
    for row in rows or []:
        item_id = str(row.get("shopee_item_id") or "").strip()
        if item_id:
            ids.add(item_id)
        fingerprint = product_fingerprint(row.get("product"))
        if fingerprint:
            fingerprints.add(fingerprint)
    return ids, fingerprints


def main():
    if not REPORT.exists():
        raise SystemExit(f"Relatório Shopee ausente: {REPORT}")
    report, config = load(REPORT, {}), load(CONFIG, {})
    details = ranking_details()
    mapping = category_map(config)
    published_ids, published_fingerprints = publication_memory()
    history_doc = load(HISTORY, {'items': []})
    old_queue = load(OUT, {'items': []}) if REUSE_ENABLED else {'items': []}
    next_id = highest_reserved_id(OUT,ROOT / "oficina_garagem" / "data" / "generated") if REUSE_ENABLED else 0
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
        reuse_candidate = False
        prior_titles = []
        if item_id in published_ids:
            if REUSE_ENABLED:
                reuse_candidate, prior_titles = can_queue_reuse(history_doc, item_id)
            if not reuse_candidate:
                skipped["produto_ja_publicado"] += 1
                continue
        if item_id in seen_ids:
            skipped["item_id_duplicado"] += 1
            continue
        fingerprint = product_fingerprint(product)
        other_fingerprints = ({product_fingerprint(row.get("product")) for row in history_doc.get("items") or []
                               if str(row.get("shopee_item_id") or "") != item_id}
                              if reuse_candidate else published_fingerprints)
        if fingerprint and fingerprint in other_fingerprints:
            skipped["produto_semelhante_ja_publicado"] += 1
            continue
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

        detail = details.get(item_id) or {}
        image_url = str(detail.get("imageUrl") or "").strip()
        if image_url and not image_url.startswith("https://"):
            image_url = ""

        category = display_category(raw_category)
        if REUSE_ENABLED:
            next_id += 1
        items.append({
            "id": next_id if REUSE_ENABLED else len(items) + 1,
            "shopee_item_id": item_id,
            "product": product,
            "affiliate_link": link,
            "image_url": image_url,
            "shop_name": row.get("shopName"),
            "source_keyword": keyword,
            "editorial_label": keyword_label(keyword),
            "category": category,
            "opportunity_score": row.get("opportunityScore"),
            "priority_tier": row.get("priorityTier"),
            "status": "PENDING",
            "reuse_candidate": reuse_candidate,
            "prior_publication_count": len(prior_titles) if reuse_candidate else 0,
            "prior_titles": prior_titles if reuse_candidate else [],
            "rules": {
                "no_fake_testing": True,
                "no_invented_specs": True,
                "publication_requires_gate": True,
                "safety_review": category == "Segurança e Proteção",
                "single_editorial_title": True,
            },
        })
        seen_ids.add(item_id)
        if fingerprint:
            seen_products.add(fingerprint)
        keyword_counts[keyword_key] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "version": 6,
        "project": "Oficina & Garagem",
        "source": "Shopee intent_report v2.3 + ranking details + publication history",
        "editorial_policy": "produto real -> um único título editorial -> conteúdo útil -> CTA contextual -> gate -> publicação",
        "max_per_keyword": MAX_PER_KEYWORD,
        "total": len(items),
        "skipped": dict(skipped),
        "items": items,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fila criada: {OUT} | itens={len(items)} | descartes={dict(skipped)}")
    if not items:
        raise SystemExit("Nenhum item elegível para a fila editorial.")


if __name__ == "__main__":
    main()
