# Checkpoint C9 — Ponte para automações existentes + fila Radar completa (16/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C9-3WP-API1000-R2-FULL-QUEUE-SAFE-20261116`  
**Repositório:** `adelrib27/blogger-automation1`  
**Branch:** `feature/v31-affiliate-hub-c1-safe-20261115`  
**PR:** [#52 — DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52), sem merge e sem mudança em `main`.

## Objetivo definitivo do usuário

Os três WordPress existentes — Casa e Decoração, Oficina & Garagem, Radar Tech BR — **já têm geradores de artigo, SEO e publicadores automáticos**. Não criar geradores substitutos. V31 é uma **camada central universal de dados**: primeiro API Shopee; se o erro 1000 for confirmado, consultar os CSV Shopee no R2, entregando somente itens com links afiliados **já convertidos para a campanha do site**. O mesmo produto pode ser reutilizado em matérias distintas, contanto que **assunto, intenção e título sejam originais e preservem palavras-chave**. Novos blogs devem ser integrados por cadastro, sem codificar lista fixa de três.

## Ponte reversível preparada na BRANCH (não em main)

- `.github/workflows/v31_c9_discovery_reusable.yml`: workflow **reutilizável** por qualquer blog configurado (site/scanner/config/regras/destino), com acesso isolado a `v31-editorial-safe`. Executa `opportunity_router` API-first, fallback no erro 1000, conta mínima de links, publica apenas **artefatos de dados de oportunidades**, nunca posts. **Não recebe credenciais WordPress/Blogger**.
- **Casa:** alteração exclusiva na branch de `casa_editorial_generate_schedule.yml`, usa `V31_CASA_R2_FALLBACK_ENABLED` (repository variable) e `min_fallback: 3`; OFF => fluxo Shopee antigo, ON => nova descoberta; o job antigo só continua se descoberta nova for `success` e artefato for baixado.
- **Oficina:** alteração exclusiva na branch de `oficina_editorial_autonomous.yml`, usa `V31_OFICINA_R2_FALLBACK_ENABLED` e `min_fallback: 2`, mesma política fail-closed/rollback.
- **Radar:** alteração exclusiva na branch de `radar_fase3_fila_diaria.yml`, usa `V31_RADAR_R2_FALLBACK_ENABLED` e `min_fallback: 5`, depois `radar_legacy_adapter.py` alimenta o **seletor original** de 5 categorias/5 shops/5 keywords e valida atomicamente antes de substituir `data/fase3/fila_dia.json`. Mantém validação e persistência do workflow existente e não altera `radar_editorial_vnext_autonomous.yml`.
- **Defaults seguros:** todas as flags OFF/ausentes, logo as automações da `main` permanecem exatamente iguais. Mesmo após eventual merge, ativação é **por blog**, revertida colocando a respectiva Repository Variable em `false` (não alterar secrets/env de todos os publicadores).
- **Reusabilidade:** onboarding de novos blogs em `sites.d/*.json` e `shadow.d/*.json`; workflow compartilhado aceita projetos com scanner e saída v2.3 compatíveis; formatos de fila personalizados usam apenas adaptador de saída específico.
- `fallback_v23.py`: acrescentou `shopId` e `productLink` do produto original, além de até **3 links de lojas alternativas por keyword**, para não confundir diversidade diária com presença do primeiro produto de cada termo. Não inventa avaliação, preço, desconto, vendas ou comissão.
- `opportunity_router.py`: gate `--min-fallback` barra oferta insuficiente **antes** de substituir o ranking original; com API saudável, continua prioritário, mesmo que estoque R2 seja menor. O circuito interrompe o scanner no PRIMEIRO erro 1000 confirmado.
- `cache_replenish.py` e `c9_radar_shop_diversify.py`: pré-conversão por campanha e reparo direcionado de conflito de lojas, com limite e persistência R2. **Não publicam**.

## Provas reais da C9

1. **[43892029483](https://github.com/adelrib27/blogger-automation1/actions/runs/43892029483)** — **110/110 testes PASS** de integração, flags, fonte API prioritária, fallback insuficiente sem clobber e simulação Radar de fila completa. Após ampliação, **114/114 testes PASS** em [43894779041](https://github.com/adelrib27/blogger-automation1/actions/runs/43894779041).
2. **[43892133372](https://github.com/adelrib27/blogger-automation1/actions/runs/43892133372)** — GitHub **aceitou o contrato do workflow reutilizável**. O job foi corretamente `skipped` porque só executa em `main`; nenhuma mutation/post. O workflow temporário de validação foi removido.
3. **[43892555790](https://github.com/adelrib27/blogger-automation1/actions/runs/43892555790)** — inventário CSV **REAL no R2**, sem escritas/API: Radar possui candidatos elegíveis para TODAS as cinco categorias (Tecnologia 184; Casa & Decoração 209; Cozinha & Utilidades 151; Ferramentas & Automotivo 323; Moda & Beleza 36). Casa: zero na categoria Cama, Mesa e Banho; Oficina: zero em Segurança e Proteção nos critérios atuais. Isso NÃO significa que os produtos tenham links convertidos.
4. **[43892989795](https://github.com/adelrib27/blogger-automation1/actions/runs/43892989795)** — 3 novas conversões Shopee **reais** para o Radar (`radarwp`), sucesso e R2 persistido. Primeiro teste de fila completa **falhou de propósito pelo gate de diversidade**, pois havia 5 categorias/keywords/itens mas somente **4 lojas distintas**; a fila de produção **NÃO** foi alterada.
5. **[43893705873](https://github.com/adelrib27/blogger-automation1/actions/runs/43893705873)** — auditoria READ-ONLY confirmou as 5 categorias tinham uma opção cada e 4 lojas distintas.
6. **[43894290446](https://github.com/adelrib27/blogger-automation1/actions/runs/43894290446)** — reparo **REAL**: `c9_radar_shop_diversify.py` selecionou uma alternativa segura de loja diferente na categoria Tecnologia, converteu **1 link** via Shopee, gravou no R2, e o `c9_radar_full_probe.py` criou em DIRETÓRIO TEMPORÁRIO uma fila Radar completa com **5 categorias + 5 lojas + 5 keywords**, respeitando o algoritmo original. `V31_C9_RADAR_FULL_QUEUE_REAL_R2_PASS`, sem artigo/post.
7. **[43894779041](https://github.com/adelrib27/blogger-automation1/actions/runs/43894779041)** — **SUCCESS**, 114 testes; o **scanner original Radar** recebeu erro 1000 **simulado** em memória, realizou 1 chamada simulada, alternou automaticamente ao R2 **REAL**, consumiu os links já convertidos e gerou a fila original com 5 categorias/5 lojas/5 slots. `V31_C9_RADAR_FULL_ROUTER_ERROR1000_PASS`; nenhuma chamada verdadeira a Shopee/WordPress nesse teste e nenhuma alteração na fila de produção.
8. Os workflows temporários C9 de contratos, inventário, conversões e E2E foram **removidos após execução**; as provas permanecem nos históricos.

## Inventário após as conversões C9

| Campanha | Links convertidos cacheados | Reserva inicial de 3 dias | Categorias do perfil com link |
|---|---:|---:|---:|
| `casaedecoracaowp` | 2 | 9 | 2/8 |
| `oficinawp` | 2 | 6 | 2/6 |
| `radarwp` | 6 | 15 | 5/5 obrigatórias |
| Blogger Air Fryers | 1 | sem perfil shadow C9 | nicho piloto |
| **Total no R2** | **11** | | |

O status de shadow dos três WordPress continua `NOT_READY` para reserva de três dias. **Concluir uma fila Radar diária em teste não implica possuir três dias de estoque ou autorização para publicar.**

## Pendências de liberação (C10)

1. **Não fazer merge ou ativação automática sem validação de rollout.** Flags por blog continuam OFF em `main`. Para rollback imediato, alterar apenas a respectiva flag para `false`.
2. Expandir os links cacheados gradualmente até reservas por campanha e verificar validade das URLs/imagens no momento de publicar. Novos links ainda exigem API Shopee saudável.
3. **Deduplicação editorial:** Casa/Oficina e política Radar legada bloqueiam itens já usados. O usuário prefere liberar reutilização de produtos SOMENTE quando **o assunto, intenção de busca e título forem diferentes**. Essa mudança demanda mecanismo transacional de tópicos/títulos e validação de texto em todos os blogs. Não simplesmente desligar os gates antigos.
4. Preparar **canário por blog** com shadow real em horários e rollback; confirmar monitoramento de API 1000, estatísticas de fallback e ausência de publicação duplicada.
5. Expandir cadastro real além dos 21 registros (18 Blogger/3 WordPress) e perfis de monitoramento além dos 3 WordPress; não inventar IDs, domínios, campaigns ou credenciais.
6. O limite de 3 chamadas globais por execução da C8 é padrão conservador, não um limite estrutural de blogs. Dimensionar orçamento, cota Shopee e frequência das pré-conversões para 50+ blogs.
7. O Environment `v31-editorial-safe` deverá ter escopo de branches adequado antes do merge de workflows com credenciais de armazenamento, independentemente de qualquer suposição sobre exposição de secrets.

**Estado C9:** integração reversível PREPARADA e E2E com R2 real PASS; **NÃO em produção**. Mantém os geradores de artigos existentes; a publicação LIVE é uma decisão de rollout C10, não resultado automático de testes.
