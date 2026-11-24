# SYSTEM MASTER — V31 Hub Editorial Shopee

**Sistema:** V31 Hub Editorial Shopee — Blogger & WordPress  
**Repositório canônico:** `adelrib27/blogger-automation1`  
**Branch de operação:** `main`  
**Escopo:** catálogo de produtos Shopee, pesquisa editorial, conversão afiliada, SEO, geração de artigos, revisão independente, DRAFTs e controles de publicação para Blogger e WordPress  
**Referência temporal do inventário:** 23/11/2026, horário `America/Recife`  
**Estado de liberação editorial:** `SAFE / DRAFT controlado`; política automática de `LIVE` em `pending_policy_approval`

> **Contrato desta fonte mestre.** Este documento define a arquitetura, o vocabulário e as regras operacionais do V31 como um sistema único. A implementação observável reside na `main`; o cadastro e as políticas de execução residem nos respectivos JSON; o catálogo e os jobs persistidos residem no R2/D1; a situação de cada artigo reside na API autenticada do CMS. Uma afirmação de estado mutável requer leitura dessas fontes. Toda alteração de arquitetura ou regra de negócio também atualiza este documento no mesmo ciclo de entrega. Nenhum PASS de simulação substitui a confirmação de uma operação externa.

## 1. Visão geral e propósito

O V31 opera uma biblioteca comercial **universal e cumulativa** de produtos Shopee, sem depender da existência prévia de um blog, de um nicho fixo ou de uma campanha específica. Dois datafeeds CSV alimentam a biblioteca. O sistema normaliza identificadores, conserva registros, organiza categorias e facetas, distingue produtos elegíveis de produtos que exigem revisão, permite busca por tema e prepara pautas para blogs Blogger ou WordPress devidamente cadastrados.

Ao existir uma demanda editorial válida, o V31 associa **site real + campanha Shopee real + SKU/variante exatos**. A seleção passa por controles de fonte, categoria, identidade do produto, foto e URL afiliada, pesquisa factual, relevância SEO e deduplicação. O conteúdo aprovado pode ser armazenado como HTML privado imutável, identificado por hash e coordenado com o estado `READY/USED` do Cloudflare D1. Os adaptadores de CMS entregam conteúdo exclusivamente em **rascunho**, mediante gates e confirmação de leitura remota. A publicação pública constitui uma operação separada, submetida a autorização expressa e política própria.

O sistema não promete tráfego, vendas, comissão, posição em buscadores ou disponibilidade de produto. Preço, cupom, estoque, frete, avaliação, garantia e características técnicas somente aparecem quando sustentados por evidência aplicável ao produto exato.

### Resultados desejados

1. Manter um catálogo central pesquisável e protegido, com preservação do acervo e da moderação.
2. Permitir atendimento a **qualquer blog atual ou futuro** que possua identidade, rota, campanha, fontes e permissões verificadas.
3. Produzir artigos originais e úteis, com conteúdo factual, imagem legítima, link comercial contextual e transparência de afiliação.
4. Evitar cruzamento entre blogs/campanhas, repetição de artigos, consumo duplicado de jobs e publicação indevida.
5. Expandir a produção por site de forma controlada, com observabilidade e sem teto global artificial de artigos.

## 2. Arquitetura lógica

```text
Datafeed CSV 1 ─┐
                ├──> validação de feed ──> catálogo SQLite ──> snapshot privado R2
Datafeed CSV 2 ─┘                                │                    │
                                                  ├── taxonomia/FTS5    ├── CURRENT.json
                                                  └── inventário/facetas└── índice sidecar
                                                             │
Tema + site verificado + campanha ──> roteamento/escopo ──> oferta elegível
                                                             │
                                              conversor Shopee por campanha
                                                             │
                                            evidência exata e revisão factual
                                                             │
                                          SEO + HTML final + assinatura
                                                             │
                                          envelope privado imutável R2
                                                             │
                                            D1 lease → READY → USED
                                                             │
                                        entrega idempotente em DRAFT
                                                   │                │
                                                Blogger         WordPress
                                                   └──── GET + hash ────┘
                                                             │
                                         autorização LIVE separada e fechada
```

