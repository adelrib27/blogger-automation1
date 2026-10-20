# CHECKPOINT — Topic Graph LAB SAFE v1

Data: 2026-10-20
Projeto: `adelrib27/blogger-automation1`
Branch exclusiva: `lab/topic-graph-safe-v1`
Estado: **LAB / NÃO PRODUÇÃO / AINDA NÃO VALIDADO**

## Isolamento confirmado

- `main` não foi modificada por este experimento.
- Nenhum arquivo de Radar Tech BR, Casa e Decoração, Oficina & Garagem, Vida Pet Prática, Conecta Achados ou Pinterest Automation foi alterado.
- Nenhuma publicação ou edição de CMS foi executada.
- O workflow do LAB usa `permissions: contents: read`, sem secrets e sem cliente Blogger/WordPress.
- Alvos não verificados permanecem bloqueados; nenhum edge recebeu `PLAN_READY`.

## Implementação existente

Diretório isolado: `lab_topic_graph/`.

Componentes:

- registry versionado de silos/clusters para shadow classification;
- classificador determinístico fail-closed;
- content registry;
- link graph estrutural;
- política de anchors;
- orçamento de links experimental;
- backfill planner dry-run com trava por `content_hash`;
- A/B contra o seletor lexical legado;
- diagnóstico A/B temporal, limitado a alvos existentes na data de publicação;
- anchor registry;
- link health registry offline;
- auditor/validador do grafo LIVE observado;
- snapshot compacto do grafo editorial LIVE observado;
- candidatos shadow a pillar, sem promoção;
- testes adversariais;
- workflow GitHub Actions exclusivo da branch LAB.

## Corpus validado

Leitura Blogger OAuth `blogger.readonly` confirmou:

- 36 posts LIVE no blog;
- 35 artigos editoriais presentes em `data/historico.json`;
- 1 post institucional (`Política de Privacidade`) deliberadamente fora do histórico editorial;
- distribuição de labels LIVE coincide com o baseline do histórico: Banheiro 2, Casa e Decoração 6, Cozinha 7, Decoração 1, Iluminação 1, Lavanderia 2, Organização 3, Quarto 7.

Portanto, não há evidência de divergência material entre o corpus editorial do histórico e o inventário LIVE neste checkpoint.

## Baseline shadow após refinamento

Corpus editorial: 35 artigos.

- URLs válidas registradas: 35/35.
- artigos com categoria: 29/35 (82,86%).
- artigos com palavra-chave histórica: 0/35.
- classificados `APPROVED`: 29/35.
- `UNCLASSIFIED_NO_MATCH`: 6/35.
- conflito de categoria após refinamento: 0.
- edges propostos estruturalmente: 38, todos `BLOCKED_TARGET_UNVERIFIED`.

Os 6 não classificados permanecem fail-closed; não ampliar a taxonomia apenas para elevar cobertura.

## Correções produzidas pelo primeiro baseline

A taxonomia shadow foi corrigida para:

- reconhecer plural de `lençóis`;
- impedir que o verbo genérico `preparar` force classificação em preparo de refeições;
- classificar drinks no cluster de bebidas;
- cobrir roupas amassadas no cluster de lavanderia;
- cobrir ar seco no cluster de umidade/conforto;
- aceitar `Decoração` para caminho de mesa;
- adicionar cluster de luminária/cabeceira.

Essas alterações são hipóteses do LAB, não regras de produção.

## A/B estrutural — corpus atual

Visão contrafactual usando todo o corpus atual:

- links legados selecionados: 102;
- mesmo cluster: 37;
- cluster diferente no mesmo silo: 13;
- cross-silo: 15;
- pelo menos uma ponta não classificada: 37.

Esta visão **não** reconstrói o momento histórico de publicação e não deve ser usada isoladamente para medir qualidade.

## A/B temporal — aproximação correta do momento de publicação

Somente alvos com `publicado_em` anterior ao artigo fonte são elegíveis:

- fontes avaliadas: 35;
- links legados selecionados: 75;
- mesmo cluster: 25;
- cluster diferente no mesmo silo: 12;
- cross-silo: 19;
- pelo menos uma ponta não classificada: 19;
- candidatos estruturais Topic Graph no mesmo cluster: 33.

`cross-silo` é sinal de revisão, não prova automática de erro.

## Grafo editorial LIVE observado — Blogger readonly

A leitura integral dos 35 artigos editoriais foi concluída via Blogger API readonly. O escopo de edge é o bloco editorial `Veja também`; links afiliados e navegação do template não entram na medição.

Métricas observadas:

- artigos editoriais: 35;
- classificados: 29;
- não classificados: 6;
- arestas editoriais LIVE: 70;
- fontes com links editoriais: 28;
- fontes sem links editoriais: 7;
- artigos com inbound zero: 13;
- mesmo cluster: 22;
- mesmo silo, cluster diferente: 13;
- cross-silo: 16;
- arestas envolvendo conteúdo não classificado: 19;
- alvos internos desconhecidos: 0;
- source→target duplicado: 0;
- alvos com repetição do anchor exato do título: 17;
- arestas com canonical/HTTP externamente verificado: 0.

