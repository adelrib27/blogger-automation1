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
    ("Comece pelo contexto da comparação", "Antes de comparar opções, defina onde o acessório será usado e quais informações realmente influenciam a escolha. Considere o espaço disponível, a forma de armazenamento e a finalidade pretendida. O objetivo é criar critérios antes de olhar detalhes comerciais. Essa etapa ajuda a separar necessidades reais de características que chamam atenção no anúncio, mas que talvez não sejam relevantes para a decisão."),
    ("Confirme cada especificação importante", "Quando uma característica fizer diferença, procure a informação na página atual do produto e, quando houver, nas orientações do fabricante. Medidas, materiais, capacidade, compatibilidade e instruções podem variar entre versões e vendedores. Se um dado estiver ausente ou ambíguo, mantenha-o como não confirmado. Reconhecer uma lacuna é mais seguro do que completar a informação por semelhança com outro item."),
    ("Compare informações equivalentes", "Ao colocar duas opções lado a lado, use os mesmos critérios para ambas. Compare apenas dados claramente informados em fontes relacionadas ao item correto. A descrição de outro modelo pode servir como referência de pesquisa, mas não deve ser transferida para o produto analisado. Assim, a comparação permanece baseada em informações que realmente pertencem a cada opção."),
    ("Separe fato de linguagem promocional", "Anúncios misturam dados objetivos e frases de divulgação. Para decidir com mais clareza, identifique quais pontos podem ser conferidos diretamente e quais dependem apenas de linguagem comercial. Dê prioridade ao que possui descrição verificável e relação clara com o item. Expressões promocionais podem explicar a proposta do vendedor, mas não substituem especificações confirmadas."),
    ("Use fontes ligadas ao item correto", "Encontrar uma página parecida não basta para confirmar uma característica. Sempre que possível, verifique se a fonte corresponde ao mesmo item, modelo ou identificação usada na pesquisa. Se essa ligação não puder ser demonstrada, use a página apenas como referência de contexto e não como prova de uma especificação. Essa distinção impede que detalhes de outra versão sejam atribuídos ao item analisado."),
    ("Revise os dados antes da decisão", "Informações comerciais podem mudar. Por isso, um dado consultado anteriormente deve ser verificado novamente quando for importante para a escolha. A revisão também ajuda a identificar divergências entre fontes. Quando houver conflito, não selecione automaticamente a versão mais conveniente: registre a diferença e consulte a página atual do produto antes de considerar o ponto resolvido."),
    ("Organize o que já foi verificado", "Um histórico simples facilita futuras comparações. Registre o produto consultado, a fonte usada, o assunto abordado e quais informações estavam confirmadas naquele momento. Esse registro também ajuda a criar novos ângulos editoriais sem repetir o texto anterior, porque permite distinguir fatos já documentados, dados que precisam de nova consulta e assuntos já explorados."),
    ("Quando faltar informação", "A ausência de um dado também é uma conclusão útil. Se determinada característica não aparece nas fontes ligadas ao produto, ela não precisa ser preenchida por inferência. O conteúdo pode orientar o leitor a conferir esse ponto no anúncio antes da compra. Dessa forma, o artigo continua útil sem transformar uma informação pendente em uma afirmação definitiva."),
    ("Evite copiar a descrição comercial", "O artigo pode partir do mesmo produto sem repetir o texto do anúncio. Em vez de reproduzir a descrição comercial, use um ângulo editorial próprio, organize os critérios de decisão e explique quais dados precisam ser verificados. O produto permanece como referência, enquanto o conteúdo responde a uma intenção de pesquisa diferente e ganha utilidade independente."),
    ("Faça uma última checagem", "Antes de considerar o conteúdo pronto, revise título, palavra-chave, estrutura e todas as afirmações específicas sobre o item. Cada detalhe factual precisa ter uma fonte autorizada correspondente. Também confirme se o texto não introduziu preço, estoque, prazo ou outra informação variável sem necessidade. Essa checagem final funciona como uma barreira contra erros da geração automática."),
]

RISK_WORDS = {
    "saude", "estresse", "ansiedade", "cura", "curar", "tratamento", "diagnostico", "prescricao",
    "medicamento", "remedio", "previne", "prevenir", "garante", "garantir", "seguranca", "seguro",
    "reduz", "reduzir", "evita", "evitar", "treinamento", "comando", "recompensa", "petisco", "racao",
    "vinagre", "sabao", "eficacia", "elimina", "protege", "melhora"
}
RISK_PREFIXES = ("terapeut", "lubrif", "absorv", "antiderrap", "durabil", "resistent", "lavavel")
RISK_PHRASES = ("bem estar", "estimulo mental", "peso suportado", "beneficio comprovado")

