# V31 — Validação do agendador Radar Tech BR

Código histórico `V31-RADAR-20261127-405`.

- O [evento schedule original](https://github.com/adelrib27/blogger-automation1/actions/runs/45983768245) selecionou o Radar com `DUE` e produziu o output `site`, mas pulou `pilot-fallback-draft`.
- O [PR #187](https://github.com/adelrib27/blogger-automation1/pull/187) ajustou a avaliação de status em `pilot-fallback-draft`. A condição exige que a execução não tenha sido cancelada, que `choose-pilot-fallback` tenha concluído com sucesso e que exista um site selecionado.
- Em 27/11/2026 às 11h07 (Brasília), a [execução manual 46013016909](https://github.com/adelrib27/blogger-automation1/actions/runs/46013016909) selecionou o Radar, concluiu a verificação independente e registrou `DRAFT_VERIFIED` para o WordPress #405. O recibo está no [log de entrega](https://github.com/adelrib27/blogger-automation1/actions/runs/46013016909/job/140554642268). A etapa LIVE foi pulada. Essa execução não conta como comprovação automática.

## Primeiro evento schedule após o PR #187

A [execução automática 46026800956](https://github.com/adelrib27/blogger-automation1/actions/runs/46026800956), iniciada em 27/11/2026 às 12h39 (Brasília), comprovou o caminho corrigido até o escritor:

- `choose-one` consultou o D1 e registrou `wordpress_radartechbr: DUE`;
- `draft / authenticated-history` e `draft / independent-verifier` concluíram com sucesso;
- o resultado editorial foi `NO_NEW_OFFER`, com motivo `no_new_offer_with_trusted_source`;
- havia um candidato com fonte, recusado por `article_prose_reused`;
- `VERIFIED_DRAFT` permaneceu vazio, `draft / deliver-draft` foi pulado e não houve `DRAFT_VERIFIED`;
- `release`/LIVE permaneceu pulado.

## Validação automática ponta a ponta concluída

Código de continuidade final: `V31-RADAR-SCHEDULE-46058071209`.

A [execução automática 46058071209](https://github.com/adelrib27/blogger-automation1/actions/runs/46058071209), iniciada em 27/11/2026 às 16h38 (Brasília), confirmou todo o fluxo:

- o [job de seleção pelo D1](https://github.com/adelrib27/blogger-automation1/actions/runs/46058071209/job/140705324473) registrou `pilot_fallback: wordpress_radartechbr: DUE`;
- o [verificador independente](https://github.com/adelrib27/blogger-automation1/actions/runs/46058071209/job/140705594321) concluiu com recibo `READY`;
- o [escritor e verificador final](https://github.com/adelrib27/blogger-automation1/actions/runs/46058071209/job/140706348518) registrou `DRAFT_VERIFIED` com `draft_id: "406"`;
- o hash verificado do HTML foi `68f5b60808d1b287fd909191f3cdedd9ddb6341469a96e44ebe8188dad062dc6`;
- o job `release`/LIVE permaneceu pulado.

O DRAFT automático #406 é evidência nova e independente da execução manual #46013016909 e do DRAFT #405. A validação solicitada está concluída; a checagem recorrente pode permanecer pausada.
