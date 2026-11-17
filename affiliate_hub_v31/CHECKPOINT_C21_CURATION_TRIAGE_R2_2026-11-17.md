# Checkpoint C21 — triagem integral de curadoria e gate de origem (17/11/2026)

**Código de continuidade:** \`V31-EDITORIAL-C21-R2-203649-194964-282GUARDS-17LINKS-213TESTS-20261117\`

**Repositório:** \`adelrib27/blogger-automation1\`  
**Branch isolada:** \`feature/v31-affiliate-hub-c1-safe-20261115\`  
**PR:** [#52 DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52) — sem merge.  
**Escopo:** Blogger e WordPress; Pinterest fora deste hub.

## Ponto inicial confirmado

C20 terminou com 203.649 SKUs cumulativos no SQLite privado do Cloudflare R2, 203.649 entradas do índice FTS5, 8.685 elegíveis pela classificação anterior, 194.964 pendentes e 17 URLs afiliadas reais por campanha. Nenhum blog futuro recebe campanha inventada, e nenhum writer LIVE V31 está ativo.

## Execuções feitas no C21

1. **\`product_discovery.py\`**: a busca \`discover\` e a sugestão de categorias passam a falhar fechado se **qualquer** origem armazenada possuir status \`review\`/\`conflict\` ou se houver divergência de ramos/categorias. A versão anterior ignorava o registro de origem conflitante quando outra origem tinha \`matched\`.
2. **\`curation_triage.py\`**: varredura incremental de TODOS os produtos, com sete filas sem promoção. Os resultados são contagens agregadas por lane e categoria oficial L1/L2, lojas distintas e informação explícita de que **não existem métricas comerciais medidas**. Não expõe título, chave de SKU, link afiliado, segredo ou nome de campanha.
3. **\`source_policy_gate.py\`**: recusa produtos de fonte protegida ou conflitante, mesmo se a moderação/taxonomia histórica os considerava elegíveis; permite a compatibilidade com catálogos antigos **sem tabela de facetas** somente se os outros gates anteriores já aprovaram o item. A checagem não cria tabelas em dry-run.
4. **Gate aplicado aos consumidores SAFE:** \`universal_index.lookup\`, \`source_category_index.browse_source\`, \`Catalog.for_conversion\` e \`library_pool.library_candidates\`. Itens anteriormente aprovados mas com raiz sensível ou conflito não entram em novas conversões nem aparecem como automaticamente aprovados nas consultas protegidas. **Não remove links existentes** nem altera posts anteriores.
5. **\`.github/workflows/v31_c21_curation_audit_safe.yml\`**: diagnóstico semanal preparado com \`workflow_dispatch\` (confirmação) e cron semanal; condicionado a \`main\` e flag \`V31_EDITORIAL_C21_AUDIT_ENABLED=='true'\`. A flag não foi habilitada, o PR não foi mesclado, e o diagnóstico recorrente **não está ativo em produção**. Usa mutex \`v31-editorial-catalog-single-writer\`, secrets privados R2 e não possui credenciais Blogger, WordPress ou Shopee.

## Auditoria R2 real

- [Run inicial C21 44190455521](https://github.com/adelrib27/blogger-automation1/actions/runs/44190455521): **SUCCESS**, 209 testes, catálogo inalterado.
- [Canário do bloqueio de fontes 44191158191](https://github.com/adelrib27/blogger-automation1/actions/runs/44191158191): **SUCCESS**, mostrou 282 SKUs historicamente elegíveis pelos critérios anteriores mas vetados pelo gate de categoria de origem.
- [**Canário final R2 real 44191963790**](https://github.com/adelrib27/blogger-automation1/actions/runs/44191963790): **SUCCESS**, **213 testes PASS**, leitura integral, guarda de fontes, verificação de \`for_conversion\`, pool de pré-conversão e busca universal. **0** chamadas à Shopee, **0** novas URLs, **0** escrita R2, **0** posts/Pins/blogs. Confirmou **203.649 produtos**, **203.649 FTS**, **17 URLs afiliadas anteriores** e integridade geral.

### Distribuição exata dos 194.964 pendentes

| Fila | Produtos | Tratamento |
|---|---:|---|
| \`TAXONOMY_REVIEW\` | **91.047** | Categoria de origem existente; falta validação semântica/editorial |
| \`NO_OFFICIAL_CATEGORY\` | **88.239** | Falta faceta oficial recuperada; obter fonte ou revisão específica |
| \`POLICY_REVIEW\` | **15.678** | Risco ou categoria protegida: não promover automaticamente |
| \`SOURCE_CONFLICT\` | **0** | Categoria em conflito: bloqueio se aparecer |
| \`DATA_REPAIR\` | **0** | Reparo estrutural: bloqueio se aparecer |
| \`MODERATION_REVIEW\` | **0** | Moderação específica: bloqueio se aparecer |
| \`OTHER_HOLD\` | **0** | Fallthrough fail-closed |
| **TOTAL** | **194.964** | **0 aprovações novas** |

**282** entre os 8.685 anteriormente elegíveis possuem faceta protegida ou conflito: mantêm o histórico, mas são barrados nas novas interfaces protegidas. Não deduzir que tenham sido publicados nem que suas URLs antigas sejam inválidas. A análise de resultados existentes requer auditoria separada.

### Oportunidades por densidade de catálogo (não previsões de venda)

Na fila editorial, os grupos com maior diversidade observada incluem peças automotivas (19.449 pendentes / 845 lojas, com necessidade de cuidado técnico), melhoria doméstica (5.026 / 607), utensílios de cozinha (2.013 / 491), decoração (1.122 / 459) e móveis (7.313 / 403). Estes indicadores **medem oferta/revisão disponível**, não conversão comercial, CTR, comissão, lucro ou qualidade dos anúncios. Itens potencialmente ligados à segurança demandam verificação aprofundada.

## Limites e próximos passos

1. **C22:** propor classificação/revisão para amostras de \`TAXONOMY_REVIEW\` (91.047) a partir de evidência real de título + categorias L1/L2/L3, sem \`UPDATE\` de \`products\` ou \`product_taxonomy\` e sem autoaprovação. Testar falsos positivos por nicho antes de qualquer promoção.
2. Auditar também \`Catalog.candidates\`, \`Catalog.select_products\`, eventuais roteadores legados e interfaces de artigos para cobrir todo caminho do planejamento à publicação; \`Catalog.for_conversion\` bloqueia novas conversões, **mas C21 não certifica todos os writers de produção**.
3. Retomar a integração supervisionada ao orquestrador Blogger/WordPress somente quando houver um blog/tema/campanha real, preservando SEO, conteúdo original, validação de links, rollback e estado separado por site.
4. Coletar métricas reais autorizadas de tráfego/cliques/vendas por campanha antes de alegar ganho de conversão. Não expandir ritmo de API Shopee nem pré-converter em massa sem verificar cotas e pertinência editorial.
5. Para futura promoção, revisar \`main\` e histórico atual da PR #52, gates de concorrência, flags, publicadores, integridade e possibilidade de rollback; **não liberar LIVE automaticamente**.

**Estado ao fechar o C21:** código + testes + auditoria R2 real aprovados. Catálogo e links comerciais preexistentes intactos, LIVE OFF, PR #52 em DRAFT. Workflows temporários de canário devem ser excluídos após a execução final; guardar somente links dos runs e este checkpoint.
