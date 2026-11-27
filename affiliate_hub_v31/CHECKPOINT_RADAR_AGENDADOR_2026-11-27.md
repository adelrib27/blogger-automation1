# V31 — Validação do agendador Radar Tech BR

Código de continuidade `V31-RADAR-20261127-405`.

- O [evento schedule original](https://github.com/adelrib27/blogger-automation1/actions/runs/45983768245) selecionou o Radar com `DUE` e produziu o output `site`, mas pulou `pilot-fallback-draft`.
- O [PR #187](https://github.com/adelrib27/blogger-automation1/pull/187) ajustou a avaliação de status em `pilot-fallback-draft`. A condição exige que a execução não tenha sido cancelada, que `choose-pilot-fallback` tenha concluído com sucesso e que exista um site selecionado.
- Em 27/11/2026 às 11h07 (Brasília), a [execução manual 46013016909](https://github.com/adelrib27/blogger-automation1/actions/runs/46013016909) selecionou o Radar, concluiu a verificação independente e registrou `DRAFT_VERIFIED` para o WordPress #405. O recibo está no [log de entrega](https://github.com/adelrib27/blogger-automation1/actions/runs/46013016909/job/140554642268). A etapa LIVE foi pulada.
- A validação automática segue pendente. O workflow está ativo e a consulta em 27/11 ainda não mostrou um evento `schedule` depois da integração do PR #187.

## Retomada

Consultar o [histórico do agendador](https://github.com/adelrib27/blogger-automation1/actions/workflows/v31_autonomous_draft_scheduler.yml) filtrado pelo evento `schedule` após 27/11/2026 às 09h45 (Brasília). Registrar o ID da execução e a decisão da pré-checagem no D1. Se o Radar estiver `DUE`, confirmar que a chamada ao escritor iniciou e registrar seu resultado editorial. Para confirmar criação automática ponta a ponta, exigir `DRAFT_VERIFIED` com o ID do WordPress. O recibo #405 é da execução manual. Preservar deduplicação, cadência e LIVE desativado.
