import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_SRC = ROOT / "src"
LAB_ROOT = ROOT / "vida_pet_pratica"
CONFIG = LAB_ROOT / "config" / "shopee_oportunidades.json"
INTENT = LAB_ROOT / "config" / "shopee_intent_rules.json"
OUT = LAB_ROOT / "data" / "pilot"

os.environ["SHOPEE_OPPORTUNITIES_CONFIG"] = str(CONFIG)
os.environ["SHOPEE_INTENT_RULES"] = str(INTENT)
os.environ["SHOPEE_OUTPUT_DIR"] = str(LAB_ROOT / "data" / "shopee_oportunidades")
os.environ.setdefault("SHOPEE_TOP_N", "24")

if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))

import shopee_oportunidades_v23 as shopee  # noqa: E402

QWEN_MODEL = os.getenv("VIDAPET_QWEN_MODEL", "@cf/qwen/qwen3-30b-a3b-fp8").strip()
GROQ_MODEL = os.getenv("VIDAPET_GROQ_MODEL", "openai/gpt-oss-120b").strip()

GLOBAL_BLOCKLIST = [
    "medicamento", "remedio", "remédio", "antibiotico", "antibiótico",
    "anti-inflamatorio", "anti-inflamatório", "vermifugo", "vermífugo",
    "antipulgas", "carrapaticida", "suplemento", "vitamina", "ração", "racao",
    "petisco", "shampoo medicamentoso", "tratamento veterinario", "tratamento veterinário"
]

EDITORIAL_BLOCKLIST = [
    "cura ", "curar ", "trata ", "tratamento para", "previne doença", "previne doenca",
    "elimina ansiedade", "reduz ansiedade", "veterinário recomenda", "veterinario recomenda",
    "100% seguro", "totalmente seguro", "garantia de segurança", "garantia de seguranca",
    "comprovado cientificamente", "resultado garantido"
]


def normalize(text):
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def html_text(html):
    text = re.sub(r"<[^>]+>", " ", str(html or ""))
    return re.sub(r"\s+", " ", unescape(text)).strip()


def word_count(html):
    return len(re.findall(r"\b[\wÀ-ÿ'-]+\b", html_text(html), flags=re.UNICODE))


def safe_json(raw):
    text = str(raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("Resposta sem JSON válido")
    return json.loads(text[start:end + 1])


def save(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass
class Metrics:
    provider: str
    model: str
    elapsed_seconds: float = 0.0
    http_attempts: int = 0
    retries: int = 0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    rate_limit_remaining_requests: str | None = None
    rate_limit_remaining_tokens: str | None = None
    error: str | None = None


def cloudflare_call(prompt):
    account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    if not account or not token:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID/CLOUDFLARE_API_TOKEN ausentes")
    body_prompt = prompt
    if QWEN_MODEL.startswith("@cf/qwen/qwen3") and not body_prompt.startswith("/no_think"):
        body_prompt = "/no_think\n" + body_prompt
    payload = json.dumps({
        "messages": [{"role": "user", "content": body_prompt}],
        "max_tokens": 8192,
        "temperature": 0.2
    }, ensure_ascii=False).encode("utf-8")
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{QWEN_MODEL}"
    req = urllib.request.Request(
        endpoint, data=payload, method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "VidaPetPratica-Lab/1.0"
        }
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        doc = json.loads(response.read().decode("utf-8", "replace"))
    result = doc.get("result") or {}
    text = result.get("response") or result.get("text") or result.get("output_text")
    if not text and result.get("choices"):
        message = (result["choices"][0] or {}).get("message") or {}
        text = message.get("content")
    if not text:
        raise RuntimeError("Workers AI retornou resposta vazia")
    usage = result.get("usage") or doc.get("usage") or {}
    return str(text).strip(), usage, {}


def groq_call(prompt, retries=3):
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY ausente")
    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_completion_tokens": 8192,
        "reasoning_effort": "low"
    }, ensure_ascii=False).encode("utf-8")
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    last = ""
    for attempt in range(retries):
        req = urllib.request.Request(
            endpoint, data=payload, method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "VidaPetPratica-Lab/1.0"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                headers = dict(response.headers.items())
                doc = json.loads(response.read().decode("utf-8", "replace"))
            choices = doc.get("choices") or []
            text = ((choices[0] or {}).get("message") or {}).get("content") if choices else ""
            if not text:
                raise RuntimeError("Groq retornou resposta vazia")
            return str(text).strip(), doc.get("usage") or {}, headers
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:1200]
            last = f"HTTP {exc.code}: {detail}"
            if exc.code == 429 and attempt + 1 < retries:
                retry_after = exc.headers.get("Retry-After")
                try:
                    wait = max(5, min(int(float(retry_after)), 90)) if retry_after else 30
                except ValueError:
                    wait = 30
                time.sleep(wait)
                continue
            raise RuntimeError(last) from exc
        except Exception as exc:
            last = str(exc)
            if attempt + 1 < retries:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(last) from exc
    raise RuntimeError(last or "Falha Groq")


