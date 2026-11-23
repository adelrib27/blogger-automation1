# V31 Radar Tech BR C120 — ventilador portátil USB #256 reescrito e verificado

**Data:** 23/11/2026, **post:** 256, **permalink inalterado:** https://radartechbr.com.br/ventilador-portatil-com-resfriamento-e-iluminacao/

## Backups, fontes e campanha
- Backup anterior a qualquer mutação `affiliate_hub_v31/backups/C120_RADAR_WP_POST_256_BEFORE_REWRITE_2026-11-23.json`, commit `115c2613d5df8d1290cda5648dded1d8534edb01`: HTML raw, título, excerpt, meta AIOSEO, categoria, imagem e datas.
- Antes da escrita, `wp_get_post_full(context=edit)` revalidou `modified=2026-11-23T10:10:27`, HTML/excerpt/title, status, slug, categoria Tecnologia ID3, featured_media257 iguais aos dados do backup. Nenhuma mudança concorrente.
- Link Shopee **inalterado** `https://s.shopee.com.br/6q1tNiARrK` → redireciona a `product/1212157552/26787190586`, PID `an_18352820579`. Shopee exigiu login de navegador, logo **preço/estoque/mecanismo de resfriamento/variante não comprovados**.
- Produto cujo título de anúncio menciona `Mini Ar Condicionado USB com LED – Ventilador Portátil Com Alça | Resfria, Umidifica e Ilumina | Mz`. O texto distingue o título de vendedor de especificação comprovada; **não dizer que o produto é ar-condicionado com compressor nem que possui evaporador sem ficha técnica**.
- Foto original preservada `https://cf.shopee.com.br/file/br-11134207-7r98o-mak3706pyphrf1`; featured_media WordPress 257.
- Fontes explicativas (tecnologia geral): `https://www.energy.gov/home-cooling` e `https://www.energy.gov/cmei/femp/best-management-practice-13-other-water-intensive-processes`.

## Escrita e homologação
- Prévia completa `affiliate_hub_v31/previews/C120_RADAR_WP_POST_256_REWRITE_CANDIDATE_2026-11-23.json` commit `cde28c3bf3c327cee1feaae7b638fd6978abc33c`.
- Novo título **Ventilador portátil com luz: como avaliar** (41 caracteres); meta/excerpt AIOSEO **145 caracteres**, keyword `ventilador portátil com luz`.
- Texto ~**1.309 palavras**, 8 H2, **1** cartão Shopee (2 âncoras da mesma campanha, 1 imagem e 1 disclosure) e links internos para Guias de Tecnologia e categoria Ar-condicionado apenas para **explicar a diferença tecnológica**, sem reclassificar ventilador como AC.
- `wp_update_post` no post existente às **15:20:39**; slug e URL intactos, status publish, categoria Tecnologia3 e imagem destacada257 inalteradas. Não ativou qualquer LIVE automático.
- AIOSEO `seo-data-update` confirmado para title, description e focus, `robots.noindex=false`.
- GET autenticado pós-escrita conferiu HTML **idêntico byte a byte** à prévia GitHub, excerpt/título/SEO, media e categoria originais, 1 CTA, 2 links afiliados, 1 disclaimer.
- Firecrawl `maxAge=0` da página pública confirmou HTTP200, título novo, única oferta, link afiliado original, fonte DOE e ausência da introdução antiga.

## Fila
Finalizados com readback WordPress e visualização pública: #260 C116, #314 C117, #311 C118, #278 C119, **#256 C120** (5/10). Não repetir edições.
- Pendente #29, #28, #25, #24: sem links afiliados encontrados no HTML/meta WordPress; não inventar URL.
- Candidato #138 com link Shopee existente, ainda requer validação individual de produto e campanha, backup e revisão.
- Segurança: workflow legacy Radar vNext ainda pausado `if: false`, config `publicacao_automatica=false`. Suíte universal V31 tem oito falhas históricas de roteamento pendentes.

**Código de retomada:** `V31-RADAR-C120-20261123-POST256-VERIFIED-5-OF-10`.
