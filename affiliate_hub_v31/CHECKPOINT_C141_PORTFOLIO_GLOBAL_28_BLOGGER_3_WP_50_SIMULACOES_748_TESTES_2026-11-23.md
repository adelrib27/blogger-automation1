# V31 C141 — Reconciliação UNIVERSAL Blogger multiconexões: 28 candidatos + 3 WordPress

**Data local:** 2026-11-23, Recife (evidências GitHub entre 2026-11-23T23:00Z e 2026-11-24T00:08Z).
**Continuidade:** `V31-C141-20261123-28-BLOGGER-3-WP-24-PENDING-50-SIM-748-PASS-LIVE-OFF`.
**Status:** PR integrado, CI + Action remota **PASS**, cobertura histórica corrigida, **24 Blogger aguardam autenticação da conta**; sem LIVE automático.

## 1. Correção obrigatória de escopo — não confiar nos números C139/C140
**Pedido do proprietário:** o V31 deve atender **todos os Blogger atualmente ativos** e os WordPress existentes, com foco em qualidade e sem teto numérico; **excluir Ar-Condicionado sem Dúvidas**; `Vida Pet Prática` é somente **REFERÊNCIA METODOLÓGICA UNIVERSAL**, não projeto/blog-alvo/pipeline separado. Não editar, publicar ou apagar o CMS de origem por causa dessa referência.

Fonte **viva do repositório**:
- `CHECKPOINT_C102_ARTIGO_POR_BLOGGER_PRE_EXECUCAO_2026-11-23.md` e `CHECKPOINT_C102_30_BLOGGER_ARTIGOS_LIVE_2026-11-23.md`: **32 blogs Blogger inventariados** por API no ciclo C102, dos quais **30 editoriais com post LIVE verificado**, um LAB `Casa Prática Lab` e um não lançado `Meu Céu Noturno`. C102 publicou um por blog em uma autorização MANUAL específica e confirmou cada post por GET — **não autoriza LIVE automático futuro**.
- Quatro fontes de dados C102 `C102_SOURCES_BATCH_{A,B,C,D}_2026-11-23.json`: **30 IDs distintos e URLs Blogger datadas**, confrontados com 30 registros `LIVE_VERIFIED` de `C102_ARTICLE_ROLLOUT_MANIFEST_2026-11-23.json`. É prova histórica de CMS por identidade, NÃO login atual.
- `CHECKPOINT_C103_AUDITORIA_PORTFOLIO_BLOGS_2026-11-23.md`: 32 Blogger + três WP; a recomendação de congelar 23 Blogger foi explicitamente **NÃO EXECUTADA** em CMS, e está SUPERADA pela nova decisão do proprietário de cobrir todos os ativos, sem antecipar exclusões.
- Os dois conectores `Blogger Bridge V2` e `Blogger Bridge — Achados para Casa` em 23/11 **listaram os mesmos seis blogs** de uma conta. Oito consultas `get_blog` dos IDs históricos fora dessa lista receberam "não pertence à lista da conta conectada"; isso prova que **essa conexão não tem esses blogs**, não que eles foram deletados, desativados ou não sejam do proprietário. Não extrapolar uma única conexão como inventário universal.

## 2. Inventário estruturado e classificação
[Inventário detalhado C141](EDITORIAL_GLOBAL_PORTFOLIO_C141.json), versionado na main com **30 entradas**:
- **28 candidatas Blogger** a homologar no V31 universal (30 históricas menos Ar-Condicionado excluído e a referência metodológica Vida Pet).
- Entre os 28: **quatro verificados no subconjunto de conta acessível**; **24 com `HISTORICALLY_VERIFIED_PENDING_CROSS_ACCOUNT_AUTH`**. Os 24 não são "inativos". **20 de 28** já possuem rota `site_routes.json` / `sites.d`; **oito** carecem de rota universal real (**Jardim, Mala Pronta, Ateliê Criativo, Achados da Rotina, Casa Leve, Pedal Leve, Violão do Começo, Café na Medida**).
- **Três WordPress autenticados** por GET em C139: Casa e Decoração, Oficina & Garagem e Radar Tech BR.
- **31 candidatos de planejamento** (28 Blogger +3 WP) são cobertura histórica priorizada, **NÃO 31 blogs com permissão operacional já verificada** e **não um limite permanente**.
- Ar-Condicionado `2228849984262880811` = `EXCLUDED_BY_OWNER`, não excluir CMS/Loja/dados; Vida Pet `8052455848487624244` = `REFERENCE_ONLY_NOT_V31_EDITORIAL_DESTINATION`. Ambas as classificações são negativas de **onboarding V31**, não exclusões físicas. Manter metodologia C69 (Evidence Engine, SKU exato, TTL, fonte independente, failover, cooldown, SearchBudget, READY) disponível a TODOS os nichos.

