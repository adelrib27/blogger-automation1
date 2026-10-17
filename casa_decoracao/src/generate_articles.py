import html
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from quality_gate import (
    draft_quality,
    focus_keyword_from_item,
    meta_description_from_item,
    seo_title_from_item,
)

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "casa_decoracao" / "data" / "editorial_queue_100.json"
OUT_DIR = ROOT / "casa_decoracao" / "data" / "generated"
MODEL = os.getenv("CASA_AI_MODEL", "@cf/qwen/qwen3-30b-a3b-fp8").strip()
BATCH_SIZE = max(1, min(int(os.getenv("CASA_GENERATION_BATCH_SIZE", "5")), 20))
MAX_ITEM_ATTEMPTS = 3

HEALTH_SENSITIVE_TERMS = (
    "cervical",
    "ortopedico",
    "ortopédico",
    "terapeutico",
    "terapêutico",
)

UNSAFE_HEALTH_PATTERNS = (
    r"\balivia(?:r|m)?\s+(?:a\s+)?dor(?:es)?\b",
    r"\breduz(?:ir|em)?\s+(?:a\s+)?(?:dor|dores|press[aã]o)\b",
    r"\b(?:tratar|tratamento\s+(?:de|para))\s+(?:dor|dores|les[aã]o|h[ée]rnia)\b",
    r"\bprevine(?:m|r)?\s+(?:dor|dores|les[aã]o|problema)\b",
    r"\bcorrige(?:m|r)?\s+(?:a\s+)?postura\b",
    r"\bcontribui(?:r)?\s+para\s+(?:a\s+)?recupera[cç][aã]o\b",
    r"\bpress[aã]o\s+sobre\s+(?:os\s+)?m[uú]sculos\s+e\s+nervos\b",
)

CHEMICAL_SENSITIVE_TERMS = (
    "percarbonato",
    "tira-manchas",
    "tira manchas",
)


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cloudflare_config():
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    if not account_id or not token:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID/CLOUDFLARE_API_TOKEN ausentes")
    return account_id, token


