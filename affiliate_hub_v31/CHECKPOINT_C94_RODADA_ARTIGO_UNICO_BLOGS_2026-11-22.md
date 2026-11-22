# C94 — Rodada sequencial de um artigo por blog V31 sem nova publicação em 22/11/2026

Pedido do usuário: após implementar C93, percorrer blogs que NÃO receberam artigo novo hoje, UM POR VEZ até o último, criar e publicar um novo artigo editorial para cada blog elegível. Data editorial: 22/11/2026 (America/Recife).

## Auditoria e restrições operacionais
- INVENTÁRIO Blogger API autenticado: 31 blogs na conta; V31 roteia apenas subconjunto via site_routes.json/sites.d. Respeitar roteamento, não publicar em LAB, blogs não homologados ou conteúdo sem nicho verificado apenas para aumentar contador.
- Ar-Condicionado sem Dúvidas já tem 2 posts Midea novos em 22/11; Cadeira Certa publicou Office Arco em 22/11. PULAR para evitar duplicação diária. Móveis para Cada Canto tem 3 LIVE, todos de 18/11, e 6 drafts. NÃO alterar draft assinado C81 id 4106024906916105222 (evidência HMAC).
- WP Radar Tech BR: último post publicado em 20/11; Casa e Decoração: 21/11; Oficina & Garagem: 21/11 na checagem inicial. Conferir novamente antes de publicar devido aos crons independentes.
- Shopee D1 em 22/11 já usou 3/3 conversões globais, portanto NÃO executar generateShortLink ou furar limite para esta rodada. Aproveitar apenas links já existentes validados da campanha específica ou offerLink da API da mesma conta, distinguindo falta de SubID. NÃO inventar links, produtos ou fotos.
- Política C92/C93: anúncio esgotado não é banimento do modelo; procurar vendedores alternativos; não prometer estoque. Um post educativo de qualidade pode ser publicado sem CTA comercial quando não houver oferta confiável, mas nunca inventar afiliado.
- Publicação de cada artigo requer GET prévio do draft e confirmação pós-publicação, SEO original, fonte verificável, links internos, imagem da oferta real e aviso de afiliação se tiver CTA.
- AUTO LIVE V31 continua OFF; esta é execução editorial MANUAL explicitamente solicitada, não autorização para liberar cron LIVE.

## Passos e diário de operações
Registros de artigos serão acrescentados a cada publicação verificada. Evitar transformar um draft já publicado em item duplicado; preservar títulos/permalinks. Este arquivo é checkpoint antes das primeiras mudanças da C94.
