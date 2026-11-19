# V31 — Contrato UNIVERSAL de SEO + estratégia Shopee para PRÓXIMOS blogs

**Versão:** C68 / 1.0 · **Fonte primária:** *FICHA TÉCNICA — NOVA ESTRATÉGIA DE BLOGS AUTOMATIZADOS COM SHOPEE*, v1.0, **12/11/2026**, 11 seções + diretriz final; complementada pelas orientações de SEO trazidas pelo proprietário em 19/11/2026.

**Aplicação:** novos blogs reais **Blogger e WordPress**, por nicho **somente depois de pesquisa e cadastro**; o módulo `future_blog_seo.py` é **offline/SAFE**. Este documento **NÃO ativa** nenhum escritor/cron já existente, não modifica posts ou autoriza LIVE. A arquitetura V31 continua um motor e acervo universal, nunca uma reserva de produtos antecipada para blogs futuros.

## 0. Mandato e prioridades

**O leitor busca primeiro a solução; o produto entra como evidência/opção comercial pertinente.** Não criar conteúdo porque um item existe no CSV Shopee. O novo projeto deve responder a pesquisas com **intenção de compra planejada**, critérios de escolha e comparação; selecionar **somente** anúncios elegíveis e pertinentes na conta/campanha real; publicar texto próprio e útil sem imitar depoimento, teste, consumo ou preço não verificado.

**Ordem de decisão:** demanda pesquisada e competitividade → nicho com utilidade/viabilidade → mapa de intenção e clusters → artigos originais que resolvem dúvidas → busca de SKUs elegíveis e links por campanha → gate editorial/comercial → DRAFT SAFE → revisão/autorização LIVE → monitoramento e atualização real. O feed CSV/R2 alimenta a biblioteca permanente, mas não prova volume de buscas, comissão atual, disponibilidade ou resultados de venda.

## 1. Extração fiel da ficha: 11 blocos → 11 contratos

| Capítulo da ficha | Decisão incorporada para novos projetos | Prova de implantação |
|---|---|---|
| 1. Objetivo | Conteúdo para decisões reais de compra, não vitrine de links | Brief com pergunta de busca, público/necessidade e resposta direta |
| 2. Produtos prioritários | Compra comparada, uso prático, alternativas, preço médio/alto **relativo à categoria** | Lista de 2+ opções apenas quando há dados verificáveis; categorias da ficha são exemplos, não catálogo fechado |
| 3. Comissões | **Sem percentual mínimo de 3%**, sem obrigatoriedade de comissão extra; comissão **positiva e verificada** | Origem API/campanha/timestamp de elegibilidade; cálculo R$ somente se preço e percentual realmente disponíveis |
| 4. Editorial | Qual escolher, A vs B, vale a pena (sem review fingido), critérios, diferenças, custo-benefício, capacidade/tamanho | H1/título, metadescrição, resposta no início, critérios, limites, fotos reais, CTA e transparência |
| 5. Shopee Affiliate Open API | Descoberta por query/categoria, confirmação de elegibilidade, alternativas e registro anti-repetição | `product_key`, campanha exata, resultado API datado, cache R2 e evidência de imagem |
| 6. Rotação/atualização | Preservar produto bom; trocar só com motivo factual; relinks/atualização de conteúdo antigo | Log de motivo, data, SKU anterior/novo, URLs, conteúdo antigo preservado, reversibilidade |
| 7. Isolamento | **Preferir repositório independente por blog**, secrets, workflow, histórico e logs individuais | Repo/branch/env/secrets separados; compartilhar motor V31 como código/biblioteca, não tokens |
| 8. Publicadores | Blogger API v3 + OAuth; WordPress REST API + autenticação; **e-mail descartado** | Conexão autenticada validada, bloqueio concorrência/dedup, PREVIEW → DRAFT → LIVE autorizado |
| 9. Seleção de nicho | Demanda, compra/necessidade **muito altas**; alternativas, preço/comissão R$, disponibilidade, concorrência **altas**; extra do vendedor secundário | Scorecard com fonte/URL/data por critério, UNKNOWN não vira número |
| 10. KPIs | Impressões, cliques orgânicos, posições, affiliate CTR, conversões, ticket, comissão REAL R$, conteúdo qualificado, atualizações úteis, falhas | Painel com fonte/periodicidade e `not_available` quando não conectado |
| 11. Novo projeto | Pesquisar nichos → selecionar fundamentado → identidade/categorias → repo+contas → Shopee sem mínimo → SAFE → autorização LIVE | Gate de onboarding assinado por site real; nunca pular perguntas comerciais |
 
