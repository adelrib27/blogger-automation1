# V31 C140 — motor universal único, 50 simulações em cada ciclo crítico

**Data:** 2026-11-23, America/Recife. **Repositório:** `adelrib27/blogger-automation1`, branch `main`.
**Código de continuidade:** `V31-C140-20261123-50-SIMULATIONS-728-TESTS-UNIVERSAL-ONLY-LIVE-OFF`.
**Status:** C140 CONCLUÍDA para **gate offline de escopo e simulações**; NÃO é homologação E2E de todos os CMS, nem autorização de LIVE.

## 1. Decisão do proprietário (prevalece sobre C139)
- Em cada ciclo crítico de execução do V31, realizar **de 10 a 50 SIMULAÇÕES**; a implementação assume **50 por padrão** e falha fechada fora de 10–50.
- `Vida Pet Prática` foi somente **fonte de ideias de engenharia** para o sistema **UNIVERSAL**. **NÃO tratá-la como blog-alvo, projeto, fila, writer ou exceção individual do V31.** Qualquer técnica validada (independentemente do nicho de origem) é patrimônio de **um único motor editorial** Blogger+WordPress.
- Por esta correção, a referência foi **retirada do inventário de destinos V31**. O CMS de origem e qualquer conteúdo remoto NÃO foram alterados nem desativados. A contagem C139 `5 Blogger + 3 WP` foi substituída pela foto C140: **4 Blogger** (Móveis, Cozinha, Estilo, Limpeza) **+ 3 WordPress** (Casa, Oficina, Radar), e **Ar-Condicionado sem Dúvidas excluído**. Os números são um inventário atual, não teto fixo de blogs para o futuro. Nenhum outro blog será cadastrado sem prova de atividade/identidade/campanha.
- Qualidade acima de quantidade: SEO, fatos independentes, SKU e variante exatos, imagem real, link afiliado convertido na campanha correta, links internos e antirrepetição, mantendo políticas de publicação LIVE em HOLD.

## 2. Referências revisadas antes de alterar código
- `V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json`, `EDITORIAL_ACTIVE_SCOPE_POLICY.json`, último [checkpoint C139](CHECKPOINT_C139_DECISAO_ESCOPO_TODOS_BLOGS_ATIVOS_EXCETO_ARCOND_2026-11-23.md) da branch main `f0ad07716633c7cb176fc9bf127212b4210b6186`.
- Relatório mestre anexo V31 C80, seção 4.4: a fusão C69 já definiu a metodologia universal Evidence Engine, identidade de SKU/modelo, fontes confiáveis, TTL 7 dias sem renovação em leitura, duas evidências exatas quando aplicável, Candidate Failover, Evergreen, cooldown SKU/ângulo, anti-duplicação, SearchBudget, buffer READY, isolamento `site_key+campaign`. Fusão não é implantação de fluxo pet-only.
- PREVIEW C140 [salvo antes do código](CHECKPOINT_C140_PREVIEW_50_SIMULACOES_MOTOR_UNIVERSAL_2026-11-23.md) no commit `458cb18ae8c2d7f270a240d5bb5968aa27b038cb`.

