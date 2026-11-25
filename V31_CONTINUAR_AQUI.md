# V31 — Índice operacional

**Fonte mestre única:** [SYSTEM_MASTER.md](SYSTEM_MASTER.md).  
**Estado operacional legível por máquina:** [CONTINUIDADE_ESTADO.json](affiliate_hub_v31/CONTINUIDADE_ESTADO.json).  
**Repositório:** `adelrib27/blogger-automation1`, branch `main`.  
**Estado de publicação:** SAFE/DRAFT controlado. LIVE automático permanece desativado (`activation=pending_policy_approval`).

## Fonte de decisão

Leia `SYSTEM_MASTER.md` antes de qualquer execução. Em seguida, confira os arquivos de política, rotas e estado vivo do serviço envolvido. O conteúdo deste índice é apenas um atalho operacional; não substitui o documento mestre, a implementação ou os estados reais de R2, D1, Shopee e CMS.

## Portfólio habilitável

O motor universal possui **7 rotas editoriais cadastradas**: quatro Blogger (Móveis para Cada Canto, Limpeza Inteligente, Estilo no Dia a Dia e Acessórios, Cozinha Sem Complicação) e três WordPress (Casa e Decoração, Oficina & Garagem, Radar Tech BR). **Vida Pet Prática** é um blog Blogger ativo, identificado como `8052455848487624244`, mas depende de confirmação de rota e campanha V31 antes de receber DRAFT. **Ar-Condicionado sem Dúvidas** está fora do rollout.

Os **24 IDs indisponíveis** descritos em `affiliate_hub_v31/EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json` permanecem bloqueados. O sistema não tenta reativá-los nem recriar seus writers, crons ou campanhas.

## Posição C155 (atual)

C155: run 45542125840 tentativa 2 solicitada com sucesso via rerun job 138963418120; falhou novamente no novo job 139238956452, logs 404 e steps ausentes. RELEASE skipped. D1 permaneceu READY, sem lease/consumo, evidência fresca até 02/12 03:46 UTC, 0 tentativas DRAFT no dia. Não repetir terceira entrega. R2 CURRENT.json confirma snapshot 24/11 21:34 UTC; refresh novo não confirmado. Novo diagnóstico Blogger READ_ONLY em workflow próprio (sem cron, sem D1 writes ou POST CMS) para identificar estágio de D1, R2, assinatura, binding, identidade, marcador e colisão usando credenciais do mesmo runtime; trigger somente mudança do próprio arquivo na main ou dispatch. PR e CI pendentes.

[Checkpoint C155](affiliate_hub_v31/CHECKPOINT_C155_ENTREGA_RECUPERACAO.md).

## Posição C154

C154: PR #162 mesclada (f0b5b18872a0a5a800e2f1da90c402020a163181), CI 45620945094 PASS 922 testes. Envelope READY Móveis recuperado do R2; SHA HTML e Ed25519 verificados contra âncora do verificador; 12 artigos sem marcador ou shortlink idêntico. Entrega ainda não autorizada por este diagnóstico: histórico agendado, estado atual e falha 404 do job precisam conciliação. Refresh corrigido, nova execução real pendente.


C154 — PR #162: correção de dependência cryptography em cinco workflows; aguarda CI/merge e execução real do refresh. C153 runtime confirmado: 2 links convertidos e persistidos, run 45492088943. Casa #334 confirmado em DRAFT por CMS; hash envelope não verificado. Móveis READY shopee:1235923910:19299550912 sem consumo no D1, 7 drafts + 5 publicados sem ID literal; log deliver-draft indisponível (404). Não repetir POST até reconciliação. LIVE OFF, sem alterar cron.

[Checkpoint C154](affiliate_hub_v31/CHECKPOINT_C154_RECUPERACAO_AUTOMACOES.md).

## Posição C153

C153: fila comercial regular não depende de fonte factual, template ou revisão de artigo. Perfil factual é prioridade opcional, não veto. Mantêm-se moderação, origem, campanha real, escopo, cache, reserva D1 na fila diária e single writer; a recuperação pontual editorial continua restrita. LIVE e flags de DRAFT inalterados. PR #160 mesclada em 60db4b0eda1c216a6ed34e028d5e264d904807ef; CI 45448688104: 922 testes e 50 simulações PASS. Sem nova conversão real confirmada; dispatch indisponível no conector GitHub atual. A próxima execução regular deve ser auditada antes de qualquer retry.

[Checkpoint C153](affiliate_hub_v31/CHECKPOINT_C153_CONVERSAO_INDEPENDENTE.md).

## Posição C152 SAFE (24/11/2026)

- Checkpoint assinado no GitHub: [C152 — auditoria legada e guarda universal](affiliate_hub_v31/CHECKPOINT_C152_AUDITORIA_LEGADA_SAFE_2026-11-24.md). Prévia anterior à mudança: [C152 PREVIEW](affiliate_hub_v31/CHECKPOINT_C152_PREVIEW_AUDITORIA_LEGADA_2026-11-24.md).
- Radar Tech BR **56 artigos existentes** (37 publicados + 19 drafts) com histórico RAW autenticado conferido. Quatro produtos C151 ainda não homologados; **nenhum DRAFT novo**.
- PR [#159](https://github.com/adelrib27/blogger-automation1/pull/159): guarda `legacy_cms_collision.py` e integração nos writers Blogger/WordPress revisado e direto. SAFE CI [#45446503885](https://github.com/adelrib27/blogger-automation1/actions/runs/45446503885): **922/922** testes, **50/50** simulações, regressões WordPress PASS. Validar CI mais recente antes de qualquer merge.
- Radar request continua desativado; LIVE `pending_policy_approval`. Próxima obrigação é verificar oferta real, fabricante, campanha/cache e D1/R2 atuais, sem reativar cron ou repetir conversão.

## Próxima operação segura

1. Confirmar a `main` e os workflows recentes, verificando novos commits antes de mutações.
2. Confirmar a identidade, campanha, SKU, imagem, fontes independentes, SEO e duplicidade de cada candidato.
3. Rodar 50 simulações offline por ciclo crítico; em DRAFT real, confirmar ID/status/hash por GET autenticado.
4. Reconciliar colisões READY/CMS sem repetir POST; diagnosticar indisponibilidade Shopee sem forçar ofertas.
5. Manter o limite diário por site, o catálogo cumulativo, o escopo exclusivo Blogger/WordPress e LIVE desativado até autorização expressa.

**Preservação:** o mecanismo de continuidade mantém o estado atual no JSON e um checkpoint técnico verificável enquanto necessário. Arquivos de relatório desnecessários não determinam autorização operacional. Consulte `SYSTEM_MASTER.md` para o contrato completo.
