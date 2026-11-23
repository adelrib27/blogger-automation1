# V31 C138 — RCA real da fila afiliada e orçamento D1 (somente leitura)

**Data:** 2026-11-23 America/Recife. **Código:** `V31-C138-20261123-CONVERSION-QUEUE-2-ACTIVE-3-OF-3-ATTEMPTS-LIVE-OFF`.
**Status:** diagnóstico concluído, nenhum trigger adicional, nenhuma nova conversão ou post.

## Fontes verificadas
- [C137](CHECKPOINT_C137_R2_CAMPANHA_12_CANDIDATOS_0_LINKS_666_TESTES_2026-11-23.md): R2 oficial comprovou 12 SKUs de catálogo em 3 Blogger prioritários (Cozinha, Estilo, Limpeza), 0 links em `affiliate_links` para suas campanhas. [Run #45278265895](https://github.com/adelrib27/blogger-automation1/actions/runs/45278265895) SUCCESS, `r2_writes=0`, `d1_writes=0`, `affiliate_conversions=0`.
- `.github/workflows/v31_universal_request_queue_daily.yml`: schedule `47 11 * * *` UTC, dispara `site_request_queue` apenas para pedidos reais, orçamento máximo global 3; função `load_requests` considera só arquivos de pedidos `enabled=true`. Antes de qualquer mutação executa prévia R2 e regressões; R2 só é atualizado quando a conversão é real. Não há separação indevida de campanha no conversor: `convert_one` valida campanha e escreve cache `affiliate_links(product_key,campaign)`.
- [GitHub Actions #45056332000](https://github.com/adelrib27/blogger-automation1/actions/runs/45056332000), `2026-11-22T18:39:32Z`, **SUCCESS**: `requests_active=2`, `requests_evaluated=2`, `conversion_candidates=3`, `conversion_reservations_denied=2`, `converted=1`, `shopee_mutation_attempts=1`, `r2_snapshot_saved_and_verified=true`, `publication_calls=0`. `handoff_dispatch` salvou dois envelopes privados de revisão; não criou post.
- [GitHub Actions #44934503717](https://github.com/adelrib27/blogger-automation1/actions/runs/44934503717), `2026-11-21T18:15:19Z`, **SUCCESS**: `requests_active=2`, `converted=2`, `conversion_reservations_denied=1`, `publication_calls=0`. A fila converte links para os sites realmente pedidos, mas não inclui automaticamente os 3 novos prioritários.
- D1 oficial `v31-universal-ready-safe` por SELECT: `v31_shopee_conversion_attempts` em `2026-11-23` tinha 3 reservas globais (`slot=1` campanha `moveisparacadacanto`, `slot=2/3` `radarwp`), ocupando **3/3** da cota do dia. Reservas de tentativas não comprovam conversão nem R2 persistido. Não repetir/converter sem orçamento após renovação NATURAL UTC.
- `v31_ready_jobs` (mesmo D1): READY=1, USED=2 (invariante C135–C137); o único READY Casa colide com WP #314 (HTML divergente), **não consumir**.

## Diagnóstico causal
**Causa imediata da falta de links nos 12 candidatos C137:** nenhum desses SKUs tem linha `affiliate_links` na campanha Blogger exata. A fila de conversão agendada **não está quebrada**, pois realizou conversões reais e persistiu R2 nos runs verificados, mas só enxerga **dois pedidos ativos**. Cozinha, Estilo e Limpeza estão tecnicamente registrados, mas ainda sem requests/perfis homologados; por isso não é seguro forçar o conversor a abastecê-los a partir de títulos genéricos.

**Cota global de 23/11:** já 3/3 reservas, não fazer nova chamada Shopee nesta data UTC. Não inferir que 3 reservas = 3 links entregues.

## Próxima implementação segura C139+
1. Preparar os três blogs candidatos **um por vez**: selecionar SKU no catálogo, validar foto e URL exata, verificar fontes independentes de fabricante/GTIN/variante, verificar uso anterior no CMS e assegurar campanha V31 correta.
2. Só com evidência factual, cadastrar perfil e request válido que autorize o canário DRAFT. Não inventar pedido/identidade factual apenas para liberar fila.
3. Aguardar renovação NATURAL da cota `v31_shopee_conversion_attempts` e usar fluxo de conversão já existente com orçamento e idempotência, sem duplicar shortlinks por campanha.
4. Observar próximo canário Móveis (próximo ciclo após virada UTC) via scheduler existente, sem disparar manualmente. Monitor C136 cron 23:47 UTC permanece ativo; repetir auditoria se houver run schedule Casa/Oficina pós-PR137.
5. Sem LIVE: política `pending_policy_approval`, requer homologação E2E e autorização final. Manter Pinterest separado.

## Ações realizadas na C138
Somente leituras GitHub (arquivos, runs e logs) e Cloudflare D1 SELECT. **Zero alterações de R2/D1/CMS**, **zero novas conversões**, **zero DRAFTs**, **zero publicação LIVE**. Os checkpoints e estado GitHub são as únicas escritas documentais desta etapa.

**Continuidade:** ler `V31_CONTINUAR_AQUI.md` -> `CONTINUIDADE_ESTADO.json` -> este checkpoint C138 -> D1 quota diária e últimos runs `v31_universal_request_queue_daily.yml` / `v31_autonomous_draft_scheduler.yml`, e só então executar alterações.
