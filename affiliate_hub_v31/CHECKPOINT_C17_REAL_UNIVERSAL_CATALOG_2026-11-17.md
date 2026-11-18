# CHECKPOINT C17 — Biblioteca universal real com categorias L1/L2/L3 (17/11/2026)

**Continuidade:** `V31-EDITORIAL-C17-R2-203649-OFFICIAL-CATEGORIES-20261117`  
**Repositório:** `adelrib27/blogger-automation1`  
**Branch:** `feature/v31-affiliate-hub-c1-safe-20261115`  
**PR:** [#52, DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52) — **não mesclado**, nenhum publicador alterado na main.

## Direção confirmada pelo usuário

Construir **uma biblioteca universal de produtos Shopee**, não uma reserva limitada aos três WordPress. Os feeds de 100.000 e 10.000 itens devem alimentar uma base **cumulativa**, indexada por categorias/subcategorias/nichos disponíveis, antes de qualquer novo Blogger/WordPress existir. Só no pedido de um blog ou artigo decidir tema, título, produtos e campanha específica. Não há blog/nicho futuro presumido; links gerados para outra campanha não podem ser copiados ou inventados.

O usuário autorizou condução técnica autônoma para melhorar confiabilidade e escala, **sem abrir a publicação LIVE nem mexer nos agendamentos das páginas de loja**. Pinterest/Pins é projeto separado. A eventual investigação da concentração de consultas diárias das páginas de loja e erro Shopee 1000/10030 ocorrerá **depois de encerrar V31**, sem presumir que os dois erros tenham a mesma causa.

## Descobertas factuais dos dois CSVs

[Auditoria C16](https://github.com/adelrib27/blogger-automation1/actions/runs/44125064203): os dois feeds Shopee contêm categorias oficiais em inglês:
- Feed de **100.000 linhas**: `globalCategory1`, `globalCategory2` e `globalCategory3`.
- Feed de **10.000 linhas**: `globalCategory1` e `globalCategory2`.
- Há níveis de categorias reais como `home living > furniture > cupboards cabinets`, `beauty > hair care`, `spare parts and accessories for vehicles > spare parts for automobiles`. Não são nichos de blog presumidos.
- A auditoria também apontou **102.255** registros no snapshot antigo potencialmente recuperáveis de um status de taxonomia `unclassified`, mas isso não é aprovação automática, nem afirma que todos esses itens podem ser anunciados com segurança.
- O corpus dos feeds **rotaciona/muda**: em uma leitura atual, cerca de **94 mil SKUs não constavam da base R2 antiga**. Portanto não trocar o snapshot anterior por um dataset novo descartando histórico.

## C16 — Índice de origem separado de moderação editorial

- `source_category_index.py`: tabela aditiva `product_source_categories(product_key,source,level1,level2,level3,status)`, indexada por hierarquia e fonte, sem dependência de `site_key`; produto duplicado entre feeds tem registros de fonte independentes; conflito dentro do mesmo feed é sinalizado.
- `category_hierarchy()`: navegação L1 → L2 → L3 com contagem de produtos e separação de quantos já são `editorially_approved`. `browse_source()`: consulta para tema informado somente quando o usuário criar o blog; retorna `editorial_approved` e, se houver campanha declarada, `affiliate_url` apenas para essa campanha.
- Categorias de origem **não são aprovação editorial**. A base inclui áreas como `health` e `food beverages`; produtos restritos, ambíguos, incompletos ou sensíveis continuam não publicáveis até política/curadoria específica. Não gerar links para produtos sem elegibilidade.
- `source_enrichment.py` valida hashes de `products`, `product_taxonomy` e `affiliate_links` para migração só da tabela nova. O dry-run evidenciou que a base de produtos estava defasada, por isso **não foi executado o enriquecimento isolado**, pois faltavam 94.507 IDs de produto daquele teste.

## C17 — Ingestão CUMULATIVA sem apagar produtos/links

- `catalog_expansion.py`: em arquivo temporário copia o snapshot R2 privado, guarda todos os IDs originais e hashes SHA-256 das tabelas legadas, **insere apenas produtos inéditos** dos dois CSVs com a moderação e taxonomia atuais, adiciona categorias L1/L2/L3 de fonte, e compara que os produtos, status e URLs antigos permaneceram **bit a bit iguais** no conteúdo lógico das tabelas.
- A execução real salva **um snapshot** privado R2 e o restaura para reconferir todos os hashes, contagens, categorias oficiais e links. Falha fechada em qualquer divergência. Não envia dados ao Git nem ao WordPress/Blogger; não usa Shopee GraphQL nem converte links neste passo.
- [Dry-run REAL 44127080037](https://github.com/adelrib27/blogger-automation1/actions/runs/44127080037) — **165 testes, PASS**, sem escrita R2.
- [Execução REAL 44127603439](https://github.com/adelrib27/blogger-automation1/actions/runs/44127603439) — **SUCCESS**, snapshot R2 salvo e restaurado, `retention_pending=false`, nenhum dado original alterado e zero posts.

| Métrica | Antes | Após C17 R2 real |
|---|---:|---:|
| Produtos distintos no catálogo | 109.507 | **203.649** |
| Novos produtos adicionados | — | **94.142** |
| Itens aprovados na curadoria atual | 4.674 | **8.685** |
| Itens em revisão | 104.833 | **194.964** |
| Produtos com pelo menos 1 categoria oficial L1 | 0 na tabela nova | **109.576** |
| Registros L1/L2/L3 importados dos feeds | 0 na tabela nova | **110.000** |
| Categorias L1 oficiais detectadas | — | **29** |
| Links afiliados reais existentes, por campanha | 17 | **17, preservados** |

**Importante:** 109.576 com categoria de origem são produtos distintos dos feeds **atuais**; os demais produtos históricos permanecem no catálogo sem essa informação oficial enquanto não aparecerem em feeds arquivados/atualizações futuras. **194.964 em revisão não estão aprovados para publicação ou conversão**. Não anunciar toda a base como produtos elegíveis.

## Teste de futuro blog sem cadastro prévio

[QA R2 real 44128121400](https://github.com/adelrib27/blogger-automation1/actions/runs/44128121400) — **SUCCESS**: catálogo 203.649, 29 categorias L1, 109.576 produtos indexados; buscas por `Home & Living/Furniture`, `Beauty/Hair Care` e `Spare Parts for Automobiles` retornaram resultados reais; simulação de uma campanha de blog **não cadastrado** provou zero links de outra campanha. Testou o Radar com erro 1000 **simulado**, R2 real e fila 5/5/5, PASS. Nenhuma chamada à Shopee, publicação ou escrita em R2.

## Validação final de navegação em 3 níveis

[GitHub Actions 44128756858](https://github.com/adelrib27/blogger-automation1/actions/runs/44128756858) — **SUCCESS, 166/166 testes**, R2 real: **29 categorias L1**, para `Home & Living` existem **17 subdivisões L2** e, em `Furniture`, **10 subdivisões L3**. Buscas reais de produtos por `Home & Living/Furniture`, `Beauty/Hair Care` e `Spare Parts for Automobiles` para um blog ainda não cadastrado passaram, com **zero links cruzados de campanha**. A mesma execução aprovou novamente `C9_RADAR_FULL_ROUTER_ERROR1000_PASS` usando erro 1000 SIMULADO e snapshot R2 REAL. **0 chamadas comerciais, 0 publicações, 0 gravações nesse teste de leitura.**

## Atualização cumulativa preparada, mas OFF

`.github/workflows/v31_c17_catalog_refresh_safe.yml`:
- Apenas `main`, com execução manual mediante confirmação ou cron semanal **OFF até que `V31_EDITORIAL_CATALOG_REFRESH_ENABLED=true` seja deliberadamente configurada**; essa variável não foi habilitada aqui.
- Concurrency global `v31-editorial-catalog-single-writer`, sem credenciais de publicação, testes completos antes da migração.
- Não depende de ter blogs cadastrados, e os feeds atuais podem ser reimportados idempotentemente; links e produtos legados permanecem intactos.
- O workflow só passa a existir na `main` após decisão explícita de merge do PR, não ocorreu.

## Pendências de escala e qualidade (C18+)

1. **Curadoria ampliada, sem inventar categorias:** usar evidência hierárquica oficial L1/L2/L3 para expandir, com regras estritas, o número de produtos aptos para artigos/links. Não promover automaticamente as áreas sensíveis e os 194.964 em revisão. Diferenciar *categoria conhecida* de *publicação autorizada*.
2. **Busca de texto/ranqueamento comercial legítimo:** integrar consulta por nichos reais, palavras-chave, intenções, diversidade de lojas e, se existirem dados Shopee atuais verificáveis, métricas reais de cliques/conversões. Nada de preços, vendas, avaliações, descontos ou comissões inventados.
3. **Conversão progressiva independente dos blogs:** `library_pool.py` já planeja conversão por todos os nichos aprovados sem predefinição de blogs. Uma campanha global de biblioteca somente se explicitamente aprovada; para cada blog, converter/salvar sob sua própria campanha. O limite de 3 chamadas/run é de segurança piloto, não capacidade estrutural.
4. **Observabilidade e capacidade R2:** medir crescimento acumulado, custo de snapshots, validade de produtos antigos e taxas reais de erro. Evitar que a importação recorrente regrave informação antiga ou cause perda de links.
5. **Integração LIVE posterior:** recuperar reservas cacheadas, preservar autores/SEO/publicadores existentes, simular canário, e manter flags global/blog/reuso OFF até critérios de release. Blog novo só é criado quando o usuário pedir, sem antecipar nichos.
6. **Páginas de loja:** nenhuma alteração na frequência diária por enquanto; hipótese de carga da API e eventual rotação mensal distribuída somente após V31.

**Estado:** biblioteca cumulativa + hierarquia oficial **gravadas no R2 real**, regressões e prova de blog futuro PASS. **NÃO é liberação de publicação**.
