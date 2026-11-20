# C79 — backend R2 S3 condicional para envelopes READY privados (20/11/2026)

**PRÉVIA EM_ANDAMENTO — salvo ANTES de qualquer código ou mutação R2 nesta fase.**

## Ponto de entrada real
- GitHub `main` HEAD `20df80eaca11d4300ef720d61d0e6ecafefc556b`, estado C78 `PRONTO_PARA_PROXIMA_ETAPA`.
- C77 [PR #102](https://github.com/adelrib27/blogger-automation1/pull/102) CI518 PASS e C78 [PR #103](https://github.com/adelrib27/blogger-automation1/pull/103) CI527 PASS. `private_ready_envelope.py` exige backend `put_if_absent` atômico e readback.
- R2 S3 já usado por `R2State.from_env()` em `v31-editorial-shopee`; ambiente GitHub `v31-editorial-safe` teve `R2_ACCOUNT_STATUS=MATCH` na C77. Segredo novo D1 NÃO configurado e writers D1 desligados.
- Cloudflare documenta `PutObject` S3 + `If-None-Match: *` atômico; falha por objeto existente retorna HTTP 412 `PreconditionFailed`, ver https://developers.cloudflare.com/r2/api/s3/conditional-operations/ (última atualização 10/11/2026).

## Plano isolado e verificável
1. Implementar `r2_private_ready_backend.py`: cliente boto3 S3 existente com `put_object(IfNoneMatch='*')`, identificação fixa da conta `ebb8d5b4cf9a2cb850c6d8051bd2661f` e bucket `v31-editorial-shopee`, chave rigidamente limitada a `v31/private-ready/v1/<site>/<campanha>/<sha-prefix>/<sha>.json`, GET com tamanho limitado e nenhum fallback.
2. `from_environment()` valida IDs oficiais ANTES de criar boto3/abrir rede; `get()` trata 404 apenas como ausente e falha fechado em outras exceções; `put_if_absent()` traduz só 412 PreconditionFailed em False, 409 e timeout permanecem erros. Não expor objetos/segredos em logs.
3. CI offline: identidade, bucket, prefixo, validação de SDK, condições atômicas, 412 e concorrência simulada, readback/truncamento, corrupção e idempotência do C78.
4. Após PR+CI, canário REAL opcional apenas em GitHub Actions `environment: v31-editorial-safe`, com objeto exclusivamente sintético sob prefixo `v31/private-ready/v1/c79-canary/`, GET/2º PUT=412/limpeza controlada; nunca tocar catálogo/pointer/produtos/posts/contas diferentes.
5. D1 token mínimo ainda pendente: não inventar credencial, não habilitar writers ou LIVE nem chamar Firecrawl. Atualizar checkpoint, JSON, índice sempre antes/depois.

**Estado inicial:** `EM_ANDAMENTO`, sem alterações Cloudflare/R2/CMS nesta fase.
