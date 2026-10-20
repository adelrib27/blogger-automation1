import hashlib
import re
import time
from html import escape
from pathlib import Path

import article_builder_v1 as builder
import evidence_engine as evidence

# V13 reduz o papel do modelo à organização editorial de baixo risco:
# ele produz somente títulos de seção e perguntas de verificação.
# O corpo é renderizado deterministicamente; fatos específicos continuam
# separados e vinculados às evidências exatas pelo normalize_doc do V9.
source_path = Path(__file__).with_name("article_builder_evergreen_v9.py")
source = source_path.read_text(encoding="utf-8")
marker = "\nbuilder.main()\n"
if marker not in source:
    raise RuntimeError("SAFE V13: ponto de entrada V9 não encontrado")
source = source.rsplit(marker, 1)[0] + "\n"
ns = {"__name__": "vida_pet_evergreen_v9_for_v13", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)

original_call = ns["original_call"]
normalize_doc = ns["normalize_doc"]
strict_gate = ns["strict_gate"]
current_candidate = ns["current_candidate"]
current_package = ns["current_package"]
previous_for = ns["previous_for"]
SPEC_TERMS = ns["SPEC_TERMS"]
ABSOLUTE_PATTERNS = ns["ABSOLUTE_PATTERNS"]

MIN_CALL_INTERVAL_SECONDS = 18.0
LAST_CALL = [0.0]

RISKY_TERMS = {
    "ansiedade", "estresse", "dor", "doenca", "sintoma", "comportamento",
    "seguranca", "seguro", "acidente", "energia", "frustracao", "curiosidade",
    "engajamento", "relaxamento", "satisfacao", "tedio", "temperamento",
    "estimulo", "estimulos", "estimular", "acalma", "acalmar", "receptivo",
    "racao", "petisco", "suplemento", "medicamento", "remedio",
}
OUTCOME_PATTERN = re.compile(
    r"\b(?:reduz|elimina|previne|cura|melhora|acalma|estimula)\s+"
    r"(?:ansiedade|estresse|dor|doenca|sintoma|comportamento)\b"
)

SAFE_HEADINGS = [
    ["Comece pela pergunta principal", "Defina o foco desta análise", "Organize o ponto de partida"],
    ["Separe contexto e informação", "Observe o cenário da escolha", "Mapeie o que precisa de consulta"],
    ["Transforme dúvidas em verificações", "Converta dúvidas em perguntas úteis", "Liste o que ainda precisa ser conferido"],
    ["Compare sem preencher lacunas", "Mantenha pendências visíveis", "Diferencie resposta e suposição"],
    ["Revise a página atual do item", "Volte às fontes antes da escolha", "Confira o que pode ter mudado"],
    ["Organize as anotações da decisão", "Registre critérios e pendências", "Guarde uma trilha simples da análise"],
    ["Feche a análise com clareza", "Revise os pontos antes de decidir", "Finalize sem transformar dúvida em certeza"],
]

