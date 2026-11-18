# Checkpoint C19 — Índice textual FTS5 para escala, R2 real (17/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C19-R2-FTS5-203649-17LINKS-20261117`

**Repositório:** `adelrib27/blogger-automation1`  
**Branch:** `feature/v31-affiliate-hub-c1-safe-20261115`  
**PR:** [#52 DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52), não mesclado; `main` intocada e switches LIVE OFF.

## Objetivo e decisões preservadas

O V31 guarda um catálogo de qualquer assunto, antes de existir blog sobre ele. Os dois CSVs Shopee alimentam uma biblioteca privada cumulativa com **203.649 produtos distintos**, 109.576 com categorias oficiais L1/L2/L3 e **8.685 editorialmente aprovados** pelos gates atuais. **194.964** continuam em revisão. Nenhum deles é promovido automaticamente por conter categoria. Há **17 URLs afiliadas reais pré-convertidas**, restritas às campanhas originais. No futuro, a criação de blog consulta o acervo por um tema só quando o usuário o informar; os links selecionados são convertidos na campanha correta quando necessário. Nenhum produto/preço/comissão/venda foi inventado.

## C18 — Descoberta contextual (pré-requisito)

- `curation_audit.py` comprovou via R2 real **424 itens presentes em ambos os feeds**, sem conflitos nas categorias L1/L2; categorias sensíveis e de maior responsabilidade editorial seguem protegidas.
- `product_discovery.py` oferece `suggest_category_paths` (descobre L1/L2 a partir do assunto informado, sem cadastrar blog) e `discover` (resultados por relevância textual + diversidade de lojas + vínculo real de campanha). `include_review` nunca é permissão de publicar; `can_publish=False` em todo resultado.
- [Canário C18 R2 real 44179473566](https://github.com/adelrib27/blogger-automation1/actions/runs/44179473566) **175/175 testes PASS**: `Air Fryer → home appliances/kitchen appliances`, `Guarda Roupa → home living/furniture`, `Freio → spare parts and accessories for vehicles/spare parts for automobiles`, 12 lojas distintas em cada amostra, zero links de outra campanha, zero publicações.

## C19 — Busca textual persistente FTS5

Arquivos:
- `title_index.py`: índice virtual SQLite FTS5 `v31_catalog_fts(product_key,title,description)`, tokenização `unicode61 remove_diacritics 2`; termos de busca normalizados/validados contra MATCH injection. Se índice ainda não existe, `fts_condition` cai no método anterior.
- `product_discovery.py`: aproveita o índice em `discover` e `suggest_category_paths`, mantendo a pontuação comercial ausente; scoring continua apenas textual e seleção final usa os gates da curadoria/campanha.
- `title_index_migrate.py`: copia snapshot R2 a pasta temporária, calcula **SHA-256 lógico** do conteúdo anterior de produtos, taxonomia e links afiliados, compara resultados reais de 3 temas **ANTES** e **DEPOIS** da indexação, valida índice completo, e apenas com `--execute` salva um snapshot R2 privado e restaura para conferir contagem, hashes e rankings.
- `ingest.py` e `catalog_expansion.py`: quando índice FTS5 está presente, reconstruí-lo dentro da transação/staging de importação dos feeds, garantindo que produtos recém-incluídos sejam pesquisáveis no mesmo snapshot; testes simulam importação cumulativa e importação tradicional.
- `tests/test_title_index.py` e `tests/test_catalog_expansion.py` protegem equivalência com busca antiga, links separados por campanha, SQL FTS seguro, idempotência e atualização após novos produtos.

### Benchmark em catálogo REAL, sem vender promessa artificial

[GitHub Actions 44180894099](https://github.com/adelrib27/blogger-automation1/actions/runs/44180894099): **195 testes PASS, dry-run somente leitura**. Mesmos candidatos/ranking e sugestões L1/L2 nas 3 consultas; 203.649 produtos indexados no arquivo temporário, 17 links e 8.685 aprovações inalterados.

| Amostra de 3 temas | Sem FTS | Com FTS | Ganho no mesmo ensaio |
|---|---:|---:|---:|
| Dry-run R2 | 5,39 s | 1,16 s | ~4,7x |

[GitHub Actions 44181139736](https://github.com/adelrib27/blogger-automation1/actions/runs/44181139736): **SUCCESS, 195 testes**. Salvou **um snapshot R2 REAL**, restaurou e comprovou 203.649 linhas do FTS, 203.649 produtos históricos, 8.685 elegíveis, 17 links afiliados **INALTERADOS**, rankings equivalentes, `retention_pending=false`, **0 GraphQL, posts ou Pinterest**. Novo ensaio (rodada distinta): **7,55 s sem FTS** e **1,59 s com FTS**, ~4,7x.

**Os tempos são amostras isoladas**, não benchmarks de concorrência de dezenas de blogs nem promessa de conversão comercial. O aumento do tamanho do SQLite por FTS deve ser monitorado antes de ampliar frequência/escala.

## Contratos de release ainda pendentes

1. **Nenhum cron/flag de produção foi habilitado** e nenhum PR foi mesclado. A rotina de catálogo semanal opcional em `.github/workflows/v31_c17_catalog_refresh_safe.yml` permanece protegida por `V31_EDITORIAL_CATALOG_REFRESH_ENABLED` OFF/não definida.
2. Manter páginas de loja e publicadores atuais intactos. A hipótese de carga da Shopee em atualizações diárias de lojas e eventual rotação mensal distribuída será examinada **depois do V31**, sem associar automaticamente erro GraphQL 1000 ao erro 10030.
3. **194.964 itens em revisão** exigem uma etapa de curadoria orientada por categoria de origem, precisão semântica, segurança e condições comerciais, sem aprovar em massa somente por ter categoria oficial.
4. **Pool universal de conversão:** os links convertidos com campanha de biblioteca não se transformam em links para o subID de um blog ainda inexistente. A automação futura precisa identificar a campanha real do novo blog e converter os itens selecionados para ela, sem roubar URL de outro blog.
5. Integração supervisionada com orquestradores existentes de criação/geração Blogger/WordPress e publicação, preservando SEO, títulos originais e qualidade editorial. Não criar automaticamente novo blog ou posts de teste sem pedido específico.
6. Estratégia de conversão real de afiliado: observabilidade por campanha, páginas/consultas/CTR e resultados **verificáveis**, nunca métricas inventadas; respeitar as cotas reais da Shopee ao dimensionar conversões.

## C19.4 — Regressão FINAL do R2 pós-indexação

[GitHub Actions 44181357095](https://github.com/adelrib27/blogger-automation1/actions/runs/44181357095) — **SUCCESS** após salvar/restaurar R2:

- **195 testes V31** PASS no SHA do workflow; C19 e novas regressões de atualização dos feeds também passaram no CI geral da branch.
- `V31_C19_REAL_FTS_R2_PERSISTED_PASS`: **203.649 produtos indexados** e **17 links afiliados preservados** no snapshot R2 restaurado.
- `V31_C18_TOPIC_DISCOVERY_R2_PASS`: busca de temas para um futuro blog, sem receber link de outra campanha e sem publicação.
- `V31_C8_SHADOW_READONLY_PASS`: integridade das campanhas legadas Casa, Oficina e Radar preservada; shadow **não** ativa publicação.
- `V31_C9_RADAR_FULL_ROUTER_ERROR1000_PASS`: Radar monta fila real de 5 categorias/5 lojas usando R2 com erro Shopee 1000 **SIMULADO**, sem publicação.
- Nenhuma chamada comercial Shopee, nenhum post, nenhum novo Writer ou agendamento LIVE.

**Estado final C19:** FTS5 persistido e pós-canário de consumidores antigos **PASS**, 203.649 produtos, 17 links e 8.685 aprovações anteriores preservados. A produção da `main` continua no modo antigo; só o R2 privado recebeu o índice, pois o PR não foi mesclado. Próximo marco: C20, curadoria de produtos pendentes e integração da descoberta ao orquestrador de novos blogs, sem ativar publicações prematuramente.
