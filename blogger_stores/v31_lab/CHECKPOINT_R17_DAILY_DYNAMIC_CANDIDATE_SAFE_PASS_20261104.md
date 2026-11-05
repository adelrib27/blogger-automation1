# Blogger Automation V31 LAB — Checkpoint R17: candidato diário dinâmico em SAFE

Data local: **04/11/2026**, America/Recife. Resultado: **15/15 testes direcionados PASS em GitHub Actions, exclusivamente offline e sem publicação**.

## Continuidade e fonte de verdade
- Repo: `adelrib27/blogger-automation1`.
- Branch exclusiva LAB: `lab/v31r1-shopee-safe-20261103`.
- Parent R16 observado antes do commit: `befa7db2a006e3d18b1a2e47f5375dfa010dd47a`.
- Commit R17 com **somente três novos arquivos**: `2cca7fc2a11008c2de2dcc50bfab4c39adde66d7`.
- Runner: `0.8-v31r1-lab`; cron V31 e replicação V31 continuam desativados.
- Blogger LAB: blog `4739187376492839837`, Page LOJA `2446067640331732447`, `https://blog-teste-tema-worpress.blogspot.com/p/loja.html`.
- A página permaneceu `live`, com `updated_at=2026-11-04T21:06:56-03:00`, um par de marcadores V31 e 16 cards existentes.
- Ledger remoto: blob Git `fab8c013074053352d8d9b63aeb09c2f18e48823`, **2 operações PERSISTED**.
- Histórico remoto: blob Git `b21a55ae275bae677c116189e138e5053428c4ca`, **3 entradas**. Nenhum PLAN novo foi gravado.

## Mudança mínima R17

O scanner V31 existente já permite rotação de 14 dias e modos `new`, `fallback_older` e `carry_forward_last`. O contrato antigo de reserva multi-ciclo tinha uma proibição permanente de IDs repetidos em todo o histórico. A R17 adiciona um **adaptador puro e separado** para compatibilizar essas regras, sem modificar o contrato de segunda rotação previamente validado.

Arquivos novos:
1. `blogger_stores/src/v31_daily_candidate_contract_safe.py`: recebe seleção SAFE e HTML obtidos por fonte autenticada externa; usa gate diário R16, verificador da seleção Shopee, histórico de 14 dias, Policy Guard injetável, renderer V31 e `stage` do ledger. Rejeita entradas recentes rotuladas como novas, fallback incoerente, carry-forward indevido, vitrine inalterada, HTML divergente e operação pendente. Retorna somente candidato e PLAN **em memória**. Não tem CLI nem IO remoto.
2. `blogger_stores/tests/v31_daily_candidate/test_v31_daily_candidate_contract_safe.py`: 15 cenários sintéticos e direcionados de aceitação/bloqueio.
3. `.github/workflows/v31_lab_daily_dynamic_candidate_contract_safe.yml`: somente `push` com paths restritos, `contents: read`, checkout sem credenciais persistidas, sem acesso Shopee ou Blogger, sem cron, sem upload de artefatos e sem gravação de estado.

O novo contrato **não** substitui o publicador transacional. A aprovação SAFE não concede autorização de Git write, Blogger PUT, GitHub cron ou publicação.

## Evidências de execução

- GitHub Actions: https://github.com/adelrib27/blogger-automation1/actions/runs/41952772979
- Job: `contrato-dinamico-offline`, id `127000374817`, `completed/success`.
- Log: `Ran 15 tests in 0.027s`, `OK`.
- Marcador: `V31_LAB_DAILY_DYNAMIC_CANDIDATE_SAFE_PASS; blogger_put=false; git_write=false; cron=false; shopee_api=false; artifact_upload=false`.
- Auditoria de políticas independente, sem publicação: https://github.com/adelrib27/blogger-automation1/actions/runs/41952772623, `completed/success`.
- Readback GitHub do commit confirmou exatamente três caminhos; ledger/histórico mantiveram os blobs R14.
- Blogger Bridge V2 confirmou a Page LAB publicada sem nova atualização.

## Próxima etapa, sem atalhos

1. Em um **novo dia elegível** pela data America/Recife, executar o scanner SAFE real da Shopee com o histórico canônico de três entradas; o run R16 anterior executou `SKIP_ALREADY_UPDATED_TODAY` corretamente, portanto ainda **não** comprova esse cenário.
2. Integrar o novo pré-validador dinâmico no preflight com GET Blogger autenticado e comparação de hashes, sem gravação remota. Testar somente cenários faltantes.
3. Adaptar **separadamente** a transação multi-ciclo (CAS/backup+claim/If-Match/readback/prova pública/ledger+histórico), inclusive recuperação após falhas e retries idempotentes.
4. Apenas após SAFE e autorização específica para cada tipo de escrita, realizar ciclo controlado em LAB. Somente então considerar cron GitHub em branch padrão com isolamento dos outros blogs; a mera adição de `schedule` em branch LAB não o ativa.
5. Replicação universal V31 e limpeza de backups/artefatos continuam pendentes e sem autorização de escrita.

**Não repetir a segunda publicação da LOJA. Não migrar os 18 blogs legados. Não usar V20 defeituosa como fallback. Não alterar main, tema, produção, cron ou secrets.**
