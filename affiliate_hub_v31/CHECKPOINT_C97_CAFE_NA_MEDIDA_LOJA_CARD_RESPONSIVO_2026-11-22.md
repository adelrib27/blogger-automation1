# V31 C97 — Café na Medida: corrigido o cartão gigante do moedor na Loja

**Data:** 22/11/2026 (America/Recife).
**Blog ID:** `4820923154548273510`.
**Página Loja ID:** `4202100014512520679`.
**URL permanente:** https://cafe-na-medida.blogspot.com/p/loja.html
**Status:** **CORRIGIDO — LIVE — verificado no Blogger e navegador público desktop/mobile**.

## Relato do proprietário
A captura de tela da Loja C96 mostrava o cartão único de "Moedores de café" expandido para toda a largura da página. A foto do moedor aparentava tamanho desproporcional em relação aos demais produtos.

## Causa exata
No HTML do Blogger Page havia 12 grades com CSS:
`grid-template-columns:repeat(auto-fit,minmax(min(100%,235px),1fr))`.
O modo `auto-fit` **colapsa colunas vazias**: uma categoria com um único card passa a ocupar toda a linha. Assim, a imagem também expande horizontalmente apesar do tamanho desejado de 205 px na declaração inline (estilos do tema podem aumentar a altura renderizada).

## Correção
- Foram alteradas **somente** as 12 grades da Loja para `repeat(auto-fill,minmax(min(100%,235px),1fr))`. Com `auto-fill`, colunas vazias permanecem reservadas e um cartão sozinho preserva a mesma largura dos outros.
- Definida altura da área de foto `231px`, `overflow:hidden`, `box-sizing:border-box` e imagem `height:205px!important;max-height:205px!important;object-fit:contain!important`, para reduzir risco de conflito com CSS genérico do tema.
- Mantidos conteúdo, títulos, foto de cada anúncio, vendedor, avaliações consultadas, links internos, URLs afiliadas, termos legais e página original.
- **Não** alterado o tema nem os workflows de publicação automática; V31 AUTO LIVE permanece desativado.

## Backup, exportação e implantação
- Backup **antes da correção:** `affiliate_hub_v31/backups/C97_CAFE_NA_MEDIDA_LOJA_PRE_GRID_FIX_2026-11-22.html`.
- HTML integral corrigido: `affiliate_hub_v31/exports/C97_CAFE_NA_MEDIDA_LOJA_GRID_RESPONSIVA_2026-11-22.html` (81.092 caracteres).
- Único update `Blogger_Bridge_V2.update_page` na página existente; request_id `v31-c97-cafe-loja-image-grid-20261122-01`.
- GET após alteração: `status=live`, conteúdo idêntico ao export, 12 grades auto-fill, 35 cartões, 35 imagens com altura declarada 205 px, 35 destinos Shopee distintos.
- Firecrawl público maxAge=0: HTML contém 12 grades auto-fill, foto do moedor presente, 35 produtos, 35 URLs afiliadas distintas.
- Browser remoto desktop 1280 px, medição real: **primeiro cartão 282 px de largura**, demais cartões também **282 px**; foto do primeiro com **205 px** de altura.
- Browser remoto celular 375 px: cartão com **351 px de largura**, imagem **205 px** de altura, **sem rolagem horizontal**.

## Guardas
- Não houve nova busca nem conversão Shopee, nenhuma mudança em R2/D1, nenhuma publicação adicional, nenhum produto clonado e nenhuma alteração de tema ou de outros blogs.
- Rollback, se necessário: restaurar apenas conteúdo da página `4202100014512520679` a partir do backup C97 após confirmar que não houve edições posteriores.

**C97 concluída e homologada.**
