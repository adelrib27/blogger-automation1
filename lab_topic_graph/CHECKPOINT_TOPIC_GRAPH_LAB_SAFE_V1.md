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

## Evidência LIVE de ruído semântico

Amostra dirigida de risco com conteúdo completo lido via Blogger readonly: 6 artigos e 14 links internos reais.

Classificação manual de revisão:

- `RELEVANT`: 4;
- `WEAK_BROAD`: 5;
- `LIKELY_IRRELEVANT`: 5.

Exemplos confirmados de ruído:

- artigo sobre ar seco → câmera de segurança com lâmpada;
- câmera de segurança → controle de umidade;
- câmera de segurança → manter ambiente fresco sem ar-condicionado;
- drinks → secagem de louças.

Também houve evidência de links contextualmente válidos entre umidade, ar seco e conforto térmico. Portanto, ainda é necessário calibrar fronteiras entre clusters/silos ambientais; não se deve marcar todo cross-silo como falso positivo.

Arquivo de evidência: `reviews/live_link_semantic_sample_v1.json`.

## Riscos ainda abertos

1. `palavra_chave` histórica tem cobertura 0%; títulos/categorias carregam quase todo o sinal.
2. A taxonomia ambiental ainda pode estar fragmentada entre quarto e conforto da casa.
3. O corpus é pequeno; cobertura de 29/35 não é suficiente para declarar taxonomia final.
4. Link health ainda é `REGISTERED_ONLY`; a camada offline não libera links sem verificação externa.
5. Ainda não existem pillars aprovados; `pillar_article_id` permanece `null` no registry LAB.
6. Backfill permanece bloqueado porque não há captura/versionamento de `content_hash` do HTML fonte no runner offline.
7. A revisão semântica LIVE é uma amostra dirigida de risco, não estimativa de precisão global.

## Próxima etapa autônoma

Continuar somente no LAB:

1. instrumentar snapshot read-only do grafo LIVE de links internos;
2. construir verificação de alvo por ID/URL/status a partir de snapshot readonly, sem CMS write;
3. revisar fronteiras ambientais e registrar relações permitidas como hipótese, sem liberar cross-silo por padrão;
4. selecionar candidatos a pillar somente por critérios mensuráveis, sem promover automaticamente artigo existente;
5. ampliar revisão A/B com amostra estratificada e medir falsos positivos/relevância;
6. testar backfill apenas como patch plan com hash do conteúdo;
7. decisão final somente após evidência suficiente.

## Decisão atual

**AINDA NÃO VALIDADO.**

Há evidência real de que o seletor lexical atual produz links semanticamente fracos/incorretos e de que o Topic Graph pode reduzir esse risco estruturalmente. Ainda não há evidência suficiente para migrar produção, definir pillars ou habilitar atualização automática de posts.
