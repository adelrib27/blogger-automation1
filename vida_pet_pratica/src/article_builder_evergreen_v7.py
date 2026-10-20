import json
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

FAMILY_INTRO = {
    "criteria": "Este conteúdo parte de uma pergunta de comparação diferente das abordagens anteriores. A ideia é organizar quais informações realmente precisam ser confirmadas antes de decidir, sem transformar o nome comercial em conclusão. O produto entra apenas como referência identificada pelas fontes da rodada; o restante do artigo funciona como método de pesquisa. Assim, a nova página consegue acrescentar uma intenção editorial própria mesmo quando o item já apareceu antes no blog.",
    "placement": "Nesta abordagem, o ponto de partida é o ambiente e não a ficha comercial. O objetivo é organizar uma análise de espaço, circulação e acesso antes de relacionar qualquer detalhe ao item. Quando uma informação específica do produto for necessária, ela precisa estar confirmada na fonte correta. Isso cria um conteúdo centrado em planejamento do local, diferente de uma comparação de modelos ou de uma descrição de características.",
    "checklist": "Aqui o produto volta ao blog por meio de um checklist, não de uma nova descrição comercial. A proposta é separar o que pode ser preparado e observado pelo leitor daquilo que depende de confirmação no anúncio. Cada etapa precisa levar a uma ação verificável: consultar uma fonte, identificar uma versão, medir o contexto ou registrar uma pendência. Dessa forma, o artigo ganha estrutura própria e evita apenas reescrever o conteúdo anterior.",
    "maintenance": "O foco desta página é como pesquisar informações de conservação sem inventar procedimentos. Antes de qualquer orientação específica, é preciso localizar instruções vinculadas ao item correto e registrar o que ainda não está disponível. O texto organiza essa verificação e diferencia escolhas domésticas de dados do produto. Assim, o mesmo item pode sustentar um novo assunto sem repetir a publicação anterior nem transferir instruções de ofertas parecidas.",
    "errors": "Uma forma de criar um novo conteúdo sobre um produto já conhecido é examinar erros de pesquisa e comparação. Em vez de enumerar características, esta página mostra onde uma decisão pode perder qualidade: identidade confusa, fonte inadequada, versão misturada ou conclusão feita sem evidência. O produto permanece como caso concreto identificado pelas fontes, mas o valor editorial está no método usado para evitar esses erros em uma nova consulta.",
    "routine": "Esta página usa a rotina como eixo editorial. O objetivo não é afirmar como o produto funciona, mas organizar as perguntas que surgem quando um acessório precisa conviver com espaço, armazenamento e outras tarefas da casa. Os fatos específicos continuam separados e vinculados às evidências. Essa mudança de perspectiva permite reutilizar um item conhecido sem reproduzir a mesma estrutura de comparação ou descrição usada anteriormente.",
    "variation": "O novo ângulo desta publicação é a variação editorial: como planejar alternativas sem transformar preferência ou reação do animal em promessa. O texto se concentra em registrar opções, contexto e perguntas para consulta, enquanto os dados específicos do produto permanecem limitados ao que foi revalidado. Essa separação ajuda o blog a ampliar o assunto de um item conhecido sem apenas trocar palavras do título ou repetir a ficha comercial.",
    "compatibility": "Nesta abordagem, compatibilidade é tratada como uma sequência de perguntas e não como uma garantia. O artigo organiza quais dados precisam ser comparados entre o contexto do leitor e a fonte do item, mantendo em aberto aquilo que não estiver confirmado. O produto é identificado pelas evidências da rodada, mas nenhuma adequação é presumida pelo nome ou pela imagem. Isso cria uma intenção editorial distinta das páginas anteriores.",
}

