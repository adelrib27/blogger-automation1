import hashlib
import re
import time

import article_builder_v1 as builder
import evidence_engine as evidence

original_call = builder.groq_call
original_gate = builder.gate
last_call = [0.0]
current_candidate = [{}]
current_package = [{}]
session_accepted = []

COMMON_BLOCKS = [
    ("Confirme os dados na fonte correta", "Quando uma característica for importante para a decisão, procure a informação na página atual do produto e, quando houver, nas orientações do fabricante. Se o dado estiver ausente ou ambíguo, mantenha-o como não confirmado. Uma página parecida pode ajudar na pesquisa, mas não deve ser usada como prova de uma especificação sem vínculo claro com o item analisado."),
    ("Separe fato de linguagem promocional", "Anúncios podem reunir dados objetivos e frases de divulgação. Para comparar melhor, identifique quais pontos podem ser conferidos diretamente e quais dependem apenas de linguagem comercial. Dê mais peso ao que possui descrição verificável e relação clara com o item. Expressões promocionais ajudam a entender a proposta do vendedor, mas não substituem especificações confirmadas."),
    ("Revise antes de decidir", "Informações comerciais podem mudar. Por isso, um dado consultado anteriormente deve ser verificado novamente quando for relevante para a escolha. Quando houver divergência entre fontes, registre o conflito e consulte a página atual do produto antes de considerar o ponto resolvido. A ausência de uma informação também é útil: ela indica exatamente o que ainda precisa ser conferido."),
]

