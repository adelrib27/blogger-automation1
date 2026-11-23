# V31 C116 — Radar Tech BR: 4 drafts nativos, Shopee RADARWP, 2 links exatos gerados
**Data:** 2026-11-23 (America/Recife). **Estado:** PARTIAL COMMERCIAL, EDITORIAL DONE, DRAFT ONLY.
**Objetivo:** incorporar quatro artigos de ar-condicionado de forma nativa ao Radar Tech BR, SEM herdar campanhas/links/meta/conteúdos Blogger.

## Conteúdo e WordPress — executado e relido
Categoria nativa `Ar-condicionado` ID20, filha de `Tecnologia` ID3. Posts DRAFT:
- ID **353**, `instalacao-ar-condicionado-split-checklist-antes-compra`, guia de instalação; inclui ofertas Shopee específicas Midea 9k e Midea 12k como referências para comparação, não substitui dimensionamento técnico.
- ID **354**, `ar-condicionado-conectado-9000-btus-wifi-app-ficha-tecnica`, Midea Lite Conectado 9k; link afiliado exato da própria campanha RADARWP e imagem oficial atual da API.
- ID **355**, `midea-ai-ecomaster-12000-btus-funcoes-dados-tecnicos`, Midea AI Ecomaster 12k; link afiliado exato da própria campanha RADARWP e imagem oficial atual da API.
- ID **356**, `lg-dual-inverter-compact-12000-btus-comparacao-tecnica`, LG Dual Inverter Compact 12k; **sem CTA afiliado** até conversão oficial no novo limite diário.

Os 4 HTML foram substituídos por textos próprios com class `radartech-climatizacao`, notas editoriais nativas, link interno real para `https://radartechbr.com.br/guias-tecnologia/`, sem menção, URL, foto, CSS de rastreamento, tags, preços nem offerLink da antiga origem Blogger. Validação `wp_list_posts(status=draft,context=edit,raw_columns=true)` confirmou 353-356 e `wp_get_post_meta` revelou apenas meta padrão `footnotes`, sem canonical ou SEO de origem REST-visíveis. Todos permanecem DRAFT; nenhum LIVE.

## Campanha e fontes técnicas
- Rota única oficial `wordpress_radartechbr` tem `campaign="radarwp"`, `allowed_niches` inclui `climatizacao/ar_condicionado`, `publish_enabled=false`. Alteração na `affiliate_hub_v31/site_routes.json` commit `dd67ab20cdc7929ed8648772882be00a92df1b54`.
- [Workflow C112](https://github.com/adelrib27/blogger-automation1/blob/main/.github/workflows/v31_c112_radartech_arcond_offer_audit_once.yml): **READ ONLY** autenticou na Shopee API, validou exatamente os 3 pares `shopId,itemId`, nome/modelo/capacidade, imagem em host confiável e preço positivo; verificação da API não confirma estoque. Leu D1 com 1/3 slots usados em 23/11 por outra campanha.
- [Workflow C113](https://github.com/adelrib27/blogger-automation1/blob/main/.github/workflows/v31_c113_radarwp_arcond_convert_two_once.yml) executado PASS em 23/11: reservou atomicamente D1 global slots 2 e 3 e chamou `generate_shortlink(canonical, campaign='radarwp', credentials_secret)`, ou seja, API `generateShortLink` com subIds `RADARWP`. Link retornado com host oficial válido, produto/loja exatos e fotografia obtida em consulta própria. Não reutilizou a campanha Blogger `arcondicionadosemduvidas`.
  1. **Midea 9k** `shopee:1736335904:58267891881`: `https://s.shopee.com.br/3qOu7KtrLy`; foto de API `https://cf.shopee.com.br/file/sg-11134201-8259y-mvvssxr4fmki12`. Inserido nos DRAFTs 353 e 354.
  2. **Midea 12k** `shopee:889973435:18398298625`: `https://s.shopee.com.br/8pna4WfdWs`; foto de API `https://cf.shopee.com.br/file/sg-11134201-7rdwv-mctkguzbqfro18`. Inserido nos DRAFTs 353 e 355.
- Releitura exata de presença no WordPress dos links/SKUs/imagens/campanha `RADARWP` e rel `nofollow sponsored noopener noreferrer` em cada CTA. Post 356 continua sem link comercial de origem ou outro produto (nenhum encaminhamento enganoso).
- Nota: recepção válida de `shortLink` pela API com subID correto **não comprova comissão efetivamente atribuída**, estoque no checkout ou redirecionamento final acessível por ferramentas de navegação externas. Não prometer aprovação/pagamento Shopee sem dados de relatório afiliados.

## Pendente — LG 12k
Produto `shopee:822103155:58265302556` também passou READ ONLY C112 e tem imagem verificada por API, mas **nenhum slot D1 disponível hoje** (3/3). Não gerar mutation adicional ou reutilizar link do Blogger.
- Uma automação independente de retomada única está agendada para **24/11/2026 às 07:00 America/Recife**, para verificar cota/identidade do LG, converter **uma vez** pela campanha `RADARWP` após autorização D1 e então, via conector WordPress, atualizar só DRAFT 356 com imagem/CTA; registrar falhas ou indisponibilidade sem inventar URL; sem LIVE.
- Um teste de credenciais WordPress dentro do GitHub Actions C114 resultou em `wordpress_credentials_not_configured`: o secret `V31_WORDPRESS_SITE_CREDENTIALS_JSON` não está acessível naquele environment. O WordPress conectado no ChatGPT está funcionando. A automação usa o conector WordPress do ChatGPT para atualização; NÃO afirmar que Workflow Actions possa escrever no WordPress com as credenciais atuais.

## Publicação, exclusão da origem e continuidade
**0 novos LIVE, 0 exclusões.** Quatro artigos preservados nativamente no Radar Tech BR em DRAFT. A página antiga do Blogger e seus links históricos não devem ser copiados. O backup do Blogger original (4 posts + 10 páginas) permanece no Drive conforme C115.
Antes de excluir o Blogger: verificar homologação/publishing individual com aprovação, canonical e novas URLs HTTP200, links internos, páginas antigas ainda úteis e riscos SEO por falta de 301 interdomínios. Não ligar autopublicador V31 nem alterar WordPress fora do Radar, Pinterest ou Mercado Livre.