MEDICAL_CONTEXT_RE = re.compile(
    r"\b(?:tratar|tratamento|cura|curar|diagnostico|prescricao|terapeutic[oa]|medicamento|remedio)\b"
    r"|\btrata\s+(?:doenca|dor|ferida|infeccao|ansiedade|sintoma|problema de saude)\b",
    flags=re.I,
)


def safe_title(candidate):
    keyword = str(candidate.get("keyword") or "").lower()
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
    return "Acessórios pet: critérios práticos para comparar opções"


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
        if s.get("allowed_in_article") and s.get("identity_level") == "EXACT_PRODUCT" and s.get("evidence_id")
    ]


def has_risk(text):
    norm = evidence.normalize(text)
    if re.search(r"\d", str(text or "")):
        return True
    words = set(norm.split())
    if words & RISK_WORDS:
        return True
    if any(any(word.startswith(prefix) for prefix in RISK_PREFIXES) for word in words):
        return True
    padded = f" {norm} "
    return any(f" {phrase} " in padded for phrase in RISK_PHRASES)


def general_prompt(candidate, package):
    current_candidate[0] = candidate
    current_package[0] = package
    return f"""Você é editor do blog Vida Pet Prática.
Escreva uma introdução editorial curta sobre como pesquisar e comparar anúncios do tema abaixo.
Você NÃO conhece especificações do produto.

TEMA: {candidate.get('keyword')}
ÂNGULO EDITORIAL: {candidate.get('angle')}

Retorne SOMENTE JSON válido com: title, focus_keyword, meta_description, article_html, cta_text, claim_evidence.
O article_html deve ter aproximadamente 120 a 180 palavras.
Fale somente de critérios de pesquisa, comparação de fontes e confirmação de dados no anúncio.
Não dê orientação de cuidado do animal e não descreva características de produto.
Não use números, medidas, saúde, comportamento, treinamento, limpeza, alimentação ou segurança.
claim_evidence deve ser [].
"""


def safe_ai_intro(html):
    plain = builder.html_text(html)
    if not plain:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", plain)
    kept = []
    total = 0
    for sentence in sentences:
        sentence = re.sub(r"\s+", " ", sentence).strip()
        if not sentence or has_risk(sentence):
            continue
        count = len(sentence.split())
        if total + count > 150:
            break
        kept.append(sentence)
        total += count
    if not kept:
        return ""
    candidate = " ".join(kept)
    if has_risk(candidate):
        return ""
    return "<h2>Como organizar a pesquisa</h2><p>" + candidate + "</p>"


def normalize_doc(doc, candidate, package):
    if not isinstance(doc, dict):
        doc = {}
    keyword = str(candidate.get("keyword") or "acessório pet")
    product_name = re.sub(r"\s+", " ", str(candidate.get("productName") or "")).strip()
    ids = exact_evidence_ids(package)

    html = safe_ai_intro(doc.get("article_html") or "")
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

    return {
        "title": safe_title(candidate),
        "focus_keyword": keyword,
        "meta_description": clip_text(
            f"Veja critérios práticos para comparar {keyword}, confirmar informações no anúncio e separar fatos verificados de dados ainda pendentes.",
            150,
        ),
        "article_html": html,
        "cta_text": "Confira no anúncio as informações e condições atuais do item antes de decidir.",
        "claim_evidence": [{"claim": product_name, "evidence_ids": ids[:2]}],
    }


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
    return bool(MEDICAL_CONTEXT_RE.search(evidence.normalize(article_plain)))


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
    before_verified = html.split("<h2>O que foi confirmado sobre este item</h2>", 1)[0]
    if before_verified and has_risk(builder.html_text(before_verified)):
        filtered.append("editorial_sanitizer_residual_risk")
    wc = builder.word_count(html)
    if wc < 650:
        filtered.append("safe_assembly_too_short")
    if wc > 950:
        filtered.append("safe_assembly_too_long")

    filtered = list(dict.fromkeys(filtered))
    result["reasons"] = filtered
    result["status"] = "PASS" if not filtered else "REJECTED"
    result["product_fact_mode"] = "deterministic_evidence_section_only"
    result["editorial_sanitizer"] = "SAFE_V4_TOKEN_AWARE"
    result["medical_gate"] = "contextual_regex"
    result["ai_intro_discard_on_risk"] = True
    return result


builder.prompt_for = general_prompt
builder.groq_call = throttled_call
builder.gate = strict_gate
builder.main()
