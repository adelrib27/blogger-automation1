# V31 C133 — Auditor de prontidão universal DRAFT + 610 testes verdes

**Data:** 2026-11-23 (America/Recife), repositório `adelrib27/blogger-automation1`, branch `main`.  
**Código de retomada:** `V31-C133-20261123-610-TESTS-READY2-ROUTE5-MISSING1-LIVE-OFF`.

## C132 já resolvido
- PR #134 merge `c4a66c3e98178db636cdae1f4c3ac0b38b330d9c`, [Actions #45258280168](https://github.com/adelrib27/blogger-automation1/actions/runs/45258280168): **605 testes PASS**. Resolvidos os oito casos antigos (6 FAIL, 2 ERROR) sem enfraquecer o filtro de nichos por site.
- `affiliate_hub_v31/draft_adapter.py`: `product_offer_html(topic=title)` preserva vínculo semântico com o produto (em vez de palavra-chave genérica “tecnologia”); revalida `category/niche` da rota durante `prepare_draft`, inclusive contra briefing antigo com link de campanha válido. Regressão adicional impedindo bypass.
- Checkpoint detalhado [C132](CHECKPOINT_C132_UNIVERSAL_605_TESTS_MERGED_READINESS_2026-11-23.md). Não repetiu os artigos Radar.

## C133 concluído
- PR [#135](https://github.com/adelrib27/blogger-automation1/pull/135) **merged**, commit `c6e869d0ffd6fe8a95bb8503e3d7678d0d46a5a2`.
- Nova implementação de auditor declarativo **`affiliate_hub_v31/autodraft_rollout_readiness.py`**. Lê arquivos locais oficiais: portfólio dos cinco Blogger, `routing.sites()`, `site_requests.d` habilitados, perfis `autonomous_review_sources.json`. Não faz rede, conversão, validação externa nem grava CMS/R2/D1.
- CLI possui `--output` JSON e `--require-complete` que encerra com falha se ainda faltar cadastro. O modo normal gera relatório HONESTO com `all_configured_for_draft_preflight=false` sem confundir preflight local com homologação real.
- Cinco testes novos em `affiliate_hub_v31/tests/test_autodraft_rollout_readiness.py`: detectar rota faltante sem inventar campanha, não equiparar cadastro simples a aprovação, bloquear `publish_enabled=true`, permitir cadastro declarativo de blog futuro e impedir IDs duplicados.
- Workflow seguro `.github/workflows/v31_c133_autodraft_rollout_readiness_safe.yml`, acionado somente em mudanças de cadastros e por despacho manual; **sem secrets, sem API e sem LIVE**, com artifact JSON por 14 dias.
- Suíte completa [#45259792390](https://github.com/adelrib27/blogger-automation1/actions/runs/45259792390): **610 tests PASS**, zero failures; includes regressões de geradores WordPress.
- Primeira execução do novo auditor [#45259940897](https://github.com/adelrib27/blogger-automation1/actions/runs/45259940897): SUCCESS para auditoria (não implantação total); saída:
```json
{"priority_sites":8,"configured":2,"status_counts":{"PROFILE_AND_REQUEST_MISSING":5,"CONFIGURED_NOT_REMOTE_HOMOLOGATED":2,"ROUTE_MISSING":1},"all_configured":false,"mode":"OFFLINE_READ_ONLY"}
```
- O nome `CONFIGURED_NOT_REMOTE_HOMOLOGATED` significa somente rota+perfil+pedido; **NÃO** significa novo DRAFT publicado, vínculo afiliado testado ou release autorizado.

## Exatamente o que falta em cada site do foco atual
| Plataforma | Site | Rota | Perfil de revisão | Pedido habilitado | Situação |
|---|---|---|---|---|---|
| Blogger | Cozinha Sem Complicação | blogger_cozinha_sem_complicacao | não | não | PROFILE_AND_REQUEST_MISSING |
| Blogger | Móveis para Cada Canto | blogger_moveis_para_cada_canto | sim | sim | CONFIGURED_NOT_REMOTE_HOMOLOGATED |
| Blogger | Estilo no Dia a Dia | blogger_estilo | não | não | PROFILE_AND_REQUEST_MISSING |
| Blogger | Limpeza Inteligente | blogger_limpeza | não | não | PROFILE_AND_REQUEST_MISSING |
| Blogger | Vida Pet Prática | **inexistente** (ID 8052455848487624244) | não | não | ROUTE_MISSING |
| WordPress | Casa e Decoração | wordpress_casa_decoracao | sim | sim | CONFIGURED_NOT_REMOTE_HOMOLOGATED |
| WordPress | Radar Tech BR | wordpress_radartechbr | não | não | PROFILE_AND_REQUEST_MISSING |
| WordPress | Oficina & Garagem | wordpress_oficina_garagem | não | não | PROFILE_AND_REQUEST_MISSING |

## Estado DRAFT real e regras de segurança
- O primeiro agendamento piloto de 23/11 [#45137244359](https://github.com/adelrib27/blogger-automation1/actions/runs/45137244359) escolheu Móveis, leu CMS, passou pela verificação independente mas retornou `NO_NEW_OFFER:research_budget_exhausted` e **não criou novo DRAFT**. D1 `v31_search_budget` Móveis 2026-11-23: SEARCH 3/3 e HTTP 3/3, SELECT somente; leases 0.
- Os DRAFTs já criados e relidos no CMS continuam Blogger Móveis ID `4106024906916105222` e WordPress Casa ID `321` (ambos `draft`). D1 READY WordPress Casa=1 (não consumido), USED Blogger Móveis=1, USED WordPress Casa=1.
- O cron seleciona apenas `blogger_moveis_para_cada_canto` com `V31_AUTODRAFT_ACTIVE=true` e `V31_AUTODRAFT_ROLLOUT_SITE=blogger_moveis_para_cada_canto`; **não ativar `all`**. `V31_AUTOLIVE_ACTIVE` não foi ligado, release schedule SKIPPED; workflow legacy Radar também mantém if false e config false.
- Oito sites são prioridade de implantação, **não teto da biblioteca**; continuam 24 rotas cadastradas e novos sites podem ser adicionados via JSON com campaigns verificadas, sem alterar Python.

## Próximas ações técnicas e critério de saída
1. Obter rota/campanha real Vida Pet, sem adivinhar subID/links; preservar backups das 11 fontes Blogger.
2. Habilitar solicitações e perfis de revisão dos 6 sites que ainda não os têm **um por vez** com validação de ID, campanha, biblioteca, quota, fonte, CMS e deduplicação.
3. Na renovação natural da cota, observar 1 canário agendado e sua evidência completa no CMS antes de aumentar rollout DRAFT. Cota esgotada no dia não deve ser contornada.
4. Confirmar idempotência, URL afiliada campanha EXATA, imagem real do feed, metadados SEO e links internos reais por blog.
5. LIVE automático **OFF até homologação e autorização formal de política assinada**. Não publicar posts ao criar meramente cadastros.

**Ponto de entrada:** `V31_CONTINUAR_AQUI.md`; depois este checkpoint, [C132](CHECKPOINT_C132_UNIVERSAL_605_TESTS_MERGED_READINESS_2026-11-23.md) e `affiliate_hub_v31/BLOGGER_PORTFOLIO_FIVE_2026-11-23.json`.
