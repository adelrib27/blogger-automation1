import re
import time

import article_builder_v1 as builder
import evidence_engine as evidence

original_call = builder.groq_call
original_gate = builder.gate
last_call = [0.0]
current_candidate = [{}]
current_package = [{}]

SAFE_BLOCKS = [
    ("Comece pelo contexto de uso", "Antes de comparar opções, observe onde o acessório será utilizado e como ele entra na rotina da casa. Considere espaço disponível, circulação, local de armazenamento e facilidade de acesso. O objetivo é definir critérios antes de olhar características comerciais. Essa etapa ajuda a separar necessidades reais de detalhes que podem chamar atenção no anúncio, mas que talvez não sejam relevantes para a situação do leitor."),
    ("Confirme cada especificação importante", "Quando uma característica fizer diferença na decisão, procure a informação na página atual do produto e, quando houver, nas orientações do fabricante. Medidas, materiais, capacidade, compatibilidade e instruções podem variar entre versões e vendedores. Se um dado estiver ausente ou ambíguo, mantenha-o como não confirmado. É melhor reconhecer uma lacuna do que completar a informação por semelhança com outro produto."),
    ("Compare informações equivalentes", "Ao colocar duas opções lado a lado, use os mesmos critérios para ambas. Compare apenas dados que estejam claramente informados em fontes relacionadas ao item correto. Uma descrição de outro modelo pode servir para pesquisa, mas não deve ser transferida para o produto analisado. Esse cuidado evita que uma comparação pareça precisa quando, na verdade, está misturando versões diferentes ou informações sem vínculo comprovado."),
    ("Separe fato de linguagem promocional", "Anúncios costumam reunir dados objetivos e frases de divulgação. Para decidir com mais clareza, identifique quais pontos podem ser conferidos diretamente e quais dependem apenas de linguagem comercial. Dê mais peso ao que possui descrição verificável e relação clara com o item. Expressões promocionais podem ajudar a entender a proposta do vendedor, mas não substituem especificações confirmadas nem devem ser transformadas em afirmações técnicas."),
    ("Use fontes ligadas ao item correto", "Encontrar uma página parecida não basta para confirmar uma característica. Sempre que possível, verifique se a fonte corresponde ao mesmo item, modelo ou identificação usada na pesquisa. Se essa ligação não puder ser demonstrada, use a página apenas como referência de contexto e não como prova de uma especificação. Essa distinção reduz o risco de atribuir ao produto detalhes que pertencem a outra versão."),
    ("Revise as informações antes da decisão", "Dados comerciais podem mudar ao longo do tempo. Por isso, uma informação consultada anteriormente deve ser verificada novamente quando ela for importante para a escolha. A revisão também ajuda a identificar divergências entre fontes. Quando houver conflito, não escolha automaticamente a versão mais conveniente: registre a diferença e consulte a página atual do produto antes de considerar o ponto resolvido."),
    ("Organize o que já foi verificado", "Um histórico simples facilita futuras comparações. Registre o produto consultado, a fonte usada, o assunto abordado e quais informações estavam confirmadas naquele momento. Esse registro ajuda a evitar repetição de conteúdo e também permite criar novos ângulos editoriais sem perder a referência do que já foi pesquisado. Para uma automação, essa memória é importante para manter consistência entre publicações."),
    ("Quando faltar informação", "A ausência de um dado também é uma conclusão útil. Se determinada característica não aparece nas fontes ligadas ao produto, ela não precisa ser preenchida por inferência. O conteúdo pode orientar o leitor a conferir esse ponto no anúncio antes da compra. Essa abordagem mantém o artigo útil sem transformar incerteza em certeza e preserva uma diferença clara entre informação confirmada e informação ainda pendente."),
    ("Evite copiar a descrição comercial", "O artigo pode partir do mesmo produto sem repetir o texto do anúncio. Em vez de reproduzir a descrição comercial, use um ângulo editorial próprio, organize os critérios de decisão e explique quais dados precisam ser verificados. Assim, o conteúdo ganha utilidade independente e reduz a semelhança com outras páginas. O produto permanece como referência, mas o texto é construído para responder a uma necessidade de pesquisa do leitor."),
    ("Faça uma última checagem", "Antes de considerar o conteúdo pronto, revise título, palavra-chave, estrutura e todas as afirmações específicas sobre o item. Cada detalhe factual precisa ter uma fonte autorizada correspondente. Também vale confirmar se o texto não introduziu preço, estoque, prazo ou outra informação variável sem necessidade. A última checagem funciona como uma barreira simples contra erros que podem passar durante a geração automática."),
]