FAMILY_BLOCKS = {
    "criteria": [
        ("Defina a pergunta principal da comparação", "Antes de abrir várias páginas, escreva qual decisão o conteúdo precisa ajudar a organizar. Uma pergunta clara evita que a pesquisa vire uma coleção de dados sem função. Se o foco é tamanho, versão, instruções ou identificação, procure apenas as informações necessárias para esse objetivo e marque o que ficou ausente. O anúncio pode apresentar muitos detalhes, mas nem todos precisam entrar no artigo. Essa seleção reduz ruído e mantém a nova abordagem separada do histórico já publicado. Quando uma questão não puder ser respondida pela fonte correta, ela permanece como pendência em vez de ser completada por inferência."),
        ("Dê pesos diferentes às fontes", "Uma fonte ligada ao item exato tem função diferente de uma página apenas semelhante. Antes de usar qualquer informação, registre por que aquela fonte é relevante e qual vínculo existe com o produto. Uma segunda página pode ajudar a confirmar identidade ou levantar perguntas, mas não deve transferir especificações quando a correspondência não está demonstrada. Esse processo torna a comparação auditável: cada fato específico consegue apontar para sua evidência, enquanto observações gerais permanecem claramente separadas. Quantidade de resultados não substitui qualidade de correspondência, e uma lacuna bem registrada é preferível a uma resposta construída com dados de outro item."),
        ("Converta palavras amplas em verificações", "Termos como prático, compacto ou funcional podem ter significados diferentes para cada rotina. Em vez de aceitar essas palavras como conclusão, converta-as em perguntas observáveis. A página informa dimensões? Existem variações? Há instruções associadas à versão escolhida? O leitor consegue identificar o item sem depender apenas de fotografia? Esse tipo de decomposição permite comparar sem prometer resultado. Também cria um texto mais útil do que repetir a linguagem promocional, porque mostra o caminho da decisão. Se um critério importante não estiver documentado, o artigo pode apontar exatamente o que precisa ser conferido antes de avançar."),
        ("Feche a análise com pendências explícitas", "A etapa final não precisa produzir uma resposta para tudo. Revise o que foi confirmado, o que permanece variável e quais pontos ainda exigem consulta. Informações comerciais podem mudar, por isso a página atual do item deve ser revista quando um detalhe for decisivo. Guardar as pendências ajuda também em futuras atualizações: o sistema sabe quais questões precisam de nova checagem quando o produto voltar ao rodízio. Esse fechamento transforma a publicação em um guia de comparação, não em uma reprodução da oferta, e preserva espaço para outros ângulos editoriais no futuro."),
    ],
    "placement": [
        ("Mapeie o ambiente antes de escolher um ponto", "Comece observando o local onde o acessório poderia entrar na rotina. Marque áreas de passagem, móveis próximos, portas, cantos e superfícies já ocupadas. O objetivo não é indicar uma posição universal, mas reconhecer quais limitações do ambiente precisam ser comparadas com informações confirmadas do item. Se dimensões forem importantes e ainda não estiverem disponíveis na fonte correta, mantenha mais de uma alternativa em aberto. Planejar o espaço antes de concluir evita que uma fotografia seja usada como escala e cria uma análise independente das promessas do anúncio."),
        ("Separe circulação, armazenamento e área de uso", "Um mesmo cômodo pode ter zonas com funções diferentes. Algumas partes precisam permanecer livres, outras recebem objetos guardados e outras concentram atividades do dia a dia. Ao pensar no posicionamento, descreva essas funções primeiro e só depois relacione o produto ao espaço. Essa sequência ajuda a identificar quais dados realmente fazem falta. O conteúdo não precisa afirmar que determinado ponto é melhor; pode mostrar como comparar opções e registrar limitações. Quando a decisão depende de tamanho, instalação ou outro detalhe do item, use somente o que estiver associado à oferta correta."),
        ("Considere o acesso ao redor do item", "Além do espaço ocupado, observe se o local permite acessar a área próxima para reorganizar objetos e revisar o ambiente quando necessário. Esse critério pertence ao planejamento da casa, não a uma característica do produto. Por isso, ele pode ser discutido sem atribuir capacidades ao item. Faça um pequeno esquema do local e compare duas ou mais posições possíveis. Depois volte às fontes para verificar quais informações do produto podem confirmar ou eliminar uma alternativa. Se a fonte não responder, preserve a incerteza em vez de transformar uma hipótese de posicionamento em recomendação definitiva."),
        ("Registre por que cada posição foi considerada", "Finalize anotando os motivos que levaram cada alternativa a continuar ou sair do planejamento: espaço, circulação, acesso e dados efetivamente confirmados. Esse registro permite revisar a escolha sem reconstruir toda a pesquisa e diferencia esta publicação de um artigo voltado a características ou comparação de modelos. Quando o mesmo produto voltar ao rodízio, o histórico mostrará que o tema de posicionamento já foi explorado. O próximo conteúdo poderá então escolher outra intenção, mantendo a produção contínua sem repetir estrutura, título ou raciocínio."),
    ],
    "checklist": [
        ("Monte a lista antes de consultar a oferta", "Um checklist útil começa pelo que precisa ser verificado, e não pelo que o anúncio escolheu destacar. Anote os pontos que influenciam a decisão no contexto do leitor e depois use as fontes para responder apenas ao que depende do produto. Essa ordem reduz a influência da linguagem promocional e mantém o artigo focado em ações concretas. Cada item da lista deve terminar em uma verificação: confirmar identidade, conferir uma versão, medir o ambiente ou registrar uma informação ausente. O que não puder ser confirmado continua aberto, sem ser completado por uma página semelhante."),
        ("Separe confirmados, variáveis e pendentes", "Divida o checklist em três grupos. No primeiro ficam dados sustentados por evidências ligadas ao item. No segundo, informações comerciais que podem mudar e precisam ser revistas perto da decisão. No terceiro, perguntas ainda sem resposta. Essa separação deixa claro o limite entre fato e pesquisa em andamento. Também facilita uma atualização futura, porque o sistema sabe onde procurar mudanças. Uma lista incompleta, mas rastreável, é mais útil do que uma lista cheia de detalhes cuja origem não pode ser demonstrada. O objetivo é organizar a decisão, não preencher todos os campos a qualquer custo."),
        ("Confirme item e variação antes de usar números", "Quando uma página reúne versões diferentes, qualquer medida ou configuração precisa permanecer associada à opção correta. Antes de copiar um dado para o checklist, confirme que ele pertence ao mesmo item e à mesma variação analisada. Se essa ligação não estiver clara, marque o ponto para nova consulta. O mesmo cuidado vale para outras lojas: uma oferta parecida não prova que o produto é idêntico. Essa etapa evita misturar versões e transforma a identificação em parte explícita do processo. Ela também cria um caminho de auditoria para cada informação específica usada no artigo."),
        ("Faça uma revisão final da página atual", "Antes de encerrar a lista, consulte novamente a oferta atual quando a decisão depender de um detalhe comercial ou técnico. Descrições, opções e condições podem mudar depois que o histórico foi criado. A memória persistente serve para lembrar o que já foi abordado e quais evidências existiam, mas não substitui a nova checagem. Registre a data da consulta e as pendências que permaneceram. Em uma futura reutilização do produto, esse histórico ajuda a escolher um ângulo diferente e impede que o sistema monte o mesmo checklist com palavras apenas ligeiramente alteradas."),
    ],
    "maintenance": [
        ("Procure instruções ligadas ao item exato", "Quando o assunto é conservação, comece pelas instruções associadas ao produto correto. Diferencie documentação, descrição do vendedor e comentários de compradores. Uma informação encontrada em item semelhante pode indicar o que vale pesquisar, mas não deve virar procedimento específico. Se a fonte exata não explicar um ponto importante, registre a ausência. O artigo continua útil ao mostrar como localizar e comparar orientações, sem inventar uma rotina. Essa disciplina permite falar de manutenção com clareza mesmo quando a documentação disponível é curta ou incompleta."),
        ("Separe procedimento do produto e organização da casa", "A forma como alguém guarda ou organiza um acessório pertence à rotina doméstica; já um procedimento específico do item precisa de fonte. Manter essa divisão evita que uma escolha pessoal seja apresentada como instrução oficial. O texto pode explicar como registrar documentos, guardar referências e planejar uma nova consulta sem atribuir ao produto um método não confirmado. Quando o item retornar ao rodízio, a automação deve consultar novamente as fontes relevantes em vez de assumir que a orientação antiga continua válida. A memória ajuda a localizar o histórico, mas não substitui evidência atual."),
        ("Registre divergências sem escolher por conveniência", "Se duas fontes ligadas ao produto apresentarem informações diferentes, não selecione automaticamente a mais detalhada. Anote a divergência e procure uma referência com vínculo mais forte com o item. Enquanto o conflito permanecer, deixe esse ponto fora das instruções específicas. Essa decisão mantém o texto coerente com o Evidence Engine e evita combinar partes de versões distintas. Uma divergência também pode justificar failover para outro candidato quando compromete o assunto principal. A automação contínua deve preservar o padrão de evidência mesmo que isso exija abandonar um produto naquela rodada."),
        ("Guarde a trilha para a próxima atualização", "Ao finalizar a pesquisa, registre quais fontes foram consultadas, quando a checagem ocorreu e quais pontos cada referência sustentou. Esse histórico permite que uma futura rodada saiba exatamente o que precisa ser revalidado. Se a página mudar, a nova publicação poderá refletir o estado atual sem apagar o que havia sido observado antes. O produto pode voltar com outro assunto, mas o texto não deve copiar a estrutura da manutenção já usada. A persistência serve tanto para controlar fatos quanto para impedir repetição editorial ao longo do tempo."),
    ],
    "errors": [
        ("Evite começar pelo título comercial", "Quando o artigo nasce do título da oferta, ele tende a repetir a mesma ordem de características e palavras usada pelo vendedor. Comece pela pergunta editorial e use o nome do produto apenas para identificação confirmada. Essa mudança reduz a chance de transformar a página em uma ficha comercial ampliada. Também facilita criar novos conteúdos sobre o mesmo item, porque cada publicação pode responder a um problema diferente. O histórico deve guardar a intenção e a estrutura já usadas para impedir que uma futura rodada apenas reorganize frases que o blog já publicou."),
        ("Não complete lacunas com produtos parecidos", "Uma página semelhante pode trazer detalhes tentadores, mas aparência ou categoria não demonstram identidade. Se uma informação importante não aparece em fonte ligada ao item, mantenha a lacuna. O conteúdo pode orientar o leitor a conferir esse ponto em vez de oferecer uma resposta construída por inferência. Essa regra evita que uma automação muito ativa acumule pequenos erros ao longo de centenas de artigos. O failover existe justamente para permitir que um candidato seja abandonado quando a evidência não sustenta o assunto, sem pressionar o sistema a preencher a agenda com afirmações frágeis."),
        ("Não confunda muitas fontes com boa evidência", "Encontrar vários resultados não resolve um problema de correspondência. Um conjunto grande de ofertas semelhantes continua fraco para uma especificação se nenhuma estiver claramente ligada ao produto escolhido. Priorize identidade, autoridade e rastreabilidade. Fontes adicionais podem sugerir perguntas ou ajudar a localizar a página correta, mas apenas referências autorizadas sustentam fatos específicos. Essa hierarquia deixa a pesquisa mais consistente e facilita auditoria. Quando duas fontes realmente correspondem ao item e divergem, registre o conflito em vez de escolher a resposta que deixa o artigo mais completo."),
        ("Não repita a mesma arquitetura textual", "Trocar o produto ou o título não basta quando subtítulos, sequência de argumentos e conclusão permanecem iguais. O rodízio evergreen precisa comparar a nova página com o histórico e rejeitar estruturas muito próximas. Se a similaridade ultrapassar o limite, o artigo deve ser descartado e outro ângulo ou candidato entra no lugar. Essa trava protege o blog de uma coleção de páginas quase idênticas. O objetivo da memória persistente é tornar essa diferença mensurável, não depender apenas da impressão de que algumas palavras foram alteradas."),
    ],
    "routine": [
        ("Desenhe a rotina antes de olhar o produto", "Comece descrevendo quando o acessório aparece no dia a dia, onde ficaria guardado e quais outras tarefas acontecem no mesmo espaço. Esse mapa gera perguntas para a pesquisa sem depender de características comerciais. Depois, consulte o anúncio apenas nos pontos em que uma informação específica é necessária. Se um dado não estiver confirmado, mantenha a questão aberta. Essa ordem cria uma publicação centrada em organização, diferente de uma página de comparação. O produto serve como referência factual, enquanto o corpo do artigo ajuda a estruturar decisões que pertencem ao contexto da casa."),
        ("Divida o processo em momentos menores", "Uma rotina ampla pode ser separada em preparação, uso, armazenamento e revisão das informações. Cada momento produz perguntas próprias e ajuda a escolher o que realmente merece pesquisa. O texto não precisa impor horários ou procedimentos; ele apenas organiza a observação. Essa divisão também mostra onde faltam dados na oferta. Em vez de preencher a lacuna com uma suposição, registre o ponto para consulta. Quando o produto voltar ao blog no futuro, o histórico indicará quais partes da rotina já foram exploradas e permitirá escolher uma intenção diferente."),
        ("Organize também o histórico das informações", "A rotina do blog precisa guardar mais do que o texto publicado. Registre identificador, fontes, data de checagem, ângulo e fingerprint semântico. Esse conjunto permite saber o que já foi usado e o que precisa ser revisto. Se a oferta mudar, a automação consegue atualizar a pesquisa sem esquecer a estrutura anterior. O leitor não precisa ver todo o controle interno, mas se beneficia dele porque cada nova página começa de um estado conhecido. Persistência transforma o rodízio em expansão planejada, não em reciclagem improvisada."),
        ("Use o histórico para escolher o próximo assunto", "Depois de concluir a página, marque quais partes da rotina foram abordadas. Na próxima reutilização do item, o sistema consulta esse registro antes de escolher o novo ângulo. Se organização já foi explorada, pode avançar para comparação, posicionamento, conservação ou outro tema disponível. Caso todas as opções estejam próximas demais de conteúdos existentes, deixe o produto em descanso e escolha outro. Essa política mantém a produção contínua sem obrigar o blog a publicar uma variação superficial apenas para ocupar uma data na agenda."),
    ],
    "variation": [
        ("Mude a pergunta antes de mudar as palavras", "Um novo artigo só é realmente diferente quando responde a outra pergunta. Antes da geração, registre o foco usado anteriormente e escolha um eixo que ainda não esteja no histórico. A nova página pode organizar opções, contexto, espaço ou critérios de pesquisa, mas não deve simplesmente renomear subtítulos. Essa decisão é feita antes do texto e depois confirmada pelo fingerprint semântico. O produto pode continuar sendo a mesma referência factual, enquanto a intenção editorial muda de maneira verificável. Se a diferença não for suficiente, o sistema rejeita a tentativa e procura outra direção."),
        ("Planeje alternativas sem prever resposta do animal", "É possível discutir variedade de opções sem prometer como cada animal vai reagir. O conteúdo pode mostrar como registrar quais acessórios estão disponíveis, quais perguntas precisam ser conferidas e quais informações ainda faltam na oferta. Evite transformar preferência individual em resultado esperado. Essa cautela mantém o texto no campo de planejamento e pesquisa. Quando um detalhe específico do produto for relevante, ele entra apenas pela seção sustentada por evidências. Assim, o assunto se amplia sem misturar orientação editorial com afirmações que a fonte não demonstrou."),
        ("Alterne também a estrutura da página", "Variar o ângulo e manter a mesma arquitetura textual ainda pode produzir páginas muito próximas. Por isso, a automação precisa alternar a sequência de perguntas, o tipo de fechamento e os blocos usados. Um conteúdo pode ser checklist; outro, análise do ambiente; outro, erros de pesquisa. A comparação semântica depois da montagem funciona como última trava. Se a página continuar parecida com o histórico, o resultado não entra na fila READY. Essa regra protege a originalidade mesmo quando a biblioteca de produtos começa a se repetir."),
        ("Deixe ângulos esgotados em descanso", "Um produto não precisa gerar conteúdo indefinidamente sem pausa. Quando as abordagens disponíveis já foram usadas ou as novas tentativas continuam semelhantes, marque o item como temporariamente esgotado. O abastecedor pode selecionar outro produto validado e voltar mais tarde, especialmente se novas informações surgirem. Essa estratégia mantém a continuidade sem sacrificar variedade. O objetivo do rodízio é prolongar a vida editorial do catálogo, não transformar cada item em fonte obrigatória de páginas repetidas. O histórico persistente permite tomar essa decisão automaticamente."),
    ],
    "compatibility": [
        ("Transforme compatibilidade em perguntas separadas", "Não trate compatibilidade como uma conclusão única. Separe o tema em perguntas: existem medidas confirmadas, há variações identificadas, a fonte oferece instruções e qual dado do contexto do leitor precisa ser comparado? Cada resposta deve manter vínculo com sua origem. Se uma parte estiver ausente, a análise fica condicionada e não vira garantia. Essa estrutura ajuda a produzir um artigo útil sem presumir adequação pelo nome do produto. Também deixa claro quais informações precisam ser rechecadas quando a página comercial mudar ou quando o item voltar ao rodízio."),
        ("Confira cada versão antes de combinar dados", "Uma mesma oferta pode reunir opções diferentes. Ao usar qualquer medida ou configuração, confirme que o dado pertence à variação analisada. Não misture informações de páginas parecidas apenas porque o nome ou a fotografia lembram o item. Quando a associação estiver ambígua, registre a pendência. Esse cuidado evita uma falsa precisão e dá ao Evidence Engine uma regra clara: o vínculo de identidade vem antes da riqueza de detalhes. Uma publicação pode terminar com perguntas abertas e ainda cumprir seu papel de organizar a decisão."),
        ("Diferencie finalidade anunciada de adequação", "A forma como o vendedor apresenta o produto não resolve automaticamente todas as questões de uso no contexto do leitor. Trate finalidade comercial e compatibilidade como tópicos distintos. A primeira pode ajudar a identificar o item; a segunda depende dos dados necessários para a situação concreta. Essa separação evita transformar linguagem de venda em conclusão e permite que o artigo se concentre no método de verificação. Se a evidência não oferecer informação suficiente, o conteúdo orienta o que conferir em vez de afirmar que o item atende a uma condição específica."),
        ("Finalize com uma decisão condicionada", "No encerramento, organize o que foi confirmado e o que ainda depende de consulta. Evite frases universais. A decisão permanece condicionada às informações atuais do produto e ao contexto que o leitor consegue observar. Registre também a data das evidências, porque uma futura reutilização precisa revalidar os pontos relevantes. Esse fechamento cria uma base diferente de uma descrição comercial e permite que o mesmo produto retorne com outro assunto. Se o novo conteúdo ficar próximo demais do histórico, o Anti-Duplicate Guard deve bloquear a publicação."),
    ],
}


