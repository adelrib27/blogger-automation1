# C83 — Cadeira Certa — consulta autenticada à API Shopee (22/11/2026)

## Objetivo e isolamento
Concluir a conversão afiliada para um novo SKU da Cadeira Certa sem comprometer o V31 global, D1, R2 ou a política LIVE ainda desativada. Produto do Blogger DRAFT `6656620121237912250`, URL https://cadeira-certa-home-office.blogspot.com/.

## Evidência C83, primeiro gate
- [GitHub Actions #45040964757](https://github.com/adelrib27/blogger-automation1/actions/runs/45040964757) **success** (GitHub environment `v31-editorial-safe`) com `productOfferV2(itemId:58216389111,page:1,limit:5)`.
- API oficial retornou **um item exato** `shopId=1231183958`, `itemId=58216389111`, `productName="Cadeira Escritório Giratória Office Arco Estofado Mesh"`.
- `productLink=https://shopee.com.br/product/1231183958/58216389111`.
- `imageUrl=https://cf.shopee.com.br/file/sg-11134201-825bc-ms0en6j61b0ibc`.
- `offerLink` disponível da própria conta API, confirmando oferta afiliada; não se presume que esse link contém o subID da campanha do blog.
- Consulta C83 leu informação Shopee, **não gerou URL**, `WRITES=0`, credenciais mascaradas nos logs.
- Cloudflare D1 oficial SELECT dos slots de 21–22/11: último uso registrado em 21/11, três slots globais; nenhum uso 22/11 no momento de leitura (não prova que não haja writers futuros).

## Regra da conversão controlada
- Rota cadastrada: `blogger_cadeira_certa_home_office`, campanha `cadeiracertahomeoffice`, `publish_enabled=false`. SubID normalizado pela biblioteca `converter.valid_campaign`.
- Um workflow excepcional deve **reconsultar a API por IDs exatos**, reivindicar um dos até 3 slots globais UTC no D1 oficial de forma idempotente e, apenas se confirmado, chamar `converter.generate_shortlink` com `originUrl` produto correto e `subIds` da campanha.
- Printar **apenas** URL afiliada resultante, SKU, título e foto pública do anúncio; nunca segredos.
- Na falha de quota, source, secret, API ou ambiguidade, sem re-tentativa automática de mutation.
- Após receber shortlink válido, trocar no Blogger DRAFT somente link original por CTA afiliado, foto pela imagem retornada oficialmente se necessário, manter status draft; só publicar manualmente após GET e validação editorial.
- Nenhum LIVE automático será ligado. Carrossel da home é questão de tema independente.

## HTML da home
- HTML público recuperado em 22/11 confirmou carrossel **`ub-v21-featured`** com quatro artigos diferentes e, em outra seção, widget nativo **`FeaturedPost1`** com Tok Boxbit. O post é LIVE, servido com URL correta, mas não há edição de template pelo conector Blogger API. Não alterar data/post ou duplicar.