**Seção final da ficha:** priorizar produtos de compra planejada e demanda comercial relevante, viabilidade de comissão EM REAIS sem inventar ganho; consumidor determina pauta, Shopee é fonte de ofertas. **Não implementar limiar percentual de comissão** nem pressupor que comissão-base + extra se somam. O exemplo R$ 100 × 5%=R$ 5 etc. é **ilustrativo**, não um modelo de receita garantida.

### Categorias possíveis, jamais seleção antecipada

Eletrodomésticos (geladeira, lava-louças, lavadora), tecnologia (notebooks, impressoras, monitores), climatização (ar-condicionado), casa e conforto (colchões, sofás, móveis), ferramentas (lavadoras de alta pressão, furadeiras, compressores), escritório (cadeiras ergonômicas e produtividade). O usuário poderá solicitar **qualquer novo nicho compatível**, mas só há blog/campanha após criação real; não registrar reservas fictícias.

## 2. SEO de intenção (on-page): um cluster antes do calendário

Cada novo blog recebe um **mapa de demandas verificadas** (`source`, `query`, `observed_utc`; nunca inventar volume) e um mapa editorial.

**Tipos de intenção suportados pelo módulo SAFE:**
- `buying_guide`: o que observar antes de comprar; capacidade, medidas, uso, material;
- `comparison`: modelo A vs B **somente com ficha verificável para os dois**;
- `alternatives`: alternativas por perfil/necessidade; não atribuir “melhor” sem metodologia;
- `use_case`: notebook para trabalho remoto, sofá para espaços pequenos;
- `value`: custo-benefício real, custo total quando verificado;
- `features`: inverter ou convencional, funções, limites e manutenção.

**Content cluster proposto:** pilar “Como escolher [categoria] para [necessidade]” → satélites “[modelo/capacidade] vale a pena?”, “A vs B”, “medidas”, “manutenção”, “comparação por uso”. O pilar deve apontar para satélites já publicados; satélites apontam para o pilar já publicado e para assuntos adjacentes **reais**. Um blog novo com zero posts tem **cold start legítimo**: escrever o primeiro guia pilar e marcar `RELINK_AFTER_NEXT_PUBLISH`; jamais criar hiperlinks fictícios para atingir quota de links.

**Contrato por artigo:**
1. 1 pergunta/intenção principal e query de cauda longa apoiada em evidência externa datada; headings e corpo coerentes, resposta direta e informação diferenciada.
2. `SEO title` original, claro e fiel; `meta description` útil, sem falsa promessa de clique, avaliação ou resultado. Comprimentos recomendados pelo projeto **não são fatores nem limites fixos do Google**.
3. Texto autoral e legível, comparação baseada em especificações sustentadas ou questionamentos neutros (sem opinião “testamos”); prós/contras apenas se fundamentados, avisar limites.
4. Imagem legítima do mesmo SKU e **alt descritivo**, URL HTTPS válida; lazy load de imagens abaixo da dobra, atenção à primeira imagem/LCP; formatos/bytes/dimensões medidos de fato antes de afirmar compressão.
5. Links Shopee pela **campanha EXATA** do blog e `rel="sponsored nofollow"`, CTA contextual e aviso visível de comissão.
6. Artigos complementares do MESMO blog, realmente `publish`/`live`, URLs canônicas HTTPS, âncoras descritivas e assunto relacionado. Nunca apontar deliberadamente para outro blog só porque são da mesma rede.
7. Autoria e política editorial verdadeiras, fontes onde aplicável e registro de atualização quando ocorreu revisão de fato; não criar personas/credenciais, avaliações ou experiência prática.
8. DRAFT / SAFE por padrão; publicação LIVE só após gate/autorização. Evitar geração em massa com páginas quase iguais e valor mínimo; não prometer posições.

### 2.1 Links internos — critérios executáveis C68

`future_blog_seo.plan_internal_links` recebe `site_url`, `current_url`, `primary_query`, `cluster_id` e uma lista de **posts publicados lidos no CMS**, nunca URLs inferidas de slugs. Ele:

