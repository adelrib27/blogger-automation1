# V31 R61 — STOP no Verify após R60 Apply

**Data:** 2026-11-14 (America/Recife). **Classificação:** evidência real do operador, causa raiz ainda indeterminada. Nenhum deploy/restart/rollback pelo ChatGPT.

## Evidência
Operador executou `GERENCIAR_WIZARD_R60.ps1 -Mode Verify`. Retorno:
- `status=STOP_R59_AUTHENTICATED_HEALTH_OR_CDP_FAILED`
- `mode=Verify`, `browser_sha256=""`, `offline_tests=0`, `runtime_import_proven=false`
- `runner_restart=false`, `local_disk_write=false`, `writes_to_blogger=false`, `gate_v2_executed=false`.

Último estado antes do Verify: `R60_PATCHED_DISK_RUNNER_NOT_RESTARTED`, disco do `browser_provision.py` com SHA R56 `2294e223ddde3ce16f847431da82bd380b68d036bca1d23866aff6e37907241f`, backup registrado em `logs/v31_r56_wizard_wait_backups/lab-20261114T180929Z-6d739f34`. Este hash **não foi novamente conferido** durante o Verify, pois o R60 abortou antes da leitura.

## Revisão do código exato
`tools/GERENCIAR_WIZARD_R60.ps1`:
- Linhas 61–68: `InvokeR59Check` chama o bootstrap `-CheckOnly` e perde distinção de causas (health, autenticação, CDP) ao devolver código genérico.
- Linha 92: `InvokeR59Check` ocorre **antes** da leitura do SHA do Wizard (linha 93) e dos testes de PID/processo/horário (95–109).
- Logo, **não é comprovado** bug do wizard R56 ou necessidade de rollback.
`start_blogger_automation_v31.ps1` R59: `-CheckOnly` verifica hashes, token em memória via env/DPAPI, contrato health e CDP; sua mensagem de PASS imprime um rótulo legado `version=0.8-v31r1-lab-r25`, apesar de o campo efetivamente verificado ser `0.9-v31-r52-candidate`.

## Diagnóstico isolado R61
Criado `DIAGNOSTICO_V31_R61_VERIFY_STOP_SOMENTE_LEITURA.ps1`, SHA-256 `3baf6144f868dd53bc342541aa70cb584ada9201ffd49f6fc52d46d08f53bd3b`, em anexo de conversa. Ele lê SHA, Task Scheduler, listeners/processos, alcançabilidade HTTP e CDP loopback, e executa **uma única vez** R59 `-CheckOnly` sem imprimir credenciais. Saída JSON codificada em classes de erro. Sem alterações no Runner, Chrome, Blogger ou task.

**Teste:** revisão estática sem comandos de modificação e endereços externos, delimitadores balanceados; **ainda não executado em PowerShell 5.1 Windows**. Usar apenas para diagnóstico, não executar reparação automática.

## Próximo passo técnico
Receber o JSON R61 do operador. Diferenciar Runner não escutando, tarefa falha, health (401/sem resposta), DPAPI ou CDP. Só então propor correção mínima; manter backup R56 e evitar executar novamente Apply, gate V2, R59 Apply, rollback, ou novo provisionamento. Sem modificação em `main`.
