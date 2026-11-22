# V31 C82 — Cadeira Certa no Home Office: auditoria, links e novo rascunho (22/11/2026)

**Site:** https://cadeira-certa-home-office.blogspot.com/ · Blogger ID `7163624325768776034`  
**Pré-mutação:** [CHECKPOINT_C82_CADEIRA_CERTA_PRE_MUTACAO_2026-11-22.md](CHECKPOINT_C82_CADEIRA_CERTA_PRE_MUTACAO_2026-11-22.md).  
**Escopo:** correção pontual de blog; não mudar políticas de LIVE automático V31.

## Diagnóstico confirmado
1. Blogger API autenticada + Firecrawl HTTP 200 em 22/11: Tok Boxbit, ID `3691939235338797956`, já estava **LIVE** e seu permalink público funcionava. A homepage mostra esse artigo na seção **Postagens**; o carrossel destacado de 4 itens mostra outros textos, e portanto o destaque do Tok não foi corrigido na configuração do tema.
2. Quatro outros posts publicados tinham fotografias ilustrativas Wikimedia sem link a produto real Shopee. Foram preservadas as atribuições/ilustrações.
3. O post Tok já continha a fotografia `https://cf.shopee.com.br/file/br-11134207-7r98o-lyavzvonlrx140` e o link comercial `https://s.shopee.com.br/9V331snAKH`, declarando origem na Shopee Affiliate API. Esta rodada **reutilizou a URL pré-existente para o mesmo modelo**; não houve nova autenticação de checkout/SubID, conversão ou avaliação de estoque.

## Correções LIVE efetivadas via API Blogger e verificadas via GET
Quatro textos ganharam secções **diferentes por intenção de busca**, com link interno para o guia Tok, foto do **mesmo anúncio** Tok Boxbit, CTA `rel="nofollow sponsored noopener noreferrer"` à URL preexistente, aviso comercial e orientações de checagem de medidas e regulagens:
- `4636680511643933177` — Como escolher uma cadeira ergonômica para home office: 7 critérios essenciais.
- `5233454304666317388` — Cadeira gamer ou de escritório: como decidir pelo uso e pelas regulagens (Tok é explicitamente identificada como escritório, não gamer).
- `8648967166394388356` — Como comparar ajustes de altura, braços e apoio lombar de uma cadeira.
- `7516498952063951593` — Cadeira mesh ou estofada: qual material escolher para trabalhar em casa?

Todos os quatro permanecem `status=live` no GET e contêm `data-v31-commercial-example="tokboxbit-20261122"`. Conteúdo comercial não afirma preço/cupom/frete ou desempenho não verificado.

A página Loja `5014986967420563988` foi reescrita para apresentar 1 modelo real já documentado no blog, foto correspondente, link afiliado preexistente e quatro guias internos; mantidos os marcadores de atualização do sistema. GET confirmado `status=live`. O bloco “Vitrine” do **tema na homepage** é independente da página Loja e ainda pode exibir mensagem “Nenhum produto disponível”; não afirmar que o widget do tema foi populado.

## Novo artigo: produto Shopee diferente
Foi criado **um rascunho, não LIVE**:
- Blogger DRAFT ID `6656620121237912250`
- Título `Cadeira Office Arco mesh e estofada: 9 pontos para avaliar antes de comprar`
- Produto Shopee: `Cadeira Escritório Giratória Office Arco Estofado Mesh`
- URL original pública específica: `https://shopee.com.br/Cadeira-Escrit%C3%B3rio-Girat%C3%B3ria-Office-Arco-Estofado-Mesh-i.1231183958.58216389111`; shopId `1231183958`, itemId `58216389111`.
- Foto principal oriunda da **mesma página original** (`https://down-br.img.susercontent.com/file/sg-11134201-825bc-ms0en6j61b0ibc`), identificada por referência de imagem do anúncio web.
- Mais de 8.000 caracteres, 9 pontos de comparação, FAQ, links internos e transparência. Sem preços fixos nem afirmações não comprovadas de capacidade/ergonomia. Origem do anúncio indexada pela ferramenta Web, mas Shopee pode exigir login para consulta direta posterior.
- **Conversão Shopee desta campanha NÃO REALIZADA**. O rascunho distingue o link de referência ao anúncio de um CTA afiliado. **Não publicar LIVE antes de obter shortLink oficial desta conta para o shop/item exatos, validar imagem e oferta e completar revisão editorial**. Não reutilizar shortLink Tok para Office Arco.
- O cadastro V31 não tem rota específica nem campanha oficialmente verificada para Cadeira Certa, e o conector deste chat não possui execução de `workflow_dispatch` ou segredo da Shopee. **Não inventar um subID/campanha como se validado**. Uma futura conversão deve registrar rota real com campanha autorizada e usar o conversor existente, sob quota/idempotência.

