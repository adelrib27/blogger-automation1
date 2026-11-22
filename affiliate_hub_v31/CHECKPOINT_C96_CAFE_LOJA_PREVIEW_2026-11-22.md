# C96 — PRÉVIA DE CURADORIA DA LOJA CAFÉ NA MEDIDA — 22/11/2026

- Escopo: Blogger Café na Medida (blog_id 4820923154548273510), página LIVE Loja (page_id 4202100014512520679).
- Estado pré-mudança lido via Blogger API: 4 itens com links Shopee e ícones, sem fotos reais; página não atualizada desde 12/11. Blog tem 5 posts LIVE.
- Solicitação explícita do proprietário: ampliar a Loja para pelo menos 24 produtos reais relacionados a café, priorizando potencial de comissão, usando Shopee Affiliate API da mesma conta V31.
- Guardas: não criar post/página duplicada, não mexer em D1/R2, conversões, outros blogs ou LIVE automático. Atualizar só página Loja já publicada, com idempotência. Conservar permalink e textos legais.
- Fase de curadoria: API productOfferV2 READ ONLY via GitHub Actions e secrets do environment v31-editorial-safe; reunir IDs shop:item, nomes, fotos e offerLink reais, comissão observada apenas para ranking, não para promessas ao consumidor. Checar URL e vínculo por anúncio; sem afirmar estoque, preço, desconto, frete ou receita futura.
- Critérios: pelo menos 24 anúncios distintos válidos e relevantes, imagens exatas da API, links de afiliado de oferta API; excluir itens irrelevantes; diversificar categorias/vendedores; no máximo 3 cards por seller quando possível, priorizar rating>=4.0. Salvar um snapshot da página original antes de atualizar, GET após e verificar quantidade, imagens, afiliados e status.
- Regra de isolamento: links offerLink de conta API podem não ter SubID exclusivo de Café; não declarar rastreabilidade da campanha nem efetuar nova mutação generateShortLink hoje (cota global 3/3 em C94).
- Estado: EM ANDAMENTO — ainda 0 novos produtos na página; verificar resultados reais, não preencher com suposições.