- Exige origem HTTPS canônica e **hostname idêntico**; rejeita `draft`, `pending`, `future`, páginas com parâmetros, domínio estrangeiro, URL da própria postagem e duplicação de link.
- Escolhe páginas cujo título/palavras-chave têm termos de assunto coincidentes **ou** pertencem ao mesmo `cluster_id` verificado; prioriza o pilar do cluster. Não seleciona páginas irrelevantes só para chegar a 3.
- Sugere **até 3** links internos **por artigo como prática editorial ajustável**, **não como teto de produção nem condição absoluta SEO**; se não existem posts publicados/pertinentes, retorna `COLD_START_NO_PUBLISHED_ARTICLES` ou `NO_RELEVANT_INTERNAL_POSTS` e solicita relink posterior.
- Permite snippet HTML escapado `render_related_links` com âncora **título descritivo do artigo**, nunca “clique aqui”; futuramente inserir links contextualizados no parágrafo com revisão, não espalhar automaticamente sem coerência.
- Audita hrefs internos da postagem: se apontam para URL não presente na lista de `publish`/`live` retornada do CMS, **BLOQUEIA SAFE** até verificar origem. O estado publicado deve ser colhido integralmente/paginado para não classificar um post antigo como inexistente por paginação parcial.
- Planeja manutenção reversa pilar ↔ satélite. Nenhum link cruzado de campanhas.

**Importante:** a seleção semântica por tokens/cluster é **heurística de relevância**, não certificação da qualidade final. O editor precisa verificar sentido e status atual de cada destino, e links quebrados devem ser testados online quando o blog já existir.

## 3. SEO técnico — por CMS, depois da existência do domínio

| Verificação | Critério para novo blog | Fonte/status |
|---|---|---|
| HTTPS/certificado | Domínio final, redirecionamento seguro e certificado válido | TESTAR no endereço real |
| Responsivo/mobile-first | Mesmo conteúdo, links e dados relevantes no mobile, sem obstruções de CTA | TESTAR em device real |
| LCP / INP / CLS | Meta **LCP ≤2,5 s**, **INP ≤200 ms**, **CLS ≤0,1** no percentil 75; não garantido por código Python | Search Console/CrUX/PageSpeed |
| Imagens | alt, origem SKU, largura/altura, peso em bytes, formato adequado, lazy abaixo da dobra | HTML + métricas de imagem reais |
| URL/canonical | Slugs legíveis quando possível, canonical consistente com sitemap/links, sem variantes indevidas | Configurar no CMS |
| Sitemap XML | Autogerado corretamente e acessível após criação/publicação | GET remoto + Search Console |
| Robots.txt/noindex | Não bloquear posts públicos acidentalmente; preservar drafts privados | GET remoto |
| Dados estruturados | `BlogPosting`/`Article`, `BreadcrumbList` se compatível com fatos visíveis e tema/plugin sem duplicação | Rich Results Test e URL publicada |
| Product / Review / AggregateRating | **NÃO injetar dados não existentes**, teste próprio, estoque/preço/nota não verificáveis | Se não houver requisitos/fatos, `NOT_APPLICABLE` |
| Rastreamento | Links internos quebrados, órfãos, redirecionamento, status/canonicals e Search Console | Scan periódico após site real |
| Metadados | Blogger: template/descrição customizada e recursos disponíveis; WordPress: plugin/campos REST compatíveis, sem prometer meta salvo caso a API não aceite | Validar readback da página pública |

**Atenção ao Blogger:** Blogger pode gerar permalinks por data; não prometer URL formatada exatamente como WordPress. **Atenção ao WordPress:** não presumir plugin SEO ativo, acesso REST a meta fields ou alteração do tema; integração depende de leitura/capacidade no CMS. A biblioteca C68 é **standalone** para que legados C67 não sejam afetados.

## 4. Autoridade (E-E-A-T) e SEO off-page — ações legítimas

- Assinatura/autoria e credenciais **verdadeiras** e política de transparência; citar métodos e fontes verificáveis, explicar como o conteúdo foi produzido quando pertinente.
- Conseguir backlinks por conteúdo de referência, dados reais, PR digital e parcerias editoriais adequadas; **não gerar spam, guest posts artificiais nem inventar menções**.
- Criar comparativos, checklists e material realmente útil para ser citado; monitorar backlinks/menções reais por ferramentas próprias, valor inicial `UNKNOWN`.
- Registrar fontes, correções e atualização de artigos antigos; publicar revisão com motivo concreto, não trocar produtos em massa para aparentar frescor.
- Off-page é workflow humano/relacional, **não deve ser afirmado como concluído por uma execução de escritor**.

## 5. SEO local — SOMENTE quando existe operação local real

