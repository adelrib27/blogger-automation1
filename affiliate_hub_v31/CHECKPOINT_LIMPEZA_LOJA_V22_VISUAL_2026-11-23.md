# V31 — Limpeza Inteligente | Loja V22 ajuste visual ao vivo
Data: 2026-11-23 (America/Recife).
Blog ID: `7757953554206491487`
Post vitrine LIVE: `6383277011247909539` — https://limpeza-inteligente.blogspot.com/2026/11/loja.html
Página LOJA de entrada: `4457645831148890823` — https://limpeza-inteligente.blogspot.com/p/loja.html (encaminha ao post vitrine).
**Escopo do pedido:** melhorar e ajustar somente a página LOJA após a instalação e aprovação do tema de imagens inteiras, sem reinstalar tema nem mudar a rotação de ofertas, links ou identidade geral.

## Backup seguro, anterior à alteração
- `affiliate_hub_v31/backups/limpeza_inteligente_loja_live_pre_visual_2026-11-23.html` em GitHub `main`, commit `c5b43854c58f594318ddfb52579676bb0e15b1bd`, **GET readback byte a byte exato** do conteúdo do post antes de editar (39433 caracteres).
- **Não utilizar** como recuperação a cópia experimental no Google Docs: ela perdeu 286 caracteres na leitura; só o GitHub foi validado exato.

## Atualização real no Blogger
- Atualizado somente HTML do post LIVE `6383277011247909539`, adicionando no final um único `<style id="v31-limpeza-loja-v22-visual">`, CSS isolado por `.bls-page`. Não alterado HTML anterior; Blogger GET confirmado idêntico após a atualização.
- Ajustado hero, largura da vitrine de 1440 para 1200 px, espaçamento, títulos, painéis de categorias, cards de produtos, imagens com `object-fit:contain`, botões visuais por pseudoelemento e responsividade para até 620 px. Preservados conteúdo, scripts, categorias, cards, preços exibidos e links comerciais anteriores.
- Vitrine mantém **20 links/cards de produtos** e **3 slides**. São **32 referências de URL Shopee** no documento; o prefixo `s.shopee.com.br` presente antes da alteração foi comparado como conjunto sem diferença depois da mudança. **Não** houve conversão nova pela API, alteração de SubID, garantia de preços ou atualização de estoque.
- Nenhuma edição de tema, `/p/loja.html`, outros posts, outros blogs, Cloudflare/R2/D1 ou rotinas LIVE do V31.

## Testes
- Readback Blogger: `status=live` e HTML idêntico ao enviado (sem exceções).
- Firecrawl Browser desktop na URL pública: `.bls-page` com largura computada 1200 px; primeiro produto `display:flex`, `padding:11px`, imagem `object-fit:contain`; CTA pseudo `Conferir na Shopee`; **20 cards**, **3 slides**, **32 links Shopee** presentes; **nenhuma rolagem horizontal anormal**.
- Auditoria anterior da página identificou 32 imagens de host `cf.shopee.com.br`, inicialmente 14 ainda em lazy load; após rolar a página, **32/32 carregadas, zero quebradas**. Não trocar imagens por erro aparente de lazy-load.
- `/p/loja.html` redireciona ao post loja; scraping público 200.
- Captura mobile solicitada; execução de inspeção DOM mobile foi bloqueada por limite de sessões de navegador. Recomendado validar visualmente pelo dono no celular antes de homologação definitiva.
- A API Shopee não foi chamada neste ciclo: a presença do link não comprova comissão ou estoque.

## Rollback
Restaurar exatamente o conteúdo do backup no arquivo `affiliate_hub_v31/backups/limpeza_inteligente_loja_live_pre_visual_2026-11-23.html` no post Blogger ID `6383277011247909539`; em seguida GET readback. Não reverter a página LOJA de encaminhamento nem o tema de miniaturas, porque ambos são separados.
