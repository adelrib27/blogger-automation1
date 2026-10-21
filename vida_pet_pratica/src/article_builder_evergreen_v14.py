import hashlib
import re
import time
from html import escape
from pathlib import Path

import article_builder_v1 as builder
import evidence_engine as evidence

# V14 elimina texto livre do provedor. O Groq escolhe apenas variantes A/B/C;
# headings, perguntas e corpo editorial vêm de templates locais revisados.
# Fatos específicos continuam separados e evidenciados pelo normalize_doc do V9.
source_path = Path(__file__).with_name("article_builder_evergreen_v13.py")
source = source_path.read_text(encoding="utf-8")
marker = "\nbuilder.main()\n"
if marker not in source:
    raise RuntimeError("SAFE V14: ponto de entrada V13 não encontrado")
source = source.rsplit(marker, 1)[0] + "\n"
ns = {"__name__": "vida_pet_evergreen_v13_for_v14", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)

original_call = ns["original_call"]
normalize_doc = ns["normalize_doc"]
strict_gate = ns["strict_gate"]
current_candidate = ns["current_candidate"]
current_package = ns["current_package"]

MIN_CALL_INTERVAL_SECONDS = 18.0
LAST_CALL = [0.0]

OPENERS = [
    "Use esta etapa para organizar a decisão sem transformar linguagem comercial em conclusão. Leia as perguntas como um roteiro de conferência e mantenha qualquer resposta específica vinculada à página atual da opção analisada.",
    "Nesta parte, trabalhe apenas com critérios que possam ser revisitados. As perguntas ajudam a separar contexto, preferência e informação da oferta, deixando explícito aquilo que ainda depende de uma nova consulta.",
    "O objetivo desta seção é tornar a comparação mais clara e rastreável. Em vez de completar lacunas, use as perguntas para registrar o que precisa ser verificado e onde a resposta deverá ser confirmada.",
]

CLOSERS = [
    "Ao concluir, registre somente o que ficou claro e mantenha as demais questões como pendências. Essa separação facilita revisar a escolha depois sem transformar ausência de informação em suposição.",
    "Feche a etapa conferindo se cada anotação continua ligada ao critério certo. Quando uma resposta depender da oferta atual, preserve a referência para que a próxima revisão possa ser feita sem reconstruir toda a pesquisa.",
    "Antes de avançar, diferencie o que pertence ao contexto da casa do que depende da página do item. Essa divisão mantém o texto útil e reduz o risco de aplicar uma informação fora do lugar.",
]

