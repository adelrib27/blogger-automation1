# V31 — Validação do agendador Radar Tech BR

Código de continuidade `V31-RADAR-20261127-405`.

- O [evento schedule original](https://github.com/adelrib27/blogger-automation1/actions/runs/45983768245) selecionou o Radar com `DUE` e produziu o output `site`, mas pulou `pilot-fallback-draft`.
- O [PR #187](https://github.com/adelrib27/blogger-automation1/pull/187) ajustou a avaliação de status em `pilot-fallback-draft`. A condição exige que a execução não tenha sido cancelada, que `choose-pilot-fallback` tenha concluído com sucesso e que exista um site selecionado.
- Em 27/11/2026 às 11h07 (Brasília), a [execução manual 46013016909](https://github.com/adelrib27/blogger-automation1/actions/runs/46013016909) selecionou o Radar, concluiu a verificação independente e registrou `DRAFT_VERIFIED` para o WordPress #405. O recibo está no [log de entrega](https://github.com/adelrib27/blogger-automation1/actions/runs/46013016909/job/140554642268). A etapa LIVE foi pulada.
- A validação automática segue pendente. O workflow está ativo e a consulta em 27/11 ainda não mostrou um evento `schedule` depois da integração do PR #187.

## Evento schedule após o PR #187

A [execução automática 46026800956](https://github.com/adelrib27/blogger-automation1/actions/runs/46026800956), iniciada em 27/11/2026 às 12h39 (Brasília), comprovou o caminho corrigido até o escritor:

- `choose-one` consultou o D1 e registrou `wordpress_radartechbr: DUE`;
- `draft / authenticated-history` e `draft / independent-verifier` concluíram com sucesso;
- o resultado editorial foi `NO_NEW_OFFER`, com motivo `no_new_offer_with_trusted_source`;
- havia um candidato com fonte, recusado por `article_prose_reused`;
- `VERIFIED_DRAFT` permaneceu vazio, `draft / deliver-draft` foi pulado e não houve `DRAFT_VERIFIED`;
- `release`/LIVE permaneceu pulado.

A correção do disparo automático está comprovada, mas a validação ponta a ponta ainda não está concluída porque o guard de deduplicação rejeitou o único candidato antes da escrita no WordPress.

## Retomada

Consultar o [histórico do agendador](https://github.com/adelrib27/blogger-automation1/actions/workflows/v31_autonomous_draft_scheduler.yml) filtrado pelo evento `schedule` após 27/11/2026 às 09h45 (Brasília). Nas próximas execuções em que o Radar estiver `DUE`, verificar se um candidato novo ultrapassa o guard de deduplicação. Para confirmar criação automática ponta a ponta, exigir `DRAFT_VERIFIED` com o ID do WordPress. O recibo #405 é da execução manual. Preservar deduplicação, cadência e LIVE desativado.
