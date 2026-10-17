import html
import json
import os
import re
import time
import urllib.request
from pathlib import Path

from quality_gate import quality, word_count

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "oficina_garagem" / "data" / "editorial_queue.json"
OUT_DIR = ROOT / "oficina_garagem" / "data" / "generated"
MODEL = os.getenv("OFICINA_AI_MODEL", "@cf/qwen/qwen3-30b-a3b-fp8").strip()
BATCH_SIZE = max(1, min(int(os.getenv("OFICINA_GENERATION_BATCH_SIZE", "2")), 10))
ENABLED = os.getenv("OFICINA_GENERATION_ENABLED", "false").strip().lower() in {"1","true","yes","on"}


def load(path, default):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def creds():
    account = os.getenv("OFICINA_CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("OFICINA_CLOUDFLARE_API_TOKEN", "").strip()
    if not account or not token: raise RuntimeError("Credenciais Cloudflare Oficina ausentes")
    return account, token


def ai(prompt, retries=3):
    account, token = creds()
    req_body = json.dumps({"messages":[{"role":"user","content":prompt}],"max_tokens":8192,"temperature":0.42}, ensure_ascii=False).encode()
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    last = ""
    for attempt in range(retries):
        req = urllib.request.Request(endpoint, data=req_body, method="POST", headers={"Authorization":f"Bearer {token}","Content-Type":"application/json","Accept":"application/json","User-Agent":"OficinaGaragem-Editorial/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as response: payload = json.loads(response.read().decode("utf-8","replace"))
            result = payload.get("result") if isinstance(payload, dict) else None
            text = (result or {}).get("response") if isinstance(result, dict) else ""
            if text: return text.strip()
            last = "resposta vazia"
        except Exception as exc: last = str(exc)
        if attempt + 1 < retries: time.sleep(5 if attempt == 0 else 15)
    raise RuntimeError("Falha Workers AI: " + last)


def clean(raw):
    raw = re.sub(r"^```(?:html)?\s*", "", str(raw or "").strip(), flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)
    raw = re.sub(r"</?(?:html|head|body)[^>]*>", "", raw, flags=re.I)
    raw = re.sub(r"<h1[^>]*>.*?</h1>", "", raw, flags=re.I|re.S)
    return raw.strip()


def slug_category(name):
    return {"Ferramentas":"ferramentas","Manutenção":"manutencao","Acessórios Automotivos":"acessorios-automotivos","Organização de Garagem":"organizacao-de-garagem","Limpeza e Conservação":"limpeza-e-conservacao","Segurança e Proteção":"seguranca-e-protecao"}.get(name, "")


def cut_words(value, limit):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(value) <= limit:
        return value
    short = value[:limit + 1].rsplit(" ", 1)[0].rstrip(" -:;,. ")
    return short or value[:limit].rstrip(" -:;,. ")


def seo_title(item):
    # O título editorial vem da pauta/keyword, nunca do título comercial completo,
    # evitando transformar números/promessas do anúncio em afirmações editoriais.
    topic = str(item.get("topic") or "").strip()
    return cut_words(topic, 60)


def meta_description(item):
    label = str(item.get("editorial_label") or item.get("source_keyword") or "produto").strip().lower()
    text = f"Veja critérios para comparar {label}, conferir compatibilidade, limitações e especificações no anúncio ou manual antes de decidir pela compra."
    return cut_words(text, 155)


def prompt(item):
    extra = "\n- TEMA SENSÍVEL: trate como guia de compra. Não ensine procedimentos de segurança, reparo, elevação, corte, solda, frenagem, direção, suspensão ou eletricidade. Exija revisão humana." if item.get("rules",{}).get("safety_review") else ""
    return f"""Você é editor de um blog brasileiro chamado Oficina & Garagem. Escreva um guia de compra informativo e conservador em português do Brasil.
PAUTA EDITORIAL: {item['topic']}
INTENÇÃO PRINCIPAL: {item['source_keyword']}
OFERTA RELACIONADA DA SHOPEE: {item['product']}
CATEGORIA: {item['category']}
REGRAS:
- 900 a 1300 palavras, pelo menos 4 H2 distintos; sem H1.
- O título da oferta é apenas referência comercial; não trate números, potência, tensão, torque, capacidade, medidas ou alegações presentes nele como fatos verificados.
- Não invente preço, desconto, estoque, entrega, potência, tensão, corrente, torque, capacidade de carga, medidas, compatibilidade, certificação, garantia ou desempenho.
- Se um dado não estiver confirmado, ensine o leitor a verificar no anúncio, ficha técnica ou manual.
- Não diga que testamos, usamos ou comprovamos o produto.
- Não dê instruções passo a passo de reparos automotivos, sistemas críticos, elevação de veículo, corte, solda ou intervenções elétricas.
- Não forneça valores de torque, pressão, tensão, corrente ou carga só porque aparecem no título comercial da oferta.
- Explique contexto de uso, para quem pode fazer sentido, limitações, compatibilidade a conferir, erros de compra e checklist final.
- Use naturalmente a intenção principal no texto.
- HTML somente com <p>, <h2>, <h3>, <ul>, <li>, <strong>, <em>. Sem links, estilos, markdown ou CTA.
{extra}
Responda SOMENTE com o fragmento HTML.
"""


def build(item, raw):
    editorial = clean(raw)
    if word_count(editorial) < 850: raise RuntimeError("artigo curto")
    link = html.escape(item["affiliate_link"], quote=True)
    product = html.escape(item["product"])
    cat_slug = slug_category(item["category"])
    cta = f'<div class="og-produto-relacionado"><p><strong>Oferta relacionada:</strong> {product}</p><p><a href="{link}" target="_blank" rel="nofollow sponsored">Ver oferta na Shopee →</a></p><p><small>Link de afiliado. Podemos receber comissão em compras qualificadas, sem custo adicional. O título acima reproduz a identificação da oferta; confirme preço, estoque, compatibilidade, especificações, entrega e garantia na página do vendedor.</small></p></div>'
    internal = f'<p><a href="/category/{cat_slug}/">Veja outros guias de {html.escape(item["category"])}</a>.</p>' if cat_slug else ""
    article = {**item, "seo_title":seo_title(item), "meta_description":meta_description(item), "focus_keyword":item["source_keyword"], "excerpt":meta_description(item), "editorial_html":editorial, "content_html":editorial+cta+internal, "word_count":word_count(editorial), "generation_model":MODEL, "status":"GENERATED"}
    article["quality"] = quality(article)
    if article["quality"]["status"] == "REJECTED": raise RuntimeError("quality gate: " + ", ".join(article["quality"]["reasons"]))
    return article


def main():
    if not ENABLED:
        print("Geração desativada por OFICINA_GENERATION_ENABLED=false; nenhuma chamada de IA realizada.")
        return
    doc = load(QUEUE, {})
    items = doc.get("items") or []
    processed = 0
    for item in items:
        if processed >= BATCH_SIZE: break
        if item.get("status") not in {"PENDING","QUARANTINE"}: continue
        try:
            article = build(item, ai(prompt(item)))
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            save(OUT_DIR / f"{int(item['id']):03d}.json", article)
            item["status"] = "GENERATED" if article["quality"]["status"] == "DRAFT_READY" else "HUMAN_REVIEW"
            item["quality"] = article["quality"]
            item["last_error"] = ""
        except Exception as exc:
            item["generation_attempts"] = int(item.get("generation_attempts") or 0) + 1
            item["last_error"] = str(exc)[:800]
            item["status"] = "BLOCKED" if item["generation_attempts"] >= 3 else "QUARANTINE"
        processed += 1
    doc["items"] = items
    save(QUEUE, doc)
    print(f"Itens processados: {processed}")


if __name__ == "__main__": main()
