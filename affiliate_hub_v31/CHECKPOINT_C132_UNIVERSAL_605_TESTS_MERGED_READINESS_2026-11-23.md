# C132 — Retorno ao V31 UNIVERSAL: 605 testes aprovados, DRAFT rollout parcialmente habilitado

**Data:** 23/11/2026 (America/Recife), **branch:** `main`, **repositório:** `adelrib27/blogger-automation1`.  
**Decisão do proprietário:** deixar Radar Tech BR de ser o foco exclusivo e retomar motor universal Shopee → Blogger/WordPress. **AUTO LIVE continua desativado**.

## 1. Correção concluída — 8 falhas históricas resolvidas
- Checkpoint de segurança ANTES de editar: `affiliate_hub_v31/CHECKPOINT_C132_RETOMADA_UNIVERSAL_PRE_CORRECAO_TESTES_2026-11-23.md`.
- PR [#134](https://github.com/adelrib27/blogger-automation1/pull/134) integrado por squash na `main`, commit **`c4a66c3e98178db636cdae1f4c3ac0b38b330d9c`**.
- Suíte completa [run 45258280168](https://github.com/adelrib27/blogger-automation1/actions/runs/45258280168): **605 tests, 0 errors, 0 failures, SUCCESS**. Um novo teste foi acrescentado para barrar briefing legado incompatível com a rota atual. Anteriormente eram 604 testes e 6 falhas + 2 erros.
- Ajustes em 7 arquivos de **fixtures de testes** para reconhecer a nova política tecnológica do Radar (C105/C114): Air Fryer/liquidificador/luminárias/ferramentas são excluídos do Radar, tecnologia e ar-condicionado genuíno podem entrar. Testes preservam blogs pertinentes de cozinha/decoração/ferramentas.
- Correção necessária na implementação `affiliate_hub_v31/draft_adapter.py`: o bloco comercial passa `topic=title` baseado no briefing **ligado ao produto** em vez de `topic=keyword` genérica `tecnologia`, pois `product_offer_html` exige vínculo semântico concreto. Nova verificação de `f"{category}/{niche}" in site["allowed_niches"]` **no momento do prepare_draft**, inclusive se o briefing foi aprovado antes de uma mudança de política. Nenhum bloqueio foi removido.
- **Escopo modificado:** somente `draft_adapter.py` + sete arquivos de testes. Nenhum workflow, R2, D1, CMS ou segredo foi modificado por esta correção; nenhum artigo de Radar reescrito outra vez.

## 2. Estado autônomo REAL em 23/11
- GitHub scheduler `.github/workflows/v31_autonomous_draft_scheduler.yml`: `schedule: 47 */4 * * *`, com fail-closed de site e de rollout. Último agendamento confirmado [#45137244359](https://github.com/adelrib27/blogger-automation1/actions/runs/45137244359) em 23/11 08:16 UTC: `choose-one=success`, `authenticated-history=success`, `independent-verifier=success`, `deliver-draft=SKIPPED`, `release=SKIPPED`. Resultado do verificador: `{"site_key":"blogger_moveis_para_cada_canto","status":"NO_NEW_OFFER","reason":"research_budget_exhausted"}`. Job mostra env `V31_AUTODRAFT_ACTIVE=true`, `V31_AUTODRAFT_ROLLOUT_SITE=blogger_moveis_para_cada_canto`, `V31_AUTODRAFT_FULL_ROLLOUT_APPROVED` vazio; **não concluir que o rollout all foi autorizado**. Último agendamento adicional anterior [#45075573402](https://github.com/adelrib27/blogger-automation1/actions/runs/45075573402) em 22/11 também passou pela verificação sem entregar novo DRAFT.
- Cloudflare D1 **somente SELECT** na conta oficial ID `ebb8d5b4cf9a2cb850c6d8051bd2661f`, banco `9bfce7a4-6167-4bfc-a65e-a74c1a34f064`: para Móveis `2026-11-23`, **SEARCH=3/3** e **HTTP=3/3**; para 22/11, ambos 1/3. Leases ativos=0. `v31_ready_jobs`: Blogger Móveis USED=1; WordPress Casa USED=1 e READY=1; evidências verificadas total 3. Meta de queries SELECT `changes=0`. **Não renovar quota artificialmente e não consumir READY em escrita sem autorização de homologação operacional.**
- CMSs autenticados: Blogger Móveis post ID `4106024906916105222` com `status=draft` na API; WordPress Casa e Decoração post ID `321` com `status=draft`. Esses dois DRAFTs já existiam em C81; **não criar duplicatas**.
- O motor de LIVE universal requer vars `V31_AUTOLIVE_ACTIVE==true` e política aprovada, além de ambiente segregado `v31-autonomous-live`; as execuções observadas tiveram `release=SKIPPED`. O workflow Radar legado também conserva `if: false` e `publicacao_automatica=false`. **Não ativar LIVE**.

## 3. Lacuna de implantação POR SITE (não falha na universalidade do catálogo)
- Cadastro declarativo total no repositório: **24 rotas**, 21 Blogger e 3 WordPress; suporta novos blogs por arquivos `sites.d/*.json` sem editar Python.
- Perfis para o **novo verificador autônomo** em `affiliate_hub_v31/autonomous_review_sources.json`: somente **2**: `blogger_moveis_para_cada_canto` e `wordpress_casa_decoracao`. Também existem somente **2** pedidos explícitos em `site_requests.d`.
- Prioridade de portfólio Blogger do proprietário `BLOGGER_PORTFOLIO_FIVE_2026-11-23.json`: **5 preservados**, mas com maturidade diferente:
  - Cozinha Sem Complicação ID `3552757910439359679`: rota `blogger_cozinha_sem_complicacao`, campanha `cozinhasemcomp`; ainda sem request/perfil de revisão.
  - Móveis para Cada Canto ID `1439741542627895062`: rota `blogger_moveis_para_cada_canto`, campanha `moveisparacadacanto`; request + perfil presentes; piloto ativo.
  - Estilo no Dia a Dia ID `4830103887652146866`: rota `blogger_estilo`, campanha `estilo`; sem request/perfil.
  - Limpeza Inteligente ID `7757953554206491487`: rota `blogger_limpeza`, campanha `limpeza`; sem request/perfil.
  - Vida Pet Prática ID `8052455848487624244`: **sem rota atual e sem campanha verificada no registry**, também sem request/perfil. Não inventar campanha ao cadastrar.
- WordPress: Radar Tech BR rota `wordpress_radartechbr` campanha `radarwp` sem perfil/request do verificador; Casa e Decoração rota `wordpress_casa_decoracao` campanha `casaedecoracaowp` com perfil/request e DRAFT verificado; Oficina & Garagem rota `wordpress_oficina_garagem` campanha `oficinawp` sem perfil/request.
- Os cinco Blogger priorizados **não limitam a capacidade universal futura**, tampouco autorizam deletar blogs de origem ou migrar posts sem validação SEO e backup.

## 4. O que permanece necessário antes de liberar produção geral
1. Registrar, com fonte real, a rota/campanha do blog Vida Pet Prática (sem inventar subID ou link).
2. Criar requests e perfis de revisão (e fontes confiáveis por produto/campanha) para quatro Blogger restantes e dois WP restantes **um de cada vez**, com DRAFT canário, limites por site, deduplicação e CMS readback; só depois considerar ampliação de rollout.
3. Com orçamento renovado e D1 compatível, verificar um **novo DRAFT** do piloto agendado, e atestar imagem/URL/CTA/hash no CMS; atualmente `NO_NEW_OFFER` por 3/3 pesquisas, logo não há novo draft a homologar hoje.
4. Validar gerenciamento de templates, links internos, SEO, normas de divulgação de afiliado, metas diárias e monitoramento de falhas por site sem limitar o catálogo à lista atual.
5. **Não ativar AUTO LIVE** sem política assinada e autorização específica do proprietário; não confundir 605 testes verdes com prova de automação real para todos os sites.

**Código de continuidade:** `V31-C132-20261123-605-TESTS-GREEN-MERGED-2-OF-8-AUTODRAFT-READY-LIVE-OFF`.
