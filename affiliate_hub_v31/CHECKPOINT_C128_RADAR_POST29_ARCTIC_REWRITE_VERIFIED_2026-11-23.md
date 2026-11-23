# C128 Radar — Arctic Air Cooler #29 reescrito preservando PDP TikTok original
**Data:** 23/11/2026 America/Recife. **Status:** WordPress post #29 LIVE manualmente editado; automações LIVE continuam desativadas.

## Correção do diagnóstico anterior
O original incluía URL `https://vt.tiktok.com/ZS9UNndpjDsxQ-GACcI/` no cartão comercial. Não era link Shopee, mas não estava ausente. A auditoria C127, run [45254493657](https://github.com/adelrib27/blogger-automation1/actions/runs/45254493657), confirmou HTTP200 via HEAD e redirect 301 para `https://shop.tiktok.com/br/pdp/1731402390818161683`. Não comprovou estoque, comissão ou identidade de variante.

A foto original WP (media73) era uma caixa branca/cinza com lateral verde-azulada; candidato Shopee #23493283907 possuía outra composição/imagem e não passou correspondência forte; **não usado**. Em C127 constam fotos comparadas nos artefatos, com run bem-sucedida.

## Antes da edição
- Backup integral original já protegido: `affiliate_hub_v31/backups/C127_RADAR_WP_POST_29_ORIGINAL_2026-11-23.json`, commit `95acbfcdf10c9c26d3f8c4579e86f83150906a87`.
- Preview completo criado ANTES do write: `affiliate_hub_v31/previews/C128_RADAR_POST29_ARCTIC_EDIT_WITH_TIKTOK_ORIGINAL_2026-11-23.json`, commit `4403b0afec1e0f859dbe79c4635b9bf742e45e7b`.
- Proteções imediatamente antes do write: `modified=2026-10-17T15:39:40`, HTML/title/excerpt iguais ao backup; slug/status/categoria3/media73 inalterados; origem do link TikTok intacta.

## Após o write
- `wp_update_post` alterou SOMENTE título, HTML e excerpt do post ID29; status publish; `modified=2026-11-23T17:02:14`; permalink inalterado:
  https://radartechbr.com.br/arctic-air-cooler-portatil-o-que-conferir-antes-de-comprar/
- Novo título: **Arctic Air Cooler portátil: o que vale conferir**, SEO excerpt/meta 146 caracteres, foco `Arctic Air Cooler portátil`.
- Texto ~1313 palavras, 9 H2, **1 bloco comercial**, **1 link TikTok original** com `rel="nofollow sponsored"`, **1 foto original WP**, **1 disclosure contextual** indicando explicitamente TikTok Shop (não Shopee), dois links internos e fontes DOE.
- Não afirma refrigeração por compressor, redução de temperatura numérica, estoque, preço, desempenho clínico ou que o TikTok Shop seja Shopee.
- `wp_ability_aioseo_posts_seo_data_update` confirmado, `robots.noindex=false`.
- Readback `wp_get_post_full(context=edit)`: HTML byte-exato ao preview, título/excerpt e AIOSEO iguais, slug/categoria3/media73 preservados, 1 CTA e um único link comercial original.
- Teste Firecrawl público `maxAge=0`: HTTP200, título novo, 1 bloco comercial, link TikTok original presente.

## Situação
**8/10 editoriais reescritos e verificados:** #260, #314, #311, #278, #256, #138, #28, #29.  
**Restam:** #25 Kapbom e #24 Luz RGB, ambos links originais TikTok Shop PDP validados em C127. NÃO trocar por candidatos Shopee que só correspondem pelo nome. Reescrever individualmente com seu próprio backup/preview/readback se o estado WP permanecer intocado.  
**Separar conceitos:** 8/10 artigos reescritos não significa 8/10 ofertas Shopee; os posts #29 e restantes têm TikTok legado. A migração exata Shopee desses PDPs continua pendente.
**Segurança:** workflow legacy `if: false`, `RADAR_LIVE_PUBLISH_ENABLED=false`, config `publicacao_automatica=false`; as oito falhas legadas de contrato universal seguem pendentes. Nenhum outro blog alterado.

**Código de retomada:** `V31-RADAR-C128-20261123-EIGHT-REWRITTEN-2-TIKTOK-PENDING`.
