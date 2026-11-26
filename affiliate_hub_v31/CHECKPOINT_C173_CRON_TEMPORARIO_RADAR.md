# C173 — homologação do agendamento do Radar

Código de continuidade: `V31-C173-CRON-RADAR`.

A janela temporária do Radar roda nos minutos 02, 12, 22, 32, 42 e 52. A execução [45901514576](https://github.com/adelrib27/blogger-automation1/actions/runs/45901514576) pertence ao fluxo regular de Móveis para Cada Canto. O Radar tem o DRAFT #404 verificado em disparo manual na C172.

Depois do primeiro evento `schedule` com `IS_PILOT_SCHEDULE=true` e seleção do Radar, restaurar `42 * * * *` nos quatro pontos do workflow e registrar a execução e o desfecho editorial. Se houver DRAFT, validar o recibo e o status no WordPress. O piloto opera em DRAFT. O fluxo regular conserva sua agenda.
