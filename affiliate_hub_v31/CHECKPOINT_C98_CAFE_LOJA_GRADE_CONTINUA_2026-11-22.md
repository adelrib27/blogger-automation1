# C98 — Café na Medida: Loja com grade contínua e remoção visual dos avisos legados

**Data:** 22/11/2026 (America/Recife)
**Página existente:** `https://cafe-na-medida.blogspot.com/p/loja.html`
**Blog ID:** `4820923154548273510`
**Page ID:** `4202100014512520679`
**Status:** PUBLICADO, QA autenticado + DOM público + layout desktop em navegador real

## Problema apresentado pelo proprietário
Na imagem da C97, o moedor manual aparecia com tamanho correto, mas isolado em uma linha, deixando grande área vazia ao lado. Acima da Loja persistia um aviso do tema legado **“Ainda não há fotos de produtos disponíveis para os destaques. Confira os produtos abaixo.”** e um carrossel antigo vazio, embora a vitrine já tivesse fotos reais em seus cartões. O cabeçalho legado “Loja / Vitrine de produtos do Café na Medida” duplicava o cabeçalho editorial.

## Causa
O HTML da página tinha **12 grids independentes**, agrupadas por categoria. A categoria Moedores continha apenas 1 cartão, deixando o restante da linha vazio; a mera mudança de `auto-fit` para `auto-fill` em C97 não resolveria esse agrupamento por seções. No tema, o aviso `.ub-v29-photo-notice`, o carrossel vazio `#ub-v21-store-carousel` e o cabeçalho `.ub-store-heading` são elementos criados fora do conteúdo da Blogger Page.

## Correção C98
- Foi preservada a introdução editorial, os atalhos de categorias e o rodapé legal.
- Todas as 12 seções de produtos foram recompostas em uma **grade contínua única** `.cafe-c98-grid` com 35 cartões. O grupo principal agora não cria áreas vazias por categoria, e os quatro primeiros cartões ficam lado a lado. Cada cartão conserva sua etiqueta de categoria.
- Os 12 atalhos de categorias foram mantidos e agora apontam à âncora da primeira ficha da categoria dentro da grade; `:target` destaca o cartão.
- Os 12 links para artigos editoriais preservados, agora reunidos em seção “Guias para comprar melhor”, abaixo da grade.
- CSS **limitado à página específica** `#post-body-4202100014512520679` oculta o aviso incorreto, o carrossel legado vazio e o cabeçalho duplicado; não remove elementos do tema em outros locais e não altera tema universal.
- Responsividade: grid adaptável no desktop e regra CSS de duas colunas para viewport de até 520 px, com fotos de altura compacta; nenhum layout mobile foi declarado homologado por screenshot neste checkpoint.

## Evidências
- Backup da Blogger Page C97 antes da alteração: `affiliate_hub_v31/backups/C98_CAFE_NA_MEDIDA_LOJA_BEFORE_CONTINUOUS_GRID_2026-11-22.html` (81.092 caracteres).
- HTML corrigido preparado primeiro no GitHub: `affiliate_hub_v31/exports/C98_CAFE_NA_MEDIDA_LOJA_GRADE_CONTINUA_SEM_AVISO_2026-11-22.html` (80.088 caracteres).
- Atualização única via `Blogger_Bridge_V2.update_page`, request_id `v31-c98-cafe-loja-continuous-grid-20261122-01`.
- GET autenticado confirmou conteúdo byte-a-byte idêntico à exportação GitHub, página LIVE, 35 cartões, uma grade contínua, 35 fotos originais, 35 links afiliados Shopee distintos e 12 links internos a guias. Nenhum identificador técnico exposto no conteúdo.
- Firecrawl HTML público `maxAge:0`: 35 cartões na nova `.cafe-c98-grid`, nenhum dos grids separados anteriores e os mesmos 35 destinos de oferta.
- Firecrawl browser real desktop 1280 px: aviso legado **oculto**, carrossel vazio **oculto**, os quatro primeiros cartões **na mesma linha**, larguras **222,39–222,41 px**, com alinhamento vertical idêntico. Intervalo entre nav categorias e catálogo **27 px**. A verificação de CSS ocorreu em navegador real; extração estática de HTML pode omitir `<style>` mesmo quando as regras são aplicadas.
- Tentativa separada de confirmação visual mobile retornou sem relatório detalhado e não é considerada homologação por navegador nesta execução.

## Integridade e limites
- **Não alterados:** temas Blogger, outros blogs, posts, imagens, dados de produto, URLs afiliadas, D1/R2, Shopee API, limites de conversão, crons e `V31_AUTOLIVE_ACTIVE`.
- A página continua usando as mesmas 35 ofertas já verificadas na C96; nenhuma nova oferta ou preço foi inventado. Loja pública NÃO prova estoque atual nem comissão garantida.
- Caso surja regressão, restaurar **somente** o HTML da página existente via backup C98, após verificar edições posteriores.
- Aviso antigo permanece no HTML do tema legado, mas oculto visualmente somente na Loja; correção definitiva do widget exigiria edição autorizada e backup do tema, fora do escopo desta intervenção.

**Estado C98:** CONCLUÍDO — grade contínua e aviso legado oculto, desktop homologado.
