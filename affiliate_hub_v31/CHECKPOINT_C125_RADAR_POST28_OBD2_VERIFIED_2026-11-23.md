# V31 Radar Tech BR — C125: Scanner OBD2 #28 revisado com oferta de imagem correspondente

**Data:** 23/11/2026 (America/Recife); **status:** revisão manual aplicada e homologada no artigo publicado.  
**WordPress:** post ID 28; permalink original **https://radartechbr.com.br/scanner-obd2-bluetooth-o-que-verificar-antes-de-comprar/**.

## Diagnóstico de origem
- O artigo original **não tinha link Shopee no HTML ou metadados básicos**. Não foi possível recuperar vendedor nem anúncio original.
- C122 [GitHub Actions run 45245173559](https://github.com/adelrib27/blogger-automation1/actions/runs/45245173559): no catálogo R2 1GB da campanha V31, zero correspondências exatas de título/linha para os quatro pendentes e zero links campaign radarwp entre matches.
- C123 [run 45245633827](https://github.com/adelrib27/blogger-automation1/actions/runs/45245633827): pesquisa Shopee Affiliate API READ ONLY, 25 ofertas para OBD2 e 16 para RGB; Arctic e Kapbom tiveram erro transitório GraphQL 10000, que NÃO significa falta de estoque. CSV/artefato de candidatos disponível na run por 7 dias.
- C124 [run 45246247233](https://github.com/adelrib27/blogger-automation1/actions/runs/45246247233): comparação visual com foto WordPress 1024×1024, 20 imagens OBD2 baixadas. Candidato **shop 1712301672, item 58252631500** apresentou hash de imagem `pHash distance=0`, `dHash distance=1`, `aHash distance=0`, único match forte. Esta evidência indica mesma imagem promocional, NÃO garante vendedor original nem hardware/variante idêntico.
- Oferta candidata tem nome comercial `Scanner Automotivo Bluetooth OBD2 Android iOS EML 327 Versao 2.1Mini Scanner Scan Entrega Imediata`. O título menciona iOS, mas **não prova suporte BLE** — o artigo ressalta isso.
- Novo link da API oficial, verificado redirecionamento via Firecrawl: `https://s.shopee.com.br/7VICcLB4oz` → `shopee.com.br/product/1712301672/58252631500`, parâmetro afiliado `mmp_pid=an_18352820579`. Shopee exibiu login/tráfego e não permitiu comprovar preço/estoque/revisão física. **O link é nova oferta relacionada, não recuperação do URL original ou persistência prévia de campanha radarwp na biblioteca R2.** Palavra de campanha lógica do site é `radarwp`; a API retorna conta de afiliado, não comprova etiqueta de campanha isolada.
- Foto do anúncio atual escolhida para CTA: `https://cf.shopee.com.br/file/br-11134207-81ztc-mj0lc5l693ib7f`. Imagem destacada WP original attachment ID72 **preservada**.

## Backup e mudança
- Backup completo antes da gravação: `affiliate_hub_v31/backups/C125_RADAR_WP_POST_28_BEFORE_REWRITE_2026-11-23.json`, commit `cfc65b0fbd35da3e1b23f2b22c0f40da199fa765`. Inclui HTML, SEO, title/excerpt, tags, status, categoria, mídia, datas e permalink.
- Prévia editorial versionada antes de gravar: `affiliate_hub_v31/previews/C125_RADAR_WP_POST_28_REWRITE_CANDIDATE_2026-11-23.json` commit `befa7d1080e059e70c7e699b962692efb1f401a9`.
- Validado imediatamente antes do write: post, `modified=2026-11-23T10:10:04`, título, HTML e excerpt iguais ao backup, categoria Tecnologia ID3, status publish, slug original e imagem destacada ID72 idênticos, CTA um e duas âncoras.
- `wp_update_post` executado no **post existente**, sem alterar URL, slug, status ou featured_media. `modified=2026-11-23T16:14:57`.
- Novo título: **Scanner OBD2 Bluetooth: confira a compatibilidade** (49 caracteres); meta/excerpt 145 caracteres; foco AIOSEO `scanner OBD2 Bluetooth compatibilidade`.
- ~1.347 palavras, 8 H2, 1 cartão com imagem do anúncio, 2 links afiliados da mesma URL com rel `nofollow sponsored`, 1 disclosure, 2 links internos. Fontes explícitas do criador do aplicativo Car Scanner: escolha de adaptador, requisitos de Bluetooth LE no iOS e FAQ; não representam teste do produto Shopee.
- AIOSEO update/readback confirmou title, meta e foco, `robots.noindex=false`; não declarar desempenho Google a partir de TruSEO 0.

## Homologação
1. `wp_get_post_full(context=edit)`: HTML novo **byte-exato** à prévia, título/excerpt idênticos, mesmo permalink/slug/status/categoria/media, 1 CTA e 2 âncoras.
2. Publicação pública Firecrawl maxAge=0: **HTTP 200**, novo título, 1 cartão e link afiliado, fonte Car Scanner, sem parágrafo genérico inicial; sem noindex exposto.
3. A edição é **manual e específica** do post previamente publicado, mediante autorização de seguir a Etapa 4; writer automático LIVE permanece desativado.

## Continuidade
**7/10 concluídos:** #260, #314, #311, #278, #256, #138 e #28. NÃO REEXECUTAR.  
**Pendem:** #29 Arctic (API erro 10000; sem match R2), #25 Kapbom (erro 10000; sem match R2), #24 Luz RGB (16 listagens Shopee, 0 fotos com match forte da imagem original). Sem inserir URLs artificiais.  
V31 universal ainda contém oito falhas históricas de fixtures; isso não foi corrigido neste ciclo.

**Código:** `V31-RADAR-C125-20261123-OBD2-7-DE-10-VALIDADO`.
