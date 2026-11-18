# Checkpoint C18 — seleção temática para blogs futuros, curadoria segura (17/11/2026)

**Continuidade:** `V31-EDITORIAL-C18-R2-SAFE-TOPIC-DISCOVERY-20261117`

**Repositório** `adelrib27/blogger-automation1` — branch `feature/v31-affiliate-hub-c1-safe-20261115`; [PR #52 DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52), sem merge nem alterações dos publicadores/lojas da `main`.

## Objetivo

V31 é uma **biblioteca universal CUMULATIVA** para quaisquer blogs Blogger/WordPress que venham a ser criados, não apenas as campanhas Casa/Oficina/Radar. O usuário não quer que a IA presuma categorias ou nichos de blogs inexistentes. Primeiro armazenar/indexar todos os produtos Shopee com categorias oficiais; só no pedido de criação do blog usar o tema informado para localizar e ranquear produtos. Preservar autenticidade de preços, vendas, comissões e links por campanha. Não usar Pinterest.

C17 gravou e restaurou no R2 **203.649 produtos**, 109.576 com facetas oficiais L1/L2/L3 provenientes dos CSVs mais recentes, **8.685 já aprovados** pela taxonomia conservadora e 194.964 pendentes, **17 links afiliados anteriores intactos**. Fallback API-first do Radar com erro 1000 SIMULADO também passou. Atualização cumulativa semanal continua OFF na branch até eventual release supervisionado.

## C18.1 — Segurança/qualidade do índice real

[GitHub Actions 44177966028](https://github.com/adelrib27/blogger-automation1/actions/runs/44177966028) — **SUCCESS**, **167 testes** e leitura R2 REAL:

- **424 produtos** aparecem em ambos os feeds; nenhum conflito entre as categorias oficiais L1 ou ramos L1/L2 nesses registros.
- **109.576 produtos** têm categoria de origem, dos quais **4.656** também aprovados editorialmente (outros 4.029 aprovados atuais podem ter sido herdados sem faceta dos CSVs recentes).
- A auditoria sinalizou roots que **não devem promover produtos automaticamente** só pela categoria: `health`, `food beverages`, `mom baby`, `baby kids fashion`, `hobbies collections`. Alguns já passaram em versões anteriores da curadoria; C18 os retém **fora da nova seleção publicável sem revisão manual/mais evidências**.
- Nenhum URL de produto, identificador, campanha ou secret foi exibido no relatório. Nenhuma escrita R2, chamada GraphQL ou publicação.

## C18.2 — Seletor por tema, diversidade de lojas e campanha própria

- **`product_discovery.py`**: função `discover(catalog,topic,category,subcategory,campaign,limit,max_per_shop,include_review)`, busca produtos do catálogo por palavras significativas do assunto informado **naquele momento**; opcionalmente restringe por categoria oficial. Não depende de blog pré-cadastrado.
- Classificação editorial inalterada: **só `products.moderation='eligible'` E `product_taxonomy.status='matched'` E root sem proteção** podem aparecer na seleção normal. `include_review=True` serve à curadoria, jamais à publicação; itens pendentes são identificados explicitamente.
- Se as categorias L1/L2/L3 de duas fontes forem contraditórias, a descoberta bloqueia o produto. Links comerciais são procurados somente para a `campaign` explicitamente recebida; se ausentes, produto retorna `requires_conversion` e `affiliate_url=None`, **nunca** o link da campanha de outro blog.
- Pontuação `semantic_score` usa exclusivamente termos presentes em título/descrição e equivalência de expressão; `max_per_shop` evita concentração no mesmo vendedor, sem inventar preço, vendas, avaliação, comissão, ROI nem CTR. A relevância vem antes do cache.
- Todos os itens da função trazem `can_publish=False`: selecionar produto é diferente de autorizar gerar/publicar artigo, ação que continua dependente dos gates originais de SEO, originalidade, link real da campanha e confirmação do release. Modo SAFE.
- **`suggest_category_paths(catalog,topic)`**: descobre automaticamente os caminhos L1/L2 que têm títulos contendo o assunto informado, com contagem de produtos e quantos já estão aprovados, sem precisar saber antecipadamente categoria/nicho do blog. Roots protegidos vêm sinalizados para revisão.

## C18.3 — Canário com R2 real

[GitHub Actions 44178839555](https://github.com/adelrib27/blogger-automation1/actions/runs/44178839555) — **SUCCESS**, **173 testes**; consulta sem cadastrar novo blog, usando campanha hipotética `futureblogv31`:

| Assunto informado | Aprovados na primeira seleção (até 12) | Candidatos para revisão (até 12) | Lojas distintas |
|---|---:|---:|---:|
| Air Fryer | 12 | 12 | 12 |
| Guarda Roupa | 12 | 12 | 12 |
| Freio Automotivo | 4 | 12 | 12 |

- Zero links de campanhas existentes entregues à campanha hipotética; zero publicação, zero chamadas Shopee ou gravacões R2.
- A amostra é um piloto de recomendação, **não** prova de que houve cliques, vendas, comissões ou rentabilidade.
- Testes adicionais cobrem categorias protegidas, recusa de assunto vazio, identificação de links convertidos por campanha, busca só de reviews e conflitos entre feeds.

## Limitações e próximos marcos

1. O catálogo tem 194.964 pendentes. Categoria oficial é **faceta de descoberta**, não certificação de produto apto a anúncio. É possível identificar temas promissores para curadoria, mas a aprovação automática ampla exige critérios e validações adicionais antes de escrever no R2.
2. A automação de criação de blog precisará integrar os dois passos **sugestão de categorias e escolha contextual** ao gerador existente. Não criar blog de teste nem duplicar publicador sem pedido específico.
3. Conversão de links deve continuar usando o conversor Shopee existente na campanha correta. Biblioteca universal sem a campanha futura **não pode magicamente pré-converter links com subIDs de blogs que ainda não existem**. Se um pool comum for definido, seu rastreamento e regras devem ser verificados explicitamente, nunca atribuídos à campanha privada de outro site.
4. Para escala de milhares de consultas, avaliar uma busca de texto indexada (FTS5 ou similar), telemetria e controle de ritmo API sem causar rajadas. A rotina de biblioteca atual ainda não foi ativada no cron.
5. Os 3 WordPress continuam **NOT_READY** para reserva antiga de três dias, com 17 links no R2 divididos entre campanhas existentes; a seleção universal NÃO faz cache pronto para essas campanhas.
6. O usuário quer avaliar **mais tarde** se as páginas de loja, todas com refresh diário, somam requisições excessivas. Não modificar o cron das lojas agora; erros 1000 e 10030 **não são considerados causas idênticas**.

**Estado:** busca semântica universal testada em modo read-only; classificação ampla e integração automática final com geradores ainda pendentes. PR continua DRAFT, switches OFF, nenhuma publicação.


## C18.4 — Prova FINAL de inferência de caminhos L1/L2 pelo tema

[Run 44179473566](https://github.com/adelrib27/blogger-automation1/actions/runs/44179473566) **SUCCESS — 175/175 testes + R2 REAL read-only**:

| Tema novo | Categoria L1 sugerida por dados reais | Subcategoria L2 sugerida |
|---|---|---|
| `Air Fryer` | `home appliances` | `kitchen appliances` |
| `Guarda Roupa` | `home living` | `furniture` |
| `Freio` | `spare parts and accessories for vehicles` | `spare parts for automobiles` |

Em cada cenário havia **5 caminhos sugeridos** para consideração; busca de produto comprovou **12 lojas diferentes** na amostra de candidatos para revisão, com **12/12 aprovados** para Air Fryer e Guarda Roupa e **4/12** para Freio. Zero vazamentos de URL para a campanha hipotética, zero novas conversões e zero publicação. `suggest_category_paths` trata até categorias não aprovadas apenas como pistas, nunca como permissão de publicar ou converter.

O seletor atual ainda percorre os produtos/categorias existentes na busca contextual. **C19 deve avaliar um índice de busca textual persistente** para milhares de consultas sem varrer todo o catálogo; não alegar desempenho de alta escala antes de medir.

