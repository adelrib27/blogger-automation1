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

## Posição C165 (atual)

C164 confirmou DRAFT Radar #401 e replay. C165 introduz descoberta por modelo exato no catálogo elegível, seleção de fonte do fabricante e um canário em Ar-condicionado com possibilidade de uma conversão protegida pelo D1. Radar ainda em piloto e LIVE desativado. [Evidências e retomada C165](affiliate_hub_v31/CHECKPOINT_C165_MODELOS_FONTES.md).

## Posição C164

C163 confirmou histórico CMS, campanha/cache e ausência de jobs Radar. C164 corrige exclusões de filtros automotivos, prioriza categorias menos cobertas entre candidatos com o mesmo estado de cache e valida intervalo por perfil no D1. Um canário de Soundcore Select 4 Go testa DRAFT no Radar sem ativar cron do piloto ou LIVE. Consulte o [checkpoint C164](affiliate_hub_v31/CHECKPOINT_C164_CADENCIA_EDITORIAL.md) e confirme o recibo antes de repetir.

## Posição C162

C162: roteamento declarativo WordPress por site/taxonomia, Radar Tecnologia 3 e Ar-condicionado 20 parent3, sem Guias de Compra legado. Payload review v2 assina id/parent/slug/taxonomy_path; prepare e promotion recalculam pelo SKU no catálogo. Envelope v1 preservado para rotas sem mapa, v2 assinado e validado. Writer verifica configuração e ancestrais por GET antes da reserva, envia categories no POST, confirma GET e replay; writer direto bloqueado para rotas mapeadas. Workflow GET read-only após merge; 9 regressões novas (inclui adulteração, readback, replay, hierarquia). Sem ativar Radar, sem alterar CMS/cron/cotas/LIVE. CI e runtime GET pendentes. Distribuição inteligente e descoberta de novas categorias/fontes são próximas fases; novas rotas exigem mapeamento explícito verificado.

[Checkpoint C162](affiliate_hub_v31/CHECKPOINT_C162_CATEGORIAS_ASSINADAS.md).

## Posição C161

C161: proprietário define Radar Tech BR piloto prioritário E2E universal; integrar outros um por vez somente após comprovação. Preservar acervo comercial independente e operações já homologadas. Radar GET 37 publish, 19 draft, 0 future; categorias 1 Guias de Compra (arquivo), 3 Tecnologia, 20 Ar-condicionado parent 3. D1 Radar zero READY/USED; pedido editorial OFF, sem perfil; três tentativas históricas proibidas de repetição. C160 dry-run real 45829122530 PASS 7 campanhas/5 cache-only, 2 candidatos, zero mutação. Defeito universal WordPress: POST não envia categories e GET não verifica hierarquia. Corrigir roteamento declarativo, assinatura/binding e replay; fontes confiáveis e cap adaptativo após medições. Cron atual 4h, GitHub mínimo 5min sujeito a atraso; cap Shopee 3/dia não é cota oficial. LIVE OFF até aprovação expressa. Nenhuma alteração de código, flags ou CMS neste diagnóstico.

[Checkpoint C161](affiliate_hub_v31/CHECKPOINT_C161_RADAR_PILOTO_E2E.md).

## Posição C160

C160: cadastro comercial separado de enabled editorial por commercial_enabled opcional. Quatro demandas novas staged (Cozinha, Estilo, Limpeza, Oficina), Radar comercial true e editorial false; Móveis/Casa preservados. Sete campanhas na fila regular, cinco cache-only. Fallback comercial usa somente rota e SKU elegível/fonte segura/foto/URL oficial; D1 histórico por par campanha/SKU e reserva atômica preservados, cap global 3 e 2 por cron. Pilot/target permanecem editoriais. Auditoria C159 run 45697792398 D1/R2 PASS, CMS 6/7 (Oficina credencial GitHub ausente), 4 candidatos por rota. Run 45697192610 2 conversões verificadas. CI e novo dry-run R2 pendentes. Nenhum perfil factual inventado; Vida Pet não cadastrado; LIVE OFF.

[Checkpoint C160](affiliate_hub_v31/CHECKPOINT_C160_CADASTRO_COMERCIAL_INDEPENDENTE.md).

## Posição C159

C159: PR #168 mesclada c39eea8a48e27c66118ee2afbe161222d21acc3c. Cadastro: 7 rotas ativas, 2 pedidos/perfis habilitados, Radar staged disabled, quatro rotas sem pedido/perfil. Blogger API list confirma Móveis, Limpeza, Estilo, Cozinha, Vida Pet (ID 8052455848487624244, sem rota), Ar-Condicionado explicitamente excluído. Ampliação do diagnóstico C148 com --all-cms: uma restauração R2, contagem total de links armazenados por campanha (não prova de validade), amostras por site e GET CMS de todas as rotas, falhas isoladas, sem writes. Dois testes novos. CI e prova real pendentes; sem ativar sites.

[Checkpoint C159](affiliate_hub_v31/CHECKPOINT_C159_COBERTURA_UNIVERSAL.md).

## Posição C158

C158: entrega automática Blogger comprovada no run agendado 45639927141, DRAFT 5901505853451174265, GET CMS e HTML idêntico R2, D1 USED, replay sem duplicata. Manual 45678855827 SUCCESS/draft_daily_cap_reached, sem POST adicional. C157 merge a53464bfe29e3eb48bd464e5a3ca59925bcc1b1e, 930 testes e 50 simulações PASS. C156 biblioteca 286152 produtos, 53 links preservados. LIVE pending_policy_approval. Cobertura de todos os sites ainda não homologada.

[Checkpoint C158](affiliate_hub_v31/CHECKPOINT_C158_HOMOLOGACAO_DRAFT_AUTOMATICO.md).

## Posição C157

C157: run 45630060213 terminou SUCCESS sem entrega (NO_NEW_OFFER/research_budget_exhausted). READY Buriti continua no D1; HTTP e SEARCH 3/3. Recuperação assinada agora consulta READY frescos por tenant antes do ranking e pesquisa; valida escopo/catálogo/cache/foto, envelope e binding, histórico e cap. Adicionada sondagem READ_ONLY no catálogo R2 atualizado. CI/merge/prova real pendentes; não repetir refresh ou alterar cota. LIVE OFF.

[Checkpoint C157](affiliate_hub_v31/CHECKPOINT_C157_PRIORIDADE_READY.md).

## Posição C156

C156: catálogo recuperado em run 45626464263 SUCCESS, 286152 produtos (+82503), 53 links preservados, R2 CURRENT confirmado por GET (snapshot 25/11 13:48 UTC). Run Blogger 45627622648 recuperou mesmo READY e falhou em deliver-draft sem runner/logs; D1 READY, used_epoch null, sem lease confirmado depois. Encontrada dupla aquisição do mesmo grupo concurrency no workflow e job, hipótese forte de bloqueio de infraestrutura; removida só aquisição interna, trava global e D1 intactos. CI/merge e prova real pendentes; não rerun SHA anterior.

[Checkpoint C156](affiliate_hub_v31/CHECKPOINT_C156_LOCK_ENTREGA.md).

## Posição C155

C155: PR #164 mesclada, diagnóstico READ_ONLY #45624408248 aprovado em runtime real: READY e evidência fresca, assinatura/envelope/binding/identidade PASS, 12 posts completos, 0 colisões, 0 marcadores, 0 cota usada. Não repetir job sem logs; execução nova do scheduler atual via dispatch explícito. Refresh corrigido ainda não rodou na main. Oito workflows adicionais com suite completa receberam cryptography e teste preventivo; CI/merge desta correção pendentes. LIVE OFF.


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
