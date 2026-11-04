# Checkpoint V31 R1 LAB — gate transacional de escrita PLAN, validado em Git isolado

Data: 2026-11-04 (America/Recife). Status: **VALIDADO EM SAFE/SANDBOX + CI. NÃO HOUVE RESERVA GIT OPERACIONAL NEM PUBLICAÇÃO**.

## Identidade
- GitHub: `adelrib27/blogger-automation1`, branch exclusiva `lab/v31r1-shopee-safe-20261103`.
- Blog LAB `4739187376492839837`, página LOJA `2446067640331732447`, URL `https://blog-teste-tema-worpress.blogspot.com/p/loja.html`.
- Tema escolhido `TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB.xml`: não alterado.
- `main` e os blogs de produção NÃO foram modificados.

## Implementado — exclusivamente arquivos novos da branch LAB
- `blogger_stores/src/v31_git_plan_write_gate.py`: executor de reserva `PLAN` de **um único arquivo ledger**. Revalida hashes imutáveis do plano, seleção, HTML original/candidato, blobs Git e transição `PERSISTED -> PLAN`; exige parent/head exato, clone limpo, origem e branch pinadas. Faz somente `git push` não forçado, verifica remoto depois, preserva bytes do histórico e nunca autoriza Blogger PUT ou cron.
- O modo `SANDBOX` só aceita repositório bare temporário e branch `sandbox-v31`; modo `LAB_REAL` depende de **workflow_dispatch manual em GitHub Actions**, identidade da branch e dupla autorização específica da operação/digest. Nenhum workflow que realize reserva real foi ativado nesta etapa.
- `blogger_stores/tests/v31_git_write_gate/test_v31_git_plan_write_gate.py`: 28 testes Git isolados, cobrindo uma reserva, concorrência, stale HEAD, hashes divergentes, alterações do ledger/histórico, replay, origem errada, bloqueios de autorização.
- `.github/workflows/v31_lab_git_plan_write_gate_safe.yml`: **somente push LAB, `contents: read`, checkout sem credenciais persistidas, sem GitHub push operacional, Blogger PUT, cron ou aprovação automática**. O job ainda compara artefatos reais da segunda seleção com SHA-256 e prepara um plano `PLAN` só em memória e relatório.

## Validação independente GitHub Actions
- Run https://github.com/adelrib27/blogger-automation1/actions/runs/41905280253 — `completed/success`, commit `ea85e788ae5ad899218f8542ad8c32a35dc25461`.
- **147/147 testes aprovados**: 28 novo gate Git + 14 executor read-only + 36 contrato CAS + 26 recuperação + 14 ledger + 29 reconciliador.
- Marcadores: `V31_GIT_PLAN_GATE_CANONICAL_BASELINE_PASS`, `V31_LAB_SECOND_REAL_ARTIFACT_PLAN_WRITE_GATE_SAFE_PASS`, `V31_LAB_GIT_PLAN_WRITE_GATE_SAFE_PASS`.
- Artefato de CI: `v31-lab-git-plan-write-gate-safe-1`, ID `13359598694`, digest `sha256:2ca43ddb17180405bbe62f653a1b572d0e2e682303f2514410ed03fdf27b7d85`.
- Hash de seleção: `aea7191e1e4ea77581b33591e0e940f6bd582114c90ea2e457a7173faf3664b7`.
- Hash do HTML original: `6f3810a364fe2114865b96fa5f118c10495bfe39943406624710ac9aaf25f450`.
- Hash do HTML candidato: `d33070c001281ed795489a032a504accfcab2b593010c1a9e8cf5bb86b8109b8`.
- `git_remote_reservation_committed=false`, `git_remote_write_allowed=false`, `blogger_put_allowed=false`, `cron_allowed=false`.

## Estado externo reconfirmado após CI
- Blogger LOJA: `live`, última edição `2026-11-03T22:19:09-03:00`, 16 cards, 16 imagens e 16 links. Nenhuma segunda rotação publicada.
- Ledger canônico `blogger_stores/v31_lab/state/v31_rotation_ledger.json`: blob `9f9c3b9baa65b4358a006a5343fd15356d7cdc27`, 1 operação `PERSISTED`.
- Histórico canônico `blogger_stores/v31_lab/state/v31_rotation_history.json`: blob `de0f022994ca47f0b8316169815afe25722fdfff`, 2 entradas.
- Runner `0.8-v31r1-lab`: `v31_enabled_for_new_blogs=false`, `daily_store_updates_enabled_by_runner=false`. Este indicador não representa desligamento dos cron preexistentes de outros blogs.

## Próximo marco obrigatório
1. Reconfirmar branch/head, identidade e estado do Blogger/ledger antes de qualquer escrita.
2. Obter **autorização explícita para realizar SOMENTE reserva `PLAN` no ledger da branch LAB**, com operação e digest corretos, e preparar um workflow manual separado sujeito a gate. Uma aprovação para reserva Git **não autoriza** Blogger PUT, mudança de tema, cron ou produção.
3. Após eventual reserva e readback de Git, exigir Blogger GET autenticado e hash exato antes de autorizar segunda publicação. Se o Blogger já tiver recebido o candidato, nunca repetir PUT.
4. Segunda publicação controlada apenas no LAB, prova pública Cloudflare `PUBLIC_EXACT_PASS`, ledger+histórico atualizados atomicamente, com autorização específica.
5. Somente depois, validar recorrência diária por GitHub Actions, sem reconstruir motor comercial WordPress/Blogger existente; replicação universal permanece pendente.

**Segurança: mantenha o Tema V31 R1; não reativar fallback V20 defeituoso. Este documento NÃO é autorização para escrita operacional nem publicação.**
