# C70 — verificação schedule real e reparo SAFE da fila universal (19/11/2026)

**ESTADO: EM_ANDAMENTO / PRÉVIA GRAVADA ANTES DE QUALQUER MUDANÇA DE CÓDIGO.**

## Escopo e regras
Retomada solicitada a partir de `main`, com leitura em ordem de `V31_CONTINUAR_AQUI.md`, `CONTINUIDADE_ESTADO.json` e checkpoint C69. Objetivo: investigar execução real `event=schedule`, corrigir de modo fail-closed apenas defeitos SAFE comprovados, validar testes e preservar estado Blogger, WordPress e `vida_pet_pratica/`. **NÃO publicar LIVE; NÃO repetir conversão Shopee já confirmada; NÃO ativar writer via Evidence/READY C69; NÃO copiar dados pet-specific.**

## Pré-auditoria real GitHub (antes de mutations)
- `main` HEAD observado: `9ef571d27874452d5c44b153e186bce4f72d2613` (C69 concluída).
- CI C69 [#44598880655](https://github.com/adelrib27/blogger-automation1/actions/runs/44598880655): SUCCESS, 467 testes V31 e legados PASS. Motor `universal_evidence_ready.py` e cache SQLite seguem **offline**, não ligados a publicadores.
- **NOVA evidência V31 em 19/11:** [GitHub Actions #44600350780](https://github.com/adelrib27/blogger-automation1/actions/runs/44600350780), workflow `v31_universal_request_queue_daily.yml`, evento **`schedule`** real, às `2026-11-19T19:38:04Z` / 16h38 Recife, estado `failure`. Não aguardar cegamente 20/11 para diagnosticar este fluxo.
- Log do job `135829735081`: 467 testes PASS. Preview: `conversion_candidates=3`, `requests_active=2`, `converted=0`, `publication_calls=0`. Etapa EXECUTE: `converted=3`, `shopee_mutation_attempts=3`, `r2_snapshot_saved_and_verified=true`, `publication_calls=0`, modo `SITE_REQUEST_QUEUE_LIVE_CACHE_ONLY`. **Efeito confirmado: três links comerciais convertidos/cache R2, zero posts. Não repetir etapa EXECUTE sem nova prova de necessidade.**
- Etapa seguinte `python -m affiliate_hub_v31.handoff_dispatch` falhou fechada com `V31_C37_PRIVATE_EDITORIAL_HANDOFF_FAILED_HandoffError` antes da execução `--execute`. Causa exata ainda não determinada. Não declarar envelopes materializados.
- Cron YAML configurado: fila `47 11 * * *` (08h47 Recife), Blogger `18 12 * * *` (09h18), WordPress `41 12 * * *` (09h41). Disparo da fila ocorreu com atraso grande; cron UTC não foi alterado.
- A pesquisa de runs recentes ainda **não encontrou** eventos `schedule` pós-C69 para Blogger e WordPress V31. A verificação read-only de 20/11 às 10h10 Recife permanece útil para avaliar os três separadamente.
- Nenhuma mudança de blog, WordPress, R2 ou LIVE efetuada por esta retomada. C67 WordPress Casa #305 foi autorizado e publicado anteriormente uma única vez: não republicar.

## Plano SAFE
1. Registrar esta prévia no GitHub e atualizar estado JSON C70 `EM_ANDAMENTO`.
2. Investigar código `handoff_dispatch` e os testes; distinguir dependência de configuração/dados vs. bug. Se necessário, propor patch isolado e testes offline **sem chamar Shopee/CMS**.
3. Avaliar gates factuais pós-IA e contrato D1/locks em modo offline com testes; sem Firecrawl real enquanto saldo da **mesma chave** não for comprovado.
4. Registrar cada commit/PR/CI no checkpoint. Manter C70 aberto se a prova de schedule Blogger/WordPress ou handoff remoto ainda faltar.
5. Em 20/11, leitura específica `event=schedule` dos três workflows e resultado no destino; a checagem já agendada em C65 é **somente leitura**.

## Limites operacionais
`min_ready=3` do C69 não é teto total; pedidos `articles:null` continuam. `publish_enabled=false` impede LIVE irrestrito. Há credenciais em Actions, não trazer segredo aos checkpoints.

## C70.1 — causa identificada, patch + CI + merge
- Causa-raiz de `HandoffError` identificada no código: `site_requests.d` contém `articles:null` para pedidos contínuos C61/C65; `handoff_dispatch.py` passava o valor diretamente ao `plan_editorial_handoff()`, que exige inteiro 1..24; portanto erro de contrato `invalid_article_count` antes da gravação de envelopes. O log de produção suprimia o detalhe e registrava `HandoffError` genérico; diagnóstico por inspeção com testes.
- [PR #98](https://github.com/adelrib27/blogger-automation1/pull/98) **MERGED** na main, merge SHA `252a38084f8498bd9cc3e71557ceed1d606695a5`. Corrigiu **somente** `affiliate_hub_v31/handoff_dispatch.py` e novo `tests/test_c70_handoff_continuous.py`: `articles:null` vira `MAX_ARTICLES_PER_BATCH=24` **apenas na chamada de planejamento**, sem editar pedido original ou limitar total; pedidos finitos mantêm sua quantidade. Evita afrouxar gates do catálogo, não toca CMS, Vida Pet ou workflow.
- [CI #44606961972](https://github.com/adelrib27/blogger-automation1/actions/runs/44606961972) **SUCCESS**: 471 testes V31 PASS (4 novos), Casa 24/24, Oficina 21/21, Radar 15/15 e crossblog. Evidência validada no log `Ran 471 tests ... OK`.
- **Próximo ensaio SAFE:** canário temporário por push, executar `handoff_dispatch` **sem `--execute`**, apenas leitura do R2 real, sem Shopee/API de publicação/Writer; após capturar resultado, remover workflow temporário. CI offline não é, isoladamente, prova de handoff produtivo.

## C70.2 — validação independente no R2 REAL, somente leitura
- Após o PR #98, criado canário efêmero `.github/workflows/v31_c70_TEMP_handoff_preview_readonly.yml` com `push` estritamente preso ao commit de criação; sem `--execute`, sem Shopee ou CMS.
- [Action #44607319448](https://github.com/adelrib27/blogger-automation1/actions/runs/44607319448) **SUCCESS**. Log: 4 testes C70 PASS, `V31_C37_PRIVATE_EDITORIAL_HANDOFF_PASS`; payload resumido `mode=DRY_RUN`, `requests_evaluated=2`, `ready_review_jobs=10`, `conversion_needed=30` (posições dentre até 24 por pedido, NÃO conversões adicionais), `private_envelopes_saved=0`, `catalog_r2_writes=0`, `publication_calls=0`. Confirmada causa corrigida na leitura R2 de produção sem efeitos externos.
- **Ação SAFE seguinte autorizada pelo escopo:** completar *somente* a etapa lateral já prevista no cron e que falhou: materializar os dois envelopes privados `REVIEW_REQUIRED` no R2 e conferir leitura, sem nova execução do `site_request_queue --execute`, sem Shopee e sem CMS. Gate de exatos dois pedidos reais cadastrados e invariantes de campanha/sem LIVE. Reverter caminho TEMP depois.
