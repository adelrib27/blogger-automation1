# V31 C110 — Radar Tech BR: menus especializados + 8 hubs publicados, inclusive Smartphones, Computação e TVs

**Data:** 23/11/2026 • **Status:** CONCLUÍDO e HOMOLOGADO (publicação manual WordPress).
**Pedido do proprietário:** aplicar menu/submenus propostos na C109 e ampliar Radar Tech BR para **Smartphones, Computação e TVs**.
**Site:** https://radartechbr.com.br/

## 8 páginas editoriais criadas e publicadas
| ID WP | Página | URL | Função |
|---:|---|---|---|
| 333 | Áudio e Bluetooth | https://radartechbr.com.br/audio-bluetooth/ | Hub com 4 artigos LIVE de áudio |
| 334 | Smartwatches | https://radartechbr.com.br/smartwatches/ | Hub com 2 artigos LIVE de relógios |
| 335 | Projetores e acessórios | https://radartechbr.com.br/projetores-acessorios/ | Guia de compatibilidade e 1 post relacionado |
| 336 | Gadgets e conectividade | https://radartechbr.com.br/gadgets-conectividade/ | Hub de 6 artigos tecnológicos |
| 337 | **Smartphones** | https://radartechbr.com.br/smartphones/ | Novo guia sobre sistema, memória, câmera, bateria, redes e segurança (sem falsa análise de aparelhos) |
| 338 | **Computação** | https://radartechbr.com.br/computacao/ | Novo guia sobre notebooks, PCs, armazenamento, processador, periféricos e ergonomia |
| 339 | **TVs e Smart TVs** | https://radartechbr.com.br/tvs/ | Novo guia sobre tamanho, resolução, painel, recursos de jogos, conectividade e instalação |
| 340 | Guias de Compra de Tecnologia | https://radartechbr.com.br/guias-tecnologia/ | Hub curado com links de artigos tecnológicos e seções `#como-escolher`, `#compatibilidade`, `#antes-de-comprar` |

Todos os 8 corpos foram preparados, revisados e salvos previamente em `affiliate_hub_v31/C110_RADAR_TECH_HUBS_HTML_READY_2026-11-23.json`. Conteúdos têm aprox. 444–552 palavras visíveis, perguntas frequentes, links internos reais para posts LIVE e aviso editorial, sem especular modelos/preços ou fingir testes. Primeiro publicados como rascunhos e TODOS conferidos em `wp_list_pages(context=edit,raw_columns=true)` como HTML exatamente idêntico ao artefato; depois publicados e reconfirmados `status=publish` com slugs e permalinks corretos.

**As verticais Smartphones, Computação e TVs são PÁGINAS EDITORIAIS, não novas categorias WordPress ainda.** Isso evita categorias de arquivo vazias ou rotas inexistentes. Quando houver artigos suficientes, classificar em taxonomias pode ser considerada em ciclo futuro. A rota automática V31 em `site_routes.json` ainda permite somente `tecnologia/gadgets` e `publish_enabled=false`; não inventar nichos Shopee/R2 sem validar a classificação.

## Menu principal implantado, responsivo e acessível
Navegação no header `wp_template_part` WordPress Twenty Twenty-Five ID66, original preservado.
**Início | Tecnologia ▾ | Smartphones | Computação | TVs | Guias de Compra ▾ | Loja**.
- Submenu **Tecnologia**: Todos os artigos de tecnologia; Áudio e Bluetooth; Smartwatches; Projetores e acessórios; Gadgets e conectividade.
- Submenu **Guias de Compra**: Central de guias de tecnologia; Como escolher; Compatibilidade; Antes de comprar (links para IDs HTML reais em `/guias-tecnologia/`).
- Top bar **Sobre e Contato** preservada e botão de busca mantido. Reduz duplicação de links utilitários.
- HTML usa `<details><summary>` (interação nativa de clique/touch/teclado), links reais `<a href>`, com estilos CSS no WordPress `custom_css` post ID56, seletores `rt-c110-*`. Estilos evitam clipping/overflow horizontal antigo no celular e mantêm foco visível, dropdown acessível e quebra de linha no mobile. **Teste no navegador Firecrawl desktop** confirmou ambos dropdowns com links presentes e expandidos; mobile HTML+CSS confirmado, mas interatividade tátil em dispositivos reais não foi testada em hardware.
- Homepage `wp_template` home ID42 passou a conter atalhos adicionais Smartphones, Computação e TVs e mudou Guias de Compra de `/category/guias-de-compra/` (misturado com posts fora do nicho) para o hub curado `/guias-tecnologia/`.

