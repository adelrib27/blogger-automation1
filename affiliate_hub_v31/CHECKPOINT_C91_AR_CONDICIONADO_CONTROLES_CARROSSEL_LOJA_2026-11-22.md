# V31 C91 — Ar-Condicionado sem Dúvidas: controles Anterior / Próximo da Loja

**Data:** 22/11/2026. **Blog:** https://ar-condicionado-sem-duvidas.blogspot.com/ · Blogger `2228849984262880811`.

## Estado de produção anterior à mudança
O proprietário enviou captura da página `/p/loja.html` do tema C90 já instalado, com um slide de LG Dual Inverter Compact 12.000 BTUs, card do produto e link afiliado intactos. Os botões **Anterior** e **Próximo** apareciam em formato estreito e com texto dividido na vertical.

Inspeção independente do HTML público e do DOM executado (Firecrawl, HTTP 200):
- `#ub-v21-store-carousel .ub-v21-controls button[data-ub-step]` possui estilo `border-radius:50%;width:44px;padding:10px`;
- O carrossel da loja contém **1 slide**;
- O JavaScript marca os dois botões com `hidden=true`, mas o `display:inline-block` de uma regra CSS mais específica impede o comportamento nativo de `[hidden]`; estilo computado `display:block`, `width=44px`, `height≈74.56px`, `white-space:normal`;
- O resultado é um controle visual vertical que, para um único slide, nem deveria aparecer.

## Correção pontual C91: artefato validado, **NÃO INSTALADO**
Arquivo completo criado localmente nesta conversa:
`TEMA_EXCLUSIVO_AR_CONDICIONADO_SEM_DUVIDAS_V31_C91_CONTROLES_LOJA_CORRIGIDOS.xml` — **218.203 bytes**, SHA256 `313fab7f9b494b82431966c7556f18f6ddd915b698b5a22fe3d546650e0cf1ed`.
Versão de texto `TEMA_EXCLUSIVO_AR_CONDICIONADO_SEM_DUVIDAS_V31_C91_CONTROLES_LOJA_CORRIGIDOS_HTML_COMPLETO.txt`, diff `C91_ALTERACOES_CONTROLES_CARROSSEL_LOJA.patch`, relatório `RELATORIO_C91_CORRECAO_BOTOES_CARROSSEL_LOJA.md` e JSON `VALIDACAO_C91_CONTROLES_LOJA.json`.

**Somente 2 hunks de alteração sobre o tema C90 original**:
1. Substituída a regra CSS de botões de 44px por estilo **restrito ao carrossel Loja**: `width:auto;min-width:102px;min-height:44px;padding:10px 16px;border-radius:var(--ub-button-radius);white-space:nowrap`, centralização, flex no próprio botão. Acrescentada regra `button[data-ub-step][hidden]{display:none!important}` estritamente no carousel da Loja.
2. Dentro do bloco original de autoplay da Loja, retirada somente a alteração textual de “Anterior”/“Próximo” para glifos de seta `‹` e `›`. JavaScript de navegação, pausa, autoplay e compartilhamento preservados.

**Com 1 produto:** controles Anterior e Próximo ficam corretamente ocultos; contador `1 / 1` e Compartilhar permanecem. **Com múltiplos produtos:** botões horizontais e legíveis, sem quebra de palavras, e navegação preservada.

## Validação
- XML Blogger estrito lxml PASS; estrutura de elementos e lista de widgets idênticas ao C90; diff exatamente 2 hunks.
- tinycss2: zero novos erros de parsing.
- Node `--check`: 6 scripts JS executáveis PASS; 3 blocos com marcadores de template/comentários de widgets Blogger não passam em Node isolado (não alterados; não afirmar 100% JS sem contexto).
- Chromium Playwright local, viewport 360px: **hidden → display:none, largura 0**; modo múltiplos botões visíveis **102×44 px, nowrap, sem overflow horizontal**. Trata-se de simulação local, não prova de instalação LIVE.
- Não alterado: Blogger Blog1, carrossel da HOME, artigo LG, foto, shortlink Shopee `https://s.shopee.com.br/8fU8IIYmXO`, Loja, menu BTUs/Inverter/Consumo/Instalação, formulário Contato, política SEO, campanha, D1/R2, cron ou LIVE automático.
- O arquivo XML completo é um **artefato da conversa**; este checkpoint não implica que o binário completo esteja commitado no GitHub.

## Próximo gate
1. Proprietário faça backup do tema C90 vigente, aplique o XML C91 em **Blogger → Tema → Editar HTML** e salve.
2. Verificar Loja em desktop/mobile: apenas 1 item → sem botões Anterior/Próximo, compartilhamento e contador visíveis.
3. Quando a Loja tiver 2+ produtos, verificar navegação anterior/próximo com rótulos horizontais e pause/share intactos; não criar ofertas artificiais só para testar.
4. Preservar o funcionamento das quatro páginas temáticas e do formulário C90 e status de 10 páginas LIVE, 1 artigo LIVE, 0 DRAFT. Não reconverter o LG, não ligar `V31_AUTOLIVE_ACTIVE`.
