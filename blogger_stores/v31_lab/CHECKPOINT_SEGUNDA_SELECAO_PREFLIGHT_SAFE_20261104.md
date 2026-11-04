# Checkpoint — segunda seleção Shopee V31 real e preflight SAFE (LAB)

Data técnica: 2026-11-04 UTC. Escopo exclusivo: repositório `adelrib27/blogger-automation1`, branch `lab/v31r1-shopee-safe-20261103`, blog `4739187376492839837`, página LOJA `2446067640331732447`.

## Estado anterior preservado
- Primeira rotação Shopee V31 consolidada em `71d57ca75ec39bf5c67b2b36c7983196a7d8df37`.
- Ledger canônico: `blogger_stores/v31_lab/state/v31_rotation_ledger.json`, blob SHA `9f9c3b9baa65b4358a006a5343fd15356d7cdc27`, 1 operação `PERSISTED`.
- Histórico: `blogger_stores/v31_lab/state/v31_rotation_history.json`, blob SHA `de0f022994ca47f0b8316169815afe25722fdfff`, 2 registros (seed + primeira rotação).
- Nenhum novo registro foi acrescentado e nenhuma operação foi alterada nesta etapa.

## Segunda seleção Shopee V23 -> V31 em SAFE
- Workflow criado `.github/workflows/v31_lab_second_shopee_safe.yml`, restrito à branch LAB e trigger específico, permissões `contents:read`, sem cron e sem credenciais Blogger.
- Workflow: https://github.com/adelrib27/blogger-automation1/actions/runs/41840458808 — `completed/success`.
- Arquivo de entrada de rotação **CANÔNICO**: `blogger_stores/v31_lab/state/v31_rotation_history.json`. O workflow inicial que usava somente o seed NÃO foi modificado.
- Gates `PERSISTED` e identidade do blog OK; 6 testes do scanner + 14 testes do ledger OK; Shopee Affiliate API real autenticada, sem secrets expostos.
- Artefato: `v31-lab-second-shopee-safe-1`, artifact ID `13329560335`, retenção sete dias.
- Seleção `SAFE_READY`: 4 categorias, 16 itens únicos, 16 imagens e 16 links afiliados validados, todos os 16 em modo `new`.
- Sobreposição com os 16 produtos publicados: **zero**; itens novos vs. catálogo publicado: **16**; fallback: **0**.
- SHA-256 `selecao_shopee_v23_SECOND_REAL_SAFE.json`: `aea7191e1e4ea77581b33591e0e940f6bd582114c90ea2e457a7173faf3664b7`.
- `published=false`; nenhuma alteração em Blogger, ledger, histórico ou main.

## Segundo preflight READ-ONLY (HTML candidato)
- Workflow `.github/workflows/v31_lab_second_preflight_readonly.yml`, branch LAB, sem cron, `contents:read` + `actions:read`, sem Git push.
- Workflow: https://github.com/adelrib27/blogger-automation1/actions/runs/41841058542 — `completed/success`.
- Baixou apenas o artifact de seleção V31 do run `41840458808`, comprovou SHA-256 acima.
- `v31_lab_store_preflight.py` executou Blogger GET e renderização candidata; **não faz PUT**.
- Preflight: `V31_LAB_PREFLIGHT_SAFE_PASS`, `publication=false`, anterior com 16 cards, 16 links, 16 fotos; candidata com 16 cards, 16 links, 16 fotos e 4 categorias.
- Conferência adicional: IDs da página original idênticos ao último histórico publicado; IDs da candidata idênticos à segunda seleção, 16 únicos, disjuntos do catálogo anterior; marcadores V31 preservados.
- Fonte pública prévia: HTTP 200, 16 cards, 16 links, 16 fotos; `public_before.exact_catalog=false` no relatório genérico, não usar esta verificação prévia como prova exata da **candidata não publicada**.
- HTML original SHA-256: `6f3810a364fe2114865b96fa5f118c10495bfe39943406624710ac9aaf25f450`; HTML candidato SHA-256: `d33070c001281ed795489a032a504accfcab2b593010c1a9e8cf5bb86b8109b8`.
- Artefato: `v31-lab-second-preflight-readonly-1`, artifact ID `13328911297`, inclui `LOJA_ORIGINAL_BACKUP.html`, `LOJA_CANDIDATA_NAO_PUBLICAR.html`, `RELATORIO_SAFE.json`, retenção sete dias.
- Readback independente após o run: página Blogger continua com os 16 IDs da primeira rotação; ledger/histórico mantêm os blobs SHA citados.

## Estado rigoroso e próximas etapas
**VALIDADO EM SAFE:** segunda seleção REAL Shopee + preflight HTML da segunda vitrine com histórico consolidado e checks de não repetição, sem nenhuma publicação.

**NÃO VALIDADO:** segunda publicação LAB, aceitação pública da segunda candidata, persistência de uma **segunda** rotação, recuperação entre falhas e repetição diária, cron, replicação em novos blogs. Os flags do Runner permanecem `v31_enabled_for_new_blogs=false`, `daily_store_updates_enabled_by_runner=false` na última checagem anterior; reconfirmar ao retomar.

**Bloqueio:** não executar workflow de publicação ou primeiro workflow one-shot, não gravar ledger/history, não modificar main/produção, não habilitar cron sem autorização explícita. Antes de eventual publicação LAB, reconfirmar ao vivo Blogger GET/SHA, branch HEAD, origem/hashes dos artefatos e preservar backup; avaliar necessidade de snapshot durável antes da expiração de artefatos.