O usuário listou Google Perfil da Empresa, avaliações e NAP. Esses recursos **não são requisito padrão de blog afiliado nacional sem estabelecimento**. Ativar apenas para negócio local verdadeiro, elegível e com endereço/área de atendimento, marca, telefone e diretórios **fornecidos/verificados**. Não criar presença/avaliações fictícias nem inventar NAP.

## 6. Política de produto, comissão, concorrência e risco de API

**Seleção de nicho:** registrar `demanda_comercial`, `intencao_compra`, `utilidade` (muito alto), `comparabilidade`, `preco_medio`/comissão em reais, `ofertas_elegiveis`, `concorrencia` (alto); comissão extra vendedor apenas fator secundário. Campos devem conter `estado: verified|unknown|not_applicable`, fonte, data e evidências. Um score numérico poderá existir **somente como método editorial declarado**, nunca como volume de pesquisa medido sem dados.

**SKU:** usar `shop_id:item_id` único, foto legítima, categoria/taxonomia aprovada, link único pela campanha do site, dados atuais da API se disponíveis. A consulta R2 mantém itens em `REVIEW` **bloqueados**; não deduzir comissão positiva da existência de um link CSV. Falta de preço/comissão = **comissão não verificada**, não 0% nem 3%.

**Estimativa em reais (só com dados reais):** `receita_bruta_estimada = preco_atual_confirmado * percentual_total_verificado/100`. Percentuais distintos **não são automaticamente somáveis**; atualizações/estornos fazem a comissão real divergir da estimativa. Nenhuma meta de faturamento é garantida.

**Erro comercial vs técnico:** `10000` e outros erros de API são falhas técnicas — retry limitado com backoff e diagnóstico sanitarizado; depois interromper ou usar somente cache **da campanha correta, já aprovado**. Erro da API **não significa sem produtos elegíveis**. Segredos sempre em Secrets, apps/cotas Shopee reais isoladas; várias cópias da mesma credencial continuam compartilhando quota.

**Rotação de anúncios:** validar relevância editorial e motivos (anúncio inativo, produto não disponível, especificação incorreta, atualização real); preservar os bons apesar de comissão percentual menor; links/dados só substituídos com evidência e log.

## 7. Independência operacional: V31 UNIVERSAL + projetos separados

A ficha diz **preferencialmente 1 repositório por blog**, com workflows e histórico próprios. Isso é compatível com a missão V31 por esta separação:

- **Camada central V31:** acervo R2 dos 2 CSVs, taxonomia/curadoria, módulo de conversão e templates de código/SEO **reutilizáveis**, sem nichos inventados nem contas futuras;
- **Camada projeto novo real:** próprio `site_key`/registro, domínio Blogger ID ou WordPress HTTPS real, campanha afiliada exclusiva, config editorial e clusters, histórico, secrets específicos, ambiente SAFE e lock de publicador, logs/cron do próprio repositório quando adotado. Alternativa de cadastro em `sites.d` do Hub permanece para blogs realmente existentes e autorizados; o isolamento do projeto não deve quebrar o motor.
- Nenhum blog novo será provisionado por esta ficha isoladamente. Quando o proprietário solicitar um nicho/blog real, pesquisar demanda/concorrência e confirmar contas, domínio e campanha antes do provisionamento; não clonar tokens.
- Noite/dia: fila limitada de conversões R2 por execução **não limita o TOTAL de artigos** do projeto. `articles:null` continua válido para geração contínua DRAFT-first.

## 8. Contrato de dados por novo blog e por artigo

**Novo blog:** `site_key`, plataforma, domínio/ID existente, campanha única, `niche`, perfil de público, fontes de pesquisa de demanda, mapa cluster/pilar, author/policy validada, timezone, repositório, var/secrets separados, quotas/custo API declarados, status de sitemap/robots/HTTPS, mecanismo de dedup e gatilho SAFE.

**Artigo:** `query`, `search_intent`, `keyword_evidence {source,query,observed_utc}`, `cluster_id`, `title`, `meta_description`, `canonical_url`, `editorial_decision_criteria`, `verified_product_keys`, `image_url/alt`, `campaign_link`, `disclosure`, `internal_links [{url,title,status,cluster_id}]`, `draft_id`, `content_sha256`, `reviewers`, `publication_evidence`.

**Estados de pesquisa:** `VERIFIED` (fonte/datado), `UNKNOWN` (não há medição), `NOT_APPLICABLE` (ex.: Perfil Empresa em blog nacional). **UNKNOWN ≠ 0**. Não publicar afirmação baseada em UNKNOWN.

