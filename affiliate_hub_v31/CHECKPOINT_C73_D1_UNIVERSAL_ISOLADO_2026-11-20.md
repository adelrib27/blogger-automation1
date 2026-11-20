# C73 — D1 V31 universal dedicado: implantação SAFE (20/11/2026)

**PRÉVIA EM_ANDAMENTO — registrada ANTES de qualquer mutação em Cloudflare.**

## Estado e escopo
- C71 [PR #99](https://github.com/adelrib27/blogger-automation1/pull/99) integrado em `main`, [CI #44747425029](https://github.com/adelrib27/blogger-automation1/actions/runs/44747425029) SUCCESS 494 testes + legacy. Contratos `d1_universal_ready.py`, `final_fact_gate.py`, migration `migrations/c71_universal_ready_d1.sql` testados **offline**, não ligados aos writers.
- C72 [Action #44747950119](https://github.com/adelrib27/blogger-automation1/actions/runs/44747950119) SUCCESS: `remaining_credits=1000` (GET, mesma chave `FIRECRAWL_API_KEY` GitHub), nenhum search/scrape/post. Workflow TEMP removido.
- Cloudflare **conta primária já usada no ecossistema Shopee** `b1515400afe32581994c4d3f038f835f` confirmada por leitura no conector Cloudflare Projeto Automação. Bancos existentes: `ar-variedades-pfe-catalog-safe`, `vida-pet-pratica-state`, `pinterest-automation-db`. Consulta `sqlite_master` somente leitura comprovou que `ar-variedades-pfe-catalog-safe` tem tabelas `arv_*` dedicadas a outro subsistema, sem `v31_ready_*`. **Não reutilizar nem modificar esses 3 bancos.**
- Na segunda conta Cloudflare, nenhum D1 existente; a conta primária foi escolhida porque já hospeda projetos Shopee e é a conta V31 apropriada, mas novos recursos são estritamente separados.

## Implantação segura pretendida
1. Criar exclusivamente novo banco D1 `v31-universal-ready-safe` na conta `b1515400afe32581994c4d3f038f835f`, com replicação desativada e sem links a R2/Workers/CMS/CSV existentes.
2. Aplicar exclusivamente as 4 tabelas C71 `v31_ready_leases`, `v31_ready_jobs`, `v31_verified_evidence`, `v31_search_budget` e índice da migration, mediante endpoint oficial D1, verificar esquema e banco de destino.
3. Exercitar no banco novo apenas **fixtures sintéticas identificadas `v31_c73_canary_*`**, com INSERT/RETURNING e 2 tentativas de lease, idempotência READY/USED e orçamento; remover todas as fixtures, validar contagens zero. Nunca introduzir SKU real/segredo nem usar LIVE.
4. Não instalar Worker/writer real sem validar autenticação/lease/ROI e sem inserir segredos GitHub; não ativar Firecrawl search nem conectar workflow ao banco enquanto canários não PASS e integração credencial apropriada não criada.
5. Registrar IDs/evidências, falhas e limpeza no checkpoint e no estado; se houver erro, interromper mutações, preservar dados e auditar. Em nenhuma circunstância alterar dados Pet/ARV/Pinterest, R2, Shopee, Blogger ou WordPress.

## Evidências de cron e CMS
- GitHub V31 `event=schedule` reais de 19/11: fila #44600350780 failure pós 3 links Shopee; Blogger #44609598601 SUCCESS DRAFT_CREATED 0 LIVE; WP #44614079395 SUCCESS DRAFT_CREATED 0 LIVE. Em 20/11 10h34 Recife sem novos 3 schedules na listagem. Auditoria CMS 20/11: Blogger 3 LIVE/3 DRAFT, WP 45 LIVE/59 DRAFT, origem de +2 LIVE não atribuída ao V31.

**Estado inicial:** C73 prévia apenas no GitHub, D1 universal novo ainda não criado ao gravar este checkpoint. Segredos nunca aparecem em commits/logs.

## C73.1 — D1 V31 dedicado criado e esquema aplicado

- Conta Cloudflare principal `b1515400afe32581994c4d3f038f835f`; banco D1 **`v31-universal-ready-safe`** novo, UUID `e16554d8-27e8-40ca-9b6e-5f6d7b54d076`, criado 20/11/2026 14:23:40Z. Nenhum banco anterior foi modificado.
- Migration `affiliate_hub_v31/migrations/c71_universal_ready_d1.sql` executada diretamente no D1 via API Cloudflare **somente após verificar id e nome do banco**. Cinco comandos `CREATE TABLE/INDEX IF NOT EXISTS` sucesso. Consulta `sqlite_master` confirmou as quatro tabelas `v31_ready_jobs`, `v31_ready_leases`, `v31_search_budget`, `v31_verified_evidence`.
- READ replication desligada; sem Worker, cron, token GitHub D1 novo ou publicação. Dados Shopee e CMS não foram tocados.
- Próximo ensaio C73.2: dados sintéticos `v31_c73_canary_*` no novo banco somente, testar atomicidade `RETURNING`, contenção de lease, dedup READY, budget e 429, depois limpeza por `site_key`, contagens zero. Não escrever nomes de blogs reais neste teste.


## C73.2 — D1 real: seis verificações funcionais PASS e limpeza confirmada

- O novo banco exclusivo `v31-universal-ready-safe` UUID `e16554d8-27e8-40ca-9b6e-5f6d7b54d076` foi verificado por nome+ID antes das operações e recebeu somente fixture sintética `site_key=v31_c73_canary_blog`, `campaign=v31_c73_canary`; nenhum SKU/produto de CSV ou blog real foi escrito.
- Testes realizados na própria API D1 SQL/RETURNING: `lease_contention=true` (segundo proprietário recusado enquanto lease válido), `ready_idempotent=true` (duplicata recusada), `same_sku_cooldown=true` (outro ângulo do mesmo SKU bloqueado), `daily_budget_bounded=true` (terceira tentativa bloqueada com cap 2), `breaker_429=true` (estado bloqueado persiste), `tenant_tag_isolated=true`. **`all_pass=true`**.
- Limpeza `finally` efetuou `DELETE` somente para o tenant sintético nas quatro tabelas; leitura de `jobs, leases, budgets, evidence` retornou tudo zero: `fixture_cleanup_zero=true`.
- Não houve escrita em WordPress, Blogger, Vida Pet, catálogo R2, Shopee nem qualquer Firecrawl SEARCH/scrape. Apenas novo D1 V31 e dados sintéticos transitórios.
- **C73 SAFE concluída:** D1 real e SQL atômico comprovados, mas o adaptador `d1_universal_ready.py` ainda opera via *query runner* abstrato; não há credential GitHub D1 dedicada ao V31, Worker, binding, sincronização REAL com writer nem chamada real Firecrawl. Não inferir funcionamento de integração Writer/Evidence apenas a partir da migration.


## C73.3 — CORREÇÃO CRÍTICA DE TITULARIDADE CLOUDFLARE (20/11/2026)

**A hipótese anterior de que a conta Cloudflare com ARV e Vida Pet era a conta principal do catálogo V31 estava ERRADA.** Auditoria somente leitura de três contas com conectores Cloudflare e do checkpoint C3:

| E-mail | Conta ID | Evidência |
| --- | --- | --- |
| `adeiltonrib27@gmail.com` | `ebb8d5b4cf9a2cb850c6d8051bd2661f` | **Bucket OFICIAL `v31-editorial-shopee`**, criado 15/11/2026 22:14Z, Standard, ENAM; sem D1 |
| `adeiltonrml@gmail.com` | `b1515400afe32581994c4d3f038f835f` | Bancos ARV e Vida Pet; R2 `pinterest-media`; **D1 `v31-universal-ready-safe` criado C73 nesta conta errada para o R2 original** |
| `comercebem@gmail.com` | `4c6570edc2eeb0f55440904ae236b046` | Nenhum D1; API R2 respondeu 403 código 10042, R2 não habilitado |

**Histórico:** `affiliate_hub_v31/CHECKPOINT_C3_R2_2026-11-15.md` comprova bucket V31 na conta selecionada pelo proprietário. O código GitHub usa `vars.V31_EDITORIAL_R2_ACCOUNT_ID`, mas a variável não foi lida neste diagnóstico; pode ser conferida de modo não secreto antes de deploy.

**BLOQUEIO:** não conectar aos writers o D1 novo `e16554d8-27e8-40ca-9b6e-5f6d7b54d076` da conta `adeiltonrml`; o banco está isolado e vazio após limpeza das fixtures, sem integração ao R2 e sem LIVE. Não apagar nem migrar por inferência. A próxima configuração D1 para o V31 deverá considerar a conta do bucket oficial `adeiltonrib27` (ou arquitetura multi-account explicitamente validada). Os testes SQL C73.1/C73.2 continuam válidos, mas **não demonstram seleção correta da conta de produção**. Nenhuma mudança Cloudflare/CMS nesta auditoria.
