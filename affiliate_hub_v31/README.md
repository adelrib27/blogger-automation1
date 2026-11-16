# V31 Hub Editorial Shopee — Blogger & WordPress

## Escopo canônico (15/11/2026)

Este projeto opera **exclusivamente para blogs Blogger e WordPress**. Pinterest e redes sociais têm projetos separados e **não fazem parte** deste módulo.

Repositório: `adelrib27/blogger-automation1`. A implantação reside em uma branch isolada. Nenhuma automação de produção foi modificada.

### Secrets e variáveis do Hub (centralizado)

**Registro oficial de nomes e instruções:** [SECRETS.md](SECRETS.md)  
**Manifesto legível por máquina:** [credentials_registry.json](credentials_registry.json)  
**Verificação sem revelar valores:** `python -m affiliate_hub_v31.credentials --profile manifest`  
**Workflow manual SAFE:** `.github/workflows/v31_editorial_secret_inventory_safe.yml` (disponível para execução manual após inclusão na branch padrão).

Namespace isolado: `V31_EDITORIAL_...`. Nenhuma credencial real é versionada aqui, e os workflows comerciais existentes permanecem intactos. **Status atualizado:** Secrets e Variables no GitHub Environment `v31-editorial-safe` foram cadastrados e validados pelos testes reais do R2; consulte os checkpoints C3.2 e C4/C5.

### C11/C12 — Reuso editorial sem repetição de título nem corpo (16/11/2026)

