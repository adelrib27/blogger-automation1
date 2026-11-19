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

## C64 — fila de conversão: candidatos reais e execução controlada
- [Preview fila C37 #44551256082](https://github.com/adelrib27/blogger-automation1/actions/runs/44551256082) SUCCESS, 49 testes. Resultado REST/R2: `requests_active=1`, `requests_evaluated=1`, `conversion_candidates=3`, `ready_review_jobs=3`, `needs_curation=12`, `converted=0`, `r2_writes=0`, `publication_calls=0`.
- Com essa evidência, o status C64 no JSON foi definido como `remote_operation_in_progress=true` e `mutation_in_progress=true` no commit `31aa711` ANTES da mutação. O trigger único `C64_TEST_MODE.txt=queue_execute` commit `ef57003` iniciou [Action #44551595546](https://github.com/adelrib27/blogger-automation1/actions/runs/44551595546), job `135656491310`. Preservar R2 e não tentar conversão duplicada se falha ou resposta inconclusiva: obter primeiro logs/recibo e reconsultar cache.

## C64 — conversões oficiais concluídas
- [Ação de conversão #44551595546](https://github.com/adelrib27/blogger-automation1/actions/runs/44551595546) **SUCCESS**, job 135656491310: `conversion_candidates=3`, `shopee_mutation_attempts=3`, `converted=3`, `api_interrupted=false`, `r2_snapshot_saved_and_verified=true`, `publication_calls=0`. A fila preservou a campanha real, catálogo e status de curadoria; nenhuma publicação.
- O JSON foi atualizado com `remote_operation_in_progress=false` após confirmar o recibo da ação e persistência R2. Modo temporário voltou a `preview` no commit `aec5023`, disparando [Action #44552150160](https://github.com/adelrib27/blogger-automation1/actions/runs/44552150160). Provar novo produto disponível ANTES de acionar o POST de rascunho Blogger.

## C64 — Blogger pronto para novo rascunho, disparo único
- [Preview pós-conversão #44552150160](https://github.com/adelrib27/blogger-automation1/actions/runs/44552150160) SUCCESS 49 testes, `Blogger status=READY_FOR_ORIGINAL_DRAFT_REVIEW`, 0 POST, 0 LIVE. WordPress Casa preview para o tema de teste `NO_APPROVED_CACHED_PRODUCT_FOR_TOPIC`; não inventar produto/campanha nem abrir pedido contínuo.
- Estado JSON atualizado ANTES do Blogger POST com `remote_operation_in_progress=true`, `mutation_in_progress=true` no commit `9be764c`. Gatilho modo `blogger_draft_once` commit `24b7066` disparou [Action #44552501661](https://github.com/adelrib27/blogger-automation1/actions/runs/44552501661). A API Blogger foi consultada antes: **1 DRAFT existente** ID `3612281866616913629` às 15:14 UTC. Se resultado incerto, fazer readback antes de qualquer reexecução.

## C64 — DRAFT Blogger real após conversão: prova independente
- [Action #44552501661](https://github.com/adelrib27/blogger-automation1/actions/runs/44552501661) **SUCCESS**; log writer `status=DRAFT_CREATED`, `draft_creation_calls=1`, `publication_calls=0`, `has_real_csv_photo=true`, `has_keyword_link_and_cta=true`, `internal_links_from_real_posts=true`, `campaign_from_registry=true`, testes 49 PASS. WordPress Casa ainda PREVIEW no tema escolhido (sem POST).
- Leitura independente API Blogger às 15:16 UTC: **3 LIVE +2 DRAFT**, antes **3+1**. Novo post DRAFT ID `2990403416970116294`, título 'Guia de compra: Guarda-Roupa Casal 6 Portas 2 Gavetas Peroba/Off White RP154 Rei Móveis'; HTML ~5.800 chars, 1 imagem Shopee, 3 ocorrências de URL afiliada Shopee, 1 CTA, disclosure, 2 links internos reais; nenhum LIVE novo. DRAFT anterior 3612281866616913629 preservado. WordPress Casa permaneceu **43 LIVE +58 DRAFT**.
- **DEFICIÊNCIA EDITORIAL REAL:** o corpo do novo DRAFT repete a denominação comercial integral, algo tecnicamente válido mas pouco natural. Manter o post em revisão. [PR #86](https://github.com/adelrib27/blogger-automation1/pull/86) adiciona instrução IA e gate antes de Blogger `posts.insert(isDraft=True)` para textos futuros; CI [#44553367508](https://github.com/adelrib27/blogger-automation1/actions/runs/44553367508) iniciado. Não duplicar, editar ou publicar post novo nesta homologação.
- **PRODUTO E LINKS FORAM EVIDÊNCIA DE FIM A FIM NO BLOGGER**, independentemente do cron. Cron agendado ainda precisa ser visto separadamente como `event=schedule`, mas não é necessário esperar para testar R2, Shopee, Writer e POST DRAFT.

## C64 — correção editorial integrada, limpeza e balanço
- [PR #86 MERGED](https://github.com/adelrib27/blogger-automation1/pull/86), commit `b44110d147dfeffcfc6dbc05399a2636350a205c`: o gerador Blogger universal agora pede à IA não repetir o nome comercial integral no corpo e aplica bloqueio determinístico antes do POST, inclusive se um escritor customizado contornar o parser. O produto continua apresentado no bloco comercial afiliado real. [CI #44553367508](https://github.com/adelrib27/blogger-automation1/actions/runs/44553367508) **SUCCESS: 384 V31 +24 Casa +21 Oficina +15 Radar +crossblog PASS**. Não foi executado POST adicional após a alteração.
- **Limpeza concluída:** workflow TEMP `.github/workflows/v31_c64_TEMP_immediate_homologation.yml` removido do `main` no commit `c773e41` e, SOMENTE DEPOIS, trigger `affiliate_hub_v31/C64_TEST_MODE.txt` removido no commit `c54f04c`, evitando reentrada de `blogger_draft_once`/`queue_execute`. Workflows permanentes Blogger, WordPress e conversor continuam presentes e não tiveram agenda nem flag de LIVE alterada.
- **O que está realmente comprovado C64:** workflow GitHub Actions em `event=push` percorreu credenciais legítimas, catálogo R2 dos CSV, fila universal C37, API Shopee 3 URLs oficiais na campanha real e recibo de persistência R2, seleção C55 de produto novo, criação Blogger `isDraft=True` 1 vez, foto/link/CTA/disclosure/2 links internos e API Blogger independente 3 LIVE +2 DRAFT. WordPress C60 tem DRAFT real anterior #303 C62 e no C64 prévia autenticada quanto à plataforma em site conhecido, sem novo POST.
- **O que não é prova/pendência:** (1) agendamento GitHub `event=schedule` posterior a C61/C64 ainda não observado; (2) WordPress C60 `NO_APPROVED_CACHED_PRODUCT_FOR_TOPIC` para assunto da prévia, sem pedido WordPress persistente e sem conversão WordPress nesta fase; (3) revisão humana/editorial dos DRAFTs antes de LIVE; (4) uma implementação universal de publicação LIVE totalmente não assistida ainda não homologada/autorizada, o escopo validado é DRAFT seguro. Não aprovar produtos REVIEW em massa.

## Encerramento
**C64: CONCLUÍDA a homologação funcional imediata DRAFT-first com teste real Blogger e conversor; status geral V31 = PRONTO_PARA_PROXIMA_ETAPA, não homologação LIVE irrestrita.** Próxima prioridade C65: prova de `schedule` de um ciclo sem risco, backlog comercial multi-site e rotas WordPress de pedidos reais; validar qualidade do próximo texto gerado com o novo gate e plano de autorização LIVE somente após revisão. Não repetir o DRAFT Blogger `2990403416970116294` ou WordPress #303. Nenhuma mutação remota C64 pendente.

### Continuidade final conferida
- [Guard da `main` #44554026282](https://github.com/adelrib27/blogger-automation1/actions/runs/44554026282) **SUCCESS** sobre o commit de encerramento do JSON `382984791`, e [guard do índice #44553901145](https://github.com/adelrib27/blogger-automation1/actions/runs/44553901145) **SUCCESS**. `active_work` e `continuity_status` em `PRONTO_PARA_PROXIMA_ETAPA`; sem mutação ativa e sem necessidade de rollback.
