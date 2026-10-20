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

RISK_WORDS = {
    "saude", "estresse", "ansiedade", "cura", "curar", "tratamento", "diagnostico",
    "prescricao", "medicamento", "remedio", "previne", "prevenir", "garante", "garantir",
    "seguranca", "seguro", "reduz", "reduzir", "treinamento", "comando", "recompensa",
    "petisco", "racao", "vinagre", "sabao", "eficacia", "elimina", "protege", "melhora",
}
RISK_PREFIXES = ("terapeut", "lubrif", "absorv", "antiderrap", "durabil", "resistent", "lavavel")
RISK_PHRASES = ("bem estar", "estimulo mental", "peso suportado", "beneficio comprovado")
MEDICAL_CONTEXT_RE = re.compile(
    r"\b(?:tratar|tratamento|cura|curar|diagnostico|prescricao|terapeutic[oa]|medicamento|remedio)\b|"
    r"\btrata\s+(?:doenca|dor|ferida|infeccao|ansiedade|sintoma|problema de saude)\b",
    flags=re.I,
)

ANGLE_BLOCKS = {
    "criteria": [
        ("Comece pela pergunta que o artigo precisa responder", "Uma nova publicação sobre o mesmo produto deve partir de uma pergunta diferente da anterior. Em vez de repetir a descrição do anúncio, defina o que o leitor precisa comparar nesta etapa: espaço disponível, informação presente na página, opções anunciadas ou pontos que ainda não estão claros. Essa pergunta orienta a pesquisa e ajuda a manter o conteúdo independente. Quando o objetivo está explícito, fica mais fácil perceber se um parágrafo realmente acrescenta algo ou apenas reformula o que já apareceu em outro artigo."),
        ("Transforme preferências em critérios observáveis", "Palavras amplas como prático, confortável ou funcional podem significar coisas diferentes conforme a rotina. Para comparar opções sem transformar opinião em fato, converta essas ideias em perguntas observáveis. O anúncio informa dimensões? Existem instruções claras? Há variações identificadas? A página distingue versões do mesmo item? O conteúdo pode organizar essas verificações sem afirmar que uma opção é superior. Assim, o leitor recebe um método de comparação e a automação evita preencher lacunas com suposições."),
        ("Dê peso diferente para cada tipo de informação", "Nem todo trecho de uma página comercial tem o mesmo valor editorial. Nome do item, identificação, instruções e especificações claramente associadas ao produto têm função diferente de slogans e frases promocionais. Ao montar os critérios, separe o que pode ser conferido do que apenas apresenta a proposta de venda. Uma expressão chamativa pode sugerir um ponto para investigar, mas não deve virar conclusão. Essa hierarquia deixa o artigo útil sem depender de uma lista extensa de características."),
        ("Compare ausência de dados também", "A falta de uma informação pode ser tão relevante quanto a presença dela. Se uma característica importante para a decisão não aparece na fonte correta, registre esse ponto como pendente. Não complete o espaço usando um produto parecido nem uma descrição de outra versão. Em uma comparação editorial, a ausência ajuda a definir o que o leitor ainda precisa conferir. Isso também permite que duas publicações sobre o mesmo item tenham objetivos diferentes sem repetir o mesmo conjunto de afirmações."),
        ("Separe critério principal de detalhes secundários", "Escolha poucos pontos centrais para conduzir a análise e trate os demais como verificações complementares. Essa organização evita um artigo que tenta falar de tudo ao mesmo tempo e acaba parecido com textos anteriores. Um conteúdo pode focar identificação e dimensões; outro, variações e instruções; outro, organização do espaço. O produto continua sendo o mesmo, mas a intenção editorial muda de forma clara. O histórico interno deve registrar essa intenção para impedir que o próximo texto volte ao mesmo eixo."),
        ("Use fontes adicionais sem misturar identidades", "Uma segunda página pode ajudar a confirmar o item ou mostrar como determinada informação é apresentada, mas ela só deve autorizar uma especificação quando a correspondência do produto estiver demonstrada. Se a identidade não estiver clara, mantenha a fonte como contexto. O objetivo dos critérios não é acumular links, e sim saber por que cada fonte está sendo consultada. Essa disciplina também facilita a revisão posterior, porque cada afirmação específica continua ligada a uma evidência rastreável."),
        ("Feche a comparação com uma lista de pendências", "Antes de concluir, revise quais perguntas receberam resposta e quais continuam abertas. Uma boa lista de pendências evita que o texto force uma conclusão onde a evidência não chegou. Ela também ajuda na atualização futura: se o anúncio ganhar uma informação nova, o sistema sabe exatamente qual ponto merece nova checagem. Esse fechamento transforma o artigo em um guia de decisão, não em uma repetição da ficha comercial, e mantém espaço para novos ângulos editoriais."),
    ],
    "placement": [
        ("Observe primeiro o espaço disponível", "Antes de pensar no ponto exato onde um acessório pode ficar, mapeie o ambiente. Considere áreas de passagem, móveis próximos, portas, cantos e superfícies já ocupadas. O objetivo não é determinar uma posição universal, mas criar perguntas que ajudem a conferir se o item combina com aquele espaço. Se dimensões forem importantes, elas só entram na análise quando estiverem confirmadas na fonte do produto. Sem essa informação, o artigo pode orientar a medição do local sem inventar o tamanho do acessório."),
        ("Separe circulação de área de uso", "Um ambiente costuma ter zonas com funções diferentes. Há locais usados para circulação, outros para guardar objetos e outros reservados às atividades do pet. Ao avaliar posicionamento, diferencie essas funções antes de escolher um ponto. Essa leitura do espaço é mais útil do que afirmar que existe um local ideal para todos. O texto pode sugerir que o leitor observe a própria rotina e compare alternativas, mantendo qualquer detalhe específico do produto condicionado ao que estiver confirmado no anúncio."),
        ("Pense no acesso para manutenção do ambiente", "O posicionamento também pode ser analisado pela facilidade de acessar a área ao redor do item. Pergunte se o local permite mover objetos próximos, verificar o piso e reorganizar o espaço quando necessário. Não é preciso criar uma rotina fixa nem recomendar um método específico. Basta tratar o acesso como um critério de planejamento. Essa abordagem mantém o foco no ambiente e produz um artigo diferente de outro dedicado a características do produto ou comparação de modelos."),
        ("Teste o plano no papel antes de mudar o espaço", "Uma forma simples de planejar é desenhar ou anotar onde ficam os principais elementos do ambiente e marcar duas ou três posições possíveis. Compare cada opção com as limitações que você já identificou. Essa etapa não depende de promessas sobre o produto e pode ser feita antes da compra. Quando as medidas do item estiverem confirmadas, elas podem ser acrescentadas ao planejamento. Se não estiverem, deixe a medida como pendência e evite decidir com base apenas em fotografias."),
        ("Considere mudanças na rotina da casa", "Um ponto que parece adequado hoje pode deixar de fazer sentido depois de uma mudança de móveis ou de organização. Por isso, trate posicionamento como uma decisão revisável. O artigo pode orientar o leitor a observar quais áreas permanecem estáveis e quais mudam com frequência. Essa perspectiva é especialmente útil em espaços pequenos, nos quais cada objeto disputa área disponível. Nenhuma dessas observações exige atribuir uma característica ao produto; elas servem para estruturar a decisão do ambiente."),
        ("Confronte o plano com as informações confirmadas", "Depois de escolher posições possíveis, volte à página do item e confira quais dados realmente ajudam a validar o plano. Dimensões, forma de instalação ou instruções só devem ser usadas quando estiverem associadas ao produto correto. Se uma informação necessária não estiver disponível, mantenha mais de uma alternativa de posição em aberto. O objetivo é evitar que uma hipótese do ambiente seja apresentada como certeza e preservar a distinção entre planejamento editorial e especificação comercial."),
        ("Registre por que uma posição foi considerada", "Ao finalizar, anote os critérios que levaram cada local a ser considerado: espaço, circulação, acesso e informações confirmadas do anúncio. Esse registro permite revisar a decisão sem depender da memória e cria um histórico editorial diferente de um artigo de comparação. Em uma futura publicação sobre o mesmo produto, o sistema poderá escolher outro assunto sem repetir essa estrutura. O valor do texto está no processo de planejamento, não em declarar um único lugar como resposta definitiva."),
    ],
    "checklist": [
        ("Monte a lista antes de olhar detalhes do anúncio", "Um checklist funciona melhor quando nasce da rotina e não da descrição comercial. Comece anotando o que precisa ser conferido antes de um passeio, deslocamento ou outra atividade relacionada ao acessório. Depois, use o anúncio apenas para responder às perguntas que realmente dependem do produto. Essa ordem evita que a publicidade defina sozinha os critérios do artigo. Também cria uma estrutura editorial distinta de textos que começam enumerando características e depois tentam justificar cada uma."),
        ("Separe itens confirmados de itens ainda pendentes", "Divida a lista em duas partes: informações já verificadas e pontos que precisam de nova consulta. Essa separação deixa claro onde existe evidência e onde existe apenas uma pergunta. Se o anúncio não informar uma medida, componente ou instrução, não transfira o dado de outro produto. O checklist continua útil mesmo com campos em aberto, porque mostra exatamente o que deve ser conferido antes da decisão. A transparência vale mais do que uma lista artificialmente completa."),
        ("Revise identificação e versão do item", "Antes de usar qualquer dado encontrado, confirme se a página consultada corresponde ao mesmo item, modelo ou variação. Produtos com nomes parecidos podem ter diferenças importantes e uma informação correta para uma versão pode estar errada para outra. Inclua essa confirmação no checklist como etapa própria. Esse cuidado é especialmente útil quando várias ofertas aparecem na pesquisa. A tarefa não é escolher a descrição mais detalhada, e sim manter cada informação ligada à identidade certa."),
        ("Crie uma etapa para conferir o ambiente", "Além dos dados do produto, reserve um espaço no checklist para o contexto em que ele será usado. Observe área disponível, forma de guardar o item e outros elementos que influenciam a organização da rotina. O conteúdo não precisa afirmar que o produto serve para aquele contexto; pode simplesmente mostrar quais perguntas precisam ser respondidas. Assim, o artigo permanece útil sem transformar uma observação doméstica em especificação ou garantia de adequação."),
        ("Inclua uma revisão das condições atuais", "Páginas comerciais mudam. Opções, descrições e condições podem ser atualizadas depois que o artigo foi escrito. Por isso, o checklist deve terminar com uma nova consulta à página atual do produto quando a decisão estiver próxima. O histórico do sistema pode guardar o que foi visto anteriormente, mas não deve tratar esse registro como prova de que tudo continua igual. Essa etapa mantém a automação preparada para conteúdos evergreen sem congelar informações variáveis."),
        ("Evite itens genéricos que não mudam a decisão", "Uma lista muito longa pode parecer completa e ainda assim ser pouco útil. Remova pontos que não ajudam a comparar, confirmar ou organizar a escolha. Cada item do checklist deve levar a uma ação clara: conferir uma informação, medir um espaço, identificar uma versão ou registrar uma pendência. Essa seleção produz um texto mais focado e reduz a chance de repetir blocos de outros artigos. O mesmo produto pode então sustentar novas publicações com listas realmente diferentes."),
        ("Guarde o checklist como parte do histórico editorial", "Depois da publicação, registre quais etapas foram usadas e qual intenção de busca orientou o conteúdo. Na próxima reutilização do produto, o sistema consulta esse histórico e evita montar a mesma sequência com palavras diferentes. Se outro ângulo for escolhido, ele deve partir de uma nova pergunta e de uma estrutura própria. Esse registro transforma o checklist em memória editorial e ajuda a manter a produção contínua sem acumular páginas quase iguais."),
    ],
    "maintenance": [
        ("Comece pelas instruções disponíveis", "Quando o assunto envolve conservação ou manutenção, a fonte correta vem antes de qualquer procedimento. Procure instruções associadas ao item exato e diferencie orientação do fabricante, descrição do vendedor e comentários de compradores. Se não houver instrução confirmada, trate o ponto como pendente. O artigo pode explicar como localizar e comparar essas informações sem inventar um método. Essa abordagem permite falar do tema de forma útil mesmo quando a documentação do produto é limitada."),
        ("Não transfira procedimentos entre produtos parecidos", "Dois acessórios podem ter aparência semelhante e ainda exigir cuidados diferentes. Por isso, uma orientação encontrada em outro anúncio não deve ser aplicada automaticamente ao item analisado. Use páginas semelhantes apenas para levantar perguntas que depois serão verificadas na fonte correta. O conteúdo editorial pode mostrar esse processo e destacar a importância da correspondência de identidade. Dessa forma, a automação não transforma uma dica genérica em instrução específica sem evidência."),
        ("Organize a consulta por tipo de informação", "Separe o que você procura em grupos: instruções disponíveis, materiais confirmados, peças removíveis quando documentadas e orientações de armazenamento quando existirem. Essa organização evita que o artigo misture fatos com inferências. Se um grupo ficar vazio, registre a ausência em vez de preenchê-lo. A manutenção editorialmente responsável não exige uma resposta para todas as perguntas; exige clareza sobre o que está confirmado e sobre o que ainda depende de consulta."),
        ("Revise a fonte sempre que o conteúdo for reutilizado", "Um artigo evergreen pode voltar a abordar o mesmo produto meses depois. Nessa situação, não basta copiar a evidência antiga. Consulte novamente a página atual e verifique se as instruções continuam presentes e associadas ao mesmo item. Se houver mudança, o novo texto deve refletir o estado atual. Essa rotina diferencia reaproveitamento de produto de reaproveitamento de conteúdo e mantém o histórico útil sem transformar registros antigos em especificações permanentes."),
        ("Trate divergências como sinal de nova verificação", "Se duas fontes ligadas ao item apresentarem orientações diferentes, não escolha automaticamente a mais detalhada. Registre a divergência e procure uma fonte com maior autoridade sobre o produto. Enquanto o conflito não estiver resolvido, o artigo pode informar que aquele ponto precisa de confirmação. Essa postura é mais segura do que combinar partes de instruções diferentes e cria valor editorial ao ensinar o leitor a reconhecer situações em que a informação ainda não está consolidada."),
        ("Separe rotina da casa de instrução do produto", "O modo como cada pessoa organiza a própria casa não deve ser apresentado como procedimento oficial do acessório. O artigo pode falar de planejamento, local de armazenamento e registro de informações, mas precisa distinguir essas escolhas domésticas das instruções específicas do item. Essa separação amplia as possibilidades de conteúdo sem aumentar o risco de afirmar algo que a evidência não sustenta. Também ajuda a criar novos ângulos para o mesmo produto."),
        ("Finalize com um registro de fontes consultadas", "Ao encerrar a pesquisa, guarde quais fontes foram usadas, quando foram consultadas e quais pontos cada uma sustentou. Esse registro facilita futuras atualizações e evita reconstruir toda a investigação do zero. Se o produto voltar ao rodízio, o Evidence Engine pode revalidar as mesmas referências e procurar mudanças. O novo artigo continua original porque usa outra intenção editorial, enquanto a base factual permanece controlada e rastreável."),
    ],
    "errors": [
        ("Erro: começar pelo título comercial", "Usar o título do anúncio como estrutura do artigo costuma puxar o texto para a mesma sequência de palavras e características. Em vez disso, comece pela pergunta editorial que precisa ser respondida. O nome do produto só entra na seção de identificação confirmada. Essa separação reduz a chance de transformar a publicação em uma versão ampliada da ficha comercial e ajuda a criar conteúdos diferentes sobre o mesmo item ao longo do tempo."),
        ("Erro: preencher toda lacuna com uma suposição", "Quando uma informação não aparece na fonte correta, a tentação é procurar um produto parecido e completar o texto. Esse atalho aumenta o risco de atribuir ao item algo que pertence a outra versão. Uma lacuna deve continuar sendo lacuna até existir evidência suficiente. O artigo pode ser útil justamente ao mostrar o que ainda precisa ser conferido. A ausência de dado não impede o conteúdo; ela define um limite para as afirmações."),
        ("Erro: confundir quantidade de fontes com qualidade", "Encontrar muitas páginas não resolve o problema de identidade. Dez ofertas semelhantes continuam sendo fontes fracas para uma especificação se nenhuma estiver claramente ligada ao item correto. Priorize correspondência, autoridade e clareza. Fontes adicionais podem servir como contexto ou apontar perguntas, mas apenas evidências autorizadas sustentam fatos do produto. Essa regra evita que a pesquisa pareça robusta apenas porque reuniu muitos resultados."),
        ("Erro: repetir a mesma estrutura em todo artigo", "Trocar o produto e manter os mesmos subtítulos cria páginas parecidas mesmo quando os itens são diferentes. No rodízio evergreen, o problema é ainda maior porque o produto pode ser exatamente o mesmo. Por isso, cada novo ângulo precisa de uma sequência própria de perguntas e etapas. O histórico deve guardar título, intenção, estrutura e impressão semântica para impedir que a automação apenas reorganize frases já publicadas."),
        ("Erro: transformar linguagem promocional em conclusão", "Palavras de divulgação podem indicar como o vendedor apresenta o item, mas não comprovam automaticamente desempenho, adequação ou resultado. Use esses termos apenas como pista para investigação. Se uma afirmação específica for importante, procure evidência ligada ao produto. Essa separação mantém o texto útil e evita que o artigo repita a publicidade como se fosse análise independente. Também abre espaço para conteúdos orientados a método de escolha, e não a promessa comercial."),
        ("Erro: esquecer que informações mudam", "Um anúncio consultado hoje pode ser alterado no futuro. Guardar evidências é importante, mas reutilizar o produto exige nova verificação dos pontos relevantes. O sistema deve saber quando a evidência foi checada e qual artigo a utilizou. Assim, uma publicação evergreen não herda automaticamente tudo de uma rodada anterior. A memória serve para evitar repetição e orientar pesquisa, não para dispensar a atualização das fontes."),
        ("Erro: concluir quando ainda existe conflito", "Se fontes autorizadas divergem, o conteúdo não deve escolher uma delas apenas para fechar o parágrafo. Registre o conflito e mantenha a questão aberta até existir informação melhor. Essa decisão pode até levar o sistema a abandonar o candidato e selecionar outro produto para aquela rodada. O objetivo da automação contínua não é publicar a qualquer custo, e sim manter a fila abastecida sem diminuir o padrão de evidência."),
    ],
    "routine": [
        ("Mapeie a rotina antes de pensar no produto", "Para criar um artigo de organização realmente novo, comece pelas etapas da rotina e não pela ficha do item. Anote quando o acessório entra no dia a dia, onde costuma ser guardado e quais outras tarefas acontecem no mesmo espaço. Essa visão ajuda a formular perguntas relevantes para a pesquisa. O produto aparece depois, apenas nos pontos em que uma informação confirmada pode ajudar. Assim, o conteúdo permanece centrado na organização e não repete uma análise de características."),
        ("Divida a rotina em momentos menores", "Uma rotina ampla pode ser separada em preparação, uso, armazenamento e revisão das informações. Cada momento gera perguntas próprias e permite escolher um foco editorial diferente. O texto não precisa prescrever horários nem procedimentos; basta mostrar como organizar a observação. Essa decomposição também ajuda a identificar onde faltam dados no anúncio. Em vez de preencher a lacuna, o sistema registra o que precisa ser conferido antes de transformar a observação em decisão."),
        ("Defina onde guardar registros e informações", "Além do objeto físico, a organização pode incluir as informações do produto. Guardar identificador, fonte consultada, data da checagem e instruções confirmadas facilita futuras revisões. Esse registro não precisa aparecer como uma tabela complexa para o leitor, mas deve existir na memória editorial. Quando o produto voltar ao rodízio, a automação sabe o que já foi abordado e pode escolher outra intenção sem perder o vínculo com as evidências anteriores."),
        ("Use o espaço disponível como variável da rotina", "O mesmo acessório pode ocupar posições diferentes conforme a casa. Em vez de sugerir uma solução única, o artigo pode orientar a observação do espaço e das limitações locais. Se uma dimensão for necessária para planejar, ela só deve ser utilizada quando estiver confirmada para o item. Essa forma de escrever mantém a utilidade do conteúdo mesmo sem uma especificação completa e diferencia a abordagem de um texto dedicado apenas à comparação de produtos."),
        ("Crie um ponto de revisão periódica", "A organização não precisa ser tratada como decisão permanente. Mudanças no ambiente, no anúncio ou nas necessidades da casa podem exigir nova consulta. Inclua na rotina um momento de rever as informações que realmente importam. A automação também deve fazer isso quando reutilizar o item: revalidar evidências antes de gerar o próximo conteúdo. Essa repetição da verificação é desejável; o que não deve se repetir é o texto ou a intenção editorial."),
        ("Separe hábitos pessoais de fatos do item", "Uma escolha de organização pode funcionar para uma casa e não fazer sentido em outra. Portanto, apresente hábitos como possibilidades de planejamento, não como características ou resultados do produto. Os fatos específicos permanecem na seção vinculada às evidências. Essa separação permite explorar rotinas, espaços e formas de registro sem atribuir ao item uma capacidade que não foi demonstrada. É uma forma de ampliar o catálogo editorial mantendo o Fact Gate intacto."),
        ("Use o histórico para escolher o próximo assunto", "No final da publicação, o sistema deve registrar quais partes da rotina foram exploradas. Se o produto voltar ao rodízio, ele consulta esse histórico antes de escolher o novo ângulo. Uma próxima página pode tratar de comparação, posicionamento, conservação ou erros de pesquisa, desde que a estrutura seja realmente diferente. O rodízio deixa de ser uma simples reciclagem e passa a funcionar como expansão planejada do conjunto de conteúdos."),
    ],
    "variation": [
        ("Defina o objetivo editorial da nova abordagem", "Quando um produto volta ao rodízio, variar o conteúdo não significa apenas trocar o título. O novo artigo precisa responder a uma pergunta que ainda não foi explorada. Comece registrando o foco anterior e escolha outro eixo, como organização do espaço, critérios de comparação ou formas de planejar a interação com o acessório. Essa decisão deve ser feita antes da geração do texto. O produto permanece como referência factual, mas a narrativa editorial nasce de uma intenção diferente."),
        ("Planeje alternativas sem prometer reação do animal", "Um conteúdo pode discutir maneiras de organizar diferentes opções de atividade sem prever como cada animal reagirá. Evite transformar preferência, interesse ou comportamento em resultado esperado. Em vez disso, mostre como o tutor pode registrar quais acessórios estão disponíveis, quando foram apresentados e quais informações do anúncio precisam ser conferidas. A utilidade está no planejamento e na observação, não em afirmar que determinado item produzirá uma resposta específica."),
        ("Alterne perguntas, não apenas produtos", "Mesmo com vários acessórios disponíveis, artigos podem ficar repetitivos se sempre perguntarem a mesma coisa. No rodízio editorial, alterne a pergunta principal: o que comparar, como organizar o espaço, quais dados estão ausentes, como revisar fontes ou como registrar versões. Essa variação de intenção cria páginas distintas e permite que um mesmo produto reapareça sem parecer uma cópia. O histórico semântico serve para confirmar se a diferença é real depois da geração."),
        ("Crie registros simples para evitar repetição", "Anote título, ângulo, subtítulos principais e uma impressão semântica de cada publicação. Antes de escrever novamente sobre o produto, compare o novo plano com esse conjunto. Se a proposta estiver próxima demais, descarte o ângulo e tente outro. Esse processo não depende de lembrar manualmente o que já foi publicado. A memória persistente transforma a variedade editorial em uma regra do sistema e não em uma expectativa subjetiva."),
        ("Use a fonte do produto apenas onde ela é necessária", "O artigo não precisa repetir todas as características confirmadas em toda nova abordagem. Se o foco é organização ou comparação, basta inserir os fatos específicos que realmente ajudam a identificar o item. O restante do texto pode ensinar um método de pesquisa e planejamento. Essa contenção reduz repetição entre páginas do mesmo produto e mantém a distinção entre conteúdo editorial e evidência comercial. Mais fatos não significam automaticamente um artigo melhor."),
        ("Revalide antes de reutilizar qualquer fato", "Mesmo que o produto já tenha sido usado em outra publicação, a nova rodada deve conferir novamente as evidências relevantes. O item pode continuar igual, mas a página comercial pode mudar. Revalidar impede que a memória editorial seja confundida com uma fonte atual. O sistema pode reaproveitar a identidade do produto e o histórico dos ângulos, mas cada nova afirmação específica precisa continuar ligada a uma evidência autorizada da rodada vigente."),
        ("Deixe ângulos esgotados em descanso", "Se todas as abordagens disponíveis para um produto estiverem muito próximas de conteúdos existentes, o sistema não precisa forçar uma nova página. Marque aquele item como temporariamente esgotado e passe para outro produto validado. Novos ângulos podem surgir no futuro, especialmente se houver mudanças de contexto ou novas informações. Essa decisão preserva a originalidade e garante que o rodízio contínuo não se transforme em produção repetitiva apenas para cumprir uma quantidade."),
    ],
    "compatibility": [
        ("Transforme compatibilidade em conjunto de perguntas", "Compatibilidade não deve ser tratada como uma palavra única nem presumida pelo título comercial. Divida o tema em perguntas: existem medidas confirmadas? Há instruções de ajuste? A página identifica variações? O anúncio informa para quais configurações o item foi projetado? Cada resposta precisa vir da fonte correta. Se uma informação não estiver disponível, mantenha a pergunta aberta. Essa estrutura cria um artigo dedicado ao processo de verificação, diferente de uma página que simplesmente descreve o acessório."),
        ("Meça o contexto antes de buscar uma resposta", "Quando o uso depende de tamanho ou espaço, comece levantando os dados do próprio contexto que o leitor consegue observar. Depois compare essas necessidades com informações confirmadas do item. O artigo não deve concluir que existe adequação se uma das partes estiver ausente. Essa ordem evita que fotografias ou nomes de produto sejam usados como substitutos de medidas. O objetivo é mostrar como chegar a uma decisão baseada em dados disponíveis, sem oferecer uma garantia universal."),
        ("Diferencie ajuste de finalidade anunciada", "Um vendedor pode indicar uma finalidade geral para o acessório, mas isso não responde automaticamente a todas as perguntas de ajuste. Trate finalidade e compatibilidade como tópicos separados. A primeira descreve como o item é apresentado; a segunda depende dos dados específicos necessários para o contexto do leitor. Essa distinção evita transformar linguagem comercial em conclusão e cria uma estrutura editorial própria para artigos sobre escolha e adequação."),
        ("Confira cada variação separadamente", "Quando uma página reúne tamanhos, versões ou configurações, associe cada informação à variação correta. Não use uma medida encontrada em uma opção como se valesse para todas. Se a associação não estiver clara, registre a pendência. Essa regra também se aplica a fontes externas: uma página só reforça o dado quando a identidade do mesmo modelo ou variação estiver demonstrada. O controle de variantes é parte do Evidence Engine e deve aparecer na lógica editorial."),
        ("Registre quais dados faltam para decidir", "Uma análise de compatibilidade pode terminar sem resposta definitiva e ainda ser útil. Liste os dados que faltam e indique onde deveriam ser conferidos. Esse registro evita uma conclusão forçada e orienta uma futura atualização do artigo. Se a página do produto ganhar uma tabela ou instrução nova, o sistema sabe qual questão revisitar. A memória editorial passa a guardar não só o que foi confirmado, mas também o que permaneceu pendente."),
        ("Não use experiência individual como especificação", "Relatos de compradores podem sugerir perguntas importantes, porém não substituem documentação ou informação vinculada ao produto. Uma pessoa pode descrever um uso específico que não representa todas as situações. Utilize esses relatos apenas para identificar o que merece nova conferência. Se o dado não aparecer em uma fonte apropriada, ele não entra como fato. Essa separação mantém o artigo orientado a verificação, não a generalização de experiências."),
        ("Finalize com uma decisão condicionada aos dados", "Ao concluir, organize o que foi confirmado e o que ainda depende de consulta. A decisão deve permanecer condicionada às informações realmente disponíveis para o item e para o contexto do leitor. Evite frases universais. Essa forma de fechamento preserva a utilidade do conteúdo e deixa claro que a automação não substitui a verificação atual do anúncio. Também cria uma base distinta para futuras publicações do mesmo produto com outro ângulo."),
    ],
}


