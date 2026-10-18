import html
import re
import unicodedata

SITE_URL = "https://oficina.radartechbr.com.br"
CTA_CLASS = "og-produto-relacionado"

STOPWORDS = {
    "a","as","o","os","um","uma","de","da","das","do","dos","e","em","no","na","nos","nas",
    "para","por","com","sem","ao","aos","ou","como","que","qual","se","antes","mais","menos",
    "seu","sua","uso","usar","sobre"
}
HUMAN_REVIEW_TERMS = (
    "freio", "direcao", "suspensao", "airbag", "macaco hidraulico", "cavalete", "elevador automotivo",
    "solda", "soldador", "esmerilhadeira", "serra", "disco de corte", "bateria automotiva",
    "carregador de bateria", "instalacao eletrica", "torquimetro", "torque", "combustivel",
    "extintor", "oculos de protecao", "luva de protecao", "protetor auricular"
)
EXPERIENCE_PATTERNS = (
    r"\b(?:n[oó]s\s+)?testamos\b",
    r"\bem nossos? testes?\b",
    r"\bna nossa experi[eê]ncia\b",
    r"\bcomprovamos\b",
)
DANGEROUS_INSTRUCTION_PATTERNS = (
    r"\b(?:remova|solte|desmonte|substitua|troque)\b.{0,50}\b(?:freio|airbag|dire[cç][aã]o|suspens[aã]o)\b",
    r"\b(?:levante|eleve)\b.{0,50}\bve[ií]culo\b",
    r"\b(?:corte|solde|esmerilhe)\b.{0,60}\b(?:metal|chassi|carroceria|pe[cç]a)\b",
    r"\b(?:ligue|conecte|ponte)\b.{0,60}\b(?:bateria|rede el[eé]trica|tomada)\b",
)
ABSOLUTE_CLAIM_PATTERNS = (
    r"\bgarant(?:e|ir|indo|ido)\b.{0,90}\b(?:sempre|seguran[cç]a|prote[cç][aã]o|condi[cç][oõ]es? de uso)\b",
    r"\b(?:100\s*%|totalmente)\s+(?:seguro|protegido|garantido)\b",
    r"\bprote[cç][aã]o\s+garantida\b",
)
NUMERIC_SPEC = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:kg|g|cm|mm|m|l|ml|w|v|ah|mah|nm|psi|bar|%|hz|rpm|amp|ampere|amperes)\b",
    re.I,
)
PROMPT_LEAKAGE = ("regras obrigatorias", "responda somente", "fragmento html", "rascunho atual")
FASTENER_AS_TOOL = re.compile(
    r"\bferramentas?\s+(?:pequenas?|menores?|mi[uú]das?)\b.{0,100}\b(?:parafusos?|pregos?|porcas?|arruelas?|buchas?)\b",
    re.I | re.S,
)
FIXED_FREQUENCY_PATTERNS = (
    r"\bferramentas?\s+que\s+(?:s[aã]o\s+)?(?:utilizadas?|usadas?)\s+(?:diariamente|todos os dias)\b",
    r"\bferramentas?\s+de\s+uso\s+di[aá]rio\b",
    r"\bitens?\s+(?:menos\s+usados?|raramente\s+usados?|usados?\s+com\s+menos\s+frequ[eê]ncia)\b",
    r"\bferramentas?\s+(?:menos\s+usadas?|raramente\s+usadas?|usadas?\s+com\s+menos\s+frequ[eê]ncia)\b",
)


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


