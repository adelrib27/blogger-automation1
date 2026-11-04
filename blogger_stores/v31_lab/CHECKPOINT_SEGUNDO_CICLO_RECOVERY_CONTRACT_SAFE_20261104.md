# Checkpoint V31 LAB — contrato SAFE de retomada do segundo ciclo (2026-11-04)

## Direção preservada
- Tema selecionado pelo proprietário: **TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB**.
- Arquivo V6 corrigido entregue neste projeto é somente referência histórica; não substituir a V31.
- V20 legado defeituoso não deve ser promovido como rollback; nenhuma retirada de código/tema foi executada nesta etapa.
- Escopo único: repositório `adelrib27/blogger-automation1`, branch `lab/v31r1-shopee-safe-20261103`, blog LAB `4739187376492839837`, página LOJA `2446067640331732447`.

## Baseline LIVE conferido antes da mudança
- Blogger LOJA LIVE, `updated_at=2026-11-03T22:19:09-03:00`, 16 cards / 16 fotos / 16 links originais.
- Ledger `blogger_stores/v31_lab/state/v31_rotation_ledger.json`: blob `9f9c3b9baa65b4358a006a5343fd15356d7cdc27`, 1 operação `PERSISTED`.
- Histórico `blogger_stores/v31_lab/state/v31_rotation_history.json`: blob `de0f022994ca47f0b8316169815afe25722fdfff`, 2 entradas.
- Segunda seleção Shopee de 16 produtos novos, zero sobreposição, SAFE SUCCESS `41840458808`; preflight HTML candidato READ-ONLY SUCCESS `41841058542`. **Ainda não publicados.**
- Runner `0.8-v31r1-lab`: `daily_store_updates_enabled_by_runner=false`, `v31_enabled_for_new_blogs=false`.

## Evolução executada — SOMENTE LAB, sem publicar
- `blogger_stores/v31_core/v31_second_resume_safe.py`: classificador **puro, sem IO**, para determinar com base no ledger/histórico e SHA observado se (a) há plano pré-PUT, (b) Blogger pode ter aceitado PUT antes da falha do job, (c) falta verificação pública, (d) falta finalizar o par atômico, ou (e) a operação já está persistida.
- Nunca emite autorização para PUT, commit de histórico ou cron; qualquer SHA ou histórico divergente bloqueia a retomada.
- `blogger_stores/tests/v31_second_recovery/test_v31_second_resume_safe.py`: 26 cenários offline com *fixtures sintéticas* de primeira/segunda rotação, inclusive repetição, falha após PUT, HTTP 429, histórico antecipado, operação concorrente e estado divergente.
- Testes locais: **26/26 PASS** usando cópia anterior do módulo de ledger; isto **não substitui** CI contra o código e estado canônico atuais.
- GitHub hashes conferidos com arquivos locais: `v31_second_resume_safe.py` blob `d1a417224013289bf9c4f387f904b61cc15a2e96`; teste blob `a75faa3ffa1f32ef1aadac1f313f46d821118efa`.
- Workflow criado `.github/workflows/v31_lab_second_recovery_contract_safe.yml`: `contents: read`, `persist-credentials: false`, sem segredos, sem rede, sem Blogger PUT, sem Git push, sem cron. Executa 26 novos testes, regressão do ledger e do finalizador atômico, e confere estado canônico.
- GitHub run: https://github.com/adelrib27/blogger-automation1/actions/runs/41863083640 — **QUEUED/PENDENTE DE CI NA CRIAÇÃO DESTE CHECKPOINT**. Não declarar CI PASS sem consultar resultado final.

## Limites ainda não resolvidos
- Este classificador é um **gate de recuperação em SAFE**, não um publicador nem um controlador transacional completo.
- O reconciliador anterior `v31_atomic_rotation.reconcile` e `v31_lab_atomic_finalize.py` estão fixados na primeira rotação; não reutilizá-los diretamente na segunda.
- Ainda faltam CAS real de reserva pré-PUT, simulação de crash antes/depois do commit Git, avaliação de concorrência entre jobs e orquestração segura para segunda rotação.
- A segunda publicação LAB, prova pública da candidata, persistência da segunda rotação, cron diário e replicação para outros blogs **não foram executados/validados**.
- Próxima ação: conferir CI `41863083640`; se PASS, criar e validar em SAFE o contrato transacional multi-ciclo, sem modificar `main` ou publicar sem autorização explícita.

## Invariantes
- Nenhum arquivo de `main`, Blogger tema, página LOJA, 18 blogs legados, ledger/histórico operacionais ou Cloudflare foi alterado por esta etapa.
- Fail-closed; readback Blogger após falha de workflow deve ser tratado antes de qualquer tentativa de republicação; nunca inferir PUT falho de um job GitHub `failure`.

## Artefatos temporarios (confirmados via metadados GitHub)
- Segunda selecao: run `41840458808`, artifact `13329560335`, digest ZIP `sha256:70653f59331a8bee05d63d2e4b1844b905d0d6a722fd7243cf6d2161d20b1c97`, expira **2026-11-11 13:43:18 UTC**.
- Preflight segundo HTML: run `41841058542`, artifact `13328911297`, digest ZIP `sha256:95553291b569c20d601157522bceb961d45879d18fe23d9d68712f0d089ed191`, expira **2026-11-11 13:46:02 UTC**.
- Os SHA-256 dos arquivos internos e a origem devem ser revalidados antes de qualquer utilizacao. Artefato expirar nao autoriza repetir selecao nem publicacao. Snapshot duravel ainda nao foi feito nesta etapa.
