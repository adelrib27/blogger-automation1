# Checkpoint V31 R1 LAB — prova real If-Match HTTP 412 em página sacrificial

Data 2026-11-04 (America/Recife). **VALIDADO NO BLOGGER REAL, APENAS NA PÁGINA SACRIFICIAL. NÃO HOUVE PUBLICAÇÃO DA SEGUNDA ROTAÇÃO.**

## Identidade
- Repo: `adelrib27/blogger-automation1`, branch LAB `lab/v31r1-shopee-safe-20261103`.
- Blogger LAB: `4739187376492839837`.
- LOJA (intocável para este teste): `2446067640331732447` — https://blog-teste-tema-worpress.blogspot.com/p/loja.html
- Página sacrificial criada **e mantida publicada para auditoria**: ID `3604438301826573070`, título `V31-IF-MATCH-TEST-SACRIFICIAL`, URL https://blog-teste-tema-worpress.blogspot.com/p/v31-if-match-test-sacrificial.html.
- A página sacrificial NÃO deve ser confundida com LOJA nem com as cinco páginas institucionais; não apagar automaticamente sem autorização.

## Execução independente
- GitHub Actions: https://github.com/adelrib27/blogger-automation1/actions/runs/41928309254 — `completed / success`; commit `c486ffd141cfce6109a24dff613b8c2f2f130494`.
- Workflow: `.github/workflows/v31_lab_if_match_live_probe_once.yml`, `contents: read`, sem push Git operacional, sem publicação da LOJA, sem cron ou upload de artefatos. Segredos OAuth consumidos pelo runtime do GitHub e não registrados.
- Script: `blogger_stores/src/v31_etag_sacrificial_live_once.py`; guardas contra repo/branch incorretos, tentativa reexecutada, e IDs institucionais; inventário inicial de 6 páginas live e 0 draft.
- Cinco casos unitários locais passaram (somente o novo script, não a regressão geral). O workflow executou **uma única** tentativa real `PUT blogger.pages.update` com `If-Match` forte propositalmente obsoleto, enviando conteúdo idêntico **apenas à página sacrificial**.
- Resultado observado pela API: **HTTP 412 Precondition Failed**.
- GET autenticado antes/depois: conteúdo SHA256 `2bf936e8b20033aeac9ee70b58d645237a8f3f5e1a8d4fede192d852f8956b5f` em ambos; ETag SHA256 `a2609f6384761da70a51de4364fb37fc757dc175ffcf2fc3c6c6909b2878295e` em ambos; updated igual `2026-11-04T19:47:35-03:00`.
- Marker em log: `V31_SACRIFICIAL_LIVE_IF_MATCH_RESULT`, `verdict=OBSERVED_412_AND_NO_CHANGE`; `V31_SINGLE_SACRIFICIAL_PROBE_COMPLETE`.
- Readback **independente via Blogger Bridge V2** após Actions confirmou página sacrificial `live` com 86 caracteres de HTML, ID/título/URL corretos e data de atualização idêntica.
- Isso prova **o comportamento observado nesta chamada real**, não uma garantia irrestrita para qualquer evento concorrente futuro. O controlador da publicação real ainda deve validar `If-Match` em cada PUT, com guarda CAS/backup.

## Estado canônico reconfirmado
- LOJA continua live com **16 cards, 16 imagens, 16 links** e updated `2026-11-03T22:19:09-03:00`. Nenhum PUT na LOJA.
- Ledger `blogger_stores/v31_lab/state/v31_rotation_ledger.json`, blob Git `8331d025d77fc752230eec71f6c7d8ba86ece5a5`: operações `PERSISTED + PLAN`, sem `prewriteClaim` ainda.
- Histórico `blogger_stores/v31_lab/state/v31_rotation_history.json`, blob Git `de0f022994ca47f0b8316169815afe25722fdfff`: 2 entradas.
- A reserva PLAN permanece a do commit `801381b4e0d2d23fa60f478da67b6dca6ec3df32`. Não criar outra.
- Runner `0.8-v31r1-lab`, `daily_store_updates_enabled_by_runner=false`, `v31_enabled_for_new_blogs=false`. Nenhum cron novo.
- Tema `TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB.xml` preservado.

## Próximo trabalho, sem repetição de testes
1. Conectar o claim Git real atômico e backup imutável ao publicador único, **preparando-o em SAFE sem gravar claim antecipadamente**; gravar claim apenas imediatamente antes de um PUT posteriormente autorizado. 
2. Obter aprovação específica antes de **qualquer PUT na LOJA**. Verificar novamente Blogger GET + HTML SHA original, ETag forte, Git HEAD e blobs, backup, cliente HTTP com If-Match; aplicar somente o candidato imutável uma vez, nunca repetir em timeout.
3. Confirmar readback, prova pública independente Cloudflare `PUBLIC_EXACT_PASS`; finalizar ledger+histórico num único commit CAS. Só depois ativar/validar atualização diária e replicação.
4. Página sacrificial fica preservada como evidência; exclusão posterior exige autorização específica. Limpeza dos artefatos antigos de GitHub Actions permanece separada.

**Estado: PROVA REAL DE IF-MATCH PASSOU; SEGUNDA ROTAÇÃO AINDA NÃO PUBLICADA; CLAIM OPERACIONAL NÃO GRAVADO.**