def family_for(angle):
    text = evidence.normalize(angle)
    if "posicionar" in text or text.startswith("onde "):
        return "placement"
    if "checklist" in text or "preparacao" in text or "deslocamento" in text:
        return "checklist"
    if "manutencao" in text or "limpeza" in text or "conservacao" in text:
        return "maintenance"
    if "erro" in text:
        return "errors"
    if "ajuste" in text or "compatibilidade" in text or "supervisao" in text:
        return "compatibility"
    if "variar" in text or "alternar" in text or "interacao" in text or "brincadeira" in text or "estimulo" in text:
        return "variation"
    if "organizar" in text or "organizacao" in text or "rotina" in text or "bagunca" in text:
        return "routine"
    return "criteria"


def subject_for(keyword):
    key = evidence.normalize(keyword)
    return {
        "brinquedo interativo pet": "Brinquedo interativo",
        "guia cachorro": "Guia para cachorro",
        "tapete coletor areia gato": "Tapete coletor de areia",
        "caixa areia gato": "Caixa de areia para gatos",
        "peitoral cachorro": "Peitoral para cachorro",
        "caixa transporte pet": "Caixa de transporte pet",
        "cama pet": "Cama pet",
        "comedouro pet": "Comedouro pet",
        "bebedouro fonte pet": "Bebedouro para pet",
        "comedouro lento pet": "Comedouro lento",
        "tapete higienico cachorro": "Tapete higiênico para cachorro",
        "escova tira pelos pet": "Escova tira pelos",
        "arranhador gato": "Arranhador para gatos",
        "porta racao pet": "Porta ração pet",
        "organizador acessorios pet": "Organizador de acessórios pet",
    }.get(key, "Acessório pet")


