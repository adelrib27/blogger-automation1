# V31 C134 — PREVIEW auditado antes de mutações operacionais

**Data:** 2026-11-23 (America/Recife). **Branch oficial:** `main`. **Base auditada:** `70af55cb6c850639274c773d92f009171db50e46`. **Status:** C134 EM_ANDAMENTO / SAFE / LIVE_OFF.
**Retomada:** `V31-C134-20261123-PREVIEW-610-PASS-BUDGET-EXHAUSTED-LIVE-OFF`.

## Fontes obrigatórias e estado vivo verificados
- `V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json`, `CHECKPOINT_C133_AUDITOR_PRONTIDAO_UNIVERSAL_610_TESTES_2026-11-23.md` lidos da `main`.
- PRs [#134](https://github.com/adelrib27/blogger-automation1/pull/134) e [#135](https://github.com/adelrib27/blogger-automation1/pull/135) integrados; CI [#45259792390](https://github.com/adelrib27/blogger-automation1/actions/runs/45259792390) **610 testes offline PASS**; auditor [#45259940897](https://github.com/adelrib27/blogger-automation1/actions/runs/45259940897) **2 configurados / 5 com rota sem perfil+request / 1 sem rota** entre 8 prioritários. Cadastro declarativo não significa homologação remota.
- Nova execução `schedule` [#45260835997](https://github.com/adelrib27/blogger-automation1/actions/runs/45260835997), em 23/11 20:34 UTC: histórico CMS autenticado PASS, verificador independente executado PASS **com resultado `NO_NEW_OFFER: research_budget_exhausted`**, job `deliver-draft` SKIPPED, `release` SKIPPED. Não houve novo DRAFT nesse ciclo. `success` do workflow não significa publicação de rascunho.
- Cloudflare plugin conectado à **conta oficial** `adeiltonrib27@gmail.com`, ID `ebb8d5b4cf9a2cb850c6d8051bd2661f`; GET real do R2 `v31-editorial-shopee` e D1 `v31-universal-ready-safe` UUID `9bfce7a4-6167-4bfc-a65e-a74c1a34f064` retornou success. Nenhum objeto de catálogo/snapshot foi alterado.
- D1 SELECT-only em 23/11: `v31_ready_leases` 0; `v31_ready_jobs` **READY=1, USED=2**; `v31_verified_evidence` 3. Cota `blogger_moveis_para_cada_canto` campanha `moveisparacadacanto` de 23/11 UTC: SEARCH **3/3**, HTTP **3/3**. **Não aumentar teto nem reexecutar pesquisa no dia.**
- Blogger plugin GET autenticado do post `4106024906916105222` do blog `1439741542627895062`: `draft`, foto e link Shopee no HTML, aviso de afiliado; nenhum write CMS.
- WordPress Casa plugin `wp_list_posts(status=draft)` inclui post `321` com status `draft` (GET individual através da ferramenta retornou payload vazio; não alegar conferência de hash por esta leitura).
- Plugin Firecrawl desta sessão relata 327 créditos remanescentes, período 20/11–20/12. **Não comprovada equivalência entre esta conexão e a chave GitHub do V31:** não gastar créditos nem afirmar quota de workflow com base nesta leitura.
- PRs antigos abertos (ex. #132 sobre lojas Blogger de origem; #69 laboratório local) não estão autorizados para merge automático nesta C134.

## Guardas e decisões de C134
1. Prioridade: **homologação universal de DRAFT**, não trabalhos editoriais isolados concluídos e não Pinterest.
2. Não criar DRAFT repetido, não consumir READY sem revalidar tenant/campanha/SKU/assinatura/TTL/status CMS e idempotência.
3. Não cadastrar Vida Pet com campanha inventada. Cinco rotas sem perfil/review precisam de fontes/produtos comprovados; não fabricar evidências nem usar template genérico como validação.
4. `LIVE` automático **DESATIVADO**; nenhuma mudança de policy/variáveis do GitHub para permitir LIVE antes da homologação e autorização final do proprietário.
5. Mudanças de código, se necessárias, em branch isolada, testes/PR/CI e checkpoint incremental; preservar R2/D1/CMS e contas fora do V31.

## Próximas verificações nesta C134
- Auditar workflow DRAFT e política LIVE, bem como perfil/request por site e oportunidades de correção segura do auditor.
- Consultar D1 e configurações para site/campanha sem escrever, reconfirmar DRAFTs e filas sem tentar contornar cotas.
- Melhorar observabilidade/preflight de rollout se o código atual não diferenciar corretamente bloqueio temporário, cadastro declarativo e homologação operacional.
- Registrar relatório de aceite/bloqueios e próximos gates. Um novo canário agendado requer renovação **natural** da cota e não implica LIVE.

**Intervenções remotas até este preview:** somente leitura; criação deste checkpoint documental na `main`. **CMS writes: 0. R2 writes: 0. D1 writes: 0. LIVE writes: 0.**
