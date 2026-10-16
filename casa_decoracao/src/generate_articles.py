import html
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "casa_decoracao" / "data" / "editorial_queue_100.json"
OUT_DIR = ROOT / "casa_decoracao" / "data" / "generated"
MODEL = os.getenv("CASA_AI_MODEL", "@cf/qwen/qwen3-30b-a3b-fp8").strip()
BATCH_SIZE = max(1, min(int(os.getenv("CASA_GENERATION_BATCH_SIZE", "5")), 20))
MAX_ITEM_ATTEMPTS = 3


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
        "temperature": 0.55,
    }, ensure_ascii=False).encode("utf-8")
    last_error = ""
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(endpoint, data=body, method="POST", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CasaEDecoracao-Editorial/1.1",
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


def title_from_topic(topic):
    title = str(topic or "").strip()
    if title:
        title = title[0].upper() + title[1:]
    if len(title) <= 60:
        return title
    short = title[:60].rsplit(" ", 1)[0]
    return short.rstrip(" -:;,")


def meta_from_item(item):
    topic = str(item.get("topic") or "").strip()
    product = str(item.get("product") or "").strip()
    base = f"{topic[:1].upper() + topic[1:]}: veja critérios práticos, pontos de atenção e o que conferir antes de escolher {product.lower()}."
    if len(base) <= 155:
        return base
    base = f"{topic[:1].upper() + topic[1:]}: veja critérios práticos, pontos de atenção e o que conferir antes da compra."
    return base[:155].rstrip(" ,;:-")


def prompt_for(item):
    return f"""Você é editor sênior de um blog brasileiro de Casa e Decoração.
Escreva um artigo original, aprofundado e natural em português do Brasil.

PAUTA: {item['topic']}
PRODUTO RELACIONADO: {item['product']}
CATEGORIA: {item['category']}

REGRAS OBRIGATÓRIAS:
- Produza aproximadamente 900 a 1300 palavras de conteúdo editorial útil.
- Não invente preço, desconto, estoque, entrega, potência, voltagem, autonomia, capacidade, material, dimensões, peso, garantia, compatibilidade, certificação, vendas ou desempenho do produto.
- Não diga que o produto foi testado fisicamente.
- Quando um dado específico não estiver confirmado, use linguagem prudente como “vale conferir no anúncio”.
- Separe orientação geral de características específicas do produto.
- Explique contexto de uso, para quem pode fazer sentido, limitações e o que conferir antes da compra.
- Evite exageros como “o melhor”, “imperdível”, “100% garantido”.
- SEO natural, sem repetição artificial da palavra-chave.
- Foque exatamente na intenção da pauta para evitar canibalização.
- Não inclua H1.
- Use apenas <p>, <h2>, <h3>, <ul>, <li>, <strong> e <em> quando necessário.
- NÃO inclua preço, botão, link ou CTA comercial. O sistema acrescentará o bloco afiliado depois.
- Não inclua comentários sobre estas instruções.

Responda SOMENTE com o fragmento HTML do artigo. Não use markdown nem cercas de código.
"""


def expansion_prompt(item, draft_html):
    return f"""Expanda e aprofunde o artigo abaixo para aproximadamente 900 a 1300 palavras, mantendo a mesma pauta e sem inventar fatos sobre o produto.

PAUTA: {item['topic']}
PRODUTO RELACIONADO: {item['product']}
CATEGORIA: {item['category']}

Mantenha linguagem natural, útil e prudente. Acrescente critérios de comparação, contexto de uso, limitações, erros comuns e um checklist final. Não inclua H1, links, preço nem CTA. Não afirme teste físico. Se uma especificação não estiver confirmada, diga para conferir o anúncio, ficha técnica ou manual.

RASCUNHO ATUAL:
{draft_html}

Responda SOMENTE com o fragmento HTML final, sem markdown.
"""


def build_article(item, raw_html):
    content = clean_html(raw_html)
    count = word_count(content)
    if count < 700:
        content = clean_html(call_ai(expansion_prompt(item, content)))
        count = word_count(content)
    if count < 650:
        raise RuntimeError(f"artigo ainda curto após expansão: {count} palavras")
    if "<h2" not in content.lower() or "<p" not in content.lower():
        raise RuntimeError("HTML sem estrutura editorial mínima")

    product = html.escape(str(item["product"]))
    link = html.escape(str(item["affiliate_link"]), quote=True)
    category_slug = {
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
    }.get(item.get("category"), "")
    category_link = (
        f'<p><a href="/category/{category_slug}/">Veja também outros guias de {html.escape(str(item["category"]))}</a>.</p>'
        if category_slug else ""
    )
    cta = f'''\n<div class="cd-produto-relacionado" style="margin:28px 0;padding:20px;border:1px solid #72eadb;border-radius:14px;background:#effffb;box-shadow:0 0 18px rgba(75,230,210,.20);">
<p><strong>Produto relacionado ao tema:</strong> {product}</p>
<p><a href="{link}" target="_blank" rel="nofollow sponsored" style="display:inline-block;padding:12px 18px;background:#19c6b3;color:#052f2c;text-decoration:none;font-weight:700;border-radius:10px;">Ver produto no TikTok Shop →</a></p>
<p><small>Link de afiliado. O site pode receber comissão em compras qualificadas, sem custo adicional para você. Preço, estoque, entrega e especificações devem ser confirmados na página do vendedor.</small></p>
</div>'''
    meta = meta_from_item(item)
    return {
        **item,
        "seo_title": title_from_topic(item.get("topic")),
        "meta_description": meta,
        "excerpt": meta,
        "content_html": content + cta + category_link,
        "word_count": count,
        "generation_model": MODEL,
        "status": "GENERATED",
    }


def main():
    queue = load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    candidates = [
        x for x in items
        if x.get("status") in {"PENDING", "QUARANTINE"}
        and int(x.get("generation_attempts") or 0) < MAX_ITEM_ATTEMPTS
    ][:BATCH_SIZE]
    if not candidates:
        print("Nenhuma pauta elegível para geração.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    by_id = {int(x["id"]): x for x in items}
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
            current.pop("last_error", None)
            generated_count += 1
        except Exception as exc:
            current["status"] = "QUARANTINE"
            current["last_error"] = str(exc)[:500]
            print(f"QUARANTINE {item_id}: {exc}")

    queue["items"] = [by_id[int(x["id"])] for x in items]
    save_json(QUEUE_PATH, queue)
    print(f"Gerados: {generated_count}/{len(candidates)}")


if __name__ == "__main__":
    main()
