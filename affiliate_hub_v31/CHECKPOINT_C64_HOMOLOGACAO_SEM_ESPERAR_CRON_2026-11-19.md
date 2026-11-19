# C64 — homologação acelerada sem esperar agendamento (19/11/2026)

**EM_ANDAMENTO — PRÉVIA antes dos testes.** Usuário pediu conclusão no menor prazo possível, sem aguardar 20/11. A data do cron não é bloqueio de testes manuais.

## Ponto de partida independente
- [C63](CHECKPOINT_C63_CRONS_RADAR_QUALITY_2026-11-19.md) PR #85 MERGED, suíte 383 V31 +24 Casa +21 Oficina +15 Radar PASS.
- Blogger Móveis: 3 LIVE +1 DRAFT (ID 3612281866616913629), pedido persistente `articles:null`, só rascunhos, anti-SKU; WordPress Casa: 43 LIVE +58 DRAFT (ID #303 preservado). Estas contagens são pré-teste C64.
- Não foi observado primeiro cron `schedule` depois C61; próxima janela 20/11. Validar operação com run em GitHub Actions agora não é o mesmo que comprovar evento `schedule`.
- O conector GitHub deste ambiente não expõe `workflow_dispatch`/POST Actions. Para executar sem esperar, usar workflow **temporário** no `main` com gatilho `push` limitado a arquivo-modo `affiliate_hub_v31/C64_TEST_MODE.txt`, controle fail-closed.
- As credenciais ficam exclusivamente nos `secrets` do environment GitHub; nunca no checkpoint nem nos logs.

## Plano de controle e idempotência
1. Criar workflow TEMP para executar **PREVIEW** do Blogger cadastrado e WordPress Casa (sem post), testes offline prévios e sem escrita Shopee/R2.
2. Se PREVIEW passar, alterar o arquivo modo para `blogger_draft_once` (uma execução DRAFT no blog piloto Blogger e WordPress somente PREVIEW), sob mesma concorrência `v31-editorial-catalog-single-writer`, sem POST LIVE.
3. Registrar run/job ID, resultado, verificar API Blogger/WordPress de forma independente. Se inconclusivo, **nunca repetir automaticamente**: read-after-write remoto antes.
4. Remover workflow TEMP primeiro e arquivo-modo depois, verificar limpeza e que os permanentes não mudaram; atualizar `CONTINUIDADE_ESTADO.json` e índice, guard PASS.
5. Distinguir homologação por run `push` de agendamento por `schedule`. O cron diário deve continuar com verificação futura, mas **não impede testes funcionais concluídos hoje**.

## Marcos
- **FEITO:** estado C64 em andamento persistido.
- **PENDENTE:** setup do TEMP, teste prévia, canário Blogger, evidências reais, limpeza e guard.

## C64 — execução imediata disparada
- **FEITO:** workflow TEMP `.github/workflows/v31_c64_TEMP_immediate_homologation.yml` commit `d5fbbb9`; arquivo-modo `affiliate_hub_v31/C64_TEST_MODE.txt=preview` commit `3e397ff` acionou [Action #44550783543](https://github.com/adelrib27/blogger-automation1/actions/runs/44550783543), `event=push`, job `135653613424`. Testes instalados no environment seguro, sem writes; **não reexecutar** enquanto o job estiver pendente ou em andamento.
- **DISTINÇÃO:** isso aciona agora o próprio código dos escritores Blogger C55 e WordPress C60, mas não é `event=schedule` dos workflows permanentes. Cron continua prova separada.

## C64 — prévias de escritores PASS e gargalo comercial concreto
- [Action #44550783543](https://github.com/adelrib27/blogger-automation1/actions/runs/44550783543) **SUCCESS**, 49 testes e duas execuções conectadas SEM post: Blogger Móveis `NO_VERIFIED_CAMPAIGN_PRODUCT_YET` (`draft_creation_calls=0`); WordPress Casa `NO_APPROVED_CACHED_PRODUCT_FOR_TOPIC` (`wordpress_posts_created=0`). As rotas/autenticação de leitura e R2 foram acessadas, mas nenhum novo produto verificado elegível entre os candidatos para a seleção.
- A hipótese de que bastava aguardar o cron é **refutada**: o escritor tem gate comercial e precisa de um produto aprovado com foto/link convertido para a campanha exata. No modo sem produto, não deve escrever, e esse comportamento foi confirmado.
- **DIAGNÓSTICO DA FILA DISPARADO:** workflow TEMP C64 foi ampliado com modos explícitos `queue_preview` e `queue_execute` (conversão oficial limitada a até 3, nunca artigos). O arquivo-modo mudou para `queue_preview` no commit `e89169d`; [Action #44551256082](https://github.com/adelrib27/blogger-automation1/actions/runs/44551256082) está em execução. **Não converter ou criar rascunho sem antes verificar resultado desta prévia**.