def family_for(angle):
    text = evidence.normalize(angle)
    if "posicionar" in text or "onde" in text: return "placement"
    if "checklist" in text or "preparacao" in text or "deslocamento" in text: return "checklist"
    if "manutencao" in text or "limpeza" in text or "conservacao" in text: return "maintenance"
    if "erro" in text: return "errors"
    if "ajuste" in text or "compatibilidade" in text or "supervisao" in text: return "compatibility"
    if "variar" in text or "alternar" in text or "interacao" in text or "brincadeira" in text or "estimulo" in text: return "variation"
    if "organizar" in text or "organizacao" in text or "rotina" in text or "bagunca" in text: return "routine"
    return "criteria"


def natural_subject(keyword):
    key = evidence.normalize(keyword)
    mapping = {
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
    }
    return mapping.get(key, "Acessório pet")


def fit_title(text):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= 65:
        return text if len(text) >= 35 else text + " na rotina"
    words = text.split()
    out = []
    for word in words:
        if len(" ".join(out + [word])) > 65:
            break
        out.append(word)
    return " ".join(out).rstrip(":,.-")


def title_for(candidate):
    subject = natural_subject(candidate.get("keyword") or "")
    family = family_for(candidate.get("angle") or "")
    suffix = {
        "criteria": "critérios antes de escolher",
        "placement": "onde posicionar no ambiente",
        "checklist": "checklist antes de usar",
        "maintenance": "como planejar a conservação",
        "errors": "erros de comparação para evitar",
        "routine": "como organizar a rotina",
        "variation": "como criar uma abordagem diferente",
        "compatibility": "como conferir ajuste e compatibilidade",
    }[family]
    return fit_title(f"{subject}: {suffix}")


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


