# V31 Hub Editorial Shopee — Blogger & WordPress

### C23 — Nova chave Shopee validada após rotação (18/11/2026)

- Proprietário confirmou rotação e atualização de `V31_EDITORIAL_SHOPEE_APP_SECRET` no GitHub Environment. [Canário autenticado 44302637196](https://github.com/adelrib27/blogger-automation1/actions/runs/44302637196) **SUCCESS**, uma única consulta de leitura `productOfferV2` (`V31_SHOPEE_API_PASS`) e **230 testes PASS**, sem mutações, R2 writes ou posts. Workflow temporário removido.
- **Pendente ação manual GitHub:** restringir `Settings → Environments → v31-editorial-safe → Deployment branches and tags` para apenas `main` e revisar aprovações. A chave foi validada, mas o segredo ainda pôde ser usado em canário da branch feature, então não é prudente habilitar operações LIVE antes da proteção. [Issue #53](https://github.com/adelrib27/blogger-automation1/issues/53).
- [Checkpoint C23](CHECKPOINT_C23_SHOPEE_SECRET_ROTATED_2026-11-18.md). Código `V31-EDITORIAL-C23-SHOPEE-ROTATED-AUTH-PASS-230TESTS-20261118`. PR #52 permanece DRAFT, `main` e Pinterest intocados. Falta de métricas de vendas/comissões não é bloqueio técnico.

### C22 — E2E de seleção por nicho e campanha, pronto para liberação supervisionada (17/11/2026)

- **230 testes V31 PASS + self-tests Casa, Oficina e originalidade cross-blog PASS**, [canário R2 real 44196154349](https://github.com/adelrib27/blogger-automation1/actions/runs/44196154349). 203.649 SKUs, 17 links reais anteriores intactos, 8.403 historicamente elegíveis que passam no gate adicional de origem, 194.964 ainda em revisão e zero conversões/publicações nessa prova.
- **Fluxo completo de preparação (SAFE):** `site_launch_plan.py` vincula tema real a nicho/campanha do blog cadastrado ou mantém blog futuro sem campanha inventada; `review_proposals.py` seleciona lotes de curadoria manual por categoria oficial e título. `Catalog.candidates/select_products`, `editorial.py`, fallback v2.3 WordPress e `link_warmup.py` agora respeitam categoria protegida/conflitante **antes de gerar pautas, selecionar ofertas ou tentar converter**. Os três WordPress têm testes integrados no R2 real.
- **Estoque de fallback ainda incompleto:** Casa 4/9, Oficina 4/6 e Radar 8/15, total faltante **14 ofertas afiliadas reais**; as categorias exigidas estão representadas. Não confundir classificação histórica com autorização LIVE. Repor sob limite 1–3 mutations/rodada após resolver o bloqueio administrativo, verificar persistência e shadow.
- **Ação manual necessária antes de LIVE:** comprovar rotação do Shopee App Secret previamente exposto e restringir o Environment GitHub `v31-editorial-safe` à branch `main`. PR #52 continua DRAFT; **nenhuma rotina de publicação, loja ou Pinterest foi ligada**. A ausência de estatísticas comerciais de vendas/comissões NÃO é bloqueio técnico; não simular tais métricas.
- [Checkpoint C22](CHECKPOINT_C22_E2E_READINESS_R2_2026-11-17.md), continuidade `V31-EDITORIAL-C22-R2-203649-8403SAFE-14GAP-17LINKS-230TESTS-20261117`.

### C21 — Curadoria exaustiva e bloqueio de conversão por fonte (17/11/2026)

- **Auditoria R2 real:** 203.649 produtos, 203.649 entradas FTS5, 17 URLs afiliadas comerciais preservadas. Os 194.964 pendentes agora se distribuem em **91.047 revisão de taxonomia**, **88.239 sem categoria oficial vinculada** e **15.678 retidos por política**; as outras quatro filas estão zeradas na fotografia atual. O resultado não promoveu ninguém.
- **Segurança comercial:** **282 itens historicamente elegíveis** apresentaram categoria sensível ou conflito de origem; novos gates em `source_policy_gate.py`, `Catalog.for_conversion`, `library_pool.library_candidates`, `universal_index.lookup` e `source_category_index.browse_source` impedem seu uso comercial na nova rota, preservando URLs existentes e o legado. O gate é somente leitura e não cria schema em dry-run.
- **[Canário R2 real 44191963790](https://github.com/adelrib27/blogger-automation1/actions/runs/44191963790): SUCCESS, 213 testes.** Integridade, contagem das 7 filas, C20, bloqueios de fontes, pool e consulta universal aprovados. Nenhuma chamada de conversão/API Shopee, nenhuma escrita R2, blog, post ou Pin.
- Diagnóstico semanal está **preparado, mas OFF** por `V31_EDITORIAL_C21_AUDIT_ENABLED`, dependente de eventual merge revisado para `main`; a PR #52 continua DRAFT e os publicadores existentes não foram alterados. [Checkpoint C21](CHECKPOINT_C21_CURATION_TRIAGE_R2_2026-11-17.md), continuidade `V31-EDITORIAL-C21-R2-203649-194964-282GUARDS-17LINKS-213TESTS-20261117`.
- Próxima etapa C22: propostas **não publicáveis** de revisão com evidência real por produto e tema, análise de falsos positivos, integração segura com planejadores Blogger/WordPress e observabilidade de conversão apenas com dados reais.

### C20 — Intake SAFE para blogs futuros e fila separada de revisão (17/11/2026)

- O tema do próximo blog **não é antecipado**: `future_site_intake.py` recebe assunto e plataforma (Blogger ou WordPress) quando solicitados, consulta categorias L1/L2 e entrega separadamente candidatos já elegíveis e itens **pendentes de revisão**, com causas de bloqueio. `product_discovery.discover(..., include_review=True, review_only=True)` impede mistura entre os dois grupos.
- O seletor não cria blogs, não reserva pautas, não converte links, não atribui campanha a blogs inexistentes, não aprova automaticamente produtos e nunca publica. A saída de CI é agregada, sem títulos/URLs/IDs. Links de campanhas anteriores jamais são reutilizados em outro blog.
- **203 testes offline PASS** no [run 44185865913](https://github.com/adelrib27/blogger-automation1/actions/runs/44185865913). **Canário R2 real PASS** no [run 44186244836](https://github.com/adelrib27/blogger-automation1/actions/runs/44186244836): 203.649 produtos + 203.649 índices FTS5 e 17 links preservados; consultas Air Fryer/Guarda-Roupa/Freio com 12 candidatos aprovados e 12 em fila de revisão cada, **0** escritas R2, conversões, posts ou blogs criados.
- Os **194.964 pendentes do C19 não foram liberados**. Resta integrar o adaptador aos geradores existentes após autorização para um blog concreto, desenvolver curadoria adicional e controlar conversões reais por campanha. PR #52 continua DRAFT, main e flags LIVE intocadas. [Checkpoint C20](CHECKPOINT_C20_SAFE_FUTURE_SITE_R2_2026-11-17.md), código `V31-EDITORIAL-C20-R2-INTAKE-203649-17LINKS-203TESTS-20261117`.

## Escopo canônico (15/11/2026)

Este projeto opera **exclusivamente para blogs Blogger e WordPress**. Pinterest e redes sociais têm projetos separados e **não fazem parte** deste módulo.

Repositório: `adelrib27/blogger-automation1`. A implantação reside em uma branch isolada. Nenhuma automação de produção foi modificada.

### Secrets e variáveis do Hub (centralizado)

**Registro oficial de nomes e instruções:** [SECRETS.md](SECRETS.md)  
**Manifesto legível por máquina:** [credentials_registry.json](credentials_registry.json)  
**Verificação sem revelar valores:** `python -m affiliate_hub_v31.credentials --profile manifest`  
**Workflow manual SAFE:** `.github/workflows/v31_editorial_secret_inventory_safe.yml` (disponível para execução manual após inclusão na branch padrão).

Namespace isolado: `V31_EDITORIAL_...`. Nenhuma credencial real é versionada aqui, e os workflows comerciais existentes permanecem intactos. **Status atualizado:** Secrets e Variables no GitHub Environment `v31-editorial-safe` foram cadastrados e validados pelos testes reais do R2; consulte os checkpoints C3.2 e C4/C5.



### C19 — Índice FTS5 de alta escala no R2, com fallback e prova de equivalência (17/11/2026)

- **Índice textual real persistido:** `v31_catalog_fts` no SQLite privado Cloudflare R2 com **203.649 produtos indexados** por título/descrição; `title_index.py` usa FTS5 somente quando disponível, com termos MATCH sanitizados e fallback ao modo anterior quando não há índice.
- **Seleção editorial intacta:** `product_discovery.py` usa FTS5 como pré-filtro; a validação de aprovação, relevância, loja, campanha correta e `can_publish=False` permanece exatamente igual. [Migração R2 real 44181139736](https://github.com/adelrib27/blogger-automation1/actions/runs/44181139736) **SUCCESS, 195 testes**, confirmou rankings iguais em três temas, **17 links afiliados**, **8.685 itens elegíveis** e 203.649 produtos preservados; R2 salvo uma vez e restaurado sem retenção pendente.
- **Medição em catálogo REAL:** [dry-run 44180894099](https://github.com/adelrib27/blogger-automation1/actions/runs/44180894099): 3 consultas **5,39 s → 1,16 s** (~4,7x); [gravação real 44181139736](https://github.com/adelrib27/blogger-automation1/actions/runs/44181139736): **7,55 s → 1,59 s** (~4,7x). São comparações de amostra, não promessa de throughput de produção.
- **Manutenção automática do índice:** `ingest.py` e `catalog_expansion.py` recompõem FTS5 durante importações futuras se a tabela já existe, sem reindexar snapshots legados que ainda não o possuem. Testes para importação incremental e de 2 feeds foram adicionados.
- [Regressão final R2 real 44181357095](https://github.com/adelrib27/blogger-automation1/actions/runs/44181357095): **PASS**, índice de 203.649 SKUs gravado/restaurado, 17 URLs de afiliado preservadas, seleção contextual C18 PASS, shadow Casa/Oficina/Radar PASS, adaptador Radar com erro 1000 **SIMULADO** PASS; nenhum artigo publicado.
- Nenhum cron LIVE ativado, nenhuma chamada à Shopee, nenhum post ou alteração das lojas. [Checkpoint C19](CHECKPOINT_C19_FTS5_REAL_R2_2026-11-17.md), código `V31-EDITORIAL-C19-R2-FTS5-203649-17LINKS-20261117`.

### C18 — Seleção comercial por tema de blogs futuros, sem adivinhar nichos (17/11/2026)

- `curation_audit.py` identifica divergências entre feeds e categorias que exigem revisão reforçada. [R2 real 44177966028](https://github.com/adelrib27/blogger-automation1/actions/runs/44177966028): **424 itens em ambos os feeds, 0 divergências entre L1/L2**, 17 links antigos preservados, sem writes.
- `product_discovery.py`: `suggest_category_paths(catalog,topic)` descobre rotas reais L1/L2 pelo **assunto informado pelo usuário**, sem blog predefinido; `discover(catalog,topic,category,subcategory,campaign,max_per_shop)` classifica pertinência textual, diversidade de lojas e estado do cache. **Só candidatos anteriormente aprovados** na seleção normal; revisão opcional separada. Links afiliados nunca são copiados entre campanhas; nenhuma avaliação/preço/comissão/venda é inventada e `can_publish=False` até gates editoriais futuros.
- [Canário REAL 44179473566](https://github.com/adelrib27/blogger-automation1/actions/runs/44179473566) **175/175 testes PASS**: `Air Fryer → home appliances/kitchen appliances`, `Guarda Roupa → home living/furniture`, `Freio → spare parts and accessories for vehicles/spare parts for automobiles`; amostras com 12 lojas distintas e 0 links da campanha errada. Nenhuma API Shopee, escrita R2, blog criado ou artigo publicado.
- **Não é garantia de conversão/venda**: o ranking atual usa correspondência textual, nunca métricas comerciais fabricadas. Para escala maior faltam índice de texto persistente (C19), curadoria segura ampliada e integração supervisionada dos geradores existentes.
- [Checkpoint C18](CHECKPOINT_C18_SAFE_DISCOVERY_2026-11-17.md), `V31-EDITORIAL-C18-R2-SAFE-TOPIC-DISCOVERY-20261117`.

### C16/C17 — Biblioteca CUMULATIVA real + categorias oficiais L1/L2/L3 (17/11/2026)

- **R2 real atualizado** em [GitHub Actions 44127603439](https://github.com/adelrib27/blogger-automation1/actions/runs/44127603439): agora **203.649 SKUs distintos**, incorporando **94.142 produtos novos** dos dois CSVs sem apagar os 109.507 antigos; **8.685 produtos aprovados** pelos critérios editoriais atuais, **194.964 continuam sob revisão**; os **17 links afiliados anteriores foram preservados** em suas respectivas campanhas. Um único snapshot privado foi salvo e restaurado, com hashes e integridade confirmados, sem publicação ou conversão de links.
- O feed oficial de 100 mil linhas contém `globalCategory1/2/3`; o de 10 mil possui `globalCategory1/2`. O índice `source_category_index.py` grava a **hierarquia OFICIAL por produto/fonte**, independentemente de existir blog sobre aquele tema. Os feeds atuais geraram **110.000 registros de categorias para 109.576 produtos distintos**, cobrindo **29 categorias L1**; dados antigos que não apareceram nos feeds novos ficam preservados para futuras classificações, não apagados.
- **Navegação por categoria/nicho:** `category_hierarchy(cat,level1,level2)` permite navegar L1 → L2 → L3 e conhecer separadamente a contagem **aprovada editorialmente**; `browse_source(cat,level1,level2,level3,campaign)` encontra candidatos e só devolve URL afiliada já convertida para a campanha informada, sem pré-selecionar blogs. [QA real 44128756858](https://github.com/adelrib27/blogger-automation1/actions/runs/44128756858) **166/166 testes PASS**, 29 categorias L1, 17 níveis L2 em Casa/Home & Living e 10 L3 em Furniture, mais Radar com erro 1000 simulado e R2 REAL 5/5/5.
- **Estado de aprovação não é categoria:** um produto pode ter categoria oficial no CSV e ainda estar em revisão (por exemplo, áreas sensíveis, títulos ambíguos ou dados incompletos). Esses itens NÃO são liberados automaticamente para anúncios; o catálogo evita informações e comissões fabricadas.
- `catalog_expansion.py` faz importação **append-only**, compara SHA-256 dos produtos/taxonomias/links antigos antes e depois e novamente depois de restaurar o snapshot R2. A execução normal sem `--execute` é dry-run (sem gravação).
- **Renovação autônoma preparada, ainda OFF:** workflow `.github/workflows/v31_c17_catalog_refresh_safe.yml`, apenas `main`, manual com confirmação ou cron semanal guardado por `V31_EDITORIAL_CATALOG_REFRESH_ENABLED=='true'`. O cron **não foi habilitado** e o PR não foi mesclado; produção, publicadores e páginas de loja não foram alterados.
- [Checkpoint C17](CHECKPOINT_C17_REAL_UNIVERSAL_CATALOG_2026-11-17.md) — código `V31-EDITORIAL-C17-R2-203649-OFFICIAL-CATEGORIES-20261117`. **Próxima etapa C18:** classificar com segurança mais itens a partir da hierarquia Shopee, ranking de produtos usando somente dados reais e pré-conversão gradual por campanha, respeitando a saúde da API.

### C15 — Índice universal por categoria e nicho (17/11/2026)

- **Pedido central do usuário:** organizar o catálogo dos dois CSVs por categorias e nichos, para que um novo blog escolha os produtos adequados **quando o tema for solicitado**, não antecipar as demandas de blogs inexistentes. Não criar um segundo gerador de artigos nem substituir o conversor Shopee que já funciona.
- **`universal_index.py`** fornece `grouped_inventory(catalog)` (todo o acervo, incluindo pendentes) e `lookup(catalog,category,niche,query,campaign)` (produtos aprovados para um tema informado; link afiliado somente da própria campanha). Integra-se à tabela `product_taxonomy` e ao SQLite já guardado no R2, sem dependência de um blog.
- **Auditoria R2 REAL**: [run 44115748746](https://github.com/adelrib27/blogger-automation1/actions/runs/44115748746), **109.507 produtos**, **4.674 atualmente classificados/aprovados** e **104.833 ainda em revisão**. Isso comprova que **a classificação de toda a base ainda NÃO está concluída**; pendentes ficam no catálogo e nunca são publicados como classificados.
- A pré-conversão geral `library_pool.py` é opcional e independente dos blogs, não uma obrigação de definir previamente novos nichos/campanhas. A geração de URL afiliada para cada blog exige a campanha correta. **Nenhuma campanha universal foi inventada/ativada.**
- **Pinterest/Pins fora do escopo**; Worker v1.0 de outro fluxo não deve ser presumido como componente existente ou dependência do V31. Nenhuma página de loja alterada.
- [Checkpoint C15](CHECKPOINT_C15_UNIVERSAL_LIBRARY_2026-11-17.md).

### C14 — Main reconciliada com segurança, 17 links reais e flags OFF (17/11/2026)

- [Prova de merge seco](https://github.com/adelrib27/blogger-automation1/actions/runs/44089068660): YAML de 118 workflows e 137/137 testes PASS, sem conflitos.
- [Sincronização real main → feature](https://github.com/adelrib27/blogger-automation1/actions/runs/44089292281): reconciliou branch V31 com a main, **zero arquivos de dados editoriais alterados em relação à main**, 137 V31 + 24 Casa + 21 Oficina + guard cross-blog PASS. `main` intocada, PR ainda DRAFT.
- [Auditoria dos interruptores](https://github.com/adelrib27/blogger-automation1/actions/runs/44089682722): **todos OFF** (release global, Casa, Oficina, Radar, reutilização, cron de cache e shadow), nenhum fallback de publicação ativado.
- [Novo lote real de 3 conversões](https://github.com/adelrib27/blogger-automation1/actions/runs/44089505226): 3/3 links afiliados Shopee reais, um por campanha, R2 salvo/restaurado sem pendências, 0 posts. **Casa 4/9, Oficina 4/6, Radar 8/15**; 5/5 categorias Radar, cache total **17 links** (incluindo 1 Blogger). Ainda faltam **14 links** para as reservas iniciais.
- Todos os workflows transitórios de C14 foram excluídos depois da validação; não foi acionado nenhum schedule de lojas ou publicador V31.
- [Checkpoint completo C14](CHECKPOINT_C14_BRANCH_SYNC_R2_17_2026-11-17.md), código `V31-EDITORIAL-C14-MAIN-SYNC-137-TESTS-R2-17LINKS-FLAGS-OFF-20261117`. **C15:** reserva gradual restante, revalidação da main, gate de release por blog com rollback.

### C13 — Canário R2 REAL, histórico atual da main e 14 links válidos (17/11/2026)

- [Canário E2E C13](https://github.com/adelrib27/blogger-automation1/actions/runs/44086403960) **SUCCESS**: 137/137 testes V31, 24 Casa, 21 Oficina, guard cross-blog; construtores originais Casa/Oficina + Radar erro 1000 **simulado** com R2 real e 5 slots, **ZERO publicação**.
- Auditoria do checkout da branch e do **histórico atual da `main`** em pasta temporária: Casa **46 publicações, 41 itens com corpo histórico verificável**, Oficina **12 publicações, apenas 1 item com corpo verificável**. Ausência do corpo proíbe reutilização do produto; o PR está divergente da `main` e precisa ser reconciliado antes do merge.
- `queue_identity.py`: durante o opt-in editorial, IDs de fila são sempre maiores que os drafts já existentes em `data/generated`, mesmo quando fila antiga foi zerada. Protege os artigos antigos de sobrescrita.
- [Lote real controlado](https://github.com/adelrib27/blogger-automation1/actions/runs/44086617987) **SUCCESS**: 3 tentativas/3 links afiliados Shopee convertidos (1 por campanha), 1 snapshot R2 persistido e restaurado/verificado, nenhum post.
- **Novo estoque:** Casa **3/9**, Oficina **3/6**, Radar **7/15** links em cache, 5/5 categorias Radar cobertas; total **14 links incluindo 1 Blogger**. Faltam 17 links para a reserva inicial de três dias. Todos permanecem `NOT_READY` para fallback automático.
- Workflows C13 temporários retirados; **nenhum agendamento de loja modificado e nenhum switch de publicação ativado**.
- [Checkpoint C13](CHECKPOINT_C13_REAL_CANARY_2026-11-17.md), continuidade `V31-EDITORIAL-C13-CANARY-137-REAL-R2-14-LINKS-20261117`. Próximo passo: C14, reposição gradual e reconciliação de PR/produção.

### C11/C12 — Reuso editorial sem repetição de título nem corpo (16/11/2026)

- **Recurso opt-in e desativado por padrão**: além de `V31_EDITORIAL_C9_RELEASE_ENABLED` e da flag de cada blog, exige `V31_EDITORIAL_PRODUCT_REUSE_ENABLED=true`. Reutilizar o produto NÃO equivale a repetir a matéria.
- `reuse_policy.py`: limite-piloto de 2 artigos por produto no mesmo blog, checagem de histórico/tema/título e, na C12, comparação do **editorial_html** contra os arquivos antigos do mesmo produto e título publicado. Se faltar documento histórico, **bloquear antes do WordPress**.
- Integrado apenas aos scripts existentes de **Casa e Oficina** (construtor de fila, Qwen3, publisher), sem novos geradores; todos os controles legados continuam quando as flags estão OFF. O Radar conserva os critérios próprios até canário específico.
- [QA C11 real dos scripts originais](https://github.com/adelrib27/blogger-automation1/actions/runs/43910337180): **125 testes V31 + 24 Casa + 21 Oficina + cross-blog PASS**, sem publicação.
- [QA C12](https://github.com/adelrib27/blogger-automation1/actions/runs/43911094183): **126/126 testes V31 PASS**, incluindo corpo igual/corpo realmente diferente/ausência de histórico. Código da etapa ainda não mesclado, nenhum post LIVE alterado.
- [Checkpoint C11](CHECKPOINT_C11_EDITORIAL_REUSE_SAFE_2026-11-16.md) e [Checkpoint C12](CHECKPOINT_C12_BODY_ORIGINALITY_SAFE_2026-11-16.md). Próxima liberação depende de **estoque suficiente + histórico real + canário não publicável**.
- **Hipótese futura registrada no Runbook C10:** as páginas de loja de todos os blogs fazem rotação diária e podem estar concentrando chamadas com os agendamentos editoriais; depois de concluir V31, medir consumo e avaliar rotação mensal distribuída. **Nada alterado nas lojas agora.**

### C10 — Liberação futura protegida por dois switches (16/11/2026)

- **Novo interruptor global** `V31_EDITORIAL_C9_RELEASE_ENABLED` em conjunto com a flag de **cada blog**. **Ambos OFF/ausentes** => automações antigas continuam sem o roteador.
- Somente após revisão do PR, auditoria de estoque, teste canário sem publicação e validação de originalidade por **pauta/título** será possível habilitar a execução comercial por blog. O antigo publicador poderá publicar posts ao ativar as flags; **NÃO ativar sem critérios cumpridos**.
- **Rollback:** desabilitar a flag global para toda a rede ou a flag específica; cancelar manualmente runs já iniciados. Sem merge automático.
- [Runbook operacional C10](C10_RELEASE_RUNBOOK_2026-11-16.md), código `V31-EDITORIAL-C10-CANARY-READY-BUT-OFF-20261116`.

### C9 — Ponte reversível API→R2 para 3 WordPress; 5 slots Radar REAIS (16/11/2026)

- **Não substitui publicadores**: adiciona um workflow de descoberta reutilizável `v31_c9_discovery_reusable.yml` (somente API Shopee/R2, sem secrets WordPress) e integra por flags **OFF por padrão** os trabalhos já existentes de Casa, Oficina e fila diária Radar, somente na **branch do PR #52**. O branch `main` continua intocado.
- **Rollback por blog:** `V31_CASA_R2_FALLBACK_ENABLED`, `V31_OFICINA_R2_FALLBACK_ENABLED`, `V31_RADAR_R2_FALLBACK_ENABLED`: ausente/`false` => scanner antigo; `true` => workflow compartilhado. Falha do novo job não libera o publicador.
- **Fallback insuficiente bloqueado:** `--min-fallback` exige ao menos 3, 2 e 5 links válidos respectivamente; não interfere na prioridade da API Shopee quando ela funciona.
- **Radar preservado:** `radar_legacy_adapter.py` usa o seletor ORIGINAL de 5 categorias, 5 lojas e 5 keywords. `fallback_v23.py` passou a carregar `shopId` e até 3 lojas alternativas por keyword.
- **Catálogo real/Radar:** [run 43894290446](https://github.com/adelrib27/blogger-automation1/actions/runs/43894290446) PASS — corrigiu conflito de loja com **1 link Shopee REAL**, montou fila Radar completa em diretório temporário. [run 43894779041](https://github.com/adelrib27/blogger-automation1/actions/runs/43894779041) PASS — **scanner Radar original + erro 1000 simulado + R2 REAL + fila 5/5**, **114/114 testes offline** e zero publicações.
- **Inventário:** [run 43892555790](https://github.com/adelrib27/blogger-automation1/actions/runs/43892555790), **113/113 testes**, Radar com oferta CSV nas 5 categorias. Casa: `Cama Mesa Banho` sem elegíveis; Oficina: `Seguranca e Protecao` sem elegíveis sob regras atuais, sem inventar produtos para completar.
- Cache R2 atual: **Casa 2/9**, **Oficina 2/6**, **Radar 6/15** (cinco categorias cobertas), **Blogger Air Fryers 1**; **11 links** no total. Ainda insuficiente para a meta de 3 dias; todos `NOT_READY` no shadow. O sistema NÃO foi mesclado nem ativado em produção.
- **Checkpoint:** [C9 — ponte 3WP + Radar completo](CHECKPOINT_C9_3WP_R2_2026-11-16.md), `V31-EDITORIAL-C9-3WP-API1000-R2-FULL-QUEUE-SAFE-20261116`.
- **Próximo gate C10:** revisão/rollout canário por blog, estoque por campanha, reconciliação e originalidade de assunto/título. Nunca desativar dedup de conteúdo por causa da autorização de reutilizar produtos.

### C8 — Shadow read-only e cache multi-site com orçamento (16/11/2026)

- **Observação REAL do R2:** [run 43886181941](https://github.com/adelrib27/blogger-automation1/actions/runs/43886181941), **PASS** (94 testes); `shadow_audit.py` compara links utilizáveis com reservas de 3 dias, com perfis expansíveis em `shadow.d/*.json`.
- **Reposição REAL controlada:** [run 43887349902](https://github.com/adelrib27/blogger-automation1/actions/runs/43887349902), **PASS** (101 testes): **3 mutations / 3 links novos**, um por campanha WordPress, único snapshot R2, restauração validada, nenhum artigo/publicação.
- **Estado atual:** Casa **2/9**, Oficina **2/6**, Radar **2/15** links utilizáveis. No Radar, **2/5 categorias** obrigatórias cobertas. Todos `NOT_READY` para uso automático LIVE.
- `cache_replenish.py`: rodízio de campanhas, máxima global de **3 tentativas por execução**; prioriza categorias ainda sem link. `--execute` explicitamente necessário para mutations; sem isso a operação é dry-run. **NUNCA publica**.
- Novos workflows `v31_c8_shadow_safe.yml` e `v31_c8_cache_replenish_safe.yml`: em `main` somente após PR revisado, schedules protegidos por `V31_EDITORIAL_SHADOW_ENABLED` e `V31_EDITORIAL_CACHE_WARMUP_ENABLED` (ambos **desligados por padrão**), manual com confirmação para conversão.
- Workflows temporários de teste removidos, **workflows comerciais antigos intocados**.
- [Checkpoint C8](CHECKPOINT_C8_SHADOW_REPLENISH_2026-11-16.md), código `V31-EDITORIAL-C8-SHADOW-REPLENISH-REAL-PASS-20261116`. Próxima etapa: integração por blog com rollback, expansão de cache e fila Radar completa.

### C7 — R2 REAL integrado às filas dos três WordPress (16/11/2026)

- **Casa e Decoração:** [run 43878643279](https://github.com/adelrib27/blogger-automation1/actions/runs/43878643279) PASS. Uma conversão Shopee REAL (`casaedecoracaowp`), cache R2, construtor de fila original validado sem publicação.
- **Oficina & Garagem:** [run 43879142065](https://github.com/adelrib27/blogger-automation1/actions/runs/43879142065) PASS. Uma conversão Shopee REAL (`oficinawp`), cache R2, construtor original validado sem publicação.
- **Erro 1000:** [run 43879995986](https://github.com/adelrib27/blogger-automation1/actions/runs/43879995986) PASS com erro 1000 **simulado** nos scanners originais e recuperação de ofertas do R2 **real**; circuito interrompe novas chamadas no primeiro erro.
- **Radar Tech BR:** [run 43880690866](https://github.com/adelrib27/blogger-automation1/actions/runs/43880690866) PASS. Uma conversão Shopee REAL (`radarwp`) e validação de **um slot** no `prepare_slot.py` original; **fila de 5 categorias ainda não validada**.
- **89/89 testes SAFE aprovados**, sem publicar artigos ou modificar workflows LIVE. Gatilhos temporários removidos. Estoque de apenas **1 link afiliado por campanha** ainda é insuficiente para rotina diária de 50 blogs.
- [Checkpoint C7 completo](CHECKPOINT_C7_REAL_3WP_2026-11-16.md), continuidade: `V31-EDITORIAL-C7-R2-3WP-FALLBACK-SAFE-20261116`.
- Próximo passo C8: pré-conversão de lotes com limites/cotas e teste em shadow mode dos fluxos existentes, migrando controles de repetição de produto para originalidade de pauta/título.

### C6 — Fallback CSV/R2 universal para blogs atuais e futuros (16/11/2026)

- **Objetivo corrigido:** os três WordPress existentes **já possuem geração de artigos**. O V31 fornece produtos: **API Shopee primeiro; erro 1000 confirmado sem ofertas úteis → CSV/R2**; sem modificar os publicadores.
- [Cadastro extensível de blogs](sites.d/README.md): inclui `site_routes.json` e registros independentes em `sites.d/*.json`. Atualmente **18 Blogger e 3 WordPress**, com suporte a novos sites sem alterar o motor; teste com **60 blogs fictícios adicionais**.
- [fallback_v23.py](fallback_v23.py): usa somente links de afiliado já convertidos na campanha de cada site; gera `ranking.json`, `intent_report.json`, CSV e relatórios compatíveis com as filas v2.3, sem inventar métricas comerciais.
- [opportunity_router.py](opportunity_router.py): mantém o scanner antigo, observa código 1000, usa fallback quando necessário e só entrega artefatos completos. Outros erros bloqueiam a rotina.
- **86 testes offline aprovados**, incluindo simulação do scanner real de Casa e Decoração com erro 1000. **Nenhum workflow de publicação LIVE foi alterado e o fallback REAL ainda não foi acionado nos blogs.**
- **Próximo requisito:** pré-conversão de links por campanha enquanto a API estiver saudável, teste de compatibilidade das filas e adaptador adicional para Radar (fila por slots).
- [Checkpoint C6 multisite](CHECKPOINT_C6_UNIVERSAL_FALLBACK_2026-11-16.md). Continuidade: `V31-EDITORIAL-C6-UNIVERSAL-FALLBACK-20261116-SAFE`.

### C4/C5 — Pilotos REAIS: conversão e originalidade de pautas

- **C4** [run 43771181969](https://github.com/adelrib27/blogger-automation1/actions/runs/43771181969): uma conversão `generateShortLink` real aprovada, link salvo no R2 e cache reutilizado sem nova API; restauração validada.
- **C5** [run 43771386845](https://github.com/adelrib27/blogger-automation1/actions/runs/43771386845): o **mesmo produto real** usado em **dois blogs Blogger**, com dois títulos/ângulos diferentes mantendo `air fryer`; ambos em `REVIEW_REQUIRED`, sem artigo/publicação.
- R2 restringe snapshots ao **atual + anterior**, e limpeza na execução real completada sem pendência.
- Todos os workflows transitórios de teste foram removidos após sucesso.
- **Checkpoint:** [C4/C5 — conversão real e pautas originais](CHECKPOINT_C4_C5_2026-11-15.md), código `V31-EDITORIAL-C5-ORIGINALIDADE-REAL-PASS-20261115`.
- Ainda faltam: publicar **rascunhos reais** nas plataformas, revisar textos completos e regras de agendamento/ativação gradual; credenciais LIVE e rotação da App Secret exposta precisam ser verificadas.

### C3 — Cloudflare R2 privado criado e verificado

- **Bucket existente:** `v31-editorial-shopee`, na conta selecionada pelo proprietário, classe **Standard**, sem domínio público `r2.dev` ou domínio personalizado.
- **Comprovado:** ativação da assinatura no painel e criação/consulta pela API Cloudflare. **Marco histórico C3:** naquele momento ainda não havia objetos; o primeiro catálogo real foi gravado e restaurado posteriormente em C3.2.
- **Pendente:** criar credenciais S3 limitadas ao bucket e cadastrá-las no Environment GitHub `v31-editorial-safe`, configurar `V31_EDITORIAL_R2_ACCOUNT_ID` e `V31_EDITORIAL_R2_BUCKET`; validar conexão real e só então importar os feeds.
- **Checkpoint:** [C3 — bucket privado criado](CHECKPOINT_C3_R2_2026-11-15.md).
- **Continuidade:** `V31-EDITORIAL-C3-R2-PRIVATE-20261115-CREATED`.

### C2.1 — Dois feeds REAIS auditados em GitHub Actions

- **Prova:** [run 43732094595](https://github.com/adelrib27/blogger-automation1/actions/runs/43732094595), `V31_C2_REAL_FEEDS_PASS`. Foram lidos **100.000 + 10.000 registros**, com cabeçalhos de **24 e 16 colunas**.
- **493 duplicações preliminares** e **109.507 chaves diferentes** pelo deduplicador atual. Os feeds não possuem coluna reconhecida de `shopId`; revisar identificadores alternativos antes de tratar essas chaves como produtos comerciais distintos.
- **4.758 registros** corresponderam a nichos na versão inicial da taxonomia, **105.242 ainda sem nicho aprovado**. Não significa descarte definitivo.
- Bugs reais resolvidos: redirecionamento HTTPS interno Shopee e CSV com campos multilinha/aspas. O workflow temporário de auditoria foi removido; dados não foram persistidos.
- **Checkpoint C2.1:** [leitura real, limitações e próximos passos](CHECKPOINT_C2_1_FEEDS_REAIS_2026-11-15.md). Código: `V31-EDITORIAL-C2.1-FEEDS-REAIS-20261115-PASS`.
- **Marco histórico C2.1:** R2 e conversão comercial foram posteriormente validados em C3.2 e C4; a publicação automática nova permanece desativada.

### C2 — Categorias, nichos, feeds e R2 SAFE

**Checkpoint de continuidade:** [C2-2026-11-15](CHECKPOINT_C2_2026-11-15.md)  
**Código:** `V31-EDITORIAL-C2-TAXONOMIA-R2-20261115-SAFE`

- Taxonomia de **20 nichos/15 categorias** em [taxonomy.json](taxonomy.json), com bloqueio de desconhecidos, acessórios e ambiguidades antes da conversão.
- [site_routes.json](site_routes.json): rotas de seleção para **18 blogs Blogger** e **2 WordPress** verificadas no repositório; todas com `publish_enabled=false`.
- [converter.py](converter.py): cliente `generateShortLink` sob demanda, cache por campanha, verificação de domínio e rechecagem após conversão; mutation testada **somente com mocks**.
- [ingest.py](ingest.py): importação de dois CSVs de forma atômica em banco local; [r2_state.py](r2_state.py) versiona backups privados. [ingest_cli.py](ingest_cli.py) pode ser executado na nuvem quando os secrets dos feeds e storage estiverem disponíveis.
- [workflow de importação SAFE](../.github/workflows/v31_editorial_ingest_r2_safe.yml): **manual, apenas main, sem schedule e sem publicação**.
- **Validação C2:** 45/45 testes offline aprovados. Benchmark isolado com 110.000 linhas **sintéticas** passou em 18,41 s no GitHub Actions [run 43728505370](https://github.com/adelrib27/blogger-automation1/actions/runs/43728505370); 105.000 produtos únicos e 5.000 duplicatas planejadas. Isso **não comprova** comportamento ou esquema dos feeds reais. O gatilho temporário de benchmark foi removido.

**Ainda não executados:** download real dos feeds, provisionamento/acesso real ao R2, conversão real `generateShortLink`, publicação Blogger/WordPress. Nenhum serviço LIVE foi alterado. É obrigatória a rotação da chave Shopee anteriormente exposta.

### Objetivo

1. Receber os dois feeds CSV da Shopee em área privada de armazenamento. A contagem histórica relatada é de 100.000 + 10.000 linhas **antes** da deduplicação; esta branch ainda não baixou os arquivos atuais.
2. Importar, normalizar, deduplicar e classificar produtos para revisão editorial antes de publicar.
3. Reutilizar links afiliados já validados por produto/campanha. Para links faltantes, chamar a Shopee Affiliate Open API com autenticação assinada, limites e registro de tentativas.
4. Expor candidatos a adaptadores separados: **Blogger** e **WordPress**, preservando IDs, filtros, HTML comercial e política de cada site.
5. Agendar rotinas de ingestão e publicação na nuvem somente após testes e aprovação do fluxo LIVE.

### Limites de segurança

- Feeds privados, App Secret, tokens, arquivos de catálogo e métricas comerciais não entram no repositório público nem nos logs.
- Github Actions não oferece disco persistente entre execuções: é necessário provisionar backup/estado persistente privado antes de executar de verdade (p.ex. R2 ou banco gerenciado).
- Nunca concluir que URL de produto tem atribuição de afiliado: armazenar somente retorno validado da API ou importação legada verificada.
- Nenhuma integração com Pinterest. Não apagar fluxos Pinterest preexistentes de outros projetos.
- Modo padrão: **SAFE**, sem publicar, sem editar posts, sem ativar schedules e sem emitir links em massa.
- Live Blogger e WordPress exigirão validadores próprios, idempotência, fila de revisão, proteção contra duplicados e opção de rollback.
- Link Shopee pode expirar/mudar; revisão de validade deve preceder publicação.
- Política editorial: não publicar indiscriminadamente produtos não revisados, alegações não confirmadas ou páginas duplicadas.

### O que existe nesta etapa

- `affiliate_hub_v31/catalog.py`: banco SQLite local e importador CSV, deduplicação, revisão básica, cache por campanha, consultas.
- `affiliate_hub_v31/__init__.py`: pacote Python.
- **C1:** 20 testes offline aprovados, e a autenticação Shopee real passou em uma consulta somente leitura; veja C1.3. **C2:** módulo de importação, classificação, conversão por demanda e persistência R2 preparado e coberto por testes offline. Falta cadastrar credenciais de feeds/R2, comprovar o esquema CSV real, testar a mutation de conversão real, conectar os adaptadores e agendar a publicação após aprovação.

### Marco C1.3 — Autenticação Shopee real (15/11/2026)

- **PASS real:** GitHub Actions [execução 43725343531](https://github.com/adelrib27/blogger-automation1/actions/runs/43725343531), saída sanitizada `V31_SHOPEE_API_PASS`.
- **Escopo exato:** consulta `productOfferV2` assinada com credenciais do GitHub Environment `v31-editorial-safe`, solicitando apenas 1 produto; sem publicar, sem converter, sem baixar CSV e sem expor respostas.
- Gatilho transitório de branch criado para essa validação e removido imediatamente após PASS; mantido somente o workflow manual SAFE em draft.
- A chave anteriormente exibida em captura ainda deve ser rotacionada; teste de autenticação **não prova** segurança da credencial.
- Próximas dependências: esquema real dos feeds, credenciais de download, persistência privada e conversor validado por testes.

**Código de continuidade:** `V31-EDITORIAL-C1-API-REAL-PASS-20261115`.

### Próximo marco de validação

`V31-EDITORIAL-C1-20261115-SAFE`

Testes unitários sintéticos **14/14 PASS** em CI após correção de allowlist de encurtadores. Próximo passo: validar o esquema CSV real e os secrets do Environment; depois preparar ingestão em nuvem com persistência privada. Não tratar simulação como implantação concluída.

## Separação operacional

```
Feeds Shopee (privados)
    → catálogo/deduplicação/revisão (privado)
    → links afiliados validados pela Open API (cache privado)
    → seleção editorial e política por site
          ├── adaptador Blogger → SAFE → aprovação LIVE → Blogger
          └── adaptador WordPress → SAFE → aprovação LIVE → WordPress

Pinterest: fora deste projeto.
```
