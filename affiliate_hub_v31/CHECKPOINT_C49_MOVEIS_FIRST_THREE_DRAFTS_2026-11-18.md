# V31 C49 — Primeiro lote real de 3 artigos Blogger: móveis (18/11/2026)

## Confirmação de pedido e estratégia editorial

O proprietário escolheu iniciar com **3 artigos**, idealmente **um por categoria/ambiente**, e explicitou que os artigos **não precisam depender exclusivamente da API Shopee**. O blog "Móveis para Cada Canto" já foi criado como Blogger real e registrado no Hub V31 em C48.

Estratégia: iniciar com **três guias evergreen originais**, independentes de variações de preço/estoque e de links de campanha não verificados. O Blogger usa **marcadores (labels)**, não exige uma taxonomia técnica rígida de categorias para existir. A integração Blogger Bridge V2 disponível permite criar rascunhos, **mas não expõe parâmetro para gravar marcadores**. Os ambientes abaixo são **organização editorial**, ainda não etiquetas técnicas na plataforma. Não inventar labels aplicados.

## Entrega realizada na conta Blogger

- Blog real: **Móveis para Cada Canto** — https://moveisparacadacanto.blogspot.com/
- Blogger ID: `1439741542627895062`, mesmo da rota `blogger_moveis_para_cada_canto`.
- **3 rascunhos criados com Blogger API e verificados por list_drafts**:
  1. **Sala:** _Sofá para sala pequena: como escolher tamanho, formato e tecido_ — medidas, circulação, tipos, tecidos, conforto e checklist.
  2. **Quarto:** _Guarda-roupa para quarto: portas, medidas e divisões que fazem diferença_ — portas, materiais, divisões internas, estabilidade e checklist.
  3. **Home office:** _Home office confortável: como escolher mesa e cadeira para trabalhar em casa_ — mesas, cadeiras, altura, iluminação, cabos e checklist.
- **Status confirmado dos três: `draft`**. **0 artigos publicados** nesta ação, **0 links afiliados inseridos nos artigos** (nenhuma URL específica foi verificada para o conteúdo desses guias); **0 marcadores aplicados** pela API conectada.
- Artigos informativos e originais, em pt-BR com headings H2/H3, listas e recomendações de segurança sem afirmar especificações, preços, avaliações ou comissões de produtos não verificados.
- Blog SEO/HTTPS/timezone previamente verificados C48. **Tema visual V31 continua aguardando allowlist do Runner** `target_not_authorized` para o novo ID; não contornar.

## Fila V31 exclusivamente para estoque de afiliados

- Arquivo `affiliate_hub_v31/site_requests.d/blogger_moveis_para_cada_canto.json` registra **pedido REAL de 3 artigos**, `platform=blogger`, assunto geral cobrindo sofá, guarda-roupa, mesa/escritório, `enabled=true`.
- O cron `v31_universal_request_queue_daily.yml` é limitado a no máximo **3 mutações Shopee por execução entre todos os pedidos**; usa campanha `moveisparacadacanto` somente após verificar rota real, moderação/curadoria/URLs, persiste links no R2 e gera **envelopes editoriais privados de revisão**, **nunca publica**.
- A fila prepara estoque comercial futuro independente dos três rascunhos e **não insere automaticamente links nos textos**, evitando relações incorretas produto↔guia. Não interpretar solicitação de 3 artigos como autorização de publicação imediata nem como promessa de resultados de comissão.
- Teste estrutural reforça que o pedido só existe para blog real, quantidade 3, campanha isolada e `publish_enabled=false`; CI deve aprovar antes do merge para a main.

## Próximo passo explícito, sem desviar da biblioteca universal

Verificar CI e canário R2 de fila SAFE, conservar 3 rascunhos. Para lançamento visual completo, autorizar o ID Blogger exato no Runner e instalar tema V31. Publicar os textos só depois da etapa de revisão/editoria e da autorização de publicação para o novo blog. Categoria editorial de ambiente pode virar marcador Blogger via um recurso que efetivamente aceite labels, mas **não é impeditivo** para o conteúdo.

**Código de continuidade:** `V31-C49-MOVEIS-3DRAFTS-SALA-QUARTO-HOMEOFFICE-CACHEONLY-20261118`.