def prompt_for(candidate, package):
    current_candidate[0] = candidate
    current_package[0] = package
    return f"""Você é editor do blog Vida Pet Prática. Escreva apenas uma abertura editorial original de 100 a 140 palavras para o assunto abaixo.
PALAVRA-CHAVE: {candidate.get('keyword')}
NOVO ÂNGULO: {candidate.get('angle')}
O texto precisa mostrar claramente que esta abordagem é diferente de uma descrição de produto. Não descreva especificações do item, não cite preço, não faça afirmações de saúde, comportamento, treinamento, limpeza, alimentação ou segurança. Fale somente de como organizar a decisão, observação ou pesquisa conforme o novo ângulo.
Retorne SOMENTE JSON válido com title, focus_keyword, meta_description, article_html, cta_text, claim_evidence. claim_evidence deve ser []."""


def safe_intro(raw, family):
    plain = builder.html_text(raw)
    if not plain:
        return ""
    kept, total = [], 0
    for sentence in re.split(r"(?<=[.!?])\s+", plain):
        sentence = re.sub(r"\s+", " ", sentence).strip()
        if not sentence or has_risk(sentence):
            continue
        count = len(sentence.split())
        if total + count > 120:
            break
        kept.append(sentence)
        total += count
    text = " ".join(kept)
    if not text or has_risk(text):
        return ""
    heading = {
        "criteria": "Defina o critério antes de comparar",
        "placement": "Comece pelo ambiente, não pelo anúncio",
        "checklist": "Organize a verificação antes de decidir",
        "maintenance": "Pesquise as instruções antes de criar uma rotina",
        "errors": "Mude a pergunta para não repetir o conteúdo",
        "routine": "Observe a rotina antes de avaliar o acessório",
        "variation": "Um novo ângulo precisa de uma nova pergunta",
        "compatibility": "Compatibilidade começa com dados verificáveis",
    }[family]
    return f"<h2>{heading}</h2><p>{text}</p>"


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


