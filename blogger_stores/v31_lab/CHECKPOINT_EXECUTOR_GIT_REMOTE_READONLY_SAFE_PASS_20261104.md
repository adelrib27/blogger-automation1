# Checkpoint V31 R1 LAB — executor Git remoto READ-ONLY + corrida sandbox aprovada

Data: 2026-11-04 (America/Recife). **VALIDADO SAFE READ-ONLY + GIT SANDBOX, NAO VALIDADO PARA ESCRITA/PUBLICACAO**.

## Identidade e escopo
- Repositório: `adelrib27/blogger-automation1` — branch exclusiva `lab/v31r1-shopee-safe-20261103`.
- Tema aprovado e inalterado: `TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB.xml`.
- Blogger LAB `4739187376492839837`; Page LOJA `2446067640331732447`; URL `https://blog-teste-tema-worpress.blogspot.com/p/loja.html`.
- Alterações restritas a arquivos novos na branch LAB, sem alterar `main`, tema, Runner, Blogger, Cloudflare, ledger/histórico, cron e blogs de produção.
- Branch LAB no momento do CI: `21d1b23d1af76ff9405150ea45a0957c2b65ed47`. Branch `main` é paralela e mutável; reconferir antes de qualquer uso.

## Novos componentes
- `blogger_stores/src/v31_git_reservation_executor_safe.py`: usa `git ls-remote` somente leitura no remote GitHub, compara HEAD com checkout, autentica bytes/blobs Git por `git show HEAD:path` / SHA-1 Git, valida identidade exata LAB, seleção Shopee, HTML original/candidato e produz proposta de reserva `PLAN` **somente em relatório fora do repositório**.
- O mesmo script testa um conflito de `git push` não forçado entre dois clones de um `git init --bare` temporário criado exclusivamente no runner CI; só um commit pode vencer. Nenhum `git push` aponta para o remote GitHub.
- `blogger_stores/tests/v31_git_executor/test_v31_git_reservation_executor_safe.py`: 14 testes com fake checkout/remote; recusas para HEAD divergente, origem errada, SHA incorreto, estado sujo, arquivo faltante, regravação de relatório e comandos Git não permitidos.
- `.github/workflows/v31_lab_git_reservation_executor_safe.yml`: `contents: read`, `actions: read`, sem credenciais persistidas, sem Blogger PUT, cron, Git push remoto ou commit operacional. Reusa seleção e preflight imutáveis de 4/11 com hashes fixados.
- Commits de criação: executor `954fbbeca63f388d1c458cb4825026a0e85326b6`, testes `de3a02e317b8a4d96ba4839f1f3c52c70a02165f`, workflow `21d1b23d1af76ff9405150ea45a0957c2b65ed47`.

## Prova independente em GitHub Actions
- https://github.com/adelrib27/blogger-automation1/actions/runs/41902007643 — **completed / success**.
- **119/119 testes PASS**: 14 executor Git + 36 CAS multi-ciclo + 26 recuperação segundo ciclo + 14 ledger + 29 atomic.
- PASS no HEAD remoto exato, SHA-256 da segunda seleção `aea7191e1e4ea77581b33591e0e940f6bd582114c90ea2e457a7173faf3664b7`, HTML original `6f3810a364fe2114865b96fa5f118c10495bfe39943406624710ac9aaf25f450`, HTML candidato `d33070c001281ed795489a032a504accfcab2b593010c1a9e8cf5bb86b8109b8`.
- PASS da colisão de dois `push` não forçados em **Git local isolado**: primeiro aceito; segundo rejeitado; histórico intacto.
- Artefato do CI: `v31-lab-git-remote-readonly-safe-1` (ID `13359376017`), digest `sha256:a0224b79cdd4774e97028035350f24a8ccc1591bdfa342359ee39d206f3c8523`.
- Arquivo interno `V31_GIT_RESERVATION_EXECUTOR_SAFE.json`, SHA-256 `d62b3d1bf59f9d8803947476dddefbaf7ecf22c0d5a92cb95849c29c42d7a265`. O relatório marca explicitamente `git_reservation_committed=false`, `blogger_readback_live=false`, `git_remote_write_allowed=false`, `blogger_put_allowed=false`, `cron_allowed=false`.

## Estado real reconfirmado depois da execução
- Blogger Page `live` atualizado em `2026-11-03T22:19:09-03:00`, 16 cards/16 fotos/16 links, sem publicação desta etapa.
- Ledger `blogger_stores/v31_lab/state/v31_rotation_ledger.json`: blob `9f9c3b9baa65b4358a006a5343fd15356d7cdc27` (1 operação `PERSISTED`).
- Histórico `blogger_stores/v31_lab/state/v31_rotation_history.json`: blob `de0f022994ca47f0b8316169815afe25722fdfff` (2 entradas).
- Runner `0.8-v31r1-lab`: `daily_store_updates_enabled_by_runner=false`, `v31_enabled_for_new_blogs=false`.

## O que ainda FALTA
1. Executor real de reserva remota: autenticação, gate explícito de write LAB, commit de uma única reserva `PLAN` com non-force e prova de readback remoto. **Nenhuma reserva foi gravada neste marco.**
2. Ler novamente a página Blogger autenticada imediatamente antes de qualquer PUT e comparar HTML ao backup aprovado. Revalidar após PUT; se candidato já estiver no Blogger, NUNCA repetir PUT.
3. Prova pública Cloudflare `PUBLIC_EXACT_PASS` da SEGUNDA publicação, seguida de commit atômico dos dois JSON canônicos e validação de idempotência.
4. Somente então validar agendamento GitHub Actions para LOJA V31 em LAB; preservar motor comercial WordPress/Blogger existente; não recriar scanner nem alterar tema.
5. Replicação E2E de novo blog V31, retirada segura do fallback V20 legado, auditoria políticas e instalador portátil ainda pendentes.

**Este checkpoint NÃO autoriza reserva Git remota, Blogger PUT, cron ou mudanças de produção.**
