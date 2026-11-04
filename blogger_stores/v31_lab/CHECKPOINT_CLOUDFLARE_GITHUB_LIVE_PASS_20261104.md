# Checkpoint V31 LAB — GitHub Actions + Cloudflare Browser Rendering LIVE READ-ONLY PASS

## Identidade do teste
- Blog LAB: `4739187376492839837`, Page LOJA: `2446067640331732447`.
- GitHub: `adelrib27/blogger-automation1`, branch isolada `lab/v31r1-shopee-safe-20261103`.
- Environment GitHub: `v31-lab`, com 1 branch autorizada e segredos de conta/token Cloudflare (nomes apenas; não registrar valores).
- Workflow: `.github/workflows/v31_lab_cloudflare_public_live_readonly.yml`.
- Disparo controlado: commit `169f3993578679045ea554097108fce8416fb811`, apenas trigger de verificação read-only.
- Execução: https://github.com/adelrib27/blogger-automation1/actions/runs/41769090187 .
- Job `126374304436`: `completed/success`, todas as etapas aprovadas.
- Código Python 3.12: **14 testes** do verificador V31 + **22 testes** do adaptador Cloudflare aprovados.
- Seleção Shopee: artifact do run `41751202914`, SHA256 `46ef8a293875720f036d90430d1e57c862277b42bde966fbf34b15f9d2cb6c0c`, aprovado por `sha256sum -c`.
- Cloudflare Environment secrets estavam presentes: `V31_CF_LAB_ACCOUNT_ID` e `V31_CF_LAB_BROWSER_TOKEN`. Valores não devem constar aqui, em logs nem no pacote.

## Prova automática independente
- Artifact do run: ID `13294391153`, `v31-lab-cloudflare-public-proof-1`.
- ZIP SHA256 `c04f72657bb4d344216cfce537cf6917e88f91de2edd6f9c0ccc5f4093f4c498`.
- `RELATORIO_PUBLICO_CLOUDFLARE.json` conferido após baixar o ZIP do GitHub:
  - `status=PUBLIC_EXACT_PASS`.
  - `transport=CLOUDFLARE_BROWSER_RENDERING`.
  - `public_http=200`; `cards=16`, `images=16`, `links=16`, `categories=4`.
  - `public_verified=true`, `publication_attempted=false`.
  - `selection_sha256=46ef8a293875720f036d90430d1e57c862277b42bde966fbf34b15f9d2cb6c0c`.
  - `public_html_sha256=fd9f7d33d4b83699b3c55bb143d006e1e4882de94d2c3b3804fa9a4bd2c660cc`.
  - `verified_at_utc=2026-11-04T03:45:55.366663+00:00`.

## Verificação pós-job
- Blogger Bridge get_page: atualização da LOJA `2026-11-03T22:19:09-03:00`, ainda 16 cards, 16 fotos, 16 links; nenhuma nova publicação pelo teste.
- Runner: `0.8-v31r1-lab`, flag novos blogs `false`, flag diária `false`.
- Ledger histórico no GitHub **permanece** `PUBLISHED_PENDING_PUBLIC`, sem mudança no arquivo original.

## Escopo e próximo passo
**VALIDADO EM LAB:** execução automática e autenticada do GitHub Actions lendo a página pública via Cloudflare e conferindo catálogo exato por hash, com artifact auditável, sem publicação.

**NÃO VALIDADO AINDA:** aplicação transacional da prova ao ledger/histórico com compare-and-swap e execução/reinício concorrente; novas rotações diárias; cron; provisionamento de novos blogs. Não ligar flags ainda.

Próxima integração: orquestrador V31 que valida proveniência do artifact e aplica `PUBLIC_VERIFIED` e `PERSISTED` com CAS e histórico idempotente. Precisa de testes SAFE de repetição, queda pós-commit e edição concorrente; depois teste LAB end-to-end. Não reexecutar a publicação inicial.
