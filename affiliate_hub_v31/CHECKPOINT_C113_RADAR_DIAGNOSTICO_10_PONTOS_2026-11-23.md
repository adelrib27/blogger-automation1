# V31 / Radar Tech BR — C113: diagnóstico de 10 falhas e validação da navegação C112

**Data:** 2026-11-23 • **Origem:** `1_comando_chatgpt_corrigir_blog.txt` + captura da HOME fornecida pelo proprietário.  
**Escopo:** diagnóstico ETAPA 2, sem corrigir código editorial e sem reescrever ou publicar artigos.  
**Repositório:** `adelrib27/blogger-automation1` / `main`. **Site:** https://radartechbr.com.br/

## C112 — Navegação alterada e homologada antes do diagnóstico
- WP-CLI GET autenticado confirmou o header `wp_template_part` **post ID 66**, original com 3.370 caracteres, **idêntico** ao arquivo C110 antes de alterar.
- Backup pré-mudança: `affiliate_hub_v31/backups/C112_RADAR_HEADER_BEFORE_NAV_COMPACT_2026-11-23.html`.
- Novo header C112: `affiliate_hub_v31/exports/C112_RADAR_HEADER_COMPACT_TECH_ARCOND_2026-11-23.html`, 2.567 caracteres, aplicado via `wp_update_template(type=template_part,template_id=twentytwentyfive//header)`.
- Resultado: removida faixa utilitária escura superior (`rt-v2-utility`), menu principal **Início | Tecnologia ▾ | Guias de Compra ▾ | Loja**. **Smartphones, Computação, TVs e Smart TVs, Ar-condicionado** agora dentro de Tecnologia, junto aos 4 hubs preexistentes e categoria geral; manteve bloco de busca/branding, ações e menu Guias. Categorias WordPress: Ar-condicionado ID 20, parent Tecnologia ID 3, zero artigos.
- GET autenticado WordPress pós-escrita retornou **conteúdo exato** do arquivo GitHub novo (2567/2567). Firecrawl RAW público fresco (maxAge=0) também confirmou a ordem dos links e `<details>` duplo, ausência de top-level Smartphone e ausência de `rt-v2-utility-inner` no DOM. Nenhuma publicação de post, home rewrite, alteração CSS ou mudança em automação.
- Atenção: submenu Ar-condicionado leva a categoria vazia legitimamente criada pelo proprietário; não inventar conteúdo ou agregar artigo por categoria sem conferência.

## Fontes do diagnóstico
1. Gerador vNext `radar_tech_br/src/generate_articles.py`, em particular linhas 143–170, 201–224, 227–278 e 305–364.
2. Gate `radar_tech_br/src/quality_gate.py`, linhas 63, 132–165 e 218–269.
3. Publicador `radar_tech_br/src/publish_generated.py`, especialmente linhas 100–105, 306–383.
4. Fila `radar_tech_br/src/prepare_slot.py`, workflow `.github/workflows/radar_editorial_vnext_autonomous.yml`, `config/wordpress.json`, rota `affiliate_hub_v31/site_routes.json`.
5. Amostras WordPress `wp_get_post_full(context=edit)`: post #314 (ventilador), #326 (aparador), controle recente #324 (luminária). Dados e autores consultados diretamente; `/politica-editorial/` página #170 também verificada.
6. API Shopee, sem nova chamada: campos solicitados em `src/shopee_oportunidades.py` linhas 97–134 e produtos serializados na fila `data/fase3/fila_dia.json` (snapshot 22/11).

## Os 10 pontos: evidência, causa e prioridade

### 1. Vazamento de instruções na meta descrição — CONFIRMADO / P0
- `generate_articles.py:220–224`: `meta_description(plan)` começa literalmente com `reader_need`. Em `:347` e `:351` o texto é reutilizado em SEO e excerpt. `quality_gate.py:63` não inclui `O leitor precisa/busca` nos gatilhos anti-leak.
- WordPress #314 e #326: `excerpt.raw` e `_aioseo_description` começam com `O leitor precisa...`, verificadas via API autenticada.
- Corrigir na ETAPA 3: separar `reader_need` interno da frase comercial ao leitor, gerar descrição específica com verificação final em excerpt+SEO+HTML, zero instrução editorial.