O diagrama descreve o **contrato da integração**. Os módulos individuais existem; sua homologação operacional de ponta a ponta é um requisito explícito do roadmap, e não uma permissão presumida para executar todos os blocos automaticamente.

### Fronteiras de responsabilidade

- **Biblioteca:** armazena e pesquisa produtos; não autoriza publicidade a partir de uma categoria isolada.
- **Rota:** define o destino, plataforma, identificador CMS, campanha e nichos permitidos; não transforma a presença de um blog em permissão de escrita.
- **Oferta:** resolve produto exato, origem, imagem e link comercial da campanha; não inventa atributos.
- **Revisão:** verifica fatos, texto final, evidências, hashes, SEO e autorização técnica; o gerador não aprova a própria redação.
- **Estado:** R2 conserva bytes privados e D1 coordena concorrência, evidência e jobs; não constitui autorização de publicação pública.
- **Entrega:** os adaptadores escrevem DRAFT, verificam GET/status/identidade e registram recibos; não publicam LIVE por consequência de um DRAFT.
- **Liberação:** exige aprovação e verificações independentes, com política de ativação explícita.

## 3. Mapa de diretórios e arquivos principais

Os caminhos abaixo são relativos à raiz do repositório. A relação destaca os **pontos de entrada e contratos centrais**, não todos os utilitários ou testes disponíveis.

| Caminho | Responsabilidade atual |
|---|---|
| `SYSTEM_MASTER.md` | Contrato documental mestre de arquitetura, políticas, limites e roadmap. |
| `affiliate_hub_v31/` | Núcleo universal de catálogo, roteamento, evidência, revisão, armazenamento e entrega editorial. |
| `affiliate_hub_v31/CONTINUIDADE_ESTADO.json` | Estado de execução legível por máquina: atividade, próximo passo, bloqueios e referências verificadas. |
| `V31_CONTINUAR_AQUI.md` | Ponto de entrada operacional que aponta para o estado verificável e a execução corrente. |
| `affiliate_hub_v31/EDITORIAL_ACTIVE_SCOPE_POLICY.json` | Carteira autorizada, destinos verificados, exclusões e gates de qualidade. |
| `affiliate_hub_v31/EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json` | Lista de negação por ID e chave, com veto de roteamento e escrita para 24 identidades indisponíveis. |
| `affiliate_hub_v31/site_routes.json` e `affiliate_hub_v31/sites.d/*.json` | Registro extensível de rotas por blog e campanha. |
| `affiliate_hub_v31/site_requests.d/*.json` | Demandas editoriais reais: `site_key`, tema, plataforma, estado e quantidade total solicitada. |
| `affiliate_hub_v31/future_blog_onboarding.template.json` | Contrato declarativo de cadastro, SEO, pesquisa, evidências e limites para um destino novo. |
| `affiliate_hub_v31/autonomous_review_sources.json` e `trusted_manufacturer_sources.json` | Perfis de pesquisa e lista controlada de fontes técnicas. |
| `affiliate_hub_v31/autonomous_live_policy.json` | Gate de ativação e limites da liberação automática pública. |
| `affiliate_hub_v31/tests/` | Testes unitários, contratos, simulações de riscos e integração SAFE. |
| `.github/workflows/` | Agendamentos, CI, canários, auditorias, controle de concorrência e execução protegida. |
| `casa_decoracao/`, `oficina_garagem/`, `radar_tech_br/`, `vida_pet_pratica/` | Componentes e recursos específicos dos respectivos sites. O contrato global permanece no núcleo universal. |
| `src/` | Adaptadores e rotinas de geração, SEO, WordPress, políticas Blogger e verificações transversais. |
| `requirements.txt` | Dependências Python de integração Google/Gemini declaradas na raiz; workflows instalam também dependências específicas. |

