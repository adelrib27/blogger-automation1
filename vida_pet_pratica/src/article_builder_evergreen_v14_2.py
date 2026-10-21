from pathlib import Path

# V14.2 preserva o V14/V14.1 para auditoria. A única mudança editorial é
# substituir os três parágrafos globais repetidos por texto local específico
# de cada família/seção. O provedor continua limitado a escolher A/B/C e
# nenhum threshold/gate é reduzido.
source_path = Path(__file__).with_name("article_builder_evergreen_v14.py")
source = source_path.read_text(encoding="utf-8")

old_namespace = 'ns["safety_check_editorial"](html)'
new_namespace = 'ns["ns"]["safety_check_editorial"](html)'
if source.count(old_namespace) != 1:
    raise RuntimeError("SAFE V14.2: namespace hotfix target mismatch")
source = source.replace(old_namespace, new_namespace, 1)

start_marker = "\ndef render_section(heading, questions, variant):"
end_marker = "\ndef fix_meta(doc, candidate):"
start = source.find(start_marker)
end = source.find(end_marker, start + 1)
if start < 0 or end < 0 or end <= start:
    raise RuntimeError("SAFE V14.2: render patch markers not found")

replacement = r'''

FAMILY_SECTION_COPY = {
    "comparison": [
        ("Antes de comparar ofertas, delimite a situação em que a escolha será usada. Isso evita que detalhes chamativos ocupem o lugar do critério que realmente orienta a decisão.", "Ao terminar esta etapa, deixe explícito o que pertence ao contexto e o que ainda depende da página atual. Uma dúvida sem resposta deve continuar registrada como pendência."),
        ("Uma comparação consistente precisa observar as alternativas pela mesma pergunta. Quando cada página destaca aspectos diferentes, organize primeiro uma base comum de leitura.", "Se duas opções não permitem a mesma verificação, não force equivalência. Registre a diferença de informação e prossiga apenas com critérios que possam ser aplicados de modo coerente."),
        ("A oferta atual serve para confirmar aquilo que é específico da opção analisada. Use a consulta para localizar a informação necessária, sem preencher ausências com inferências.", "Depois da consulta, separe os pontos confirmados daqueles que continuam abertos. Essa divisão torna a próxima revisão mais simples e mantém a origem de cada informação visível."),
        ("Preferências da rotina ajudam a definir prioridades, mas não transformam a descrição comercial em resposta automática. Mantenha cada tipo de informação em seu papel.", "Ao revisar as anotações, verifique se opiniões, necessidades do ambiente e dados da oferta não foram misturados. O que não tiver fonte adequada permanece fora das conclusões."),
        ("Para comparar alternativas, escolha critérios que façam sentido para todas elas. Assim, diferenças de apresentação não parecem mais importantes apenas porque receberam mais destaque no anúncio.", "Quando uma diferença depender de informação ausente, marque-a para nova checagem. A comparação continua útil mesmo sem uma resposta fechada para todos os pontos."),
        ("Ofertas podem mudar, por isso informações comerciais antigas funcionam como histórico e não como confirmação atual. Identifique quais pontos realmente precisam ser revistos perto da escolha.", "Feche esta parte anotando onde a nova conferência deverá ocorrer. Isso evita reutilizar uma observação antiga como se ela ainda descrevesse o estado atual da oferta."),
        ("O fechamento da comparação deve mostrar tanto o que foi confirmado quanto o que ficou sem resposta. Pendências claras são melhores do que conclusões construídas para preencher lacunas.", "Revise os critérios restantes e mantenha somente os que ajudam a decisão. Se uma resposta depender de outra fonte, registre essa necessidade sem antecipar o resultado."),
    ],
    "placement": [
        ("Comece pelo espaço realmente disponível e pelas tarefas que já acontecem nele. O planejamento do ambiente vem antes de qualquer conclusão sobre onde o acessório poderia ficar.", "Anote as limitações encontradas no próprio ambiente e mantenha separadas as questões que dependem da oferta. Essa base ajuda a comparar locais sem criar uma regra universal."),
        ("Áreas de uso e de passagem têm funções diferentes na rotina da casa. Observe essa diferença antes de escolher um ponto apenas porque ele parece livre em um momento isolado.", "Ao final, preserve mais de uma alternativa quando o contexto ainda não estiver claro. Uma posição só deve ser descartada por um critério identificado, não por suposição."),
        ("A organização ao redor também faz parte da escolha do local. Considere como o espaço é acessado nas tarefas comuns, sem atribuir ao produto capacidades que não foram verificadas.", "Registre quais acessos precisam continuar disponíveis e quais dúvidas pertencem ao item. Se a decisão depender de informação específica, deixe a posição em aberto até a consulta adequada."),
        ("Comparar mais de um ponto do ambiente ajuda a distinguir conveniência real de primeira impressão. Use os mesmos critérios para observar cada alternativa de local.", "Depois da comparação, anote por que cada opção continuou ou saiu do planejamento. Essa trilha permite rever a escolha se a rotina ou a organização da casa mudar."),
        ("Quando o posicionamento depender de instruções do item, volte à fonte correspondente. O ambiente pode sugerir alternativas, mas não substitui uma orientação específica que precise ser confirmada.", "Se a página atual não responder ao ponto necessário, preserve a pendência. Não use informações de outro produto apenas para completar o planejamento do local."),
        ("Restrições do ambiente devem aparecer de forma concreta no planejamento. Passagens, tarefas concorrentes e áreas já ocupadas ajudam a explicar por que um local merece ou não nova análise.", "Organize essas restrições antes de decidir. Quando uma limitação estiver ligada apenas ao contexto da casa, mantenha-a separada de qualquer informação específica da oferta."),
        ("O melhor local depende deste contexto e pode mudar com a rotina. Por isso, trate a decisão como uma escolha revisável, e não como uma regra aplicável a qualquer casa.", "Finalize indicando o que faria a escolha ser revista. Essa condição deixa o planejamento mais útil e evita transformar uma situação particular em recomendação geral."),
    ],
    "maintenance": [
        ("Antes de procurar procedimentos, defina qual dúvida de conservação realmente precisa ser resolvida. Isso limita a pesquisa e evita transformar hábitos domésticos em instruções do produto.", "Ao fechar esta etapa, separe o que pode ser organizado pela rotina do que depende de orientação específica. O segundo grupo só avança com fonte ligada ao item."),
        ("Instruções de conservação precisam vir de uma referência associada à opção analisada. Uma página parecida pode sugerir perguntas, mas não fornece automaticamente o procedimento correto.", "Se a orientação necessária não estiver disponível, registre a ausência. Manter a lacuna é mais seguro do que completar o texto com um procedimento encontrado em outra oferta."),
        ("Há diferença entre organizar a casa e seguir uma instrução do item. O texto pode tratar da primeira sem apresentar a escolha pessoal como orientação oficial.", "Revise cada anotação e identifique sua origem. Quando algo depender da página atual ou do fabricante, deixe essa dependência visível antes de prosseguir."),
        ("Evite criar etapas apenas para tornar a orientação mais completa. Se uma ação específica não foi confirmada, ela não deve aparecer como procedimento recomendado.", "Transforme a ausência em uma pergunta para a próxima consulta. Assim, a manutenção continua auditável sem inventar uma resposta para preencher o roteiro."),
        ("Fontes atuais podem divergir ou deixar pontos sem explicação. Nesses casos, registre a diferença em vez de escolher por conveniência a versão mais detalhada.", "Uma divergência relevante continua aberta até existir referência suficiente. O conteúdo deve refletir esse limite e manter fora qualquer instrução cuja origem esteja em conflito."),
        ("Algumas dúvidas só precisam ser revisitadas perto da decisão ou quando a oferta mudar. Organizar essa próxima conferência evita refazer toda a pesquisa sem necessidade.", "Anote qual fonte deverá ser consultada e qual pergunta ainda falta responder. Essa trilha torna a atualização futura mais objetiva e econômica."),
        ("A revisão final deve distinguir orientações confirmadas, escolhas de organização e pendências. Essa separação impede que partes diferentes da pesquisa acabem apresentadas como uma única regra.", "Mantenha fora do texto tudo o que ainda não tiver suporte adequado. O histórico pode lembrar a dúvida, mas não substitui a evidência necessária para respondê-la."),
    ],
    "checklist": [
        ("Um checklist útil começa pelo contexto da decisão, não pela ordem em que o anúncio apresenta informações. Defina primeiro onde e por que a opção está sendo considerada.", "Ao terminar, mantenha a pergunta principal visível. Ela ajuda a decidir quais itens realmente pertencem à lista e quais apenas aumentariam o volume de informação."),
        ("Liste somente pontos que possam levar a uma verificação concreta. Cada entrada deve indicar o que consultar, observar ou deixar pendente antes da escolha.", "Se um item da lista não puder ser verificado com a fonte disponível, marque-o como aberto. O checklist não precisa parecer completo à custa de informação incerta."),
        ("Contexto da rotina e informação da oferta respondem a perguntas diferentes. Separá-los deixa claro o que vem da necessidade do leitor e o que precisa de confirmação externa.", "Revise a lista para evitar que uma preferência apareça como fato do produto. Quando a origem de uma resposta não estiver clara, mantenha a questão como pendência."),
        ("Comparar opções não significa presumir que todas servem da mesma forma. Use critérios comuns e deixe a adequação em aberto quando a informação necessária não estiver documentada.", "Depois de comparar, registre somente diferenças sustentadas pela consulta. Uma conclusão que dependa de inferência deve voltar para a lista de pontos a confirmar."),
        ("Instruções disponíveis merecem uma etapa própria no checklist porque podem estar separadas da descrição principal da oferta. Procure a referência ligada à opção correta.", "Quando a orientação estiver ausente ou ambígua, não transfira conteúdo de outro item. Registre exatamente qual ponto precisa de uma fonte melhor."),
        ("Pendências organizadas tornam o checklist mais útil do que uma lista cheia de respostas frágeis. Agrupe as dúvidas pelo tipo de consulta que ainda será necessária.", "Retire perguntas que não influenciam a decisão e preserve as demais. A lista final deve mostrar com clareza o que já está resolvido e o que ainda exige verificação."),
        ("A revisão final serve para confirmar que o checklist continua ligado ao objetivo inicial. Releia cada resposta junto com a fonte ou observação que a sustenta.", "Finalize sem esconder lacunas. Se uma pendência continua relevante, ela deve permanecer visível para impedir que a próxima etapa trate ausência de informação como confirmação."),
    ],
    "routine": [
        ("Organize primeiro em que momento da rotina o acessório seria considerado. O foco aqui é entender a sequência de tarefas, e não prever como o animal irá reagir.", "Registre o momento escolhido e as limitações observadas no contexto. Qualquer detalhe específico do item continua dependente da fonte atual e deve permanecer separado."),
        ("O espaço usado durante a atividade pode ter outras funções ao longo do dia. Observe o que já acontece ali antes de planejar uma mudança de organização.", "Ao concluir, anote quais ajustes pertencem somente ao ambiente. Se alguma decisão depender de informação do item, mantenha essa pergunta para a consulta correspondente."),
        ("Planejar a rotina exige perguntas que possam ser revisitadas sem promessa de resultado. Concentre-se em sequência, disponibilidade do ambiente e informações que ainda precisam ser conferidas.", "Mantenha as anotações ligadas ao planejamento, não a previsões de comportamento. O que depender do produto deve apontar para a página atual antes de entrar na decisão."),
        ("Quando a rotina exigir uma orientação específica, consulte as instruções associadas à opção analisada. O nome comercial, sozinho, não explica como o item deve entrar no planejamento.", "Se a orientação não estiver disponível, preserve a dúvida. Essa ausência pode mudar a escolha do momento de uso e precisa continuar visível na revisão."),
        ("Ter uma alternativa de momento ou de organização evita transformar a primeira ideia em regra. Compare possibilidades com base no contexto real da casa.", "Depois de observar as alternativas, registre qual delas exige menos mudança e quais pontos ainda estão abertos. Não atribua ao produto a decisão que veio apenas do planejamento doméstico."),
        ("Anotações curtas ajudam a perceber o que já foi observado e o que ainda depende de consulta. Use o registro para separar fatos do contexto, preferências e perguntas sem resposta.", "Essa trilha também facilita comparar outra opção depois. Preserve a origem de cada anotação para não reconstruir a decisão com lembranças imprecisas."),
        ("Antes de decidir, releia o plano como uma sequência completa. Verifique se espaço, momento e fonte da informação continuam coerentes com o objetivo desta página.", "Feche mantendo visíveis as pendências relevantes. Uma questão sem resposta pode justificar nova consulta ou outra alternativa, mas não deve ser convertida em certeza."),
    ],
    "errors": [
        ("Começar pela linguagem do anúncio pode fazer a pesquisa repetir prioridades comerciais. Defina a pergunta editorial antes de observar como a oferta descreve o item.", "Ao terminar, verifique se o critério principal continua sendo seu ponto de referência. Expressões promocionais não devem substituir a pergunta que orienta a análise."),
        ("Misturar páginas semelhantes é um erro fácil quando nomes e imagens parecem próximos. Confirme a identidade antes de associar uma informação específica à opção analisada.", "Se a correspondência não estiver demonstrada, retire o detalhe da conclusão. A página semelhante pode permanecer apenas como pista para uma nova pesquisa."),
        ("Uma lacuna na fonte não precisa ser preenchida para o conteúdo parecer completo. Identificar claramente o que falta é parte da qualidade da pesquisa.", "Registre a pergunta que continua aberta e onde ela deverá ser verificada. Isso impede que uma inferência silenciosa se torne um fato repetido em rodadas futuras."),
        ("Preferências pessoais ajudam a organizar escolhas, mas não provam características da oferta. O erro aparece quando contexto e fato específico são apresentados como se fossem equivalentes.", "Releia as anotações e marque a origem de cada uma. Se algo veio apenas da preferência ou do ambiente, mantenha essa natureza explícita."),
        ("Comparações perdem sentido quando cada alternativa é julgada por um critério diferente. Volte ao objetivo comum antes de usar uma diferença como argumento de escolha.", "Se o mesmo critério não puder ser aplicado, registre a limitação. Não compense a falta de base comum escolhendo a oferta que simplesmente traz mais informação."),
        ("Histórico ajuda a lembrar o que já foi visto, mas não significa que a oferta permaneça igual. Trate registros antigos como referência para saber o que precisa ser conferido novamente.", "Antes de reutilizar uma observação, verifique se ela continua sustentada pela fonte atual. A memória orienta a revisão; ela não substitui uma confirmação necessária."),
        ("A revisão final deve procurar erros que ainda possam contaminar a decisão: identidade confusa, fonte inadequada, critério desigual ou lacuna preenchida por suposição.", "Corrija o que puder ser corrigido e preserve o restante como pendência. O objetivo é terminar com uma trilha confiável, não com uma resposta forçada para cada pergunta."),
    ],
    "organization": [
        ("Comece definindo qual problema de organização precisa ser resolvido na rotina. Isso ajuda a evitar que o planejamento cresça para questões que não influenciam a escolha.", "Anote o objetivo e as limitações do ambiente em linguagem simples. Esses pontos serão a referência para avaliar as próximas etapas sem depender da apresentação comercial."),
        ("Mapeie a área onde a opção entraria e observe o que já ocupa ou atravessa esse espaço. O contexto físico deve ser entendido antes de qualquer reorganização.", "Depois do mapeamento, mantenha abertas as alternativas que ainda fazem sentido. Uma limitação do ambiente deve ficar separada de qualquer característica específica não confirmada."),
        ("Uso e armazenamento podem acontecer em momentos diferentes da rotina. Pensar nos dois evita escolher apenas com base na situação em que o item está sendo utilizado.", "Registre o que muda entre usar e guardar. Quando uma decisão depender da oferta atual, transforme esse ponto em pergunta para a fonte correta."),
        ("Uma organização prática precisa conviver com tarefas já existentes na casa. Observe quais movimentos, acessos e arrumações precisam continuar possíveis no dia a dia.", "Ao revisar, diferencie uma dificuldade do ambiente de uma limitação do produto. Só a segunda exige informação específica da oferta antes de entrar no texto."),
        ("Compare formas de organizar o espaço sem assumir que uma única disposição servirá sempre. Mudanças na rotina podem tornar outra alternativa mais adequada ao mesmo contexto.", "Anote por que cada arranjo foi considerado. Esse registro facilita adaptar o planejamento depois sem transformar uma solução temporária em regra fixa."),
        ("Quando a organização depender de instrução do item, volte à página atual antes de fechar o plano. O ambiente mostra necessidades, mas não confirma orientações específicas.", "Se faltar a informação necessária, mantenha mais de uma possibilidade e registre a consulta pendente. Não use uma oferta parecida para eliminar essa incerteza."),
        ("Finalize o planejamento revendo objetivo, espaço, rotina e pendências em conjunto. A organização deve continuar compreensível mesmo para quem não acompanhou todas as etapas anteriores.", "Mantenha apenas decisões sustentadas pelo contexto ou por fonte apropriada. O restante pode ficar documentado para uma atualização futura, sem virar conclusão antecipada."),
    ],
}


def render_section(family, section_index, heading, questions, variant):
    pair = FAMILY_SECTION_COPY.get(family, [])[section_index]
    lead, close = pair
    q = list(questions)
    key = str(variant).strip().upper()
    if key == "B":
        q = q[1:] + q[:1]
    elif key == "C":
        q = q[-1:] + q[:-1]
    elif key != "A":
        raise RuntimeError("SAFE V14.2: invalid_variant")
    question_html = "<ul>" + "".join(f"<li>{escape(text.rstrip(' ?.!;:') + '?')}</li>" for text in q) + "</ul>"
    return (
        f"<h2>{escape(heading)}</h2>"
        f"<p>{escape(lead)}</p>"
        f"{question_html}"
        f"<p>{escape(close)}</p>"
    )


def render_article(candidate, variants):
    family = family_for(candidate)
    blueprints = FAMILY_BLUEPRINTS[family]
    copy_rows = FAMILY_SECTION_COPY.get(family) or []
    if len(blueprints) != 7 or len(copy_rows) != 7:
        raise RuntimeError("SAFE V14.2: family_copy_count")
    html = "".join(
        render_section(family, idx, heading, questions, variants[idx])
        for idx, (heading, questions) in enumerate(blueprints)
    )
    if len(re.findall(r"<h2\b", html, flags=re.I)) != 7:
        raise RuntimeError("SAFE V14.2: h2_count")
    if "??" in html:
        raise RuntimeError("SAFE V14.2: double_question_mark")
    return html
'''

source = source[:start] + replacement + source[end:]
ns = {"__name__": "__main__", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)