FAMILY_BLUEPRINTS = {
    "comparison": [
        ("Defina o contexto da escolha", [
            "Em qual situação esta opção será considerada no dia a dia?",
            "Qual necessidade prática deve orientar a comparação entre alternativas?",
            "Que ponto precisa permanecer registrado antes de abrir as ofertas?",
        ]),
        ("Use a mesma base de comparação", [
            "As opções consultadas respondem ao mesmo objetivo de uso?",
            "Quais informações aparecem de forma comparável nas páginas atuais?",
            "O que ainda não pode ser colocado lado a lado com clareza?",
        ]),
        ("Confira a informação da oferta", [
            "Onde a página atual explica como o item deve ser utilizado?",
            "Que informação depende de confirmação diretamente na oferta?",
            "Qual detalhe deve ficar pendente quando a fonte não responde?",
        ]),
        ("Separe preferência e informação", [
            "Quais critérios pertencem à rotina e não à descrição comercial?",
            "Que pontos estão sustentados pela página atual da opção?",
            "Onde uma preferência pessoal não deve virar conclusão geral?",
        ]),
        ("Compare alternativas com consistência", [
            "Qual critério pode ser aplicado igualmente a todas as opções?",
            "Que diferença aparece apenas na apresentação comercial da oferta?",
            "Qual comparação precisa de outra fonte antes de ser registrada?",
        ]),
        ("Revise o que pode mudar", [
            "Quais informações comerciais podem mudar perto da decisão?",
            "Onde confirmar novamente os pontos que influenciam a escolha?",
            "Que anotação antiga precisa ser tratada apenas como histórico?",
        ]),
        ("Feche a comparação com pendências", [
            "Quais respostas já têm fonte claramente identificada?",
            "Quais dúvidas continuam abertas depois da comparação?",
            "Que critério ajuda a reduzir a lista sem inventar informação?",
        ]),
    ],
    "placement": [
        ("Mapeie a área disponível", [
            "Que parte do ambiente está realmente disponível para o acessório?",
            "Quais tarefas já usam essa área ao longo da rotina?",
            "Que limite do espaço precisa ser anotado antes da escolha?",
        ]),
        ("Separe uso e passagem", [
            "Quais áreas precisam permanecer livres durante as tarefas da casa?",
            "Onde o acessório poderia ficar sem atrapalhar outras atividades?",
            "Que alternativa de local merece ser comparada com mais atenção?",
        ]),
        ("Observe a rotina de limpeza", [
            "Qual posição simplifica a organização da área ao redor?",
            "Que acesso precisa permanecer disponível para limpar o espaço?",
            "Onde a rotina atual cria um limite prático para o posicionamento?",
        ]),
        ("Compare mais de um local", [
            "Quais pontos da casa atendem melhor ao objetivo desta análise?",
            "Que vantagem pertence ao ambiente e não ao produto?",
            "Qual opção de local depende de informação ainda não confirmada?",
        ]),
        ("Volte à página do item", [
            "Que informação da oferta pode mudar a escolha do local?",
            "Onde confirmar instruções relacionadas ao uso do acessório?",
            "Qual ausência de informação impede fechar uma posição agora?",
        ]),
        ("Registre as restrições do ambiente", [
            "Quais obstáculos do ambiente precisam ficar anotados?",
            "Que tarefa da casa disputa espaço com o acessório?",
            "Qual pendência deve ser resolvida antes da decisão?",
        ]),
        ("Escolha sem criar regra universal", [
            "Qual local faz mais sentido para este contexto específico?",
            "Que alternativa continua disponível caso a organização mude?",
            "O que deve ser revisto se a rotina da casa mudar?",
        ]),
    ],
    "maintenance": [
        ("Delimite o objetivo da manutenção", [
            "Que parte da rotina doméstica precisa ser organizada primeiro?",
            "Qual dúvida depende de instrução ligada ao item atual?",
            "O que pode permanecer como pendência nesta consulta?",
        ]),
        ("Procure a orientação correta", [
            "Onde a oferta atual apresenta orientações de conservação?",
            "Que informação precisa ser confirmada em fonte ligada ao item?",
            "Qual ponto não deve ser preenchido usando uma opção parecida?",
        ]),
        ("Separe rotina e instrução", [
            "Que cuidado pertence à organização da casa e não ao produto?",
            "Qual orientação depende diretamente da página ou do fabricante?",
            "Onde uma escolha pessoal deve continuar identificada como preferência?",
        ]),
        ("Evite procedimentos inventados", [
            "Que etapa ainda não possui orientação confirmada?",
            "Qual pergunta precisa continuar aberta até nova consulta?",
            "Onde registrar a ausência de instrução sem completar por conta própria?",
        ]),
        ("Revise as fontes atuais", [
            "Quais referências estão ligadas exatamente à opção analisada?",
            "Que informação antiga precisa ser conferida novamente?",
            "Onde uma divergência entre fontes deve permanecer registrada?",
        ]),
        ("Organize a próxima conferência", [
            "Que ponto merece nova consulta perto da decisão?",
            "Qual fonte deverá ser revisitada quando a oferta mudar?",
            "Que pendência pode ser resolvida sem ampliar o assunto do artigo?",
        ]),
        ("Feche a rotina de verificação", [
            "Quais orientações ficaram claramente associadas à fonte correta?",
            "Quais dúvidas ainda não têm resposta suficiente?",
            "O que precisa continuar fora do texto até ser confirmado?",
        ]),
    ],
    "checklist": [
        ("Comece pelo contexto do uso", [
            "Em qual situação o acessório será considerado nesta decisão?",
            "Que parte da rotina precisa entrar no checklist?",
            "Qual dúvida deve ser registrada antes de consultar a oferta?",
        ]),
        ("Liste o que precisa ser conferido", [
            "Quais informações da página atual influenciam esta escolha?",
            "Que ponto depende de instrução ligada à opção analisada?",
            "Qual questão ainda não pode ser respondida com a fonte disponível?",
        ]),
        ("Separe contexto e oferta", [
            "Que critério pertence à rotina e não ao anúncio?",
            "Qual informação precisa vir diretamente da página do item?",
            "Onde uma preferência pessoal deve permanecer apenas como preferência?",
        ]),
        ("Compare sem presumir adequação", [
            "Quais opções podem ser comparadas usando o mesmo critério?",
            "Que diferença precisa de confirmação antes de ser considerada?",
            "Qual conclusão deve permanecer aberta por falta de informação?",
        ]),
        ("Revise as instruções disponíveis", [
            "Onde estão as orientações ligadas ao uso desta opção?",
            "Que ponto precisa ser conferido novamente antes da decisão?",
            "Qual informação não deve ser transferida de outro produto?",
        ]),
        ("Organize as pendências do checklist", [
            "Quais itens da lista já têm resposta verificável?",
            "Quais perguntas precisam de uma fonte adicional?",
            "Que ponto pode ser retirado por não influenciar esta decisão?",
        ]),
        ("Faça a revisão final", [
            "O checklist continua focado no objetivo desta página?",
            "As respostas verificadas estão ligadas às fontes correspondentes?",
            "Quais pendências devem continuar visíveis antes da escolha?",
        ]),
    ],
    "routine": [
        ("Defina o momento de uso", [
            "Em quais partes da rotina este acessório seria considerado?",
            "Que tarefa vem antes ou depois desse momento?",
            "Qual limite de tempo ou espaço precisa ser apenas observado?",
        ]),
        ("Organize o espaço da atividade", [
            "Que área da casa está disponível durante esse momento?",
            "Quais objetos já ocupam o mesmo espaço na rotina?",
            "Que mudança de organização precisa ser considerada antes do uso?",
        ]),
        ("Mantenha o foco no planejamento", [
            "Que pergunta ajuda a organizar a atividade sem prometer resultado?",
            "Qual informação pertence ao contexto e não ao produto?",
            "O que precisa ser confirmado na página atual da opção?",
        ]),
        ("Consulte as instruções do item", [
            "Onde a oferta apresenta orientações ligadas ao uso?",
            "Que ponto deve permanecer aberto quando a instrução está ausente?",
            "Qual informação não deve ser inferida pelo nome do produto?",
        ]),
        ("Planeje alternativas de rotina", [
            "Que outro momento da rotina poderia receber esta atividade?",
            "Qual alternativa exige menos reorganização do ambiente?",
            "Que opção deve permanecer apenas como possibilidade nesta análise?",
        ]),
        ("Registre o que foi observado", [
            "Quais aspectos do contexto ficaram claros durante o planejamento?",
            "Que dúvida ainda depende de consulta à fonte atual?",
            "Qual anotação ajuda a comparar outra opção depois?",
        ]),
        ("Revise antes de decidir", [
            "O plano continua coerente com o espaço realmente disponível?",
            "As informações específicas vieram da fonte correspondente?",
            "Quais pontos ainda precisam permanecer como pendência?",
        ]),
    ],
    "errors": [
        ("Evite começar pela linguagem do anúncio", [
            "Qual é a pergunta editorial antes de abrir a oferta?",
            "Que expressão comercial não deve virar conclusão automática?",
            "Qual critério pode manter a pesquisa focada no objetivo?",
        ]),
        ("Não misture opções diferentes", [
            "As informações consultadas pertencem à mesma opção analisada?",
            "Que detalhe veio de uma página apenas semelhante?",
            "Qual ponto deve ser removido quando a identidade não está clara?",
        ]),
        ("Não complete o que a fonte omite", [
            "Qual informação continua ausente na página atual?",
            "Que dúvida precisa permanecer aberta sem uma fonte adequada?",
            "Onde registrar a lacuna para uma nova consulta?",
        ]),
        ("Não confunda preferência com fato", [
            "Que escolha depende do contexto particular da casa?",
            "Qual ponto realmente está descrito na oferta atual?",
            "Onde uma opinião deve permanecer separada da informação verificável?",
        ]),
        ("Não compare critérios diferentes", [
            "As alternativas estão sendo avaliadas pelo mesmo objetivo?",
            "Que comparação perdeu sentido por usar referências diferentes?",
            "Qual critério precisa ser redefinido antes de continuar?",
        ]),
        ("Não trate histórico como estado atual", [
            "Que informação antiga precisa ser conferida novamente?",
            "Qual mudança da oferta pode afetar a comparação?",
            "Onde a memória ajuda sem substituir uma nova consulta?",
        ]),
        ("Feche corrigindo as pendências", [
            "Quais erros de pesquisa foram eliminados nesta revisão?",
            "Que dúvidas ainda exigem uma fonte melhor?",
            "Qual anotação evitará repetir a mesma confusão depois?",
        ]),
    ],
    "organization": [
        ("Defina o objetivo da organização", [
            "Que problema de espaço ou rotina precisa ser organizado?",
            "Qual tarefa doméstica deve continuar simples depois da escolha?",
            "Que limite do ambiente precisa ser anotado primeiro?",
        ]),
        ("Mapeie onde o item entraria", [
            "Que área da casa está disponível para esta opção?",
            "Quais objetos já disputam o mesmo espaço?",
            "Que passagem ou tarefa não deve ser atrapalhada?",
        ]),
        ("Separe uso e armazenamento", [
            "Onde o acessório ficaria quando não estivesse em uso?",
            "Que parte da rotina muda entre usar e guardar o item?",
            "Qual pendência depende de informação da oferta atual?",
        ]),
        ("Compare alternativas de organização", [
            "Que arranjo exige menos mudança na rotina existente?",
            "Qual opção de local permanece fácil de revisar depois?",
            "Que vantagem pertence ao ambiente e não ao produto?",
        ]),
        ("Confira o que depende do item", [
            "Que informação da página atual influencia a organização?",
            "Onde confirmar orientações ligadas ao uso ou armazenamento?",
            "Qual ausência de informação precisa continuar visível?",
        ]),
        ("Registre as decisões do espaço", [
            "Quais critérios fizeram uma alternativa continuar na lista?",
            "Que limitação descartou outra possibilidade de organização?",
            "Qual anotação ajudará a revisar o espaço no futuro?",
        ]),
        ("Finalize sem engessar a rotina", [
            "A organização escolhida continua adaptável a mudanças da casa?",
            "Quais pontos dependem de nova conferência perto da decisão?",
            "Que alternativa pode permanecer registrada como plano secundário?",
        ]),
    ],
}