### 3.1 Catálogo e pesquisa

| Módulo | Interface e função |
|---|---|
| `feed_download.py`, `feed_schema_probe.py` | Validam origem, formato e disponibilidade dos datafeeds. |
| `ingest.py`, `ingest_cli.py` | Importam os dois CSVs em operação atômica, com verificação de integridade antes da substituição do arquivo de trabalho. |
| `catalog_expansion.py` | Realiza expansão cumulativa, conservando moderação, registros e links existentes. |
| `catalog.py` | Abstrai o SQLite e os registros `products`, `product_taxonomy` e `affiliate_links`. |
| `taxonomy.py`, `taxonomy.json` | Regras conservadoras de classificação e normalização de título, categoria e nicho. |
| `source_category_index.py`, `title_index.py` | Hierarquia oficial e pesquisa textual por índice. |
| `universal_inventory.py`, `universal_index.py` | Inventário pesquisável, facetas e agrupamentos independentes do blog. |
| `universal_index_storage.py`, `universal_lexicon.py` | Índice lateral privado, vocabulário e instantâneos próprios. |
| `universal_reassessment.py`, `safe_reclassification.py`, `curation_triage.py` | Reavaliação explicável e promoção estritamente condicionada de SKUs elegíveis. |
| `r2_state.py` | Persistência privada e verificação SHA/integridade dos snapshots do catálogo. |

### 3.2 Seleção, rotas e conversão afiliada

| Módulo | Interface e função |
|---|---|
| `routing.py` | Consolida `site_routes.json` e `sites.d/`; valida identificadores, campanhas e especialização dos destinos. |
| `editorial_scope_validation.py` | Calcula `scope_status`, bloqueia identidades inelegíveis e oferece o simulador de 50 cenários. |
| `future_site_intake.py`, `site_launch_plan.py` | Avaliam assuntos e propostas de sites sem criar CMS, converter ou publicar. |
| `site_request_queue.py` | Organiza solicitações reais, seleção por rodada, orçamento de conversão e critérios de autorização. |
| `product_discovery.py`, `verified_supply.py` | Pesquisam e filtram ofertas compatíveis com o assunto e a rota. |
| `converter.py`, `universal_conversion.py` | Assinam chamadas Shopee, geram links por campanha e mantêm cache validado. |
| `campaign_cache_readiness.py` | Audita links já persistidos para a campanha exata, apenas em leitura. |
| `article_commerce.py` | Gera bloco comercial com imagem real, CTA, link afiliado e links editoriais pertinentes. |
| `universal_brief.py`, `universal_editorial_handoff.py` | Criam propostas editoriais e handoff estruturado por demanda real. |

### 3.3 Evidência, SEO, revisão e dados imutáveis

| Módulo | Interface e função |
|---|---|
| `universal_evidence_ready.py` | Whitelist de evidências, identidade exata, orçamento de pesquisa, cooldown e modelo READY em modo SAFE. |
| `manufacturer_review.py`, `structured_review_source.py` | Conferem fabricante/modelo e fatos estruturados identificáveis por GTIN quando disponíveis. |
| `source_policy_gate.py`, `final_fact_gate.py` | Recusam fontes contestadas e exigem fatos aprovados vinculados ao HTML final. |
| `future_blog_seo.py` | Verifica intenção, metadescrição, links internos do próprio site e sinais on-page. |
| `independent_review.py`, `autonomous_review.py` | Preparam candidatos e executam verificação independente com restrição de fontes e orçamento. |
| `review_signatures.py`, `reviewed_ready_promotion.py` | Vinculam bytes/identidade/evidência a recibos HMAC e atestação verificável; aplicam preflight antes de READY. |
| `private_ready_envelope.py`, `r2_private_ready_backend.py` | Conservam o HTML exato em objeto privado com escrita condicional sem sobrescrita. |
| `d1_universal_ready.py`, `d1_http_runner.py` | Coordenam leases, evidências, orçamento de pesquisa e estado READY/USED via SQL atômico e HTTP controlado. |

