# C10 — Runbook de liberação, rollback e expansão V31 (16/11/2026)

**Estado:** preparação final em **PR #52 DRAFT**. Não há merge nem ativação LIVE nesta etapa.
**Código de continuidade:** `V31-EDITORIAL-C10-CANARY-READY-BUT-OFF-20261116`

## Arquitetura final (não criar outro publicador)

Os três WordPress já possuem automações completas de artigos e SEO. O V31 é a **fonte de oportunidades** que cada automação pode consultar:
1. API Shopee funciona → usar a oportunidade normal já qualificada;
2. API retorna erro 1000 → interromper consultas repetidas e restaurar catálogo CSV/R2;
3. selecionar apenas produto aprovado, keyword pertinente, imagem por URL original Shopee, link afiliado REAL já convertido para a campanha do blog;
4. validar estoque e formato da fila; se faltar o mínimo, parar o trabalho sem publicar item inconsistente;
5. manter gerador, segurança editorial, horários e publicador existentes;
6. incrementar cadastro de outros Blogger/WordPress em `sites.d/` e `shadow.d/`; escalar a descoberta compartilhada, não duplicar o motor.

## Duplo interruptor com valores OFF por padrão

GitHub **Repository variables**, não Secrets; se ausentes, tratam-se como desligadas:

| Variável | Estado requerido antes do primeiro merge | Finalidade |
|---|---|---|
| `V31_EDITORIAL_C9_RELEASE_ENABLED` | **ausente / false** | Interruptor global: desliga o fallback de todos os blogs |
| `V31_CASA_R2_FALLBACK_ENABLED` | **ausente / false** | Opt-in apenas do Casa e Decoração |
| `V31_OFICINA_R2_FALLBACK_ENABLED` | **ausente / false** | Opt-in apenas do Oficina & Garagem |
| `V31_RADAR_R2_FALLBACK_ENABLED` | **ausente / false** | Opt-in apenas da fila diária Radar |
| `V31_EDITORIAL_SHADOW_ENABLED` | **ausente / false** | Cron da auditoria de cache (sem publicação) |
| `V31_EDITORIAL_CACHE_WARMUP_ENABLED` | **ausente / false** | Cron de pré-conversão de links (sem publicação) |

**Ambos, GLOBAL e POR SITE, precisam estar true para um blog trocar de descoberta.** Quando apenas uma chave estiver false ou ausente, a rotina de descoberta antiga fica ativa. Os três jobs originais continuaram com SEO, geração, qualidade, publicação e horários iguais aos de `main`.

## Gates de canário de release, em ordem

**G0 — Revisão e integridade:** revisar diff do PR e Actions (CI verde), registrar SHA, confirmar que as flags globais e individuais estão OFF, revisar políticas de acesso ao Environment e execução manual. Nenhum merge automático neste projeto. Publicadores antigos são afetados somente se o PR for mesclado, mas o default OFF preserva o fluxo antigo.

**G1 — Capacidade de fallback:** executar `v31_c8_shadow_safe.yml` manualmente; conferir produtos/links válidos por campanha, origem Shopee e estoque suficiente. Metas de conforto de **três dias** conforme agendamentos existentes: Casa >=9, Oficina >=6, Radar >=15, com 5 categorias/lojas/keywords para Radar. A conclusão de 5 slots em C9 é necessária, mas ainda NÃO satisfaz o estoque de 15.

**G2 — Reposição controlada:** executar `v31_c8_cache_replenish_safe.yml` somente com confirmação explícita, inicialmente orçamento 1–3 mutations globais/run; inspecionar `api_interrupted`, `retention_pending`, integridade do snapshot R2 e contagens. Lote diário de 3 links é **bootstrap conservador**, NÃO a capacidade definitiva de 50+ blogs: aumentar orçamento/cron somente depois de medir cotas Shopee, erros 1000, custo e consumo real. Nunca deixar o gerador tentar converter link inédito enquanto a API está indisponível.

**G3 — Canário em modo não publicável:** executar provas equivalentes às do C9, com erro 1000 SIMULADO e catálogo R2 REAL, sem credenciais WordPress; comparar saída do scanner com o contrato da fila original, nomeadamente Casa/Oficina (v2.3) e Radar (5 categorias/5 lojas). Um erro deve produzir status FAILED e **nenhum** artefato ou item publicável.

