# C27 — Pré-merge da main atual com preservação de estado: PASS (18/11/2026)

**Continuidade:** `V31-EDITORIAL-C27-CURRENT-MAIN-37STATE-NOOVERLAP-230TESTS-20261118`.

## Evidência real

- O GitHub retornou em 18/11/2026 que `main` avançou **18 commits** desde o SHA-base antigo do PR, todos afetando arquivos de estado de Blogger e WordPress (fila, geração, publicação, rotação, seleção e relatórios), **37 caminhos** distintos.
- [**Run C27 44306854268**](https://github.com/adelrib27/blogger-automation1/actions/runs/44306854268): **SUCCESS**, checkout da feature com `fetch-depth:0`, `git fetch origin main` e comparação de `git merge-base`. Logs sanitizados: `MAIN_PATHS=37`, `FEATURE_PATHS=153`, `SHARED_PATHS=0`, `MAIN_STATE_PATHS=37`; `V31_C27_MAIN_STATE_HISTORY_PRESERVED_PASS`.
- `git merge --no-commit --no-ff origin/main` foi executado **somente no runner temporário**, saída `Automatic merge went well; stopped before committing as requested`, `V31_C27_MERGE_WITH_CURRENT_MAIN_PASS`.
- Na árvore combinada, **230/230 testes V31 PASS**, **24/24 Casa PASS**, **21/21 Oficina PASS**, gate cross-blog PASS, `V31_C27_COMBINED_MAIN_BRANCH_REGRESSION_PASS`.
- O workflow e seu gatilho temporários C27 foram removidos após o sucesso; execução não usou segredo, Environment, Shopee API, R2 ou publicador, tampouco fez push à `main`.
- A [auditoria C26](https://github.com/adelrib27/blogger-automation1/actions/runs/44306017629) comprovou **10 flags de release OFF**; o proprietário confirmou que as proteções do Environment `v31-editorial-safe` foram salvas, admitindo apenas `main`.
- **Não ativar LIVE** ao preparar release. Respeitar reservas de links por campanha: último snapshot C22 Casa 4/9, Oficina 4/6, Radar 8/15 (déficit total 14). Nenhum dado comercial fabricado. Pinterest e lojas fora do escopo.

## Gate de evolução

O teste C27 comprova a compatibilidade com a `main` amostrada, mas `main` pode continuar a receber commits de automação. Para qualquer merge real, usar SHA da feature esperado e merge de três vias, conferindo que dados atuais de `main` são preservados; deixar switches OFF e testar shadow R2 antes da primeira mutation com budget 1. Não alterar historico publicado.
