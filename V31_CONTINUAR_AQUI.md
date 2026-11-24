# V31 — CONTINUAR AQUI (fonte de verdade operacional única)

**Checkpoint vigente: C143 — 23/11/2026, America/Recife.**
**Código de retomada:** `V31-C143-20261123-DELETED-24-BLOGGER-4-ACTIVE-3-WP-19-WRITERS-BLOCKED-50-SIM-760-PASS-LIVE-OFF`

> **AVISO CRÍTICO DE CONTINUIDADE:** o proprietário **JÁ EXCLUIU OS 24 BLOGS BLOGGER HISTÓRICOS** que a C141 havia classificado incorretamente como pendentes de autenticação. **NUNCA tentar recuperá-los, reautenticá-los, registrar rota/campanha, atualizar Loja ou criar artigos para esses 24.** C102, C103, C141 e qualquer texto anterior que diga "28 Blogger candidatos", "24 pendentes" ou "oito rotas sem cadastro" são **história forense obsoleta**, NÃO tarefas ativas. Não reabrir esse trabalho em outro chat.

## Ordem obrigatória de leitura antes de qualquer trabalho

1. Este `V31_CONTINUAR_AQUI.md`.
2. [Estado atual limpo — `CONTINUIDADE_ESTADO.json`](affiliate_hub_v31/CONTINUIDADE_ESTADO.json). O JSON C143 substitui o estado histórico inchado; nele, `last_checkpoint_phase=C143`, `checkpoint_detail`, `active_work.next_safe_step`.
3. [Checkpoint técnico C143](affiliate_hub_v31/CHECKPOINT_C143_RETIRO_24_BLOGGER_APAGADOS_19_WORKFLOWS_760_TESTES_2026-11-23.md).
4. [Política de escopo atual](affiliate_hub_v31/EDITORIAL_ACTIVE_SCOPE_POLICY.json) e [lista mínima de negação dos 24 IDs apagados](affiliate_hub_v31/EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json). Arquivo [`EDITORIAL_GLOBAL_PORTFOLIO_C141.json`](affiliate_hub_v31/EDITORIAL_GLOBAL_PORTFOLIO_C141.json) está marcado `SUPERSEDED_DO_NOT_USE`; NÃO carregá-lo como fonte de destinos.

## Quem realmente entra na automação V31 agora

**Blogger — 4 destinos atuais, ambos conectores confirmaram os IDs em 23/11:**
- `blogger_moveis_para_cada_canto` — Móveis para Cada Canto — `1439741542627895062`.
- `blogger_limpeza` — Limpeza Inteligente — `7757953554206491487`.
- `blogger_estilo` — Estilo no Dia a Dia e Acessórios — `4830103887652146866`.
- `blogger_cozinha_sem_complicacao` — Cozinha Sem Complicação — `3552757910439359679`.

**WordPress — 3 destinos atuais:** Casa e Decoração, Oficina & Garagem, Radar Tech BR, conectores GET autenticados e rotas existentes.

**Exclusões:** Blogger `Ar-Condicionado sem Dúvidas` está acessível, mas explicitamente **EXCLUÍDO da expansão editorial**; o blog não foi apagado pelo V31. `Vida Pet Prática` é **somente referência de princípios de engenharia aplicados ao motor editorial universal**; NÃO projeto, blog-alvo ou writer independente do V31. Os **24 Blogger históricos foram APAGADOS pelo proprietário**, só continuam como tombstones (`allow_reenroll=false`) para impedir que código ou cron antigo os reutilize.

**Novos blogs futuros são PERMITIDOS** depois de prova de propriedade/atividade CMS, nova identidade que não esteja na lista de negação, campanha Shopee legítima e onboarding genérico. Sete é contagem **atual**, não teto do V31.

## Validação, segurança e resultados reais

- [PR #146](https://github.com/adelrib27/blogger-automation1/pull/146) **MERGED**: 15 rotas de Blogger apagado retiradas de `site_routes.json`, mais 1 arquivo em `sites.d`; `routing.py` impede reinserção por ID/chave; `site_launch_plan.py` e fila de requests fecham caminho.
- **18 workflows de Loja de Blogger apagado perderam `on.schedule` e receberam `jobs.if: false`**; um 19º writer manual também recebeu `if:false`. Auditor Blogger exige `V31_C143_OWNER_DELETED_JOB_DISABLED` em todos e falha se forem reativados sem revisão. Workflows atuais de Blogger/WordPress não foram desativados.
- [CI PR #146 #45300132547](https://github.com/adelrib27/blogger-automation1/actions/runs/45300132547) **SUCCESS: 760 testes e 50/50 SIMULAÇÕES** offline, testando os 24 IDs apagados em TODO ciclo; zero writes e `live_authorized=false`.
- [Auditoria C143 pós-merge #45300244527](https://github.com/adelrib27/blogger-automation1/actions/runs/45300244527) **SUCCESS**: 50 simulações, 18 testes específicos, 62 casos+contratos de segurança, Policy Guard 13/13, auditor de workflows PASS.
- [Auditoria de Políticas Blogger #45300244466](https://github.com/adelrib27/blogger-automation1/actions/runs/45300244466) **SUCCESS**, e [auditor C133 somente leitura #45300244463](https://github.com/adelrib27/blogger-automation1/actions/runs/45300244463) **SUCCESS**.
- Política `affiliate_hub_v31/autonomous_live_policy.json` mantém `activation=pending_policy_approval` — **LIVE V31 OFF** até homologação E2E e autorização final expressa.

## Próxima execução segura C144

Avançar **somente** com os quatro Blogger atuais e três WordPress, um DRAFT idempotente por vez após: 50 simulações por ciclo crítico, SKU real e variante exata, fonte independente/fabricante, foto real do CSV Shopee, afiliado convertido na campanha correta, SEO e título únicos, links internos válidos, aviso afiliado, orçamento diário e GET pós-gravação com hash. Não repetir posts já existentes.

**Colisões preservadas:** WordPress Casa READY `shopee:306698991:8503898928` conflita com DRAFT #314, **não consumir nem alterar**. DRAFTs verificados anteriormente: Blogger Móveis #4106024906916105222 e WordPress Casa #321. Os processos de publicação LIVE do V31 continuam BLOQUEADOS.

## Separação e histórico

O arquivo `CHECKPOINT_ATUAL.md` pertence à **rede Blogger legada**, NÃO governa este V31. Os antigos checkpoints C102/C141/C142 e os commits Git não foram reescritos ou destruídos; eles ficam como evidência do passado, explicitamente revogada **para seleção de blogs e retomada operacional**. Os workflows de Loja antigos dos blogs apagados foram desativados, sem tocar no Blogger CMS, D1/R2 ou Shopee. Pinterest e Mercado Livre são projetos separados.

**Não perguntar novamente pelo destino dos 24 históricos: o proprietário já confirmou sua exclusão.**