### 2. Artigo genérico sem conexão factual com oferta — CONFIRMADO NAS AMOSTRAS / P0
- `generate_articles.py:227–239` exige utilidade independente da oferta, mas manda **não escrever como ficha técnica ou review, nem repetir o modelo**. `article_prompt:262–278` envia ao modelo somente título, necessidade, conexão e `item['product']`, sem ficha técnica estruturada da oferta; `quality_gate.py` não impõe factualidade mínima por SKU.
- #314 orienta potência, ruído, limpeza e tipos sem especificações verificadas da oferta citada. Isso não torna toda orientação genérica incorreta, mas diminui valor de decisão sobre aquele produto.
- Corrigir na ETAPA 3: `product_evidence` validado com `fact_source` e `unknown_fields`; detalhes que faltarem viram “confira no anúncio”, nunca invenção.

### 3. Introdução/conclusão e frases repetitivas — CONFIRMADO / P1
- #314 reitera “opção econômica e eficaz” no corpo e na conclusão. #326 repete explicações gerais de higiene. `quality_gate.py:132–134` só veta H2 idêntico, não semelhança de parágrafos nem conclusão redundante.
- Correção futura: similaridade textual/semântica com tolerância para termos técnicos; conclusão deve acrescentar decisão, limitações e itens a conferir, não reciclar introdução.

### 4. Dois blocos de oferta Shopee — CONFIRMADO E EXIGIDO PELO CÓDIGO / P0
- `generate_articles.py:305–332`: `pieces=[first_part,cta,second_part,...,cta]`, CTA duas vezes.
- `quality_gate.py:225–269`: **exige** exatamente 2 títulos de produto/2 CTAs, 4 ocorrências de affiliate link, 2 disclosures, 4 rel sponsored/no-follow.
- No #314 há **2 blocos `og-produto-relacionado`** e 4 links do MESMO SKU; #326 tem 2 blocos e 4 links também. Os 2 `<img>` por artigo não são evidência de duas imagens editoriais distintas: são repetição do bloco.
- Correção futura: 1 bloco principal por oferta, 1 disclosure comercial claro e 1–2 links no próprio bloco; adaptar gate, testes, CTA e migration/compatibilidade. Não retirar links à força de artigos antigos sem backup.

### 5. Negrito/keyword stuffing visual — CONFIRMADO NAS AMOSTRAS / P1
- HTML #314: 30 `<strong>`/`<b>`; **28** contêm “ventilador”; #326: 18 negritos, 14 com “aparador de pelos”.
- O prompt `universal_article_rules:254` pede naturalidade mas o gate não limita densidade de negrito/palavra-chave. Isso não prova penalidade do Google; é sinal de baixa qualidade editorial.
- Correção futura: permitir negrito apenas em pontos úteis, detectar excesso com limiar proporcional e não forçar repetição exata da keyword.

### 6. Títulos sem intenção de busca forte — CONFIRMADO EM EXEMPLOS / P1
- Exemplos #326 `Aparar Pelos com Fácil Uso e Higiene`, #314 `Escolhendo o Melhor Ventilador para o Verão`, #320 `Escolhendo Parafusadeiras para Trabalhos Diversos`.
- `generate_articles.py:143–170,201–207` exige título de 35 a 60 caracteres, mas não verifica padrões reais de busca nem identificação do modelo quando a intenção exige. `quality_gate.py:153–156` aceita 25–65 caracteres de título e 110–160 de meta, **diferente** da meta desejada 140–155.
- Corrigir na ETAPA 3: intenção real e título descritivo específico; comparativos/listas com preços somente quando dados completos, estáveis e equivalência forem verificadas; CTR não é garantido.

### 7. Nichos fora de tecnologia — CONFIRMADO / P0
- WordPress no início da auditoria: **37 posts LIVE, 14 na Tecnologia e 23 em Guias de Compra**, contendo moda, cozinha, beleza etc. #326 está na categoria genérica e não pertence à identidade editorial atual.
- `prepare_slot.py` mantém cinco categorias históricas; workflow `radar_editorial_vnext_autonomous.yml` valida as cinco antigas e cinco slots; `publish_generated.py:27–34` ainda mapeia categorias removidas; `config/wordpress.json` ainda apresenta nicho amplo.
- A rota V31 `wordpress_radartechbr` já está em `allowed_niches=[tecnologia/gadgets]`, `publish_enabled=false`, **mas não controla por si só o writer legado**. Corrigir seleção no ponto de origem, preservando destinos SEO e não apagar posts sem estratégia.

