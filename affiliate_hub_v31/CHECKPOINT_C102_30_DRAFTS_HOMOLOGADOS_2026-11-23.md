# C102 — HOMOLOGAÇÃO DOS 30 RASCUNHOS ANTES DA PUBLICAÇÃO MANUAL — 23/11/2026

- Pedido: 1 artigo por blog Blogger ativo. Inventário de 32 blogs, 30 de produção; excluir apenas Casa Prática Lab e Meu Céu Noturno não iniciado, como em C94.
- **30/30 artigos com status DRAFT e IDs distintos confirmados por get_post**, conteúdo byte a byte idêntico aos exports GitHub; nenhum novo LIVE criado nesta etapa.
- Todos contêm título SEO original, corpo orientativo distinto do C94, foto e `offerLink` afiliado do anúncio já verificado na rodada C94, um CTA laranja, link ao artigo anterior e link à Loja, aviso de afiliado. Os anúncios não foram revalidados na Shopee em 23/11; disponibilidade e variantes precisam ser conferidas pelo leitor. Não declarar comissão garantida ou imagem de produto diferente.
- 5 grupos de textos completos: `affiliate_hub_v31/C102_PREVIEWS_A_2026-11-23.json` até `C102_PREVIEWS_E_2026-11-23.json`. Textos 489–566 palavras cada.
- Manifesto/idempotência de 30 sites: `affiliate_hub_v31/C102_ARTICLE_ROLLOUT_MANIFEST_2026-11-23.json`.
- O Blogger inicialmente retornou HTTP429 na 6ª criação simultânea. Após pausa e execução **serial** as 30 gravações foram concluídas; Casa Leve exigiu novo request_id após comprovar lista de drafts vazia, o anterior ficou incerto. Não repetir chamadas com IDs antigos.
- Próxima etapa: **publicação individual MANUAL**, como a rodada C94 já autorizada por pedido do proprietário, SEM ativar rotas cron ou `V31_AUTOLIVE_ACTIVE`. Para cada site: reler draft por ID, reler list_published_posts para não duplicar artigo do dia, publicar pelo Blogger Bridge com publish_request_id único e reler GET para confirmar LIVE/URL. Qualquer erro/quota interrompe a rodada com checkpoint, não repete publicação às cegas.
- Não tocar em Lojs C101, temas, D1/R2, conversor, Cloudflare, Pinterest, rotas automáticas ou DRAFT HMAC legados.
