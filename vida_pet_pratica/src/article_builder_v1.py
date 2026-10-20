import json
import os
import re
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

import automation_core_v1 as core
import evidence_engine as evidence

LAB_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = LAB_ROOT / "data" / "architecture_lab"
POLICY_PATH = LAB_ROOT / "config" / "automation_policy.json"
HISTORY_PATH = LAB_ROOT / "state" / "article_history.json"
RANKING_PATH = LAB_ROOT / "data" / "shopee_oportunidades" / "ranking.json"
GROQ_MODEL = os.getenv("VIDAPET_GROQ_MODEL", "openai/gpt-oss-120b").strip()


class ProviderFatalError(RuntimeError):
    pass


def load_json(path, default):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def html_text(html):
    text = re.sub(r"<[^>]+>", " ", str(html or ""))
    return re.sub(r"\s+", " ", unescape(text)).strip()


def word_count(html):
    return len(re.findall(r"\b[\wÀ-ÿ'-]+\b", html_text(html), flags=re.UNICODE))


def parse_json(raw):
    text = str(raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("Groq não retornou objeto JSON")
    return json.loads(text[start:end + 1])


def groq_call(prompt):
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise ProviderFatalError("GROQ_API_KEY ausente")
    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.15,
        "max_completion_tokens": 9000,
        "reasoning_effort": "low",
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "VidaPetPratica-Lab/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            doc = json.loads(response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1200]
        message = f"Groq HTTP {exc.code}: {detail}"
        if exc.code in {401, 403, 429} or "browser_signature_banned" in detail:
            raise ProviderFatalError(message) from exc
        raise RuntimeError(message) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderFatalError(f"Groq indisponível: {exc}") from exc
    choices = doc.get("choices") or []
    raw = ((choices[0] or {}).get("message") or {}).get("content") if choices else ""
    if not raw:
        raise RuntimeError("Groq retornou resposta vazia")
    return parse_json(raw), doc.get("usage") or {}


def exact_sources(package):
    return [s for s in package.get("sources") or [] if s.get("allowed_in_article") and s.get("identity_level") == "EXACT_PRODUCT" and s.get("support_text")]


def prompt_for(candidate, package):
    evidence_block = [
        {"evidence_id": s["evidence_id"], "source_domain": s.get("source_domain"), "support_text": s.get("support_text")}
        for s in exact_sources(package)
    ]
    return f"""Você é editor do blog brasileiro Vida Pet Prática.
Crie um artigo útil e original usando SOMENTE as evidências autorizadas abaixo para qualquer afirmação específica sobre o produto.

PRODUTO: {candidate.get('productName')}
PALAVRA-CHAVE: {candidate.get('keyword')}
ÂNGULO NOVO: {candidate.get('angle')}
EVIDÊNCIAS AUTORIZADAS: {json.dumps(evidence_block, ensure_ascii=False)}

Retorne SOMENTE JSON válido:
{{
  "title": "35 a 65 caracteres",
  "focus_keyword": "palavra-chave natural",
  "meta_description": "até 155 caracteres",
  "article_html": "HTML do artigo",
  "cta_text": "duas frases neutras",
  "claim_evidence": [
    {{"claim": "frase factual EXATA copiada do article_html", "evidence_ids": ["EV-..."]}}
  ]
}}

REGRAS:
- Português do Brasil; 700 a 900 palavras; pelo menos 5 H2; sem H1.
- HTML permitido: <p>, <h2>, <h3>, <ul>, <li>, <strong>, <em>.
- O artigo deve seguir o ângulo informado e ser útil mesmo sem compra.
- Não copie o título comercial como título editorial.
- Toda frase que declare característica específica do produto deve constar em claim_evidence e citar evidência autorizada.
- Não extrapole a evidência. Produto semelhante não autoriza especificação.
- Não invente material, medida, capacidade, compatibilidade, durabilidade, desempenho ou benefício.
- Ignore preço, desconto, cupom, estoque, frete e prazo de entrega mesmo que apareçam nas fontes.
- Não faça review fingindo teste pessoal.
- Não faça diagnóstico, tratamento, prescrição, alegação terapêutica ou promessa de segurança.
- Para passeio, higiene e alimentação, inclua supervisão/adequação ao animal quando pertinente, como orientação geral, sem transformar isso em característica do produto.
- CTA neutro: orientar a conferir detalhes e condições atuais no anúncio.
"""


def evidence_lookup(package):
    return {s.get("evidence_id"): s for s in exact_sources(package)}


def gate(doc, package, history, max_similarity):
    title = re.sub(r"\s+", " ", str(doc.get("title") or "")).strip()
    meta = re.sub(r"\s+", " ", str(doc.get("meta_description") or "")).strip()
    article = str(doc.get("article_html") or "").strip()
    cta = re.sub(r"\s+", " ", str(doc.get("cta_text") or "")).strip()
    claims = doc.get("claim_evidence") or []
    article_plain = html_text(article)
    article_norm = evidence.normalize(article_plain)
    reasons = []
    wc = word_count(article)
    h2 = len(re.findall(r"<h2\b", article, flags=re.I))

    if not 35 <= len(title) <= 65:
        reasons.append(f"title_length:{len(title)}")
    if not meta or len(meta) > 155:
        reasons.append(f"meta_length:{len(meta)}")
    if not 650 <= wc <= 950:
        reasons.append(f"word_count:{wc}")
    if h2 < 5:
        reasons.append(f"h2_count:{h2}")
    if re.search(r"<h1\b|<script\b|<style\b|<iframe\b", article, flags=re.I):
        reasons.append("forbidden_html")
    if not cta:
        reasons.append("cta_missing")
    if re.search(r"R\$\s*\d|\b\d{1,3}%\b", article_plain, flags=re.I):
        reasons.append("volatile_price_or_discount")

    banned = ["cura ", "curar ", "trata ", "tratamento para", "previne doenca", "elimina ansiedade", "100% seguro", "resultado garantido"]
    norm = evidence.normalize(article_plain)
    hits = [x for x in banned if evidence.normalize(x) in norm]
    if hits:
        reasons.append("medical_or_absolute_claim:" + ",".join(hits))

    lookup = evidence_lookup(package)
    if not claims:
        reasons.append("claim_evidence_missing")
    for idx, row in enumerate(claims):
        claim = re.sub(r"\s+", " ", str((row or {}).get("claim") or "")).strip()
        ids = list((row or {}).get("evidence_ids") or [])
        if not claim or not ids:
            reasons.append(f"claim_{idx}_invalid")
            continue
        if evidence.normalize(claim) not in article_norm:
            reasons.append(f"claim_{idx}_not_in_article")
        if any(eid not in lookup for eid in ids):
            reasons.append(f"claim_{idx}_unauthorized_evidence")
            continue
        support = " ".join(lookup[eid].get("support_text") or "" for eid in ids)
        claim_tokens = evidence.tokens(claim)
        support_tokens = evidence.tokens(support)
        overlap = len(claim_tokens & support_tokens) / max(1, len(claim_tokens))
        if overlap < 0.45:
            reasons.append(f"claim_{idx}_weak_support:{overlap:.2f}")

    current_semantic = f"{title} {article_plain}"
    for old in history:
        old_text = f"{old.get('title') or ''} {old.get('semanticText') or old.get('articleText') or ''}"
        if old_text.strip() and evidence.similarity(current_semantic, old_text) >= max_similarity:
            reasons.append("semantic_duplicate_history")
            break

    return {
        "status": "PASS" if not reasons else "REJECTED",
        "reasons": reasons,
        "word_count": wc,
        "h2_count": h2,
        "title_length": len(title),
        "meta_length": len(meta),
        "claims_count": len(claims),
    }


def candidate_from_item(item, history, max_similarity, max_results):
    item_id = str(item.get("itemId") or "")
    allowed, blocked = core.source_guard(item)
    if not allowed:
        return None, {"itemId": item_id, "stage": "SOURCE_GUARD", "reasons": blocked}
    package = evidence.build_evidence_package(item, max_results=max_results)
    core.save_json(OUT_DIR / "evidence" / f"{item_id}.json", package)
    if package.get("status") != "VERIFIED" or len(exact_sources(package)) < 2:
        return None, {"itemId": item_id, "stage": "EVIDENCE_REJECTED", "reasons": package.get("reasons") or ["external_exact_source_missing"]}
    angle, angle_status = core.choose_angle(item, history, max_similarity)
    if not angle:
        return None, {"itemId": item_id, "stage": angle_status, "reasons": ["no_unique_angle_available"]}
    return {
        "status": "VERIFIED_READY_CANDIDATE", "itemId": item_id, "productName": item.get("productName"),
        "category": (item.get("categories") or [None])[0],
        "keyword": (item.get("intentMatchedKeywords") or item.get("keywords") or [None])[0],
        "angle": angle, "fingerprint": core.fingerprint(item_id, angle), "evidence_file": f"evidence/{item_id}.json",
    }, None


def write_provider_failure(message, generation_attempts, rejected):
    report = {
        "status": "PROVIDER_BLOCKED",
        "version": "ARTICLE_BUILDER_V1_1",
        "provider": "groq",
        "model": GROQ_MODEL,
        "reason": message,
        "generation_attempts": generation_attempts,
        "candidate_failover_suspended": True,
        "why": "Falha do provedor não invalida produtos; failover é reservado para falhas do produto/evidência/artigo.",
        "wordpress_written": False,
        "publishing_enabled": False,
        "rejections": rejected,
    }
    save_json(OUT_DIR / "provider_failure.json", report)
    save_json(OUT_DIR / "post_buffer_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    policy = load_json(POLICY_PATH, {})
    min_ready = int(policy.get("min_ready", 3))
    max_similarity = float((policy.get("anti_duplicate") or {}).get("max_similarity", 0.72))
    max_results = int((policy.get("evidence") or {}).get("max_search_results", 8))
    history = load_json(HISTORY_PATH, [])
    initial = load_json(OUT_DIR / "ready_buffer.json", [])
    ranking = (load_json(RANKING_PATH, {}) or {}).get("ranking") or []

    queue = list(initial)
    queued_ids = {str(x.get("itemId") or "") for x in queue}
    posts, rejected = [], []
    rank_index = 0
    generation_attempts = 0

    while len(posts) < min_ready:
        if queue:
            candidate = queue.pop(0)
        else:
            candidate = None
            while rank_index < len(ranking) and candidate is None:
                item = ranking[rank_index]
                rank_index += 1
                item_id = str(item.get("itemId") or "")
                if not item_id or item_id in queued_ids:
                    continue
                queued_ids.add(item_id)
                try:
                    candidate, rejection = candidate_from_item(item, history, max_similarity, max_results)
                except Exception as exc:
                    candidate, rejection = None, {"itemId": item_id, "stage": "CANDIDATE_FAILOVER", "reasons": [str(exc)]}
                if rejection:
                    rejected.append(rejection)
            if candidate is None:
                break

        item_id = str(candidate.get("itemId") or "")
        package = load_json(OUT_DIR / candidate["evidence_file"], {})
        if len(exact_sources(package)) < 2:
            rejected.append({"itemId": item_id, "stage": "FACT_SOURCE_GATE", "reasons": ["external_exact_source_missing"]})
            continue

        passed, last_gate = None, None
        for _ in range(2):
            generation_attempts += 1
            try:
                doc, usage = groq_call(prompt_for(candidate, package))
                gate_result = gate(doc, package, history, max_similarity)
            except ProviderFatalError as exc:
                write_provider_failure(str(exc), generation_attempts, rejected)
                raise SystemExit("Provider Groq bloqueado; failover de produtos suspenso para preservar recursos") from exc
            except Exception as exc:
                doc, usage = None, {}
                gate_result = {"status": "ERROR", "reasons": [str(exc)]}
            last_gate = gate_result
            if gate_result.get("status") == "PASS":
                passed = {
                    "status": "VERIFIED_READY", "itemId": item_id, "productName": candidate.get("productName"),
                    "category": candidate.get("category"), "keyword": candidate.get("keyword"), "angle": candidate.get("angle"),
                    "fingerprint": candidate.get("fingerprint"), "content": doc, "gate": gate_result, "usage": usage,
                    "wordpress_written": False,
                }
                break
        if passed:
            posts.append(passed)
            save_json(OUT_DIR / "posts" / f"{item_id}.json", passed)
        else:
            rejected.append({"itemId": item_id, "stage": "ARTICLE_GATE", "reasons": (last_gate or {}).get("reasons") or ["unknown"]})

    report = {
        "status": "POST_BUFFER_COMPLETE" if len(posts) >= min_ready else "POST_BUFFER_INCOMPLETE",
        "version": "ARTICLE_BUILDER_V1_1", "min_ready": min_ready, "ready_posts": len(posts),
        "generation_attempts": generation_attempts, "candidate_failover": True,
        "wordpress_written": False, "publishing_enabled": False, "posts": posts, "rejections": rejected,
    }
    save_json(OUT_DIR / "post_buffer.json", posts)
    save_json(OUT_DIR / "post_rejections.json", rejected)
    save_json(OUT_DIR / "post_buffer_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if len(posts) < min_ready:
        raise SystemExit(f"Buffer insuficiente: {len(posts)}/{min_ready} posts passaram")


if __name__ == "__main__":
    main()