O snapshot versionado está em `reviews/live_link_graph_observed.v1.json`. A fonte primária é `blogger_api_readonly`. O crawler público em lote foi explicitamente rejeitado como evidência porque omitiu links conhecidos em páginas-controle.

### Órfãos por inbound

Foram observados 13 artigos sem links editoriais recebidos. Isso inclui conteúdo recente e páginas específicas de cama/lençóis, conforto térmico, mesa, iluminação/fotos, lavanderia, petiscos, barbeador e drinks. O status de órfão é diagnóstico; não autoriza backfill automático.

## Evidência LIVE de ruído semântico

A amostra dirigida e o grafo completo confirmam coexistência de links bons e fracos.

Exemplos coerentes:

- escorredor → secar louças;
- lençóis Queen → renovar quarto com lençóis;
- roupas amassadas → rotina de passar roupas.

Exemplos estruturalmente frágeis/incorretos:

- câmera de segurança → limpeza de piso;
- câmera de segurança → controle de umidade;
- caminho de mesa → luminária de cabeceira;
- rotina de passar roupas → secar louças/preparar refeições/escorredor;
- protetor de colchão → câmera de segurança com lâmpada.

Também existe evidência de relações ambientais plausíveis que hoje aparecem como cross-silo, como ar seco → ambiente fresco. Portanto, `cross-silo` continua sendo sinal de revisão, não taxa automática de erro.

## Candidatos shadow a pillar

Arquivo: `reviews/pillar_candidates.shadow.json`.

`CANDIDATE_FOR_REVIEW`, sem promoção:

- `conforto-umidade` → `Controle da umidade em ambientes fechados com soluções`;
- `cozinha-bebidas` → `Como preparar bebidas geladas de forma rápida e prática`;
- `lavanderia-roupas` → `Como organizar a rotina de passar roupas de forma eficiente`;
- `quarto-conforto-termico` → `Como manter o ambiente fresco sem ar-condicionado em dias`;
- `seguranca-monitoramento` → `Como escolher uma câmera de segurança para monitorar a casa`.

Clusters multiartigo sem pillar existente adequado:

- `cozinha-mesa`;
- `cozinha-pia-louca`;
- `quarto-cama-textil`.

Clusters com apenas um artigo permanecem `BLOCKED_SINGLETON_CLUSTER`.

Nenhum `pillar_article_id` foi promovido no registry oficial do LAB e nenhum backfill foi liberado.

## Testes do grafo observado

O validador `observed_live_graph.py` verifica fail-closed:

- fonte readonly e modo LAB;
- inventário completo;
- zero capacidade de escrita/publicação/alteração de produção;
- `PLAN_READY=false`;
- ausência de alegação de hash completo ou canonical verificado;
- IDs/paths únicos;
- todos os artigos marcados LIVE;
- source/target conhecidos;
- ausência de self-link e duplicata;
- relacionamento silo/cluster recalculado e comparado ao armazenado;
- métricas recalculadas e comparadas ao snapshot.

A suíte específica do grafo observado passou localmente: **7/7 PASS**.

## Riscos ainda abertos

1. `palavra_chave` histórica tem cobertura 0%; títulos/categorias carregam quase todo o sinal.
2. A taxonomia ambiental ainda pode estar fragmentada entre quarto e conforto da casa.
3. O corpus é pequeno; cobertura de 29/35 não é suficiente para declarar taxonomia final.
4. Ainda não há verificação HTTP/canonical independente para os targets; `PLAN_READY` permanece bloqueado.
5. Existem apenas candidatos shadow a pillar; nenhum pillar foi aprovado/promovido.
6. Backfill permanece bloqueado porque o snapshot do grafo guarda links observados, não o HTML completo versionado com `content_hash` por fonte.
7. A contagem cross-silo é estrutural e necessita julgamento semântico antes de ser tratada como erro.
8. Anchors observados repetem o título completo do alvo; diversidade/clareza ainda precisam ser testadas em patch plans, nunca em produção nesta fase.

## Próxima etapa autônoma

Continuar somente no LAB:

1. verificar targets por HTTP/canonical em modo read-only e registrar timestamp/redirect/status;
2. materializar `content_hash` seguro do HTML fonte para os artigos que entrarem em simulação de backfill;
3. recalibrar a fronteira ambiental usando evidência do grafo e revisão semântica;
4. simular pillar↔satellite e satellite↔satellite apenas para candidatos elegíveis;
5. produzir patch plans com hash, anchor proposto, orçamento e blocking reasons;
6. executar A/B dos patch plans versus links LIVE atuais;
7. manter qualquer promoção/migração bloqueada até evidência suficiente.

## Decisão atual

**AINDA NÃO VALIDADO.**

Há evidência real e agora censitária do grafo editorial LIVE de que o seletor lexical atual produz associações estruturalmente fracas e de que o Topic Graph pode reduzir esse risco. Ainda não há evidência suficiente para migrar produção, promover pillars ou habilitar atualização automática de posts.