## Backups e arquivos finais — NÃO sobrescrever às cegas
- Backup integral FSE pre-C110 (header/home): `affiliate_hub_v31/backups/C110_RADAR_TECH_PRE_NOVOS_MENUS_2026-11-23.json` commit `bf84f00046d157b5a7c6588622759410f96f0d49`.
- Backup CSS WordPress antes do menu: `affiliate_hub_v31/backups/C110_RADAR_TECH_CUSTOM_CSS_BEFORE_MENUS_2026-11-23.css`, commit `d92addaa1a17dd1f1706c658fab4f004493e419d`.
- Header final: `affiliate_hub_v31/exports/C110_RADAR_TECH_HEADER_FINAL_2026-11-23.html`, commit `2ef9aaa01de519bfaf63e97c51c096d0b8898df3`, aplicado via `wp_update_template` e conferido byte-a-byte no DB.
- CSS final: `affiliate_hub_v31/exports/C110_RADAR_TECH_CUSTOM_CSS_FINAL_2026-11-23.css`, commit `0e5304038dc04e9da5ad716a949d0d295e9a1487`, aplicado via WPVibe `post update 56 --post_content_base64=...`, conferido byte-a-byte; CSS público normalizado aparece no HTML.
- Home C110 com seis atalhos (antes de harmonizar carrossel): `affiliate_hub_v31/exports/C110_RADAR_TECH_HOME_FINAL_2026-11-23.html`; a versão ativa final da HOME é a C111 (abaixo).
- Manifesto anti-duplicação com 8 IDs e URLs: `affiliate_hub_v31/C110_RADAR_TECH_HUBS_PUBLISH_MANIFEST_2026-11-23.json`.

## Homologação / segurança
- WP API final antes do último ajuste: **37 posts LIVE + 15 drafts preservados** e 8 hubs novos LIVE, sem excluir nenhum dos artigos anteriores. Taxonomias atuais Tecnologia e Guias de Compra intocadas.
- Firecrawl RAW HTML fresco HTTP200 na HOME e nos hubs verificados (incl. Smartphones, Computação, TVs, Guias Tecnologia, Áudio, Smartwatches, Projetores e Gadgets). HTML contém os links, menu, 2 submenus, CSS público, textos e páginas sem 404.
- No primeiro hub Áudio, 4 artigos reais relacionados presentes, perguntas frequentes e aviso editorial.
- `/guias-tecnologia/` expõe âncoras funcionais das seções citadas no dropdown.
- Nenhum site Blogger ou WordPress além de Radar Tech foi alterado; páginas Loja/Sobre/Contato/legais, textos dos 37 posts, D1/R2, Pinterest e Cloudflare intactos. V31 automático LIVE permanece OFF.

## Coerência da HOME — etapa C111 também executada
- O carrossel ainda mostrava categorias antigas Casa & Decoração, Ferramentas & Automotivo e Moda & Beleza. C111 substituiu slides fora do nicho por 2 guias reais de tecnologia (áudio Bluetooth e smartwatch), renomeou a chamada de scanner para conectividade, e manteve 5 slides e 5 botões.
- `wp:query` de publicações recentes foi alterado para `inherit=false`, `taxQuery={"category":[3]}`, perPage 10, reduzindo recomendações recentes só à categoria **Tecnologia** (14 posts LIVE). HTML público confirmou 10 posts recentes de tecnologia, sem itens de moda, cozinha ou ferramentas.
- A HOME ativa atual é `affiliate_hub_v31/exports/C111_RADAR_TECH_HOME_TECH_ONLY_CAROUSEL_LATEST_PREVIEW_2026-11-23.html`, com backup C111 em `affiliate_hub_v31/backups/C111_RADAR_TECH_HOME_BEFORE_TECH_CAROUSEL_2026-11-23.html`. A atualização foi conferida exata no DB. Post individual antigo fora do nicho **continua online** em URL própria, aguardando eventual migração SEO-segura; não confundir filtro da homepage com exclusão do post.

**C110 CONCLUÍDA / C111 CONCLUÍDA. Não duplicar hubs ou reexecutar gravações sem conferir os IDs e o conteúdo atual do site.**