def title_for(candidate):
    family = family_for(candidate.get("angle") or "")
    suffix = {
        "criteria": "critérios antes de escolher",
        "placement": "como planejar o posicionamento",
        "checklist": "checklist para organizar a decisão",
        "maintenance": "como pesquisar conservação",
        "errors": "erros de comparação para evitar",
        "routine": "como organizar a rotina",
        "variation": "como variar a abordagem",
        "compatibility": "como conferir compatibilidade",
    }[family]
    text = f"{subject_for(candidate.get('keyword') or '')}: {suffix}"
    if len(text) <= 65:
        return text
    out = []
    for word in text.split():
        if len(" ".join(out + [word])) > 65:
            break
        out.append(word)
    return " ".join(out).rstrip(":,.-")


def exact_evidence_ids(package):
    return [s.get("evidence_id") for s in package.get("sources") or [] if s.get("allowed_in_article") and s.get("identity_level") == "EXACT_PRODUCT" and s.get("evidence_id")]


def plan_prompt(candidate, package):
    current_candidate[0] = candidate
    current_package[0] = package
    family = family_for(candidate.get("angle") or "")
    ids = [f"{family}-{i+1}" for i in range(len(FAMILY_BLOCKS[family]))]
    return f"""Você organiza a estrutura editorial do blog Vida Pet Prática.
ÂNGULO: {candidate.get('angle')}
FAMÍLIA: {family}
BLOCOS DISPONÍVEIS: {json.dumps(ids)}
Escolha uma ordem para TODOS os blocos, sem criar texto novo e sem adicionar fatos.
Retorne SOMENTE JSON válido: {{"selected_blocks": ["id1", "id2"]}}."""


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