def product_is_allowed(item):
    name = normalize(item.get("productName") or "")
    blocked = [term for term in GLOBAL_BLOCKLIST if normalize(term) in name]
    return not blocked, blocked


def choose_source(ranking):
    rejected = []
    for item in ranking:
        allowed, blocked = product_is_allowed(item)
        if allowed:
            return item, rejected
        rejected.append({"itemId": item.get("itemId"), "productName": item.get("productName"), "blocked": blocked})
    raise RuntimeError("Nenhum produto SAFE disponível no ranking")


def prompt_for(item):
    product = str(item.get("productName") or "").strip()
    keyword = str((item.get("intentMatchedKeywords") or item.get("keywords") or [""])[0]).strip()
    categories = ", ".join(item.get("categories") or [])
    shop = str(item.get("shopName") or "").strip()
    link = str(item.get("offerLink") or "").strip()
    return f"""Você é editor do blog brasileiro Vida Pet Prática, especializado em soluções práticas para cães e gatos.

Use o produto real abaixo apenas como ponto de partida editorial. O artigo deve ser útil por si só e não pode inventar características que não estejam confirmadas no título do anúncio.

PRODUTO REAL DA SHOPEE: {product}
INTENÇÃO DE BUSCA VALIDADA: {keyword}
CATEGORIA: {categories}
LOJA: {shop}
LINK DE AFILIADO DISPONÍVEL PARA CTA: {link}

Gere SOMENTE um objeto JSON válido com estes campos:
{{
  "title": "título editorial entre 35 e 65 caracteres",
  "focus_keyword": "palavra-chave principal natural",
  "meta_description": "descrição de até 155 caracteres",
  "article_html": "fragmento HTML completo",
  "cta_text": "duas frases neutras para apresentar a opção relacionada"
}}

REGRAS EDITORIAIS:
- Português do Brasil.
- 650 a 950 palavras no article_html.
- Pelo menos 5 seções H2 distintas; sem H1.
- HTML permitido no artigo: <p>, <h2>, <h3>, <ul>, <li>, <strong>, <em>.
- Não copie nem faça paráfrase rasa do título comercial.
- O conteúdo deve resolver uma dúvida, necessidade ou escolha prática do tutor.
- Não escreva review fingindo teste ou experiência pessoal.
- Não invente preço, desconto, estoque, frete, medidas, materiais, capacidade, compatibilidade, durabilidade ou desempenho.
- Se um detalhe técnico não estiver confirmado, ensine o leitor a conferir a descrição do anúncio ou as instruções do fabricante.
- Não faça diagnóstico, tratamento, prescrição, recomendação veterinária ou alegação terapêutica.
- Não prometa reduzir ansiedade, curar, prevenir doenças ou garantir segurança.
- Não trate ração, suplemento, medicamento, antipulgas ou produto veterinário como recomendação.
- Em passeio, transporte, alimentação e higiene, recomende supervisão e adequação ao porte/necessidades do animal quando pertinente.
- Não use linguagem de urgência, escassez ou pressão de compra.
- O CTA deve apresentar o produto como opção relacionada e orientar o leitor a conferir medidas, materiais, compatibilidade e condições no anúncio.
- Não coloque links no article_html; o sistema só registra o link separadamente.
"""


