import html
import re
import unicodedata

SITE_URL = "https://casaedecoracao.radartechbr.com.br"
CTA_CLASS = "cd-produto-relacionado"
CTA_PRODUCT_TITLE_CLASS = "cd-produto-titulo-original"
CTA_CONSULT_TEXT = "consultar o modelo na Shopee"
MIN_WORDS = 550
MAX_WORDS = 1100
ALLOWED_CATEGORIES = {
    "Decoração", "Organização", "Sala", "Quarto", "Cozinha", "Banheiro", "Área Externa", "Cama, Mesa e Banho"
}
STOPWORDS = {
    "a","as","o","os","um","uma","de","da","das","do","dos","e","em","no","na","nos","nas",
    "para","por","com","sem","ao","aos","ou","como","que","qual","se","antes","mais","menos",
    "seu","sua","uso","usar","sobre","casa","produto"
}
EXPERIENCE_PATTERNS = (
    r"\b(?:n[oó]s\s+)?testamos\b",
    r"\bem nossos? testes?\b",
    r"\bna nossa experi[eê]ncia\b",
    r"\bcomprovamos\b",
    r"\busamos este produto\b",
)
DANGEROUS_PATTERNS = (
    r"\b(?:desligue|ligue|emende|conecte|descape|corte)\b.{0,70}\b(?:fio|fios|rede el[eé]trica|tomada|disjuntor|220v|127v)\b",
    r"\b(?:instale|troque|remova|desmonte)\b.{0,70}\b(?:tomada|disjuntor|chuveiro|fia[cç][aã]o|rede el[eé]trica)\b",
    r"\b(?:abra|feche|troque|instale|conecte)\b.{0,70}\b(?:g[aá]s|botij[aã]o|registro de g[aá]s|mangueira de g[aá]s)\b",
    r"\bmisture\b.{0,80}\b(?:cloro|bleach|[aá]gua sanit[aá]ria|am[oô]nia|vinagre|[aá]cido)\b",
)
MEDICAL_PATTERNS = (
    r"\b(?:cura|trata|elimina|resolve)\b.{0,70}\b(?:dor|ins[oô]nia|cervical|coluna|alergia|refluxo)\b",
    r"\b(?:corrige|garante)\b.{0,70}\b(?:postura|coluna|alinhamento|sono)\b",
    r"\bbenef[ií]cio terap[eê]utico\b",
    r"\b(?:ideal|indicado|recomendad[oa])\b.{0,80}\b(?:alergia|al[eé]rgic[oa]s?|asma|rinite)\b",
    r"\b(?:n[aã]o|sem)\b.{0,30}\b(?:p[oó]len|esporos?)\b",
)
ABSOLUTE_PATTERNS = (
    r"\b(?:100\s*%|totalmente)\s+(?:seguro|imperme[aá]vel|antiderrapante|garantido|eficaz)\b",
    r"\bgarante\b.{0,80}\b(?:seguran[cç]a|durabilidade|prote[cç][aã]o|resultado|conforto)\b",
    r"\bevitar?\s+acidentes?\b",
    r"\bnunca\s+(?:mofa|escorrega|quebra|vaza)\b",
    r"\b(?:segur[oa]|inofensiv[oa])\b.{0,70}\b(?:crian[cç]as?|beb[eê]s?|animais?|pets?)\b",
    r"\b(?:crian[cç]as?|beb[eê]s?|animais?|pets?)\b.{0,70}\b(?:segur[oa]|inofensiv[oa])\b",
    r"\bn[aã]o\s+(?:possui|possuem|cont[eé]m|tem)\b.{0,50}\b(?:subst[aâ]ncias?\s+t[oó]xicas?|toxicidade)\b",
    r"\b(?:sustent[aá]vel|ecol[oó]gic[oa]|econ[oô]mic[oa])\b.{0,80}\b(?:a longo prazo|sempre|garantid[oa])\b",
    r"\b(?:permanece|permane[cç]a|dura|duram)\b.{0,70}\b(?:intact[oa]s?|por muito tempo|anos?)\b",
    r"\bn[aã]o\s+corre(?:m)?\s+o\s+risco\b.{0,80}\b(?:danificad[oa]s?|arrancad[oa]s?|quebrad[oa]s?)\b",
)
NUMERIC_SPEC = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:kg|g|cm|mm|m|l|ml|w|v|ah|mah|%|hz|rpm|litros?|pe[cç]as?)\b",
    re.I,
)
PROMPT_LEAKAGE = ("regras obrigatorias", "responda somente", "fragmento html", "rascunho atual", "fALHAS detectadas")