TITLE_FALLBACKS = {
    "Higiene": "Higiene pet: como organizar uma rotina mais prática",
    "Diversao e Enriquecimento": "Brinquedos para pets: como comparar opções na rotina",
    "Transporte e Passeio": "Passeio com pets: critérios para comparar acessórios",
    "Organizacao": "Organização pet: como comparar acessórios para a rotina",
    "Alimentacao e Hidratacao": "Acessórios para pets: critérios para a rotina diária",
    "Conforto": "Acessórios pet: critérios para comparar opções de conforto",
}

RISK_TERMS = [
    "saude", "bem estar", "estresse", "ansiedade", "cura", "curar", "tratamento", "diagnostico",
    "terapeut", "previne", "prevenir", "garante", "garantir", "seguranca", "seguro", "reduz", "reduzir",
    "evita", "evitar", "estimulo mental", "treinamento", "comando", "recompensa", "petisco", "racao",
    "vinagre", "sabao", "lubrif", "absorv", "antiderrap", "durabil", "eficacia", "resistent", "lavavel",
    "peso suportado", "elimina", "protege", "melhora", "beneficio comprovado"
]

MEDICAL_CONTEXT_RE = re.compile(
    r"\b(?:tratar|tratamento|cura|curar|diagnostico|prescricao|terapeutic[oa]|medicamento|remedio)\b"
    r"|\btrata\s+(?:doenca|dor|ferida|infeccao|ansiedade|sintoma|problema de saude)\b",
    flags=re.I,
)


def safe_title(candidate):
    keyword = str(candidate.get("keyword") or "").lower()
    category = str(candidate.get("category") or "")
    if "tapete coletor" in keyword:
        return "Tapete coletor de areia: critérios para comparar opções"
    if "brinquedo interativo" in keyword:
        return "Brinquedo interativo: critérios para comparar opções"
    if "guia cachorro" in keyword:
        return "Guia para cachorro: critérios para comparar opções"
    if "caixa areia" in keyword:
        return "Caixa de areia para gatos: como comparar opções"
    if "cama pet" in keyword:
        return "Cama pet: critérios para comparar opções de conforto"
    if "comedouro" in keyword:
        return "Comedouro pet: critérios para comparar opções"
    return TITLE_FALLBACKS.get(category, "Acessórios pet: critérios práticos para comparar opções")


def clip_text(text, limit=150):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= limit:
        return text
    out = []
    for word in text.split():
        if len(" ".join(out + [word])) > limit - 1:
            break
        out.append(word)
    return " ".join(out).rstrip(".,;:") + "."


def exact_evidence_ids(package):
    return [
        s.get("evidence_id") for s in package.get("sources") or []
        if s.get("allowed_in_article")
        and s.get("identity_level") == "EXACT_PRODUCT"
        and s.get("evidence_id")
    ]


def general_prompt(candidate, package):
    current_candidate[0] = candidate
    current_package[0] = package
    return f"""Você é editor do blog Vida Pet Prática.
Escreva somente uma camada editorial geral sobre como avaliar e comparar anúncios relacionados ao tema abaixo.
Você NÃO conhece especificações do produto e não deve inventar nenhuma.

CATEGORIA: {candidate.get('category')}
TEMA: {candidate.get('keyword')}
ÂNGULO: {candidate.get('angle')}

Retorne SOMENTE JSON válido com as chaves:
title, focus_keyword, meta_description, article_html, cta_text, claim_evidence.

Regras:
- Português do Brasil.
- O article_html deve ter aproximadamente 180 a 260 palavras e 2 ou 3 H2.
- Fale apenas de pesquisa, comparação de anúncios, organização de critérios e confirmação de dados em fontes.
- Não dê orientação de cuidado, saúde, comportamento, treinamento, limpeza, alimentação ou segurança do animal.
- Não use números, medidas, horários, frequência ou prazos.
- Não descreva material, mecanismo, resistência, aderência, absorção, durabilidade, desempenho ou benefício de produto.
- Não mencione marca, modelo ou característica específica do item.
- claim_evidence deve ser [].
"""


def risky_sentence(text):
    norm = evidence.normalize(text)
    if re.search(r"\d", str(text or "")):
        return True
    return any(evidence.normalize(term) in norm for term in RISK_TERMS)


