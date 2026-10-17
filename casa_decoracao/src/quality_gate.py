import html
import re
import unicodedata

SITE_URL = "https://casaedecoracao.radartechbr.com.br"

STOPWORDS = {
    "a", "as", "o", "os", "um", "uma", "uns", "umas", "de", "da", "das", "do", "dos",
    "e", "em", "no", "na", "nos", "nas", "para", "por", "com", "sem", "ao", "aos", "ou",
    "como", "que", "qual", "quais", "se", "antes", "mais", "menos", "seu", "sua", "seus", "suas",
    "dia", "uso", "usar", "sobre", "entre", "pelo", "pela", "pelos", "pelas",
}

BUY_TERMS = {
    "escolher", "escolha", "comprar", "compra", "conferir", "observar", "avaliar", "comparar",
    "medir", "medidas", "diferenças", "diferencas", "vale", "pena",
}
ORGANIZE_TERMS = {"organizar", "organização", "organizacao", "guardar", "armazenar", "armazenamento", "despensa", "armário", "armario"}
CARE_TERMS = {"limpar", "limpeza", "cuidar", "cuidados", "manutenção", "manutencao", "lavar", "conservar", "proteção", "protecao", "proteger"}
DECOR_TERMS = {"decoração", "decoracao", "decorar", "combinar", "visual", "mesa", "estilo", "ambiente"}
SAFETY_TERMS = {"segurança", "seguranca", "risco", "lâmina", "lamina", "mistura", "misturas", "químico", "quimico"}

# Marcadores que só devem existir nas instruções internas de geração. Evitar
# expressões editoriais legítimas usadas no CTA, como "produto relacionado".
PROMPT_LEAKAGE = (
    "regras obrigatórias:",
    "regras obrigatorias:",
    "pauta:",
    "responda somente",
    "fragmento html",
    "rascunho atual:",
    "você é editor sênior",
    "voce e editor senior",
)