### 3.4 Escrita CMS, auditoria e publicação

| Módulo | Interface e função |
|---|---|
| `automatic_blogger_drafts.py` | Geração e inserção de um DRAFT Blogger com `isDraft=True`, identidade remota e deduplicação. |
| `automatic_wordpress_drafts.py` | Geração e inserção de DRAFT WordPress com `status="draft"`, slug estável e readback. |
| `reviewed_draft_delivery.py` | Consome um READY verificado e confirma o rascunho por ID, status e hash. |
| `ready_cms_collision_audit.py`, `audit_draft_pilots.py` | Verificam sobreposição de jobs e posts e a identidade dos pilotos quando há acesso remoto válido. |
| `autodraft_rollout_readiness.py`, `autodraft_schedule_outcome.py` | Expõem prontidão e resultados sem equiparar sucesso de job à existência de artigo. |
| `manual_live_release.py`, `autonomous_live.py` | Concentram os gates de liberação pública, sem autorização implícita do DRAFT. |
| `continuity_guard.py` | Audita coerência do registro de continuidade sem realizar escrita externa. |

## 4. Persistência, identidades e contratos de dados

### 4.1 SQLite e Cloudflare R2

- **Banco do catálogo:** SQLite, com tabelas comerciais e taxonomia, índices de pesquisa e integridade de banco verificada.
- **Bucket privado oficial:** `v31-editorial-shopee`.
- **Conta Cloudflare identificada para o núcleo:** `ebb8d5b4cf9a2cb850c6d8051bd2661f`.
- **Ponteiro de snapshots do catálogo:** `v31-editorial/CURRENT.json`.
- **Ponteiro de índice independente:** `v31-editorial/UNIVERSAL_INDEX_CURRENT.json`.
- **Envelope editorial privado:** namespace `v31/private-ready/v1/<site_key>/<campaign>/<prefixo_hash>/<sha256>.json`.

O R2 utiliza acesso S3 compatível, validação de SHA-256 e verificação de leitura. O envelope aplica `If-None-Match: *` para impedir que a gravação de um objeto com a mesma chave substitua bytes existentes. Um objeto isolado não é artigo aprovado e não autoriza o CMS.

### 4.2 Cloudflare D1

- **Banco oficial:** `v31-universal-ready-safe`.
- **Identificador de banco:** `9bfce7a4-6167-4bfc-a65e-a74c1a34f064`.
- **Tabelas de controle:** `v31_ready_leases`, `v31_ready_jobs`, `v31_verified_evidence`, `v31_search_budget`.
- **Transporte:** `CloudflareD1HTTPRunner`, com conta e banco fixados, SQL parametrizado, limites de payload e erro sanitizado.
- **Escritas:** bloqueadas por padrão; exigem controles explícitos e ambiente autorizado.

A reserva e o consumo verificam de maneira atômica `site_key`, campanha, SKU, hash de evidência, validade temporal e propriedade do lease. O objetivo é impedir duplicação em concorrência, consumo após expiração e utilização por outro destino.

### 4.3 Identidade obrigatória

| Campo | Regra |
|---|---|
| `site_key` | Chave lógica estável, minúscula, com letras, números e sublinhado. |
| `platform` | `blogger` ou `wordpress`. |
| `identifier` | ID Blogger autenticado ou URL base WordPress comprovada. |
| `campaign` | Identificador de campanha Shopee pertencente ao site. |
| `product_key` | SKU comercial no formato de chave `shopee:...`, vinculado a produto/variante. |
| `image_url` | Foto verdadeira vinculada ao mesmo SKU, com domínio admitido. |
| `affiliate_url` | URL HTTPS gerada/confirmada para a campanha correspondente. |
| `html_sha256` | Digest do HTML final aprovado e entregue, sem regeneração posterior. |
| `fingerprint` | Chave de idempotência de produto, pauta/ângulo e destino. |
| `status` | Estado distinguível entre análise, READY, USED, DRAFT verificado e LIVE autorizado. |