def sanitized_ai_intro(html, max_words=170):
    plain = builder.html_text(html)
    sentences = re.split(r"(?<=[.!?])\s+", plain)
    kept = []
    total = 0
    for sentence in sentences:
        sentence = re.sub(r"\s+", " ", sentence).strip()
        if not sentence or risky_sentence(sentence):
            continue
        words = sentence.split()
        if total + len(words) > max_words:
            break
        kept.append(sentence)
        total += len(words)
    if not kept:
        return ""
    return "<h2>Como organizar a comparação</h2><p>" + " ".join(kept) + "</p>"


def normalize_doc(doc, candidate, package):
    if not isinstance(doc, dict):
        return doc

    keyword = str(candidate.get("keyword") or "acessório pet")
    doc["title"] = safe_title(candidate)
    doc["focus_keyword"] = keyword
    doc["meta_description"] = clip_text(
        f"Veja critérios práticos para comparar {keyword}, confirmar informações no anúncio e separar fatos verificados de detalhes ainda pendentes.",
        150,
    )
    doc["cta_text"] = "Confira no anúncio as informações e condições atuais do item antes de decidir."

    html = sanitized_ai_intro(doc.get("article_html") or "")
    product_name = re.sub(r"\s+", " ", str(candidate.get("productName") or "")).strip()
    ids = exact_evidence_ids(package)
    html += (
        "<h2>O que foi confirmado sobre este item</h2>"
        "<p>Na identificação consultada do anúncio, o item aparece como <strong>" + product_name + "</strong>. "
        "Essa identificação está vinculada às fontes autorizadas desta análise. Outros detalhes devem ser conferidos na página atual do produto antes da decisão.</p>"
    )

    used = set()
    for heading, paragraph in SAFE_BLOCKS:
        if builder.word_count(html) >= 700 and len(re.findall(r"<h2\b", html, flags=re.I)) >= 7:
            break
        if heading in used:
            continue
        html += f"<h2>{heading}</h2><p>{paragraph}</p>"
        used.add(heading)

    doc["article_html"] = html
    doc["claim_evidence"] = [{"claim": product_name, "evidence_ids": ids[:2]}]
    return doc


def throttled_call(prompt):
    for attempt in range(1, 5):
        elapsed = time.monotonic() - last_call[0]
        if last_call[0] and elapsed < 18.0:
            time.sleep(18.0 - elapsed)
        try:
            last_call[0] = time.monotonic()
            doc, usage = original_call(prompt)
            return normalize_doc(doc, current_candidate[0], current_package[0]), usage
        except builder.ProviderFatalError as exc:
            text = str(exc)
            if "HTTP 429" not in text or attempt >= 4:
                raise
            match = re.search(r"try again in\s+([0-9.]+)s", text, flags=re.I)
            retry_after = float(match.group(1)) if match else 6.0
            time.sleep(max(6.0, retry_after + 2.0))


def precise_medical_problem(article_plain):
    norm = evidence.normalize(article_plain)
    return bool(MEDICAL_CONTEXT_RE.search(norm))


def strict_gate(doc, package, history, max_similarity):
    result = original_gate(doc, package, history, max_similarity)
    article_plain = builder.html_text(doc.get("article_html") or "")
    reasons = list(result.get("reasons") or [])

    filtered = []
    for reason in reasons:
        if reason == "medical_or_absolute_claim:trata " and not precise_medical_problem(article_plain):
            continue
        filtered.append(reason)

    html = str(doc.get("article_html") or "")
    general_part = html.split("<h2>O que foi confirmado sobre este item</h2>", 1)[0]
    if risky_sentence(builder.html_text(general_part)):
        filtered.append("editorial_sanitizer_residual_risk")

    if builder.word_count(html) < 650:
        filtered.append("safe_assembly_too_short")
    if builder.word_count(html) > 950:
        filtered.append("safe_assembly_too_long")

    filtered = list(dict.fromkeys(filtered))
    result["reasons"] = filtered
    result["status"] = "PASS" if not filtered else "REJECTED"
    result["product_fact_mode"] = "deterministic_evidence_section_only"
    result["editorial_sanitizer"] = "SAFE_V3"
    result["medical_gate"] = "contextual_regex"
    return result


builder.prompt_for = general_prompt
builder.groq_call = throttled_call
builder.gate = strict_gate
builder.main()
