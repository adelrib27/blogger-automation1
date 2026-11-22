# V31 C89 — Ar-Condicionado sem Dúvidas: FeaturedPost duplicado + fontes institucionais (22/11/2026)

## Escopo e diagnóstico CONFIRMADO (HTML público LIVE)
Blog https://ar-condicionado-sem-duvidas.blogspot.com/ (Blogger ID `2228849984262880811`). Proprietário enviou captura da HOME mostrando **três apresentações do mesmo artigo**: 1 slide no carrossel personalizado, 1 cartão padrão na grade e 1 exibição indevida do conteúdo completo com foto enorme abaixo da grade.

`Firecrawl rawHtml` público (HTTP 200, `maxAge=0`) comprovou:
- `#Blog1` inclui o post LIVE `940950273343255024` LG Dual Inverter, e o carrossel já consome `#Blog1 .post-wrapper`;
- **o HTML normalizado pelo Blogger reinseriu `div.widget.FeaturedPost#FeaturedPost1` DEPOIS de `Blog1`**, mesmo que o XML C87 original NÃO contivesse `FeaturedPost1` nem seção `featured_post`;
- `FeaturedPost1` reproduz o post LG no DOM, causando a duplicação visual.
- Não é falha de imagem nem de feed. NÃO republicar, duplicar ou alterar o artigo (e sua URL afiliada `https://s.shopee.com.br/8fU8IIYmXO`).

## Artefato XML C89 preparado (NÃO INSTALADO ainda)
Partida da base exata `TEMA_EXCLUSIVO_AR_CONDICIONADO_SEM_DUVIDAS_V31_C87.xml` já entregue no chat C87 (SHA256 `6d0bcab7cfc84c912ffac0dd8b187717b5258738434c447f88960354ac465019`, 216.894 bytes).

**Modificação em UM bloco XML somente:** no ponto em que C87 removera o widget, C89 acrescentou explicitamente seção `id=featured_post` contendo `<b:widget id='FeaturedPost1' type='FeaturedPost' visible='false'>` e `useMostRecentPost=false`, com `main` vazio. É a desativação nativa do widget, não uma regra CSS para esconder o resultado. Objetivo: preservar a identidade do widget no modelo para que o Blogger deixe de anexá-lo automaticamente e, estando `visible=false`, deixe de excluí-lo da listagem principal (`data:widgets` não inclui widgets invisíveis, conforme referência técnica de Blogger XML https://blogger.fineshop.app/docs/theme-xml/data/widgets).

- Carrossel `#ub-v21-featured` e seletor `#Blog1 .post-wrapper` preservados, 5 slots máximos; 12 postagens da HOME continuam controladas pelo Blogger.
- `Blog1` único; todos os 12 IDs anteriores de widgets mantidos; novo arquivo contém 13 IDs incluindo o gadget legado desativado.
- Sem qualquer mudança em marca visual C87, hero, CSS, JS, navegação, Loja, posts, D1, R2, campanha Shopee, cron ou LIVE automático.
- XML `lxml` estrito PASS; `node --check` em 5 blocos JS PASS; diff é uma única região.
- **Arquivo entregue neste chat:** `TEMA_EXCLUSIVO_AR_CONDICIONADO_SEM_DUVIDAS_V31_C89_SEM_POST_DUPLICADO.xml`.
- SHA256 C89 `7638ca1759f6523fb083f0c73bb22d2870d3c9f41909c727976460d0a06a5281` (217.819 bytes); TXT de cópia, diff, backup da fonte C87, manifesto JSON e relatório local acompanham.
- O GitHub contém [patch textual exato](../blogger_themes/patches/C89_AR_CONDICIONADO_DUPLICACAO_FEATUREDPOST.xml.patch) e este checkpoint; **não afirmar que o XML completo de 217KB foi commitado** — ele está como artefato do chat.

**Status C89 do TEMA: VALIDADO LOCALMENTE, `live_installed=false`.** A credencial Blogger disponível via bridge permite Posts/Pages, mas não editar o HTML do tema para este blog. Não chamar o Runner `adopt_model_v31_exact` porque sua allowlist se refere a outros blogs LAB. O proprietário deve fazer backup no Blogger, instalar XML C89 em Tema → Editar HTML e salvar; então validar HTTP público: `#Blog1` 1 post, `#ub-v21-featured` 1 slide, **sem 3º bloco longo e sem widget FeaturedPost1 visível**. Se o Blogger continuar migrando o widget, coletar XML normalizado após salvar; não usar CSS hack nem alegar deploy bem-sucedido sem prova.

## Seis páginas de menu: ATUALIZADAS e verificadas sem duplicar
As seis páginas LIVE C88 já existiam no blog. Foram atualizadas via `Blogger_Bridge_V2__get_page` + `update_page`, com request_ids C89 individuais e marcador `data-v31-c89-sources="20261122"`, mantendo os mesmos IDs e slugs:
- `Sobre` `8479275003826990437` → `/p/sobre.html`: referência Inmetro e método de análise.
- `Loja` `4814998680660659640` → `/p/loja.html`: link ao anúncio original LG e Sistema PBE/Inmetro; CTA afiliado já existente preservado.
- `Contato` `1229660535318855287` → `/p/contato.html`: fonte oficial da Ajuda Blogger sobre comentários, alerta para não usar comentários para dados privados. Nenhum e-mail, formulário ou destinatário inventado.
- `Política de Privacidade` `3365012459566429524` → `/p/politica-de-privacidade.html`: Google Privacy + Ajuda Blogger; sem alegar que já usa Analytics/Ads.
- `Termos de Uso` `2885404980077440157` → `/p/termos-de-uso.html`: ajuda Blogger + Inmetro; sem inventar garantias ou aconselhamento técnico-jurídico.
- `Aviso de Afiliados` `5684981871851687539` → `/p/aviso-de-afiliados.html`: identificação Shopee (produto LG) + PBE, discriminação comercial original.
- Revisão autenticada Blogger GET **6/6 status LIVE**, marcador presente e HTML original preservado. Ao consultar URLs públicas, **Sobre, Loja e Aviso** tinham marcador e fonte externa com HTTP 200; **Contato respondeu HTTP 200, mas o primeiro scrape não exibia ainda o marcador atualizado** (possível cache); não afirmar homologação HTML pública plena de 6/6 sem revalidar. Loja preserva shortlink `https://s.shopee.com.br/8fU8IIYmXO`.
- As fontes referenciadas foram verificadas via busca externa: Inmetro PBE, suporte oficial Blogger e Google Privacy. Textos editoriais são originais, sem reproduções extensas. Política jurídica não foi submetida a análise formal por advogado.

## Gate final recomendado para próxima interação
1. Proprietário instala C89 e manda captura HOME; auditoria publica confirma ausência do 3º bloco, correto carrossel, grade, SEO, fontes e imagem.
2. Conferir exibição nos dispositivos móveis e página interna do artigo; 1 post LIVE, 0 DRAFT, 6 páginas LIVE preservados.
3. Evitar qualquer tentativa de reconversão da oferta LG; D1 já registrou slot 2 de 22/11 para `shopee:822103155:58265302556` e campanha `arcondicionadosemduvidas`.
4. `V31_AUTOLIVE_ACTIVE=false` segue — não mexer na política C81 nem outros blogs.
