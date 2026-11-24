# V31 C143 — limpar 24 blogs Blogger apagados pelo proprietário

**Data local de decisão:** 2026-11-23 (America/Recife). **Execução no GitHub:** de 2026-11-24T00:44Z a 2026-11-24T00:49Z.
**Código de retomada:** `V31-C143-20261123-DELETED-24-BLOGGER-4-ACTIVE-3-WP-19-WRITERS-BLOCKED-50-SIM-760-PASS-LIVE-OFF`.
**Status:** IMPLEMENTADO / CI GREEN / ACTIONS READ-ONLY GREEN / LIVE V31 OFF.

## 1. Correção explícita do proprietário — revoga C141 e elementos de C142
> **"os 24 blogs Blogger históricos"** foram **excluídos pelo proprietário**. Não existirá etapa de reautenticar, reativar, recuperar ou produzir artigos/Loja nesses 24, mesmo que C102 tenha links/postagens como prova histórica.

A listagem autenticada de **ambos conectores Blogger disponíveis** hoje mostra os mesmos seis IDs, de uma conta:
- `1439741542627895062` — **Móveis para Cada Canto** → alvo V31 atual;
- `7757953554206491487` — **Limpeza Inteligente** → alvo V31 atual;
- `4830103887652146866` — **Estilo no Dia a Dia e Acessórios** → alvo V31 atual;
- `3552757910439359679` — **Cozinha Sem Complicação** → alvo V31 atual;
- `2228849984262880811` — **Ar-Condicionado sem Dúvidas** → excluído pelo usuário do escopo editorial V31; ainda acessível ao conector, **NÃO foi excluído no CMS nesta etapa**;
- `8052455848487624244` — **Vida Pet Prática** → metodologia de engenharia integrada universalmente, **não blog-alvo/pipeline/projeto separado** no V31, e **não um dos 24 apagados**.

Os **três WordPress** continuam alvos: Casa e Decoração, Oficina & Garagem, Radar Tech BR. Escopo atual: **4 Blogger + 3 WP = 7 alvos**; isso é fotografia da conexão atual e NÃO teto fixo para novos blogs futuros VERIFICADOS (IDs novos, fora das tombstones).

**Revogação expressa:** contagem anterior de `28 Blogger candidatos + 3 WP` e instrução `24 aguardam autenticação` são **INCORRETAS e PROIBIDAS nas retomadas após C143**. O relatório C102/C141 é material forense do passado, não inventário operacional de sites existentes.

