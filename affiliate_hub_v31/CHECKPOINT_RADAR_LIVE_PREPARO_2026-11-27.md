# V31 — Preparação do LIVE do Radar

Código de continuidade `V31-RADAR-20261127-LIVE`.

- O [PR #190](https://github.com/adelrib27/blogger-automation1/pull/190) entrou na main com o perfil de oferta de substituição. [CI SAFE](https://github.com/adelrib27/blogger-automation1/actions/runs/46028421396) aprovado. O aceite de entrega automática continua condicionado ao recibo `DRAFT_VERIFIED` e ao GET do WordPress.
- O [ambiente v31-autonomous-live](https://github.com/adelrib27/blogger-automation1/settings/environments/28775494561/edit) foi criado e limitado à branch main. A flag geral de LIVE foi conferida em false. O ambiente dedicado ainda não tem credenciais de catálogo R2, D1 e WordPress do Radar. As credenciais de R2/D1 atualmente estão restritas ao ambiente DRAFT.
- A migração `c81_live_ledger.sql` foi aplicada ao D1 oficial após o pedido de ativação do proprietário. A leitura confirmou a tabela e o índice de tentativas. Nenhum registro de entrega foi criado por essa operação.

## Prévia

Conectar o cron dedicado do piloto ao liberador já existente, condicionado a autorização explícita por site, flag geral, agendamento na main e recibo do mesmo ciclo. Preservar o comportamento da cadência regular e manter o fallback de DRAFT. O Python continua exigindo política aprovada pelo hash, prova assinada, evidência fresca, deduplicação e readback.

A efetiva ativação do Radar depende de comprovar entrega automática, provisionar as credenciais do ambiente dedicado e aprovar a configuração aplicável que inclui o Radar. O estado executável da política e a flag geral permanecem desativados nesta etapa.