def strip_accents(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def normalized(value):
    value = strip_accents(value).casefold()
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def plain_text(value):
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


def token_set(value):
    return {
        token for token in normalized(value).split()
        if len(token) >= 3 and token not in STOPWORDS
    }


def word_count(content_html):
    return len(re.findall(r"\b[\wÀ-ÿ'-]+\b", plain_text(content_html), flags=re.UNICODE))


def trim_at_word(value, limit):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(value) <= limit:
        return value
    short = value[: limit + 1].rsplit(" ", 1)[0]
    return short.rstrip(" -:;,.")


def focus_keyword_from_item(item):
    topic = str(item.get("topic") or "").strip()
    product = str(item.get("product") or "").strip()
    topic_tokens = token_set(topic)
    product_tokens = token_set(product)
    if len(topic_tokens & product_tokens) >= 2:
        keyword = topic
    else:
        keyword = f"{product} {topic}"
    return trim_at_word(keyword, 90)


def seo_title_from_item(item):
    topic = str(item.get("topic") or "").strip()
    product = str(item.get("product") or "").strip()
    if topic:
        topic = topic[0].upper() + topic[1:]
    if len(token_set(topic) & token_set(product)) >= 2:
        candidate = topic
    else:
        candidate = f"{topic}: {product}"
    return trim_at_word(candidate, 60)


def meta_description_from_item(item):
    topic = str(item.get("topic") or "").strip()
    product = str(item.get("product") or "").strip()
    if topic:
        topic = topic[0].upper() + topic[1:]
    candidate = f"{topic}. Veja critérios práticos e o que conferir no {product.lower()} antes de decidir, sem depender de especificações não confirmadas."
    if len(candidate) < 115:
        candidate += " Confira medidas, materiais, uso e condições no anúncio."
    return trim_at_word(candidate, 158)


def intent_signature(value):
    tokens = token_set(value)
    scores = {
        "buy": len(tokens & {strip_accents(x).casefold() for x in BUY_TERMS}),
        "organize": len(tokens & {strip_accents(x).casefold() for x in ORGANIZE_TERMS}),
        "care": len(tokens & {strip_accents(x).casefold() for x in CARE_TERMS}),
        "decor": len(tokens & {strip_accents(x).casefold() for x in DECOR_TERMS}),
        "safety": len(tokens & {strip_accents(x).casefold() for x in SAFETY_TERMS}),
    }
    label, score = max(scores.items(), key=lambda row: row[1])
    return label if score else "general"


def jaccard(left, right):
    left = set(left)
    right = set(right)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def duplicate_paragraphs(content_html):
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p>", str(content_html or ""), flags=re.I | re.S)
    paragraphs = [p for p in paragraphs if len(plain_text(p)) >= 100]
    tokenized = [token_set(p) for p in paragraphs]
    for i in range(len(tokenized)):
        for j in range(i + 1, len(tokenized)):
            if jaccard(tokenized[i], tokenized[j]) >= 0.90:
                return True
    return False


def internal_link_count(content_html):
    hrefs = re.findall(r"href=[\"']([^\"']+)[\"']", str(content_html or ""), flags=re.I)
    return sum(1 for href in hrefs if href.startswith("/") or href.startswith(SITE_URL))


def draft_quality(article):
    reasons = []
    content = str(article.get("content_html") or "")
    editorial = str(article.get("editorial_html") or content)
    title = str(article.get("seo_title") or "").strip()
    meta = str(article.get("meta_description") or "").strip()
    focus = str(article.get("focus_keyword") or "").strip()
    category = str(article.get("category") or "").strip()
    affiliate_link = str(article.get("affiliate_link") or "").strip()
    product = str(article.get("product") or "").strip()

    wc = int(article.get("word_count") or word_count(editorial))
    h2_count = len(re.findall(r"<h2\b", editorial, flags=re.I))
    h2_titles = [normalized(x) for x in re.findall(r"<h2\b[^>]*>(.*?)</h2>", editorial, flags=re.I | re.S)]

    if wc < 700:
        reasons.append(f"word_count_baixo:{wc}")
    if wc > 1700:
        reasons.append(f"word_count_alto:{wc}")
    if h2_count < 3:
        reasons.append(f"poucos_h2:{h2_count}")
    if len(h2_titles) != len(set(h2_titles)):
        reasons.append("h2_repetido")
    if re.search(r"<h1\b", content, flags=re.I):
        reasons.append("h1_no_conteudo")
    if re.search(r"<(?:script|style|iframe)\b", content, flags=re.I):
        reasons.append("html_nao_permitido")
    if "```" in content or re.search(r"^\s*#{1,6}\s", plain_text(content), flags=re.M):
        reasons.append("artefato_markdown")
    editorial_norm = normalized(editorial)
    if any(normalized(marker) in editorial_norm for marker in PROMPT_LEAKAGE):
        reasons.append("vazamento_de_prompt")
    if duplicate_paragraphs(editorial):
        reasons.append("paragrafos_quase_duplicados")

    if not 25 <= len(title) <= 65:
        reasons.append(f"seo_title_tamanho:{len(title)}")
    if not 110 <= len(meta) <= 160:
        reasons.append(f"meta_description_tamanho:{len(meta)}")
    if not 3 <= len(focus) <= 100:
        reasons.append("focus_keyword_ausente_ou_invalida")
    if not category:
        reasons.append("categoria_ausente")

    focus_tokens = token_set(focus)
    body_tokens = token_set(editorial)
    if focus_tokens and len(focus_tokens & body_tokens) < min(2, len(focus_tokens)):
        reasons.append("focus_keyword_sem_cobertura_no_texto")

    product_tokens = token_set(product)
    if product_tokens and len(product_tokens & body_tokens) < min(2, len(product_tokens)):
        reasons.append("produto_pouco_relacionado_ao_texto")

    if not affiliate_link.startswith("https://"):
        reasons.append("link_afiliado_invalido")
    if affiliate_link and affiliate_link not in content:
        reasons.append("link_afiliado_ausente_do_html")
    if not re.search(r"rel=[\"'][^\"']*nofollow[^\"']*sponsored[^\"']*[\"']", content, flags=re.I):
        reasons.append("rel_afiliado_incorreto")
    if "link de afiliado" not in plain_text(content).casefold():
        reasons.append("disclosure_afiliado_ausente")
    links = internal_link_count(content)
    if links < 1:
        reasons.append("link_interno_ausente")

    return {
        "status": "DRAFT_READY" if not reasons else "REJECTED",
        "reasons": reasons,
        "metrics": {
            "word_count": wc,
            "h2_count": h2_count,
            "seo_title_length": len(title),
            "meta_description_length": len(meta),
            "internal_links": links,
        },
    }


def cannibalization_reasons(article, existing_posts, current_slug=""):
    reasons = []
    candidate_title = str(article.get("seo_title") or article.get("topic") or "")
    candidate_topic = str(article.get("topic") or "")
    candidate_product = str(article.get("product") or "")
    candidate_product_tokens = token_set(candidate_product)
    candidate_title_tokens = token_set(candidate_title)
    candidate_intent = intent_signature(candidate_topic)

    for post in existing_posts or []:
        slug = str(post.get("slug") or "")
        if current_slug and slug == current_slug:
            continue
        title_obj = post.get("title") or {}
        excerpt_obj = post.get("excerpt") or {}
        content_obj = post.get("content") or {}
        existing_title = title_obj.get("rendered") if isinstance(title_obj, dict) else str(title_obj)
        existing_excerpt = excerpt_obj.get("rendered") if isinstance(excerpt_obj, dict) else str(excerpt_obj)
        existing_content = content_obj.get("rendered") if isinstance(content_obj, dict) else str(content_obj)
        existing_text = " ".join([existing_title or "", existing_excerpt or "", existing_content or ""])
        existing_title_tokens = token_set(existing_title)

        title_similarity = jaccard(candidate_title_tokens, existing_title_tokens)
        if title_similarity >= 0.55:
            reasons.append(f"titulo_semelhante_post:{post.get('id')}")
            continue

        if candidate_product_tokens:
            existing_tokens = token_set(existing_text)
            product_coverage = len(candidate_product_tokens & existing_tokens) / max(1, len(candidate_product_tokens))
            if product_coverage >= 0.60:
                existing_intent = intent_signature(f"{existing_title} {existing_excerpt}")
                if candidate_intent != "general" and existing_intent == candidate_intent:
                    reasons.append(f"mesmo_produto_mesma_intencao_post:{post.get('id')}")

    return sorted(set(reasons))


def publication_quality(article, existing_posts=None, current_slug=""):
    base = draft_quality(article)
    reasons = list(base["reasons"])
    reasons.extend(cannibalization_reasons(article, existing_posts or [], current_slug=current_slug))

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
        "reasons": reasons,
        "metrics": base["metrics"],
    }