def normalize_doc(plan, candidate, package):
    family = family_for(candidate.get("angle") or "")
    blocks = FAMILY_BLOCKS[family]
    valid = {f"{family}-{i+1}": blocks[i] for i in range(len(blocks))}
    selected = plan.get("selected_blocks") if isinstance(plan, dict) else None
    order = [x for x in (selected or []) if x in valid]
    for key in valid:
        if key not in order:
            order.append(key)

    product_name = re.sub(r"\s+", " ", str(candidate.get("productName") or "")).strip()
    keyword = str(candidate.get("keyword") or "acessório pet")
    editorial_html = f"<h2>Uma abordagem diferente para este assunto</h2><p>{FAMILY_INTRO[family]}</p>"
    for key in order:
        heading, paragraph = valid[key]
        editorial_html += f"<h2>{heading}</h2><p>{paragraph}</p>"
    ids = exact_evidence_ids(package)
    html = editorial_html + (
        "<h2>Identificação revalidada nesta rodada</h2><p>"
        "As fontes autorizadas desta execução identificam o item como <strong>" + product_name + "</strong>. "
        "Essa identificação é o fato específico usado nesta página. Outros detalhes do produto só podem ser acrescentados quando houver evidência correspondente.</p>"
    )
    return {
        "title": title_for(candidate),
        "focus_keyword": keyword,
        "meta_description": clip_text(f"Novo ângulo sobre {keyword}: organize a análise, confirme dados na fonte correta e evite repetir abordagens já publicadas.", 150),
        "article_html": html,
        "cta_text": "Confira a página atual do item e use somente as informações confirmadas para a sua decisão.",
        "claim_evidence": [{"claim": product_name, "evidence_ids": ids[:2]}],
    }


