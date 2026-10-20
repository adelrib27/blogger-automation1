# Topic Graph LAB SAFE — blogger-automation1

Estado: **HIPÓTESE / LABORATÓRIO / NÃO PRODUÇÃO**.

Esta camada implementa um experimento offline de Siloing / Topic Clusters sem integração de escrita com Blogger ou WordPress. Ela existe para medir se uma arquitetura de grafo editorial supera o seletor atual de links internos antes de qualquer migração.

## Invariantes de segurança

- não importa nem instancia cliente Blogger/WordPress;
- não publica, edita ou remove posts;
- não usa secrets;
- não faz chamadas externas durante o runner SAFE;
- alvo não verificado nunca recebe `PLAN_READY`;
- cross-site, cross-silo e cross-cluster são negados;
- classificação ambígua fica bloqueada;
- ausência de pillar não cria URL fictícia;
- backfill nunca escreve: gera apenas plano e exige `content_hash` válido;
- qualquer tentativa de habilitar `LAB_TOPIC_GRAPH_WRITE_CMS` ou `LAB_TOPIC_GRAPH_PUBLISH` interrompe a execução.

## Fluxo

```text
historico.json
    ↓
shadow classification
    ↓
content_registry.json
    ↓
legacy selector baseline ──┐
                           ├─ comparison_ab.json
Topic Graph candidates ────┘
    ↓
structural / health / anchor gates
    ↓
link_graph.json
```

No estado atual, `target_health` é `REGISTERED_ONLY`, portanto os links permanecem `BLOCKED_TARGET_UNVERIFIED`. Isso é intencional: o primeiro estágio mede classificação e elegibilidade estrutural sem transformar hipótese em link pronto.

## Taxonomia

`config/cluster_registry.lab.json` é uma taxonomia inicial e versionada para shadow classification. Ela é **provisória**. `categoria` do CMS não é sinônimo de `silo_id` nem de `cluster_id`.

Cada artigo recebe, quando possível:

- `site_id`
- `silo_id`
- `cluster_id`
- `role` (`PILLAR` ou `SATELLITE`)
- `classification.status`
- `metadata_hash`
- `content_hash` (ausente enquanto o conteúdo fonte não for capturado de forma segura)
- `target_health`

## Estados principais

Classificação:

- `APPROVED`
- `UNCLASSIFIED_NO_MATCH`
- `BLOCKED_AMBIGUOUS`
- `BLOCKED_CATEGORY_CONFLICT`

Links:

- `PLAN_READY`
- `BLOCKED_CROSS_SITE`
- `BLOCKED_CROSS_SILO`
- `BLOCKED_CROSS_CLUSTER`
- `BLOCKED_CLASSIFICATION`
- `BLOCKED_TARGET_NOT_LIVE`
- `BLOCKED_TARGET_UNVERIFIED`
- `BLOCKED_DUPLICATE`
- `BLOCKED_ANCHOR`
- `BLOCKED_BUDGET`

`PLAN_READY` é apenas plano editorial; não é publicação.

## Runner offline

```bash
python -m lab_topic_graph.topic_graph_safe \
  --history data/historico.json \
  --registry lab_topic_graph/config/cluster_registry.lab.json \
  --output /tmp/topic-graph-safe
```

Saídas:

- `baseline.json`
- `classification_report.json`
- `content_registry.json`
- `comparison_ab.json`
- `link_graph.json`
- `run_manifest.json`

## Critério de decisão

Esta implementação não declara a arquitetura validada. A decisão permanece **“ainda não validado”** até existir amostra revisada, verificação de saúde/canonical dos alvos, A/B com métricas e evidência de redução de falsos positivos sem perda editorial relevante.
