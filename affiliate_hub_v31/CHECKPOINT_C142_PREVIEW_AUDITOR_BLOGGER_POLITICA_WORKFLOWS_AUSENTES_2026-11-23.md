# V31 C142 — PREVIEW de correção fail-closed da auditoria Blogger de políticas

**Data local:** 2026-11-23. Base `main` C141 após [checkpoint](CHECKPOINT_C141_PORTFOLIO_GLOBAL_28_BLOGGER_3_WP_50_SIMULACOES_748_TESTES_2026-11-23.md), 748 testes/50 simulações PASS, LIVE OFF.
**Objetivo:** recuperar a AUDITORIA do repo que falhou sem reativar writers de Loja descontinuados.

## Evidências reais e causa
- [GitHub Actions #45282364553](https://github.com/adelrib27/blogger-automation1/actions/runs/45282364553), `Blogger — Auditoria de Políticas`, concluiu **failure** porque `src/blogger_policy_repo_audit.py` exigia `.github/workflows/achados_casa_store_safe.yml` ausente. Antes da falha, `blogger_policy_guard_self_test.py` executou **13/13 PASS**.
- A leitura do conteúdo atual de `.github/workflows` e `src/blogger_policy_repo_audit.py` identificou **exatamente 2 caminhos faltantes entre 38 referências explícitas de workflows**: `achados_casa_store_safe.yml` e `achados_casa_store_autonomous.yml`, isto é, ambos os lados do mesmo par. Os demais caminhos exigidos existem.
- `casa_store_safe.yml` / `casa_store_autonomous.yml` presentes pertencem ao **WordPress Casa e Decoração**, NÃO são substitutos do Blogger Achados para Casa. `v31_c100_r2_exact_achados_casa.yml` é prévia R2 GET, não writer LIVE. Não remapear tais workflows.
- O Blogger Achados para Casa continua no inventário histórico do C141. Um workflow de Loja ausente **não significa que o blog foi desativado**, nem concede autorização para publicar/atualizar seus posts/Loja.

## Plano SAFE
1. Marcar explicitamente o par legado ausente como `RETIRED_PAIR_MUST_REMAIN_ABSENT_UNTIL_REAUDITED`. Exigir que AMBOS os arquivos permaneçam ausentes ou falhar quando qualquer um reaparecer (sem nova política/guard); não simplesmente remover auditoria geral.
2. Auditar todos os workflows ativos restantes normalmente com os mesmos requisitos Policy Guard, slots e schedules; não reduzir os checks de 18/18 históricos sem registrar a diferença.
3. Testar o par ausente, ressurreição de um ou dois arquivos, e execução do auditor completo offline; executar 50 simulações antes do run; CI/PR, auditor Action one-shot read-only real na main após merge.
4. Se auditor descobrir outras falhas reais, falhar fechado e documentar; não inventar workflow ausente nem ligar AUTO LIVE.
5. Retomar o V31 universal: inventário 28 históricos candidatos Blogger +3 WP, 24 pendentes de credenciais de outras contas, Ar-Condicionado excluído, Vida Pet como métodos universais apenas.

**Proibido:** edição de CMS/Loja, D1/R2/Shopee, publicação, reabilitação de cron ou alteração LIVE. Documentar evidência objetiva, sem confundir antigo workflow de Loja com publisher de artigos do motor universal.