Nenhum identificador, título comercial ou URL de campanha pode ser inventado para completar uma estrutura parcialmente cadastrada.

## 5. Escopo editorial ativo

### 5.1 Destinos com rota V31 cadastrada

| Plataforma | Destino | Identidade |
|---|---|---|
| Blogger | Móveis para Cada Canto | `1439741542627895062` |
| Blogger | Limpeza Inteligente | `7757953554206491487` |
| Blogger | Estilo no Dia a Dia e Acessórios | `4830103887652146866` |
| Blogger | Cozinha Sem Complicação | `3552757910439359679` |
| WordPress | Casa e Decoração | `https://casaedecoracao.radartechbr.com.br/` |
| WordPress | Oficina & Garagem | `https://oficina.radartechbr.com.br/` |
| WordPress | Radar Tech BR | `https://radartechbr.com.br/` |

São **7 rotas editoriais registradas**, não um máximo de capacidade nem autorização geral de execução ou publicação.

### 5.2 Blogs acessíveis com restrição de onboarding ou escopo

- **Vida Pet Prática:** Blogger ativo, `8052455848487624244`, `https://vida-pet-pratica.blogspot.com/`. O status V31 é `CMS_ACTIVE_ONBOARDING_REQUIRED`: a identidade CMS é válida, mas rota e campanha editorial V31 ainda não são confirmadas. Não há escritor V31 autorizado para esse destino. Suas publicações e seu rascunho existente permanecem intactos.
- **Ar-Condicionado sem Dúvidas:** Blogger `2228849984262880811`, acessível, mas excluído do rollout editorial automático; a exclusão não autoriza exclusão do próprio blog.
- **Identidades explicitamente negadas:** os 24 IDs no arquivo de tombstones nunca entram em seleção, novas rotas, conversão, cron ou postagem.

O cadastro de um novo blog somente ocorre após validação de propriedade/acesso CMS, identificador único elegível, campanha real, nichos permitidos e perfil de revisão. A presença de um CMS acessível não implica permissão de escrever nele.

## 6. Regras de negócio invioláveis

### 6.1 Biblioteca e curadoria

1. Os **dois CSVs** alimentam um catálogo cumulativo; ingestão e expansão preservam produto, histórico, links e decisões editoriais válidas.
2. Identificadores comerciais são deduplicados sem assumir que **produto repetido** significa **artigo repetido**. A duplicação proibida é a de intenção, título ou corpo editorial sem diferenciação legítima. O reuso editorial controlado é opt-in, exige identidade e título/ângulo distintos e, no respectivo módulo, limita-se a dois artigos por produto.
3. Faceta oficial e palavras do título são sinais de busca, não autorização automática de uso comercial.
4. Produtos em `REVIEW`, contestados, fora do nicho, de categoria protegida ou com inconsistência de origem não seguem para conversão/postagem.
5. Aprovação ou reclassificação exige evidência suficiente, transição auditável, limites de lote e validação de integridade.

### 6.2 Campanha, oferta e veracidade

1. A identidade de consumo é composta por **destino + campanha + produto exato**; o cache de um blog não pode satisfazer outro.
2. O conversor trabalha sob demanda e `dry-run` por padrão; o fluxo de conversão autoriza no máximo **3 mutações Shopee por execução** em seu comando global, quando os gates permitem.
3. Foto, variante e link comercial pertencem ao mesmo SKU e à campanha correta.
4. A indisponibilidade de oferta segura interrompe a operação (`fail closed`). O sistema não substitui produto por outro arbitrariamente e não transforma erro de API em aprovação.
5. Texto editorial não reproduz como fato preço, comissão, estoque, cupom, frete, avaliação ou especificação sem fonte pertinente.

### 6.3 Conteúdo, SEO e revisão

