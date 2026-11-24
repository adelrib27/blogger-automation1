# V31 — CONTINUAR AQUI (fonte de verdade operacional única)

**Checkpoint vigente: C144 — 23/11/2026, America/Recife.**  
**Código de retomada:** `V31-C144-20261123-PET-BLOGGER-ACTIVE-UNONBOARDED-METHOD-C69-SEPARATE-PR147-CI768-50SIM-LIVE-OFF`

> **REGRA CRÍTICA:** o proprietário já excluiu **24 blogs Blogger históricos**, anteriormente classificados incorretamente como pendentes. Esses IDs continuam nas tombstones `EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json`, permanentemente inelegíveis a novo login, rota, campanha, artigos, Loja ou cron. **NÃO reabrir C102/C141, não reautenticar nem recuperar os 24.**

> **CORREÇÃO C144 — NÃO CONFUNDIR DOIS OBJETOS:** `Vida Pet Prática` é um **BLOG BLOGGER REAL, ATIVO**, ID `8052455848487624244`, URL `https://vida-pet-pratica.blogspot.com/`, confirmado por `get_blog` e duas listagens autenticadas em 23/11. **Separadamente**, as IDEIAS/MÉTODOS de engenharia desenvolvidos na C69 foram fundidos ao V31 como arquitetura editorial UNIVERSAL para TODOS os nichos. O blog real não é metodologia, não foi apagado e não deve ser classificado `reference_only`; tampouco tem automaticamente writer/campanha V31. Seu estado correto é `CMS_ACTIVE_ONBOARDING_REQUIRED` até registrar e comprovar rota/campanha.

## Ordem obrigatória de leitura
1. Este `V31_CONTINUAR_AQUI.md`.
2. [Estado estruturado C144 — `CONTINUIDADE_ESTADO.json`](affiliate_hub_v31/CONTINUIDADE_ESTADO.json).
3. [Checkpoint final C144](affiliate_hub_v31/CHECKPOINT_C144_VIDA_PET_BLOGGER_ATIVO_DISTINCAO_C69_CI_768_2026-11-23.md), [preview gravado antes do código](affiliate_hub_v31/CHECKPOINT_C144_PREVIEW_VIDA_PET_ATIVO_ESCOPO_2026-11-23.md) e [PR #147](https://github.com/adelrib27/blogger-automation1/pull/147).
4. [Política atual](affiliate_hub_v31/EDITORIAL_ACTIVE_SCOPE_POLICY.json), [tombstones](affiliate_hub_v31/EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json), [LIVE policy](affiliate_hub_v31/autonomous_live_policy.json), [protocolo](affiliate_hub_v31/CONTINUIDADE_PROTOCOLO.md), [issue-mestre #54](https://github.com/adelrib27/blogger-automation1/issues/54).
5. GitHub `main` atual, Actions, PRs e APIs de CMS/Cloudflare/Shopee antes de qualquer mutação; nenhuma fonte congelada substitui estado vivo.

## Inventário CMS / escopo editorial C144
**Blogger — seis destinos acessíveis na conta autenticada:**
- **4 já registrados como destinos editoriais V31:** Móveis para Cada Canto `1439741542627895062`; Limpeza Inteligente `7757953554206491487`; Estilo no Dia a Dia e Acessórios `4830103887652146866`; Cozinha Sem Complicação `3552757910439359679`.
- **1 BLOG CMS ATIVO, AINDA SEM ONBOARDING V31:** Vida Pet Prática `8052455848487624244` — não deletado, elegível a receber rota/campanha universal **após provas reais**, nunca por dedução da metodologia C69.
- **1 excluído do rollout editorial:** Ar-Condicionado sem Dúvidas `2228849984262880811`; ainda existente, não apagar sem comando específico.

**WordPress — 3 já roteados:** Casa e Decoração, Oficina & Garagem, Radar Tech BR.

**Conceitos de contagem:** 7 destinos editoriais V31 **já roteados** = 4 Blogger + 3 WordPress; **mais 1 blog ativo a integrar** (Vida Pet) = 5 Blogger não excluídos; Ar é o sexto Blogger acessível, excluído. São contagens atuais, não um limite de blogs. Os 24 excluídos anteriormente estão FORA deste conjunto e nunca voltarão à fila.

## Marco efetivo e resultados reais
- [Action de continuidade #45300690268](https://github.com/adelrib27/blogger-automation1/actions/runs/45300690268) **SUCCESS**: ponte de checkpoint, **não** E2E editorial.
- [C143 PR #146](https://github.com/adelrib27/blogger-automation1/pull/146) MERGED, 24 IDs apagados bloqueados, 18 cron removidos + 19 writers antigos `if:false`, [CI de 760 testes / 50 simulações](https://github.com/adelrib27/blogger-automation1/actions/runs/45300132547).
- [C144 PR #147](https://github.com/adelrib27/blogger-automation1/pull/147) **MERGED** no SHA `e81595124e93ac57c4461b0161c60def0cb8f1bd`: política, tombstones, validador, AGENTS e 8 testes novos corrigidos.
- [CI C144 #45301938515](https://github.com/adelrib27/blogger-automation1/actions/runs/45301938515) **SUCCESS: 768 testes, 50/50 simulações, Casa WP 24/24, Oficina WP 21/21, Radar WP 15/15, guard cross-blog PASS**; execução offline, sem writes externos.
- **CMS GET Blogger Móveis** post `4106024906916105222` confirmou `status=draft`; **WordPress Casa #321/#314 não foram reconfirmados** nesta sessão (connector retornou vazio), preservar sem duplicar. Colisão READY Casa WP `shopee:306698991:8503898928` x DRAFT #314 permanece bloqueada.
- **LAB #45300343177** falhou com `V31_SHOPEE_SAFE_BLOCKED`: sem oferta segura para `Cozinha / fatiador legumes`; houve erros de API Shopee GraphQL 10000. Ciclo transacional não executado; não inferir postagem nem retentar PUT cegamente.

## Continuidade C145 e gates não negociáveis
1. Tratar Vida Pet como blog Blogger real da carteira; conferir credencial/rota/campanha Shopee próprias antes de autorizar qualquer DRAFT. Nunca criar pet-only pipeline ou privilegiar pet; aplicar motor universal C69, SEO, fontes, SKU, imagem real, transparência e idempotência iguais aos demais.
2. Prosseguir com DRAFTs idempotentes somente em destinos corretamente integrados e após **50 simulações** por ciclo crítico, evidência factual independente, SKU e variante exatos, imagem real do CSV/R2, link afiliado convertido pela campanha do site, SEO e título originais, links internos LIVE verificados e recibo/GET CMS com hash. Um DRAFT por vez; não repetir posts existentes.
3. Investigar falha LAB Shopee separadamente, com quota e fail-closed; não forçar oferta inexistente.
4. Conservar `articles:null` = continuidade sem limite total de 3 artigos. `min_ready=3` = buffer simultâneo, não teto global.
5. Política `affiliate_hub_v31/autonomous_live_policy.json` segue `activation=pending_policy_approval`. **LIVE DESATIVADO até homologação real E2E e autorização final expressa**. Não misturar Pinterest, Mercado Livre, contas Cloudflare nem bancos experimentais.

**Procedimento:** conferir o GitHub vivo → registrar preview antes de nova etapa → branch isolada → CI/auditoria → merge somente verde → atualizar JSON/checkpoint/este índice. Não alterar os 24 tombstones, segredos, CMS ou R2/D1 sem prova e necessidade.

O arquivo `CHECKPOINT_ATUAL.md` pertence à rede Blogger legada e **não** substitui este índice V31.
