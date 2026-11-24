# V31 — C152 SAFE: auditoria legada CMS e guarda universal de colisões

**Data:** 24/11/2026 · **Projeto:** V31 Hub Editorial Shopee — Blogger & WordPress · **Estado:** `SAFE_DEDUP_GUARD_TESTED` / DRAFT E2E **NÃO** homologado · LIVE **OFF**.

## Origem e imutabilidade operacional
- `main` inicialmente `e1a2fd180ce69e57f2ce3ee3e082c4618acaf8f9`; comparação com commit de retomada: `identical` (`ahead=0 / behind=0`).
- Branch isolada `fix/v31-c152-legacy-cms-collision-20261124`; PR [#159](https://github.com/adelrib27/blogger-automation1/pull/159).
- Prévia persistida ANTES de alterar os writers: `affiliate_hub_v31/CHECKPOINT_C152_PREVIEW_AUDITORIA_LEGADA_2026-11-24.md`.
- Políticas da `main` lidas: Radar `site_requests.d/wordpress_radartechbr.json.enabled=false`; `autonomous_live_policy.json.activation=pending_policy_approval`. Dez workflows antigos Radar removidos na C149 **não foram restaurados**. Escopo continua universal Blogger e WordPress, Pinterest totalmente externo.

## Resultado remoto do piloto principal — somente leitura
- WordPress autenticado, `https://radartechbr.com.br`: **37 publish + 19 draft = 56** via `wp_count_posts` e `wp_list_posts`, paginado.
- `context=edit, raw_columns=true`: **56/56 corpos RAW não vazios** verificados, **517.011 caracteres** agregados. Conferência de títulos, slugs, status, conteúdo e referências Shopee disponíveis.
- **0 matches literais** com os quatro IDs de item C151: `22398817823`, `22192873783`, `22295181772`, `58267720942`; zero literal **NÃO** prova unicidade editorial ou ausência de colisão em shortlink.
- Publicações `#138` (“Smartwatch com tela infinita: o que significa?”) e `#260` (“Smartwatch e frequência cardíaca: o que verificar”) cobrem a categoria. Colisão temática é hipótese de revisão, não prova de duplicata por SKU, fabricante ou ângulo.
- Fontes comerciais exatas, foto da variante e compatibilidade de fabricante dos quatro candidatos **não estão verificadas**; todos continuam bloqueados para conversão e DRAFT.
- Estado D1/R2 do catálogo **não foi reconsultado remotamente neste ciclo**; dados C151 são históricos. Reserva antiga não autoriza nova chamada. Três tentativas `radarwp` históricas da C149 permanecem vetadas a retry sem reconciliação.

## Código SAFE implementado
1. **`legacy_cms_collision.py`**: módulo universal, puro (sem HTTP/mutações), leitor de registros RAW completos do mesmo CMS autenticado. Detecta `product_key`, URLs Shopee originais reconhecíveis, slugs e títulos/ângulos exatos ou próximos. Testes cobrem falsos positivos, diferenças explícitas “Active”/“Lite”, outros sites, rascunhos e publicados. Retorna `REVIEW_REQUIRED` ao encontrar candidato suspeito; `NO_DETECTED_COLLISION` não autoriza CMS. Dados RAW ausentes, status e ID inválidos bloqueiam.
2. **`reviewed_draft_delivery.py`**: exige auditoria nos dois adaptadores (Blogger/WordPress) **antes** do `authorize()` D1 e do POST CMS; preserva reconciliação com mesmo rascunho por marcador/slug e hash.
3. **`automatic_blogger_drafts.py` e `automatic_wordpress_drafts.py`**: rotinas diretas universais passam a verificar histórico legado antes da geração por IA e novamente depois do reread de corrida, antes de POST DRAFT. Nunca LIVE.
4. **Suítes de regressão:** `test_legacy_cms_collision.py` testa SKU, URL original, slug, título, status, variantes e gates dos dois adaptadores revisados. `test_automatic_wordpress_drafts.py` / `test_automatic_blogger_drafts.py` exercitam bloqueio antes de IA/POST. Fixture WordPress em contexto de edição traz RAW, como o endpoint autenticado.
5. **`SYSTEM_MASTER.md`**: documenta o contrato novo, limitações e evidências; `CONTINUIDADE_ESTADO.json` assina o próximo estágio e mantém SAFE.

## CI verificado (não publicação)
- Execução [#45446503885](https://github.com/adelrib27/blogger-automation1/actions/runs/45446503885), head `acaf021904c1a0984333dc2c8aa7cc4ff177382a`: **922/922 testes unitários PASS**, **50 simulações SAFE PASS**, compilações PASS, **Casa 24/24**, **Oficina 21/21**, **Radar 15/15** e cross-blog regression PASS.
- Houve duas regressões detectadas DURANTE desenvolvimento: variante Active/Lite e fixture de conteúdo `rendered` em vez de `raw`; foram corrigidas e os testes repetidos. O cenário Blogger de título exatamente duplicado era filtrado pelo seletor legado; o teste foi atualizado para validar sobreposição semântica, e a CI acima passou.
- Alterações documentais posteriores à execução #45446503885 deverão ter seu próprio CI no PR antes da mesclagem. Apenas PASS da última revisão conta como gate de merge.
- Estes testes não fazem requisições externas e não comprovam cache Shopee, fabricante, D1/R2 atual nem DRAFT remoto.

## Critério pendente para o **primeiro DRAFT Radar**
1. Revalidar HEAD, políticas, 24 tombstones, cron e identidade de destino/campanha.
2. GET D1/R2 atualizado; conciliar `READY/USED` e reservas, colisão Casa `#314`, 3 tentativas históricas `radarwp` e links encurtados no CMS.
3. Confirmar **anúncio Shopee do SKU exato**, variação, foto original, moderação, campanha e **evidência independente** de fabricante/modelo/compatibilidade. Se candidatos C151 permanecerem ambíguos, descartar e selecionar outro SKU elegível do R2 sem fallback inseguro.
4. Revisão factual e SEO original, links internos existentes do mesmo site, disclosure `rel="nofollow sponsored"`, checagens de colisão semântica e hash do HTML imutável; executar **50 simulações** e CI.
5. **Somente então** uma conversão on-demand sujeita ao D1, uma entrega DRAFT segura com recibo, GET autenticado de ID/status/HTML hash, reconciliação `READY/USED`; repetir evidência E2E real por plataforma para declarar universal.
6. `LIVE` só mediante decisão distinta do proprietário após homologação.

**Mutações remotas deste ciclo:** CMS **0**, D1 **0**, R2 **0**, Shopee API **0**. Escritas legítimas somente em GitHub (branch, PR, implementação e checkpoints). **Nenhum novo artigo foi criado.**

**Rollback:** reverter a PR C152 no GitHub restaura o comportamento anterior sem tocar posts ou D1/R2. C149 continua aposentado. A PR não liga nenhuma flag de DRAFT ou LIVE.
