# CHECKPOINT — V31 Estoque UNKNOWN para productOfferV2 — 12/11/2026

## Escopo e estado
- Branch: `lab/v31-loja-estoque-comissao-safe-20261112`.
- Modificacoes somente na branch LAB; nenhuma publicacao Blogger/WordPress; nenhuma mudanca de tema; nenhum merge `main`.
- O fluxo antigo da `main` em `achados_da_rotina/rotation_v31.py` ja bloqueia a atualizacao no caso de `data.errors` GraphQL, em vez de declarar esgotamento; a regra universal NOVA nao foi promovida para todos os workflows produtivos.
- A consulta `productOfferV2` continua sem campo de estoque com confiabilidade homologada neste sistema; nao inventar `stockUnits` ou supor que a ausencia em resultados de busca significa esgotamento.

## Regras implantadas em LAB

1. `classify_product_offer_visibility`: classifica consulta como `LISTED`, `NOT_LISTED`, `INVALID_DISCOVERY`, `API_GRAPHQL_ERROR` ou `API_UNAVAILABLE`, mas em TODOS os casos retorna `stock_status=UNKNOWN` porque discovery nao e inventario.
2. `require_clean_discovery_metadata`: nos artefatos SAFE da Loja, rejeita metadados ausentes, HTTP diferente de 200, status diferente de `OK`, ou lista GraphQL de erros nao vazia (inclusive `10000`). Portanto erro de API bloqueia ROTACAO em vez de substituir produto por hipotese de falta de estoque.
3. `stock_status`: somente duas observacoes independentes de estoque zero, recentes, autenticadas e pertencentes ao mesmo produto podem sinalizar `CONFIRMED_OUT_OF_STOCK`. Uma leitura isolada, dado nulo, expirado, sem autenticacao, mesma execucao ou consulta falha retorna `UNKNOWN`.
4. `plan_oos_rotation`: so substitui em memoria o produto realmente OOS; deve achar alternativa valida da mesma categoria. Caso contrario preserva lista original. Retorna `writes=false`; nao altera Blogger.
5. `select_verified`: comissao positiva verificavel, sem percentual minimo nem obrigatoriedade de comissao extra; nao trata `UNKNOWN` como `OOS`.
6. CLI LAB de candidatos: exige envelope de discovery limpo como CONTRATO de entrada, mas o JSON nao comprova autenticidade. Entrega apenas HTML e JSON SAFE locais, nunca PUT.

## Testes de 12/11/2026

- GitHub Actions run **43233229864**: PASS — 33 testes de estoque/comissao, 10 testes de CLI, 14 de productOffer/UNKNOWN, 17 de filtros, 14 de policy guard, 5 de consulta mínima = **93 testes offline PASS**.
- Testado: GraphQL 10000 sob HTTP 200, ausencia na busca, nodes nulos, HTTP 503, produto listado com campo de estoque 0 nao homologado, duplicidade, URL falsa, comissao zero, catalogo falso, dois zeros independentes e ausencia de substituto.
- Workflow exclusivamente OFFLINE com `SHOPEE_HTTP_REQUESTS=0`, `BLOGGER_WRITES=0`. Nenhum teste ponta a ponta em LIVE.
- [Evidencia GitHub Actions](https://github.com/adelrib27/blogger-automation1/actions/runs/43233229864)

## Limitacoes importantes

- Nao ha adaptador de estoque Shopee homologado integrado. Os testes de `stock_status` usam observacoes sinteticas, nao estoque real. Flags em arquivos nao constituem prova criptografica de origem.
- Estoque desconhecido deve preservar produtos existentes, mas nao comprova que eles estejam disponiveis.
- A API GraphQL 10000 e intermitente e continua pendente no catalogo; query minima de LAB nao foi comprovada estavel.
- PR, merge, publicacao, agendamento LIVE e promocao da regra para todos os blogs EXIGEM nova verificacao de codigo e estado e autorizacao especifica.

## Gate seguinte

Integrar uma fonte de disponibilidade realmente autorizada (se a Shopee expuser endpoint adequado), com codigo de verificacao de origem/assinatura e registro de evidencias, depois medir em LAB se duas consultas independentes de mesmo item comprovam zero. Somente entao autorizar rotacao LIVE controlada.
