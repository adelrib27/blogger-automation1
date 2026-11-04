# Checkpoint — Primeira rotação Shopee V31 consolidada atomicamente no LAB

## Estado validado
- Blog LAB `4739187376492839837`; página LOJA `2446067640331732447`.
- Runner `0.8-v31r1-lab`. Flags `v31_enabled_for_new_blogs=false`, `daily_store_updates_enabled_by_runner=false`.
- Página Blogger Bridge: última alteração `2026-11-03T22:19:09-03:00`; 16 cards, 16 imagens, 16 links. **Nenhuma nova publicação foi executada pela consolidação.**

## Evidência GitHub e Cloudflare
- Workflow de contrato SAFE: [run 41778317763](https://github.com/adelrib27/blogger-automation1/actions/runs/41778317763), `SUCCESS`: **29 testes novos + 14 testes ledger** em Python 3.12.
- Workflow de consolidação one-shot: [run 41778466836](https://github.com/adelrib27/blogger-automation1/actions/runs/41778466836), `SUCCESS`, job `126404237866`.
- Testes do workflow LIVE: 29 (reconciliação e git race), 14 (ledger), 22 (Cloudflare), 14 (HTML V31) = **79 testes** em Python 3.12.
- Prova pública fresca, executada antes da gravação: `PUBLIC_EXACT_PASS`, HTTP 200, 16 cards, 16 fotos, 16 links, 4 categorias, `publication_attempted=false`.
- SHA-256 da seleção: `46ef8a293875720f036d90430d1e57c862277b42bde966fbf34b15f9d2cb6c0c`.
- Prova original autenticada: run `41769090187`, artifact `13294391153`, hash conferido. O orquestrador verificou a execução original na API GitHub e conferiu o digest de artifact, antes de gerar o par de arquivos.

## Transação de histórico
- Commit atômico **`71d57ca75ec39bf5c67b2b36c7983196a7d8df37`**: https://github.com/adelrib27/blogger-automation1/commit/71d57ca75ec39bf5c67b2b36c7983196a7d8df37
- O diff do commit contém **exatamente dois arquivos criados**:
  1. `blogger_stores/v31_lab/state/v31_rotation_ledger.json`
  2. `blogger_stores/v31_lab/state/v31_rotation_history.json`
- Estado canônico: `PERSISTED` para a operação `8babc29b6609e369d10f674ef5730719b66e8dd2ca51e56a76d6c1f750e0fcdc`.
- Histórico canônico tem **2 registros**, o catálogo inicial seed e a rotação Shopee publicada. Sem operações duplicadas.
- Os arquivos históricos originais **não foram sobrescritos**:
  - `blogger_stores/v31_lab/v31_lab_rotation_seed.json` (1 registro de origem)
  - `blogger_stores/v31_lab/state/LAB_FIRST_SHOPEE_PENDING_AUTOMATED_VERIFICATION_20261104.json` (checkpoint imutável de antes da confirmação pública)
- Push realizado **sem force**, com teste local de concorrência: qualquer commit concorrente gera recusa de não-fast-forward, evitando sobrescrever trabalho paralelo.

## Declaração de validação
**VALIDADO NO LAB:** seleção real, primeira publicação, verificação pública automatizada Cloudflare/GitHub e persistência atômica do histórico.

**AINDA PENDENTE:** segunda seleção real e rotação completa recorrente, garantia de recuperação com operação em andamento/reinício, scheduler diário e provisionamento automático V31 em novo blog. Não ativar flags nem cron antes destes testes.

## Engenharia portátil
O reconciliador recebe políticas de blog/branch e identificadores do artefato por arquivo de configuração; não depende de caminhos de Windows. O fluxo one-shot está restrito ao Environment `v31-lab`; nenhuma edição no `main` ou nos blogs de produção. Este checkpoint não deve ser interpretado como aprovação de operação autônoma recorrente.