CATEGORY_BLOCKS = {
    "Higiene": [
        ("Mapeie o espaço de higiene", "Antes de comparar acessórios de higiene, observe onde o item será colocado, quanto espaço existe ao redor e como a área é organizada. Esses critérios ajudam a identificar quais dados do anúncio merecem atenção. Em vez de presumir que uma solução serve para qualquer ambiente, transforme o espaço disponível e a rotina de organização em perguntas objetivas para conferir nas fontes do produto."),
        ("Verifique instruções de conservação", "Se limpeza e conservação forem importantes, procure instruções específicas no anúncio ou no material do fabricante. Não presuma que produtos parecidos aceitam os mesmos métodos. Materiais e construções podem variar, então qualquer orientação de manutenção precisa estar ligada ao item correto. Se a fonte não explicar o procedimento, trate esse detalhe como pendente e evite completar a lacuna com uma receita genérica."),
        ("Compare dimensões somente quando confirmadas", "O tamanho pode mudar bastante entre versões de um mesmo tipo de acessório. Por isso, use medidas apenas quando elas estiverem claramente associadas ao item consultado. Se duas páginas apresentarem números diferentes, não escolha uma delas por conveniência. Registre a divergência e volte ao anúncio atual. Essa prática reduz o risco de criar um texto preciso na aparência, mas baseado em uma versão diferente."),
        ("Organize os critérios de praticidade", "Praticidade pode significar coisas diferentes para cada casa. Em vez de transformar essa palavra em promessa, decomponha a decisão em pontos verificáveis: espaço necessário, instruções disponíveis, forma de armazenamento e informações de manutenção. O artigo pode orientar essa comparação sem afirmar que determinado produto torna a rotina mais fácil. A conclusão depende dos dados confirmados e do contexto de uso."),
        ("Evite transferir características", "Acessórios visualmente semelhantes podem ter diferenças importantes. Uma descrição encontrada em outro marketplace só deve autorizar uma especificação quando a identidade do mesmo item ou modelo estiver demonstrada. Caso contrário, use a página apenas como contexto. Essa separação é especialmente importante em produtos sem marca ou modelo evidente, nos quais a aparência sozinha não prova que duas ofertas são equivalentes."),
        ("Crie um histórico do item", "Registre o identificador do produto, as fontes consultadas, o assunto do artigo e os fatos autorizados. Esse histórico ajuda em futuras atualizações e também permite reutilizar o produto com outro ângulo sem copiar a publicação anterior. O novo texto pode partir de uma pergunta diferente, enquanto o sistema conserva a mesma disciplina de checar novamente os dados variáveis antes de liberar qualquer afirmação específica."),
    ],
    "Diversao e Enriquecimento": [
        ("Defina o que precisa ser comparado", "Ao pesquisar acessórios de brincadeira, comece transformando o interesse do leitor em critérios verificáveis. Espaço disponível, montagem, dimensões, materiais e instruções são exemplos de dados que podem ser relevantes, mas só devem entrar como fatos quando aparecerem em fontes ligadas ao item correto. O texto editorial pode organizar essas perguntas sem presumir como o animal reagirá ao produto."),
        ("Não transforme descrição em resultado", "Termos comerciais como interativo, multifuncional ou divertido descrevem a proposta do anúncio, mas não comprovam uma reação específica do animal. Ao escrever, mantenha essa diferença clara. O produto pode ser apresentado pela identificação confirmada, enquanto qualquer expectativa de uso deve permanecer como contexto de escolha e não como promessa de comportamento, interesse ou resultado."),
        ("Cheque peças e montagem nas fontes", "Quando a configuração física do acessório for importante, procure a informação no anúncio exato ou na documentação do fabricante. Não complete detalhes observando apenas fotos de outro produto semelhante. Se a fonte não indicar como o item é montado ou quais componentes fazem parte do conjunto, deixe o ponto como não confirmado. Essa regra impede que uma descrição comercial seja enriquecida com peças que pertencem a outra versão."),
        ("Compare anúncios do mesmo item", "Quando o mesmo identificador aparece em mais de uma fonte, compare os dados que realmente coincidem. Uma segunda página pode reforçar a evidência, mas divergências precisam ser registradas. O sistema não deve escolher automaticamente o texto mais completo; deve preferir a informação cuja ligação com o item esteja demonstrada. Assim, quantidade de fontes não substitui qualidade de correspondência."),
        ("Use avaliações apenas como contexto", "Comentários de compradores podem sugerir perguntas úteis para a pesquisa, mas não devem virar especificações técnicas sem confirmação. Uma experiência individual também não representa todos os usos. Se uma avaliação mencionar um detalhe relevante, ela pode indicar o que conferir no anúncio ou na documentação. O fato só entra na lista autorizada quando uma fonte apropriada sustenta a afirmação."),
        ("Abra novos ângulos sem repetir texto", "O mesmo produto pode aparecer em conteúdos diferentes quando cada publicação responde a uma intenção distinta. Um artigo pode focar critérios de comparação; outro, organização do espaço; outro, verificação de montagem. O histórico de ângulos impede que a automação apenas troque palavras do título. Antes de gerar, o sistema compara o novo plano com os assuntos e estruturas já utilizados."),
    ],
    "Transporte e Passeio": [
        ("Transforme compatibilidade em pergunta", "Em acessórios de passeio, compatibilidade não deve ser presumida pelo nome do produto. O conteúdo pode orientar o leitor a conferir medidas, formas de ajuste e instruções disponíveis na fonte correta, mas não afirmar que o item serve para determinado animal sem evidência. Essa abordagem transforma uma possível promessa em um checklist de informações que precisam estar confirmadas antes da escolha."),
        ("Verifique componentes no anúncio exato", "Fechos, conexões, comprimentos e outros detalhes físicos só devem ser descritos quando a fonte vinculada ao item os apresentar claramente. Fotos ou textos de ofertas semelhantes não bastam para transferir uma especificação. Se um componente for importante para o assunto e não estiver confirmado, registre a pendência. O artigo continua útil ao explicar o que verificar, sem preencher a ausência com inferência."),
        ("Compare medidas sem misturar versões", "Uma mesma categoria pode reunir variações com tamanhos diferentes. Ao pesquisar medidas, confirme que cada número pertence ao mesmo item ou modelo identificado. Se houver versões na página, não trate uma medida isolada como universal. O sistema deve manter a associação entre dado e variante ou, quando isso não for possível, deixar a informação de fora até que a identidade esteja clara."),
        ("Separe uso pretendido de garantia", "A descrição comercial pode indicar uma finalidade pretendida, mas isso não equivale a uma garantia de desempenho. O texto editorial deve preservar essa distinção. Em vez de afirmar que o acessório produz determinado resultado, organize os critérios que o leitor pode verificar: documentação, identificação do item, instruções, dimensões e condições atuais do anúncio. A decisão final fica apoiada em dados consultáveis."),
        ("Cheque informações variáveis novamente", "Antes de publicar ou atualizar um conteúdo, revise dados que podem mudar no anúncio. Mesmo quando o produto já passou pelo Evidence Engine em outra ocasião, uma nova publicação deve consultar novamente os detalhes relevantes. Essa rotina reduz o risco de um artigo evergreen reutilizar informações antigas como se fossem atuais e mantém separado o que é histórico do que precisa de nova validação."),
        ("Registre assunto e estrutura usados", "Para reutilizar um produto no futuro sem criar páginas quase iguais, guarde o título, a intenção de busca, o ângulo e uma impressão semântica do artigo. Na próxima rodada, o gerador recebe o histórico e precisa escolher uma abordagem suficientemente diferente. Se a similaridade continuar alta, aquele ângulo é rejeitado e o sistema passa a outro produto ou outro assunto disponível."),
    ],
    "Organizacao": [
        ("Defina o problema de organização", "Antes de pesquisar um organizador, descreva qual espaço precisa ser organizado e quais limitações existem. Esse contexto ajuda a decidir quais informações do anúncio são relevantes. O artigo não precisa afirmar que um produto resolve a bagunça; pode mostrar como comparar dimensões, formato, instruções e outras especificações somente depois que cada dado estiver confirmado na fonte correta."),
        ("Compare formato e espaço disponível", "Quando formato ou tamanho influenciarem a decisão, use apenas medidas vinculadas ao item exato. Não deduza dimensões pela imagem nem copie números de uma versão semelhante. Se o anúncio tiver variações, mantenha cada dado associado à variante correta. Essa disciplina evita que a automação produza uma descrição aparentemente completa, mas incompatível com o produto selecionado."),
        ("Confirme materiais antes de mencionar", "Material é uma especificação factual e precisa de fonte. Se a Shopee API não trouxer esse dado, o Evidence Engine pode procurar uma página ligada ao mesmo item ou modelo. Sem correspondência suficiente, o texto deve omitir a característica. Esse limite é preferível a usar uma descrição de mercado como se fosse prova do produto analisado."),
        ("Use o anúncio como fonte de condições atuais", "Informações comerciais e opções disponíveis podem mudar. O conteúdo editorial deve evitar congelar detalhes voláteis sem necessidade e orientar a consulta da página atual quando a decisão depender deles. O histórico interno pode guardar o que foi visto, mas uma nova publicação não deve presumir que as mesmas condições continuam válidas."),
        ("Mantenha ângulos editoriais separados", "Um produto de organização pode sustentar mais de um conteúdo, desde que a intenção mude de verdade. Comparação de opções, planejamento de espaço, critérios de tamanho e organização por categoria são exemplos de direções diferentes. O sistema registra cada ângulo utilizado e mede similaridade antes de liberar o próximo, evitando uma sequência de páginas com a mesma estrutura reescrita."),
        ("Trate ausência de dados como pendência", "Se uma característica importante não puder ser confirmada, marque a pendência em vez de inventar uma resposta. O artigo pode explicar ao leitor que esse ponto deve ser verificado no anúncio. Essa prática mantém o conteúdo transparente e também orienta o failover: quando a falta de evidência compromete o assunto principal, o sistema pode abandonar o candidato e procurar outro produto com fontes melhores."),
    ],
}

