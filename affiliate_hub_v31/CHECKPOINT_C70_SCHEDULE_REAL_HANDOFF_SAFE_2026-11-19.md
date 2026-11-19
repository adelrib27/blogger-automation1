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
