# V31 — Retomada do chat Radar Tech BR após C109/C110/C111
**Data:** 23/11/2026 (America/Recife). **Status:** AUDITORIA READ-ONLY / foco corrigido a pedido do proprietário.

## Contexto correto da conversa expirada
O proprietário especificou que a continuação procurada é a sequência: **“PERFEITO! AGORA PENSE NO QUE VALARIA ACRESCENTAR COMO MENUS OU SUBMENUS...” → “faça isso então por favor. e também gostaria de ampliar para Smartphones, Computação e TVs”**, seguida da execução parcial de atualização de header e CSS. **Não confundir essa demanda com o desenvolvimento C81 da automação DRAFT**. O checkpoint técnico definitivo dessa implantação é `affiliate_hub_v31/CHECKPOINT_C110_RADAR_TECH_MENUS_SMARTPHONES_COMPUTACAO_TVS_LIVE_2026-11-23.md` (inclui C111). A implementação existente foi concluída e não pode ser repetida.

## Verificações realizadas na retomada
- Consulta WordPress `wp_list_pages(status=publish)`: IDs 333–340 continuam **8/8 publicadas**, nas rotas exatas: `/audio-bluetooth/`, `/smartwatches/`, `/projetores-acessorios/`, `/gadgets-conectividade/`, `/smartphones/`, `/computacao/`, `/tvs/`, `/guias-tecnologia/`.
- Consulta WordPress autenticada `wp_get_post_full(id, post_type=pages, context=edit)` confirmou os oito conteúdos RAW e os slugs, com links internos existentes no markup e links institucionais. Em `/guias-tecnologia/` as três âncoras **`como-escolher`, `compatibilidade` e `antes-de-comprar`** foram encontradas no HTML original.
- Consulta `wp_get_custom_css` retornou stylesheet ativo `twentytwentyfive`, custom_css post ID 56. Conteúdo CSS vivo com **30.421 caracteres idênticos** ao export versionado `affiliate_hub_v31/exports/C110_RADAR_TECH_CUSTOM_CSS_FINAL_2026-11-23.css`.
- Navegador conectado com aba pública Radar Tech BR exibiu menu **Início | Tecnologia ▾ | Smartphones | Computação | TVs | Guias de Compra ▾ | Loja**; links dos dois submenus apontando para hubs reais; CTA de Loja, carrossel com cinco destaques de assuntos tecnológicos, atalhos adicionais e seção **Novidades em tecnologia** visíveis no texto acessível. Auditoria de DOM detalhada/responsividade de hardware não foi repetida nesta sessão.
- Fonte GitHub `C110_RADAR_TECH_HUBS_PUBLISH_MANIFEST_2026-11-23.json`: os 8 IDs/URLs têm selo histórico LIVE_VERIFIED, e C110 registra 37 posts LIVE, 15 drafts preservados, sem ativação do LIVE automático. C111 registra remoção de assuntos fora do nicho do carrossel e filtro da HOME para categoria Tecnologia ID3; isso **não** representa remoção dos posts antigos.
- `wp_get_template` retornou `{}` nesta sessão para header/home, portanto **não** declarar novo readback exato dos templates FSE nesta retomada. A verificação da navegação pública e o checkpoint anterior C110/C111 são a evidência apropriada para essas partes.

## Pendências legítimas — não refazer etapas concluídas
1. Se solicitado, fazer QA visual desktop/mobile com interação real dos dropdowns e confirmar carrossel sob toque em hardware/navegador suportado. HTML/CSS e clique desktop foram anteriormente checados.
2. Revisar SEO/indexação pelo GSC C104 antes de ampliar volume; diferenciar páginas indexadas de páginas apenas publicadas.
3. Fazer curadoria SEO-segura dos artigos legados fora do foco tecnológico (não deletar sem redirects e evidências). A categoria antiga `Guias de Compra` continua mista; menu novo usa o hub curado em vez de arquivo misturado.
4. Se futuramente criar categorias Smartphones/Computação/TVs, somente quando houver coleção real de artigos e política editorial apropriada; os 3 hubs atuais são páginas editoriais, não taxonomias.
5. Preservar backups FSE/CSS C110 e HOME C111; mudanças no tema podem fazer reaparecer arquivos antigos; não sobrescrever sem GET/backup do estado mais recente.
6. AUTO LIVE V31 continua **OFF** e esta retomada não autoriza qualquer disparo editorial.

**Mutações nesta retomada:** apenas documento de checkpoint e referência no índice da `main`; zero alterações no CMS, nos templates, CSS, catálogo R2, D1, campanhas e sistema de publicação.
