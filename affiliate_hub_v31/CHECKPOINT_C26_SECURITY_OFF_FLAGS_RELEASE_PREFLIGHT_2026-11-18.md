# C26 — Segurança de Environment salva; flags de liberação verificadas OFF (18/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C26-SECURITY-SAVED-10FLAGS-OFF-PREFLIGHT-20261118`.

## Segurança comprovada

- O proprietário confirmou em 18/11/2026 o clique **Save protection rules** após adicionar a regra `main` em **Selected branches and tags**, com screenshot mostrando `1 branch and 0 tags allowed`, `main` apenas, bypass por administradores desmarcado. A evidência é da interface do usuário; a integração GitHub não pode inspecionar Environment administrativos.
- Credenciais Shopee rotacionadas e testadas: [C23 V31 Environment 44302637196](https://github.com/adelrib27/blogger-automation1/actions/runs/44302637196) e [C24 legacy repository 44303901286](https://github.com/adelrib27/blogger-automation1/actions/runs/44303901286), ambos `V31_SHOPEE_API_PASS`, **somente leitura**, sem expor segredo.
- [**Auditoria C26 de flags de release 44306017629**](https://github.com/adelrib27/blogger-automation1/actions/runs/44306017629), **SUCCESS**. Runner avaliou 10 repository variables e confirmou que nenhuma estava igual a `true`: `V31_EDITORIAL_C9_RELEASE_ENABLED`, `V31_EDITORIAL_PRODUCT_REUSE_ENABLED`, `V31_CASA_R2_FALLBACK_ENABLED`, `V31_OFICINA_R2_FALLBACK_ENABLED`, `V31_RADAR_R2_FALLBACK_ENABLED`, `V31_EDITORIAL_SHADOW_ENABLED`, `V31_EDITORIAL_CACHE_WARMUP_ENABLED`, `V31_EDITORIAL_CATALOG_REFRESH_ENABLED`, `V31_EDITORIAL_C21_AUDIT_ENABLED`, `V31_EDITORIAL_PLANNER_ENABLED`. Logs imprimiram **somente status OFF**, nunca valores secretos.
- Workflow e trigger de auditoria C26 foram removidos imediatamente após o sucesso. O Environment `v31-editorial-safe` **NÃO** foi acessado pela auditoria; o script só leu flags, respeitando `main`-only.

## Gate de release do PR #52

- PR #52 `DRAFT` durante o pré-flight; `mergeable=true`. Até a conclusão da auditoria, **150 arquivos** de alterações, todos na integração V31, três workflows originais WordPress, seis scripts WordPress de fila/generação/publicação e arquivos relacionados.
- Os patches de Casa/Oficina/Radar preservam scanner original quando o switch GLOBAL + SITE não é `true`; se a descoberta V31 falha, a publicação condicional em modo V31 é bloqueada. No legado, a publicação continua sob regras de antes. `PRODUCT_REUSE` ativa só se 3 switches simultâneos estiverem `true`.
- `v31_c8_cache_replenish_safe.yml` tem `main`-only, Environment protegido, confirmação manual na dispatch e limite de 1 a 3 mutation calls global por run, falha fecha sem novas tentativas após erro e R2 read-after-write de integridade. A prova de leitura Shopee não demonstra conversões; cada mutation precisa ser comprovada por resultado real e persistência de snapshot.
- [C25 CI 44305403819](https://github.com/adelrib27/blogger-automation1/actions/runs/44305403819) SUCCESS; [CI após limpar teste temporário 44306252175](https://github.com/adelrib27/blogger-automation1/actions/runs/44306252175) SUCCESS. Suite offline V31 e regressões Casa/Oficina/cross-blog.
- 203.649 produtos no último R2 real C22, 17 URLs reais. Casa 4/9, Oficina 4/6, Radar 8/15; **14 links de reserva a converter**, números sujeitos a atualização por auditoria real antes das mutations. Nenhum link inventado ou no lugar errado.
- **Nenhum LIVE V31** habilitado neste pré-flight; não alterar Pinterest nem páginas de loja. Ausência de vendas/comissões não bloqueia desenvolvimento nem testes.

[Issue #53](https://github.com/adelrib27/blogger-automation1/issues/53) acompanha os passos. **A próxima etapa técnica é release controlado do PR #52, com flags OFF, shadow R2 real, canário da primeira mutation com budget 1 e apenas depois incremento progressivo e testes editoriais.** Toda habilitação de publicação continua separada do rollout do catálogo.