1. O título e o texto respondem à intenção de busca real e são originais para a pauta e o público do site.
2. A ficha editorial utiliza evidência independente do produto exato e diferencia informação técnica verificável de recomendação geral.
3. Links internos referenciam apenas posts publicados, alcançáveis e relevantes **do mesmo blog**.
4. Links afiliados usam marcação comercial apropriada, incluindo `rel="nofollow sponsored"`, CTA contextual e aviso de afiliação.
5. Metadescrição, headings, termos principais, imagem/alt e schema somente são aprovados quando consistentes com o HTML e com os fatos demonstráveis.
6. Evidências respeitam fonte autorizada, identidade exata, prazo de validade e orçamento de pesquisa. O contrato do motor de evidências utiliza TTL de **sete dias**, sem renovação artificial em simples leitura; limites de pesquisa e cooldown são configurados por rotina.
7. O texto final passa por fact gate e revisão independente; recibos criptográficos atestam integridade do material, não substituem a existência de aprovação editorial autêntica.

### 6.4 Idempotência e produção

1. **Um DRAFT por execução controlada**, sujeito ao limite diário e à verificação de histórico do próprio destino.
2. `articles: null` representa demanda contínua **sem limite total arbitrário**. Um valor numérico representa uma solicitação finita e não amplia o total sem nova autorização.
3. `min_ready = 3` é meta de **buffer simultâneo**, nunca limite vitalício de artigos ou produtos.
4. Fingerprints, slugs, IDs remotos, títulos e hashes impedem reenvio do mesmo conteúdo em caso de retry ou interrupção.
5. O HTML recebido pelo CMS é o HTML aprovado: o sistema não regenera o corpo depois da revisão/assinatura.
6. **Blogger:** criação de rascunho com `isDraft=True`. **WordPress:** criação com `status="draft"`.
7. Um resultado `SUCCESS` do workflow não prova a criação do artigo; somente o recibo e o GET autenticado confirmam identidade, status e bytes.
8. Colisões de `READY` com post existente bloqueiam consumo e nova tentativa automática até reconciliação.
9. **LIVE permanece desativado na política automática V31** (`activation=pending_policy_approval`). A liberação pública requer gates e autorização explícita, vinculada ao conteúdo correspondente. Nenhuma permissão genérica de desenvolvimento substitui essa autorização.
10. Rotinas de CMS específicas são auditadas individualmente; o estado de uma automação não autoriza interpretar o comportamento de todas as outras.

### 6.5 Segurança

- Exceções têm comportamento **fail-closed**, com mensagens e logs sanitizados.
- Segredos e URLs assinadas pertencem a GitHub Secrets/Environments e nunca ao código, Markdown, artefatos públicos ou logs.
- Conta, bucket, D1, rota, campanha e domínio são validados antes de qualquer acesso de escrita.
- Concorrência de catálogo e entrega usa locks/leases e agrupamento de execução, incluindo `v31-editorial-catalog-single-writer` nos workflows pertinentes.
- HTTP sem origem autorizada, redirecionamentos inesperados, timeouts, respostas inválidas e limites externos interrompem a aprovação.
- Auditorias em modo somente leitura não alteram CMS, Shopee, D1, R2 nem políticas.

## 7. Tecnologias, padrões e convenções

| Categoria | Tecnologia/contrato |
|---|---|
| Runtime | **Python 3.12** nos principais jobs GitHub Actions. |
| Banco de produtos | **SQLite**, índices e pesquisa **FTS5**. |
| Banco transacional | **Cloudflare D1** via HTTPS e SQL parametrizado. |
| Objetos privados | **Cloudflare R2**, API compatível com S3, cliente `boto3` nos jobs pertinentes. |
| CI e agendamento | **GitHub Actions**, YAML, `workflow_dispatch`, `schedule`, ambientes protegidos e `concurrency`. |
| CMS Blogger | **Blogger API v3 / Google API Python Client**, OAuth e leitura pós-escrita. |
| CMS WordPress | **WordPress REST API**, credenciais de aplicação por site e validação de status/slug. |
| Geração editorial | Adaptadores de IA configurados por workflow, com validação do texto produzido; geração não é prova factual. |
| Pesquisa externa | Fonte de fabricante, dados estruturados e Firecrawl quando habilitado e com orçamento comprovado. |
| Integridade | **SHA-256**, **HMAC-SHA256**, atestação **Ed25519**, readback e escrita condicional. |
| Serialização | **JSON**, **CSV**, **Markdown** e HTML editorial; UTF-8. |
| Pacotes presentes | `google-api-python-client`, `google-auth`, `google-auth-httplib2`, `google-auth-oauthlib`, `google-genai`; workflows também instalam `requests`, `boto3` e `cryptography` conforme a tarefa. |
| Tempo | Instantes transacionais em UTC; cron e interpretação humana documentados explicitamente para `America/Recife` quando necessário. |

