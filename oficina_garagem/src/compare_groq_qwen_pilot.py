import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "oficina_garagem" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import generate_articles as editorial

QUEUE = ROOT / "oficina_garagem" / "data" / "editorial_queue.json"
OUT = ROOT / "oficina_garagem" / "data" / "groq_pilot"
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
QWEN_MODEL = os.getenv("OFICINA_AI_MODEL", "@cf/qwen/qwen3-30b-a3b-fp8").strip()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


class ProviderMetrics:
    def __init__(self, provider):
        self.provider = provider
        self.logical_calls = 0
        self.http_attempts = 0
        self.retries = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.usage_samples = 0
        self.errors = []
        self.rate_limit = {}

    def begin_call(self):
        self.logical_calls += 1

    def begin_attempt(self, attempt):
        self.http_attempts += 1
        if attempt > 0:
            self.retries += 1

    def add_usage(self, usage):
        if not isinstance(usage, dict):
            return
        prompt = _int(usage.get("prompt_tokens"))
        completion = _int(usage.get("completion_tokens"))
        total = _int(usage.get("total_tokens")) or (prompt + completion)
        if prompt or completion or total:
            self.prompt_tokens += prompt
            self.completion_tokens += completion
            self.total_tokens += total
            self.usage_samples += 1

    def add_error(self, value):
        text = str(value or "").strip()
        if text:
            self.errors.append(text[:500])

    def capture_headers(self, headers):
        if not headers:
            return
        wanted = (
            "x-ratelimit-limit-requests",
            "x-ratelimit-remaining-requests",
            "x-ratelimit-reset-requests",
            "x-ratelimit-limit-tokens",
            "x-ratelimit-remaining-tokens",
            "x-ratelimit-reset-tokens",
            "retry-after",
        )
        lower = {str(k).lower(): str(v) for k, v in headers.items()}
        self.rate_limit = {k: lower[k] for k in wanted if k in lower}

    def snapshot(self):
        return {
            "logical_calls": self.logical_calls,
            "http_attempts": self.http_attempts,
            "retries": self.retries,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "token_usage_complete": self.usage_samples == self.logical_calls and self.logical_calls > 0,
            "usage_samples": self.usage_samples,
            "errors": self.errors[-5:],
            "rate_limit_last_response": self.rate_limit,
        }


QWEN_METRICS = ProviderMetrics("cloudflare-qwen")
GROQ_METRICS = ProviderMetrics("groq")


def _cloudflare_usage(payload):
    if not isinstance(payload, dict):
        return {}
    result = payload.get("result")
    if isinstance(result, dict) and isinstance(result.get("usage"), dict):
        return result["usage"]
    if isinstance(payload.get("usage"), dict):
        return payload["usage"]
    return {}


def qwen_ai(prompt, retries=3):
    QWEN_METRICS.begin_call()
    account, token = editorial.creds()
    prompt = str(prompt or "").strip()
    if QWEN_MODEL.startswith("@cf/qwen/qwen3") and not prompt.startswith("/no_think"):
        prompt = "/no_think\n" + prompt
    req_body = json.dumps(
        {"messages": [{"role": "user", "content": prompt}], "max_tokens": 8192, "temperature": 0.2},
        ensure_ascii=False,
    ).encode()
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{QWEN_MODEL}"
    last = ""
    for attempt in range(retries):
        QWEN_METRICS.begin_attempt(attempt)
        req = urllib.request.Request(
            endpoint,
            data=req_body,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "OficinaGaragem-Groq-Pilot-Qwen/2.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8", "replace"))
                QWEN_METRICS.capture_headers(response.headers)
            QWEN_METRICS.add_usage(_cloudflare_usage(payload))
            text = editorial.extract_text(payload)
            if text:
                return text
            last = "resposta vazia ou em formato não reconhecido"
            QWEN_METRICS.add_error(last)
        except Exception as exc:
            last = str(exc)
            QWEN_METRICS.add_error(last)
        if attempt + 1 < retries:
            time.sleep(5 if attempt == 0 else 15)
    raise RuntimeError("Falha Workers AI no piloto: " + last)