RISK_WORDS = {"saude", "estresse", "ansiedade", "cura", "curar", "tratamento", "diagnostico", "prescricao", "medicamento", "remedio", "previne", "prevenir", "garante", "garantir", "seguranca", "seguro", "reduz", "reduzir", "treinamento", "comando", "recompensa", "petisco", "racao", "vinagre", "sabao", "eficacia", "elimina", "protege", "melhora"}
RISK_PREFIXES = ("terapeut", "lubrif", "absorv", "antiderrap", "durabil", "resistent", "lavavel")
RISK_PHRASES = ("bem estar", "estimulo mental", "peso suportado", "beneficio comprovado")
MEDICAL_CONTEXT_RE = re.compile(r"\b(?:tratar|tratamento|cura|curar|diagnostico|prescricao|terapeutic[oa]|medicamento|remedio)\b|\btrata\s+(?:doenca|dor|ferida|infeccao|ansiedade|sintoma|problema de saude)\b", flags=re.I)


def safe_title(candidate):
    keyword = str(candidate.get("keyword") or "").lower()
    if "tapete coletor" in keyword: return "Tapete coletor de areia: critérios para comparar opções"
    if "brinquedo interativo" in keyword: return "Brinquedo interativo: critérios para comparar opções"
    if "guia cachorro" in keyword: return "Guia para cachorro: critérios para comparar opções"
    if "caixa areia" in keyword: return "Caixa de areia para gatos: como comparar opções"
    if "cama pet" in keyword: return "Cama pet: critérios para comparar opções de conforto"
    if "comedouro" in keyword: return "Comedouro pet: critérios para comparar opções"
    return "Acessórios pet: critérios práticos para comparar opções"