## Verificação final
- GET autenticado de 4/4 posts corrigidos: status LIVE, imagem Tok, link afiliado e marcador exclusivos presentes.
- GET da página Loja: LIVE com novo conteúdo comercial.
- GET do post Office Arco: DRAFT, título e link original específicos.
- `list_published_posts`: **5 LIVE**; `list_drafts`: **1 DRAFT**. Nenhuma alteração de status nos anteriores; `publish_post` não chamado.
- Zero writes em R2/D1/Shopee API; zero alterações em workflows, autolive, outros blogs ou segredos.

## Pendências remanescentes
1. Converter **Office Arco** para a campanha correta via API Shopee autenticada; inserir shortLink idêntico ao SKU no DRAFT e verificar GET/HTML; só então considerar publicação após gate LIVE.
2. A promoção Tok no carrossel depende do código/gadget do tema, não apenas da API de post; o post está acessível na listagem de Postagens e passa a receber quatro links internos.
3. O bloco da homepage “Loja”/vitrine é independente da página `/p/loja.html`. Ainda pode exigir configuração do widget/tema e um inventário válido da campanha para popular automaticamente.
4. Medir desempenho de cliques, Search Console e indexação quando dados autorizados estiverem acessíveis; não inventar métricas.

## Complemento: registro SAFE da rota editorial
- `affiliate_hub_v31/sites.d/blogger_cadeira_certa_home_office.json` criado na `main` com Blogger ID real `7163624325768776034`, site_key `blogger_cadeira_certa_home_office`, nicho `casa/moveis`, path `home living/furniture`, `publish_enabled=false`.
- Nome reservado de rastreamento para **novas conversões futuras**: `cadeiracertahomeoffice`. Trata-se de valor administrativo de subID da rota **ainda não validado por chamada de conversão na API**; não afirmar que a URL histórica Tok já usa esse subID.
- Sem `site_requests.d` habilitado e sem `autonomous_review_sources.json` para essa rota: portanto nenhuma seleção/escrita automática C81 foi ligada para o blog.
- Para obter CTA do Office Arco, aplicar conversor a produto aprovado de identidade exata `shopee:1231183958:58216389111`, sem converter automaticamente outro SKU. Se ausente ou REVIEW no catálogo, interromper e registrar fila de curadoria. Só depois atualizar o DRAFT com link real da mesma campanha.

## Complemento SEO com validação GET (22/11)
Três artigos originalmente muito curtos foram expandidos com blocos editoriais independentes e orientados à intenção de busca, sem promessas técnicas inventadas:
- Gamer versus escritório `5233454304666317388`: uso real, mecanismos, apoio lombar, perguntas frequentes e link ao guia de ajustes.
- Ajustes `8648967166394388356`: método de comparação de dimensões, sequência de inspeção, FAQ e link a materiais.
- Mesh versus estofado `7516498952063951593`: ventilação, manutenção, durabilidade e FAQ, link ao guia de sete critérios.
A releitura Blogger GET confirmou em 3/3 os marcadores `data-v31-seo-expansion="20261122"`, manutenção do CTA comercial do Tok e `status=live`. Novo DRAFT Office Arco permaneceu `status=draft` e seu SKU não foi trocado.

Verificação pública adicional com Firecrawl em `/2026/11/como-comparar-ajustes-de-altura-bracos.html` retornou HTTP 200, CTA e URL pré-existente de afiliado Tok Boxbit no texto efetivamente servido ao público. Esta validação NÃO comprova checkout ou comissão do shortLink.
