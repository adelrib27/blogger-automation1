# Regras para agentes — V31 Hub Editorial Shopee (Blogger & WordPress)

**PRIORIDADE ABSOLUTA C143 (23/11/2026):** o proprietário confirmou que os **24 blogs Blogger históricos** anteriormente descritos como "pendentes de autenticação" foram **DELETADOS POR ELE**. É proibido tratá-los como candidatos, buscar novas credenciais, reativar sites/Loja, tentar recuperação, gerar DRAFT, converter links ou publicar neles. Essas identidades só aparecem na lista mínima de negação [C143](affiliate_hub_v31/EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json) para evitar reintrodução.

O histórico C102/C141 que descrevia **28 Blogger candidatos e 24 pendentes** está **REVOGADO** para qualquer fluxo operacional. [Manifest C141](affiliate_hub_v31/EDITORIAL_GLOBAL_PORTFOLIO_C141.json) marcado `SUPERSEDED`. Commits e checkpoints antigos são evidência temporal, não tarefas a retomar. **NÃO usar `CHECKPOINT_ATUAL.md` para escolher blogs V31** — ele pertence à antiga rede Blogger e não autoriza ação em sites apagados.

## Ordem de leitura antes de alterar o V31

1. [`V31_CONTINUAR_AQUI.md`](V31_CONTINUAR_AQUI.md) — índice CANÔNICO C143.
2. [`CONTINUIDADE_ESTADO.json`](affiliate_hub_v31/CONTINUIDADE_ESTADO.json) — estado limpo (a versão anterior extensa foi substituída).
3. `checkpoint_detail` do JSON, atualmente [C143](affiliate_hub_v31/CHECKPOINT_C143_RETIRO_24_BLOGGER_APAGADOS_19_WORKFLOWS_760_TESTES_2026-11-23.md), e [política de escopo](affiliate_hub_v31/EDITORIAL_ACTIVE_SCOPE_POLICY.json).
4. Confirmar o estado LIVE `affiliate_hub_v31/autonomous_live_policy.json` antes de qualquer writer. `activation=pending_policy_approval`; jamais ativar sem homologação e autorização expressa final.

## Portfólio editorial atual

**4 Blogger:** Móveis para Cada Canto, Limpeza Inteligente, Estilo no Dia a Dia e Acessórios, Cozinha Sem Complicação. **3 WordPress:** Casa e Decoração, Oficina & Garagem, Radar Tech BR. **Mais 1 Blogger CMS ativo sem rota V31 homologada:** Vida Pet Prática (não confundir com a metodologia C69); não criar artigos antes de campanha/rota verificadas. Os nomes e IDs exatos estão na política C143. Esse número NÃO cria limite para futuros blogs genuinamente novos e autenticados.

`Ar-Condicionado sem Dúvidas` permanece EXCLUÍDO do V31 (não apagado pelo V31). **`Vida Pet Prática` é um blog Blogger REAL e ATIVO**, ID `8052455848487624244`, confirmado por API autenticada; o CMS não foi apagado nem é um mero exemplo conceitual. Ele está **aguardando onboarding V31 de rota/campanha**, portanto ainda NÃO tem writer V31 autorizado. Separadamente, **os princípios de engenharia derivados do estudo Vida Pet na C69** foram incorporados UNIVERSALMENTE ao motor V31, sem frente pet-only. Os 24 outros Blogger históricos estão deletados pelo proprietário, **não pendentes**.

## Segurança e execução

- Cada ciclo crítico de conversão/DRAFT deve executar **50 simulações offline** (suportar 10–50), e depois QA E2E real quando aplicável; PASS em simulação não é autorização para LIVE.
- Implementação universal por temas e campanhas reais: SKU/variante exatos, fotos oficiais CSV/R2, fontes independentes confiáveis, SEO original, links internos pertinentes, aviso de afiliados, CTA contextual e deduplicação global/por blog. Nunca inventar produto, comissão, preço, estoque, fonte ou link convertido.
- **18 workflows antigos de Loja dos blogs apagados não têm `schedule` e seus jobs usam `if:false`; um 19º writer manual também está bloqueado.** Nunca reintroduzir cron/job desses sites. O repo auditor Blogger faz validação fail-closed. Não confundir com workflows Blogger/WordPress dos sites atuais.
- Não alterar D1/R2/Shopee ou CMS sem verificar estado/limites, e nunca repetir POST/conversão por ausência de log. WordPress Casa READY com conflito DRAFT #314 permanece bloqueado; DRAFTs Móveis #4106024906916105222 e WP Casa #321 são registros legítimos existentes.
- Salvar preview antes de etapas longas, checkpoint, CI com regressões e relatório de evidência após mudanças; nunca afirmar sucesso remoto com base apenas em simulação.
- Pinterest e Mercado Livre são projetos separados; não misturar pipelines.
- Para sites Blogger genuinamente criados no futuro, exigir nova identidade CMS atual que NÃO esteja nos 24 tombstones e campanha verificada antes de registrar rota e perfil.

## Limites do histórico

O repositório retém commits antigos para auditoria; **não reescrever a história Git para encobrir o passado**. As referências antigas C102/C141/C142 e `CHECKPOINT_ATUAL.md` nunca sobrepõem a decisão C143 nem justificam ações nos blogs apagados. O projeto V31 não deve administrar a antiga rede Blogger legada sem uma demanda específica e verificações próprias.

**Continuidade segura:** um chat novo precisa ler os arquivos atuais da `main`; não inferir o estado por memória ou por um checkpoint histórico isolado.
