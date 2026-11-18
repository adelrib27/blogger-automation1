# Checkpoint C25 — proteção de ambiente confirmada por captura e preparo de release (18/11/2026)

**Continuidade:** `V31-EDITORIAL-C25-ENV-MAIN-ONLY-PREFLIGHT-230TESTS-20261118`.

## Ações manuais de credencial e branch

1. O usuário rotacionou o App Secret no portal oficial da Shopee, atualizou `V31_EDITORIAL_SHOPEE_APP_SECRET` no Environment. [C23 API real 44302637196](https://github.com/adelrib27/blogger-automation1/actions/runs/44302637196) autenticou `productOfferV2` com `V31_SHOPEE_API_PASS`, 230 testes V31 PASS, 0 mutations/publicações.
2. O usuário atualizou `SHOPEE_SECRET` no repositório para os fluxos anteriores. [C24 API real 44303901286](https://github.com/adelrib27/blogger-automation1/actions/runs/44303901286): `SHOPEE_APP_ID` + `SHOPEE_SECRET` **PASS**, leitura única, 0 mutations/publicações.
3. Captura fornecida pelo usuário da tela `Settings → Environments → Configure v31-editorial-safe` mostra **Selected branches and tags**, **1 branch and 0 tags allowed**, linha **`main`**, e **Allow administrators to bypass configured protection rules** *desmarcado*. Regra de deployment `main` está visível; alteração do checkbox de proteção deve ser persistida em **Save protection rules** se ainda não foi clicado. Required reviewers aparece desmarcado; opcional reforçar a liberação de produção com aprovador autorizado. A captura não revela valores de secrets.
4. O conector GitHub não dispõe de leitura administrativa de secrets/Environment para confirmação direta; não apresentar teste pré-restrição como prova de bloqueio pós-restrição. A evidência de UI é suficientemente específica para registrar o passo de branch.

## Preflight técnico sem publicar

- [PR #52 DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52) **mergeable=true** no último snapshot de metadados, mas com **149 arquivos** de mudanças; exige revisão de gates antes de merge controlado. `main` segue intocada.
- [CI do HEAD C24 44304085557](https://github.com/adelrib27/blogger-automation1/actions/runs/44304085557) **SUCCESS** (idem [44304077369](https://github.com/adelrib27/blogger-automation1/actions/runs/44304077369)). Regressão completa no workflow permanente para V31/WordPress e originalidade; C23 havia passado 230 testes.
- Conferidos quatro patches de workflow do PR: os três publishers legados Casa/Oficina/Radar só usam descoberta V31 se **GLOBAL AND SITE** forem `true`; o caminho antigo segue ativo por padrão com switches ausentes/OFF. `v31_c8_cache_replenish_safe.yml` é `main`-only, exige confirmação manual para converter e limita orçamento global a **1–3**; todos os Cron de V31 são guardados por variáveis, inicialmente OFF. Não afirmar estado efetivo das variables sem auditoria na execução.
- O PR mantém alterações em arquivos de produção apesar de switches OFF: **não mesclar automaticamente** nem ligar site/publishing sem revisão final de contraste com `main`, inventário e rollback. Testes de PR não são autorização de publicação.
- **Inventário R2 último confirmado C22:** 203.649 produtos; 17 URLs afiliadas reais preservadas. Reserva atual (não revalidada após C22): Casa 4/9, Oficina 4/6, Radar 8/15: **14 links para completar**. A conversão controlada comercial requer workflow na `main` após merge revisado e snapshots verificados; uma consulta Shopee read-only não prova orçamento de mutation.
- **LIVE OFF** em todo V31; Pinterest e páginas de loja intactas. Vendas/comissões não são pré-requisito.

## Próxima execução segura

G0: revisão final de `PR #52` e CI no HEAD, confirmação do botão **Save protection rules** se mudança não foi persistida; auditar switches no contexto real da `main`.

G1: merge controlado APÓS aprovação de gates e, ainda com switches OFF, executar shadow R2 real na `main`; G2: 1 mutation Shopee por canário inicial (sem post) e verificação de restauração R2, depois lotes pequenos até meta de reserva; G3/G4: testar originais sem publicar e só então habilitar por site conforme runbook. Sem aprovação, ficar em modo SAFE.

[Issue #53](https://github.com/adelrib27/blogger-automation1/issues/53) registra checklist. Este checkpoint é evidência/planejamento, não liberação LIVE.