def normalized(value):
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def compact(value):
    return re.sub(r"\s+", "", normalized(value))


def plain_text(value):
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


def token_set(value):
    return {t for t in normalized(value).split() if len(t) >= 3 and t not in STOPWORDS}


def word_count(value):
    return len(re.findall(r"\b[\wÀ-ÿ'-]+\b", plain_text(value), re.UNICODE))


def internal_link_count(content):
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', str(content or ""), re.I)
    return sum(1 for href in hrefs if href.startswith("/") or href.startswith(SITE_URL))


def cta_positions(content):
    return [m.start() for m in re.finditer(rf'class=["\']{re.escape(CTA_CLASS)}["\']', content, re.I)]


def quality(article):
    reasons = []
    warnings = []
    content = str(article.get("content_html") or "")
    editorial = str(article.get("editorial_html") or content)
    text = plain_text(editorial)
    folded = text.casefold()
    wc = int(article.get("word_count") or word_count(editorial))

    h2_matches_editorial = list(re.finditer(r"<h2\b[^>]*>(.*?)</h2>", editorial, re.I | re.S))
    h2_titles = [normalized(m.group(1)) for m in h2_matches_editorial]
    h2_count = len(h2_titles)

    if wc < MIN_WORDS:
        reasons.append(f"word_count_baixo:{wc}")
    if wc > MAX_WORDS:
        reasons.append(f"word_count_alto:{wc}")
    if h2_count < 5:
        reasons.append(f"poucos_h2:{h2_count}")
    if h2_titles and len(h2_titles) != len(set(h2_titles)):
        reasons.append("h2_repetido")
    if re.search(r"<h1\b", content, re.I):
        reasons.append("h1_no_conteudo")
    if re.search(r"<(?:script|style|iframe|form|button)\b", content, re.I):
        reasons.append("html_nao_permitido")
    if "```" in content:
        reasons.append("artefato_markdown")

    n = normalized(editorial)
    if any(normalized(marker) in n for marker in PROMPT_LEAKAGE):
        reasons.append("vazamento_de_prompt")

    title = str(article.get("seo_title") or "").strip()
    editorial_title = str(article.get("editorial_title") or article.get("topic") or "").strip()
    topic = str(article.get("topic") or editorial_title).strip()
    meta = str(article.get("meta_description") or "").strip()
    focus = str(article.get("focus_keyword") or "").strip()
    category = str(article.get("category") or "").strip()

    if not 35 <= len(title) <= 65:
        reasons.append(f"seo_title_tamanho:{len(title)}")
    if not 120 <= len(meta) <= 155:
        reasons.append(f"meta_description_tamanho:{len(meta)}")
    if not 3 <= len(focus) <= 100:
        reasons.append("focus_keyword_ausente_ou_invalida")
    if category not in ALLOWED_CATEGORIES:
        reasons.append("categoria_invalida")
    if not editorial_title or title != editorial_title or topic != editorial_title:
        reasons.append("tema_titulo_nao_unificado")

    for pattern in EXPERIENCE_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("alegacao_de_teste_nao_comprovada")
            break
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("instrucao_domestica_de_alto_risco")
            break
    for pattern in MEDICAL_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("alegacao_medica_ou_terapeutica_nao_sustentada")
            break
    for pattern in ABSOLUTE_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("alegacao_absoluta_nao_sustentada")
            break

    allowed_specs = compact(" ".join([str(article.get("product") or ""), editorial_title]))
    for match in NUMERIC_SPEC.finditer(text):
        spec = compact(match.group(0))
        if spec and spec not in allowed_specs:
            reasons.append(f"especificacao_numerica_nao_confirmada:{normalized(match.group(0))}")
            break

    if re.search(r"\b(?:pre[cç]o|desconto|estoque|frete)\s+(?:de|por|atual|agora|gr[aá]tis)\b", folded, re.I):
        reasons.append("condicao_comercial_nao_confirmada")
    if re.search(r"\b(?:material|dimens[aã]o|medida|capacidade|pot[eê]ncia|voltagem)\s+(?:é|e|de)\b.{0,40}\b(?:exatamente|certamente|garantid)", folded, re.I):
        reasons.append("especificacao_nao_confirmada")

    commercial_title = normalized(article.get("product") or "")
    editorial_normalized = normalized(editorial)
    if commercial_title and len(commercial_title) >= 18 and commercial_title in editorial_normalized:
        reasons.append("titulo_comercial_copiado_no_corpo")

    affiliate_link = str(article.get("affiliate_link") or "")
    if not affiliate_link.startswith("https://"):
        reasons.append("link_afiliado_invalido")

    ctas = cta_positions(content)
    if len(ctas) != 2:
        reasons.append(f"quantidade_cta_invalida:{len(ctas)}")
    if affiliate_link:
        link_count = content.count(affiliate_link)
        if link_count != 4:
            reasons.append(f"link_afiliado_quantidade_invalida:{link_count}")

    disclosure_count = plain_text(content).casefold().count("este é um link de afiliado")
    if disclosure_count != 2:
        reasons.append(f"disclosure_afiliado_quantidade_invalida:{disclosure_count}")
    rel_count = len(re.findall(r'rel=["\'][^"\']*nofollow[^"\']*sponsored[^"\']*["\']', content, re.I))
    if rel_count != 4:
        reasons.append(f"rel_afiliado_quantidade_invalida:{rel_count}")

    consult_anchor_count = len(re.findall(
        r'<a\b[^>]*>\s*consultar\s+o\s+modelo\s+na\s+Shopee\s*</a>', content, re.I
    ))
    if consult_anchor_count != 2:
        reasons.append(f"link_consulta_contextual_quantidade_invalida:{consult_anchor_count}")
    consult_text_count = plain_text(content).casefold().count(CTA_CONSULT_TEXT.casefold())
    if consult_text_count != 2:
        reasons.append(f"chamada_consulta_contextual_quantidade_invalida:{consult_text_count}")

    product = html.escape(str(article.get("product") or "").strip())
    title_marker = f'class="{CTA_PRODUCT_TITLE_CLASS}"'
    if content.count(title_marker) != 2:
        reasons.append("titulo_produto_cta_quantidade_invalida")
    if product:
        title_pattern = re.compile(
            rf'<p\s+class="{re.escape(CTA_PRODUCT_TITLE_CLASS)}"[^>]*>\s*{re.escape(product)}\s*</p>', re.I
        )
        if len(title_pattern.findall(content)) != 2:
            reasons.append("titulo_produto_cta_nao_fiel")

    image_url = str(article.get("image_url") or "").strip()
    if not image_url.startswith("https://"):
        reasons.append("imagem_produto_ausente")
    elif content.count(image_url) != 2:
        reasons.append(f"imagem_produto_quantidade_invalida:{content.count(image_url)}")

    h2_matches_content = list(re.finditer(r"<h2\b[^>]*>.*?</h2>", content, re.I | re.S))
    if len(ctas) == 2 and len(h2_matches_content) >= 3:
        if not (h2_matches_content[1].end() < ctas[0] < h2_matches_content[2].start()):
            reasons.append("cta_1_fora_depois_da_segunda_secao")
        if not (ctas[1] > h2_matches_content[-1].end()):
            reasons.append("cta_2_nao_esta_depois_da_ultima_secao")

    if internal_link_count(content) < 1:
        reasons.append("link_interno_ausente")

    focus_tokens = token_set(focus)
    body_tokens = token_set(editorial)
    if focus_tokens and len(focus_tokens & body_tokens) < min(2, len(focus_tokens)):
        reasons.append("focus_keyword_sem_cobertura_no_texto")

    status = "REJECTED" if reasons else "DRAFT_READY"
    return {
        "status": status,
        "reasons": sorted(set(reasons)),
        "warnings": sorted(set(warnings)),
        "metrics": {
            "word_count": wc,
            "h2_count": h2_count,
            "internal_links": internal_link_count(content),
            "seo_title_length": len(title),
            "meta_description_length": len(meta),
            "cta_count": len(ctas),
        },
        "safety_class": "STANDARD",
    }