## 9. Gates e aceitação de um próximo blog

- **G0 — Nicho:** demanda/intenção e concorrência pesquisadas em fonte real; sem criação por volume de CSV.
- **G1 — Identidade:** blog real, domínio, ambiente SAFE, repo/contas/segredos e campanha unívocos, sem compartilhamento indevido.
- **G2 — R2/Shopee:** SKU elegível/taxonomia, imagem real, afiliado cacheado correto, comissão positiva confirmada quando aplicável pela API; erro 10000 separado.
- **G3 — SEO/cluster:** evidência da query, brief, metadata por CMS, H2 coerentes, alt, `sponsored`, disclosure, linkagem interna publicada ou justificativa cold-start, canonical e sitemap em auditoria.
- **G4 — Robustez:** histórico completo, dedup título/SKU/URL, 1 writer por site, retries limitados sem duplicar POST, diagnóstico e rollback. Core Web Vitals medidos **depois** da hospedagem real.
- **G5 — DRAFT e revisão:** CMS ID DRAFT readback, qualidade/fatos/campanha/internos, links públicos inexistentes não forçados, sem promessas e sem schema falso.
- **G6 — LIVE:** consentimento individual, hash do título+HTML, confirmação exata e leitura após publicação; nunca LIVE em massa implícito.
- **G7 — Medição:** Search Console/GA4/eventos afiliados apenas se conectados e autorizados; KPIs sem números inventados, cadência de revisão/atualização.

**Resultado atual da C68:** o motor `future_blog_seo.py` permite preparar planos de linkagem contextual e auditorias **offline**. Não há migração dos geradores atuais, injeção automática de SEO em tema, acompanhamento GSC nem Blog Novo criado. Esses pontos exigem projeto/credenciais reais e homologação por CMS.

## 10. Métricas e cadência sugerida (proposta operacional, NÃO dado da ficha)

- Semanal: erros de API, novos drafts e dedup, links quebrados no site real, cache SKU/campanha, publicações indexáveis;
- Mensal: Search Console (impressões, CTR, consultas e posições), cliques afiliados/conv. **somente se medidos**, atualização por tema, Core Web Vitals;
- Trimestral: saúde do cluster, relink de posts órfãos, posts desatualizados, ROI em reais quando contas permitirem, oportunidades externas legítimas.

Metas quantitativas só são definidas depois de medir a linha de base. Contagem de artigos sozinha não é KPI suficiente.

## 11. Uso do módulo C68 sem LIVE

```python
from affiliate_hub_v31.future_blog_seo import plan_internal_links, audit_future_article

# Passe SOMENTE dados REAIS de um blog que já existe e posts comprovadamente
# publicados por Blogger API v3 ou WordPress REST. Nunca use fixture em produção.
plan = plan_internal_links(
    site_url="https://blog-real.example/",  # apenas exemplo, não cadastro
    current_url="https://blog-real.example/guia/", 
    primary_query="como escolher cadeira ergonomica para trabalhar",
    cluster_id="cadeiras-ergonomicas",
    published_posts=[],  # blog novo, cold-start: NÃO inventa links
)
assert plan["status"] == "COLD_START_NO_PUBLISHED_ARTICLES"
assert plan["links"] == []
```

Para auditoria offline de artigo novo real: `python -m affiliate_hub_v31.future_blog_seo --input-json /caminho/brief_validado.json`. Nunca passar segredos em JSON, logs ou CLI. `READY_FOR_EDITORIAL_SAFE_REVIEW` **NÃO** autoriza LIVE nem confirma PageSpeed/SEO rankings; estados faltantes aparecem em `technical_not_measured`.

## 12. Referências de implementação atuais (Google Search Central; não da ficha)

- Conteúdo útil e para pessoas: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Políticas antispam e páginas afiliadas: https://developers.google.com/search/docs/essentials/spam-policies
- Links rastreáveis e âncoras: https://developers.google.com/search/docs/crawling-indexing/links-crawlable
- Core Web Vitals: https://developers.google.com/search/docs/appearance/core-web-vitals
- Mobile-first: https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing
- Estrutura/sitemap/canonicals: https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- Reviews com pesquisa substancial: https://developers.google.com/search/docs/appearance/reviews-system

**Não existe garantia de indexação, primeira página, clique, venda ou comissão por seguir estes critérios.** A aferição requer sites reais, fontes de pesquisa e métricas conectadas.