def clip_text(text, limit=150):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= limit: return text
    out = []
    for word in text.split():
        if len(" ".join(out + [word])) > limit - 1: break
        out.append(word)
    return " ".join(out).rstrip(".,;:") + "."


def exact_evidence_ids(package):
    return [s.get("evidence_id") for s in package.get("sources") or [] if s.get("allowed_in_article") and s.get("identity_level") == "EXACT_PRODUCT" and s.get("evidence_id")]


def has_risk(text):
    norm = evidence.normalize(text)
    if re.search(r"\d", str(text or "")): return True
    words = set(norm.split())
    if words & RISK_WORDS: return True
    if any(any(word.startswith(prefix) for prefix in RISK_PREFIXES) for word in words): return True
    padded = f" {norm} "
    return any(f" {phrase} " in padded for phrase in RISK_PHRASES)


def general_prompt(candidate, package):
    current_candidate[0] = candidate
    current_package[0] = package
    return f"""Você é editor do blog Vida Pet Prática. Escreva uma introdução curta sobre como pesquisar anúncios do tema abaixo, sem conhecer especificações do produto.
TEMA: {candidate.get('keyword')}
ÂNGULO: {candidate.get('angle')}
Retorne SOMENTE JSON válido com title, focus_keyword, meta_description, article_html, cta_text, claim_evidence.
O article_html deve ter cerca de 100 a 150 palavras. Fale apenas de pesquisa, comparação de fontes e confirmação de dados. Não dê orientação de saúde, comportamento, treinamento, limpeza, alimentação ou segurança e não descreva características do produto. claim_evidence deve ser []."""


def safe_ai_intro(html):
    plain = builder.html_text(html)
    if not plain: return ""
    kept, total = [], 0
    for sentence in re.split(r"(?<=[.!?])\s+", plain):
        sentence = re.sub(r"\s+", " ", sentence).strip()
        if not sentence or has_risk(sentence): continue
        count = len(sentence.split())
        if total + count > 120: break
        kept.append(sentence); total += count
    candidate = " ".join(kept)
    if not candidate or has_risk(candidate): return ""
    return "<h2>Como organizar a pesquisa</h2><p>" + candidate + "</p>"


def ordered_category_blocks(candidate):
    category = str(candidate.get("category") or "Organizacao")
    blocks = list(CATEGORY_BLOCKS.get(category) or CATEGORY_BLOCKS["Organizacao"])
    angle = str(candidate.get("angle") or "")
    offset = int(hashlib.sha256(angle.encode("utf-8")).hexdigest()[:4], 16) % len(blocks)
    return blocks[offset:] + blocks[:offset]