def family_for(candidate):
    angle = evidence.normalize(candidate.get("angle") or "")
    if "erro" in angle:
        return "errors"
    if "posicion" in angle:
        return "placement"
    if any(term in angle for term in ["limpeza", "higiene", "conservacao", "manutencao"]):
        return "maintenance"
    if any(term in angle for term in ["checklist", "passeio", "desloc", "ajuste", "compatibilidade", "supervisao"]):
        return "checklist"
    if any(term in angle for term in ["brincadeira", "atividade", "interacao", "estimulo"]):
        return "routine"
    if any(term in angle for term in ["organiza", "bagunca", "guardar", "cantinho"]):
        return "organization"
    return "comparison"


def variant_prompt(candidate, package):
    current_candidate[0] = candidate
    current_package[0] = package
    family = family_for(candidate)
    return f"""Você controla apenas a variação de apresentação de um template editorial SAFE.

FAMÍLIA: {family}

Retorne SOMENTE JSON válido:
{{"variants":["A","B","C","A","B","C","A"]}}

REGRAS:
- Exatamente sete valores.
- Cada valor deve ser apenas A, B ou C.
- Não escreva títulos, perguntas, fatos, conselhos ou qualquer outro texto.
"""


def validate_variants(raw):
    if not isinstance(raw, dict):
        raise RuntimeError("SAFE V14: resposta não é objeto JSON")
    variants = raw.get("variants")
    if not isinstance(variants, list) or len(variants) != 7:
        raise RuntimeError("SAFE V14: variants_count")
    out = []
    for value in variants:
        key = str(value or "").strip().upper()
        if key not in {"A", "B", "C"}:
            raise RuntimeError("SAFE V14: invalid_variant")
        out.append(key)
    return out


