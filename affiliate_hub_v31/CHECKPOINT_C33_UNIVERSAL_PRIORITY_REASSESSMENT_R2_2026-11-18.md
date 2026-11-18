# C33 — Objetivo universal restaurado e reavaliação integral real no R2 (18/11/2026)

**Continuidade:** `V31-EDITORIAL-C33-UNIVERSAL-FIRST-194964-206PATHS-0EXISTINGRULES-236TESTS-20261118`.

## Correção de prioridade

O V31 não é um projeto para abastecer apenas três WordPress: é um **catálogo universal** para blog existentes, Blogger/WordPress e futuros temas não planejados. Dois feeds CSV → biblioteca cumulativa R2 → hierarquia oficial + taxonomia editorial independente de site → seleção por tópico informado na criação futura de um blog → aprovação/política → conversão pela campanha real daquele blog → gerador e publicador apropriados → controle de originalidade e resultado. Pinterest e Worker v1.0 fora desta alteração. Vendas/comissões não são pré-requisito para desenvolver ou testar o sistema, não inventar dados.

[Issue #54](https://github.com/adelrib27/blogger-automation1/issues/54) virou prioridade P0; [Issue #53](https://github.com/adelrib27/blogger-automation1/issues/53) é somente rollout secundário dos três WordPress. As 14 conversões reais e 3 reservas `SHADOW_READY` da C32 validaram integração, mas não fecharam a biblioteca universal.

## Gargalo de código confirmado

- `affiliate_hub_v31/catalog_expansion.py:append_feed` pula os SKUs existentes, sem reexaminar sua aprovação quando `taxonomy.json` evolui.
- `Catalog.reclassify_missing` só preenche `product_taxonomy` ausente, não a taxonomia antiga `review`.
- `Catalog.import_csv` conserva `review` se a origem anterior foi `review`. Sem migração auditável, apenas adicionar regras não libera backlog.
- `future_site_intake.py` e `site_launch_plan.py` preparam seleções por assunto para blogs não registrados, mas **não criam blog, convertem para nova campanha nem publicam**. Estar no roteador não significa estar integrado a uma automação editorial genérica.

## Executado (SAFE)

- [PR #55 C33](https://github.com/adelrib27/blogger-automation1/pull/55) mesclado na `main`, commit `9fea6d63c8c58abeb26be4a252a2f66ad9ad490b`: adicionou `universal_reassessment.py` para varrer **todos os pendentes** e contar sinais de título + facetas oficiais + bloqueios sem promover SKUs. Separa evidência por categorias e lojas, não imprime títulos, IDs ou links. README agora explicita o objetivo mestre.
- [CI 44326035397](https://github.com/adelrib27/blogger-automation1/actions/runs/44326035397) **SUCCESS: 236 testes V31**, **24 Casa**, **21 Oficina**, originalidade cross-blog PASS, todos sem rede/segredos.
- [**Canário R2 real integral 44326301478**](https://github.com/adelrib27/blogger-automation1/actions/runs/44326301478) **SUCCESS: 236 testes + scan do backlog inteiro**, `V31_C33_REAL_R2_ALL_SKUS_REVIEW_ONLY_PASS`, sem escrita R2, Shopee, links novos, aprovações ou posts.
- **Catálogo:** 203.649 produtos; **8.685 aprovados historicamente**; **194.964 em revisão** (95,7%). As 282 antigas aprovações agora bloqueadas pela origem continuam protegidas por gate de consumo (C22). R2 tem 31 links reais desde C32; este canário não os alterou.
- **Lanes reais do backlog:** `TAXONOMY_REVIEW=91.047`, `NO_OFFICIAL_CATEGORY=88.239`, `POLICY_REVIEW=15.678`; demais lanes 0 na varredura.
- **206 caminhos L1/L2** nos grupos do backlog com categoria oficial, por exemplo `spare parts and accessories for vehicles/spare parts for automobiles` (19.449 pendentes), `home living/furniture` (7.313), `spare parts and accessories for vehicles/spare parts for motorcycles` (6.158) e `home living/tools home improvement` (5.026). São **facetas para descobrir**, NÃO licença para anunciar.
- **Gargalo estratégico medido:** entre os 194.964 pendentes, `TITLE_AND_OFFICIAL_PATH=0`, `TITLE_ONLY_UNVALIDATED_PATH=0`, `TITLE_WITHOUT_OFFICIAL_FACET=0`. Todos os 91.047 com categoria oficial ficaram `OFFICIAL_FACET_WITHOUT_TITLE_ROUTE` e os 88.239 sem categoria ficaram `NO_SOURCE_OR_TITLE_ROUTE`; 15.678 bloqueados por política. A taxonomia atual de título **não oferece novas correspondências para os pendentes**. Não confundir zero evidência sob regras atuais com ausência de valor comercial.
- Workflow e arquivo-gatilho temporários da auditoria C33 foram excluídos da `main` após o sucesso; nenhum cron de publicação/Worker/Pinterest alterado.

## Próximas etapas — P0 antes do rollout LIVE

1. **C34 taxonomia orientada por dados reais**: extrair vocabulário/descritores e combinações L1/L2/L3 dos feeds já indexados (ou títulos agregados por caminho), propor rotas editoriais mais ricas em modo review-only. Evitar fixar apenas nichos dos três WordPress. Não criar aprovações com base só na categoria da Shopee. Tratar separadamente os 88.239 sem categoria, inclusive fonte histórica.
2. **C35 reclassificação incremental idempotente**: distinguir `review` reversível por ausência de regra antiga de `review` irreversível por segurança/dado/conflito; aplicar somente decisões com base de evidência e política auditáveis, preservar link/campanha, permitir rollback. Testar em R2 simulado, depois canário estritamente controlado.
3. **C36 intake universal ponta a ponta**: novo tema fornecido no momento do pedido → busca e avaliação → registrar site/campanha reais quando surgirem → conversor já existente por campanha → geração editorial por plataforma e gate de LIVE. Testar tema novo não previsto, sem fabricar blog nem antecipar nichos.
4. **Operações posteriores**: só depois pensar em ativar variáveis manuais de cron e fallback dos WP, com supervisão, ou publicação Blogger. Não pedir ao proprietário ativação LIVE agora; não presumir que o V31 universal já esteja completo.

**Conclusão:** C33 trouxe uma prova do tamanho e da estrutura do bloqueio real. **Ainda não aprovou novos produtos** e **não concluiu a automação universal**; a prioridade é a taxonomia dinâmica, a reclassificação do backlog e o consumo por blogs futuros.
