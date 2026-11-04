# LAB V31 — Integração Cloudflare Browser Rendering (contrato SAFE)

## Estado e escopo

**Somente branch LAB** `lab/v31r1-shopee-safe-20261103`. Nenhum workflow de publicação é substituído e nenhum secret é criado por este pacote.

A rota `POST /accounts/{account_id}/browser-rendering/content` com `cacheTTL=0` foi consultada ao vivo através da conta Cloudflare conectada, e seu HTML coincidiu com a LOJA Blogger em 16 IDs, 16 categorias, 16 links e 16 imagens. Isso valida a *rota de leitura*, mas não o ciclo automático de autenticação pelo GitHub.

## Arquitetura

- `blogger_stores/src/v31_public_verify_readonly.py`: fonte de verdade atual para comparação exata de HTML com a seleção Shopee segura. Reutilizado **sem alterações**.
- `blogger_stores/src/v31_public_verify_cloudflare.py`: transporte Cloudflare com URL Blogger canônica fixa e resposta limitada a 4 MB, sem nenhum PUT no Blogger; não armazena credenciais nem HTML público.
- `blogger_stores/tests/v31_cf/test_v31_public_verify_cloudflare.py`: fixtures offline e casos fail-closed. Usa caminho relativo ao arquivo do teste para funcionar no GitHub e no Windows.
- `.github/workflows/v31_lab_cloudflare_contract_safe.yml`: somente compilação e testes locais, sem tokens e sem chamada HTTP. Gatilho da branch LAB.

## Regra de falha

- `PUBLIC_EXACT_PASS`: somente se houver 16 IDs, categorias, links e imagens exatos, tema e marcadores presentes e SHA da seleção confirmado.
- `PUBLIC_PENDING_THROTTLED` (exit 75): HTTP 429/503/504 da API Cloudflare ou indisponibilidade de rede.
- `PUBLIC_VERIFICATION_FAILED` (exit 2): token/conta ausente, permissão negada, HTML inesperado, conteúdo divergente ou outro erro contratual.

Erro ou indisponibilidade **não autorizam segunda publicação, rollback cego ou persistência da rotação**.

## Protocolo para um futuro teste autenticado (ainda não executado)

1. Autorizar uma credencial Cloudflare dedicada, com o menor escopo adequado a Browser Rendering na conta identificada. **Não reutilizar tokens administrativos gerais** e não expor valores nos relatórios.
2. Configurar os secrets do GitHub somente no contexto LAB apropriado: `CLOUDFLARE_ACCOUNT_ID` e `CLOUDFLARE_BROWSER_TOKEN`; verificar regras de acesso a secrets em branches.
3. Criar workflow separado **somente leitura** que baixe o artefato da seleção Shopee V23, confirme seu SHA-256 e execute o adaptador com tokens via variáveis de ambiente. Não incluir `Blogger OAuth` nem `contents:write`.
4. Exigir artefato com `PUBLIC_EXACT_PASS` e código 0; executar casos de 429, 401, divergência e impossibilidade de consulta na CI.
5. Somente após a prova autônoma aprovada, integrar compare-and-swap para ledger e histórico, testar recuperação e então considerar cron.

**Atenção:** o arquivo de estado `PUBLISHED_PENDING_PUBLIC` não deve ser promovido por esta etapa. As flags `v31_enabled_for_new_blogs=false` e `daily_store_updates_enabled_by_runner=false` permanecem intactas.