import html
import re
import unicodedata

SITE_URL = "https://oficina.radartechbr.com.br"
STOPWORDS = {"a","as","o","os","um","uma","de","da","das","do","dos","e","em","no","na","nos","nas","para","por","com","sem","ao","aos","ou","como","que","qual","se","antes","mais","menos","seu","sua","uso","usar","sobre"}
HUMAN_REVIEW_TERMS = (
    "freio", "direcao", "suspensao", "airbag", "macaco hidraulico", "cavalete", "elevador automotivo",
    "solda", "soldador", "esmerilhadeira", "serra", "disco de corte", "bateria automotiva", "carregador de bateria",
    "instalacao eletrica", "torquimetro", "torque", "combustivel", "extintor", "oculos de protecao", "luva de protecao", "protetor auricular"
)
EXPERIENCE_PATTERNS = (r"\b(?:n[oó]s\s+)?testamos\b", r"\bem nossos? testes?\b", r"\bna nossa experi[eê]ncia\b", r"\bcomprovamos\b")
DANGEROUS_INSTRUCTION_PATTERNS = (
    r"\b(?:remova|solte|desmonte|substitua|troque)\b.{0,50}\b(?:freio|airbag|dire[cç][aã]o|suspens[aã]o)\b",
    r"\b(?:levante|eleve)\b.{0,50}\bve[ií]culo\b",
    r"\b(?:corte|solde|esmerilhe)\b.{0,60}\b(?:metal|chassi|carroceria|pe[cç]a)\b",
    r"\b(?:ligue|conecte|ponte)\b.{0,60}\b(?:bateria|rede el[eé]trica|tomada)\b",
)
NUMERIC_SPEC = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:kg|g|cm|mm|m|l|ml|w|v|a|ah|mah|nm|psi|bar|%|hz|rpm)\b", re.I)
PROMPT_LEAKAGE = ("regras obrigatorias", "responda somente", "fragmento html", "pauta:", "rascunho atual:")


def normalized(value):
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def plain_text(value):
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


def token_set(value):
    return {t for t in normalized(value).split() if len(t) >= 3 and t not in STOPWORDS}


def word_count(value):
    return len(re.findall(r"\b[\wÀ-ÿ'-]+\b", plain_text(value), re.UNICODE))


def safety_class(item):
    text = normalized(" ".join([str(item.get("product") or ""), str(item.get("topic") or ""), str(item.get("category") or "")]))
    hits = [term for term in HUMAN_REVIEW_TERMS if term in text]
    if normalized(item.get("category")) == "seguranca e protecao" or hits:
        return "HUMAN_REVIEW", sorted(set(hits))
    return "STANDARD", []


def quality(article):
    reasons = []
    warnings = []
    content = str(article.get("content_html") or "")
    editorial = str(article.get("editorial_html") or content)
    text = plain_text(editorial)
    folded = text.casefold()
    wc = int(article.get("word_count") or word_count(editorial))
    h2_count = len(re.findall(r"<h2\b", editorial, re.I))
    if wc < 850: reasons.append(f"word_count_baixo:{wc}")
    if wc > 1600: reasons.append(f"word_count_alto:{wc}")
    if h2_count < 4: reasons.append(f"poucos_h2:{h2_count}")
    if re.search(r"<h1\b", content, re.I): reasons.append("h1_no_conteudo")
    if re.search(r"<(?:script|style|iframe)\b", content, re.I): reasons.append("html_nao_permitido")
    n = normalized(editorial)
    if any(marker in n for marker in PROMPT_LEAKAGE): reasons.append("vazamento_de_prompt")
    for pattern in EXPERIENCE_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("alegacao_de_teste_nao_comprovada"); break
    for pattern in DANGEROUS_INSTRUCTION_PATTERNS:
        if re.search(pattern, folded, re.I):
            reasons.append("instrucao_procedimental_de_alto_risco"); break
    allowed_specs = normalized(" ".join([str(article.get("product") or ""), str(article.get("topic") or "")]))
    for match in NUMERIC_SPEC.finditer(text):
        spec = normalized(match.group(0))
        if spec and spec not in allowed_specs:
            reasons.append(f"especificacao_numerica_nao_confirmada:{spec}"); break
    if re.search(r"\b(?:compat[ií]vel com todos|compatibilidade universal|serve em qualquer)\b", folded, re.I):
        reasons.append("compatibilidade_universal_nao_confirmada")
    if re.search(r"\b(?:garante|100% seguro|prote[cç][aã]o garantida)\b", folded, re.I):
        reasons.append("alegacao_absoluta_de_seguranca")
    if re.search(r"\b(?:pre[cç]o|desconto|estoque)\s+(?:de|por|atual|agora)\b", folded, re.I):
        reasons.append("condicao_comercial_nao_confirmada")
    affiliate_link = str(article.get("affiliate_link") or "")
    if not affiliate_link.startswith("https://"): reasons.append("link_afiliado_invalido")
    if affiliate_link and affiliate_link not in content: reasons.append("link_afiliado_ausente")
    if "link de afiliado" not in plain_text(content).casefold(): reasons.append("disclosure_afiliado_ausente")
    if not re.search(r"rel=[\"'][^\"']*nofollow[^\"']*sponsored[^\"']*[\"']", content, re.I): reasons.append("rel_afiliado_incorreto")
    sclass, hits = safety_class(article)
    if sclass == "HUMAN_REVIEW": warnings.append("revisao_humana_obrigatoria:" + ",".join(hits or ["categoria_sensivel"]))
    status = "REJECTED" if reasons else ("HUMAN_REVIEW_REQUIRED" if warnings else "DRAFT_READY")
    return {"status": status, "reasons": sorted(set(reasons)), "warnings": sorted(set(warnings)), "metrics": {"word_count": wc, "h2_count": h2_count}, "safety_class": sclass}
