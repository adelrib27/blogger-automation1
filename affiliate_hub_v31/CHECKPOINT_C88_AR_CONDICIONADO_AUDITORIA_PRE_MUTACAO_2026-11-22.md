# V31 C88 — Ar-Condicionado sem Dúvidas, auditoria pré-mutação e plano SAFE

Data: 22/11/2026. Blog **Ar-Condicionado sem Dúvidas**, Blogger ID **2228849984262880811**, `https://ar-condicionado-sem-duvidas.blogspot.com/`. Proprietário confirmou por captura de tela a instalação do tema exclusivo C87; NÃO reinstalar.

## Estado antes das alterações
- Blogger API v3 conectada, leitura autenticada em 22/11/2026: **0 posts LIVE, 0 páginas LIVE**. Descrição existente: `Guias independentes para escolher ar-condicionado: capacidade em BTUs, inverter, consumo de energia, instalação, ruído e comparativos para comprar com critério.`.
- Tema C87 foi entregue previamente com identidade azul/ciano, carrossel a partir de `Blog1` sem `FeaturedPost1` oculto. A captura do proprietário confirma visual de cabeçalho e hero exclusivo, e mensagem "Não há nada aqui", natural com 0 posts.
- O menu do tema aponta para `/p/sobre.html`, `/p/loja.html`, `/p/contato.html`; rodapé também para `/p/politica-de-privacidade.html`, `/p/termos-de-uso.html`, `/p/aviso-de-afiliados.html`. As **6 páginas ainda não existem** na API.
- O blog não tem rota de campanha específica registrada em `affiliate_hub_v31/sites.d` no início de C88; LIVE automático global V31 permanece desligado.

## Sequência com gates
1. Confirmar configurações SEO por Runner e aplicar perfil seguro: descrição e metadescrição de busca <=150; visibilidade mecanismos e HTTPS; timezone America/São Paulo/Brasília.
2. Criar **6 páginas institucionais publicadas**, uma por slug EXATO esperado pelo menu; GET autenticado de cada uma. Contato não deve divulgar e-mail pessoal nem usar formulário externo do LAB.
3. Fazer consulta **READ ONLY** a `productOfferV2(keyword)` na Shopee Affiliate API via ambiente GitHub seguro para identificar **modelo real de condicionador de ar completo** (não capa, peça, controle, filtro ou serviço), foto exata, IDs e URL canônica. Reconsultar produto por item ID e loja.
4. Se fonte e produto elegíveis e houver slot D1, **única** mutation `generateShortLink` para a campanha **`arcondicionadosemduvidas`**, reservando previamente cota global. Nenhum retry automático de mutation. Não usar shortlinks de outros blogs.
5. Criar **um post DRAFT** longo e SEO com foto oficial, especificações estritamente verificadas (não inventar consumo, classe energética, preço, dimensões, ruído ou tensão), links internos institucionais e fonte Inmetro PBE. Após GET e garantia de link próprio, publicar **individualmente** a pedido do proprietário; manter LIVE automático V31 OFF.
6. Atualizar página Loja com a oferta validada e link ao guia; verificar homepage pública e links do menu/corpo; registrar os checkpoints de continuidade na `main`.

## Guardas
- Não tocar em outros blogs; não editar DRAFTs assinados C81; não substituir tema; não ativar `V31_AUTOLIVE_ACTIVE`.
- Não editar conteúdos Shopee/CSV/D1/R2 fora do ledger de slot especificamente autorizado pelo fluxo de conversão.
- Na impossibilidade de converter link, deixar post DRAFT e explicar o bloqueio. A ausência de contato privado é pendência legítima; não inventar endereço.
- O Sistema PBE Inmetro é fonte pública adequada para consulta de eficiência por modelo, mas uma classificação específica só pode ser afirmada após verificar código de modelo da etiqueta: https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/condicionadores-de-ar/sistema-pbe-para-consulta-dos-produtos-etiquetados
