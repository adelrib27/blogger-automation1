# Checkpoint C22 — contrato E2E de nichos, Blogger/WordPress e liberação controlada (17/11/2026)

**Continuidade:** `V31-EDITORIAL-C22-R2-203649-8403SAFE-14GAP-17LINKS-230TESTS-20261117`

**Repositório:** `adelrib27/blogger-automation1`; branch `feature/v31-affiliate-hub-c1-safe-20261115`; [PR #52 DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52). **Sem merge; main e Pinterest não alterados.**

## Objetivo do usuário
Avançar até sistema pronto ou dependência realmente manual. **Métricas de vendas, comissão, conversão e receita são desejáveis para otimizar, mas NÃO são pré-requisitos para terminar software, construir catálogo, revisar produtos, converter links ou publicar conteúdo verificado.** Ausência de métricas não é razão para parar. Não inventar taxas, comissões, preços ou vendas.

## Implementações desta etapa
1. **`catalog.py`**: `candidates()` e `select_products()` filtram domínios e imagens, categorias sensíveis e conflitos de origem **antes** do limite de resultados. Resultado não pode ficar artificialmente vazio por causa de `LIMIT` antes do gate. Consulta read-only, sem criar schema em catálogo legado.
2. **`editorial.py`**: `EditorialLedger._approved_product()` e `next_brief()` recusam o SKU de origem barrada antes de reservar pauta. `draft_adapter` já usava `Catalog.for_conversion`, que aplica o mesmo gate. Sem mudança em posts antigos.
3. **`review_proposals.py`**: amostras de curadoria por categoria oficial L1/L2, título e loja, separando sugestões com evidência de título de propostas apenas por faceta. Raízes protegidas, conflitos e URLs não confiáveis não são promovidos. **`review_required=True`, `new_approvals=0`, `can_publish=False`, `affiliate_url=None`**. A CLI em R2 só imprime contagens agregadas.
4. **`site_launch_plan.py`**: entrada contextual por tema de blog futuro sem criar campanha fictícia; para 21 sites registrados (18 Blogger + 3 WordPress), impõe plataforma, campanha real e nichos permitidos e cria pautas de intenção **para revisão**, sem persistir ou publicar. Link verificado é apenas o da campanha daquele site.
5. **`fallback_v23.py`**: até links afiliados antigos no R2 são vetados se a origem foi classificada como protegida/conflitante; a consulta usa conexão SQLite `mode=ro` real, nunca escreve.
6. **`link_warmup.py`**: pré-conversão evita selecionar SKUs bloqueados antes de qualquer mutation. `cache_replenish` e `shadow_audit` herdam proteção dos consumidores corrigidos.
7. **`.github/workflows/v31_editorial_catalog_safe.yml`**: CI permanente passou a exigir também self-tests dos dois geradores WordPress e gate cross-blog de originalidade; tudo offline, sem credenciais comerciais.

## Provas GitHub Actions
- [C22 proposta + intake inicial, run 44195101703](https://github.com/adelrib27/blogger-automation1/actions/runs/44195101703) **SUCCESS**, 227 testes, R2 real. Para quatro categorias consultadas foram selecionadas 16 propostas distintas por grupo, todas só para revisão; nas amostras nenhuma possuía evidência textual suficiente para converter proposta em classificação segura.
- [C22 WordPress E2E, run 44195633601](https://github.com/adelrib27/blogger-automation1/actions/runs/44195633601) **SUCCESS**, 230 testes, três consumidores de fallback e warmup testados com R2 real, sem chamadas Shopee.
- [**Canário final 44196154349**](https://github.com/adelrib27/blogger-automation1/actions/runs/44196154349) **SUCCESS**, **230 testes V31** + `casa_decoracao/src/self_test.py` + `oficina_garagem/src/self_test.py` + `src/editorial_cross_blog_guard_self_test.py` todos PASS, mais verificação no R2 real. Nenhuma chamada Shopee, escrita R2, conversão, draft remoto, postagem ou criação de blog. Todos os 17 links previamente convertidos preservados.
- R2 real: **203.649** produtos, **8.685** elegíveis nos critérios históricos, **282** destes barrados pelo gate adicional da fonte, portanto **8.403** historicamente elegíveis que passam pelo gate de fonte — NÃO confundir este número com autorização de publicação. **194.964** continuam em revisão editorial, sem autoaprovação.
- Contratos reais por assunto: Blogger Air Fryer 12 candidatos / 1 link da própria campanha; WordPress Radar Air Fryer 12/1; WordPress Casa organização de cozinha 12/0; hipotético blog futuro 12 candidatos, **0 URLs afiliadas**, sem atribuição de campanha.
- Amostras de quatro raízes/subcategorias pendentes apresentaram **0** propostas com título + categoria suficientes para uma promoção de confiança alta; o módulo expõe 16 por grupo como sugestões e não as autoaprova. **As categorias não bastam para alegar qualidade editorial.**

## Fallback WordPress — déficit REAL de estoque
| Perfil | Ofertas cacheadas utilizáveis | Meta de três dias | Faltam |
|---|---:|---:|---:|
| Casa e Decoração | **4** | 9 | **5** |
| Oficina & Garagem | **4** | 6 | **2** |
| Radar Tech BR | **8** | 15 | **7** |
| **Total** | **16** | **30** | **14** |

Nenhuma categoria obrigatória estava vazia na verificação C22; porém os 3 perfis seguem **`NOT_READY`** para fallback de reserva de três dias. O dry-run de warmup identificou um candidato novo por perfil, mas não executou mutations. A conversão real pode avançar progressivamente com o motor existente (1–3 mutations por rodada, parada imediata em erro API e snapshot R2 verificado). Não inventar 14 links; só contar como concluídos depois de realmente convertidos e persistidos.

## Única classe de bloqueio fora das ferramentas disponíveis: credenciais/segurança administrativas
- **Ação manual 1:** verificar no programa oficial Shopee Affiliate se o **App Secret anteriormente exposto** foi revogado/rotacionado; se não, rotacioná-lo e atualizar o secret do GitHub Environment `v31-editorial-safe` chamado `V31_EDITORIAL_SHOPEE_APP_SECRET`. Não publicar valores em Issues ou chat.
- **Ação manual 2:** em **GitHub → Settings → Environments → v31-editorial-safe**, definir restrição de branches de deployment para a `main` e revisar acesso dos GitHub Actions/approval rules. A branch feature teve acesso a esse Environment apenas para os canários controlados, o que demonstra a necessidade de verificação administrativa antes da implantação.
- **Ação de liberação após 1 e 2:** revisar atualização do PR #52 contra `main` e habilitar apenas os workflows/flags correspondentes após reserva, checks de originalidade e teste de rollback. O conector GitHub pode alterar código/PR, mas não dispõe de interface para rotacionar um secret Shopee nem gerenciar estas proteções administrativas.
- **Não é bloqueio:** falta de números comerciais de vendas/comissões. Sistema deve iniciar com relevância, categorias verificáveis, URLs oficiais por campanha, SEO e política editorial, aprendendo métricas quando disponíveis.

**Ticket de intervenção manual criado:** [GitHub Issue #53 — Segurança para liberação V31](https://github.com/adelrib27/blogger-automation1/issues/53). O checklist distingue rotação do segredo Shopee, restrição do GitHub Environment e continuidade de publicação. O workflow temporário do canário C22 e seu gatilho foram **removidos** depois dos PASS no R2; as evidências persistem nos runs da Actions.

**Decisão:** o mecanismo SAFE do C22 está implementado e validado, mas **a rede de fallback ainda não está pronta para LIVE** por segurança administrativa e falta de 14 ofertas de reserva. PR #52 continua DRAFT, nenhum switch novo foi ligado e a `main` não foi modificada. Após as duas ações manuais, dar continuidade à reposição controlada e release de um blog por vez, sem alterar páginas de loja nem Pinterest. Canários temporários devem ser removidos após a prova.
