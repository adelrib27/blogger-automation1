# V31 — C96: Café na Medida, Loja com 35 ofertas Shopee LIVE

**Data:** 22/11/2026 (America/Recife), atualização Blogger `18:49:10 -03:00`.
**Blog:** https://cafe-na-medida.blogspot.com/
**Loja:** https://cafe-na-medida.blogspot.com/p/loja.html
**Blogger blog ID:** `4820923154548273510`
**Blogger page ID:** `4202100014512520679`
**Status:** **PUBLICADO E VERIFICADO** em página preexistente; ZERO posts/páginas duplicados.

## Pedido e diagnóstico
Proprietário autorizou edição da página Loja e inclusão de ao menos 24 produtos reais Shopee da mesma Affiliate API, dando importância à comissão. A loja tinha quatro cards sem fotos de produto (ícones). O backup original, com 7.256 caracteres, foi salvo **antes** da mudança:
`affiliate_hub_v31/backups/C96_CAFE_NA_MEDIDA_LOJA_PRE_2026-11-22.html`.

## Descoberta READ ONLY na API oficial Shopee Brasil
Conta da API: mesma integração no GitHub Environment `v31-editorial-safe`, variáveis `V31_EDITORIAL_SHOPEE_APP_ID` e `V31_EDITORIAL_SHOPEE_APP_SECRET`. Nenhum valor sensível foi escrito no relatório.

- [C96 execução READ ONLY #45073667091](https://github.com/adelrib27/blogger-automation1/actions/runs/45073667091): 39 candidatos válidos; 19 shortlist após diversidade, filtro rating>=4 e vendas>=10. Erros `10000` transitórios em moedores/chaleiras; não confundir com ausência de produtos.
- [C96b execução READ ONLY #45073821892](https://github.com/adelrib27/blogger-automation1/actions/runs/45073821892): 42 anúncios válidos em consultas complementares, com buscas de relevância e mais categorias. Erros `10000` em alguns termos; coletadas alternativas.
- [C96c execução EXATA #45074004475](https://github.com/adelrib27/blogger-automation1/actions/runs/45074004475): 5/5 itens anteriores/artigo consultados por `productOfferV2(itemId)`; recuperados moedor manual `22494405073`, chaleira elétrica `54557028525` e cafeteira italiana `23898564808` (imagem e link da mesma oferta).
- Seleção final de **35 IDs de anúncios distintos**, **31 vendedores distintos**, **12 categorias**, **35 imagens Shopee exatas**, **35 offerLinks afiliados diferentes**.
- **31 dos 35 produtos** informavam taxa adicional do vendedor de pelo menos 3% na consulta. Taxa e comissão estimada foram usadas SOMENTE para ranking, em conjunto com relevância, avaliações e vendas históricas; não há garantia de venda, atribuição, estoque nem comissão. Nenhuma porcentagem, preço ou projeção financeira foi publicada na Loja.
- A consulta com `offerLink` da mesma conta NÃO comprova SubID específico por blog. Não foi executada a mutation `generateShortLink` nem consumido D1 para conversões; NÃO afirmar campanha exclusiva comprovada.

## Publicação e QA
Arquivo integral preparado/validado antes da edição:
`affiliate_hub_v31/exports/C96_CAFE_NA_MEDIDA_LOJA_35_PRODUTOS_2026-11-22.html` (77.055 caracteres).

1. Releitura Blogger da Loja e comparação BYTE-A-BYTE com backup original antes da única atualização.
2. `Blogger_Bridge_V2.update_page` na mesma `page_id` e com request_id `v31-c96-cafe-loja-35-real-shopee-20261122-01`. Página permaneceu status `live`; permalink original preservado.
3. `Blogger_Bridge_V2.get_page` confirmou **HTML exatamente idêntico** ao export (77.055 caracteres), 35 cards, 35 imagens, 70 ocorrências de links externos (imagem + CTA), **35 URLs diferentes**, 70 `rel="nofollow sponsored noopener noreferrer"` e 12 links internos para guias LIVE do mesmo blog. Nenhum texto técnico de API/SubID/IDs foi exibido.
4. **Verificação pública adicional:** Firecrawl em `https://cafe-na-medida.blogspot.com/p/loja.html`, `maxAge:0`, retornou HTML (113.569 caracteres) com **35 cards**, **70 ocorrências de offerLink**, **35 links diferentes**, hero correto, moedor e chaleira, disclosure. Essa prova verifica conteúdo público, não efetua compras ou testa estoque.

## Regras e rollback
- Fonte fotos: `imageUrl` do `productOfferV2` para o mesmo `shopId:itemId`; destino de cada card: `offerLink` da mesma oferta, domínio Shopee, rel patrocinado. Sem preços ou descontos estáticos.
- Não alterar artigo C94, status do blog, tema C95 já instalado, R2/D1, Pinterest, outras páginas e `V31_AUTOLIVE_ACTIVE=false`.
- Backup anterior no arquivo descrito acima. Em caso de regressão, restaurar **somente** conteúdo da página Loja pelo Blogger API, após confirmar ID e GET atualizado. Não restaurar o tema.
- A atualização não implantou cron de manutenção; a Shop Affiliate API não garante estoque atual e a curadoria deve ser revalidada em ciclos futuros de manutenção.
- Scripts de descoberta READ ONLY: `affiliate_hub_v31/cafe_loja_readonly.py`, `affiliate_hub_v31/cafe_loja_refill_readonly.py`; workflows `v31_c96*` disparam por push no próprio YAML ou manualmente, sem publicação e sem conversão.

**Estado C96: CONCLUÍDO — 35 ofertas reais Shopee na página Loja existente e verificadas no CMS e HTML público.**
