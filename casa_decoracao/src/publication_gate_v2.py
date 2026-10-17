import re

from quality_gate import cannibalization_reasons, draft_quality, normalized, plain_text

QUALITY_GATE_VERSION = 2

EXPERIENCE_CLAIM_PATTERNS = (
    r"\b(?:n[oó]s\s+)?testamos\b",
    r"\bem\s+nossos?\s+testes?\b",
    r"\bna\s+nossa\s+experi[eê]ncia\b",
    r"\bcomprovamos\b",
    r"\busamos\s+(?:por|durante)\b",
)

HIGH_RISK_CLAIM_PATTERNS = (
    ("alegacao_antialergica", r"\bantial[eé]rgic[oa]s?\b"),
    ("alegacao_antisseptica", r"\bantiss[eé]ptic[oa]s?\b"),
    ("alegacao_antibacteriana", r"\bantibacterian[oa]s?\b"),
    ("alegacao_microorganismos", r"\b(?:mata|elimina|remove)\s+(?:bact[eé]rias|germes|v[ií]rus|fungos)\b"),
    ("alegacao_saude", r"\b(?:cura|trata|previne|alivia|reduz)\s+(?:a\s+)?(?:dor|dores|alergia|alergias|inflama[cç][aã]o)\b"),
    ("alegacao_postura", r"\b(?:corrige|melhora)\s+(?:a\s+)?postura\b"),
)

SPEC_PATTERN = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:kg|g|cm|mm|m|l|ml|w|v|a|mah|gsm|%|hz|mp|gb|tb|pe[cç]as?)\b",
    flags=re.I,
)


def publication_risk_reasons(article):
    reasons = []
    editorial = str(article.get("editorial_html") or article.get("content_html") or "")
    text = plain_text(editorial)
    folded = text.casefold()

    for pattern in EXPERIENCE_CLAIM_PATTERNS:
        if re.search(pattern, folded, flags=re.I):
            reasons.append("alegacao_de_teste_ou_experiencia_nao_comprovada")
            break

    for code, pattern in HIGH_RISK_CLAIM_PATTERNS:
        if re.search(pattern, folded, flags=re.I):
            reasons.append(code)

    allowed_specs = normalized(" ".join([
        str(article.get("product") or ""),
        str(article.get("topic") or ""),
    ]))
    for match in SPEC_PATTERN.finditer(text):
        spec = normalized(match.group(0))
        if spec and spec not in allowed_specs:
            reasons.append(f"especificacao_numerica_nao_confirmada:{spec}")
            break

    return sorted(set(reasons))


def publication_quality_v2(article, existing_posts=None, current_slug=""):
    base = draft_quality(article)
    reasons = list(base["reasons"])
    reasons.extend(cannibalization_reasons(article, existing_posts or [], current_slug=current_slug))
    reasons.extend(publication_risk_reasons(article))

    wc = int(base["metrics"]["word_count"])
    h2_count = int(base["metrics"]["h2_count"])
    if wc < 850:
        reasons.append(f"publicacao_word_count_baixo:{wc}")
    if h2_count < 4:
        reasons.append(f"publicacao_poucos_h2:{h2_count}")

    if str(article.get("last_error") or "").strip():
        reasons.append("historico_erro_nao_resolvido")

    featured_media_id = int(article.get("featured_media_id") or 0)
    featured_url = str(article.get("featured_image_url") or "").strip()
    featured_alt = str(article.get("featured_image_alt") or "").strip()
    if not featured_media_id and not featured_url:
        reasons.append("imagem_destacada_ausente")
    if (featured_media_id or featured_url) and len(featured_alt) < 8:
        reasons.append("alt_imagem_destacada_ausente")

    reasons = sorted(set(reasons))
    return {
        "status": "QUALITY_APPROVED" if not reasons else "REVIEW_REQUIRED",
        "quality_gate_version": QUALITY_GATE_VERSION,
        "reasons": reasons,
        "metrics": base["metrics"],
    }
