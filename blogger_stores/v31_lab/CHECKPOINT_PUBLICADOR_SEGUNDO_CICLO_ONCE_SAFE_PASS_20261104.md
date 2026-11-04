# Checkpoint V31 R1 LAB — publicador único do segundo ciclo: contrato SAFE PASS

Data: **2026-11-04, America/Recife**. Status: **VALIDADO EM SAFE + BLOGGER SIMULADO, NÃO PUBLICADO**.

## Identidade fixa e limites
- GitHub: `adelrib27/blogger-automation1`.
- Branch LAB: `lab/v31r1-shopee-safe-20261103`.
- Blogger LAB: `4739187376492839837`; Page LOJA `2446067640331732447`; URL `https://blog-teste-tema-worpress.blogspot.com/p/loja.html`.
- Tema aprovado: `TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB.xml` (não alterado).
- Reserva Git **real** do segundo ciclo: commit `801381b4e0d2d23fa60f478da67b6dca6ec3df32`, operação `2ab915f6079855824374fd9577411783bf6d8e5c2bca7eb36a4aa8e1d08d5a93`; **NÃO criar segunda reserva**.
- Ledger `blogger_stores/v31_lab/state/v31_rotation_ledger.json` blob `8331d025d77fc752230eec71f6c7d8ba86ece5a5`; statuses `PERSISTED`, `PLAN`.
- Histórico `blogger_stores/v31_lab/state/v31_rotation_history.json` blob `de0f022994ca47f0b8316169815afe25722fdfff`; duas entradas.
- Nenhum Blogger PUT, Cloudflare publicação, alteração de tema, cron V31 ou mudança em blogs de produção nesta etapa.

## Implementação adicionada na branch LAB
- `blogger_stores/src/v31_second_publish_once_lab.py`: biblioteca sem CLI `--apply`. Exige GET autenticado do Blogger com identidade, título, URL, ETag e `updated`; chama o gate imutável dos artefatos do segundo ciclo; faz backup local exclusivo e lê de volta; requer **aprovação externa específica**, comprovação externa de backup durável e **claim remoto durável/atômico de tentativa única** antes de permitir um PUT; verifica HEAD/blobs Git de novo e ETag/HTML do Blogger imediatamente antes do claim. Simula o fluxo de `If-Match` e readback após uma única tentativa. Em erro/timeout, NUNCA repetir PUT ou fazer rollback cego. Retorna status pós-readback sem marcar histórico como publicado.
- `blogger_stores/tests/v31_second_once/test_v31_second_publish_once_lab.py`: **30 testes** com FakeBlogger utilizando os HTMLs oficiais arquivados. Testa recusa de permissão, ETag ausente/divergente, Git remoto divergente, backup não atestado, claim ausente/repetido, candidato já aplicado sem repetir PUT e exceção de Blogger depois de uma única tentativa.
- `.github/workflows/v31_lab_second_publish_once_contract_safe.yml`: CI `push` apenas branch LAB para os três arquivos novos; `contents: read`, `actions: read`, checkout `persist-credentials: false`, sem secrets Blogger, sem PUT, sem Git push, sem cron, sem upload de artefato. Reobtém seleção/HTML com hash pinado; testa ancestralidade real da reserva, remote HEAD e estado canônico.
- Commits: módulo `08c8e892b6dcdc1a4ab337d139cf18372d27242e`; testes `e6d9f6d40d17df0932c918f49d8d9bc24c246123`; workflow `1dbf849edda70e194c96f28b05d9102dad5f1aae`.

## Evidência CI independente
- GitHub Actions https://github.com/adelrib27/blogger-automation1/actions/runs/41919684261 — **completed / success**, commit `1dbf849edda70e194c96f28b05d9102dad5f1aae`.
- **209/209 testes PASS**: 30 novo executor simulado + 32 gate prewrite + 28 Git write-gate + 14 executor Git read-only + 36 CAS + 26 recovery + 14 ledger + 29 reconciliador.
- Logs: `V31_SECOND_ONCE_EXISTING_PLAN_CANONICAL_PASS`, `V31_SECOND_ONCE_REAL_ARTIFACT_GATE_ARCHIVED_PASS`, `V31_SECOND_ONCE_SAFE_PASS`.
- Artefatos originais checados: seleção SHA256 `aea7191e1e4ea77581b33591e0e940f6bd582114c90ea2e457a7173faf3664b7`, HTML original `6f3810a364fe2114865b96fa5f118c10495bfe39943406624710ac9aaf25f450`, HTML candidato `d33070c001281ed795489a032a504accfcab2b593010c1a9e8cf5bb86b8109b8`.
- Este CI usa HTML arquivado, não GET ao vivo do Blogger dentro do job. O teste de PUT foi exclusivamente com **FakeBlogger**.
- Nenhum artifact ZIP adicional foi enviado nesta execução SAFE, atendendo à preferência por reduzir armazenamento.

## Estado real reconfirmado após CI
- HEAD LAB: `1dbf849edda70e194c96f28b05d9102dad5f1aae` antes deste checkpoint.
- HEAD `main`: `e52e148582c45a74400397911e7457cefe0a6183` (atividade paralela; não tocar).
- Página Blogger `live`, `updated_at=2026-11-03T22:19:09-03:00`, 16 cards, 16 imagens, 16 links. **Segunda seleção não publicada**.
- Runner `0.8-v31r1-lab`, `daily_store_updates_enabled_by_runner=false`, `v31_enabled_for_new_blogs=false`.

## Próximo marco: integração operacional ainda NÃO validada
1. Implementar e testar a **atestação de backup pré-PUT remoto/durável** e a **reserva de tentativa única remota por CAS**. O módulo atual pressupõe esses serviços como callbacks externos; a simulação não comprova seu funcionamento real.
2. Confirmar em SAFE a compatibilidade real de `ETag/If-Match` com Google Blogger API; se não houver garantia verificável, falhar fechado e revisar o protocolo.
3. Criar workflow de execução excepcional com autorização específica para **um Blogger PUT apenas no LAB**, sem cron e sem alterar `main`; garantir que o workflow não dispare automaticamente.
4. **Pedir autorização separada do usuário para a publicação da segunda seleção.** A aprovação anterior do GitHub `PLAN` não autoriza Blogger PUT.
5. Após eventual PUT único: GET/readback autenticado; prova pública independente Cloudflare `PUBLIC_EXACT_PASS`; persistência atômica e idempotente do par ledger+histórico; somente depois validar agendamento diário da V31 e replicação universal.
6. A limpeza dos artefatos antigos de GitHub Actions ficará para auditoria de armazenamento **SAFE** separada, sem exclusões nesta etapa.

**Proibido interpretar este checkpoint como autorização de publicação, ativação de cron, remoção de artefatos antigos ou mudanças em produção.**
