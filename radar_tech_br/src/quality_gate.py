import html
import re
import unicodedata

SITE_URL = "https://radartechbr.com.br"
CTA_CLASS = "og-produto-relacionado"
CTA_PRODUCT_TITLE_CLASS = "og-produto-titulo-original"
CTA_CONSULT_TEXT = "consultar o modelo na Shopee"
MIN_WORDS = 900
MAX_WORDS = 1400
ALLOWED_CATEGORIES = {"Tecnologia", "Casa & Decoração", "Cozinha & Utilidades", "Ferramentas & Automotivo", "Moda & Beleza"}

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
    r"\bpreservar\s+a\s+qualidade\b",
    r"\bevitar?\s+acidentes?\b",
)
ACCESSIBILITY_CLAIM_PATTERNS = (
    r"\b(?:mobilidade reduzida|idos[oa]s?)\b.{0,100}\b(?:benefici|facilita|ideal|indicado|acess[ií]vel)\w*\b",
    r"\b(?:benefici|facilita|ideal|indicado|acess[ií]vel)\w*\b.{0,100}\b(?:mobilidade reduzida|idos[oa]s?)\b",
)
UNVERIFIED_INSTALLATION_PATTERNS = (
    r"\b(?:pode|podem|deve|devem)\s+ser\s+(?:instalad[oa]s?|fixad[oa]s?|montad[oa]s?)\b",
    r"\b(?:instala[cç][aã]o|fixa[cç][aã]o)\s+(?:é|e)\s+(?:simples|f[aá]cil|vers[aá]til)\b",
)
UNSOURCED_TREND_PATTERNS = (
    r"\btem\s+se\s+destacado\b",
    r"\b(?:é|e)\s+(?:uma\s+)?op[cç][aã]o\s+popular\b",
)
CAUSAL_BENEFIT_PATTERNS = (
    r"\breduz\w*\b.{0,70}\b(?:tempo|estresse|esfor[cç]o|movimento)\b",
    r"\bmenos\s+(?:estressante|cansativo)\b",
)
NUMERIC_SPEC = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:kg|g|cm|mm|m|l|ml|w|v|ah|mah|nm|psi|bar|%|hz|rpm|amp|ampere|amperes)\b",
    re.I,
)
PROMPT_LEAKAGE = ("regras obrigatorias", "responda somente", "fragmento html", "rascunho atual")


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
    if hits:
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

    if wc < MIN_WORDS:
        reasons.append(f"word_count_baixo:{wc}")
    if wc > MAX_WORDS:
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
    elif category not in ALLOWED_CATEGORIES:
        reasons.append("categoria_radar_invalida")

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

    for pattern in ACCESSIBILITY_CLAIM_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("alegacao_de_acessibilidade_nao_sustentada")
            break

    for pattern in UNVERIFIED_INSTALLATION_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("instalacao_ou_fixacao_nao_confirmada")
            break

    for pattern in UNSOURCED_TREND_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("alegacao_de_popularidade_sem_fonte")
            break

    for pattern in CAUSAL_BENEFIT_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("beneficio_funcional_nao_sustentado")
            break

    if re.search(r"\b(?:pre[cç]o|desconto|estoque)\s+(?:de|por|atual|agora)\b", folded, re.I):
        reasons.append("condicao_comercial_nao_confirmada")

    commercial_title = normalized(article.get("product") or "")
    editorial_normalized = normalized(editorial)
    if commercial_title and len(commercial_title) >= 18 and commercial_title in editorial_normalized:
        reasons.append("titulo_comercial_copiado_no_corpo")

    product_raw = str(article.get("product") or "").strip()
    product_escaped = html.escape(product_raw)
    marker = f'class="{CTA_PRODUCT_TITLE_CLASS}"'
    if content.count(marker) != 2:
        reasons.append(f"titulo_produto_cta_quantidade_invalida:{content.count(marker)}")
    if product_escaped:
        title_pattern = re.compile(
            rf'<p\s+class="{re.escape(CTA_PRODUCT_TITLE_CLASS)}"[^>]*>\s*{re.escape(product_escaped)}\s*</p>',
            re.I,
        )
        if len(title_pattern.findall(content)) != 2:
            reasons.append("titulo_produto_cta_nao_fiel")
        if re.search(rf"<h[1-6][^>]*>[^<]*{re.escape(product_escaped)}", content, re.I):
            reasons.append("titulo_produto_em_heading")

    image_url = str(article.get("image_url") or "").strip()
    if not image_url.startswith("https://"):
        reasons.append("imagem_produto_ausente_ou_invalida")

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
        r'<a\b[^>]*>\s*consultar\s+o\s+modelo\s+na\s+Shopee\s*</a>',
        content,
        re.I,
    ))
    if consult_anchor_count != 2:
        reasons.append(f"link_consulta_contextual_quantidade_invalida:{consult_anchor_count}")

    consult_text_count = plain_text(content).casefold().count(CTA_CONSULT_TEXT.casefold())
    if consult_text_count != 2:
        reasons.append(f"chamada_consulta_contextual_quantidade_invalida:{consult_text_count}")

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
