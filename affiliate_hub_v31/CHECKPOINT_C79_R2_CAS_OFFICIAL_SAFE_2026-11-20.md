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

## C79.1 — implementação e suíte CI homologadas
- [PR #104 MERGED](https://github.com/adelrib27/blogger-automation1/pull/104), SHA de merge `4bad4e6af19ba56481dcd03960f5f0a9a962fc3d`; arquivos somente em `affiliate_hub_v31/` (`r2_private_ready_backend.py`, `tests/test_c79_r2_private_ready_backend.py`, `C79_R2_PRIVATE_CAS_CONTRATO.md`).
- [GitHub Actions #44776194805](https://github.com/adelrib27/blogger-automation1/actions/runs/44776194805) **SUCCESS**: `Ran 537 tests ... OK` (10 testes C79), Casa 24/24, Oficina 21/21, Radar 15/15, crossblog PASS.
- Adaptação S3 usa apenas conta e bucket V31 fixos, `put_object(IfNoneMatch='*')`, 412 -> colisão, outros erros bloqueiam, não faz GET antes do PUT, GET valida content length/metadata sha256 e fecha stream, sem delete/list no backend produtivo. Fábrica `from_environment` valida account/bucket antes de instanciar boto3 e reutiliza credenciais existentes do ambiente protegido.

## C79.2 — canário REAL R2 no bucket oficial: PASS + limpeza
- Workflow temporário `.github/workflows/v31_c79_TEMP_r2_cas_canary.yml`, executado por push **uma única vez** no ambiente GitHub `v31-editorial-safe`, [run #44776685517](https://github.com/adelrib27/blogger-automation1/actions/runs/44776685517) **SUCCESS**.
- Canário fixou account ID e bucket oficial; criou rota **sintética no processo**, não cadastrada em `sites.d` e nunca utilizável por CMS real. Conteúdo e chave únicos gerados por run/nonce; HMAC de TESTE criado em memória, sem modelo/Firecrawl/SEO real.
- Logs confirmam `V31_C79_R2_CAS_REAL_PASS` após `PutObject` condicional, repetição idempotente, GET íntegro, recusa REAL de PUT de bytes diferentes com código `412 PreconditionFailed`; `V31_C79_R2_IMMUTABLE_ENVELOPE_REAL_PASS`; `V31_C79_R2_CANARY_CLEANUP_ZERO=true` após DELETE apenas da chave sintética verificada e GET readback `None`.
- O workflow temporário foi **REMOVIDO** da `main` após sucesso, commit `7eb13c1c3447c0ae164d16d2b62278b098cfc92f`. Nenhum snapshot, pointer, feed, blog, outra Cloudflare ou produto foi alterado.

## C79.3 — verificação independente Cloudflare após canário
- Conexão na conta Cloudflare oficial `adeiltonrib27@gmail.com`, account `ebb8d5b4cf9a2cb850c6d8051bd2661f`: GET bucket `v31-editorial-shopee` e D1 `v31-universal-ready-safe` **success=true**, identidade certa.
- Consulta SQL D1 somente SELECT retornou `leases=0`, `jobs=0`, `evidence=0`, `budgets=0`. C79 não implantou READY real no D1, não conectou writers, não publicou nem alterou artigos. A limpeza do canário R2 é confirmada por GET da chave sintética no próprio run.

## Limites remanescentes (C80)
- Adaptador R2 **funciona no bucket real** e é confiável para transporte imutável, mas ainda não é invocado pelos writers nem integrado ao D1 real; C77/C78/C79 são componentes SAFE verificados com canário R2 de infraestrutura, não pipeline editorial E2E.
- Falta token `V31_D1_API_TOKEN` exclusivo e minimamente privilegiado no GitHub Environment `v31-editorial-safe` (C77 verificou ausência), sem mecanismo de administração de segredo na conexão GitHub atual. **Não criar um token Cloudflare se não puder guardar em GitHub com segurança.**
- Falta revisão independente real de provas/HTML/HMAC e fontes Firecrawl/SEO por cada SKU; binding `envelope → D1 READY/USED → DRAFT CMS` e canários de concorrência/rascunho. LIVE irrestrito NÃO autorizado; `articles:null` contínuo, `min_ready=3` é somente buffer.

**C79 SAFE CONCLUÍDA**: PR104/CI537 verde, R2 CAS verdadeiro PASS, objeto sintético removido, Cloudflare D1 oficial permanece vazio. `mutation_in_progress=false`, `remote_operation_in_progress=false`, sem rollback necessário; próxima fase C80 para integração autenticada D1 e sequência editorial protegida.
