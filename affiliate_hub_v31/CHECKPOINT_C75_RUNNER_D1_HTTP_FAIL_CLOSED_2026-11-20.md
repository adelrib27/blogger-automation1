# C75 — cliente HTTP Cloudflare D1 universal, SAFE e fail-closed (20/11/2026)

**PRÉVIA EM_ANDAMENTO antes de qualquer mudança de código.**

## Contexto confirmado

- C74 criou banco D1 **exclusivo** `v31-universal-ready-safe` UUID `9bfce7a4-6167-4bfc-a65e-a74c1a34f064` na **conta correta do R2 oficial** `ebb8d5b4cf9a2cb850c6d8051bd2661f` de `adeiltonrib27@gmail.com`; migration 4 tabelas e canários sintéticos PASS, limpeza 0.
- D1 antigo C73 pertence à conta diferente `adeiltonrml@gmail.com` e permanece intocado. Nenhum writer/cron usa ambos.
- Código atual `d1_universal_ready.py` usa runner injetado e SQL atômico com `RETURNING`; `final_fact_gate.py` é offline. Ausente executor HTTP autenticado que fixe conta/banco, valide envelope D1 e negue escrita por padrão.

## Plano SAFE desta fase

1. Criar `affiliate_hub_v31/d1_http_runner.py` para `POST /query` com `sql,params`, URL Cloudflare FIXA (sem host arbitrário), conta/DB V31 explicitamente verificados, token em segredo de runtime, limite de resposta/timeouts e sem log/token/SQL completo em erros.
2. Guardar escrita atrás de opt-in independente (construct + sinal operacional), bloquear consultas múltiplas, comentários SQL e declarações inesperadas; leitura SELECT permitida em modo preview, nenhuma rede ao importar o módulo.
3. Testar em fixtures HTTP mockadas: conta errada, banco errado, token/SQL inválido, query malformada, API 401/403, D1 subresult `success:false`, timeout, parâmetros, SELECT seguro e modo write explicitamente liberado. Não usar D1 real nem token GitHub.
4. PR/CI em branch nova, preservar `main` produtiva até CI; sem modificar Writers, Workers, Casa, Oficina, Radar, Vida Pet, R2 ou publicação LIVE.
5. Depois de CI, registrar PR+verificação em checkpoint, JSON e índice; integração de token de privilégios mínimos e canário D1 real ficam etapa posterior.

**Prévia:** nenhuma publicação/Firecrawl/Cloudflare API causada por C75 neste ponto. Estado `EM_ANDAMENTO`.

## C75.1 — Código, PR e CI SAFE concluídos

- [PR #100 MERGED](https://github.com/adelrib27/blogger-automation1/pull/100), merge SHA `5b08f064c141852ea20f62a9435887e3918d262f`; alterações apenas `affiliate_hub_v31/d1_http_runner.py`, `tests/test_c75_d1_http_runner.py` e `C75_HTTP_D1_RUNNER_GUIA.md`.
- [GitHub Actions #44761018643](https://github.com/adelrib27/blogger-automation1/actions/runs/44761018643) **SUCCESS**: `Ran 505 tests` / `OK`; Casa24/24, Oficina21/21, Radar15/15, cross-blog PASS. C75 acrescentou 11 testes offline HTTP simulado sobre C71 494 testes.
- Runner HTTPS tem endereço Cloudflare + conta/UUID oficial PINADOS (C74), SELECT por padrão, escrita exige dois opt-ins, valida envelope D1, 1 statement por consulta, `sql+params`, limites, timeout e nega redirects; nenhum token/SQL/resultado em mensagem de falha.
- **Nenhuma chamada D1 real deste novo cliente**, nenhum GitHub secret novo e nenhum writer/crons alterados; o D1 criado na conta correta na C74 permanece isolado. A integração efetiva da credencial e o canário end-to-end continuam PENDENTES.

**C75 entregue em SAFE**. Não confundir CI/testes HTTP mockados com prova de credencial GitHub ou integração na produção.
