# V31 C136 — PREVIEW de monitoramento de cron legados e saúde dos DRAFTs

**Data:** 2026-11-23, America/Recife. **Branch base:** main `69000e0ac696e4251d59535f7b7d643cc6693e13`.
**Código:** `V31-C136-20261123-PREVIEW-SAFE-OBSERVATION-LIVE-OFF`.
**Objetivo:** manter a execução autônoma verificável mesmo sem janela de chat ativa, sem duplicações, sem publicar LIVE.

## Fontes lidas
- `V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json` e [checkpoint C135](CHECKPOINT_C135_READY_CMS_CONFLITO_PROVADO_638_TESTES_2026-11-23.md) conferidos na `main`.
- PR #137 merge às `2026-11-23T20:57:59Z` com `false &&` em ambos jobs de cada writer Casa/Oficina, flags de publicação falsas; até ~22:02 UTC não há resultado observado de cron pós-merge desses dois workflows. **O código bloqueado não é prova operacional de run SKIPPED.**
- V31 scheduler `#45260835997` em 23/11 atingiu D1 SEARCH 3/3 e HTTP 3/3 para Móveis, sem criar novo DRAFT. Quota renovar naturalmente no próximo dia UTC; NÃO disparar repetição agora, não aumentar limite.
- D1 `v31-universal-ready-safe` SELECT real: jobs READY=1 (Casa SKU `shopee:306698991:8503898928`, divergência de hash com WP DRAFT #314 demonstrada em C135), USED=2, leases=0. Somente leitura; não consumir READY.
- Dois pilotos históricos configurados na continuidade: Blogger Móveis #4106024906916105222, WP Casa #321, cada um com ID/título/hash de leitura CMS a revalidar. Ambos são DRAFT, nunca LIVE.
- Workflows extras revisados: `radar_fase3_fila_diaria.yml` em schedule apenas gera e valida fila (não é publisher); `radar_fase3_publicacao.yml` está manual e inerte; `casa_editorial_publish_schedule.yml` e `casa_editorial_manual.yml` são manuais e não integram o cron legado. V31 LIVE política `pending_policy_approval`.
- Observação histórica segura C94 R2: 4 candidatos de catálogo em cada Cozinha, Estilo e Limpeza, **ainda sem verificação independente de fabricante ou link convertido da campanha**, não ativar perfis/pedidos.

## Plano mínimo de implementação
1. Auditor operacional somente leitura: consultar a API GitHub Actions sobre runs `schedule` de Casa/Oficina **criados depois do merge #137**; consultar jobs do run para comprovar `skipped`. Emitir somente `PENDING_OBSERVATION`, `SKIP_VERIFIED` ou `SECURITY_EXCEPTION`, sem interpretar ausência de run como sucesso. Confirmar invariantes de static workflow/flags LIVE OFF.
2. Workflow GitHub Actions read-only agendado diariamente após último cron dos legados, e com um disparo `push` inicial ao merge. Adicional: auditor GET WordPress/Blogger + D1 SELECT via `affiliate_hub_v31.audit_draft_pilots` para vigiar integridade dos dois DRAFTs; não chamar geração/revisão, Shopee, Firecrawl ou R2.
3. Testes offline, PR, CI antes de merge; atualizar checkpoints e índice com evidência obtida, incluindo pendências de quota e rollout.

## Proibições explícitas
- Não alterar nem ativar LIVE, `V31_AUTOLIVE_ACTIVE`, cron de criação de artigos, política de aprovação ou quotas D1.
- Não dar dispatch adicional no scheduler de DRAFT nem gerar POST/PUT/PATCH de CMS.
- Não promover READY conflitado da Casa nem cadastrar Vida Pet com campanha inexistente.
- Não confundir `SUCCESS` do monitor com verificação de SKIPPED quando nenhum run pós-hold tiver ocorrido.

**Continuidade:** próxima execução inicia neste PREVIEW e verifica `main`, PR/CI e resultados das APIs.