**Convenções:** módulos Python `snake_case.py`; diretórios e chaves de site `snake_case`; nomes de segredos/flags em `UPPER_SNAKE_CASE`; validação de tipos e esquemas JSON; normalização de títulos sem apagar o título comercial original; APIs externas encapsuladas em adaptadores; `preview`/`dry-run` como comportamento padrão de comandos de risco; mensagem de falha sem vazamento de dados pessoais ou segredos.

O arquivo `requirements.txt` da raiz não é a lista exaustiva das dependências de todos os jobs. Cada workflow declara os pacotes adicionais necessários à execução concreta.

## 8. Orquestração, observabilidade e critérios de aceite

### Workflows de referência

- `.github/workflows/v31_autonomous_draft_scheduler.yml`: agenda a seleção editorial e integra o fluxo de DRAFT mediante flags e elegibilidade.
- `.github/workflows/v31_independent_review_draft.yml`: executa etapas de histórico, verificação independente e entrega, com controles de ambiente.
- `.github/workflows/v31_autonomous_draft_canary.yml`: oferece canários manuais de assinatura, armazenamento, prontidão e CMS.
- `.github/workflows/v31_c133_autodraft_rollout_readiness_safe.yml`: informa prontidão sem publicar.
- `.github/workflows/v31_c143_deleted_blogger_scope_readonly.yml`: audita escopo, bloqueios e simulações.
- `.github/workflows/v31_continuity_guard.yml`: valida a consistência do estado documentado.

**Distinção operacional obrigatória:** `workflow_dispatch`, `schedule`, `push`, `skipped`, `success`, `DRAFT_VERIFIED` e `LIVE` são estados diferentes. Não existe equivalência automática entre um disparo e uma postagem efetiva.

### Evidências atuais de qualidade