## 2. Mudanças reais implantadas no repositório
[PR #146](https://github.com/adelrib27/blogger-automation1/pull/146) **MERGED** na `main`, squash SHA `c7db35679681e2def10c1a7127d819acb0925125`.

- `affiliate_hub_v31/EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json` — apenas **24 blog IDs antigos, suas chaves de rota e `deleted_by_owner=true`, `allow_reenroll=false`**. Não contém lista antiga de posts, produtos, fotos, artigos, links de afiliado, campanhas ou credenciais. É **negação**, nunca fila de artigos.
- `affiliate_hub_v31/EDITORIAL_GLOBAL_PORTFOLIO_C141.json` — reduzido a **ponteiro `SUPERSEDED_DO_NOT_USE_FOR_ROUTES_OR_EDITORIAL`**, sem os 30 registros antigos. Git histórico de C141 permanece acessível como trilha forense, mas **nenhum componente atual deve carregá-lo**.
- `EDITORIAL_ACTIVE_SCOPE_POLICY.json` — refeito com **4 Blogger +3 WP**, 24 deletados, `deleted_blogger_pending_authentication=0`; remove chaves de `historical_candidates_pending_authentication`, `28 global candidates` e `8 rotas pendentes`. Novos blogs futuros possíveis mediante verificação CMS + campanha exata, mas IDs apagados NUNCA reaproveitados.
- `editorial_scope_validation.py` — **nega por blog ID e por chave de rota antiga**, mesmo em tentativas de spoofing, outros domínios ou campaign. Nega Ar e referência metodológica como destino editorial. Retorna `DELETED_BY_OWNER` (não `PENDING_ACCOUNT_AUTHENTICATION`).
- `site_routes.json` — **15 rotas de blogs apagados retiradas**; `sites.d/blogger_cadeira_certa_home_office.json` foi apagado (16 rotas antigas no total). O registro `routing.sites()` falha fechado se alguma for reintroduzida; `site_launch_plan` nega ID/rota apagada.
- `tests/test_c141_global_blogger_portfolio.py` e workflow `v31_c141_global_portfolio_validation_readonly.yml` **removidos**: seu propósito era defender justamente os 24 falsos candidatos; não executar/retomar esses testes como aprovação.
- Testes editoriais antigos passaram a usar somente **duas rotas e IDs 100% sintéticos** em `tests/synthetic_site_routes.py`; preservam cenários de air fryer/liquidificador, campanhas distintas, SEO, afiliados, dedup, drafts e proteção de fontes, mas não reinserem IDs de blogs reais apagados.
- `tests/test_c143_deleted_blogger_cleanup.py`: **18 testes novos**, abrangendo 24 IDs, tombstones, anti-spoof, routes, fila de pedidos, novos blogs fictícios apenas em teste, 50 simulações, auditoria de workflows e LIVE OFF.

## 3. Cron/Writers de Loja antiga bloqueados
**18 workflows antigos de Blogger já apagados perderam o campo `on.schedule` e receberam `jobs.<writer>.if: false`**. Um 19º writer manual antigo `ventiladores_em_foco_store_autonomous.yml` também recebeu `if:false`. Exemplos incluem Achados da Rotina, Mala Pronta, Ateliê, Pedal Leve, Ventiladores, Cabelos, Air Fryers, Conecta Achados, Moda, Radar Blogger, Vitrine e outros alvos apagados. **Não alterado o cron de Cozinha, Estilo e Limpeza (Blogger ainda elegíveis), nem blogs WordPress.**

`src/blogger_policy_repo_audit.py` agora exige em 19 arquivos antigos: **SEM `schedule:` + job com marcador `V31_C143_OWNER_DELETED_JOB_DISABLED`**; a tentativa de recolocar cron ou remover o bloqueio fará a auditoria FAIL. As antigas verificações de cron mensal foram ajustadas para reconhecer os sete writers desligados, mantendo o cron mensal de Cozinha e os 17 pares SAFE/LIVE com tokens de Policy Guard intactos. Não foi feita intervenção remota em Blogger ou Shopee.

## 4. Provas de testes e GitHub Actions
- [CI PR #146 #45300132547](https://github.com/adelrib27/blogger-automation1/actions/runs/45300132547): **COMPLETED SUCCESS**, **760 testes PASS** (0 erros/falhas) e **50/50 simulações** offline `phase=C143`. Simulação confirma `current_active_sites=7`, `deleted_blogger_blocked=24`, `outcomes.DELETED_BY_OWNER=24`, `cross_account_pending=0`, `cms_writes=r2_writes=d1_writes=affiliate_mutations=0`, `live_authorized=false`. Regressões WordPress Casa 24/24, Oficina 21/21, Radar 15/15 e cross-blog PASS.
- [C143 auditor SAFE pós-merge #45300244527](https://github.com/adelrib27/blogger-automation1/actions/runs/45300244527): **COMPLETED SUCCESS**, novamente **50/50 simulações**, **18 testes de exclusão PASS**, **62 testes de cenários/contratos PASS**, `blogger_policy_guard_self_test=13/13 OK`, `BLOGGER_POLICY_REPO_AUDIT_PASS`. Job apenas `contents:read`, sem segredos e sem writes.
- [Blogger — Auditoria de Políticas pós-merge #45300244466](https://github.com/adelrib27/blogger-automation1/actions/runs/45300244466): **COMPLETED SUCCESS**, produto guard `13/13`, `BLOGGER_POLICY_REPO_AUDIT_PASS`, `BLOGGER_NEW_BLOG_POLICY_REPO_AUDIT_PASS`.
- [C133 auditor de prontidão #45300244463](https://github.com/adelrib27/blogger-automation1/actions/runs/45300244463): **SUCCESS**, somente leitura.

As execuções históricas C141/C142 provaram fatos válidos **na época**, mas suas contagens de portfólio foram definitivamente superadas pela decisão de C143. Nenhuma rotina deve retomar "24 pendentes", "28 candidatos" nem "8 sem rota".

## 5. Próximos passos seguros
1. **Retomar somente o escopo atual de 4 Blogger + 3 WordPress** e novos blogs futuros que tenham identidades inéditas legitimamente autenticadas e aprovadas; nenhum tratamento pet-only. Atualizar material de onboarding somente para blogs novos.
2. Manter **50 simulações antes de ciclos críticos**, além de QA real por SKU, fonte fabricante, variante, imagem, affiliate link da campanha, SEO, links internos, dedup, D1 quotas e GET CMS SHA.
3. Preservar os DRAFTs existentes: Blogger Móveis #`4106024906916105222` e WordPress Casa #`321`, ambos verificados anteriormente com HTML SHA exato; WordPress Casa READY `shopee:306698991:8503898928` colide com DRAFT #`314` e **NÃO pode ser consumido ou recriado**.
4. Todos os agendamentos de Loja LEGADOS para blogs apagados ficam sem cron/skip; qualquer evento antigo até a propagação do GitHub não significa publicação. Monitorar novos logs sem repetir writers.
5. **Manter `affiliate_hub_v31/autonomous_live_policy.json` com `activation=pending_policy_approval`**. Nenhum LIVE novo da C143; só após homologação E2E e autorização final expressa. Pinterest e Mercado Livre continuam separados.

## 6. Continuidade e retenção
Históricos antigos já registrados em commits Git não são apagados da história reescrevendo `main` (ação destrutiva), mas seus arquivos ativos foram **revogados/limpos**: C141 JSON pontua `SUPERSEDED`, as rotas e workflow de auditoria antigos foram removidos, a lista mínima de tombstones garante não regressão. O índice V31 e `CONTINUIDADE_ESTADO.json` precisam apontar **APENAS para C143** como verdade operacional corrente, sem herdar `pending_auth`, `28 candidates` nem `c141 history` em tarefas ativas.

**Resultado:** zero mutações CMS/R2/D1/Shopee desta C143, 24 blogs apagados pelo proprietário reconhecidos como removidos, 19 workflows desligados, 50 simulações e 760 testes reais aprovados. Não prometer trabalho em background além dos workflows já existentes.
