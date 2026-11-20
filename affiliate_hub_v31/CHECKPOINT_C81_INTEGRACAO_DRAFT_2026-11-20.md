# C81 — integração editorial Blogger e WordPress em DRAFT

## Prévia de execução

- Base `main` conferida em `40689157d0a13409ffd52c5bcb0ae4a8f581ecdc`. A diferença desde C80 é a atualização da fila do Radar Tech BR.
- O bucket oficial foi confirmado por GET. Consulta SELECT no D1 oficial retornou zero em leases, jobs, evidências e orçamentos.
- GitHub registrou sucesso nos canários C79 R2 e C80 D1. A execução mensal Pedal Leve falhou separadamente e não foi reexecutada.
- Branch de trabalho prevista `v31/c81-reviewed-draft`. A primeira entrega liga preflight C77, envelope C78/C79 e READY C76, com recuperação e isolamento por site/campanha.
- Canários reais em ordem: R2/D1 sintético com limpeza, depois um DRAFT real por plataforma com evidência independente, GET do CMS e comparação de HTML. LIVE exige aprovação individual.
- Próximo passo: integrar e testar o caminho preflight → R2 → D1 e verificar o ponto de entrada dos escritores para reconciliação de DRAFT.
