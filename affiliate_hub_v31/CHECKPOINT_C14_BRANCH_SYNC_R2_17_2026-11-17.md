# CHECKPOINT C14 — Main reconciliada, flags OFF, 17 links reais R2 (17/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C14-MAIN-SYNC-137-TESTS-R2-17LINKS-FLAGS-OFF-20261117`

**Repositório:** `adelrib27/blogger-automation1`  
**Branch:** `feature/v31-affiliate-hub-c1-safe-20261115`  
**PR:** [#52 DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52), ainda aberto, sem merge em `main`, sem flags LIVE, sem publicação de teste.

## Escopo inalterado

V31 é hub universal de produtos/links Shopee para WordPress e Blogger atuais e novos; os artigos, geradores Qwen3, SEO e publicadores originais permanecem. Priorizar API Shopee; no GraphQL erro 1000 confirmado, usar catálogo CSV/SQLite privado R2 com links afiliados reais por campanha, sem inventar ofertas nem preços. Pinterest fora. Reutilização do mesmo produto para assuntos/títulos e corpos diferentes só sob gates de originalidade e triplo opt-in.

**Observação do usuário para somente DEPOIS de concluir V31:** todas as páginas de loja consultam/rotacionam produtos Shopee DIARIAMENTE, possivelmente concentrando requisições com as buscas dos artigos e 5 slots do Radar. Investigar horários/volume/erros em etapa independente e avaliar eventual rotação mensal individualizada por blog, **sem desativar loja nem atribuir automaticamente o erro 1000 ao rate-limit 10030**. Não alterar agendas das lojas antes.

## C14.1 — Auditoria de merge, sem modificar main

- [Run 44089068660](https://github.com/adelrib27/blogger-automation1/actions/runs/44089068660): `V31_C14_MERGE_DRY_RUN_PASS`, **nenhum conflito** na simulação `git merge-tree origin/main HEAD`; **118 workflows YAML** válidos; **137/137 testes V31**.
- [Run 44089292281](https://github.com/adelrib27/blogger-automation1/actions/runs/44089292281): **SUCCESS**. GitHub Actions mesclou a `main` *para dentro da branch feature apenas*, **depois de verificar que não existiam diferenças nos arquivos `**/data/**`** entre a árvore mesclada e `main`. Testes pré-push **137 V31 + 24 Casa + 21 Oficina + cross-blog PASS**. Commit da merge feature `bf08840bd736568f7610146376499b6153e74822`, `main` permaneceu `2fd5bb562e7cdcbea77d59f4dcdc2e95f467dcd1` na auditoria.
- Confirmação após merge: a branch ficou **0 commits atrás** de `main`, PR continua DRAFT e `mergeable=true`. **Nenhum histórico/fila/artigo antigo da main foi sobrescrito.**
- Se a main avançar mais após este checkpoint, sincronizar novamente antes da revisão final de release.

## C14.2 — Flags e agendamentos V31

[Run 44089682722](https://github.com/adelrib27/blogger-automation1/actions/runs/44089682722) — **SUCCESS**, auditou apenas o resultado booleano das GitHub Repository Variables, sem ler secrets:

| Chave | Resultado no run |
|---|---|
| `V31_EDITORIAL_C9_RELEASE_ENABLED` | **OFF** |
| `V31_CASA_R2_FALLBACK_ENABLED` | **OFF** |
| `V31_OFICINA_R2_FALLBACK_ENABLED` | **OFF** |
| `V31_RADAR_R2_FALLBACK_ENABLED` | **OFF** |
| `V31_EDITORIAL_PRODUCT_REUSE_ENABLED` | **OFF** |
| `V31_EDITORIAL_CACHE_WARMUP_ENABLED` | **OFF** |
| `V31_EDITORIAL_SHADOW_ENABLED` | **OFF** |

Nenhum dos workflows novos entrou em operação comercial via flags. Agendamentos e páginas de loja existentes continuaram intactos.

## C14.3 — Um lote real de 3 conversões, snapshot R2 restaurado e íntegro

[Run 44089505226](https://github.com/adelrib27/blogger-automation1/actions/runs/44089505226) — **SUCCESS**, sem posts:
1. **137/137 testes PASS**.
2. Auditoria R2 real antes do lote: **14 links** cacheados.
3. Planejamento dry-run: **0 mutações**; escolheu 1 candidato para cada um dos 3 WordPress.
4. Uma única execução real: **3 tentativas Shopee, 3 links afiliados convertidos**, um por campanha; **1 snapshot privado R2** gravado, restaurado e conferido, `api_interrupted=false`, `retention_pending=false`.
5. Auditoria R2 real após o lote:

| Blog / campanha | Links válidos | Meta 3 dias | Categorias representadas | Status |
|---|---:|---:|---:|---|
| Casa e Decoração / `casaedecoracaowp` | **4** | 9 | 3/8 | `NOT_READY` |
| Oficina & Garagem / `oficinawp` | **4** | 6 | 4/6 | `NOT_READY` |
| Radar Tech BR / `radarwp` | **8** | 15 | 5/5 obrigatórias | `NOT_READY` |
| Blogger Air Fryers | **1** | ainda sem perfil shadow | nicho piloto | piloto |

**Total R2: 17 links afiliados reais**. Catálogo 109.507 produtos / 4.674 elegíveis. **Faltam 14 links** para metas iniciais: Casa +5, Oficina +2, Radar +7. Estes números são cache validado pelo V31, não garantia de que ofertas/comissões ainda estejam ativas na Shopee. Não efetuar rajadas de chamadas para completar.

## Remoção de testes transitórios

Os quatro workflows temporários de C14 foram excluídos do PR depois das provas:
- `v31_c14_merge_dryrun_once.yml`;
- `v31_c14_reconcile_branch_once.yml`;
- `v31_c14_replenish_once.yml`;
- `v31_c14_flags_once.yml`.

Permanecem somente os workflows novos de uso SAFE sob confirmação/opt-in e a integração existente sob switches OFF. **Não houve merge da PR #52, publicação de posts, alteração de páginas de loja ou ativação de cron V31.**

## Pendências para liberação segura (C15)

1. Fazer reposição gradual dos **14 links restantes** em horários escalonados, priorizando a saúde da API e cada campanha. Limite-piloto global continua 3 mutações/run, sem converter durante erro 1000 persistente. Confirmar `SHADOW_READY` em R2 para todos; mesmo assim a condição NÃO autoriza automaticamente publicação.
2. **Revalidar histórico da main antes do primeiro merge/rollback**. C13 já comprovou: Casa 46 publicações (41 produtos com texto histórico correspondente), Oficina 12 (somente 1 correspondência; 11 sem corpo devem permanecer bloqueados para reuso). C11/C12 implementaram originalidade e bloqueio fail-closed; Radar mantém diversidade original.
3. Revisar acesso/restrições do GitHub Environment `v31-editorial-safe` e contratos de checkout/workflow_call; o teste da sintaxe YAML e merge seguro NÃO é validação de permissão LIVE. Os switches são Repository Variables auditadas no run e estão OFF.
4. Fazer canário final por blog **sem publicar**, testando tanto API saudável quanto erro 1000 simulado + R2, e planejar revisão e eventual liberação **supervisionada**, sem agendar posts de teste.
5. Novos blogs entram via `sites.d` e `shadow.d` com campanhas reais; engine não fixa 3 blogs. Adicionar chamadas/consumidores que preservem cada automação antiga em vez de duplicar geradores.
6. **Somente após V31 pronto** estudar concentração de requisições nas páginas de loja e a rotação mensal proposta pelo usuário.

**Estado final C14:** branch sincronizada sem conflito ou diffs nos dados editoriais; 137 testes PASS; flags V31 comprovadamente OFF; links R2 aumentaram de 14 para 17; **liberação automática continua bloqueada** e PR permanece DRAFT.
