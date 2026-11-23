# V31 C134 — homologação SAFE de observabilidade + pausa do LIVE legado

**Data:** 2026-11-23, America/Recife. **Repositório:** `adelrib27/blogger-automation1`, branch `main`.
**Código de retomada:** `V31-C134-20261123-623-TESTS-LEGACY-LIVE-GUARDED-DRAFT-BUDGET-BLOCKED`.
**Status:** C134 AUDITORIA E CORREÇÕES SAFE INTEGRADAS, **HOMOLOGAÇÃO UNIVERSAL DE NOVOS DRAFTs AINDA PENDENTE**.
**Proibição:** LIVE automático não autorizado. Sem alterações de `V31_AUTOLIVE_ACTIVE` ou da política de assinatura.

## 1. Fontes e conferências antes de mutações
Foram lidos na `main` `V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json`, [C133](CHECKPOINT_C133_AUDITOR_PRONTIDAO_UNIVERSAL_610_TESTES_2026-11-23.md), PRs e Actions. O [PREVIEW C134](CHECKPOINT_C134_PREVIEW_AUDITORIA_ESTADO_VIVO_2026-11-23.md) foi salvo na `main` no commit `61232868407da247a65e181cef61281e1cc843bf` **antes de alterações de código**.

- C133: PRs #134 e #135 já integrados, [610 testes PASS #45259792390](https://github.com/adelrib27/blogger-automation1/actions/runs/45259792390), auditor [#45259940897](https://github.com/adelrib27/blogger-automation1/actions/runs/45259940897). Não repetir alterações já concluídas.
- Último schedule DRAFT inspecionado: [#45260835997](https://github.com/adelrib27/blogger-automation1/actions/runs/45260835997), 23/11 20:34 UTC, GitHub concluiu `success` mas verificador retornou `NO_NEW_OFFER: research_budget_exhausted`; `deliver-draft` e `release` SKIPPED; **nenhum novo DRAFT comprovado**.
- GitHub `main` auditada antes das alterações: `70af55cb6c850639274c773d92f009171db50e46`.
- Cloudflare conexão **conta oficial** `adeiltonrib27@gmail.com`, account `ebb8d5b4cf9a2cb850c6d8051bd2661f`: GET real confirmou bucket R2 `v31-editorial-shopee` e D1 `v31-universal-ready-safe` UUID `9bfce7a4-6167-4bfc-a65e-a74c1a34f064`; nenhum objeto/snapshot/catálogo modificado.
- D1 SELECT-only: 0 leases; 2 jobs USED, 1 READY, 3 evidências; Móveis campanha `moveisparacadacanto` em 23/11 SEARCH=3/3, HTTP=3/3. READY do WordPress Casa (`casaedecoracaowp`) permanece **não consumido**. Não aumentar limites nem refazer pesquisa.
- CMS via Blogger API: `Móveis para Cada Canto` draft #`4106024906916105222` continua `draft`, HTML com imagem, URL Shopee e disclosure. WordPress Casa REST GET confirmou draft #`321` como `draft` (Vaso Rizzo Imperial). Histórico WP artigo #305 `publish` de produto diferente; jamais reutilizar READY sem cross-check do CMS.
- Blogger Vida Pet Prática GET confirmou **blog real** ID `8052455848487624244`, URL `https://vida-pet-pratica.blogspot.com/`; **não foi encontrada/verificada campanha de afiliado V31 para esta rota**, não registrar rota por adivinhação.
- Firecrawl do conector presente nesta conversa indicou **327 créditos disponíveis**, mas não há prova de equivalência com a chave usada pelo GitHub V31; não tratar saldo como orçamento autorizado deste workflow.
- `affiliate_hub_v31/autonomous_live_policy.json` mantém `activation: pending_policy_approval`; `v31_autonomous_draft_scheduler.yml` condiciona LIVE a variável e política assinada. Execução #45260835997 release SKIPPED.

## 2. Correção da observabilidade C134 — PR #136
[PR #136](https://github.com/adelrib27/blogger-automation1/pull/136) integrado em `main` via squash `7b44786b176d6dbac9fb9e16cad7670b10d64e24`.

- Adicionou `affiliate_hub_v31/autodraft_schedule_outcome.py`: `NO_NEW_OFFER: research_budget_exhausted` agora produz `BLOCKED_RESEARCH_BUDGET`; não trata sucesso de job como artigo novo; recibo completo correlaciona site, fingerprint, ID e hash somente para `DRAFT_VERIFIED`; não infere criação nova nem estado LIVE.
- Reusable workflow exporta `verification_receipt` mesmo quando o publicador DRAFT é pulado. Auditor de schedule gera resultado operacional explícito, sem rede extra ou escrita.
- Nove testes novos, [CI #45263710289](https://github.com/adelrib27/blogger-automation1/actions/runs/45263710289) **619/619 PASS**, regressões WP e cross-blog PASS.
- Não alterou rotas, quotas, credenciais, CMS, R2, D1, scheduler cron nem LIVE.

## 3. Risco descoberto e correção LIVE legado — PR #137
A auditoria encontrou **dois fluxos editoriais legados com schedule ativo e configuração de publicação LIVE**, independentes do `V31_AUTOLIVE_ACTIVE`:
- Casa `.github/workflows/casa_editorial_generate_schedule.yml`: 3 crons/dia, antes `CASA_LIVE_PUBLISH_ENABLED=true`, `CASA_WORDPRESS_STATUS=publish`. Job publicador efetivamente executou em [#45102194225](https://github.com/adelrib27/blogger-automation1/actions/runs/45102194225); essa execução mostrou `draft_ready=0`, portanto não comprova novo post naquela rodada.
- Oficina `.github/workflows/oficina_editorial_autonomous.yml`: 2 crons/dia, antes `OFICINA_LIVE_PUBLISH_ENABLED=true`, `OFICINA_WORDPRESS_STATUS=publish`. Job publicador efetivamente executou em [#45095411810](https://github.com/adelrib27/blogger-automation1/actions/runs/45095411810) e havia candidato `draft_ready=1`, **não foi demonstrado qual post, se algum, foi LIVE naquela rodada**.

[PR #137](https://github.com/adelrib27/blogger-automation1/pull/137) integrado via squash `daa4554f3bcb6aec24fdba3043894dcf877e791e`:
- `false &&` explícito nos 4 jobs (descoberta+writer de cada legado), prevenindo execução sob schedule, push e dispatch enquanto em HOLD.
- Defesa em profundidade: `LIVE_PUBLISH_ENABLED=false` e `WORDPRESS_STATUS=draft` em ambos.
- Quatro testes SAFE novos confirmam bloqueios e preservação dos gates universais/Radar.
- [CI #45264548509](https://github.com/adelrib27/blogger-automation1/actions/runs/45264548509) **623/623 PASS**, Casa 24/24, Oficina 21/21, Radar 15/15 e cross-blog PASS.
- **HOLD destes dois writers é proposital e reversível somente após homologação/autorização**; não remove seus arquivos e não altera posts existentes. Workflow manual de release segue separado e sem acionamento automático. Ainda falta observar uma execução `schedule` posterior ao merge mostrando jobs `skipped`.

## 4. O que NÃO foi feito
- Nenhum novo DRAFT gerado na C134; última tentativa agendada do Móveis bloqueada por cota diária real.
- Nenhum LIVE, chamada publish do CMS, conversão Shopee, pesquisa Firecrawl, operação de escrita R2/D1 ou mutação de CMS **executada por esta C134**.
- Não foi consumido o READY antigo do Casa nem repetido o SKU previamente usado.
- Não foram criadas campanhas falsas, não foram cadastrados 6 sites incompletos como se homologados; não houve rollout `all`.
- Sem intervenção em Pinterest, Mercado Livre, Vida Pet laboratório ou outras contas Cloudflare.

## 5. Prontidão universal e o que precisa ser resolvido em C135+
Prioridades permanecem **8** (5 Blogger, 3 WordPress): **2 configurados para preflight local** (Móveis, Casa), **5 com rota mas sem perfil+pedido** (Cozinha, Estilo, Limpeza, Radar, Oficina), **1 com blog real mas sem rota+campanha V31 verificadas** (Vida Pet).
A arquitetura `sites.d`/solicitações/profiles continua extensível, sem teto de blogs/artigos. Os 2 configurados ainda exigem canário operacional recente e um sucesso real de agendamento.

Gates para retomar após este checkpoint:
1. Conferir schedule posterior ao PR #137 e garantir jobs legados `SKIPPED` sem alterar postagem existente.
2. Na renovação **natural** da cota D1 do Móveis (não simular/resetar, nem gastar mais 23/11 UTC), observar um novo schedule e confirmar por GET CMS: `draft`, ID, HTML aprovado imutável, hash, imagem do SKU real, URL afiliada campanha correta, SEO, disclosure, links internos LIVE do mesmo blog e replay sem duplicata.
3. Revisar o READY ainda livre do WP Casa contra histórico do CMS, assinatura R2/evidência TTL e campanha, sem consumir até canário controlado e idempotente.
4. Para os cinco com rota: validar fontes exatas por SKU, credenciais, custos, campanha e identidade CMS **antes** de criar profile/request e permitir fluxo, gradualmente um site por vez.
5. Para Vida Pet: usar identidade real do Blogger; **aguardar confirmação técnica de campanha V31 real**, sem inferir `sub_id` a partir de blog ou laboratório. Guardar qualquer evidência no GitHub.
6. Só depois de homologação E2E e confirmação final do proprietário, criar/autorizar política LIVE assinada em **um** site piloto. Não alterar `activation: pending_policy_approval` nem `V31_AUTOLIVE_ACTIVE` previamente.

**Critério de aceite TOTAL AINDA NÃO SATISFEITO**: produção autônoma de novos DRAFTs em Blogger e WordPress sob quota e verificação real de ponta a ponta, sem duplicação, e rollout gradual homologado. **C134 entrega segurança e observabilidade, não a conclusão do V31.**

## Continuidade segura
Leitura obrigatória no próximo ciclo: `V31_CONTINUAR_AQUI.md` -> `CONTINUIDADE_ESTADO.json` -> ESTE checkpoint C134 -> C133, Actions recentes e estado real APIs. Não repetir PRs #134–#137. Trabalhar em branch, PREVIEW antes da próxima mutação e só mesclar após CI verde. **LIVE OFF** até autorização expressa.

## 6. Inventário CMS adicional autenticado (READ ONLY, 23/11/2026)
A revisão pontual de rotas prioritárias identificou os alvos reais sem habilitar publicação:
- **Blogger Cozinha Sem Complicação:** API Blogger GET blog ID `3552757910439359679` confirma `https://cozinha-sem-complicacao.blogspot.com/` e título; não implica perfil independente ou pedido habilitado.
- **Blogger Estilo no Dia a Dia:** GET ID `4830103887652146866`, título API **Estilo no Dia a Dia e Acessórios**, URL `https://estilo-no-dia-a-dia-e-acessorios.blogspot.com/`; rótulo do portfólio resumido difere do título completo, mas ID corresponde. Não renomear nem inferir campanha.
- **Blogger Limpeza Inteligente:** GET ID `7757953554206491487`, URL `https://limpeza-inteligente.blogspot.com/`.
- **Blogger Vida Pet Prática:** GET ID `8052455848487624244`, URL `https://vida-pet-pratica.blogspot.com/`; verificação de blog/URL **não comprova** campanha de afiliado.
- **WordPress Oficina & Garagem:** conexão REST autenticada confirmou 3 DRAFTs históricos (IDs 17, 15, 13) e 17 posts LIVE totais; último LIVE listado #129 de 22/11. Nenhum post editado.
- **WordPress Radar Tech BR:** conexão REST autenticada confirmou 19 DRAFTs, IDs recentes 355/354/353 (23/11), e 37 posts LIVE totais; último LIVE listado #326 de 22/11. Nenhum post editado.
- **WordPress Casa e Decoração:** REST GET `/wp/v2/posts/321?context=edit` confirmou `status=draft` e conteúdo com `data-v31-product-key` `shopee:400124163:42079451217`, imagem exata de oferta, link Shopee com `nofollow sponsored`, aviso de afiliado e link interno do mesmo domínio. Não declarar SHA remota idêntica sem cotejo byte a byte com envelope R2; o GET confirma estado e elementos comerciais.
- Observação: os DRAFTs anteriores existentes nesses CMS não são prova de que os seis sites restantes tenham perfis autónomos homologados, nem autorização para LIVE. Os contadores de posts refletem as respostas das APIs no instante da consulta.