def evaluate(doc, item):
    title = re.sub(r"\s+", " ", str(doc.get("title") or "")).strip()
    keyword = re.sub(r"\s+", " ", str(doc.get("focus_keyword") or "")).strip()
    meta = re.sub(r"\s+", " ", str(doc.get("meta_description") or "")).strip()
    article = str(doc.get("article_html") or "").strip()
    cta = re.sub(r"\s+", " ", str(doc.get("cta_text") or "")).strip()
    text_norm = normalize(html_text(article))
    reasons = []
    wc = word_count(article)
    h2 = len(re.findall(r"<h2\b", article, flags=re.I))
    if not 35 <= len(title) <= 65:
        reasons.append(f"title_length:{len(title)}")
    if not keyword:
        reasons.append("focus_keyword_missing")
    if len(meta) > 155 or not meta:
        reasons.append(f"meta_length:{len(meta)}")
    if not 650 <= wc <= 950:
        reasons.append(f"word_count:{wc}")
    if h2 < 5:
        reasons.append(f"h2_count:{h2}")
    if re.search(r"<h1\b|<script\b|<style\b|<iframe\b", article, flags=re.I):
        reasons.append("forbidden_html")
    hits = [term for term in EDITORIAL_BLOCKLIST if normalize(term) in text_norm]
    if hits:
        reasons.append("medical_or_absolute_claim:" + ",".join(hits))
    source_terms = [normalize(x) for x in (item.get("intentMatchedKeywords") or item.get("keywords") or []) if normalize(x)]
    if source_terms and not any(any(tok in text_norm for tok in term.split() if len(tok) >= 4) for term in source_terms):
        reasons.append("source_intent_not_reflected")
    if not cta:
        reasons.append("cta_missing")
    return {
        "status": "PASS" if not reasons else "REJECTED",
        "reasons": reasons,
        "title_length": len(title),
        "meta_length": len(meta),
        "word_count": wc,
        "h2_count": h2
    }


def run_provider(name, model, fn, prompt, item):
    metrics = Metrics(provider=name, model=model)
    started = time.time()
    try:
        metrics.http_attempts += 1
        raw, usage, headers = fn(prompt)
        metrics.elapsed_seconds = round(time.time() - started, 2)
        metrics.prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
        metrics.completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens")
        metrics.total_tokens = usage.get("total_tokens")
        metrics.rate_limit_remaining_requests = headers.get("x-ratelimit-remaining-requests") or headers.get("X-RateLimit-Remaining-Requests")
        metrics.rate_limit_remaining_tokens = headers.get("x-ratelimit-remaining-tokens") or headers.get("X-RateLimit-Remaining-Tokens")
        doc = safe_json(raw)
        quality = evaluate(doc, item)
        return {"provider": name, "model": model, "content": doc, "quality": quality, "metrics": asdict(metrics)}
    except Exception as exc:
        metrics.elapsed_seconds = round(time.time() - started, 2)
        metrics.error = str(exc)
        return {"provider": name, "model": model, "content": None, "quality": {"status": "ERROR", "reasons": [str(exc)]}, "metrics": asdict(metrics)}


def main():
    required = ["SHOPEE_APP_ID", "SHOPEE_SECRET", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "GROQ_API_KEY"]
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise SystemExit("Preflight bloqueado; secrets ausentes: " + ", ".join(missing))

    print("=== VIDA PET PRÁTICA — LABORATÓRIO GROQ vs QWEN SAFE ===")
    print("Sem escrita no WordPress. Sem cron. Um único produto real para A/B.")

    ranking = shopee.scan_v23()
    source, globally_rejected = choose_source(ranking)
    save("source_item.json", source)
    save("source_guard_rejections.json", globally_rejected)

    prompt = prompt_for(source)
    qwen = run_provider("cloudflare-qwen", QWEN_MODEL, cloudflare_call, prompt, source)
    save("qwen.json", qwen)

    groq = run_provider("groq", GROQ_MODEL, groq_call, prompt, source)
    save("groq.json", groq)

    report = {
        "status": "COMPARISON_COMPLETE",
        "site": "https://vidapetpratica.wordpress.com",
        "wordpress_written": False,
        "scheduled": False,
        "same_source_item": True,
        "source_item_id": str(source.get("itemId") or ""),
        "source_product": source.get("productName"),
        "source_keyword": (source.get("intentMatchedKeywords") or source.get("keywords") or [None])[0],
        "qwen": {"quality": qwen["quality"], "metrics": qwen["metrics"]},
        "groq": {"quality": groq["quality"], "metrics": groq["metrics"]},
        "automatic_decision": "MANUAL_REVIEW_REQUIRED",
        "migration_allowed": False,
        "note": "Nenhum conteúdo foi publicado. O candidato vencedor só poderá virar rascunho no Vida Pet Prática após revisão manual."
    }
    save("comparison.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if qwen["quality"]["status"] not in {"PASS", "REJECTED"} or groq["quality"]["status"] not in {"PASS", "REJECTED"}:
        raise SystemExit("Piloto incompleto: pelo menos um provedor retornou erro")


if __name__ == "__main__":
    main()
