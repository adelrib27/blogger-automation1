# V31 C136 — monitor operacional LIVE HOLD + GET de DRAFTs, homologado

**Data:** 2026-11-23 (America/Recife). **Projeto:** V31 Hub Editorial Shopee — Blogger & WordPress.
**Código de retomada:** `V31-C136-20261123-653-TESTS-DRAFT-GET-PASS-LEGACY-CRON-PENDING-LIVE-OFF`.
**Status:** C136 MONITOR READ-ONLY HOMOLOGADO, **a comprovação dos dois crons legados ainda PENDENTE**, canário de novo DRAFT ainda pendente; LIVE OFF.

## 1. Base e contexto
Fonte obrigatória antes de agir: `V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json`, [C135](CHECKPOINT_C135_READY_CMS_CONFLITO_PROVADO_638_TESTES_2026-11-23.md), Actions GitHub, D1 oficial por SELECT. Preview C136 salvo na `main` no commit `e02e23282cce960516d8498e852fdd24f79f9ad6` **antes do código**.

- PR #137 merge `2026-11-23T20:57:59Z`: ambos os jobs Casa/Oficina de descoberta+writer contém `false &&` e flags LIVE OFF/status draft. **Ainda não havia cron pós-merge observado.**
- `v31_ready_jobs` D1: `USED=2`, `READY=1`; leases 0; o único READY é WordPress Casa SKU `shopee:306698991:8503898928` **CONFLICTING_DRAFT_HTML** com CMS DRAFT #314, comprovado pela C135. NÃO consumir, sobrescrever, reescrever, publicar ou gerar duplicata.
- `v31_search_budget` D1 `2026-11-23`, Móveis `moveisparacadacanto`: `SEARCH 3/3`, `HTTP 3/3`; não aumentar cotas nem repetir pesquisa antes de renovação NATURAL UTC.
- `radar_fase3_fila_diaria.yml` [run #45275511554](https://github.com/adelrib27/blogger-automation1/actions/runs/45275511554) **SUCCESS** 22:01 UTC monta fila, não faz publicação. `radar_fase3_publicacao.yml` legado inerte, manual. Workflows manuais Casa separados do cron; não acionados nesta etapa. A política `autonomous_live_policy.json` permanece `activation: pending_policy_approval`.

## 2. Código implantado, CI e correção do erro real
- [PR #139](https://github.com/adelrib27/blogger-automation1/pull/139) integrado SHA `ea4dc097c819b755eaccbee6b87317c88df17946`: novo `affiliate_hub_v31/legacy_live_hold_monitor.py` (GET GitHub Actions, pós-hold, classifica `PENDING_OBSERVATION` / `SKIP_VERIFIED` / `SECURITY_EXCEPTION_JOB_RAN`), 15 testes adicionais em `tests/test_c136_legacy_live_hold_monitor.py`. `.github/workflows/v31_c136_legacy_hold_monitor_safe.yml`: `push` do próprio YAML + `workflow_dispatch` manual + cron diário `47 23 * * *` UTC (20h47 Recife), `contents:read/actions:read`, monitora jobs legados e roda `audit_draft_pilots` GET CMS/SELECT D1. Nada de POST CMS, R2, Shopee, pesquisa, aumento de limite ou LIVE.
- [CI inicial #45276501078](https://github.com/adelrib27/blogger-automation1/actions/runs/45276501078) **653/653 PASS** e regressões Casa 24/24, Oficina 21/21, Radar 15/15, cross-blog PASS.
- [Execução real #45276651288](https://github.com/adelrib27/blogger-automation1/actions/runs/45276651288) falhou na consulta remota, **sem writes**, mas passou nos testes locais/guarda estática. Erro inicialmente ocultado com fail closed.
- [PR #140](https://github.com/adelrib27/blogger-automation1/pull/140) integrado SHA `7bbb9defd42cdc185e572ee17bdbb9606e689306`: apresentou somente código seguro da falha (sem tokens/URLs). [Execução #45276964406](https://github.com/adelrib27/blogger-automation1/actions/runs/45276964406) revelou `github_response_too_large` com GET de `per_page=60`; **sem impacto em CMS/D1 e sem LIVE**.
- [PR #141](https://github.com/adelrib27/blogger-automation1/pull/141) integrado SHA `6385fd10c308366ed2acdda73a766c33b9f86f51`: reduzido GET `per_page=5`, limite seguro de resposta preservado, cobertura de teste incluída; [CI #45277141551](https://github.com/adelrib27/blogger-automation1/actions/runs/45277141551) **653 PASS** + demais regressões PASS.

## 3. Evidência operacional final
[GitHub Actions C136 #45277246529](https://github.com/adelrib27/blogger-automation1/actions/runs/45277246529): **COMPLETED SUCCESS**, dois jobs:
1. `audit-legacy-crons`: `success`. Static guard: `STATIC_SAFE_HOLD_VERIFIED`. GET remoto: `READ_ONLY_SCHEDULE_VERIFICATION` com Casa=`PENDING_OBSERVATION` (sem schedule pós-PR137 encontrado), Oficina=`PENDING_OBSERVATION` (sem schedule pós-PR137 encontrado), `all_holds_verified=false`, `cms_writes=0,d1_writes=0,workflow_dispatches=0,automatic_live_authorized=false`. **Não afirmar SKIPPED até observar execução futura real.**
2. `audit-existing-draft-pilots`: `success`. GET CMS autenticado + D1 SELECT confirmam `status=draft` e hash exato para:
   - Blogger `blogger_moveis_para_cada_canto` #`4106024906916105222`, SHA-256 `acf054f9eb4b65196aa46544c8402e7d603144d781604e006042059ba263569c`.
   - WordPress `wordpress_casa_decoracao` #`321`, SHA-256 `81303c4a8d9590a0f4490afa8d92c8f845e5add267195535b7de5a2d300e6877`.
   - A auditoria `audit_draft_pilots` também requer, para ambos, que os jobs correlacionados D1 estejam `USED`, não somente o status do post.

## 4. Contrato para C137+
- Monitor C136 `cron '47 23 * * *'` UTC continua habilitado para observar crons legados após execução natural. Quando ambos forem `SKIP_VERIFIED`, registrar run e atualizar checkpoint. **Não disparar artificialmente writer só para testar**, não inferir resultados de status de configuração.
- Aguardar virada natural UTC e scheduler independente do piloto Móveis `cron '47 */4 * * *'`. Verificar categoria `BLOCKED_RESEARCH_BUDGET` vs `DRAFT_VERIFIED`; sem duplicar, consultar Blogger GET e comparar ID/title/HTML SHA/link convertido/imagem real, D1 USED e recebido assinado. Não publicar LIVE.
- Casa D1 READY colide com WP #314 (hashes diferentes), **nenhuma entrega**. Escolher outro SKU somente após fonte independente, campanha e dedup confiáveis.
- Prontidão prioritária ainda **8**: 2 com profiles/request, 5 com rota sem profile/request, 1 Vida Pet sem campanha V31 real. Shortlist histórica C94 (12 SKUs em Cozinha, Estilo, Limpeza) é só pesquisa de catálogo, não perfil de fatos independente nem validação de afiliado. Não inventar.
- **LIVE permanece OFF**; homologação completa E2E e autorização final do proprietário obrigatórias antes de qualquer alteração em variável/política LIVE. Sem Pinterest.

**Resultado C136:** 653 testes PASS; auditoria remota final SUCCESS; dois DRAFTs confirmados por GET+SELECT; monitor agendado, ainda sem prova de cron legacy SKIPPED por ausência de run pós-hold; novos DRAFTs=0; novas publicações LIVE=0; D1/R2/CMS writes pela C136=0.
