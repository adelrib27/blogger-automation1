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
        choices = result.get("choices") or []
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message") or {}
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"].strip()
    return ""


def call_ai(prompt, retries=3):
    account_id, token = cloudflare_config()
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL}"
    body = json.dumps({"messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    last_error = ""
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(endpoint, data=body, method="POST", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CasaEDecoracao-Editorial/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
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


def strip_fences(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_generated(text):
    clean = strip_fences(text)
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", clean, flags=re.S)
        if not match:
            raise RuntimeError("IA não retornou JSON reconhecível")
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise RuntimeError("resposta da IA não é objeto JSON")
    return data


def title_fallback(topic):
    title = str(topic or "").strip()
    if title:
        title = title[0].upper() + title[1:]
    return title[:60].rstrip(" -:;,")


def prompt_for(item):
    return f"""Você é editor sênior de um blog brasileiro de Casa e Decoração.
Crie um artigo original, útil e natural em português do Brasil.

PAUTA: {item['topic']}
PRODUTO RELACIONADO: {item['product']}
CATEGORIA: {item['category']}

REGRAS OBRIGATÓRIAS:
- 900 a 1400 palavras de conteúdo editorial útil.
- Não invente preço, desconto, estoque, entrega, potência, voltagem, autonomia, capacidade, material, dimensões, peso, garantia, compatibilidade, certificação, vendas ou desempenho do produto.
- Não diga que o produto foi testado fisicamente.
- Quando um dado específico não estiver confirmado, use linguagem prudente como “vale conferir no anúncio”.
- Separe orientação geral de características específicas do produto.
- Explique contexto de uso, para quem pode fazer sentido, limitações e o que conferir antes da compra.
- Evite exageros como “o melhor”, “imperdível”, “100% garantido”.
- SEO natural, sem repetição artificial de palavras-chave.
- Não inclua H1. Use parágrafos, H2 e quando útil H3.
- NÃO inclua preço nem CTA comercial no corpo; o sistema acrescentará o link afiliado depois.
- Evite canibalização: foque exatamente na intenção desta pauta, não tente cobrir todos os assuntos relacionados.

Responda SOMENTE com JSON válido, sem markdown, neste formato:
{{
  "seo_title": "máximo 60 caracteres",
  "meta_description": "120 a 155 caracteres",
  "excerpt": "resumo curto",
  "content_html": "fragmento HTML com o artigo"
}}
"""


def enrich(item, generated):
    seo_title = str(generated.get("seo_title") or title_fallback(item.get("topic"))).strip()[:60]
    meta = str(generated.get("meta_description") or "").strip()[:155]
    excerpt = str(generated.get("excerpt") or meta).strip()[:240]
    content = str(generated.get("content_html") or "").strip()
    content = re.sub(r"</?(?:html|head|body)[^>]*>", "", content, flags=re.I)
    content = re.sub(r"<h1[^>]*>.*?</h1>", "", content, flags=re.I | re.S)
    if len(re.findall(r"\b[\wÀ-ÿ'-]+\b", re.sub(r"<[^>]+>", " ", content))) < 650:
        raise RuntimeError("artigo curto demais para o padrão editorial")
    product = html.escape(str(item["product"]))
    link = html.escape(str(item["affiliate_link"]), quote=True)
    cta = f'''\n<div class="cd-produto-relacionado" style="margin:28px 0;padding:20px;border:1px solid #72eadb;border-radius:14px;background:#effffb;box-shadow:0 0 18px rgba(75,230,210,.20);">
<p><strong>Produto relacionado ao tema:</strong> {product}</p>
<p><a href="{link}" target="_blank" rel="nofollow sponsored" style="display:inline-block;padding:12px 18px;background:#19c6b3;color:#052f2c;text-decoration:none;font-weight:700;border-radius:10px;">Ver produto no TikTok Shop →</a></p>
<p><small>Link de afiliado. O site pode receber comissão em compras qualificadas, sem custo adicional para você. Preço, estoque, entrega e especificações devem ser confirmados na página do vendedor.</small></p>
</div>'''
    return {
        **item,
        "seo_title": seo_title,
        "meta_description": meta,
        "excerpt": excerpt,
        "content_html": content + cta,
        "generation_model": MODEL,
        "status": "GENERATED",
    }


def main():
    queue = load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    pending = [x for x in items if x.get("status") == "PENDING"][:BATCH_SIZE]
    if not pending:
        print("Nenhuma pauta PENDING.")
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    by_id = {int(x["id"]): x for x in items}
    generated_count = 0
    for item in pending:
        item_id = int(item["id"])
        print(f"Gerando {item_id}: {item['topic']}")
        try:
            parsed = parse_generated(call_ai(prompt_for(item)))
            article = enrich(item, parsed)
            save_json(OUT_DIR / f"{item_id:03d}.json", article)
            by_id[item_id]["status"] = "GENERATED"
            generated_count += 1
        except Exception as exc:
            by_id[item_id]["status"] = "QUARANTINE"
            by_id[item_id]["last_error"] = str(exc)[:500]
            print(f"QUARANTINE {item_id}: {exc}")
    queue["items"] = [by_id[int(x["id"])] for x in items]
    save_json(QUEUE_PATH, queue)
    print(f"Gerados: {generated_count}/{len(pending)}")


if __name__ == "__main__":
    main()