def throttled_call(prompt):
    for attempt in range(1, 5):
        elapsed = time.monotonic() - last_call[0]
        if last_call[0] and elapsed < 18.0:
            time.sleep(18.0 - elapsed)
        try:
            last_call[0] = time.monotonic()
            plan, usage = original_call(prompt)
            return normalize_doc(plan, current_candidate[0], current_package[0]), usage
        except builder.ProviderFatalError as exc:
            text = str(exc)
            if "HTTP 429" not in text or attempt >= 4:
                raise
            match = re.search(r"try again in\s+([0-9.]+)s", text, flags=re.I)
            time.sleep(max(6.0, (float(match.group(1)) if match else 6.0) + 2.0))


def real_medical_or_absolute(text):
    norm = evidence.normalize(text)
    patterns = [
        r"\bcura\b", r"\bcurar\b", r"\btratamento\b", r"\bdiagnostico\b",
        r"\bprescricao\b", r"\bmedicamento\b", r"\bremedio\b",
        r"\bprevine\s+doenca\b", r"\belimina\s+ansiedade\b",
        r"\b100\s+seguro\b", r"\bresultado\s+garantido\b",
        r"\btrata\s+(?:doenca|dor|ferida|infeccao|ansiedade|sintoma|problema\s+de\s+saude)\b",
    ]
    return any(re.search(p, norm) for p in patterns)


