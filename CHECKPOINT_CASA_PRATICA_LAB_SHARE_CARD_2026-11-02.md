# Checkpoint — Casa Prática Lab — detalhe pendente do cartão de compartilhamento

Data: 2026-11-02

## Estado atual validado

Blog: Casa Prática Lab
Blog ID: 8930870316690519385
Page LOJA ID: 7110845449177208439
Store Post ID: 7691087355641688975
Page pública: https://casa-pratica-lab-20261102.blogspot.com/p/loja.html

A correção visual principal da LOJA foi aplicada e validada com sucesso no run GitHub Actions 41494904964.

Checks que passaram:
- Page LOJA 20 produtos + 12 hero cards
- layout amplo
- carousel delegado/sincronizado
- Policy Guard
- Store Post técnico fora da home
- 3/3 artigos editoriais presentes na home
- 3/3 artigos com imagem editorial
- CASA_PRATICA_LAB_PUBLIC_E2E_PAGE_MATURE_PASS

O workflow temporário de aplicação foi removido após PASS.

## Pequeno detalhe visual ainda pendente

Comparação visual feita com Radar Tech BR e gravação do Casa Prática Lab.

No Radar Tech BR, entre o fundo/hero desfocado do tema e o início da vitrine da LOJA existe um cartão branco arredondado do wrapper nativo do post, contendo o ícone verde de compartilhamento.

No Casa Prática Lab esse cartão branco de compartilhamento não aparece.

O usuário confirmou explicitamente que ESTE é o pequeno detalhe faltante. Não confundir com:
- seta esquerda do carousel;
- largura da loja;
- título LOJA;
- produtos;
- hero 20+12.

## Hipótese técnica já identificada

A adaptação da LOJA para a Page /p/loja.html aplica CSS que remove/neutraliza wrappers nativos do template de Page/Post:
- post-title-container / post-title / entry-title / post-header
- post-outer-container / post-outer / post / post-body-container
- backgrounds, borders, shadows, margins e paddings desses wrappers

Essa normalização visual provavelmente removeu junto o cartão/wrapper nativo no qual o Blogger exibe o botão de compartilhamento. Radar Tech BR, por usar a superfície de Store Post madura, mantém esse bloco nativo visível acima da vitrine.

## Próximo passo exato

Antes de alterar qualquer coisa:
1. Ler o HTML/CSS vivo do Radar Tech BR no Store Post /2026/10/loja.html e identificar exatamente qual elemento DOM/classe produz o cartão branco + share verde.
2. Ler o HTML público/tema do Casa Prática Lab e confirmar qual regra CSS o oculta ou remove visualmente.
3. Restaurar somente esse wrapper/cartão no Casa Prática Lab, preservando:
   - layout amplo atual;
   - carousel funcional;
   - 20+12;
   - home limpa;
   - Page LOJA canônica;
   - Store Post técnico em DRAFT;
   - writer automático das 10:20 America/Recife.
4. Adicionar check permanente no auditor para detectar a presença do bloco de compartilhamento, sem depender apenas de contagem 20+12.
5. Validar publicamente e só então considerar o detalhe concluído.

## Regra de retomada

Se um novo chat for aberto, retomar a partir deste arquivo e NÃO refazer as correções já concluídas. O único detalhe pendente neste checkpoint é o cartão branco nativo com o ícone verde de compartilhamento acima da vitrine da LOJA, como no Radar Tech BR.