**G4 — SEO e originalidade:** o mesmo produto PODE aparecer em artigos diferentes, mas NÃO título, assunto, intenção ou corpo muito semelhantes. A integração C10 acrescentou ao **Casa, exclusivamente no caminho fallback habilitado**, o gate cross-blog de título/corpo que já existe em Oficina e Radar. Ele bloqueia colisões de conteúdo, mas as filas legadas ainda vetam **produto repetido** indiscriminadamente. Antes de alterar esse controle em produção, criar reserva de pautas transacional por blog/rede, validar keywords e comparar título/corpo com histórico; não desativar gates por produto sem substituição adequada. Garantir alegações comerciais apenas com dados verificáveis e imagens por URLs originais (sem guardar imagens no R2).

**G5 — Liberação por blog somente quando aprovada:** habilitar GLOBAL e então APENAS UMA flag de site (começar Casa, depois Oficina, depois Radar), observar o primeiro ciclo, erros API, inventário, artigos e duplicidade. A liberação da flag ativa a rotina comercial já existente, que poderá publicar na Internet no horário programado; NÃO efetuar enquanto não houver revisão dos gates de conteúdo e de produto.

**G6 — Rollback imediato:** colocar `V31_EDITORIAL_C9_RELEASE_ENABLED=false` para reverter **toda a rede**, ou desativar a flag específica para um blog. Isso afeta **próximas execuções**, não desfaz posts já publicados e não cancela jobs em andamento: cancelar manualmente o run em curso no GitHub Actions se necessário. Manter os arquivos e snapshots R2 íntegros para auditoria, sem sobrescrever histórico editorial.

## Estado real em 16/11/2026

- Catálogo R2 real: **109.507 produtos** / **4.674 elegíveis** / **11 links afiliados reais cacheados** no último diagnóstico.
- Casa: **2 links utilizáveis**, meta 9; Oficina: **2**, meta 6; Radar: **6**, meta 15 (já passou na prova real de uma fila completa de 5 slots com 5 lojas).
- Inventário de blogs cadastrado: **21** (18 Blogger + 3 WordPress) sem teto codificado de sites, mas apenas **três perfis de shadow**. Meta 50+ depende de cadastros/domínios/IDs de verdade, credenciais por site e consumidores/callers do workflow.
- Faltam candidatos em duas categorias específicas sob filtros atuais: `Cama Mesa Banho` (Casa) e `Seguranca e Protecao` (Oficina); não inventar produtos ou ignorar bloqueios.
- [Evidência C9 Radar E2E](https://github.com/adelrib27/blogger-automation1/actions/runs/43894779041): scanner ORIGINAL + erro 1000 SIMULADO + R2 REAL + fila original completa + 114/114 testes; nenhum post.
- [Checkpoint C9](CHECKPOINT_C9_3WP_R2_2026-11-16.md).

**Nenhum workflow foi liberado ou agendado LIVE por este runbook.** Esta é a especificação de implantação reversível a ser aplicada após revisão.


## Hipótese para etapa POSTERIOR — tráfego Shopee das páginas de loja

**Decisão do usuário, registrada em 16/11/2026:** todos os blogs mantêm páginas de loja com atualização/rotação **diária** de produtos, possivelmente em horários distintos. Essas chamadas, somadas às buscas das automações editoriais (incluindo várias categorias e slots do Radar Tech BR), podem concentrar requisições na mesma API/credenciais e contribuir para a frequência de respostas Shopee `1000`.

**É uma hipótese, NÃO uma causa comprovada.** Não equiparar automaticamente o erro `1000` ao `10030`, mesmo que o volume, horários e tempos de espera possam influenciar ambos. A documentação de um actor de terceiros (Apify) não prova a causa de `1000` nem estabelece uma cota oficial.

**Proposta para análise futura, somente depois de concluir V31:** medir requisições reais e janelas de execução por blog, incluindo lojas, artigos, slots, testes e demais consumidores; avaliar substituir a atualização diária de cada página de loja por **uma rotação mensal distribuída entre os blogs**, mantendo as lojas ativas, a validade dos produtos e as URLs afiliadas.

**Fora do escopo desta entrega:** não alterar agendas, cadência, scripts ou consultas das páginas de loja; não implementar por enquanto backoff indiscriminado, proxy ou roteamento baseado na suposição de que `1000` e `10030` são equivalentes.

**Prioridade atual:** concluir o fallback CSV/R2, originalidade editorial, estoque por campanha, validação dos workflows existentes e rollout seguro; **depois** estudar a carga das lojas.