### 8. Mesmo molde editorial em todos os artigos — CONFIRMADO NO GERADOR VNext / P1
- `universal_article_rules:235` fixa 700–1400 palavras e 5 H2, mesma estrutura para temas distintos; `insert_contextual_blocks:305–332` insere CTA em posições fixas. Isso favorece conteúdo estruturalmente repetitivo.
- Verificações #314/#326 mostram intro genérica, múltiplos H2, seção conclusiva, CTAs repetidos; #324 é um **contraexemplo** recente, com 8 itens e FAQ, portanto não afirmar que todos os 37 usam o mesmo molde.
- Corrigir: tipos editoriais (guia de compra, compatibilidade, explicação, comparação real, checklist, FAQ) determinados pela intenção, não apenas por contagem de palavras.

### 9. Autor e metodologia — PARCIALMENTE PROCEDE / P2
- #314/#326 atribuem `Equipe Radar Tech BR`; WordPress usuário #1 **tem bio cadastrada** (“Equipe editorial ... transparência, pesquisa e revisão”). Página `/politica-editorial/` ID170 **já explica como produz conteúdo e diferença entre pesquisa e teste real**. Portanto a afirmação de que “não há perfil/metodologia” não é inteiramente correta.
- Necessidade: avaliar se autoria, bio e Política Editorial são visíveis e fáceis de acessar em cada artigo; transparência sobre fontes/produto pode ser reforçada. **Rosto pessoal não é requisito universal** e não fabricar pessoas nem alegar testes.

### 10. Comparativos, FAQ schema, atualização, imagens e links internos — LACUNAS MISTAS / P1–P2
- #314/#326: sem seção FAQ específica, 2 imagens duplicadas do CTA, 3 links internos no HTML bruto, mas quantidade não prova pertinência; WordPress `date` e `modified` existem e são iguais, não houve revisão posterior comprovada.
- #324 é diferente: contém FAQ em texto, 1 imagem e link comercial, sem prova de schema FAQ e com 2 links internos.
- `productOfferV2` do scanner disponibiliza id, nome, URL original/afiliada, imagem, preço min/max, vendas, nota agregada, comissão, loja e período; **não é ficha técnica confiável nem reviews verificadas**. “Melhores até R$ X” ou comparações só com dados e disponibilidade verificados, nunca forçar preço que muda.
- **Google Search Central atual em novembro/2026 diz que FAQ rich result deixou de ser exibido em maio/2026**; não prometer que `FAQPage` gera destaque. Perguntas úteis no texto são desejáveis, schema só quando apropriado e sem fraude. Fonte: https://developers.google.com/search/updates (novembro/2026). Google exige conteúdo original e útil, não mera produção em escala; fonte https://developers.google.com/search/docs/fundamentals/creating-helpful-content.
- Priorizar: informações verificáveis, conclusão própria, imagens **não duplicadas** quando disponíveis e licenciadas, fontes e links internos contextuais, datas de revisão reais, estrutura editorial condizente com cada intenção.

## Segurança de automações: gate independente encontrado
- Workflow legado `.github/workflows/radar_editorial_vnext_autonomous.yml` declara crons UTC `11:00,13:30,16:00,19:00,22:00`, `RADAR_LIVE_PUBLISH_ENABLED=true`, `RADAR_WORDPRESS_STATUS=publish`, `RADAR_DAILY_PUBLISH_CAP=5`, **e chama `publish_generated.py`**. `publish_generated.py` ainda aceita `status=publish` e promove de DRAFT.
- O V31 AUTO LIVE OFF e `site_routes.json.publish_enabled=false` **não equivalem** a desligar o workflow legado. Há commits de estado do Radar vNext entre 21 e 23/11, mas logs completos de todos os schedules pós-22/11 não foram obtidos via integração disponível. Estado LIVE efetivo atual não deve ser afirmado sem a leitura do Actions. **Primeira prioridade da ETAPA 3: colocar writers legados atrás de um interlock único fail-closed, com rollback, testes e preservação de rascunhos, sem promover LIVE.**

## Próxima etapa autorizável
**ETAPA 3** somente após o proprietário confirmar a continuação: corrigir prompt+normalizador+gate+CTA+SEO+classificação/workflow legado, com testes offline/regressões e pipeline controlado DRAFT; não reescrever artigos sem autorização específica. Em seguida Etapa 4 com 10 artigos priorizados para revisão, sem publicar massivamente.

**Mutação WordPress nesta conversa:** somente header C112 descrito acima. **ETAPA 2:** READ-ONLY / documentos versionados no GitHub; sem posts, Cron, config, credenciais ou API Shopee alterados.