- A suíte SAFE da integração editorial registra **768 testes aprovados** e **50 simulações aprovadas** na execução [GitHub Actions #45301938515](https://github.com/adelrib27/blogger-automation1/actions/runs/45301938515).
- Os testes locais específicos de WordPress confirmam **Casa e Decoração 24/24**, **Oficina & Garagem 21/21**, **Radar Tech BR 15/15**, com guarda de colisão entre blogs aprovada nessa execução.
- O rascunho Blogger Móveis para Cada Canto `4106024906916105222` aparece como `draft` em leitura autenticada.
- A colisão de READY da Casa e Decoração para `shopee:306698991:8503898928` com o post `#314` permanece bloqueada. O post Casa `#321` requer nova confirmação autenticada antes de qualquer operação relacionada.
- O scanner de ofertas registra um bloqueio seguro para **Cozinha / fatiador de legumes** quando não há produto elegível; mensagens Shopee GraphQL `10000` requerem diagnóstico específico, sem liberação por fallback não verificado.

**Aceite de entrega editorial real:** identidade CMS correta + campanha correta + produto/foto exatos + fatos autorizados e dentro da validade + SEO + assinatura/revisão válida + R2 HTML idêntico + D1 consistente + ausência de duplicata + POST DRAFT + GET remoto confirmando `draft` e hash + recibo auditável. Todos esses critérios precisam ocorrer **na mesma operação** antes da expansão da rotina.

## 9. Roadmap técnico priorizado

### P0 — Segurança e verdade operacional

1. Manter a negação dos 24 IDs e a exclusão de destinos desautorizados em todos os writers e agendamentos.
2. Revalidar acesso, inventário, flags e cotas pela API real antes de atividades que possam consumir dados ou criar posts.
3. Resolver divergências de auditoria de CMS, incluindo o GET dos posts WordPress Casa `#314` e `#321`, sem sobrescrever ou duplicar artigos.
4. Investigar a falha de disponibilidade da Shopee e os erros GraphQL `10000`, com limite de tentativa e circuit breaker.

### P1 — Integração e homologação DRAFT

1. Fechar o percurso completo **oferta aprovada → evidência externa → SEO → revisão independente → envelope R2 → D1 READY/USED → DRAFT → GET/hash**.
2. Demonstrar recuperação idempotente após falha de rede, perda de lease, expiração de evidência, concorrência, resposta CMS ambígua e interrupção de job.
3. Validar segregação real das chaves de revisão, atestação assinada e saldo/limite da pesquisa externa na conta correta.
4. Executar **50 simulações** em cada ciclo crítico e canários restritos; exigir evidência real por plataforma antes de ampliar o rollout.
5. Confirmar que DRAFT não consome produto de outra campanha e não aceita HTML diferente do aprovado.

### P2 — Cobertura universal e novos blogs

1. Completar o onboarding do Blogger **Vida Pet Prática** com rota, campanha e fontes verificadas, sem criar escritor especial ou permitir publicação antes dos gates.
2. Permitir cadastro adicional por arquivo em `sites.d/` e demanda real em `site_requests.d/`, sem hardcode de nichos ou teto fixo de blogs.
3. Consolidar pesquisa temática, curadoria explicável, conversão sob orçamento e geração editorial original com deduplicação global e por site.
4. Aplicar os mesmos contratos SEO, fontes e links internos aos novos destinos Blogger e WordPress.

### P3 — Operação recorrente e evolução controlada

1. Medir por site: seleção elegível, rejeições, qualidade factual, sucessos DRAFT verificados, colisões, retries, consumo de quota e latência dos agendamentos.
2. Ampliar o volume com **limite diário por site**, buffer READY e execução justa, sem limite total arbitrário de artigos.
3. Separar o mecanismo de autorização pública do mecanismo de DRAFT, com trilha de consentimento, estado persistente e rollback observável.
4. Evoluir o catálogo e a taxonomia sem liberar automaticamente itens em revisão ou modificar conteúdo externo de modo implícito.

## 10. Protocolo de mudança e continuidade

1. **Ler:** `SYSTEM_MASTER.md`, `V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json`, política de escopo, estado LIVE e o código da `main`.
2. **Verificar:** SHA atual da `main`, workflows recentes, PRs abertos e dados reais do serviço afetado. Não repetir uma operação que pode ter concluído sem recibo local.
3. **Registrar prévia:** objetivo, arquivos, riscos, branch, próximo passo e bloqueios no estado de continuidade **antes** da alteração importante.
4. **Implementar:** branch isolada, mudanças mínimas, sem segredos; preservar contratos, rotas protegidas e isolamento de tenant.
5. **Testar:** regressões, 50 simulações quando o ciclo for crítico, CI, canários seguros e readback do serviço real quando autorizado.
6. **Consolidar:** merge somente com evidência suficiente; registrar resultados, IDs, limites e rollback; atualizar este documento quando a arquitetura ou política mudar.
7. **Continuar:** o estado curto aponta para o trabalho atual e não transforma hipóteses, previews ou `SUCCESS` genérico em entregas concluídas.

**Princípio final:** o V31 é um único motor editorial universal. Cada site participa por identidade comprovada, campanha própria e aplicação uniforme de qualidade, segurança, SEO e idempotência. O acervo é cumulativo; a criação de DRAFTs é controlada; a publicação LIVE não é implícita; e a fonte mestre descreve somente aquilo que o código e as evidências atuais permitem afirmar.