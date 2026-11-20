# C81 — integração editorial Blogger e WordPress em DRAFT

## Prévia de execução

- Base `main` conferida em `40689157d0a13409ffd52c5bcb0ae4a8f581ecdc`. A diferença desde C80 é a atualização da fila do Radar Tech BR.
- O bucket oficial foi confirmado por GET. Consulta SELECT no D1 oficial retornou zero em leases, jobs, evidências e orçamentos.
- GitHub registrou sucesso nos canários C79 R2 e C80 D1. A execução mensal Pedal Leve falhou separadamente e não foi reexecutada.
- Branch de trabalho prevista `v31/c81-reviewed-draft`. A primeira entrega liga preflight C77, envelope C78/C79 e READY C76, com recuperação e isolamento por site/campanha.
- Canários reais em ordem: R2/D1 sintético com limpeza, depois um DRAFT real por plataforma com evidência independente, GET do CMS e comparação de HTML. LIVE exige aprovação individual.
- Próximo passo: integrar e testar o caminho preflight → R2 → D1 e verificar o ponto de entrada dos escritores para reconciliação de DRAFT.

## Implementação e CI inicial

- [PR #105](https://github.com/adelrib27/blogger-automation1/pull/105) integra preflight, R2 com leitura exata e reserva D1; os testes de repetição e perda da confirmação de escrita passaram no [CI inicial](https://github.com/adelrib27/blogger-automation1/actions/runs/44797320792).
- [CI do publicador DRAFT](https://github.com/adelrib27/blogger-automation1/actions/runs/44797881343) passou, incluindo reconciliação Blogger após timeout e rejeição de HTML alterado no WordPress. Os dois CMS foram simulados nos testes. USED reserva a única tentativa de POST. Um USED sem rascunho encontrado exige reconciliação confirmada e não dispara outro POST.
- A [tentativa de canário na branch](https://github.com/adelrib27/blogger-automation1/actions/runs/44797868736) foi bloqueada pelas regras de implantação do ambiente protegido antes de iniciar o runner. O workflow foi preparado para executar uma vez na main após CI, conforme as regras atuais do ambiente.
- Auditoria dos schedules: a [fila](https://github.com/adelrib27/blogger-automation1/actions/runs/44600350780) tem um disparo observado que falhou. Os mais recentes [Blogger](https://github.com/adelrib27/blogger-automation1/actions/runs/44609598601) e [WordPress](https://github.com/adelrib27/blogger-automation1/actions/runs/44614079395) retornaram sucesso no dia 19. Não foi comprovada recorrência regular. Pedal Leve possui falha mensal separada; não houve reexecução.
- Próximo passo: comprovar R2/D1 com dados sintéticos no ambiente oficial após CI; verificar catálogo, foto e crédito Firecrawl em modo somente leitura. Para os rascunhos reais, continua pendente a revisão factual independente em infraestrutura segregada.

## Canário oficial R2/D1 e dependências de produção

- [PR #105](https://github.com/adelrib27/blogger-automation1/pull/105) incorporado à main em `608d58a48cce5b9b2d1315cec0fae3c3360e7d1c` após [CI verde do candidato](https://github.com/adelrib27/blogger-automation1/actions/runs/44798278562). Código de entrega exige invocação explícita e um job revisado, sem ligação aos agendamentos existentes.
- [Canário de armazenamento real](https://github.com/adelrib27/blogger-automation1/actions/runs/44798489685/job/136504159636): envelope sintético preservado byte a byte, replay idempotente, READY→USED uma vez, quatro contagens D1 zeradas para o tenant sintético e objeto R2 removido com readback ausente. Nenhum CMS acionado.
- [Auditoria do catálogo e Firecrawl](https://github.com/adelrib27/blogger-automation1/actions/runs/44798489685/job/136504159341): snapshot oficial restaurado e validado com 203.649 produtos, 9.279 elegíveis por moderação/taxonomia, 194.370 em revisão e 43 links cacheados. A seleção filtrada identificou 7 ofertas elegíveis da campanha Blogger e 3 da campanha WordPress e, em cada rota, alcançou pelo menos uma foto do SKU no CDN Shopee. Contagem de cache para a rota não equivale a uma nova conversão de link. A chave GitHub Firecrawl tinha 1.000 créditos via GET autenticado, sem pesquisas.
- Identidades dos CMS confirmadas em leitura pelos conectores: Blogger Móveis para Cada Canto e WordPress Casa e Decoração. Nenhum artigo real foi enviado pelo fluxo C81.
- O proprietário informou que existe processo de revisão separado. A localização e o contrato operacional dele ainda estão pendentes de identificação. C77 documenta o manifesto esperado e não inclui um emissor operacional. Aguardar a referência sem aceitar assinatura criada pelo gerador.

## Recuperação com TTL e processo de revisão separado

- [PR #106](https://github.com/adelrib27/blogger-automation1/pull/106) corrigiu o bloqueio do buffer por evidência expirada e a substituição de evidência ainda referenciada em READY. [CI](https://github.com/adelrib27/blogger-automation1/actions/runs/44799063590) e [canário D1 real de recuperação](https://github.com/adelrib27/blogger-automation1/actions/runs/44799389774/job/136507261911) passaram, com limpeza confirmada.
- O proprietário esclareceu que C69/C71/C77 já tinham a engenharia de revisão, mas o serviço independente ainda não havia sido implantado. Autorizou sua implementação e a aprovação humana nos casos em que for indispensável.
- [PR #107](https://github.com/adelrib27/blogger-automation1/pull/107), incorporado em `199c7813d1fa23ab06a9252de9d391e771978130` após [CI verde](https://github.com/adelrib27/blogger-automation1/actions/runs/44801519348), implementa candidato privado por SHA, aprovação verificada via histórico do GitHub, recibo HMAC no ambiente independente e verificação Ed25519 separada. A espera pela revisão não ocupa a trava dos agendamentos. O [guia operacional](C81_REVISAO_INDEPENDENTE.md) documenta o ambiente e a aprovação.
- [Canário real R2/D1 V2](https://github.com/adelrib27/blogger-automation1/actions/runs/44801751774/job/136515386126) confirmou leitura exata com somente chave pública, replay, READY→USED, recuperação do buffer e limpeza do tenant e objeto sintéticos. As chaves e conteúdos desse ensaio eram sintéticos.
- [Busca Firecrawl real](https://github.com/adelrib27/blogger-automation1/actions/runs/44801751774/job/136515385744) com a chave já verificada e teto de duas pesquisas. Retornou dois resultados por rota, sem aprová-los como evidência. A nova leitura do catálogo listou 203.649 produtos, 9.279 elegíveis, 194.370 em revisão, 46 links cacheados no total, 9 ofertas elegíveis na amostra Blogger e 4 na amostra WordPress. O recibo de pesquisa foi guardado no R2 privado, com links afiliados excluídos dos logs.
- A configuração administrativa do ambiente exclusivo GitHub exige revisor, duas chaves de assinatura e a respectiva chave pública. R2/D1 reutilizam o ambiente já protegido. Nenhum dos testes acima representa aprovação factual de um artigo real ou entrega no CMS.
