# Checkpoint SAFE — Shopee GraphQL e fila editorial V31 — 2026-11-09

**Status:** Consulta mínima autenticada PASS; buscas por palavra-chave intermitentes com GraphQL `10000`; **publicação dos 27 blogs ainda BLOQUEADA**.

## Estado auditado
- Repositório `adelrib27/blogger-automation1`, `main` HEAD observado `48ed05b3ff470df9f04da9318e5042da50ed863f`; nenhuma alteração feita na `main`.
- PR draft **#38**: https://github.com/adelrib27/blogger-automation1/pull/38 . Código exclusivamente SAFE de leitura da API, sem schedule nem Blogger write.
- Blogger Bridge V2: **28 blogs**, sendo **27 no escopo**, com exclusão explícita de **Meu Céu Noturno — Astronomia para Iniciantes**, Blog ID `9156820142401099679`.
- Leitura atualizada via `get_blog`, posts e rascunhos por Blog ID: **0 artigos publicados em 09/11/2026 (America/Recife)** nos 27; **4 rascunhos editoriais antigos** preservados (Eletroportáteis na Cozinha; Cabelos em Foco; Ventiladores em Foco; Limpeza Inteligente).
- Fila original: **27 pautas**, 27 IDs únicos, 27 títulos distintos. **Nenhum produto por pauta foi aprovado** e nenhum artigo/rascunho novo foi criado.

## Evidências Shopee Affiliate AppID esperado 18352820579
- [Run 42692400724](https://github.com/adelrib27/blogger-automation1/actions/runs/42692400724): consulta **sem keyword**, `productOfferV2(page:1,limit:1)`, retornou HTTP 200, `errors=[]`, itemId `22094884445`, `imageUrl` e `offerLink` HTTPS em domínios permitidos. Assinatura/credenciais **funcionaram para essa consulta**.
- [Run 42692948466](https://github.com/adelrib27/blogger-automation1/actions/runs/42692948466): keyword, sortType, campos adicionais e formato V31, todos com `limit:1`, retornaram um produto e sem erros. Resultado não comprova estabilidade.
- [Run 42693253973](https://github.com/adelrib27/blogger-automation1/actions/runs/42693253973): mínima, `sort_only` e `rich_fields` PASS; consultas `keyword_only`, `v31_shape`, `v31_limit10`, `v31_limit20_page1` e `v31_limit20_page2` retornaram HTTP 200 + **`10000 System Error`**, com request IDs registrados no log.
- [Run 42516276271](https://github.com/adelrib27/blogger-automation1/actions/runs/42516276271): catálogo V31 completo (PR #36) reexecutado em 09/11 e novamente parado por erro GraphQL genérico, sem código legível no script original.

**Interpretação:** não é falha universal de assinatura nem comprovadamente causada só por 20 itens; o processamento de consultas com `keyword` mostrou falhas **intermitentes inclusive com limit 1**. A causa interna da Shopee permanece não comprovada.

## Condições para destravar
1. Tratar `10000` como possível erro transitório apenas com retry/backoff limitados, nova assinatura a cada tentativa, log sanitizado de HTTP, code, message, request ID, sem expor segredo.
2. Confirmar, por blog e pauta, um produto real da **API autenticada** com `itemId`, `imageUrl`, `offerLink`, identidade de nicho e conformidade da política central; não substituir por produto fictício ou anúncio genérico.
3. Reconsultar posts/drafts antes da escrita; fazer SAFE editorial, criar draft, readback, publicar somente conforme autorização contextual e verificar API/HTTP público.
4. Não mesclar automaticamente o PR #38 nem modificar Tema/Loja/cron/infrastrutura.

**Resultado:** SAFE de inventário/planejamento para 27 blogs; **0 posts publicados; 0 drafts criados; 0 produtos por pauta validados**. Apenas arquivos de diagnóstico em branch draft.