- **Recurso opt-in e desativado por padrão**: além de `V31_EDITORIAL_C9_RELEASE_ENABLED` e da flag de cada blog, exige `V31_EDITORIAL_PRODUCT_REUSE_ENABLED=true`. Reutilizar o produto NÃO equivale a repetir a matéria.
- `reuse_policy.py`: limite-piloto de 2 artigos por produto no mesmo blog, checagem de histórico/tema/título e, na C12, comparação do **editorial_html** contra os arquivos antigos do mesmo produto e título publicado. Se faltar documento histórico, **bloquear antes do WordPress**.
- Integrado apenas aos scripts existentes de **Casa e Oficina** (construtor de fila, Qwen3, publisher), sem novos geradores; todos os controles legados continuam quando as flags estão OFF. O Radar conserva os critérios próprios até canário específico.
- [QA C11 real dos scripts originais](https://github.com/adelrib27/blogger-automation1/actions/runs/43910337180): **125 testes V31 + 24 Casa + 21 Oficina + cross-blog PASS**, sem publicação.
- [QA C12](https://github.com/adelrib27/blogger-automation1/actions/runs/43911094183): **126/126 testes V31 PASS**, incluindo corpo igual/corpo realmente diferente/ausência de histórico. Código da etapa ainda não mesclado, nenhum post LIVE alterado.
- [Checkpoint C11](CHECKPOINT_C11_EDITORIAL_REUSE_SAFE_2026-11-16.md) e [Checkpoint C12](CHECKPOINT_C12_BODY_ORIGINALITY_SAFE_2026-11-16.md). Próxima liberação depende de **estoque suficiente + histórico real + canário não publicável**.
- **Hipótese futura registrada no Runbook C10:** as páginas de loja de todos os blogs fazem rotação diária e podem estar concentrando chamadas com os agendamentos editoriais; depois de concluir V31, medir consumo e avaliar rotação mensal distribuída. **Nada alterado nas lojas agora.**

### C10 — Liberação futura protegida por dois switches (16/11/2026)

- **Novo interruptor global** `V31_EDITORIAL_C9_RELEASE_ENABLED` em conjunto com a flag de **cada blog**. **Ambos OFF/ausentes** => automações antigas continuam sem o roteador.
- Somente após revisão do PR, auditoria de estoque, teste canário sem publicação e validação de originalidade por **pauta/título** será possível habilitar a execução comercial por blog. O antigo publicador poderá publicar posts ao ativar as flags; **NÃO ativar sem critérios cumpridos**.
- **Rollback:** desabilitar a flag global para toda a rede ou a flag específica; cancelar manualmente runs já iniciados. Sem merge automático.
- [Runbook operacional C10](C10_RELEASE_RUNBOOK_2026-11-16.md), código `V31-EDITORIAL-C10-CANARY-READY-BUT-OFF-20261116`.

### C9 — Ponte reversível API→R2 para 3 WordPress; 5 slots Radar REAIS (16/11/2026)

- **Não substitui publicadores**: adiciona um workflow de descoberta reutilizável `v31_c9_discovery_reusable.yml` (somente API Shopee/R2, sem secrets WordPress) e integra por flags **OFF por padrão** os trabalhos já existentes de Casa, Oficina e fila diária Radar, somente na **branch do PR #52**. O branch `main` continua intocado.
- **Rollback por blog:** `V31_CASA_R2_FALLBACK_ENABLED`, `V31_OFICINA_R2_FALLBACK_ENABLED`, `V31_RADAR_R2_FALLBACK_ENABLED`: ausente/`false` => scanner antigo; `true` => workflow compartilhado. Falha do novo job não libera o publicador.
- **Fallback insuficiente bloqueado:** `--min-fallback` exige ao menos 3, 2 e 5 links válidos respectivamente; não interfere na prioridade da API Shopee quando ela funciona.
- **Radar preservado:** `radar_legacy_adapter.py` usa o seletor ORIGINAL de 5 categorias, 5 lojas e 5 keywords. `fallback_v23.py` passou a carregar `shopId` e até 3 lojas alternativas por keyword.
- **Catálogo real/Radar:** [run 43894290446](https://github.com/adelrib27/blogger-automation1/actions/runs/43894290446) PASS — corrigiu conflito de loja com **1 link Shopee REAL**, montou fila Radar completa em diretório temporário. [run 43894779041](https://github.com/adelrib27/blogger-automation1/actions/runs/43894779041) PASS — **scanner Radar original + erro 1000 simulado + R2 REAL + fila 5/5**, **114/114 testes offline** e zero publicações.
- **Inventário:** [run 43892555790](https://github.com/adelrib27/blogger-automation1/actions/runs/43892555790), **113/113 testes**, Radar com oferta CSV nas 5 categorias. Casa: `Cama Mesa Banho` sem elegíveis; Oficina: `Seguranca e Protecao` sem elegíveis sob regras atuais, sem inventar produtos para completar.
- Cache R2 atual: **Casa 2/9**, **Oficina 2/6**, **Radar 6/15** (cinco categorias cobertas), **Blogger Air Fryers 1**; **11 links** no total. Ainda insuficiente para a meta de 3 dias; todos `NOT_READY` no shadow. O sistema NÃO foi mesclado nem ativado em produção.
- **Checkpoint:** [C9 — ponte 3WP + Radar completo](CHECKPOINT_C9_3WP_R2_2026-11-16.md), `V31-EDITORIAL-C9-3WP-API1000-R2-FULL-QUEUE-SAFE-20261116`.
- **Próximo gate C10:** revisão/rollout canário por blog, estoque por campanha, reconciliação e originalidade de assunto/título. Nunca desativar dedup de conteúdo por causa da autorização de reutilizar produtos.

### C8 — Shadow read-only e cache multi-site com orçamento (16/11/2026)

- **Observação REAL do R2:** [run 43886181941](https://github.com/adelrib27/blogger-automation1/actions/runs/43886181941), **PASS** (94 testes); `shadow_audit.py` compara links utilizáveis com reservas de 3 dias, com perfis expansíveis em `shadow.d/*.json`.
- **Reposição REAL controlada:** [run 43887349902](https://github.com/adelrib27/blogger-automation1/actions/runs/43887349902), **PASS** (101 testes): **3 mutations / 3 links novos**, um por campanha WordPress, único snapshot R2, restauração validada, nenhum artigo/publicação.
- **Estado atual:** Casa **2/9**, Oficina **2/6**, Radar **2/15** links utilizáveis. No Radar, **2/5 categorias** obrigatórias cobertas. Todos `NOT_READY` para uso automático LIVE.
- `cache_replenish.py`: rodízio de campanhas, máxima global de **3 tentativas por execução**; prioriza categorias ainda sem link. `--execute` explicitamente necessário para mutations; sem isso a operação é dry-run. **NUNCA publica**.
- Novos workflows `v31_c8_shadow_safe.yml` e `v31_c8_cache_replenish_safe.yml`: em `main` somente após PR revisado, schedules protegidos por `V31_EDITORIAL_SHADOW_ENABLED` e `V31_EDITORIAL_CACHE_WARMUP_ENABLED` (ambos **desligados por padrão**), manual com confirmação para conversão.
- Workflows temporários de teste removidos, **workflows comerciais antigos intocados**.
- [Checkpoint C8](CHECKPOINT_C8_SHADOW_REPLENISH_2026-11-16.md), código `V31-EDITORIAL-C8-SHADOW-REPLENISH-REAL-PASS-20261116`. Próxima etapa: integração por blog com rollback, expansão de cache e fila Radar completa.

### C7 — R2 REAL integrado às filas dos três WordPress (16/11/2026)

- **Casa e Decoração:** [run 43878643279](https://github.com/adelrib27/blogger-automation1/actions/runs/43878643279) PASS. Uma conversão Shopee REAL (`casaedecoracaowp`), cache R2, construtor de fila original validado sem publicação.
- **Oficina & Garagem:** [run 43879142065](https://github.com/adelrib27/blogger-automation1/actions/runs/43879142065) PASS. Uma conversão Shopee REAL (`oficinawp`), cache R2, construtor original validado sem publicação.
- **Erro 1000:** [run 43879995986](https://github.com/adelrib27/blogger-automation1/actions/runs/43879995986) PASS com erro 1000 **simulado** nos scanners originais e recuperação de ofertas do R2 **real**; circuito interrompe novas chamadas no primeiro erro.
- **Radar Tech BR:** [run 43880690866](https://github.com/adelrib27/blogger-automation1/actions/runs/43880690866) PASS. Uma conversão Shopee REAL (`radarwp`) e validação de **um slot** no `prepare_slot.py` original; **fila de 5 categorias ainda não validada**.
- **89/89 testes SAFE aprovados**, sem publicar artigos ou modificar workflows LIVE. Gatilhos temporários removidos. Estoque de apenas **1 link afiliado por campanha** ainda é insuficiente para rotina diária de 50 blogs.
- [Checkpoint C7 completo](CHECKPOINT_C7_REAL_3WP_2026-11-16.md), continuidade: `V31-EDITORIAL-C7-R2-3WP-FALLBACK-SAFE-20261116`.
- Próximo passo C8: pré-conversão de lotes com limites/cotas e teste em shadow mode dos fluxos existentes, migrando controles de repetição de produto para originalidade de pauta/título.

### C6 — Fallback CSV/R2 universal para blogs atuais e futuros (16/11/2026)

- **Objetivo corrigido:** os três WordPress existentes **já possuem geração de artigos**. O V31 fornece produtos: **API Shopee primeiro; erro 1000 confirmado sem ofertas úteis → CSV/R2**; sem modificar os publicadores.
- [Cadastro extensível de blogs](sites.d/README.md): inclui `site_routes.json` e registros independentes em `sites.d/*.json`. Atualmente **18 Blogger e 3 WordPress**, com suporte a novos sites sem alterar o motor; teste com **60 blogs fictícios adicionais**.
- [fallback_v23.py](fallback_v23.py): usa somente links de afiliado já convertidos na campanha de cada site; gera `ranking.json`, `intent_report.json`, CSV e relatórios compatíveis com as filas v2.3, sem inventar métricas comerciais.
- [opportunity_router.py](opportunity_router.py): mantém o scanner antigo, observa código 1000, usa fallback quando necessário e só entrega artefatos completos. Outros erros bloqueiam a rotina.
- **86 testes offline aprovados**, incluindo simulação do scanner real de Casa e Decoração com erro 1000. **Nenhum workflow de publicação LIVE foi alterado e o fallback REAL ainda não foi acionado nos blogs.**
- **Próximo requisito:** pré-conversão de links por campanha enquanto a API estiver saudável, teste de compatibilidade das filas e adaptador adicional para Radar (fila por slots).
- [Checkpoint C6 multisite](CHECKPOINT_C6_UNIVERSAL_FALLBACK_2026-11-16.md). Continuidade: `V31-EDITORIAL-C6-UNIVERSAL-FALLBACK-20261116-SAFE`.

### C4/C5 — Pilotos REAIS: conversão e originalidade de pautas

- **C4** [run 43771181969](https://github.com/adelrib27/blogger-automation1/actions/runs/43771181969): uma conversão `generateShortLink` real aprovada, link salvo no R2 e cache reutilizado sem nova API; restauração validada.
- **C5** [run 43771386845](https://github.com/adelrib27/blogger-automation1/actions/runs/43771386845): o **mesmo produto real** usado em **dois blogs Blogger**, com dois títulos/ângulos diferentes mantendo `air fryer`; ambos em `REVIEW_REQUIRED`, sem artigo/publicação.
- R2 restringe snapshots ao **atual + anterior**, e limpeza na execução real completada sem pendência.
- Todos os workflows transitórios de teste foram removidos após sucesso.
- **Checkpoint:** [C4/C5 — conversão real e pautas originais](CHECKPOINT_C4_C5_2026-11-15.md), código `V31-EDITORIAL-C5-ORIGINALIDADE-REAL-PASS-20261115`.
- Ainda faltam: publicar **rascunhos reais** nas plataformas, revisar textos completos e regras de agendamento/ativação gradual; credenciais LIVE e rotação da App Secret exposta precisam ser verificadas.

### C3 — Cloudflare R2 privado criado e verificado

- **Bucket existente:** `v31-editorial-shopee`, na conta selecionada pelo proprietário, classe **Standard**, sem domínio público `r2.dev` ou domínio personalizado.
- **Comprovado:** ativação da assinatura no painel e criação/consulta pela API Cloudflare. **Marco histórico C3:** naquele momento ainda não havia objetos; o primeiro catálogo real foi gravado e restaurado posteriormente em C3.2.
- **Pendente:** criar credenciais S3 limitadas ao bucket e cadastrá-las no Environment GitHub `v31-editorial-safe`, configurar `V31_EDITORIAL_R2_ACCOUNT_ID` e `V31_EDITORIAL_R2_BUCKET`; validar conexão real e só então importar os feeds.
- **Checkpoint:** [C3 — bucket privado criado](CHECKPOINT_C3_R2_2026-11-15.md).
- **Continuidade:** `V31-EDITORIAL-C3-R2-PRIVATE-20261115-CREATED`.

### C2.1 — Dois feeds REAIS auditados em GitHub Actions

- **Prova:** [run 43732094595](https://github.com/adelrib27/blogger-automation1/actions/runs/43732094595), `V31_C2_REAL_FEEDS_PASS`. Foram lidos **100.000 + 10.000 registros**, com cabeçalhos de **24 e 16 colunas**.
- **493 duplicações preliminares** e **109.507 chaves diferentes** pelo deduplicador atual. Os feeds não possuem coluna reconhecida de `shopId`; revisar identificadores alternativos antes de tratar essas chaves como produtos comerciais distintos.
- **4.758 registros** corresponderam a nichos na versão inicial da taxonomia, **105.242 ainda sem nicho aprovado**. Não significa descarte definitivo.
- Bugs reais resolvidos: redirecionamento HTTPS interno Shopee e CSV com campos multilinha/aspas. O workflow temporário de auditoria foi removido; dados não foram persistidos.
- **Checkpoint C2.1:** [leitura real, limitações e próximos passos](CHECKPOINT_C2_1_FEEDS_REAIS_2026-11-15.md). Código: `V31-EDITORIAL-C2.1-FEEDS-REAIS-20261115-PASS`.
- **Marco histórico C2.1:** R2 e conversão comercial foram posteriormente validados em C3.2 e C4; a publicação automática nova permanece desativada.

### C2 — Categorias, nichos, feeds e R2 SAFE

**Checkpoint de continuidade:** [C2-2026-11-15](CHECKPOINT_C2_2026-11-15.md)  
**Código:** `V31-EDITORIAL-C2-TAXONOMIA-R2-20261115-SAFE`

- Taxonomia de **20 nichos/15 categorias** em [taxonomy.json](taxonomy.json), com bloqueio de desconhecidos, acessórios e ambiguidades antes da conversão.
- [site_routes.json](site_routes.json): rotas de seleção para **18 blogs Blogger** e **2 WordPress** verificadas no repositório; todas com `publish_enabled=false`.
- [converter.py](converter.py): cliente `generateShortLink` sob demanda, cache por campanha, verificação de domínio e rechecagem após conversão; mutation testada **somente com mocks**.
- [ingest.py](ingest.py): importação de dois CSVs de forma atômica em banco local; [r2_state.py](r2_state.py) versiona backups privados. [ingest_cli.py](ingest_cli.py) pode ser executado na nuvem quando os secrets dos feeds e storage estiverem disponíveis.
- [workflow de importação SAFE](../.github/workflows/v31_editorial_ingest_r2_safe.yml): **manual, apenas main, sem schedule e sem publicação**.
- **Validação C2:** 45/45 testes offline aprovados. Benchmark isolado com 110.000 linhas **sintéticas** passou em 18,41 s no GitHub Actions [run 43728505370](https://github.com/adelrib27/blogger-automation1/actions/runs/43728505370); 105.000 produtos únicos e 5.000 duplicatas planejadas. Isso **não comprova** comportamento ou esquema dos feeds reais. O gatilho temporário de benchmark foi removido.

**Ainda não executados:** download real dos feeds, provisionamento/acesso real ao R2, conversão real `generateShortLink`, publicação Blogger/WordPress. Nenhum serviço LIVE foi alterado. É obrigatória a rotação da chave Shopee anteriormente exposta.

### Objetivo

1. Receber os dois feeds CSV da Shopee em área privada de armazenamento. A contagem histórica relatada é de 100.000 + 10.000 linhas **antes** da deduplicação; esta branch ainda não baixou os arquivos atuais.
2. Importar, normalizar, deduplicar e classificar produtos para revisão editorial antes de publicar.
3. Reutilizar links afiliados já validados por produto/campanha. Para links faltantes, chamar a Shopee Affiliate Open API com autenticação assinada, limites e registro de tentativas.
4. Expor candidatos a adaptadores separados: **Blogger** e **WordPress**, preservando IDs, filtros, HTML comercial e política de cada site.
5. Agendar rotinas de ingestão e publicação na nuvem somente após testes e aprovação do fluxo LIVE.

### Limites de segurança

- Feeds privados, App Secret, tokens, arquivos de catálogo e métricas comerciais não entram no repositório público nem nos logs.
- Github Actions não oferece disco persistente entre execuções: é necessário provisionar backup/estado persistente privado antes de executar de verdade (p.ex. R2 ou banco gerenciado).
- Nunca concluir que URL de produto tem atribuição de afiliado: armazenar somente retorno validado da API ou importação legada verificada.
- Nenhuma integração com Pinterest. Não apagar fluxos Pinterest preexistentes de outros projetos.
- Modo padrão: **SAFE**, sem publicar, sem editar posts, sem ativar schedules e sem emitir links em massa.
- Live Blogger e WordPress exigirão validadores próprios, idempotência, fila de revisão, proteção contra duplicados e opção de rollback.
- Link Shopee pode expirar/mudar; revisão de validade deve preceder publicação.
- Política editorial: não publicar indiscriminadamente produtos não revisados, alegações não confirmadas ou páginas duplicadas.

### O que existe nesta etapa

- `affiliate_hub_v31/catalog.py`: banco SQLite local e importador CSV, deduplicação, revisão básica, cache por campanha, consultas.
- `affiliate_hub_v31/__init__.py`: pacote Python.
- **C1:** 20 testes offline aprovados, e a autenticação Shopee real passou em uma consulta somente leitura; veja C1.3. **C2:** módulo de importação, classificação, conversão por demanda e persistência R2 preparado e coberto por testes offline. Falta cadastrar credenciais de feeds/R2, comprovar o esquema CSV real, testar a mutation de conversão real, conectar os adaptadores e agendar a publicação após aprovação.

### Marco C1.3 — Autenticação Shopee real (15/11/2026)

- **PASS real:** GitHub Actions [execução 43725343531](https://github.com/adelrib27/blogger-automation1/actions/runs/43725343531), saída sanitizada `V31_SHOPEE_API_PASS`.
- **Escopo exato:** consulta `productOfferV2` assinada com credenciais do GitHub Environment `v31-editorial-safe`, solicitando apenas 1 produto; sem publicar, sem converter, sem baixar CSV e sem expor respostas.
- Gatilho transitório de branch criado para essa validação e removido imediatamente após PASS; mantido somente o workflow manual SAFE em draft.
- A chave anteriormente exibida em captura ainda deve ser rotacionada; teste de autenticação **não prova** segurança da credencial.
- Próximas dependências: esquema real dos feeds, credenciais de download, persistência privada e conversor validado por testes.

**Código de continuidade:** `V31-EDITORIAL-C1-API-REAL-PASS-20261115`.

### Próximo marco de validação

`V31-EDITORIAL-C1-20261115-SAFE`

Testes unitários sintéticos **14/14 PASS** em CI após correção de allowlist de encurtadores. Próximo passo: validar o esquema CSV real e os secrets do Environment; depois preparar ingestão em nuvem com persistência privada. Não tratar simulação como implantação concluída.

## Separação operacional

```
Feeds Shopee (privados)
    → catálogo/deduplicação/revisão (privado)
    → links afiliados validados pela Open API (cache privado)
    → seleção editorial e política por site
          ├── adaptador Blogger → SAFE → aprovação LIVE → Blogger
          └── adaptador WordPress → SAFE → aprovação LIVE → WordPress

Pinterest: fora deste projeto.
```
