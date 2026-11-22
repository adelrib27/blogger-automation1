# V31 C82 — Cadeira Certa no Home Office, auditoria pré-mutação

Data: 22/11/2026, site Blogger ID `7163624325768776034`, https://cadeira-certa-home-office.blogspot.com/.

## Leitura real
Blogger API v3 confirmou **5 artigos LIVE, zero DRAFT e 6 páginas LIVE**, nenhuma publicação criada neste ciclo.
- Tok Boxbit ID `3691939235338797956` está `live`, permalink https://cadeira-certa-home-office.blogspot.com/2026/11/cadeira-mesh-giratoria-com-assento.html, HTML ~10.779 chars; referência SKU `itemId=11584184781`, foto do anúncio `https://cf.shopee.com.br/file/br-11134207-7r98o-lyavzvonlrx140` e shortlink de afiliado que o próprio artigo já usava `https://s.shopee.com.br/9V331snAKH`, rel nofollow sponsored. O texto declara que veio da Shopee Affiliate API; a consulta presente não reconverteu nem autenticou a campanha antiga.
- Quatro outros artigos (IDs `4636680511643933177`, `5233454304666317388`, `8648967166394388356`, `7516498952063951593`) usam imagens Wikimedia de caráter ilustrativo e não têm links de produtos Shopee.
- Firecrawl scrape público fresco 22/11, status HTTP 200 na homepage, mostrou **Tok no primeiro item da seção “Postagens”**, mas não no carrossel “Post em destaque” (carrossel com quatro outros artigos). Artigo Tok também respondeu HTTP 200 publicamente.
- A homepage contém vitrine “Nenhum produto disponível” e a página `Loja` ID `5014986967420563988` explica que ainda não há links homologados, texto que precisa ser ajustado à evidência real do artigo Tok.
- A coleta pública Shopee não forneceu um novo produto verificável: listagem retornou barreira de login. Não inferir ID, imagem ou link afiliado para outro SKU.
- A rota `Cadeira Certa` NÃO está registrada em `affiliate_hub_v31/site_routes.json` ou `sites.d`, nem na fila de pedidos `site_requests.d`. A criação de um link novo via V31 exige cadastrar blog/campanha corretos, selecionar produto aprovado e conversão Shopee verificada. Evitar usar cache de outra campanha.

## Plano SAFE
1. Acrescentar aos quatro artigos publicados seções **originais e distintas** com exemplo comercial Tok Boxbit, imagem exata do SKU e shortlink existente, CTA `rel="nofollow sponsored noopener noreferrer"`, aviso afiliado e link ao artigo Tok; manter imagens Wikimedia como ilustrações sem afirmar serem do anúncio. Preservar corpo e URLs dos posts.
2. Melhorar a página Loja com referência editorial ao Tok Boxbit e explicação transparente de uma única oferta documentada; não simular vitrine de diversos SKUs, nem preço/estoque.
3. Consolidar artigo Tok como pilar e links internos de todos os guias; verificar GET de cada post e estado `live` preservado; manter todo risco visível.
4. Novo artigo de **produto diferente** somente mediante prova de identidade, origem Shopee, foto do SKU e URL afiliada da campanha correta. Se não puder converter neste ciclo, preparar DRAFT com transparência de pendência, sem inventar CTA.
5. Sem mutação em D1/R2/campanhas, nenhum giro do scheduler, nenhum LIVE novo sem gate individual do V31; salvar evidências/checkpoint após as operações.

## Observações para auditoria
- Falta verificar capacidade de converter produto novo nesta conta: V31 atual registrou apenas Móveis para Cada Canto em `sites.d` e não tem campanha atestada da Cadeira Certa.
- Não confundir ausência no **carrossel** com ausência do post no site; o HTML público inclui o Tok em “Postagens”.
- Não alterar tema por tentativa e erro.
