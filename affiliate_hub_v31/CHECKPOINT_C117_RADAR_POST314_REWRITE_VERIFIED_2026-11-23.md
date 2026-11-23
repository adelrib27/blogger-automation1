# V31 Radar Tech BR — C117: segundo artigo reescrito e homologado na URL original

**Data:** 23/11/2026 (America/Recife). **Status:** post ID **314** atualizado e conferido, sem ativar automações.  
**URL original e atual:** https://radartechbr.com.br/escolhendo-o-melhor-ventilador-para-o-verao/

## Proteção do estado anterior
- Backup integral ANTES da edição: `affiliate_hub_v31/backups/C117_RADAR_WP_POST_314_BEFORE_REWRITE_2026-11-23.json`, commit `ab692bbf9ec36ad818b632ae6b755d276ee744a0`. HTML completo, title, excerpt, categoria, tags, imagem, AIOSEO meta, links, slug, timestamps.
- Antes de escrever, reconsulta API `wp_get_post_full(context=edit)` confirmou o HTML e a meta de backup, título original, slug, status publish, categoria [1], featured_media 315, `modified=2026-11-19T19:58:50`; todos os guards passaram.
- Link comercial ORIGINAL `https://s.shopee.com.br/4LL4SMJ3eI` resolvido no redirecionamento Shopee para `/product/811879342/22197514607` com `mmp_pid=an_18352820579`. A Shopee exigiu login e bloqueou verificação plena de estoque/preço e SKU da variante. **Nenhum valor corrente inserido**.
- Identidade do modelo AVTE01 também conferida no catálogo da fabricante `https://www.britania.com.br/ventilador-de-mesa-prime-air-60w-avte01/p` e no anúncio público Shopee ID22197514607. **60W e 6 pás no nome**, tensão variável (127V/220V) informada pelo fabricante; jamais afirmar bivolt ou etiquetagem específica não comprovada. Diretriz sobre certificação via Inmetro `https://www.gov.br/inmetro/pt-br/acesso-a-informacao/perguntas-frequentes/avaliacao-da-conformidade/ventiladores-de-mesa/se-um-ventiladores-de-mesa-parede-pedestal-ou-circuladores-de-ar-nao-possui-certificacao-ou-nao-ostenta-a-etiqueta-pbe-e-esta-sendo-comercializado-em-territorio-nacional-ele-esta-irregular`.

## Resultado
- Prévia integral: `affiliate_hub_v31/previews/C117_RADAR_WP_POST_314_REWRITE_CANDIDATE_2026-11-23.json` commit `0945070a30e28136b8bc575bb1e081c39b3841be`.
- **Título:** Ventilador de mesa: como escolher sem errar (43 caracteres).
- **AIOSEO meta / excerpt:** 143 caracteres, sem linguagem de prompt; focus_keyphrase `como escolher ventilador de mesa`.
- **HTML:** aproximadamente 1.302 palavras, 7 H2, 1 cartão Shopee, 2 âncoras com `rel="nofollow sponsored"`, 1 imagem de produto real, 1 disclosure, links internos para Guias de Compra Tecnologia e Ar-condicionado (como comparativo de equipamentos, sem indicar que ventilador seja ar-condicionado), fontes de fabricante e Inmetro.
- **Mudança consciente de categoria:** de Guias de Compra ID1 para **Tecnologia ID3**, mantendo slug, URL, ID314 e **featured_media ID315**. Não criar nem atribuir categoria `Ar-condicionado` ID20 para ventilador comum.
- `wp_update_post` finalizado às **15:09:07**; WordPress retornou `status=publish` e a mesma URL.
- `seo-data-update` confirmou title, descrição e focus_keyword novos; AIOSEO `robots.noindex=false`, canonical por padrão. Score AIOSEO permaneceu 0, sem alegação de tráfego.
- Leitura API pós-escrita: **HTML byte-exato igual** à prévia, excerpt/title idem, categoria Tecnologia, imagem destacada e slug preservados, 1 cartão e 2 links afiliados. Firecrawl `maxAge=0` do HTML público retornou HTTP 200 com novo título, link original, fontes e 1 CTA; texto antigo “O leitor precisa...” não apareceu.

## Estado e próximos passos
- Já concluídos nesta Etapa 4: **C116 post #260 smartwatch** e **C117 post #314 ventilador**. Não reescrever ambos novamente ao retomar.
- Restam 8 candidatos C115: **#29, #311, #278, #28, #256, #25, #138, #24**. Qualquer edição requer seu próprio backup, link/produto/variante conferidos e revalidação WP do `modified`. Os posts de ofertas sem link afiliado no HTML **não recebem URLs inventadas**.
- Segurança: LIVE automático legado permanece OFF, workflow `if: false`; reescrita foi edição manual explícita de post existente. V31 universal ainda com oito testes antigos de fixtures para reconciliação independente.

**Código de retomada:** `V31-RADAR-C117-20261123-POST314-LIVE-EDIT-VERIFIED`.
