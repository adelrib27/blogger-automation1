# Checkpoint V31 R1 LAB — Bridge de claim Git atômico e backup, SAFE direcionado

Data: 2026-11-04, America/Recife. **STATUS: código integrado por callbacks, VALIDADO EM SAFE / BACKEND SIMULADO; NÃO HOUVE CLAIM GIT OPERACIONAL OU BLOGGER PUT.**

## Identidades
- Repositório: `adelrib27/blogger-automation1`
- Branch exclusiva LAB: `lab/v31r1-shopee-safe-20261103`
- HEAD da aprovação no GitHub Actions: `553812a80ff69b47682ed03702e183f26c5df70d`
- Blogger LAB ID: `4739187376492839837`
- LOJA Page ID: `2446067640331732447`, URL `https://blog-teste-tema-worpress.blogspot.com/p/loja.html`
- Tema mantido: `TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB.xml`
- Reserva PLAN já efetivada (NÃO criar nova): commit `801381b4e0d2d23fa60f478da67b6dca6ec3df32`, operation `2ab915f6079855824374fd9577411783bf6d8e5c2bca7eb36a4aa8e1d08d5a93`.

## Mudanças feitas APENAS no código LAB
- `blogger_stores/v31_core/v31_atomic_git_claim_bridge_lab.py` — novo bridge implementando as duas interfaces já exigidas pelo publicador `v31_second_publish_once_lab.py`: `verify_durable_backup(manifest)` e `claim_attempt(request)`. Não reescreveu nem alterou o publicador original.
- A verificação de backup exige HTML original de hash aprovado lido de fonte arquivada independente, manifesto, HEAD e ETag consistentes. O escritor de claim exige autorização externa explícita: `armed=False` por padrão.
- Na simulação, o gateway prepara UM commit com **apenas** `v31_rotation_ledger.json` e `LOJA_ANTES_SEGUNDA_ROTACAO.html`; requer CAS non-force com parent HEAD antigo, confirma exatamente dois caminhos, lê as versões imutáveis no remoto após commit, valida o histórico inalterado, bloqueia segunda tentativa e HEAD divergente.
- `PinnedGitRemoteGateway` — interface concreta baseada em `git` para **futura execução manual autorizada** na branch LAB. Construção sem escrita; método de push é desativado por padrão (`write_enabled=False`). Não há CLI, workflow publicador, automação, tokens ou execução do escritor remoto nesta etapa.
- `blogger_stores/tests/v31_atomic_claim_bridge/test_v31_atomic_git_claim_bridge_lab.py` — apenas 14 testes de integração usando gateway simulado, HTML original imutável (SHA verificado) e validações de fail-closed.
- `.github/workflows/v31_lab_atomic_claim_bridge_targeted_safe.yml` — CI de apenas 14 testes, com `contents:read`, `actions:read`, sem credenciais persistidas, sem publicação, sem Git push operacional, sem cron e sem artifact upload.
- Commits do código, teste e workflow: `c207c6f0fe1c43acc73b23fcd6eb658ed32a8f17`, `bab5dc129b80cee01cd82753495b954e4fa12f3c`, `553812a80ff69b47682ed03702e183f26c5df70d`.

## Evidência de teste direcionado
- GitHub Actions: https://github.com/adelrib27/blogger-automation1/actions/runs/41931929220 — **completed/success**.
- **14/14 casos aprovados**. Marcador `V31_ATOMIC_CLAIM_BRIDGE_TARGETED_SAFE_PASS`.
- O workflow recuperou o HTML original do artefato anterior de leitura (run `41841058542`) e confirmou SHA-256 `6f3810a364fe2114865b96fa5f118c10495bfe39943406624710ac9aaf25f450`.
- Não repetiu os 257 testes antigos nem fez upload de novo artefato no Actions.

## Estado AO VIVO reconfirmado após CI (antes deste checkpoint)
- Ledger Git blob `8331d025d77fc752230eec71f6c7d8ba86ece5a5`, operações `PERSISTED + PLAN`, ainda **sem `prewriteClaim`**.
- Histórico Git blob `de0f022994ca47f0b8316169815afe25722fdfff`, 2 entradas, intacto.
- Blogger LOJA `live`, data `2026-11-03T22:19:09-03:00`, 16 cards, 16 imagens, 16 links; nenhum PUT na LOJA.
- Runner `0.8-v31r1-lab`, `daily_store_updates_enabled_by_runner=false`, `v31_enabled_for_new_blogs=false`.
- Prova real anterior de `If-Match`: página sacrificial LAB `3604438301826573070`, HTTP `412` com HTML/ETag/data preservados; run https://github.com/adelrib27/blogger-automation1/actions/runs/41928309254. **Não repetir o teste sacrificial**, não apagar página sem autorização.

## Limites — NÃO chamar isso de publicação pronta
1. O `LabAtomicClaimBridge` está **integrado à interface do publicador**, mas seu backend **GitHub de escrita real e leitor autenticado de backup durável não foram executados/testados ao vivo** neste marco. Gateway simulado não prova push real nem a origem independente do backup.
2. A proteção `If-Match` foi confirmada anteriormente com uma chamada real na página sacrificial, mas o `PUT` da LOJA exige controle contínuo de ETag/HEAD antes de enviar.
3. A publicação na LOJA LAB depende de autorização específica separada. No mesmo evento autorizado: validar HTML/HEAD, verificar o backup, claim atômico non-force com readback, só então PUT imutável único. Em falha/timeout, não repetir PUT.
4. Após PUT: GET autenticado, Cloudflare `PUBLIC_EXACT_PASS`, persistência atômica do ledger+histórico com CAS. Depois provar recorrência diária e replicação universal.
5. Limpeza do armazenamento GitHub Actions ficará para auditoria SAFE específica, **sem exclusões agora**.

**Atenção:** o simples fato de existir código de escrita na branch não concede permissão de gravar `prewriteClaim`, alterar a LOJA, ativar cron ou tocar em produção. A escrita operacional continua bloqueada.
