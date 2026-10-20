import ast
import json
import os
import re
import time

import lab_compare as lab
import run_lab as pet_runner


def parse_model_object(raw):
    text = str(raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("Resposta sem objeto estruturado")
    candidate = text[start:end + 1]
    try:
        doc = json.loads(candidate)
        if not isinstance(doc, dict):
            raise RuntimeError("JSON não é objeto")
        return doc, "STRICT_JSON"
    except json.JSONDecodeError as strict_error:
        try:
            doc = ast.literal_eval(candidate)
        except (ValueError, SyntaxError) as fallback_error:
            raise RuntimeError(
                f"Resposta estruturada inválida; JSON={strict_error}; fallback={fallback_error}"
            ) from fallback_error
        if not isinstance(doc, dict):
            raise RuntimeError("Fallback estruturado não é objeto")
        return doc, "NON_STRICT_PARSEABLE"


def save_raw(provider, raw):
    lab.OUT.mkdir(parents=True, exist_ok=True)
    (lab.OUT / f"{provider}_raw.txt").write_text(str(raw or ""), encoding="utf-8")


def run_provider(name, model, fn, prompt, item):
    metrics = lab.Metrics(provider=name, model=model)
    started = time.time()
    raw = ""
    try:
        metrics.http_attempts += 1
        raw, usage, headers = fn(prompt)
        metrics.elapsed_seconds = round(time.time() - started, 2)
        metrics.prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
        metrics.completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens")
        metrics.total_tokens = usage.get("total_tokens")
        metrics.rate_limit_remaining_requests = headers.get("x-ratelimit-remaining-requests") or headers.get("X-RateLimit-Remaining-Requests")
        metrics.rate_limit_remaining_tokens = headers.get("x-ratelimit-remaining-tokens") or headers.get("X-RateLimit-Remaining-Tokens")
        save_raw(name, raw)
        doc, parse_mode = parse_model_object(raw)
        quality = lab.evaluate(doc, item)
        quality["format_compliance"] = parse_mode
        return {
            "provider": name,
            "model": model,
            "content": doc,
            "quality": quality,
            "metrics": lab.asdict(metrics),
        }
    except Exception as exc:
        metrics.elapsed_seconds = round(time.time() - started, 2)
        metrics.error = str(exc)
        if raw:
            save_raw(name, raw)
        return {
            "provider": name,
            "model": model,
            "content": None,
            "quality": {
                "status": "ERROR",
                "reasons": [str(exc)],
                "format_compliance": "UNPARSEABLE",
            },
            "metrics": lab.asdict(metrics),
        }


def main():
    required = [
        "SHOPEE_APP_ID",
        "SHOPEE_SECRET",
        "CLOUDFLARE_ACCOUNT_ID",
        "CLOUDFLARE_API_TOKEN",
        "GROQ_API_KEY",
    ]
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise SystemExit("Preflight bloqueado; secrets ausentes: " + ", ".join(missing))

    print("=== VIDA PET PRÁTICA — LABORATÓRIO GROQ vs QWEN SAFE V2 ===")
    print("Qualidade editorial e compliance de formato são medidos separadamente.")
    print("Sem escrita no WordPress. Sem cron. Um único produto real para A/B.")

    lab.shopee.run_regression_checks = pet_runner.pet_regression_checks
    ranking = lab.shopee.scan_v23()
    source, globally_rejected = lab.choose_source(ranking)
    lab.save("source_item.json", source)
    lab.save("source_guard_rejections.json", globally_rejected)

    prompt = lab.prompt_for(source)
    qwen = run_provider("cloudflare-qwen", lab.QWEN_MODEL, lab.cloudflare_call, prompt, source)
    lab.save("qwen.json", qwen)

    groq = run_provider("groq", lab.GROQ_MODEL, lab.groq_call, prompt, source)
    lab.save("groq.json", groq)

    report = {
        "status": "COMPARISON_COMPLETE",
        "lab_version": 2,
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
        "note": "Nenhum conteúdo foi publicado. Formato não estrito é registrado separadamente e não mascara a qualidade editorial."
    }
    lab.save("comparison.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if qwen["quality"]["status"] == "ERROR" or groq["quality"]["status"] == "ERROR":
        raise SystemExit("Piloto incompleto: pelo menos um provedor retornou erro")


if __name__ == "__main__":
    main()
