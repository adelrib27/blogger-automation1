# V31 C142 — Auditorias Blogger recuperadas sem reativar writers LIVE

**Data Recife:** 2026-11-23 (logs de CI até 2026-11-24T00:21Z).
**Código de retomada:** `V31-C142-20261123-760-TESTS-50-SIM-BLOGGER-POLICY-PASS-LIVE-OFF`.
**Status:** C142 homologado em CI e em duas Actions remotas READ ONLY, LIVE editorial permanece OFF.

## Origem e proteção da continuidade
- [Preview C142](CHECKPOINT_C142_PREVIEW_AUDITOR_BLOGGER_POLITICA_WORKFLOWS_AUSENTES_2026-11-23.md) registrado em main no commit `60ead9387898db82dd8c5b045737c72db7f86da3` ANTES das alterações.
- Base antes da PR C142: [checkpoint C141](CHECKPOINT_C141_PORTFOLIO_GLOBAL_28_BLOGGER_3_WP_50_SIMULACOES_748_TESTES_2026-11-23.md), 28 Blogger candidatos no histórico C102, 4 autenticados na conexão atual, 24 aguardando outras contas, 20 de 28 roteados, 8 sem rota, 3 WP. Ar-Condicionado excluído do V31; Vida Pet somente métodos aplicados universalmente, NÃO blog-alvo/pipeline separado.
- Auditor Blogger anterior [#45282364553](https://github.com/adelrib27/blogger-automation1/actions/runs/45282364553) FALHOU porque aguardava antigo `.github/workflows/achados_casa_store_safe.yml`; o par `achados_casa_store_autonomous.yml` também já estava ausente, enquanto 36 referências a workflows ainda existiam. Produto Guard 13/13 PASS nessa execução, erro era auditor estático desatualizado.

## Mudanças verificadas
[PR #145](https://github.com/adelrib27/blogger-automation1/pull/145) squash MERGED SHA `0a30fdb9f43b1db0a43f4f3fa5cd62c4fe780792`.
1. `src/blogger_policy_repo_audit.py`: preservou verificação dos **17 pares efetivamente existentes SAFE/LIVE**, incluindo os mesmos requisitos de policy guard, código de HTML e cron. Remoção somente de referências ativas ao par de Loja Blogger Achados para Casa já AUSENTE. Adicionado `audit_retired_achados_casa_pair()`: falha fechada se UM OU AMBOS reaparecerem antes de revisão explícita de política. Não substitui pelo writer WordPress Casa nem inventa outro publisher.
2. Oito asserts de agendas nos workflows de Loja Blogger foram ajustados de **diário antigo** para o **mensal real** (sem mudar YAML de publicação): Casa em Ordem dia 8, Escolha Certa dia 13, Achados que Valem dia 3, Guia dia 15, Moda dia 18, Achadinhos Beleza dia 1, Radar Blogger dia 22, Cozinha dia 11. Cron UTC e `timezone` mantidos exatamente como nos YAML existentes.
3. `src/blogger_new_blog_policy_repo_audit.py` recebe correção apenas de expectativa: a infraestrutura histórica Loja da fonte metodológica Vida Pet possui agendamento mensal dia 26 `35 11 26 * *`; o código anterior esperava um cron diário obsoleto. **NENHUM writer ou arquivo workflow Vida Pet foi editado por esta C142**, nem foi criado projeto/pipeline pet-only no V31.
4. `affiliate_hub_v31/tests/test_c142_legacy_blogger_policy_audit.py` contém **12 testes offline** incluindo par aposentado, reaparições, 17 pares existentes, oito datas mensais, auditor histórico e proibição de writes no auditor.
5. `.github/workflows/v31_c142_blogger_policy_repo_audit_readonly.yml` é execução one-shot por alteração no próprio arquivo, com `contents:read` e `persist-credentials:false`. Simula **50 cenários** antes de auditar, não recebe tokens de Blogger/Shopee/D1/R2, não publica e não ativa cron.

## Evidências
- [CI universal #45296189579](https://github.com/adelrib27/blogger-automation1/actions/runs/45296189579) **SUCCESS**, `760 tests` PASS + **50/50 simulações**, cobrindo 28 Blogger históricos+3 WP, 24 pendentes de outra conexão, zero writes via simulação; regressões WordPress Casa 24/24, Oficina 21/21, Radar 15/15 e dedup crossblog PASS.
- [Blogger — Auditoria de Políticas #45296451078](https://github.com/adelrib27/blogger-automation1/actions/runs/45296451078) **SUCCESS pós-merge**, `blogger_policy_guard_self_test=13/13 OK`, `BLOGGER_POLICY_REPO_AUDIT_PASS`, `BLOGGER_NEW_BLOG_POLICY_REPO_AUDIT_PASS`. Isso comprova regressão de política atual e de infraestrutura histórica, NÃO comprova novos posts ou autorização LIVE.
- [C142 auditor one-shot #45296451102](https://github.com/adelrib27/blogger-automation1/actions/runs/45296451102) **SUCCESS pós-merge**: 50/50 simulações, 12/12 novos testes de política, 13/13 guard de produto e `BLOGGER_POLICY_REPO_AUDIT_PASS`; sem API/CMS writes ou tokens de acesso.
- Nenhum cron de publicação, variável de LIVE, autorização D1, cota de afiliado ou login CMS foi modificado. Política `affiliate_hub_v31/autonomous_live_policy.json`: `activation: pending_policy_approval`.

## Dívida descoberta em outra automação que NÃO foi reexecutada
- [Ventiladores em Foco — Loja Shopee LIVE #45295890185](https://github.com/adelrib27/blogger-automation1/actions/runs/45295890185), `2026-11-24T00:17Z`, **FAIL**. Log mostrou erros Shopee `10000 System Error` nos endpoints extras/top-performance e terminou em Google Blogger API `HTTP 404 Requested entity was not found` ao consultar blog ID `4473989735719981382`, post ID `1410775502611365606`. Não confundir com a falha anterior do auditor de políticas; é um **job legado de Loja LIVE separado**. Não é possível inferir quais operações anteriores ao 404 foram concluídas sem consulta CMS autenticada nessa conta. Não repetir rotação nem ajustar ID no escuro.
- Essa identidade Ventiladores aparece em C141 como **HISTORICAMENTE DOCUMENTADA, atualmente PENDING_ACCOUNT_AUTHENTICATION**; o 404 é compatível com post inexistente, acesso incorreto ou ID obsoleto, não prova blog desativado.
- **Próximo passo seguro:** GET CMS autenticado do blog/post na conta proprietária, conferir atualidade do alvo, cron e etapa de alterações antes de ajustar a rotação. Não reexecutar writer LIVE por causa de uma falha de API.

## Gates restantes do V31
- C141: **28 Blogger candidatos históricos +3 WP**, 4 Blogger já acessíveis, 24 necessitam autenticação das outras contas; 8 sem rota, nenhum blog novo será autorizado só pelo inventário histórico.
- Manter 50 simulações por ciclo antes de mutações, títulos/HTML originais, SKU/variante/fonte independente/foto real, campanha/link afiliado, links internos, disclaimer, quota, GET hash e antirrepetição.
- READY WP Casa `shopee:306698991:8503898928` conflita com DRAFT #314 `CONFLICTING_DRAFT_HTML`: **não consumir nem sobrescrever**.
- DRAFTs antigos Blogger Móveis #4106024906916105222 e WP Casa #321 confirmados após C141 sem nova escrita; Casa/Oficina legados quatro jobs schedule SKIPPED (C141).
- **LIVE V31 OFF**, exigindo homologação E2E e autorização final expressa do proprietário. Pinterest e Mercado Livre separados.

**Resultado C142:** corrigida auditoria estática Blogger +1 par aposentado protegido, 8 crons mensais validados, 50/50 simulações, 760 testes, duas Actions remotas SUCCESS, nenhuma publicação/cota/autorização LIVE decorrente da C142; falha de Ventiladores reportada separadamente e aguardando verificação de conta.