def normalize_doc(doc, candidate, package):
    if not isinstance(doc, dict): doc = {}
    keyword = str(candidate.get("keyword") or "acessório pet")
    product_name = re.sub(r"\s+", " ", str(candidate.get("productName") or "")).strip()
    ids = exact_evidence_ids(package)
    html = safe_ai_intro(doc.get("article_html") or "")
    html += "<h2>O que foi confirmado sobre este item</h2><p>Na identificação consultada do anúncio, o item aparece como <strong>" + product_name + "</strong>. Essa identificação está vinculada às fontes autorizadas desta análise. Outros detalhes devem ser conferidos na página atual do produto antes da decisão.</p>"
    for heading, paragraph in ordered_category_blocks(candidate) + COMMON_BLOCKS:
        if builder.word_count(html) >= 690 and len(re.findall(r"<h2\b", html, flags=re.I)) >= 7: break
        html += f"<h2>{heading}</h2><p>{paragraph}</p>"
    return {
        "title": safe_title(candidate), "focus_keyword": keyword,
        "meta_description": clip_text(f"Veja critérios práticos para comparar {keyword}, confirmar informações no anúncio e separar fatos verificados de dados ainda pendentes.", 150),
        "article_html": html,
        "cta_text": "Confira no anúncio as informações e condições atuais do item antes de decidir.",
        "claim_evidence": [{"claim": product_name, "evidence_ids": ids[:2]}],
    }


def throttled_call(prompt):
    for attempt in range(1, 5):
        elapsed = time.monotonic() - last_call[0]
        if last_call[0] and elapsed < 18.0: time.sleep(18.0 - elapsed)
        try:
            last_call[0] = time.monotonic()
            doc, usage = original_call(prompt)
            return normalize_doc(doc, current_candidate[0], current_package[0]), usage
        except builder.ProviderFatalError as exc:
            text = str(exc)
            if "HTTP 429" not in text or attempt >= 4: raise
            match = re.search(r"try again in\s+([0-9.]+)s", text, flags=re.I)
            time.sleep(max(6.0, (float(match.group(1)) if match else 6.0) + 2.0))


def precise_medical_problem(article_plain):
    return bool(MEDICAL_CONTEXT_RE.search(evidence.normalize(article_plain)))


def strict_gate(doc, package, history, max_similarity):
    result = original_gate(doc, package, history, max_similarity)
    html = str(doc.get("article_html") or "")
    article_plain = builder.html_text(html)
    reasons = []
    for reason in list(result.get("reasons") or []):
        if reason == "medical_or_absolute_claim:trata " and not precise_medical_problem(article_plain): continue
        reasons.append(reason)
    before_verified = html.split("<h2>O que foi confirmado sobre este item</h2>", 1)[0]
    if before_verified and has_risk(builder.html_text(before_verified)): reasons.append("editorial_sanitizer_residual_risk")
    wc = builder.word_count(html)
    if wc < 650: reasons.append("safe_assembly_too_short")
    if wc > 950: reasons.append("safe_assembly_too_long")

    semantic = f"{doc.get('title') or ''} {article_plain}"
    for old in session_accepted:
        score = evidence.similarity(semantic, old)
        if score >= 0.62:
            reasons.append(f"semantic_duplicate_session:{score:.2f}")
            break

    reasons = list(dict.fromkeys(reasons))
    result["reasons"] = reasons
    result["status"] = "PASS" if not reasons else "REJECTED"
    result["product_fact_mode"] = "deterministic_evidence_section_only"
    result["editorial_sanitizer"] = "SAFE_V5_CATEGORY_AWARE"
    result["session_duplicate_guard"] = 0.62
    if result["status"] == "PASS": session_accepted.append(semantic)
    return result


builder.prompt_for = general_prompt
builder.groq_call = throttled_call
builder.gate = strict_gate
builder.main()
