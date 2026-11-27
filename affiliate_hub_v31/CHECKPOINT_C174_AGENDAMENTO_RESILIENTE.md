# C174 — Agendamento resiliente do piloto DRAFT

Código de continuidade `V31-C174-AGENDAMENTO-RADAR`.

- Base: `32ab73d41876f4afbf50e84cadfe16a1b61a7ed8`. O C173 confirmou a configuração do cron na main, mas até a consulta nenhum evento schedule após o deploy chegou à lista de execuções. A auditoria de push verificou os três DRAFTs usados do Radar por SELECT/GET.
- O schedule regular [45901514576](https://github.com/adelrib27/blogger-automation1/actions/runs/45901514576) executou a seleção de Móveis para Cada Canto. O manual [45897356609](https://github.com/adelrib27/blogger-automation1/actions/runs/45897356609) entregou o rascunho Radar #404. A evidência delimita a falha observada ao disparo do piloto, sem atribuir uma causa interna ao GitHub.
- Plano: manter o cron de homologação, dar ao piloto também uma oportunidade após o ciclo regular, pré-checar a janela em D1 e reutilizar o writer DRAFT. O cron regular, o destino regular e as regras de publicação mantêm o contrato atual.
- Aceite: validar YAML, regras de isolamento, 50 cenários offline e regressões. Na main, registrar evento schedule com o piloto selecionado e o resultado real. Ao haver rascunho, confirmar ID, status e recibo. Retomar cadência horária depois da evidência automática.
