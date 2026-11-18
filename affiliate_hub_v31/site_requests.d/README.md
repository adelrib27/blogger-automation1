# Pedidos de blogs reais — V31

Cada arquivo `<site_key>.json` é criado **somente quando um blog real foi registrado** em `site_routes.json` ou `sites.d/`, com o assunto informado naquele momento. Não predefinir assuntos nem campanhas.

Contrato: `{"site_key":"blog_real", "platform":"blogger", "topic":"tema informado agora", "articles":6, "enabled":true}`. O site e sua campanha devem existir antes do pedido. **Nunca gravar chaves de API, emails, senha, URL afiliada ou IDs secretos neste arquivo.**

Um pedido novo entra no fluxo diário de cache (até 3 mutações por dia no total), mas **não cria nem publica artigos**. Itens em revisão permanecem bloqueados para conversão. Bloquear/desabilitar pedido: `enabled:false` ou excluir o JSON. O modelo de 24 artigos é um lote de planejamento; solicitações maiores serão particionadas na evolução do orquestrador.