def extract_text(payload):
    result = payload.get("result") if isinstance(payload, dict) else None
    if isinstance(result, dict):
        for key in ("response", "text", "output_text"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for choice in result.get("choices") or []:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message") or {}
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"].strip()
    return ""


def call_ai(prompt, retries=3):
    account_id, token = cloudflare_config()
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL}"
    body = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 8192,
        "temperature": 0.48,
    }, ensure_ascii=False).encode("utf-8")
    last_error = ""
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(endpoint, data=body, method="POST", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CasaEDecoracao-Editorial/2.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
            text = extract_text(payload)
            if text:
                return text
            last_error = "resposta vazia"
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        if attempt < retries:
            time.sleep(5 if attempt == 1 else 15)
    raise RuntimeError(f"falha na geração após {retries} tentativas: {last_error}")


def clean_html(text):
    text = str(text or "").strip()
    text = re.sub(r"^```(?:html)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    text = re.sub(r"</?(?:html|head|body)[^>]*>", "", text, flags=re.I)
    text = re.sub(r"<h1[^>]*>.*?</h1>", "", text, flags=re.I | re.S)
    return text.strip()


def word_count(content_html):
    text = re.sub(r"<[^>]+>", " ", content_html)
    return len(re.findall(r"\b[\wÀ-ÿ'-]+\b", text, flags=re.UNICODE))


def normalized_text(value):
    return str(value or "").casefold()


def is_health_sensitive(item):
    haystack = " ".join((normalized_text(item.get("topic")), normalized_text(item.get("product"))))
    return any(term in haystack for term in HEALTH_SENSITIVE_TERMS)


def is_chemical_sensitive(item):
    haystack = " ".join((normalized_text(item.get("topic")), normalized_text(item.get("product"))))
    return any(term in haystack for term in CHEMICAL_SENSITIVE_TERMS)


def unsafe_health_claims(content_html):
    plain = re.sub(r"<[^>]+>", " ", str(content_html or ""))
    plain = re.sub(r"\s+", " ", plain).casefold()
    return [pattern for pattern in UNSAFE_HEALTH_PATTERNS if re.search(pattern, plain, flags=re.I)]


def validate_health_safety(item, content_html):
    if is_health_sensitive(item) and unsafe_health_claims(content_html):
        raise RuntimeError("alegação de saúde não verificada detectada; regenerar em modo conforto/ergonomia")


def safety_guidance(item):
    blocks = []
    if is_health_sensitive(item):
        blocks.append("""
- TEMA SENSÍVEL DE SAÚDE/ERGONOMIA: trate o produto como item de conforto e preferência de uso.
- Não prometa alívio/tratamento de dor, correção de postura, prevenção, recuperação ou qualquer benefício clínico.
- Não recomende o produto para diagnóstico ou tratamento de condição médica.
- Não transforme o nome comercial “ortopédico” em evidência médica.
""")
    if is_chemical_sensitive(item):
        blocks.append("""
- TEMA DE LIMPEZA QUÍMICA: priorize segurança e instruções do rótulo/fabricante.
- Não ensine misturas com outros produtos químicos, não recomende ingestão/contato com pele e não invente concentração ou dosagem.
- Oriente teste em área discreta quando apropriado e cuidado com ventilação, armazenamento e incompatibilidades indicadas no rótulo.
""")
    return "\n".join(blocks)


def prompt_for(item):
    return f"""Você é editor sênior de um blog brasileiro de Casa e Decoração.
Escreva um artigo original, aprofundado e natural em português do Brasil.

PAUTA: {item['topic']}
PRODUTO RELACIONADO: {item['product']}
CATEGORIA: {item['category']}
PALAVRA-CHAVE PRINCIPAL: {focus_keyword_from_item(item)}

REGRAS OBRIGATÓRIAS:
- Produza aproximadamente 900 a 1300 palavras de conteúdo editorial útil.
- O assunto do texto deve permanecer diretamente relacionado à PAUTA e ao PRODUTO RELACIONADO; não troque o tipo de produto nem generalize para outro item.
- Não invente preço, desconto, estoque, entrega, potência, voltagem, autonomia, capacidade, material, dimensões, peso, garantia, compatibilidade, certificação, vendas ou desempenho do produto.
- Não diga que o produto foi testado fisicamente.
- Quando um dado específico não estiver confirmado, use linguagem prudente como “vale conferir no anúncio”.
- Separe orientação geral de características específicas do produto.
- Explique contexto de uso, para quem pode fazer sentido, limitações, erros comuns e o que conferir antes da compra.
- Evite exageros como “o melhor”, “imperdível”, “100% garantido”.
- Use a palavra-chave de forma natural; não faça repetição artificial.
- Foque exatamente na intenção da pauta para evitar canibalização.
- Não inclua H1.
- Use apenas <p>, <h2>, <h3>, <ul>, <li>, <strong> e <em> quando necessário.
- Crie pelo menos 4 seções H2 realmente diferentes entre si.
- NÃO inclua preço, botão, link ou CTA comercial. O sistema acrescentará o bloco afiliado depois.
- Não inclua comentários sobre estas instruções, markdown ou cercas de código.
{safety_guidance(item)}
Responda SOMENTE com o fragmento HTML do artigo.
"""


def expansion_prompt(item, draft_html):
    return f"""Reescreva e aprofunde o artigo abaixo para aproximadamente 900 a 1300 palavras, mantendo exatamente a mesma pauta e o mesmo produto.

PAUTA: {item['topic']}
PRODUTO RELACIONADO: {item['product']}
PALAVRA-CHAVE PRINCIPAL: {focus_keyword_from_item(item)}

Elimine repetições, acrescente critérios de comparação, contexto de uso, limitações, erros comuns e checklist final. Não inclua H1, links, preço ou CTA. Não afirme teste físico. Não invente especificações. Se um dado não estiver confirmado, diga para conferir o anúncio, ficha técnica ou manual.
{safety_guidance(item)}
RASCUNHO ATUAL:
{draft_html}

Responda SOMENTE com o fragmento HTML final, sem markdown.
"""


def category_slug(name):
    return {
        "Decoração": "decoracao",
        "Organização": "organizacao",
        "Sala": "sala",
        "Quarto": "quarto",
        "Cozinha": "cozinha",
        "Banheiro": "banheiro",
        "Área Externa": "area-externa",
        "Cama, Mesa e Banho": "cama-mesa-banho",
        "Iluminação": "iluminacao",
        "Limpeza e Utilidades": "limpeza-utilidades",
    }.get(name, "")


def build_article(item, raw_html):
    editorial = clean_html(raw_html)
    count = word_count(editorial)
    if count < 750:
        editorial = clean_html(call_ai(expansion_prompt(item, editorial)))
        count = word_count(editorial)
    if count < 700:
        raise RuntimeError(f"artigo ainda curto após expansão: {count} palavras")
    if "<h2" not in editorial.lower() or "<p" not in editorial.lower():
        raise RuntimeError("HTML sem estrutura editorial mínima")
    validate_health_safety(item, editorial)

    product = html.escape(str(item["product"]))
    link = html.escape(str(item["affiliate_link"]), quote=True)
    slug = category_slug(item.get("category"))
    category_link = (
        f'<p><a href="/category/{slug}/">Veja também outros guias de {html.escape(str(item["category"]))}</a>.</p>'
        if slug else ""
    )
    cta = f'''\n<div class="cd-produto-relacionado" style="margin:28px 0;padding:20px;border:1px solid #72eadb;border-radius:14px;background:#effffb;box-shadow:0 0 18px rgba(75,230,210,.20);">
<p><strong>Produto relacionado ao tema:</strong> {product}</p>
<p><a href="{link}" target="_blank" rel="nofollow sponsored" style="display:inline-block;padding:12px 18px;background:#19c6b3;color:#052f2c;text-decoration:none;font-weight:700;border-radius:10px;">Ver produto no TikTok Shop →</a></p>
<p><small>Link de afiliado. O site pode receber comissão em compras qualificadas, sem custo adicional para você. Preço, estoque, entrega e especificações devem ser confirmados na página do vendedor.</small></p>
</div>'''

    article = {
        **item,
        "seo_title": seo_title_from_item(item),
        "meta_description": meta_description_from_item(item),
        "focus_keyword": focus_keyword_from_item(item),
        "excerpt": meta_description_from_item(item),
        "editorial_html": editorial,
        "content_html": editorial + cta + category_link,
        "word_count": count,
        "generation_model": MODEL,
        "status": "GENERATED",
    }
    article["quality"] = draft_quality(article)
    if article["quality"]["status"] != "DRAFT_READY":
        raise RuntimeError("quality gate: " + ", ".join(article["quality"]["reasons"]))
    return article


def quarantine_existing_unsafe_health_articles(items_by_id):
    if not OUT_DIR.exists():
        return 0
    quarantined = 0
    for article_path in sorted(OUT_DIR.glob("*.json")):
        article = load_json(article_path, {})
        if not article or not is_health_sensitive(article):
            continue
        if not unsafe_health_claims(article.get("content_html")):
            continue
        item_id = int(article.get("id") or 0)
        current = items_by_id.get(item_id)
        if not current:
            continue
        current["status"] = "QUARANTINE"
        current["generation_attempts"] = 0
        current["last_error"] = "revisão automática: alegação de saúde não verificada; tentativas reiniciadas"
        try:
            article_path.unlink()
        except OSError:
            pass
        quarantined += 1
        print(f"QUARANTINE revisão saúde {item_id}: removido para regeneração segura")
    return quarantined


def recover_prompt_leakage_false_positives(items_by_id):
    recovered = 0
    for current in items_by_id.values():
        if current.get("status") != "BLOCKED":
            continue
        if str(current.get("last_error") or "").strip() != "quality gate: vazamento_de_prompt":
            continue
        current["status"] = "QUARANTINE"
        current["generation_attempts"] = 0
        current["last_error"] = "reprocessamento automático após correção do detector de vazamento de prompt"
        recovered += 1
    return recovered


def main():
    queue = load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    by_id = {int(x["id"]): x for x in items}

    recovered = recover_prompt_leakage_false_positives(by_id)
    if recovered:
        print(f"Recuperação do quality gate: {recovered} pauta(s) retornaram à quarentena para nova validação.")

    reviewed = quarantine_existing_unsafe_health_articles(by_id)
    if reviewed:
        print(f"Revisão preventiva: {reviewed} artigo(s) retornaram à quarentena.")

    candidates = [
        x for x in items
        if x.get("status") in {"PENDING", "QUARANTINE"}
        and int(x.get("generation_attempts") or 0) < MAX_ITEM_ATTEMPTS
    ][:BATCH_SIZE]
    if not candidates:
        queue["items"] = [by_id[int(x["id"])] for x in items]
        save_json(QUEUE_PATH, queue)
        print("Nenhuma pauta elegível para geração.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_count = 0

    for item in candidates:
        item_id = int(item["id"])
        current = by_id[item_id]
        current["generation_attempts"] = int(current.get("generation_attempts") or 0) + 1
        print(f"Gerando {item_id}: {item['topic']} | tentativa {current['generation_attempts']}")
        try:
            article = build_article(current, call_ai(prompt_for(current)))
            save_json(OUT_DIR / f"{item_id:03d}.json", article)
            current["status"] = "GENERATED"
            current["quality"] = article["quality"]
            current.pop("last_error", None)
            generated_count += 1
        except Exception as exc:
            if current["generation_attempts"] >= MAX_ITEM_ATTEMPTS:
                current["status"] = "BLOCKED"
            else:
                current["status"] = "QUARANTINE"
            current["last_error"] = str(exc)[:500]
            print(f"{current['status']} {item_id}: {exc}")

    queue["items"] = [by_id[int(x["id"])] for x in items]
    save_json(QUEUE_PATH, queue)
    print(f"Gerados: {generated_count}/{len(candidates)}")


if __name__ == "__main__":
    main()