## 3. Código e ensaios concretos
[PR #143](https://github.com/adelrib27/blogger-automation1/pull/143) **MERGED** via squash `5dc4dcdd114e706b872caf02484a95b52a2dc6bd`.

- `affiliate_hub_v31/EDITORIAL_ACTIVE_SCOPE_POLICY.json`: remove a referência individual da lista dos destinatários; preserva métodos de engenharia como `universal_reference_methodology`, com requisitos genéricos e proibição de projeto/rota/writer/blog-alvo específico. `simulation_gate`: mínimo 10, alvo 50, máximo 50, offline, nenhuma mutação.
- `affiliate_hub_v31/editorial_scope_validation.py`: avaliador agnóstico a nicho, identidade exata site_key/plataforma/identificador, escopo ativo autenticado, exclusão expressa, campanha e cinco dimensões de qualidade. `PREFLIGHT_ONLY_NOT_AUTHORIZED` é **apenas simulação de elegibilidade para revisão**, NUNCA autoriza CMS write ou LIVE. Toda resposta fixa `allows_cms_write=false`, `allows_live=false`, `allows_affiliate_mutation=false` e `network_calls=0`.
- Matriz reproduzível de **10 identidades × 5 riscos = 50 simulações independentes**. Dez identidades: sete sites ativos registrados, um antigo excluído, uma rota histórica não ativa e um futuro blog genérico sem registro. Cinco cenários por identidade: todos os fatores marcados válidos somente na simulação, falta de link de campanha, falta de fonte factual, colisão/duplicata CMS e solicitação de LIVE.
- `affiliate_hub_v31/tests/test_c140_50_universal_scope_simulations.py`: **50 testes individuais** de simulação mais 12 contratos, incluindo testes do guard integrado na fila real com rota Blogger excluída, rota histórica recusada, Blogger piloto Móveis permitido e request desabilitado ignorado.
- `site_request_queue.load_requests` exige escopo ativo para TODO request habilitado — assim writers universais e conversão agendada não processam rota antiga/excluída nem destino fora do inventário atual por engano. `site_launch_plan.preview_site_launch` rejeita expressamente a rota excluída mesmo em chamadas manuais de planejamento/conversão, sem apagar sua rota histórica. Novos sites exigem inventário CMS, atualização de política e campanhas reais; NÃO são proibidos permanentemente.
- Execução explícita `python -m affiliate_hub_v31.editorial_scope_validation --cases 50` adicionada antes das etapas de conversão ou DRAFT em **sete workflows relevantes**: `v31_editorial_catalog_safe.yml`, `v31_universal_request_queue_daily.yml`, `v31_universal_converter_on_demand.yml`, `v31_universal_blogger_autodraft_daily.yml`, `v31_universal_wordpress_autodraft_daily.yml`, `v31_autonomous_draft_scheduler.yml` e `v31_independent_review_draft.yml`. Simulações não tocam Shopee, Firecrawl, D1, R2, Blogger ou WordPress.

## 4. Resultado validado e evidência auditável
[CI final C140 #45288648233](https://github.com/adelrib27/blogger-automation1/actions/runs/45288648233): **COMPLETED SUCCESS** na última revisão da PR. Saída do gate `V31_SCOPE_SIMULATIONS`: `executed=50`, `passed=50`, `failed=0`, `cms_writes=0`, `d1_writes=0`, `r2_writes=0`, `affiliate_mutations=0`, `live_authorized=false`.
- Classes da simulação: `PREFLIGHT_ONLY_NOT_AUTHORIZED=7`, `AFFILIATE_CAMPAIGN_UNVERIFIED=7`, `INDEPENDENT_FACTS_MISSING=7`, `CMS_DUPLICATE_OR_CONFLICT=7`, `LIVE_NOT_AUTHORIZED=7`, `EXCLUDED_BY_OWNER=5`, `NOT_IN_VERIFIED_ACTIVE_INVENTORY=5`, `ROUTE_NOT_REGISTERED=5` = **50**.
- Suíte universal offline: **728 testes**, zero falhas/erros; regressões Casa 24/24, Oficina 21/21, Radar 15/15, antirrepetição cross-blog PASS.
- Post-merge `main`: [Action #45288813066](https://github.com/adelrib27/blogger-automation1/actions/runs/45288813066) **COMPLETED SUCCESS** com `observe-homologation` aprovado: GET CMS e SELECT D1 confirmaram Blogger Móveis DRAFT #`4106024906916105222` SHA256 `acf054f9eb4b65196aa46544c8402e7d603144d781604e006042059ba263569c` e WP Casa DRAFT #`321` SHA256 `81303c4a8d9590a0f4490afa8d92c8f845e5add267195535b7de5a2d300e6877`; jobs `choose-one`, `draft`, `release` e `audit` ficaram **SKIPPED** nessa execução de observação. **Nenhum novo DRAFT ou LIVE produzido pela C140**.

## 5. Contrato para C141+
1. Manter **50 simulações offline** por ciclo crítico via passos integrados; continuar regressões e validação remota das credenciais/CMS/R2/D1 quando uma operação for efetivamente permitida. Simulação PASS não elimina verificação factual externa e GET pós-escrita.
2. Retomar C138: fila comercial hoje tem 2 requests ativos. C137 R2 tinha 12 candidatos (4 Cozinha, 4 Estilo, 4 Limpeza), zero links afiliados na campanha exata; não inventar nem converter fora da cota. Verificar quotas atuais antes de novos disparos, sem reset, duplicação nem ultrapassar limites.
3. Manter todos os destinos editoriais atuais como alvos de homologação universal (4 Blogger + 3 WP); novos blogs futuros exigem verificação CMS e inclusão explícita na política, sem pipelines personalizados. Não tratar a referência Vida Pet como site V31 ou projeto paralelo.
4. READY WordPress Casa `shopee:306698991:8503898928` colide com DRAFT #314 (hash divergente), **não consumir**. Acompanhar monitor C136 (cron `47 23 * * *` UTC), prova de legado Casa/Oficina SKIPPED ainda pendente.
5. Política LIVE `pending_policy_approval`: nenhum activate LIVE antes de homologação E2E, autorização final explícita do proprietário e política aprovada; Pinterest separado do V31.

**Mudanças reais C140:** somente código, testes, workflows SAFE e documentação GitHub. **Zero writes CMS/D1/R2/Shopee causados pela C140; zero posts novos, zero LIVE.**