def normalize_doc(doc, candidate, package):
    if not isinstance(doc, dict):
        doc = {}
    family = family_for(candidate.get("angle") or "")
    keyword = str(candidate.get("keyword") or "acessório pet")
    product_name = re.sub(r"\s+", " ", str(candidate.get("productName") or "")).strip()
    ids = exact_evidence_ids(package)
    html = safe_intro(doc.get("article_html") or "", family)
    html += (
        "<h2>Identificação confirmada nesta nova rodada</h2><p>"
        "A pesquisa atual voltou a localizar o item como <strong>" + product_name + "</strong>. "
        "Essa identificação foi revalidada pelas evidências autorizadas desta execução. "
        "Qualquer detalhe além da identificação deve permanecer ligado à fonte correspondente.</p>"
    )
    for heading, paragraph in ANGLE_BLOCKS[family]:
        html += f"<h2>{heading}</h2><p>{paragraph}</p>"
        if builder.word_count(html) >= 720:
            break
    return {
        "title": title_for(candidate),
        "focus_keyword": keyword,
        "meta_description": clip_text(f"Um novo ângulo para {keyword}: veja como organizar a análise, confirmar dados e evitar repetir abordagens já usadas.", 150),
        "article_html": html,
        "cta_text": "Confira novamente a página atual do item e use apenas as informações confirmadas para a sua decisão.",
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
            time.sleep(max(6.0, (float(match.group(1)) if match else 6.0) + 2.0))


def precise_medical_problem(article_plain):
    return bool(MEDICAL_CONTEXT_RE.search(evidence.normalize(article_plain)))


def strict_gate(doc, package, history, max_similarity):
    result = original_gate(doc, package, history, max_similarity)
    html = str(doc.get("article_html") or "")
    article_plain = builder.html_text(html)
    reasons = []
    for reason in list(result.get("reasons") or []):
        if reason == "medical_or_absolute_claim:trata " and not precise_medical_problem(article_plain):
            continue
        reasons.append(reason)
    before_verified = html.split("<h2>Identificação confirmada nesta nova rodada</h2>", 1)[0]
    if before_verified and has_risk(builder.html_text(before_verified)):
        reasons.append("editorial_sanitizer_residual_risk")
    wc = builder.word_count(html)
    if wc < 650:
        reasons.append("safe_assembly_too_short")
    if wc > 950:
        reasons.append("safe_assembly_too_long")
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
    result["editorial_sanitizer"] = "SAFE_V6_EVERGREEN_ANGLE_AWARE"
    result["session_duplicate_guard"] = 0.62
    if result["status"] == "PASS":
        session_accepted.append(semantic)
    return result


builder.prompt_for = prompt_for
builder.groq_call = throttled_call
builder.gate = strict_gate
builder.main()