OPENERS = [
    "Use esta parte para transformar o tema em verificações objetivas. Leia as perguntas como um roteiro de consulta e mantenha qualquer resposta específica vinculada à página atual do item.",
    "Nesta etapa, a prioridade é organizar a pesquisa antes de concluir. As perguntas abaixo ajudam a separar contexto, preferência e informação que ainda precisa ser confirmada em fonte adequada.",
    "Comece pelaquilo que realmente precisa ser esclarecido. Um conjunto curto de perguntas torna a consulta mais focada e reduz a chance de misturar impressões pessoais com informações verificáveis.",
    "Trate esta seção como um pequeno roteiro de decisão. O objetivo não é responder por antecipação, mas deixar claro quais pontos merecem consulta e quais podem continuar registrados como pendência.",
    "Organize a análise a partir de perguntas concretas. Quando cada dúvida tem um lugar definido, fica mais simples revisar fontes, comparar alternativas e evitar conclusões que não estejam sustentadas.",
    "Antes de avançar, separe o que pertence ao contexto do leitor do que depende da página do item. Essa divisão ajuda a manter a pesquisa útil sem transformar ausência de informação em suposição.",
    "A melhor forma de manter esta etapa verificável é trabalhar com perguntas abertas. Elas orientam a consulta sem antecipar respostas e deixam visível o que ainda precisa ser revisto.",
    "Nesta parte, concentre a atenção no processo de conferência. As perguntas servem para ordenar a pesquisa e impedir que uma descrição ampla seja tomada como resposta para um ponto específico.",
    "Use as próximas perguntas para estruturar a comparação de modo consistente. O mesmo critério pode ser reaplicado a outras opções, desde que cada resposta permaneça associada à fonte correspondente.",
    "O foco aqui é tornar a decisão revisável. Em vez de acumular descrições, transforme cada necessidade em uma pergunta e registre depois onde a resposta foi encontrada.",
    "Esta seção funciona como uma pausa para organizar a consulta. Perguntas bem delimitadas ajudam a distinguir o que já está claro do que ainda depende de uma nova checagem.",
    "Considere as perguntas abaixo como marcadores de pesquisa. Elas não substituem a fonte, mas ajudam a saber o que procurar e a reconhecer quando uma informação continua ausente.",
    "Mantenha esta etapa simples e rastreável. A ideia é consultar apenas o que importa para o ângulo atual e deixar outros assuntos anotados para uma análise diferente.",
    "Antes de comparar respostas, confirme se todas tratam da mesma questão. As perguntas abaixo ajudam a criar essa referência comum e a reduzir associações entre informações que pertencem a contextos distintos.",
    "Nesta seção, organize o raciocínio sem tentar fechar todas as dúvidas. Uma pergunta bem formulada pode ser mais útil do que uma resposta obtida de uma fonte pouco relacionada ao item.",
    "Use esta parte para documentar o caminho da pesquisa. Ao separar perguntas por assunto, fica mais fácil voltar às fontes certas e perceber quais pontos ainda precisam de atenção.",
    "A proposta aqui é manter a consulta proporcional ao que as fontes realmente mostram. As perguntas ajudam a delimitar a decisão sem transformar linguagem promocional em conclusão.",
    "Comece por uma revisão do objetivo desta seção. Depois, use as perguntas para verificar informações de forma ordenada e manter fora do texto qualquer detalhe que não esteja suficientemente sustentado.",
    "Esta etapa privilegia clareza sobre quantidade. Poucas perguntas bem escolhidas ajudam a identificar lacunas e tornam a comparação mais fácil de atualizar quando uma página muda.",
    "Organize a consulta em torno do ângulo atual e evite trazer respostas de outros assuntos. As perguntas abaixo servem como limite prático para manter a análise coerente.",
    "Trabalhe com perguntas que possam ser revisitadas. Assim, uma futura checagem consegue comparar o estado atual das fontes sem depender de conclusões antigas ou de memória informal.",
]

