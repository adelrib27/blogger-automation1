from pathlib import Path

import article_builder_v1 as builder

# Carrega a lógica V7 sem executar o main, preservando uma única fonte para
# Fact Gate, plano Groq, títulos, anti-duplicação e famílias editoriais.
source_path = Path(__file__).with_name("article_builder_evergreen_v7.py")
source = source_path.read_text(encoding="utf-8")
marker = "\nbuilder.main()\n"
if marker not in source:
    raise RuntimeError("SAFE V7 loader: ponto de entrada não encontrado")
source = source.rsplit(marker, 1)[0] + "\n"
ns = {"__name__": "vida_pet_evergreen_v7_embedded", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)

base_normalize = ns["normalize_doc"]
family_for = ns["family_for"]

EXTENSION_BLOCKS = {
    "criteria": [
        ("Compare apenas dados que respondem à pergunta", "Depois de reunir as fontes, volte à pergunta principal e elimine informações que não ajudam a respondê-la. Essa filtragem evita que o artigo cresça apenas pela repetição de detalhes comerciais. Um dado pode estar correto e ainda assim ser irrelevante para aquele ângulo. Ao manter somente o que contribui para a decisão, a página fica mais clara e também mais diferente de publicações anteriores sobre o mesmo produto. O histórico editorial deve registrar quais critérios foram usados para que uma nova rodada escolha outro conjunto de perguntas."),
        ("Registre a lógica da decisão", "Além de guardar as evidências, registre por que cada informação foi considerada importante. Esse pequeno resumo permite que uma futura atualização entenda o raciocínio sem copiar o texto antigo. Se a oferta mudar, o sistema consegue revisar apenas os pontos afetados e preservar o restante da pesquisa. A memória passa a guardar não só o produto, mas também a intenção editorial que já foi explorada. Isso ajuda a impedir que um novo artigo volte ao mesmo caminho apenas com um título diferente."),
    ],
    "placement": [
        ("Use alternativas em vez de uma posição única", "Quando mais de um ponto do ambiente parece possível, mantenha as alternativas até que os dados necessários estejam confirmados. Essa prática evita transformar uma hipótese inicial em conclusão. Um esquema simples com opções A, B e C já ajuda a visualizar o espaço e a perceber quais informações do produto realmente fazem diferença. Depois da consulta às fontes, algumas alternativas podem ser descartadas. O artigo permanece centrado em planejamento do ambiente, sem atribuir ao item uma capacidade que não tenha sido demonstrada."),
        ("Revise o plano quando o ambiente mudar", "O posicionamento não precisa ser tratado como decisão permanente. Mudanças de móveis, circulação ou organização podem alterar os critérios usados inicialmente. Guarde o motivo de cada escolha e revise o plano quando o contexto mudar. Para a automação editorial, isso também cria uma distinção importante: atualizar a pesquisa do espaço não significa repetir a descrição do produto. Uma futura página pode usar outro ângulo, enquanto esta permanece registrada como o conteúdo dedicado ao planejamento de posição."),
    ],
    "checklist": [
        ("Dê uma ação clara para cada item da lista", "Revise o checklist e confirme que cada linha leva a uma ação concreta. Verbos como conferir, medir, identificar, comparar e registrar ajudam a separar etapas úteis de observações genéricas. Se um item não muda a decisão nem ajuda a verificar uma informação, ele pode ser removido. Essa limpeza deixa a lista menor, porém mais funcional. Também evita que o texto seja preenchido com frases semelhantes às de outros artigos. O objetivo é criar um roteiro de verificação que possa ser repetido como processo, não como conteúdo copiado."),
        ("Guarde o resultado do checklist para a próxima rodada", "Depois da análise, salve quais itens foram confirmados, quais ficaram pendentes e quais fontes sustentaram cada resposta. Quando o produto reaparecer no rodízio, o sistema consulta esse registro antes de gerar outro conteúdo. Se o próximo ângulo não for um checklist, a estrutura muda naturalmente. Se voltar a ser uma lista, ela precisa responder a outra intenção. Essa memória permite continuidade sem exigir que o blog esqueça o que já publicou e sem depender de revisão manual de todo o acervo."),
    ],
    "maintenance": [
        ("Diferencie informação atual de registro histórico", "Uma orientação encontrada em uma rodada antiga continua útil como histórico, mas não deve ser tratada automaticamente como informação atual. Ao reutilizar o produto, verifique novamente a fonte e compare o que mudou. Se a instrução desaparecer ou for alterada, registre a diferença. Essa disciplina permite manter uma memória rica sem congelar o anúncio no tempo. O conteúdo de conservação pode então ser atualizado com rastreabilidade, enquanto outros artigos do mesmo produto seguem ângulos independentes."),
        ("Use pendências para orientar a próxima consulta", "Quando a pesquisa terminar com pontos sem resposta, transforme essas lacunas em uma lista para futura verificação. Não é necessário preencher cada espaço na mesma rodada. Em uma próxima consulta, o sistema pode buscar exatamente essas informações e decidir se já existe evidência suficiente. Essa prática economiza pesquisa repetida e reduz a tentação de usar fontes apenas semelhantes. O histórico funciona como mapa do que já foi confirmado e do que ainda precisa ser esclarecido."),
    ],
    "errors": [
        ("Revise o texto procurando conclusões sem origem", "Antes de liberar a página, examine frases que soam como conclusão e pergunte qual fonte ou qual raciocínio editorial as sustenta. Se uma afirmação específica sobre o produto não tiver evidência autorizada, ela precisa sair. Se for apenas orientação de pesquisa, deixe claro esse papel. Essa revisão simples identifica muitos erros antes da publicação e complementa o Fact Gate automático. O processo também ajuda a manter o conteúdo independente da linguagem de venda."),
        ("Transforme cada erro detectado em uma regra", "Quando o sistema encontra um problema recorrente, registre a causa e converta-a em uma trava reutilizável. Pode ser uma palavra ampla demais, uma fonte sem identidade suficiente ou uma estrutura próxima de artigo anterior. Assim, a automação melhora a cada rodada em vez de repetir a mesma falha. O histórico de rejeições passa a ter valor operacional: ele não serve apenas para explicar por que um candidato caiu, mas para reduzir a chance de o mesmo tipo de erro voltar ao buffer."),
    ],
    "routine": [
        ("Mantenha perguntas da rotina separadas das especificações", "Ao revisar o artigo, identifique quais perguntas pertencem ao contexto da casa e quais dependem do produto. Espaço disponível, local de armazenamento e sequência de tarefas são observações do ambiente. Medidas, materiais ou instruções do item exigem evidência. Essa separação torna o texto mais transparente e permite que a rotina seja discutida sem criar fatos. Também facilita a reutilização futura, porque o sistema consegue mudar o foco sem precisar repetir os mesmos detalhes comerciais."),
        ("Faça a rotina funcionar como mapa editorial", "Cada etapa descrita pode sugerir um tema futuro, mas não precisa ser explorada inteira na mesma página. Registre quais partes receberam atenção e deixe as demais como possibilidades. Essa prática amplia o catálogo de assuntos sem produzir textos quase iguais. Quando o produto voltar ao rodízio, a memória mostra quais caminhos ainda não foram usados. Se nenhuma direção suficientemente diferente restar, o item entra em descanso e outro produto assume a vaga."),
    ],
    "variation": [
        ("Compare o novo plano com o histórico antes de escrever", "Antes da geração final, coloque lado a lado o novo ângulo e os registros anteriores do produto. Observe intenção, subtítulos e tipo de conclusão. Se a proposta já estiver representada no acervo, escolha outra direção antes de gastar uma nova geração. Essa checagem antecipada complementa o teste semântico realizado depois do texto pronto. Juntas, as duas etapas reduzem custo e evitam que pequenas mudanças de redação sejam confundidas com originalidade editorial."),
        ("Use o failover quando a diferença não for suficiente", "Nem todo produto conseguirá oferecer um novo assunto em cada rodada. Quando o Anti-Duplicate Guard continuar reprovando as tentativas, o sistema deve aceitar esse sinal e avançar para outro item validado. A fila não precisa ser preenchida com uma versão mais fraca do mesmo conteúdo. O failover preserva a qualidade e permite que o produto volte depois, quando houver outro contexto, nova evidência ou uma abordagem ainda não explorada."),
    ],
    "compatibility": [
        ("Separe o que o leitor mede do que a oferta informa", "Uma análise de compatibilidade costuma reunir dados de duas origens. De um lado estão medidas e limitações observadas pelo leitor; do outro, informações confirmadas na fonte do produto. Não misture essas origens nem complete uma delas por suposição. A comparação só pode avançar quando os dados necessários estiverem claros. Essa organização transforma compatibilidade em processo verificável e evita que um nome comercial seja usado como garantia de adequação."),
        ("Registre quais condições ainda precisam ser confirmadas", "Se a decisão depende de um dado ausente, escreva exatamente qual informação falta e onde ela deveria ser encontrada. Essa pendência pode orientar uma consulta posterior ou justificar a troca de candidato. Guardar a questão no histórico também evita que uma futura geração invente uma resposta para preencher o espaço. Quando o produto voltar ao rodízio, o sistema começa sabendo o que estava em aberto e pode verificar se a fonte atual trouxe alguma novidade."),
    ],
}


def extended_normalize(plan, candidate, package):
    doc = base_normalize(plan, candidate, package)
    family = family_for(candidate.get("angle") or "")
    marker = "<h2>Identificação revalidada nesta rodada</h2>"
    html = str(doc.get("article_html") or "")
    if marker not in html:
        raise RuntimeError("SAFE V8: seção de identificação não encontrada")
    before, after = html.split(marker, 1)
    extra = ""
    for heading, paragraph in EXTENSION_BLOCKS[family]:
        extra += f"<h2>{heading}</h2><p>{paragraph}</p>"
    doc["article_html"] = before + extra + marker + after
    return doc


ns["normalize_doc"] = extended_normalize
builder.prompt_for = ns["plan_prompt"]
builder.groq_call = ns["throttled_call"]
builder.gate = ns["strict_gate"]
builder.main()
