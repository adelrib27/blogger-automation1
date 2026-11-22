# V31 C92 — Ar-Condicionado sem Dúvidas: dois artigos e proteção contra produtos esgotados (22/11/2026)

**Blog:** https://ar-condicionado-sem-duvidas.blogspot.com/ — Blogger `2228849984262880811`. **LIVE automático V31 OFF**, publicações individuais autorizadas pelo usuário.

## Diagnóstico anterior à publicação
- BLOGGER API: **1 post LIVE** (LG ID `940950273343255024`), **0 DRAFTs**, 10 páginas LIVE.
- Shopee Affiliate API no ambiente `v31-editorial-safe`: consulta READ ONLY [Actions #45056107732](https://github.com/adelrib27/blogger-automation1/actions/runs/45056107732) retornou Midea `1736335904:58212764417` como oferta com `priceMin>0`, mas **página pública Shopee desse item indicou "esgotado"**. Portanto foi rejeitado. Essa divergência comprova que `productOfferV2` NÃO garante estoque.
- O mesmo problema apareceu no LG previamente divulgado: página pública `https://shopee.com.br/product/822103155/58265302556` exibiu **esgotado** (consulta pública em 22/11), apesar da API retornar oferta; não deixar CTA antigo por hábito.
- Tentativa pública de consulta de estoque granular `/api/v4/item/get` para três SKUs: HTTP 403 de Shopee; nenhuma unidade/variante foi confirmada. Não alegar estoque em tempo real.
- Consulta adicional autenticada READ ONLY [Actions #45056223307](https://github.com/adelrib27/blogger-automation1/actions/runs/45056223307), com IDs exatos, confirmou **duas ofertas distintas**, com foto e `offerLink` da conta:
  - Midea Lite Conectado Inverter 9.000 BTUs Frio: `shopee:1736335904:58267891881`, `imageUrl=https://cf.shopee.com.br/file/sg-11134201-825bc-mvq6z1k87i8a0e`, `offerLink=https://s.shopee.com.br/2VtV2Ew9rt`.
  - Midea AI Ecomaster Inverter 12.000 BTUs Frio 220V: `shopee:889973435:18398298625`, `imageUrl=https://cf.shopee.com.br/file/sg-11134201-7rdwv-mctkguzbqfro18`, `offerLink=https://s.shopee.com.br/5fqWo3kaGX`.
- As páginas Shopee públicas indexadas de ambos **não exibiam mensagem "esgotado"** no texto consultado, mas a indexação poderia ter atraso. Preço da API positivo e validade da oferta NÃO equivalem a estoque confirmado. Textos e Loja informam essa limitação.

## Conversões e orçamento global
- Em 22/11, D1 quota global tinha slot 1 Cadeira Certa, slot 2 LG ArCond. Outro workflow independente do V31 consumiu **slot 3** para Móveis para Cada Canto (`shopee:1235923910:18799312789`).
- A primeira tentativa de workflow C92 de conversão exclusiva da Midea9k [#45056315766](https://github.com/adelrib27/blogger-automation1/actions/runs/45056315766) falhou em **syntax check Python antes de qualquer API/D1**; corrigida no source.
- Após corrigir, workflow [#45056354935](https://github.com/adelrib27/blogger-automation1/actions/runs/45056354935) confirmou identidade de SKU mas parou no gate `C92_MIDEA_GLOBAL_QUOTA_OR_DUP_DENIED` por cota global cheia, **sem executar `generateShortLink`** e sem gravar nova reserva.
- Os dois artigos utilizam **somente `offerLink` oficial retornado pela Shopee Affiliate API da conta do usuário**, não shortlinks inventados. Esses links podem **não conter o SubID específico `arcondicionadosemduvidas`**; para mensuração precisa será necessária conversão futura com nova cota e dedupe, somente se autorizada. Não alegar conversão específica C92.
- Nenhuma conversão duplicada do LG; nenhuma quebra do D1.

## Blogger: dois artigos novos, escritos e publicados
1. **Midea Lite Conectado Inverter 9.000 BTUs: o que conferir antes de comprar** — Blogger ID `8208866544157240159`, URL https://ar-condicionado-sem-duvidas.blogspot.com/2026/11/midea-lite-conectado-inverter-9000-btus.html
   - API item `1736335904:58267891881`, link `https://s.shopee.com.br/2VtV2Ew9rt`; imagem exata. Conteúdo ~10k HTML chars, SEO por intenção de busca: 9k e carga térmica, inverter, conectividade não presumida, tensão, instalação, ENCE/Inmetro PBE, FAQ/checklist.
2. **Midea AI Ecomaster Inverter 12.000 BTUs Frio 220 V: 9 cuidados na compra** — Blogger ID `8847875310080419457`, URL https://ar-condicionado-sem-duvidas.blogspot.com/2026/11/midea-ai-ecomaster-inverter-12000-btus.html
   - API item `889973435:18398298625`, link `https://s.shopee.com.br/5fqWo3kaGX`; foto exata. Conteúdo ~10k HTML chars, critérios diferentes: 220V, seleção de variante, etiqueta ENCE, conjunto de unidades, instalação, garantia, FAQ/checklist.
- Ambos criados como DRAFT, revisados por `get_post` para status, SKU, foto, aviso de estoque incerto, link patrocinado `rel="nofollow sponsored noopener noreferrer"`, Inmetro e links internos; depois `publish_post` manual individual HTTP 200, status LIVE. Os dois foram editados mais uma vez somente para inserir links internos cruzados, mantendo LIVE.
- Browser público Firecrawl `maxAge=0`: HTTP 200 em ambos, títulos, fotos e links Shopee oficiais presentes. Não afirmar características ausentes da API.

## Correção de oferta esgotada LG e Loja
- Artigo LG original `940950273343255024` permanece LIVE e conserva texto educativo e imagem, mas foram retirados **ambos links afiliados** do SKU esgotado. Inserida seção `data-v31-stock-state="soldout-public-listing"` com aviso datado e link para a Loja. Atualização Blogger API HTTP 200 e GET público HTTP 200 confirmado: shortlink antigo `8fU8IIYmXO` não aparece.
- Página Loja existente `4814998680660659640`: removido cartão LG e todo CTA afiliado daquele anúncio. Passou a conter **dois cartões** `ub-product-card` com fotos, links próprios, links aos artigos e avisos explícitos de estoque não garantido. Preservou menus institucionais e fontes Inmetro. API HTTP 200, status LIVE.
- Verificação pública Firecrawl `maxAge=0` em `/p/loja.html`: HTTP 200, **2 cartões** e **ambos links** oficiais, nenhum link antigo LG.
- O tema C91 agora monta um carrossel de **dois slides**; no browser público surgem controles Anterior/Próximo, Pausar e Compartilhar, além dos cartões. A navegação multi-slide merece validação visual mais detalhada se surgir regressão; não foi preciso editar XML nesta execução.

## Guardas incorporados
- Documento [POLITICA_ESTOQUE_SHOPEE_ARCOND_C92_2026-11-22.md](POLITICA_ESTOQUE_SHOPEE_ARCOND_C92_2026-11-22.md) com estados ESGOTADO_CONFIRMADO, SEM_ALERTA_ESGOTAMENTO_MAS_ESTOQUE_NAO_COMPROVADO e INDETERMINADO, regras de remoção do CTA e verificação de modelo/variante.
- Nenhum preço fixo, promessa de desconto/estoque ou classe ENCE inventada; sem alteração nos slugs, posts de outros blogs, autoLIVE, cloudflare R2 ou política C81.
- Fontes: Inmetro PBE https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/condicionadores-de-ar/sistema-pbe-para-consulta-dos-produtos-etiquetados ; Shopee Affiliate API autenticada; páginas públicas de anúncios.

**Estado esperado ao final:** 3 posts LIVE, 0 DRAFT, 10 páginas LIVE. Necessário confirmar por nova listagem Blogger e atualizar estado persistente. `V31_AUTOLIVE_ACTIVE` segue OFF.

## Verificação final autenticada após todas as mutações — C92
Blogger V2 `list_published_posts=3` com IDs LG `940950273343255024`, Midea9k `8208866544157240159` e Midea12k `8847875310080419457`; `list_drafts=0`; `list_pages=10`. `get_post` em ambos os Midea retornou `status=live` e o respectivo `offerLink` da Shopee API; `get_post` do LG retornou `status=live`, nota de esgotamento e **ausência do shortlink comercial antigo**. `get_page` da Loja retornou `status=live`, **dois cartões**, ambos os links Midea e nenhum shortlink LG. Browser público: homepage, Loja, LG e ambos posts Midea HTTP 200; links e imagens íntegros. **C92 encerrada sem rascunhos pendentes.**