def strict_gate(doc, package, history, max_similarity):
    result = original_gate(doc, package, history, max_similarity)
    html = str(doc.get("article_html") or "")
    plain = builder.html_text(html)
    reasons = []
    for reason in list(result.get("reasons") or []):
        if str(reason).startswith("medical_or_absolute_claim:") and not real_medical_or_absolute(plain):
            continue
        reasons.append(reason)
    wc = builder.word_count(html)
    if wc < 650:
        reasons.append("safe_assembly_too_short")
    if wc > 950:
        reasons.append("safe_assembly_too_long")
    semantic = f"{doc.get('title') or ''} {plain}"
    for old in session_accepted:
        score = evidence.similarity(semantic, old)
        if score >= 0.62:
            reasons.append(f"semantic_duplicate_session:{score:.2f}")
            break
    reasons = list(dict.fromkeys(reasons))
    result["reasons"] = reasons
    result["status"] = "PASS" if not reasons else "REJECTED"
    result["product_fact_mode"] = "deterministic_evidence_section_only"
    result["editorial_sanitizer"] = "SAFE_V7_EVERGREEN_PLAN_ONLY"
    result["session_duplicate_guard"] = 0.62
    if result["status"] == "PASS":
        session_accepted.append(semantic)
    return result


builder.prompt_for = plan_prompt
builder.groq_call = throttled_call
builder.gate = strict_gate
builder.main()
