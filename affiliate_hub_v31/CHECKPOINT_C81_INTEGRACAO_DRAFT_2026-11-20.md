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