def render_section(heading, questions, variant):
    idx = {"A": 0, "B": 1, "C": 2}[variant]
    opener = OPENERS[idx]
    closer = CLOSERS[(idx + 1) % len(CLOSERS)]
    question_html = "<ul>" + "".join(f"<li>{escape(q.rstrip(' ?.!;:') + '?')}</li>" for q in questions) + "</ul>"
    return (
        f"<h2>{escape(heading)}</h2>"
        f"<p>{escape(opener)}</p>"
        f"{question_html}"
        f"<p>{escape(closer)}</p>"
    )


def render_article(candidate, variants):
    family = family_for(candidate)
    blueprints = FAMILY_BLUEPRINTS[family]
    html = "".join(
        render_section(heading, questions, variants[idx])
        for idx, (heading, questions) in enumerate(blueprints)
    )
    wc = builder.word_count(html)
    if wc < 580 or wc > 780:
        raise RuntimeError(f"SAFE V14: rendered_word_count:{wc}")
    ns["safety_check_editorial"](html)
    if "??" in html:
        raise RuntimeError("SAFE V14: double_question_mark")
    return html


def fix_meta(doc, candidate):
    keyword = str(candidate.get("keyword") or "acessório pet").strip()
    angle = str(candidate.get("angle") or "critérios de escolha").strip()
    if evidence.normalize(angle).startswith("criterios"):
        meta = f"{keyword.capitalize()}: compare opções com {angle}, conferindo as informações atuais da oferta antes da escolha."
    else:
        meta = f"{keyword.capitalize()}: organize a decisão sobre {angle}, conferindo as informações atuais da oferta antes da escolha."
    if len(meta) > 155:
        meta = f"{keyword.capitalize()}: organize a escolha com critérios claros e confira as informações atuais da oferta antes de decidir."
    doc["meta_description"] = meta[:155].rstrip()
    return doc


def editorial_call(prompt):
    elapsed = time.monotonic() - LAST_CALL[0]
    if LAST_CALL[0] and elapsed < MIN_CALL_INTERVAL_SECONDS:
        time.sleep(MIN_CALL_INTERVAL_SECONDS - elapsed)
    LAST_CALL[0] = time.monotonic()

    raw, usage = original_call(prompt)
    variants = validate_variants(raw)
    article_html = render_article(current_candidate[0], variants)
    doc = normalize_doc({"article_html": article_html}, current_candidate[0], current_package[0])
    return fix_meta(doc, current_candidate[0]), usage


builder.prompt_for = variant_prompt
builder.groq_call = editorial_call
builder.gate = strict_gate
builder.main()
