# C132 — Retomada do objetivo V31 universal ANTES de alterações técnicas

**Data:** 23/11/2026 America/Recife. **Pedido do proprietário:** "então vamos voltar paro objetivo maior".
**Projeto:** V31 Hub Editorial Shopee — Blogger & WordPress. **Repositório:** adelrib27/blogger-automation1, `main`.

## Princípios imutáveis recuperados de fontes reais
- Biblioteca universal derivada dos dois CSVs Shopee, consultável independentemente da criação de novos blogs. O pipeline deve funcionar para quaisquer nichos e sites Blogger/WordPress; o destino **aplica filtro de pertinência** sem apagar produtos da biblioteca.
- Geração DRAFT autônoma por site e campanha, imagem real e link afiliado apropriado, autorias originais, SEO, aviso de afiliado, links internos verificáveis; limites de cota e idempotência; aprovação formal para LIVE.
- C130 Radar foi **10/10 melhoria editorial**, não conclusão universal. Não reprocessar posts nem priorizar TikTok/Pinterest; C131 migração comercial é trilha separada.
- Blogger Portfolio Five decisão: cinco blogs prioritários (Cozinha Sem Complicação, Móveis para Cada Canto, Estilo no Dia a Dia, Limpeza Inteligente, Vida Pet Prática) de um conjunto acessível, sem excluir outros futuros blogs ou WordPress; 11 origens com backups, sem exclusões nem redirecionamentos automáticos.
- C81 DRAFTs pilotos Blogger Móveis post 4106024906916105222 e WP Casa post 321 com hashes originais verificados; após habilitação de flags há necessidade de demonstrar execução real agendada e estado de quotas por fonte atual.

## Estado verificado em GitHub nesta retomada
- `V31_CONTINUAR_AQUI.md` com C130 e `affiliate_hub_v31/CONTINUIDADE_ESTADO.json` possui ainda `last_checkpoint_phase=C81`, apesar dos checkpoints mais novos. Precisará de atualização aditiva sem apagar histórico.
- Workflows `v31_autonomous_draft_scheduler.yml`, `v31_independent_review_draft.yml` e `v31_universal_blogger_autodraft_daily.yml` existem. Schedule do scheduler `47 */4 * * *`, gated por vars `V31_AUTODRAFT_ACTIVE`, `V31_AUTODRAFT_ROLLOUT_SITE`, `V31_AUTODRAFT_FULL_ROLLOUT_APPROVED`; release LIVE exige `V31_AUTOLIVE_ACTIVE` + environment independente e política assinada. Não modificar essas travas.
- Última suíte universal disponível `V31 Editorial Shopee - Testes SAFE Blogger WordPress`, run 45224804913, commit 46d14a0..., 23/11: **604 testes**, **6 FAIL + 2 ERROR**. Nomes:
  1. `test_draft_adapter.test_wordpress_draft_is_always_draft_and_escaped` -> `niche_outside_site` ao construir brief cozinha no Radar.
  2. `test_site_launch_plan.test_wordpress_isolation_and_cross_site_flags` -> produto cozinha não roteado ao Radar.
  3. `test_fallback_shop_alternatives.test_three_alternative_shops_for_one_keyword_and_campaign_isolation` -> 0 candidatos para nicho antigo.
  4/5. `test_fallback_v23` dois casos de campanha isolada e link legado -> Radar 0.
  6. `test_inventory_audit.test_radar_inventory_by_keyword_not_campaign` -> supply Cozinha 0.
  7. `test_link_warmup.test_warmup_uses_only_eligible_keywords_and_missing_campaign_links` -> 0.
  8. `test_routing.test_liquidificador_not_routed_to_air_fryers_and_vice_versa` -> Radar não recebe liquidificador, corretamente.
- Regra C105/C114: Radar Tech BR apenas Tecnologia/Ar-condicionado; produtos de cozinha, moda, utilidades e ferramentas não devem passar no Radar. **Não alterar filtros para compensar testes desatualizados.**
- Suíte Radar C114 isolada run 45224804945? A verificada run 45224804945 (correção), e 45224804945? Conforme checkpoint C114, run 45224366338 SUCCESS, offline 15 novos. Suíte universal continua vermelha.
- Nenhum post, workflow de publicação ou R2/D1 alterado neste checkpoint.

## Plano seguro para esta retomada
1. Ler código atual de rotas, filtros e **oito testes antigos exatos**; definir fixtures coerentes com política Tech atual e, adicionalmente, asserts negativos explícitos impedindo vazamento de cozinha para Radar.
2. Criar branch só de correção de testes/contratos sem mexer no renderer, catálogo ou LIVE. Adicionar regressões positivas Tech e negativas cross-niche para garantir universalidade.
3. Rodar suíte universal offline PR até green, revisar diferenças e integrar somente com evidência; se erro real do código, corrigi-lo de forma mínima, sem relaxar guardas.
4. Auditar variáveis/workflow DRAFT e histórico de execuções após 22/11. Sem rodar geração real se quota/ID/campanha e estado já processado não puderem ser comprovados.
5. Atualizar checkpoint do ciclo em `V31_CONTINUAR_AQUI.md` e status estruturado, mantendo C130 e históricos.

**Código de retomada:** `V31-C132-20261123-UNIVERSAL-FIRST-604-TESTS-8-LEGACY-FAILURES-LIVE-OFF`.