def groq_ai(prompt, retries=4):
    GROQ_METRICS.begin_call()
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY ausente")
    payload = json.dumps(
        {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": str(prompt or "").strip()}],
            "temperature": 0.2,
            "max_completion_tokens": 4096,
            "reasoning_effort": "low",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    last = ""
    for attempt in range(retries):
        GROQ_METRICS.begin_attempt(attempt)
        req = urllib.request.Request(
            endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "OficinaGaragem-Groq-Pilot/2.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                body = json.loads(response.read().decode("utf-8", "replace"))
                GROQ_METRICS.capture_headers(response.headers)
            GROQ_METRICS.add_usage(body.get("usage") or {})
            choices = body.get("choices") or []
            if choices:
                text = str((choices[0].get("message") or {}).get("content") or "").strip()
                if text:
                    return text
            last = "resposta Groq vazia"
            GROQ_METRICS.add_error(last)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:1200]
            GROQ_METRICS.capture_headers(exc.headers)
            last = f"HTTP {exc.code}: {detail}"
            GROQ_METRICS.add_error(last)
            if exc.code == 429 and attempt + 1 < retries:
                retry_after = exc.headers.get("Retry-After")
                try:
                    wait = max(10, min(int(float(retry_after)), 90)) if retry_after else 60
                except ValueError:
                    wait = 60
                time.sleep(wait)
                continue
        except Exception as exc:
            last = str(exc)
            GROQ_METRICS.add_error(last)
        if attempt + 1 < retries:
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("Falha Groq: " + last)


def summarize(provider, item, article, elapsed, metrics):
    quality = article.get("quality") or {}
    return {
        "provider": provider,
        "source_item_id": str(item.get("shopee_item_id") or item.get("itemId") or ""),
        "source_product": item.get("product") or item.get("productName"),
        "category": item.get("category"),
        "title": article.get("editorial_title") or article.get("topic"),
        "focus_keyword": article.get("focus_keyword"),
        "word_count": editorial.word_count(article.get("editorial_html") or ""),
        "quality_status": quality.get("status"),
        "quality_reasons": quality.get("reasons") or [],
        "cta_generation_mode": article.get("cta_generation_mode"),
        "elapsed_seconds": round(elapsed, 2),
        "metrics": metrics.snapshot(),
    }


def generate_with(provider_name, model_name, ai_func, item, metrics):
    original_ai = editorial.ai
    editorial.ai = ai_func
    started = time.time()
    plan = None
    try:
        plan = editorial.make_plan(item)
        article = editorial.generate_article(item, plan)
        article["generation_model"] = model_name
        article["pilot_provider"] = provider_name
        elapsed = time.time() - started
        return {
            "provider": provider_name,
            "status": "GENERATED",
            "plan": plan,
            "article": article,
            "summary": summarize(provider_name, item, article, elapsed, metrics),
        }
    except Exception as exc:
        elapsed = time.time() - started
        return {
            "provider": provider_name,
            "status": "FAILED",
            "plan": plan,
            "article": None,
            "error": str(exc),
            "summary": {
                "provider": provider_name,
                "source_item_id": str(item.get("shopee_item_id") or item.get("itemId") or ""),
                "source_product": item.get("product") or item.get("productName"),
                "category": item.get("category"),
                "quality_status": "FAILED",
                "quality_reasons": [str(exc)],
                "elapsed_seconds": round(elapsed, 2),
                "metrics": metrics.snapshot(),
            },
        }
    finally:
        editorial.ai = original_ai


def main():
    doc = load(QUEUE)
    items = doc.get("items") or []
    if not items:
        raise SystemExit("Fila editorial vazia; piloto não executado")
    item = dict(items[0])
    OUT.mkdir(parents=True, exist_ok=True)
    save(OUT / "source_item.json", item)

    print("Piloto A/B: gerando candidato Qwen atual...")
    qwen = generate_with("cloudflare-qwen3-30b-a3b-fp8", QWEN_MODEL, qwen_ai, item, QWEN_METRICS)
    save(OUT / "qwen.json", qwen)

    print("Piloto A/B: gerando candidato Groq GPT-OSS 120B...")
    groq = generate_with(f"groq:{GROQ_MODEL}", GROQ_MODEL, groq_ai, item, GROQ_METRICS)
    save(OUT / "groq.json", groq)

    same_source_item = bool(
        qwen["summary"].get("source_item_id")
        and qwen["summary"].get("source_item_id") == groq["summary"].get("source_item_id")
    )
    both_generated = qwen["status"] == "GENERATED" and groq["status"] == "GENERATED"
    both_quality_pass = (
        both_generated
        and qwen["summary"].get("quality_status") != "REJECTED"
        and groq["summary"].get("quality_status") != "REJECTED"
    )
    report = {
        "status": "COMPARISON_COMPLETE" if both_generated else "COMPARISON_PARTIAL",
        "same_source_item": same_source_item,
        "wordpress_written": False,
        "production_workflows_modified": False,
        "qwen": qwen["summary"],
        "groq": groq["summary"],
        "both_generated": both_generated,
        "both_quality_pass": both_quality_pass,
        "automatic_decision": "MANUAL_REVIEW_REQUIRED",
        "note": (
            "Nenhum candidato foi publicado ou sincronizado ao WordPress. Compare qualidade editorial, "
            "fidelidade, segurança, SEO, CTA, tempo, chamadas, retries e tokens antes de qualquer migração."
        ),
    }
    save(OUT / "comparison.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not same_source_item:
        raise SystemExit("Piloto inválido: provedores não usaram o mesmo item de origem")
    if not both_generated:
        raise SystemExit("Piloto parcial: pelo menos um provedor falhou; artefatos preservados para diagnóstico")
    if not both_quality_pass:
        raise SystemExit("Piloto não aprovado pelos gates; artefatos preservados para revisão")


if __name__ == "__main__":
    main()