CLOSERS = [
    "Depois da consulta, registre apenas o que ficou claro e mantenha as demais questões como pendências. Essa separação facilita revisar a decisão sem completar lacunas por suposição.",
    "Ao terminar, anote quais perguntas receberam resposta e quais continuam abertas. Esse registro ajuda a retomar a análise depois sem confundir informação atual com uma impressão anterior.",
    "Feche a seção conferindo se cada resposta pode ser ligada à fonte correta. Se essa relação não estiver clara, preserve a dúvida para uma nova consulta.",
    "Antes de seguir, reveja as anotações e remova conclusões que tenham surgido apenas por associação. O que permanecer deve ser rastreável ou continuar explicitamente marcado como pendência.",
    "Uma revisão curta ajuda a manter o foco. Separe respostas verificadas, pontos variáveis e dúvidas ainda abertas para que a próxima etapa comece com limites claros.",
    "Finalize registrando somente o necessário para esta decisão. Assuntos laterais podem virar outra pauta e não precisam ser resolvidos dentro do mesmo artigo.",
    "Se alguma pergunta ainda depender de contexto adicional, deixe isso visível. A ausência de resposta é preferível a preencher o espaço com uma conclusão pouco sustentada.",
    "Ao encerrar, confirme se a seção continua fiel ao ângulo proposto. Essa checagem reduz repetição e evita que a pesquisa se transforme em uma descrição genérica.",
    "Guarde a origem das respostas junto das próprias anotações. Isso facilita revisar mudanças depois e reduz o risco de aplicar uma informação a outra oferta.",
    "Termine esta etapa distinguindo o que foi consultado do que foi apenas considerado. Essa diferença mantém a análise clara e torna futuras atualizações mais simples.",
    "Depois de revisar as perguntas, destaque apenas os pontos que realmente influenciam a escolha. O restante pode permanecer como referência para outra consulta.",
    "Antes de avançar, verifique se alguma resposta depende de uma condição que pode mudar. Quando isso acontecer, marque o ponto para nova checagem perto da decisão.",
    "Feche a seção com uma lista mental de pendências. Ela ajuda a saber exatamente o que procurar na próxima consulta sem repetir toda a pesquisa.",
    "Ao finalizar, prefira uma anotação incompleta e rastreável a uma resposta detalhada sem fonte adequada. Esse critério mantém a análise consistente ao longo do tempo.",
    "Revise se as perguntas continuam diferentes entre si. Quando duas tratam do mesmo ponto, reúna as anotações para evitar repetição e deixar a decisão mais legível.",
    "Termine confirmando quais respostas pertencem ao item atual. Referências gerais podem orientar a pesquisa, mas não devem assumir o lugar da fonte ligada ao item.",
    "Ao concluir esta parte, registre o que mudou em relação à consulta anterior, quando houver. Isso ajuda a manter histórico sem tratar informação antiga como estado atual.",
    "Feche a etapa sem buscar uma resposta para tudo. O importante é saber o que foi confirmado, o que permanece variável e o que ainda precisa ser consultado.",
    "Antes de passar à próxima seção, confira se as anotações podem ser entendidas sem depender do anúncio aberto. Essa clareza ajuda a retomar a pesquisa depois.",
    "Finalize mantendo as perguntas ainda úteis para uma revisão futura. Um bom critério continua compreensível mesmo quando a oferta ou o contexto de comparação muda.",
    "Ao terminar, verifique se cada conclusão está proporcional à informação disponível. Se a fonte responder apenas parte da dúvida, registre apenas essa parte.",
]


def unsafe_text(text):
    plain = re.sub(r"\s+", " ", str(text or "")).strip()
    if not plain:
        return True
    if re.search(r"\d", plain):
        return True
    norm = evidence.normalize(plain)
    for term in SPEC_TERMS | RISKY_TERMS:
        term_norm = evidence.normalize(term)
        if term_norm and re.search(rf"(?<!\w){re.escape(term_norm)}(?!\w)", norm):
            return True
    if any(re.search(pattern, norm) for pattern in ABSOLUTE_PATTERNS):
        return True
    if OUTCOME_PATTERN.search(norm):
        return True
    return False


def outline_prompt(candidate, package):
    current_candidate[0] = candidate
    current_package[0] = package
    category = str(candidate.get("category") or "Pets")
    keyword = str(candidate.get("keyword") or "acessório pet")
    angle = str(candidate.get("angle") or "critérios de escolha")
    prior = previous_for(candidate.get("itemId"))

    return f"""Você organiza conteúdo editorial para o blog brasileiro Vida Pet Prática.

Crie SOMENTE um roteiro de perguntas para um artigo. Não escreva o artigo e não responda às perguntas.

CATEGORIA: {category}
PALAVRA-CHAVE/TEMA: {keyword}
ÂNGULO DESTA PÁGINA: {angle}
ABORDAGENS JÁ USADAS NESTE ITEM: {prior}

Retorne SOMENTE JSON válido:
{{
  "sections": [
    {{"heading": "...", "questions": ["...?", "...?", "...?"]}}
  ]
}}

REGRAS OBRIGATÓRIAS:
- Português do Brasil.
- Exatamente sete seções.
- Exatamente três perguntas diferentes por seção.
- Cada título deve ser curto e descrever uma etapa de pesquisa, comparação, organização ou verificação.
- Cada pergunta deve orientar uma consulta ou decisão; não deve afirmar resposta, benefício, efeito ou resultado.
- Não descreva o produto e não mencione marca, modelo, material, medida, peça, desempenho ou característica física.
- Não use algarismos, percentuais, quantidades fixas ou instruções temporais.
- Não dê conselho sobre reação, emoção, saúde, comportamento, alimentação ou segurança do animal.
- Não faça diagnóstico, tratamento, prescrição, promessa ou alegação veterinária.
- Não ensine receita de limpeza nem recomende substâncias.
- Não fale sobre SEO, automação, IA, histórico editorial, gate ou processo interno.
- Prefira perguntas como: o que precisa ser conferido, onde essa informação aparece, qual contexto deve ser considerado, o que ainda está pendente.
"""


