# V31 C107 — Pré-publicação da limpeza dos menus Radar Tech BR (23/11/2026)

## Solicitação
O proprietário apontou que, apesar da C106 ter excluído quatro categorias fora do nicho WordPress, os menus da página inicial ainda exibiam Casa, Cozinha, Moda e Ferramentas.

## Diagnóstico autenticado
- WordPress Twenty Twenty-Five, tema de blocos; **zero menus clássicos** e apenas uma navegação de bloco `wp_navigation` ID4 com `<!-- wp:page-list /-->`. **Não alterar este objeto padrão.**
- Os links incorretos realmente estavam **incorporados no conteúdo dos blocos** de `wp_template_part` **header** ID66 e `wp_template` **home** ID42, obtidos via consulta autenticada somente-leitura do WPVibe. O Wordpress MCP `wp_get_template` retornou objeto vazio, logo o conteúdo original foi capturado pelo WPVibe `db query SELECT`, e reconferido.
- Home tinha **15 referências** aos quatro slugs excluídos; Header outras **4 referências**.
- Home também tinha uma seção inteira `rt-v3-category-feed-section` que consultava diretamente categorias inexistentes IDs4/5/6/7. Deixar assim criaria menus e cards vazios, por isso a prévia remove essa seção.
- O site precisa manter a navegação útil: `/loja/`, `/category/tecnologia/`, `/category/guias-de-compra/`, `/sobre/`, `/contato/`, além dos documentos legais no rodapé. **Nenhuma categoria excluída deve ser recriada.**

## Backups obtidos ANTES de escrita em CMS
- Header FULL original (3.426 caracteres) `affiliate_hub_v31/backups/C107_RADAR_TECH_HEADER_LIVE_TEMPLATE_BEFORE_MENUS_2026-11-23.html`, commit `d8380ca115b9e635a84c3963ac707c5449da343d`.
- Home FULL original (20.711 caracteres) `affiliate_hub_v31/backups/C107_RADAR_TECH_HOME_LIVE_TEMPLATE_BEFORE_MENUS_2026-11-23.html`, commit `8e17d68b5820de29fd94092027ef4423bf75cdaf`.

## Prévias preparadas e validadas no GitHub, antes de aplicar
- Header tech-only `affiliate_hub_v31/exports/C107_RADAR_TECH_HEADER_TECH_ONLY_PREVIEW_2026-11-23.html`, commit `dce16a94a9394670323c88d325a2ca4820e0a01b`: menu secundário Loja / Tecnologia / Guias de compra.
- Home tech-only `affiliate_hub_v31/exports/C107_RADAR_TECH_HOME_TECH_ONLY_PREVIEW_2026-11-23.html`, commit `4e13f8dec17052b7fc23fc0b77cbb57847ca6ca9`: remove grade de menus e cards vazios de categorias excluídas, mantém links de tecnologia/guias/loja, preserva carrossel, posts recentes, rodapé e seções editoriais, atualiza três cards de destaque com links de posts reais: caixa de som, smartwatch e projetor.
- Validador de bloco Gutenberg conferiu abertura/fechamento íntegros, zero links para quatro categorias excluídas em ambas as prévias, âncoras necessárias presentes. Não confundir prévia com publicação confirmada.

## Aplicação e QA a executar
1. Antes de cada escrita: reler DB `wp_template_part` ID66 e `wp_template` ID42 para confirmar conteúdo original ainda exato, evitando sobrescrever alteração concorrente.
2. Aplicar uma template por vez usando `wp_update_template` (`type=template_part` para header, `template` para home).
3. **Reconsultar os valores de conteúdo reais no banco** por WPVibe SELECT antes de prosseguir, garantindo que houve mudança. Tratar retorno vazio da ferramenta WP como situação ambígua até readback.
4. Verificar HTML público (cache fresco) e links úteis. Se quebra de renderização ou diferença inesperada, reverter usando backups exatos.
5. Não tocar em posts, categorias C106, rascunhos, páginas Loja, HMAC, automação V31 LIVE, outros blogs, R2/D1, Pinterest.

**Estado deste checkpoint: Prévia + backup completos; nenhuma escrita nos modelos WordPress C107 iniciada.**