def safety_class(item):
    title = item.get("editorial_title") or item.get("topic") or ""
    text = normalized(" ".join([
        str(item.get("product") or ""),
        str(title),
        str(item.get("category") or ""),
    ]))
    hits = [term for term in HUMAN_REVIEW_TERMS if term in text]
    if normalized(item.get("category")) == "seguranca e protecao" or hits:
        return "HUMAN_REVIEW", sorted(set(hits))
    return "STANDARD", []


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

    if wc < 850:
        reasons.append(f"word_count_baixo:{wc}")
    if wc > 1600:
        reasons.append(f"word_count_alto:{wc}")
    if h2_count < 4:
        reasons.append(f"poucos_h2:{h2_count}")
    if h2_titles and len(h2_titles) != len(set(h2_titles)):
        reasons.append("h2_repetido")
    if re.search(r"<h1\b", content, re.I):
        reasons.append("h1_no_conteudo")
    if re.search(r"<(?:script|style|iframe)\b", content, re.I):
        reasons.append("html_nao_permitido")
    if "```" in content:
        reasons.append("artefato_markdown")

    n = normalized(editorial)
    if any(marker in n for marker in PROMPT_LEAKAGE):
        reasons.append("vazamento_de_prompt")

    title = str(article.get("seo_title") or "").strip()
    editorial_title = str(article.get("editorial_title") or article.get("topic") or "").strip()
    topic = str(article.get("topic") or editorial_title).strip()
    meta = str(article.get("meta_description") or "").strip()
    focus = str(article.get("focus_keyword") or "").strip()
    category = str(article.get("category") or "").strip()

    if not 25 <= len(title) <= 65:
        reasons.append(f"seo_title_tamanho:{len(title)}")
    if not 110 <= len(meta) <= 160:
        reasons.append(f"meta_description_tamanho:{len(meta)}")
    if not 3 <= len(focus) <= 100:
        reasons.append("focus_keyword_ausente_ou_invalida")
    if not category:
        reasons.append("categoria_ausente")

    if not editorial_title or title != editorial_title or topic != editorial_title:
        reasons.append("tema_titulo_nao_unificado")

    for pattern in EXPERIENCE_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("alegacao_de_teste_nao_comprovada")
            break

    for pattern in DANGEROUS_INSTRUCTION_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("instrucao_procedimental_de_alto_risco")
            break

    allowed_specs = compact(" ".join([
        str(article.get("product") or ""),
        str(editorial_title),
    ]))
    for match in NUMERIC_SPEC.finditer(text):
        spec = compact(match.group(0))
        if spec and spec not in allowed_specs:
            reasons.append(f"especificacao_numerica_nao_confirmada:{normalized(match.group(0))}")
            break

    if re.search(r"\b(?:compat[ií]vel com todos|compatibilidade universal|serve em qualquer)\b", folded, re.I):
        reasons.append("compatibilidade_universal_nao_confirmada")

    for pattern in ABSOLUTE_CLAIM_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("alegacao_absoluta_de_seguranca_ou_conservacao")
            break

    if re.search(r"\b(?:pre[cç]o|desconto|estoque)\s+(?:de|por|atual|agora)\b", folded, re.I):
        reasons.append("condicao_comercial_nao_confirmada")
    if FASTENER_AS_TOOL.search(editorial):
        reasons.append("classificacao_tecnica_incorreta_fixadores_como_ferramentas")

    for pattern in FIXED_FREQUENCY_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("frequencia_de_uso_assumida_sem_contexto")
            break

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
        if link_count != 2:
            reasons.append(f"link_afiliado_quantidade_invalida:{link_count}")

    disclosure_count = plain_text(content).casefold().count("este é um link de afiliado")
    if disclosure_count != 2:
        reasons.append(f"disclosure_afiliado_quantidade_invalida:{disclosure_count}")

    rel_count = len(re.findall(r'rel=["\'][^"\']*nofollow[^"\']*sponsored[^"\']*["\']', content, re.I))
    if rel_count != 2:
        reasons.append(f"rel_afiliado_quantidade_invalida:{rel_count}")

    image_url = str(article.get("image_url") or "").strip()
    if image_url.startswith("https://"):
        image_count = content.count(image_url)
        if image_count != 2:
            reasons.append(f"imagem_produto_quantidade_invalida:{image_count}")

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

    sclass, hits = safety_class(article)
    if sclass == "HUMAN_REVIEW":
        warnings.append("revisao_humana_obrigatoria:" + ",".join(hits or ["categoria_sensivel"]))

    status = "REJECTED" if reasons else ("HUMAN_REVIEW_REQUIRED" if warnings else "DRAFT_READY")
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
        "safety_class": sclass,
    }
