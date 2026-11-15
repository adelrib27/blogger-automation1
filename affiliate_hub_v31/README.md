# V31 Hub Editorial Shopee — Blogger & WordPress

## Escopo canônico (15/11/2026)

Este projeto opera **exclusivamente para blogs Blogger e WordPress**. Pinterest e redes sociais têm projetos separados e **não fazem parte** deste módulo.

Repositório: `adelrib27/blogger-automation1`. A implantação reside em uma branch isolada. Nenhuma automação de produção foi modificada.

### Secrets e variáveis do Hub (centralizado)

**Registro oficial de nomes e instruções:** [SECRETS.md](SECRETS.md)  
**Manifesto legível por máquina:** [credentials_registry.json](credentials_registry.json)  
**Verificação sem revelar valores:** `python -m affiliate_hub_v31.credentials --profile manifest`  
**Workflow manual SAFE:** `.github/workflows/v31_editorial_secret_inventory_safe.yml` (disponível para execução manual após inclusão na branch padrão).

Namespace isolado: `V31_EDITORIAL_...`. Nenhuma credencial real é versionada aqui, e os workflows comerciais existentes permanecem intactos. O cadastro efetivo dos secrets/variables no GitHub Environment `v31-editorial-safe` ainda é obrigatório e não foi executado.

### C4/C5 — Pilotos REAIS: conversão e originalidade de pautas

- **C4** [run 43771181969](https://github.com/adelrib27/blogger-automation1/actions/runs/43771181969): uma conversão `generateShortLink` real aprovada, link salvo no R2 e cache reutilizado sem nova API; restauração validada.
- **C5** [run 43771386845](https://github.com/adelrib27/blogger-automation1/actions/runs/43771386845): o **mesmo produto real** usado em **dois blogs Blogger**, com dois títulos/ângulos diferentes mantendo `air fryer`; ambos em `REVIEW_REQUIRED`, sem artigo/publicação.
- R2 restringe snapshots ao **atual + anterior**, e limpeza na execução real completada sem pendência.
- Todos os workflows transitórios de teste foram removidos após sucesso.
- **Checkpoint:** [C4/C5 — conversão real e pautas originais](CHECKPOINT_C4_C5_2026-11-15.md), código `V31-EDITORIAL-C5-ORIGINALIDADE-REAL-PASS-20261115`.
- Ainda faltam: publicar **rascunhos reais** nas plataformas, revisar textos completos e regras de agendamento/ativação gradual; credenciais LIVE e rotação da App Secret exposta precisam ser verificadas.

### C3 — Cloudflare R2 privado criado e verificado

- **Bucket existente:** `v31-editorial-shopee`, na conta selecionada pelo proprietário, classe **Standard**, sem domínio público `r2.dev` ou domínio personalizado.
- **Comprovado:** ativação da assinatura no painel e criação/consulta pela API Cloudflare. **Ainda não gravamos catálogo/objetos.**
- **Pendente:** criar credenciais S3 limitadas ao bucket e cadastrá-las no Environment GitHub `v31-editorial-safe`, configurar `V31_EDITORIAL_R2_ACCOUNT_ID` e `V31_EDITORIAL_R2_BUCKET`; validar conexão real e só então importar os feeds.
- **Checkpoint:** [C3 — bucket privado criado](CHECKPOINT_C3_R2_2026-11-15.md).
- **Continuidade:** `V31-EDITORIAL-C3-R2-PRIVATE-20261115-CREATED`.

### C2.1 — Dois feeds REAIS auditados em GitHub Actions

- **Prova:** [run 43732094595](https://github.com/adelrib27/blogger-automation1/actions/runs/43732094595), `V31_C2_REAL_FEEDS_PASS`. Foram lidos **100.000 + 10.000 registros**, com cabeçalhos de **24 e 16 colunas**.
- **493 duplicações preliminares** e **109.507 chaves diferentes** pelo deduplicador atual. Os feeds não possuem coluna reconhecida de `shopId`; revisar identificadores alternativos antes de tratar essas chaves como produtos comerciais distintos.
- **4.758 registros** corresponderam a nichos na versão inicial da taxonomia, **105.242 ainda sem nicho aprovado**. Não significa descarte definitivo.
- Bugs reais resolvidos: redirecionamento HTTPS interno Shopee e CSV com campos multilinha/aspas. O workflow temporário de auditoria foi removido; dados não foram persistidos.
- **Checkpoint C2.1:** [leitura real, limitações e próximos passos](CHECKPOINT_C2_1_FEEDS_REAIS_2026-11-15.md). Código: `V31-EDITORIAL-C2.1-FEEDS-REAIS-20261115-PASS`.
- R2, conversões comerciais e publicação ainda **não executados**.

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
