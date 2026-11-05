# Checkpoint V31 R1 LAB — R16: gate de recorrência diária SAFE

Data local: 04/11/2026, America/Recife. Estado: **VALIDADO EM SAFE/LEITURA; NENHUMA ATUALIZAÇÃO DIÁRIA OU CRON ATIVO NA V31.**

## Identidade preservada
- Repositório `adelrib27/blogger-automation1`, branch `lab/v31r1-shopee-safe-20261103` e `main` não alterada.
- Blogger LAB `4739187376492839837`, LOJA `2446067640331732447` — https://blog-teste-tema-worpress.blogspot.com/p/loja.html
- Tema aprovado `TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB.xml`; 16 produtos da segunda rotação publicados e preservados.
- Ledger canônico `blogger_stores/v31_lab/state/v31_rotation_ledger.json`, Git blob `fab8c013074053352d8d9b63aeb09c2f18e48823`: **duas operações PERSISTED**, sem PLAN ativo.
- Histórico `blogger_stores/v31_lab/state/v31_rotation_history.json`, Git blob `b21a55ae275bae677c116189e138e5053428c4ca`: **três entradas** (semente + 2 publicações).

## Descoberta e decisão arquitetural
- Já existem workflows de atualização diária para diversos blogs Blogger, como `air_fryers_store_autonomous.yml`, `achados_casa_store_autonomous.yml`, `blogger_liquidificador_store_autonomous.yml`.
- Reutilizar o motor de seleção Shopee `blogger_stores/src/v31_shopee_safe_scan.py` (integra V23, semântica, Policy Guard e links de afiliado). Não duplicar motor comercial nem utilizar arquivos SHA fixos da segunda rotação como entradas de novas rotações.
- O scanner V31 possui política de histórico com janela recente de 14 dias e fallback controlado. Não impor proibição permanente de reaproveitamento.
- O GitHub Actions executa `schedule` somente na branch padrão. A V31 está isolada no LAB e adicionar cron apenas nessa branch **não habilitaria um agendamento real**. A eventual integração do agendador à `main` precisa de revisão de isolamento, estado paralelo e autorização apropriada.
- Sem cron neste marco. O novo workflow dispara **somente em push de seus próprios três arquivos**, exclusivamente na branch LAB.

## Implementação R16
- `blogger_stores/src/v31_daily_cycle_gate_safe.py`: verifica identidade LAB, perfil, 2+ operações PERSISTED, cadeia de hashes, prova pública, histórico reconciliado, produtos/categorias válidos e data local America/Recife. Retorna `SKIP_ALREADY_UPDATED_TODAY` se a última publicação foi no mesmo dia, ou `READY_FOR_SAFE_SHOPEE_SCAN` se o dia já mudou. **Nunca libera PUT, Git write ou cron.**
- `blogger_stores/tests/v31_daily_gate/test_v31_daily_cycle_gate_safe.py`: **12 testes direcionados**, sem reexecutar as suítes anteriores.
- `.github/workflows/v31_lab_daily_safe_selection_preflight.yml`: `contents:read`, sem credenciais persistidas, sem upload de artifacts. Se o gate permitir SAFE scan num novo dia, roda apenas o scanner V23/V31 já existente, com saída em `RUNNER_TEMP` e sem publicação. Se for o mesmo dia, nem instala dependências nem acessa Shopee.
- Commit dos três arquivos: `c2ddf591e1dace51299e6221dbae61cd2165fd74`, readback GitHub confirmado.

## Evidência independente
- GitHub Actions: https://github.com/adelrib27/blogger-automation1/actions/runs/41943821340 — **completed / success**.
- **12/12 testes direcionados PASS**.
- Gate sobre estado real: `SKIP_ALREADY_UPDATED_TODAY`, `dayRecife=2026-11-04`, `lastPublishedDayRecife=2026-11-04`, `persistedOperations=2`, `historyEntries=3`, `safeScanAllowed=false`.
- Passos de instalação de dependências e consulta Shopee **skipped**; resultado correto para evitar nova seleção no mesmo dia.
- Marker `V31_LAB_DAILY_SAFE_PREVIEW_PASS; schedule=false; blogger_put=false; git_write=false; no_artifact_upload=true`.
- Nenhum PUT, novo PLAN, claim, cron ou mudança em outros blogs.

## Próximos passos necessários
1. Validar um ciclo **SAFE de seleção Shopee com histórico de três entradas** em um novo dia elegível, usando o scanner existente. O teste desta data pulou corretamente essa etapa.
2. Adaptar o executor transacional para operar com entradas **dinâmicas**, não hashes/IDs fixos da segunda rotação: seleção fresca → HTML candidato → reserva PLAN CAS → backup + claim remotos atômicos → um PUT com If-Match → readback → verificação pública independente → commit atômico ledger+histórico.
3. Simular/validar recuperação e repetição para o fluxo diário usando testes mínimos; estabelecer política de falha e horário desejado no fuso Recife.
4. Somente após validação, solicitar autorização específica para ativar cron de V31 em fluxo isolado ligado à branch padrão, sem alterar workflows antigos, outros blogs ou tema. A automação de novos blogs continua desligada.
5. Limpeza de armazenamento dos artifacts antigos permanece para auditoria SAFE separada, sem exclusões.

**Não declarar atualização diária ativa. O marco R16 é o contrato de entrada/skip seguro da automação recorrente.**
