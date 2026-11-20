# C74 — Recuperação da conta Cloudflare oficial V31 (20/11/2026)

**PRÉVIA EM_ANDAMENTO — registrada ANTES de mutações Cloudflare.**

## Identidade e evidência confirmadas
- GitHub `main` retomado do checkpoint C73 e estado JSON C73; nenhum outro projeto será modificado.
- Conta Cloudflare **`adeiltonrib27@gmail.com`**, perfil estável `user:9412f150e9ef160c8c31729358185bc9`, ID da conta `ebb8d5b4cf9a2cb850c6d8051bd2661f`: `GET /accounts/.../r2/buckets/v31-editorial-shopee` retornou `success=true`, `name=v31-editorial-shopee`; `GET /accounts/.../d1/database` retornou **0 bancos**. Estas são leituras REAIS nesta retomada, a autenticação antes bloqueada por 401 está restabelecida.
- Banco `v31-universal-ready-safe` C73 na conta separada **`adeiltonrml@gmail.com`** permanece intacto, isolado, sem writer; NÃO migrar, deletar ou presumir que pertence ao R2 V31.
- Migration fonte `affiliate_hub_v31/migrations/c71_universal_ready_d1.sql`: quatro tabelas exclusivas `v31_*` mais um índice, sem dados de produção, revisada nesta fase.

## Plano de intervenção exclusivamente SAFE
1. Criar banco **NOVO e dedicado** `v31-universal-ready-safe` somente na conta do R2 oficial `ebb8d5b4cf9a2cb850c6d8051bd2661f`, sem replicação/Worker/binding/cron e sem credenciais publicadas.
2. Conferir nome+UUID obtidos, aplicar esquema C71 somente no novo D1 e conferir as 4 tabelas.
3. Rodar canário SQL somente com identificadores sintéticos `v31_c74_canary_*`, testar concorrência lease/duplicatas/budget e limpar as quatro tabelas, readback zero.
4. Se algum passo falhar, parar e documentar; não conectar D1 a writers ou R2, não consumir Firecrawl, não alterar contas, blogs, LIVE nem D1 de outros projetos.
5. Registrar evidência de resultados e atualizar estado/índice. Independente do canário, integração do D1 aos escritores fica pendente até credencial isolada e validações finais.

**Status inicial:** `EM_ANDAMENTO`; sem mutações Cloudflare C74 ao gravar este arquivo.
