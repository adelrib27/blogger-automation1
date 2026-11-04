# V31 R1 LAB — ETag: somente página sacrificial; validação SAFE mínima

Data: 2026-11-04 — **SAFE/OFFLINE**, sem Blogger PUT nem criação de páginas.

## Escopo e decisão
- Repositório `adelrib27/blogger-automation1`; branch `lab/v31r1-shopee-safe-20261103`.
- Blog LAB `4739187376492839837`; LOJA protegida `2446067640331732447`.
- Estado canônico antes da alteração: ledger SHA Git `8331d025d77fc752230eec71f6c7d8ba86ece5a5` com `PERSISTED + PLAN`; histórico SHA Git `de0f022994ca47f0b8316169815afe25722fdfff`, duas entradas.
- A consulta read-only de páginas do LAB mostrou LOJA + cinco páginas institucionais. Nenhuma é sacrificável. Nenhuma página foi criada.
- Identificado conflito do validador histórico `v31_blogger_etag_policy_safe.py`: ele exigia pageId da LOJA, incompatível com uma prova segura na página sacrificial. **Não usar essa validação anterior como prova de compatibilidade real.**

## Nova validação isolada
- `blogger_stores/v31_core/v31_sacrificial_if_match_proof_safe.py`: valida somente o **formato** de eventual prova externa, exige blog LAB correto, pageId distinto da LOJA e das páginas institucionais, título fixo `V31-IF-MATCH-TEST-SACRIFICIAL`, URL esperada, PUT real `blogger.pages.update`, ETag forte desatualizado, resposta HTTP 412, GETs autenticados e mesmo hash/ETag/updated antes e depois. Rejeita evidência marcada sintética.
- **Importante:** um relatório com formato válido ainda é dado não confiável. A função retorna `real_server_behavior_verified=false`, `blogger_put_allowed=false` e exige conferência independente antes de qualquer liberação. **O código ainda não está integrado como autorização ao publicador operacional.**
- Testes: `blogger_stores/tests/v31_etag_proof/test_v31_sacrificial_if_match_proof_safe.py`, **16 casos pertinentes**, e workflow exclusivo `.github/workflows/v31_lab_etag_proof_shape_targeted_safe.yml`, `contents:read`, sem secrets, PUT, upload de artifacts, cron ou alterações do ledger.
- Commits: módulo `4c2d3f0f4e9424f66524b87677d9654b45567137`; testes `449f47868b5f7585f320b53b1bc7be7a1177b6e1`; workflow `27875e0ef55be3670bccb0ff2b50c6579087ba6e`.

## Evidência
- GitHub Actions https://github.com/adelrib27/blogger-automation1/actions/runs/41925592297 — **completed/success**, **16/16 testes**.
- Marker: `V31_ETAG_SACRIFICIAL_EVIDENCE_SHAPE_SAFE_PASS`.
- **Não repetir os 257 testes anteriores** neste marco, em conformidade com a decisão de evitar testes desnecessários.

## Restrições mantidas / próximo passo realmente necessário
- Nenhum GET/PUT ou criação de página no Blogger nesta execução; nenhuma publicação Shopee.
- Não comprova a rejeição real de `If-Match` por `Blogger.pages.update`. O Bridge V2 disponível não aceita cabeçalho HTTP condicional em `update_page`; portanto não usá-lo para fingir teste de HTTP 412.
- Quando houver autorização específica e executor adequado: criar **uma única página sacrificial identificada** no LAB, testar uma única requisição com ETag obsoleto e conferir GET autenticado posterior. O teste pode resultar em 200 se o servidor ignorar `If-Match`; por isso não testar a LOJA nem qualquer página institucional.
- Integrar claim Git remoto durável/atômico com backup e readback ao executor apenas após validação; PUT de segunda rotação requer autorização própria. Agendamento diário/replicação ainda desativados.
- Armazenamento de artifacts do GitHub será auditado e limpo depois, nunca por exclusão automática agora.

**NÃO CONFUNDIR teste do formato da evidência com prova ao vivo ou liberação de publicação.**
