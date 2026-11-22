# V31 C83 — Cadeira Certa no Home Office: API Shopee, artigo LIVE e carrossel (22/11/2026)

**Estado: CONCLUÍDO nas duas pendências solicitadas.**  
Blog: https://cadeira-certa-home-office.blogspot.com/ · Blogger ID `7163624325768776034`.  
Escopo: uma publicação MANUAL e específica, sem ativar política LIVE automática V31, nem alterar template do Blogger.

## Pendência 1 — carrossel nativo
- Diagnóstico inicial no HTML público: o tema tem **dois mecanismos distintos**: `#ub-v21-featured` e o widget Blogger nativo `FeaturedPost1`. Antes da nova publicação, o Tok Boxbit era o `FeaturedPost1` e o carrossel tinha quatro artigos diferentes.
- Depois da publicação manual da Office Arco, **o próprio tema fez a rotação nativa**: `FeaturedPost1` passou a destacar Office Arco (ID `6656620121237912250`) e o carrossel `#ub-v21-featured` passou a listar **cinco artigos**, com **Tok Boxbit em PRIMEIRO slide** e link para a URL original:
  https://cadeira-certa-home-office.blogspot.com/2026/11/cadeira-mesh-giratoria-com-assento.html
- Leitura pública `Firecrawl` após publicação: HTTP 200, cinco títulos extraídos do HTML do carrossel; `Tok Boxbit` está na posição 1/5. `FeaturedPost1` tem `post-6656620121237912250` com Office Arco.
- **Zero alterações no tema/layout/carrossel**, zero cópias do artigo, zero mudanças artificiais de datas, URLs ou marcadores. A mudança da seleção decorre do funcionamento nativo com mais um post.
- Observação: futuras postagens podem naturalmente rotacionar os cinco slides; preservar a lógica dinâmica do template, sem fixar artificialmente um SKU.

## Pendência 2 — produto pela API Shopee (dois gates)
1. [GitHub Actions C83 #45040964757](https://github.com/adelrib27/blogger-automation1/actions/runs/45040964757) **SUCCESS, READ ONLY** — consulta autenticada `productOfferV2(itemId:58216389111)` retornou exatamente uma oferta:
   - `shopId=1231183958`, `itemId=58216389111`
   - `productName=Cadeira Escritório Giratória Office Arco Estofado Mesh`
   - `productLink=https://shopee.com.br/product/1231183958/58216389111`
   - `imageUrl=https://cf.shopee.com.br/file/sg-11134201-825bc-ms0en6j61b0ibc`
   - `offerLink` afiliado da conta retornado; não substitui campanha específica.
2. [GitHub Actions C83 #45041101197](https://github.com/adelrib27/blogger-automation1/actions/runs/45041101197) **SUCCESS, mutation única**: reconsultou o mesmo item, conferiu IDs/nome/imagem/link de origem, reservou **slot 1 de 22/11/2026** no D1 oficial `v31_shopee_conversion_attempts`, e gerou link na `generateShortLink` por `affiliate_hub_v31.converter.generate_shortlink` com campanha `cadeiracertahomeoffice`:
   - **Shortlink oficial:** https://s.shopee.com.br/9fMfOM4016
   - **Product key:** `shopee:1231183958:58216389111`
   - **Campanha:** `cadeiracertahomeoffice` (subID normalizado pela biblioteca).
   - Sem retry automático, sem segunda mutation, sem impressão de secrets.
   - **D1 SELECT posterior** confirmou uma única linha `(day_utc=2026-11-22, slot=1, campaign=cadeiracertahomeoffice, product_key=shopee:1231183958:58216389111)`. Sem alteração de R2.
3. Blogger DRAFT ID `6656620121237912250` recebeu imagem original do produto **retornada pela API**, CTA `rel="nofollow sponsored noopener noreferrer"` apontando para o shortlink oficial, disclaimer de afiliados, referência a SKU exato e links internos. Removida expressão antiga “não convertido em afiliado”. GET autenticado confirmou todos os invariantes, status DRAFT antes do release.
4. `publish_post` individual com `request_id=v31_c83_office_arco_manual_publish_20261122` retornou HTTP 200, status LIVE:
   - Título: **Cadeira Office Arco mesh e estofada: 9 pontos para avaliar antes de comprar**
   - Blogger ID: `6656620121237912250`
   - URL: https://cadeira-certa-home-office.blogspot.com/2026/11/cadeira-office-arco-mesh-e-estofada-9.html
5. GET autenticado posterior e GET público Firecrawl HTTP 200 confirmaram título, estado LIVE e shortlink presente na página. Blogger `list_published_posts=6`, `list_drafts=0`.

## Situação e salvaguardas
- **As duas pendências C83 estão comprovadas como resolvidas.** O primeiro slide da Tok aparece na HOME, e Office Arco tem URL afiliada oficial e artigo publicado.
- `V31_AUTOLIVE_ACTIVE` não foi habilitado. O writer autônomo, a assinatura C81 e o rollout somente Blogger Móveis não foram alterados. Nada foi publicado para outros blogs.
- Workflows C83 possuem gatilhos restritos a **push do próprio arquivo de workflow**, sem `schedule` ou `workflow_dispatch`. D1 impede replay da mesma campanha/SKU. Não reenviar o mesmo workflow para provocar conversão repetida.
- Novo blog já tem rota `affiliate_hub_v31/sites.d/blogger_cadeira_certa_home_office.json`, com `publish_enabled=false`. Não habilitar cron de escrita para esse blog sem homologação de fontes e planejamento.
- O carrossel é dinâmico: quando surgir artigo novo, a posição da Tok pode mudar naturalmente. Não promover mudanças artificiais.
