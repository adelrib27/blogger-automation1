# V31 C137 — R2 oficial: 12 candidatos reais, 0 caches afiliados nas três campanhas

**Data:** 2026-11-23 (America/Recife). **Código:** `V31-C137-20261123-666-TESTS-R2-12-CANDIDATES-0-CACHED-LIVE-OFF`.
**Resultado:** auditor de cache exato implantado e homologado, **sem habilitar novas rotas**; LIVE desativado.

## Fontes antes da execução
Lidos `V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json` e [checkpoint C136](CHECKPOINT_C136_MONITOR_CRON_E_DRAFTS_653_TESTES_2026-11-23.md); [PREVIEW C137](CHECKPOINT_C137_PREVIEW_CACHE_AFILIADO_R2_3_BLOGS_2026-11-23.md) registrado na main no commit `1197cd4fbb01c8e22616c1b7006bfb009159a8d5` ANTES da implementação. Base: monitor C136 #45277246529 SUCCESS (pilotos DRAFT íntegros, Casa/Oficina pending observation), LIVE policy pending.

## Implementação C137
[PR #142](https://github.com/adelrib27/blogger-automation1/pull/142) integrado `685774614ab71c3e792fc051647e0dc70b2b14bd`:
- `affiliate_hub_v31/campaign_cache_readiness.py`: auditor de R2 oficial `R2State.restore_to` (GET+integridade SHA256/SQLite), reaberto `mode=ro` + `PRAGMA query_only=ON`; quatro candidatos por site usando a taxonomia, moderação e política de origem usadas na shortlist C94; cruza `affiliate_links` EXCLUSIVAMENTE por campanha real da rota.
- `affiliate_hub_v31/tests/test_c137_campaign_cache_readiness.py` 13 testes; [CI #45278150121](https://github.com/adelrib27/blogger-automation1/actions/runs/45278150121): **666 testes universais PASS** + Casa 24/24, Oficina 21/21, Radar 15/15 e guard antirrepetição PASS.
- `.github/workflows/v31_c137_campaign_cache_r2_readonly.yml`: one-shot por `push` do próprio YAML ou dispatch explícito, SEM cron recorrente, nenhuma API Shopee, D1, CMS, fonte externa, conversão ou LIVE.

## Evidência remota real
[GitHub Action #45278265895](https://github.com/adelrib27/blogger-automation1/actions/runs/45278265895): `COMPLETED SUCCESS`, `R2_OFFICIAL_SNAPSHOT_SQLITE_READ_ONLY`, 3 sites, **12 candidatos em catálogo, 0 links no cache de campanha exata**, `r2_writes=0`, `d1_writes=0`, `cms_writes=0`, `affiliate_conversions=0`, `automatic_live_authorized=false`.
- `blogger_cozinha_sem_complicacao` campanha `cozinhasemcomp`: 4 SKUs, **0** cache.
  - `shopee:1803576078:58215462340` (fritadeira elétrica/tacho de uso industrial)
  - `shopee:1612799037:46565715088` (forma de silicone para bolo/air fryer)
  - `shopee:967211054:58209682843` (desengordurante spray Super Dom 300 ml)
  - `shopee:735701971:23596760890` (forma air fryer com alça)
- `blogger_estilo` campanha `estilo`: 4 SKUs, **0** cache.
  - `shopee:770186978:23099153938` (vestido feminino festa/plus size)
  - `shopee:323761608:18397672754` (sapato social masculino + relógio/cinto)
  - `shopee:388442075:9517347156` (sandália Fabi Shoes)
  - `shopee:855455765:19546550508` (kit calça jeans masculina)
- `blogger_limpeza` campanha `limpeza`: 4 SKUs, **0** cache.
  - `shopee:328666563:21596900116` (aspirador de pó portátil sem fio)
  - `shopee:1870350552:54712945812` (saco para aspirador)
  - `shopee:1053378287:21699070627` (aspirador vertical portátil)
  - `shopee:786307292:22096374889` (mop PVA)

**Precisão:** `cache=0` é ausência de linha `affiliate_links(product_key,campaign)` para os 12 candidatos **na snapshot atual auditada**, NÃO ausência universal de todos os links no R2 nem indisponibilidade da API Shopee. Os URLs de origem do CSV não são links afiliados e não podem ser usados como CTA convertido. Nem título/moderação de vendedor, nem categoria, nem `source_safe_for_use` fornecem automaticamente prova independente de modelo, fabricante, fotos ou estoque. **Nenhum perfil de revisão/pedido habilitado** nesta etapa.

## Seguimento seguro
1. Investigar por GET (sem writes) o estado da **fila universal real de conversão** e limites/credenciais, e verificar se as três campanhas estão legitimamente cadastradas, sem inventar.
2. Antes da conversão/READY de um SKU, confirmar permissão da campanha, identidade de produto, foto real e trilha de fonte independente; garantir antirrepetição CMS e limites D1 de conversão global.
3. Não adicionar perfil sintético com informações inventadas, não converter produto inadequado apenas para preencher quota; quando houver evidência suficiente, priorizar canário individual DRAFT.
4. C136 monitor read-only continua cron UTC 23:47; nova quota de pesquisa Móveis depende virada UTC natural, sem dispatch duplicado.
5. **AUTO LIVE OFF**: `pending_policy_approval`, sem ativação antes da homologação E2E e autorização expressa final.
