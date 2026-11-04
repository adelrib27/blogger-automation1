# Checkpoint V31 — Verificador Público e Ledger SAFE

Data técnica: 2026-11-03 (America/Recife) / 2026-11-04 UTC.

## Estado real no LAB
- Runner ao vivo: `0.8-v31r1-lab`; flags `v31_enabled_for_new_blogs=false`, `daily_store_updates_enabled_by_runner=false`.
- Blogger Bridge: blog `4739187376492839837`, página `2446067640331732447`, atualizado `2026-11-03T22:19:09-03:00` com 16 cards únicos, 16 fotos e 16 links afiliados.
- Publicação Shopee V23 → V31: efetivamente realizada e confirmada por leitura do Blogger Bridge e publicação pública independente; job mutador #41753180692 terminou falha HTTP 429 **depois do PUT**.
- Branch isolada: `lab/v31r1-shopee-safe-20261103`. Nenhum commit em `main` ou alteração em blogs de produção nesta etapa.

## Trabalho feito neste checkpoint
1. Verificador público estritamente READ-ONLY: `blogger_stores/src/v31_public_verify_readonly.py`, workflow `.github/workflows/v31_lab_public_verify_readonly.yml`; URL canônica, comparação exata de IDs, fotos, links, categorias e Tema V31 R1, HTTP 429 → `PUBLIC_PENDING_THROTTLED`, sem escrita nem cron. 14 testes locais passaram. Push de trigger `31d70de9c36be7583db5f888a91965619b7f1d3f`. **Resultado da execução GitHub não verificado** por limitação na consulta de runs; não marcar como PASS.
2. Ledger de rotação idempotente e parametrizado: `blogger_stores/v31_core/v31_rotation_ledger.py`, testes em `blogger_stores/tests/v31_ledger/`; 14 testes locais passaram. Estados `PLAN → PUBLISHED_PENDING_PUBLIC → PUBLIC_VERIFIED → PERSISTED`. Operação pendente bloqueia nova publicação, histórico só é append após prova pública, proteção contra duplicação. **Ainda não integrado ao motor diário**.
3. Snapshot fail-closed pendente em `blogger_stores/v31_lab/state/LAB_FIRST_SHOPEE_PENDING_AUTOMATED_VERIFICATION_20261104.json`; não equivale a persistência final de rotação. SHA da seleção `46ef8a293875720f036d90430d1e57c862277b42bde966fbf34b15f9d2cb6c0c`.

## Bloqueios para avançar com segurança
- Confirmar um run real da verificação pública read-only em GitHub Actions e inspecionar relatório; avaliar 429 de URL canônica.
- Autenticar as provas, integrar estado/controle transacional ao orquestrador e validar commit atômico do histórico com concorrência, recuperação e renovação da seleção Shopee.
- Só então ativar cron diário em LAB. Provisionamento universal V31 permanece pendente de projeto/testes próprios.
- Proibido rerodar a publicação #41753180692, aplicar rollback cego, alterar `main`, outros blogs ou ativar flags sem nova validação.