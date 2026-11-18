# CHECKPOINT C8 — Shadow mode + reposição de links multi-site (16/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C8-SHADOW-REPLENISH-REAL-PASS-20261116`

## Escopo e decisão editorial

Projeto **V31 Hub Editorial Shopee — Blogger & WordPress**, **sem Pinterest**.
Os três WordPress possuem publicadores próprios: V31 fornece dados de produtos, links cacheados e fallback da API Shopee com erro 1000. **Não criar outros geradores/publicadores para substituí-los.** O mesmo produto pode servir a pautas diferentes; impedir canibalização por **assunto/título/ângulo**, mantendo keywords importantes.

Branch isolada `feature/v31-affiliate-hub-c1-safe-20261115`, [PR #52 draft](https://github.com/adelrib27/blogger-automation1/pull/52), sem merge nem mudanças nos publicadores LIVE.

## C8 implementado

1. `affiliate_hub_v31/shadow.d/*.json`: registro configurável por blog para diagnosticar estoque, config e keywords, agenda REAL atual e exigências de categoria; perfis iniciais dos 3 WordPress. Novos sites entram em `sites.d/` e `shadow.d/`, sem modificar Python. **21 sites cadastrados no inventário de rotas (18 Blogger e 3 WordPress); 3 perfis shadow configurados até este checkpoint**. Não inventar blog ou credenciais.
2. `affiliate_hub_v31/shadow_audit.py`: restaura snapshot **REAL** do R2 uma vez por execução, conta somente links afiliados válidos na campanha do blog, cruzados com nichos e keywords. Relatório apresenta contagens, cobertura de categorias, reserva em dias e status `NOT_READY`/`SHADOW_READY`. **Nunca publica, converte, escreve no R2 ou exibe URLs comerciais.** `SHADOW_READY` não constitui liberação para publicar.
3. `affiliate_hub_v31/link_warmup.py`: preferir uma **categoria ainda não coberta** antes de acumular produtos numa categoria. Preserva filtro semântico e proteção contra acessórios/desvios.
4. `affiliate_hub_v31/cache_replenish.py`: pré-conversão por campanha com **limite GLOBAL de 3 tentativas Shopee por execução**, `--execute` explícito, `--site all` com rodízio equitativo entre perfis (incluindo 50+ blogs), opção de apenas consultar sem fazer mutations, interrupção na falha da API, um snapshot R2 por lote com verificação de restauração. Não toca publicadores. O rodízio a 3 tentativas/dia é deliberadamente conservador e **insuficiente para a meta final de escala sem posterior dimensionamento de cotas e orçamento**.
5. `.github/workflows/v31_c8_shadow_safe.yml`: job read-only na nuvem, manual após merge, schedule `07:47 America/Recife` que só executará se `vars.V31_EDITORIAL_SHADOW_ENABLED == 'true'`. **Desligado por padrão**, branch `main` e Environment `v31-editorial-safe`.
6. `.github/workflows/v31_c8_cache_replenish_safe.yml`: manual após merge mediante `confirm_conversion=true`; schedule `08:27 America/Recife` que só roda com `vars.V31_EDITORIAL_CACHE_WARMUP_ENABLED == 'true'`. **Desligado por padrão**. Usa o mesmo `concurrency: v31-editorial-catalog-single-writer`, limitado a 1–3 mutations e somente R2/Shopee (sem credenciais de publicação).
7. Novos testes `test_shadow_audit.py`, `test_cache_replenish.py` e aprimoramento de `test_link_warmup.py`: teste de 50 blogs no round-robin, cache por campanha, validação de inputs, 3 mutations máximas, falha parcial com persistência, R2 mock, shadow sem writes.

## Evidência REAL GitHub Actions

**[Run 43886181941](https://github.com/adelrib27/blogger-automation1/actions/runs/43886181941)**: `V31_C8_SHADOW_READONLY_PASS`, **94/94 testes**; auditoria do catálogo R2 real, **sem gravação/nenhuma Shopee API/nenhuma publicação**.

Resultados ANTES do novo lote:

| Site | Usáveis | Meta para 3 dias | Categorias |
| --- | ---: | ---: | ---: |
| Casa e Decoração (`casaedecoracaowp`) | 1 | 9 (3/dia) | 1 de 8 |
| Oficina & Garagem (`oficinawp`) | 1 | 6 (2/dia) | 1 de 6 |
| Radar Tech BR (`radarwp`) | 1 | 15 (5/dia) | 1 de 5 obrigatórias |

Total no catálogo: 109.507 produtos, 4.674 elegíveis, 4 links cacheados (1 Blogger + 3 WordPress).

**[Run 43887349902](https://github.com/adelrib27/blogger-automation1/actions/runs/43887349902)**: **SUCCESS**, **101/101 testes offline PASS**. Dry-run primeiro: 0 mutations. Lote real: **3 tentativas e 3 conversões Shopee bem-sucedidas**, **1 por campanha WordPress**, único snapshot R2, `retention_pending=false`, R2 restaurado e conferido. Shadow posterior: `V31_C8_SHADOW_READONLY_PASS`.

Resultados APÓS o lote:

| Site | Usáveis | Meta 3 dias | Categorias cobertas | Status |
| --- | ---: | ---: | ---: | --- |
| Casa e Decoração | 2 | 9 | 2/8 | `NOT_READY` |
| Oficina & Garagem | 2 | 6 | 2/6 | `NOT_READY` |
| Radar Tech BR | 2 | 15 | 2/5 obrigatórias (3 ainda faltando) | `NOT_READY` |

Links totais no catálogo R2: **7** (6 WordPress + 1 Blogger Air Fryers). Não presumir disponibilidade/vigência comercial ilimitada.

Os workflows temporários `v31_c8_shadow_once.yml` e `v31_c8_replenish_once.yml` foram **removidos** depois dos runs PASS, preservando logs de auditoria.

## Não concluir produção sem estes gates

- **Nenhuma alteração nos workflows LIVE de Casa, Oficina ou Radar**. O fallback automático ainda não está ligado aos publicadores, nem houve merge.
- Ampliação do cache: de 2 por blog para metas conservadoras 9/6/15, cobrindo todas as categorias do Radar. A estratégia de 3 chamadas globais por execução é apenas o bootstrap; dimensionar custos, cotas e taxa para 50+ blogs antes de schedule LIVE.
- O job shadow agendado no PR **não roda** até merge e criação de variável opt-in. Mesmo com merge, manter flags desligadas até revisão de Environment e credenciais.
- Fluxos existentes hoje podem bloquear produto já publicado; substituir com critério editorial por **assunto/título/intenção** antes de ativar fallback no publicador, sem remover controles contra artigos repetidos.
- Radar: não há prova de fila completa com 5 categorias usando exclusivamente cache; apenas 1 slot foi validado em C7.
- Shopee CSV é fonte de produtos, mas API `generateShortLink` continua necessária para pré-aquecer links novos quando estiver saudável.
- Branch restriction do Environment `v31-editorial-safe` e rotação da App Secret Shopee anteriormente exposta em screenshot **ainda não foram confirmadas**.
- Refresh automático dos feeds CSV no R2 e monitoramento de disponibilidade das imagens por URL Shopee requerem avaliação adicional.

## Próximo marco

**C9 — Validação editorial e integração com feature flag por blog**: preparar uma ponte com os workflows existentes sem duplicar geradores, ensaiar shadow em horário de produção com rollback, alinhar fila completa do Radar e política de reutilização de produto, e liberar ativação controlada **somente após aprovação e gates**. O PR permanece draft.

**Estado final C8:** os componentes e o piloto real foram concluídos; **não está liberado para publicação automática com fallback**.