def choose_variant(options, seed):
    idx = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % len(options)
    return options[idx]


def safe_heading(raw, candidate, section_index):
    text = re.sub(r"\s+", " ", builder.html_text(str(raw or ""))).strip()
    if text and not unsafe_text(text):
        return text
    return choose_variant(
        SAFE_HEADINGS[section_index % len(SAFE_HEADINGS)],
        f"{candidate.get('itemId') or ''}|{candidate.get('angle') or ''}|heading|{section_index}",
    )


def normalize_question(raw):
    text = re.sub(r"\s+", " ", builder.html_text(str(raw or ""))).strip()
    text = text.rstrip(" .!;:") + "?"
    if unsafe_text(text):
        return ""
    words = text.split()
    if len(words) < 5 or len(words) > 18:
        return ""
    return text


def validate_outline(raw, candidate):
    if not isinstance(raw, dict):
        raise RuntimeError("SAFE V13: resposta não é objeto JSON")
    sections = raw.get("sections")
    if not isinstance(sections, list) or len(sections) != 7:
        raise RuntimeError("SAFE V13: sections_count")
    normalized = []
    seen = set()
    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            raise RuntimeError("SAFE V13: section_not_object")
        heading = safe_heading(section.get("heading"), candidate, idx)
        questions = section.get("questions")
        if not isinstance(questions, list):
            raise RuntimeError("SAFE V13: questions_not_list")
        safe_questions = []
        for raw_q in questions:
            q = normalize_question(raw_q)
            key = evidence.normalize(q)
            if q and key not in seen:
                seen.add(key)
                safe_questions.append(q)
        if len(safe_questions) != 3:
            raise RuntimeError(f"SAFE V13: safe_questions:{idx}:{len(safe_questions)}")
        normalized.append({"heading": heading, "questions": safe_questions})
    return normalized


def render_section(section, candidate, section_index):
    base = f"{candidate.get('itemId') or ''}|{candidate.get('angle') or ''}|{section_index}"
    opener = choose_variant(OPENERS, base + "|open")
    closer = choose_variant(CLOSERS, base + "|close")
    style = int(hashlib.sha256((base + "|style").encode("utf-8")).hexdigest()[:8], 16) % 3

    questions = section["questions"]
    if style == 0:
        question_html = "<ul>" + "".join(f"<li>{escape(q)}</li>" for q in questions) + "</ul>"
    elif style == 1:
        question_html = (
            "<h3>Perguntas para esta etapa</h3>"
            + "".join(f"<p><strong>Para conferir:</strong> {escape(q)}</p>" for q in questions)
        )
    else:
        question_html = (
            "<p><strong>Questões para revisar</strong></p><ul>"
            + "".join(f"<li>{escape(q)}</li>" for q in questions)
            + "</ul>"
        )

    return (
        f"<h2>{escape(section['heading'])}</h2>"
        f"<p>{escape(opener)}</p>"
        f"{question_html}"
        f"<p>{escape(closer)}</p>"
    )


def render_article(sections, candidate):
    html = "".join(render_section(section, candidate, idx) for idx, section in enumerate(sections))
    wc = builder.word_count(html)
    if wc < 580 or wc > 780:
        raise RuntimeError(f"SAFE V13: rendered_word_count:{wc}")
    ns["safety_check_editorial"](html)
    return html


def editorial_call(prompt):
    elapsed = time.monotonic() - LAST_CALL[0]
    if LAST_CALL[0] and elapsed < MIN_CALL_INTERVAL_SECONDS:
        time.sleep(MIN_CALL_INTERVAL_SECONDS - elapsed)
    LAST_CALL[0] = time.monotonic()

    raw, usage = original_call(prompt)
    sections = validate_outline(raw, current_candidate[0])
    article_html = render_article(sections, current_candidate[0])
    doc = {"article_html": article_html}
    return normalize_doc(doc, current_candidate[0], current_package[0]), usage


builder.prompt_for = outline_prompt
builder.groq_call = editorial_call
builder.gate = strict_gate
builder.main()
