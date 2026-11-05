# Checkpoint R19 — GitHub schedule V31 / Shopee SAFE real em LAB (2026-11-05)

## Hierarquia: estado real > R19 SAFE > R18 > histórico
**LAB:** `adelrib27/blogger-automation1`, branch `lab/v31r1-shopee-safe-20261103`, blog `4739187376492839837`, página LOJA `2446067640331732447` (https://blog-teste-tema-worpress.blogspot.com/p/loja.html).
**Condição:** agendamento diário instalado/ativo no GitHub, mas **a primeira execução `schedule` ainda NÃO foi comprovada**. Nunca declarar rotina ponta a ponta validada enquanto não ocorrer evento `schedule` e proof público exato.

### Evidência de ausência do disparo original
- Cron original `17 13 * * *` UTC (10h17 Recife) não aparece no histórico acessível do GitHub Actions até o diagnóstico R19 de hoje.
- API independente `GET /repos/adelrib27/blogger-automation1/actions/workflows/407631838` confirma `state=active`; hipótese de workflow desativado não sustentada. GitHub documenta possibilidade de atraso/descarte de `schedule`, mas **a causa específica ainda não foi determinada**.

### Comprovação REAL no LAB sem publicação
- Commit LAB de diagnóstico `6cac54ffe8229121142f9ac2a3a9967046047c3e`, somente arquivo novo `.github/workflows/v31_lab_r19_safe_diagnostic_20261105.yml`.
- Run SAFE GitHub https://github.com/adelrib27/blogger-automation1/actions/runs/42069512772 — `completed/success`; gate do dia `READY_FOR_SAFE_SHOPEE_SCAN`; executou o scanner Shopee real e GET Blogger autenticado; gerou candidata HTML somente na memória / RUNNER_TEMP; nenhum Blogger PUT, nenhuma escrita Git canônica.
- `V31_LAB_SHOPEE_SAFE_READY`: **16 produtos, 16 fotos, 16 links de afiliado**, `published=false`; seleção SHA256 `e1c71fd4b341cfdb690b0eb04664661d02504533319a42e3edd7155a9d55b5ed`.
- `R19_REAL_SHOPEE_AND_BLOGGER_READONLY_SAFE_PASS`: modos `new:16` (16 novos), SHA256 HTML atual `d33070c001281ed795489a032a504accfcab2b593010c1a9e8cf5bb86b8109b8`, SHA256 HTML candidato `13470ca8d582aea4b0d9986accc35f796860dfb66a0400b834bc33eb50848014`.
- Os dados Shopee capturados são prova do momento do scan: não são arquivo de publicação, não devem ser publicados sem novo preflight no momento do PUT.

### Correções preventivas LAB
- Commit LAB `9ee2f563d67969cc688fdd0e8c2157f88c4e9e9e`, exatamente dois arquivos:
  - `blogger_stores/src/v31_lab_daily_autonomous_transaction.py`: exigir credenciais Cloudflare verificáveis antes de registrar PLAN; backup original precisa corresponder byte a byte inclusive quebras finais.
  - `blogger_stores/tests/v31_daily_autonomous/test_v31_lab_daily_autonomous_transaction.py`: +4 testes.
- CI https://github.com/adelrib27/blogger-automation1/actions/runs/42070166300 — **51/51 testes SAFE PASS** (24 transação, 15 candidata, 12 gate); policy audit https://github.com/adelrib27/blogger-automation1/actions/runs/42070166342 completed/success.

### Redundância no cron, sem mudar LOJA
- Commit main `d528c101d1d746bc2b51381487c272fe5f942b63`, **somente** `.github/workflows/v31_lab_daily_autonomous_dispatch.yml`: `17 13 * * *` UTC (10h17 Recife), mais `23 18 * * *` UTC (**15h23 Recife**). A segunda janela é fallback; gate diário bloqueia publicação duplicada.
- Probe após essa atualização da main: https://github.com/adelrib27/blogger-automation1/actions/runs/42070557326, `completed/success` (HTTP 204) → https://github.com/adelrib27/blogger-automation1/actions/runs/42070573573, `completed/success`; job `executar-ciclo-diario-exclusivo-lab` foi **skipped**.
- Não houve publicação por esse probe e não se deve apresentá-lo como evento `schedule`.

### Estado canônico verificado após os testes
- Blogger LOJA: `status=live`, atualizado pela última vez em `2026-11-04T21:06:56-03:00`, 16 cards, tema V31 preservado.
- Ledger blob `fab8c013074053352d8d9b63aeb09c2f18e48823`: 2 operações `PERSISTED`, sem novas operações.
- Histórico blob `b21a55ae275bae677c116189e138e5053428c4ca`: 3 entradas.
- Outros blogs, workflows legados, credenciais e tema de produção preservados.

### Próxima evidência indispensável
No horário programado, consultar `schedule` do workflow GitHub ID `407631838`; verificar `workflow_dispatch` no LAB com origem `MAIN_SCHEDULE_LAB_ONLY`, seleção Shopee e Policy Guard, Git PLAN+backup+claim CAS, no máximo 1 Blogger PUT forte If-Match, GET autenticado, `PUBLIC_EXACT_PASS` Cloudflare e Git ledger/histórico em commit atômico (3 operações PERSISTED / 4 runs). Sem nenhuma publicação no mesmo dia se uma já tiver ocorrido. Resultado ambíguo após claim exige reconciliação manual; proíbido retry automático de PUT.
