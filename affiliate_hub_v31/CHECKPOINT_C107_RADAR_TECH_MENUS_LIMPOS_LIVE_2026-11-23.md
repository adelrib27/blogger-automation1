# V31 C107 — Radar Tech BR: menus antigos removidos e homologados LIVE

**Data:** 23/11/2026. **Site:** https://radartechbr.com.br/ (WordPress).
**Pedido do usuário:** “faltou eliminar os menús” após exclusão C106 das categorias fora do nicho.

## Causa confirmada
O tema ativo é **Twenty Twenty-Five (block theme / Full Site Editing)**. O WordPress contém zero menus clássicos em `wp_list_menus` e a navegação `wp_navigation` ID4 é somente `<!-- wp:page-list /-->`. Os menus visíveis que ainda apontavam para as categorias excluídas estavam **embutidos em blocos estáticos de templates personalizados no banco**:
- `wp_template_part` header: post ID **66**, slug `header`, API template ID `twentytwentyfive//header`.
- `wp_template` home: post ID **42**, slug `home`, API template ID `twentytwentyfive//home`.

Por isso a exclusão de categorias C106, sozinha, não removeu atalhos da interface.

## Segurança: tudo salvo antes das alterações
- Backup **HTML Gutenberg integral do cabeçalho antes**: `affiliate_hub_v31/backups/C107_RADAR_TECH_HEADER_LIVE_TEMPLATE_BEFORE_MENUS_2026-11-23.html` (3.426 chars, commit `d8380ca115b9e635a84c3963ac707c5449da343d`).
- Backup **HTML Gutenberg integral da home antes**: `affiliate_hub_v31/backups/C107_RADAR_TECH_HOME_LIVE_TEMPLATE_BEFORE_MENUS_2026-11-23.html` (20.711 chars, commit `8e17d68b5820de29fd94092027ef4423bf75cdaf`).
- Checkpoint ANTES das mutações: `affiliate_hub_v31/CHECKPOINT_C107_RADAR_TECH_PRE_APLICACAO_MENUS_2026-11-23.md`, commit `eafd675e1c0216c06c625ec73d9e6f911f079da1`.
- Prévias finais antes do CMS: `affiliate_hub_v31/exports/C107_RADAR_TECH_HEADER_TECH_ONLY_PREVIEW_2026-11-23.html` (3.247 chars, commit `dce16a94a9394670323c88d325a2ca4820e0a01b`) e `affiliate_hub_v31/exports/C107_RADAR_TECH_HOME_TECH_ONLY_PREVIEW_2026-11-23.html` (14.548 chars, commit `4e13f8dec17052b7fc23fc0b77cbb57847ca6ca9`).

## Alterações executadas
1. **Header:** trocada somente a navegação secundária estática `rt-v2-trending` para **Loja, Tecnologia, Guias de compra**. Menu principal com Loja Radar Tech BR, Sobre, Contato e acesso de pesquisa foi preservado. Antes existia 1 link de cada categoria obsoleta `casa-decoracao`, `cozinha-utilidades`, `moda-beleza`, `ferramentas-automotivo`.
2. **Homepage:** eliminadas **15 referências** às quatro categorias antigas do modelo personalizado:
   - Promoção secundária “Casa & decoração” substituída por destaque de áudio/conectividade dentro de Tecnologia.
   - Grade de atalhos `rt-v2-category-grid` passa a oferecer **Tecnologia, Guias de compra e Loja Radar Tech BR**; título atualizado para “Explore o Radar Tech BR”.
   - 3 cards editoriais de Casa, Cozinha e Ferramentas substituídos por guias técnicos já publicados (áudio Bluetooth, smartwatch e acessórios de projetor), URLs existentes e cores abstratas no lugar das imagens erradas. Primeiro card de Tecnologia preservado.
   - Seção `rt-v3-category-feed-section` inteira removida por listar posts de categorias IDs 4/5/6/7 já excluídas. **Outros blocos da home** (carrossel de destaque, últimas publicações, rodapé e layout global) foram preservados.
3. Ambas as escritas feitas via **WordPress `wp_update_template`** (header tipo `template_part`, home tipo `template`), individualmente e com precondição de conteúdo original byte-a-byte. Após **cada** gravação, WPVibe SELECT conferiu o conteúdo da template no banco **exatamente igual** ao arquivo final do GitHub.
4. Teste de integridade dos blocos Gutenberg: zero blocos abertos/fechados incorretamente nas duas prévias.

## QA independente
**Firecrawl RAW HTML fresco, HTTP 200:**
- **Home desktop**: nav visível `Loja · Tecnologia · Guias de compra`; 0 links e 0 labels antigos de categorias excluídas, novos cards de tecnologia, sem bloco de categorias obsoletas; rodapé e publicações recentes presentes.
- **Home mobile**: HTTP200, mesmo nav correto, zero URLs excluídas.
- **Post individual** `/caixa-som-kapbom-ka-8955-guia-antes-da-compra/`: HTTP200, nav correto e sem atalhos antigos.
- **Categoria Tecnologia** `/category/tecnologia/`: HTTP200, nav correto e sem atalhos antigos.
**WordPress API após alterações**: 52 posts preservados (37 LIVE e 15 drafts). Permanecem só categorias ID1 Guias de Compra e ID3 Tecnologia. Todas as quatro categorias retiradas da taxonomia C106 continuam ausentes.

## Limites importantes
- **Não foram apagados artigos de outras categorias**. Como C106 já explicou, diversos posts fora do foco seguem temporariamente na categoria `Guias de Compra`. Eles podem aparecer em listagens recentes, mas não são mais promovidos pelos menus de categorias excluídas. Limpeza editorial posterior precisa considerar URLs indexadas e receita/SEO antes de remoções.
- Os arquivos originais do **tema no filesystem** ainda podem conter menus antigos, porém as **customizações FSE salvas no banco**, que são as atualmente exibidas ao visitante, foram efetivamente corrigidas. Se alguém apagar as personalizações do Site Editor ou redefinir o tema, a navegação antiga pode voltar: verificar o menu ao trocar/restaurar tema.
- `wp_navigation` ID4 não foi alterado; menus clássicos inexistentes não foram recriados.
- Nenhuma URL de post, slug, conteúdo, rascunho, página Loja, tema ativo, rota GitHub, Cloudflare, Blogger, Pinterest, D1/R2 ou política de publicação LIVE foi alterada neste ciclo.
- A rota `wordpress_radartechbr` no GitHub continua restrita a `["tecnologia/gadgets"]` e `publish_enabled=false` desde C106.

## Retomada sem repetição
- **C107 CONCLUÍDA. Não reaplicar os templates sem reler o banco.**
- Para reproduzir/rollback, usar os dois backups C107 de templates e `wp_update_template` por ID. Confirmar nenhum editor mexeu no modelo entre a decisão de reverter e a escrita.
- Pendências independentes: otimização editorial de posts não tech em Guias de Compra, eventual auditoria SEO/redirects de URLs de categorias eliminadas, evitar reexposição após troca do tema.