## 3. Mudança de código e segurança
[PR #144](https://github.com/adelrib27/blogger-automation1/pull/144), **MERGED** SHA `17a040d2d71bf6f02dc420dd02220e817239546c`:
- `EDITORIAL_ACTIVE_SCOPE_POLICY.json` agora aponta para **inventário C141 global**, classifica os quatro `current_targets` como apenas o subconjunto com autorização dessa conexão e declara 28 candidatos em histórico + 24 pendentes de autenticação externa. **Não se usa 4 como teto geral.**
- `editorial_scope_validation.py` valida TODAS as 30 identidades/IDs/posts históricos e 28 candidatos por dado estruturado; uma rota com histórico C102 sem conta atual recebe `PENDING_ACCOUNT_AUTHENTICATION` em vez de `NOT_IN_VERIFIED_ACTIVE_INVENTORY`. A ausência de login continua **bloqueando writes**, mas **não elimina o blog do escopo**. Exclusões pessoais, referências metodológicas, URLs e identidade fake são negadas.
- **50 simulações offline** distribuídas em **31 identidades de candidatos (28 Blogger +3 WP)**, cinco cenários de exclusão Ar, cinco da referência negada, cinco de blog futuro não registrado e quatro testes extras de riscos. O loop mantém **10–50** permitidos e **50 por padrão**. `--cycle-index=${{ github.run_number }}` muda a amostragem entre cycles se novos sites elevarem o portfólio acima de 31. **Não cria limite de 31 blogs**, só fixa 50 simulações por execução.
- 20 testes novos C141 verificam todas as identidades, classificações, rotas, ausência de aprovação por outra conta, antisspoof, crescimento do inventário e rotatividade. Mantém 50 testes C140 e demais contratos.
- **8 workflows** de validação/conv. e DRAFT/CMS recebem `cycle-index` da GitHub Action (inclui um observador one-shot C141), todos offline; nenhum writer foi ligado ou quota adulterada.

## 4. Resultados reais de CI e Actions
[CI final PR #144 #45294360601](https://github.com/adelrib27/blogger-automation1/actions/runs/45294360601): **COMPLETED SUCCESS**, **748 testes**, 0 falhas/erros; **50 simulações PASS** no `cycle_index=796`, `distinct_candidate_sites_simulated=31`, `global_candidates=28`, `24 pending`, `cms_writes=r2_writes=d1_writes=affiliate_mutations=0`, `live_authorized=false`. Regressões WordPress Casa 24/24, Oficina 21/21, Radar 15/15, dedup cross-blog PASS.
- [Auditor remoto C141 #45294493367](https://github.com/adelrib27/blogger-automation1/actions/runs/45294493367) — **COMPLETED SUCCESS** após merge, 20 testes específicos PASS, 62 testes de cenário+contrato PASS, 50/50 simulações PASS no `cycle_index=1`; leitura efetiva do manifest e da política da `main`, **30 históricos, 28 candidatos, quatro conectados, 24 pendentes, 3 WP; nenhuma escrita e LIVE OFF**.
- [Scheduler pós-merge #45294493285](https://github.com/adelrib27/blogger-automation1/actions/runs/45294493285) — **SUCCESS observação**, `choose-one=SKIPPED`, `draft=SKIPPED`, `release=SKIPPED`, `audit=SKIPPED`. GET CMS autenticado+SELECT D1 confirmam os dois pilotos antigos: Blogger Móveis DRAFT #`4106024906916105222`, SHA `acf054f9eb4b65196aa46544c8402e7d603144d781604e006042059ba263569c`; WordPress Casa DRAFT #`321`, SHA `81303c4a8d9590a0f4490afa8d92c8f845e5add267195535b7de5a2d300e6877`.

**Pendência C136 resolvida por observação real**:
- [Casa cron #45293319159](https://github.com/adelrib27/blogger-automation1/actions/runs/45293319159), 23/11 23:58:40 UTC: jobs `v31_casa_discovery=SKIPPED` e `autonomo=SKIPPED` confirmados em `fetch_workflow_run_jobs`.
- [Oficina cron #45291834245](https://github.com/adelrib27/blogger-automation1/actions/runs/45291834245), 23/11 23:47:36 UTC: jobs `v31_oficina_discovery=SKIPPED` e `publicar-um-slot=SKIPPED` confirmados. Esses quatro são **pós-bloqueio PR #137**, não inferência estática.

## 5. Diagnósticos adicionais sem alterações
- Cloudflare D1 oficial consultado por **SELECT apenas** após 00:07 UTC 24/11: `v31_shopee_conversion_attempts` tinha três reservas **no dia UTC 23/11** (1 Móveis, 2 RadarWP), nenhuma linha ainda no dia 24/11. `v31_search_budget` mostrou Móveis 23/11 `SEARCH 3/3` e `HTTP 3/3`, nenhuma linha de 24/11 nesta leitura. **Não interpretar ausência de linha como autorização para dispensar limite diário**, nem realizar conversão/repetição.
- D1 `v31_ready_jobs`: `READY=1`, `USED=2` sem mudança; READY WordPress Casa SKU `shopee:306698991:8503898928` continua **CONFLICTING_DRAFT_HTML** com CMS #314 (C135), não consumir/alterar.
- [Blogger — Auditoria de Políticas #45282364553](https://github.com/adelrib27/blogger-automation1/actions/runs/45282364553), cron anterior à C141, **FAIL** porque `src/blogger_policy_repo_audit.py` referencia workflow de Loja `.github/workflows/achados_casa_store_safe.yml` ausente do repositório. Guard de produto 13/13 PASS antes de falhar na referência de arquivo. **Não presumir falha de LIVE nem restaurar workflow de publicação sem análise**; acompanhar RCA do auditor do Blogger como dívida separada, sem relaxar segurança.

## 6. Prioridades para C142
1. **Reconciliar contas Blogger reais**, não contar somente a conexão parcial. Usar os 24 IDs históricos do arquivo C141 e ler `list_blogs` das conexões adicionais quando disponíveis; confirmar que seguem ativos, credenciais e propriedade. Marcar `AUTHENTICATED_CONNECTED_ACCOUNT_SUBSET` somente após prova; não publicar no escuro. Pode exigir conexão de outra conta ou Work para verificação de credenciais, porém **não solicitar intervenção até ser indispensável**.
2. Para os oito sem rota V31, cadastrar em etapas **após** confirmar IDs, campanhas reais, nichos e fontes; nenhum `fakeblog`, link fictício ou autorização automagicamente.
3. Continuar homologação DRAFT por site com 50 simulações prévias, review de fabricante/variante, foto do CSV do mesmo SKU, links Shopee convertidos por campanha, SEO, links internos e auditoria de anti-duplicação.
4. Investigar auditor `blogger_policy_repo_audit.py` falhando por workflow antigo ausente. Não reativar Loja ou writer LIVE para "corrigir CI"; separar contrato legado de workflows realmente existentes após migração.
5. Monitorar C136, confirmar novos crons e resultados; LIVE continua `pending_policy_approval` até autorização expressa final.

**Mudanças C141:** somente GitHub código, inventário, testes, workflows SAFE e checkpoint. **Zero artigos criados, zero LIVE novos, zero R2/D1/CMS/Shopee writes ou disparo manual de publisher pela C141.** Pinterest e Mercado Livre permanecem projetos separados.
