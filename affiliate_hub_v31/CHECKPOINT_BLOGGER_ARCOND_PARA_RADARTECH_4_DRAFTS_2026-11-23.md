# V31 — Salvamento dos quatro artigos do Blogger Ar-Condicionado no Radar Tech BR
**Data:** 2026-11-23 (America/Recife). **Fase:** preparação editorial em WordPress DRAFT, sem LIVE.
**Solicitação do proprietário:** aproveitar os quatro artigos do blog `https://ar-condicionado-sem-duvidas.blogspot.com/` no WordPress `https://radartechbr.com.br/` antes da exclusão manual do Blogger.
**Fonte:** Blogger API v3 (blog ID `2228849984262880811`); WordPress Radar Tech BR via conector autenticado. 4 artigos publicados lidos com HTML integral. Outros 10 conteúdos de páginas preservados no backup pré-exclusão.

## Preflight
- Radar Tech possui categoria WordPress **Ar-condicionado**, ID **20**, filha de Tecnologia ID3. A categoria já existia e tinha 0 posts publicados no início; nenhuma categoria nova foi criada.
- Radar Tech mantém núcleo tecnológico e publicação automática V31 LIVE desativada.
- Leitura WordPress de títulos LIVE (37 posts) e DRAFT (15 antigos) não apontou títulos idênticos aos quatro artigos criados nesta migração.
- Backup completo anterior do Blogger com 4 posts e 10 páginas foi validado byte a byte e permanece em Google Docs: https://docs.google.com/document/d/1fkVydzea_FLyIXEunxc0y8PC24x09jbKV6ykaQsuFwg/edit
- Diagnóstico C104 do GSC registrou 0 impressões e 0 cliques na propriedade Ar-Condicionado no período final 20/08–20/11/2026 e amostra de duas URLs detectadas, mas não indexadas. Isso NÃO demonstra que as quatro URLs não possuem links externos ou que dados mais recentes são iguais.

## Migrações REAIS confirmadas na API WordPress
Cada artigo foi **reescrito editorialmente**, com foco técnico, links para referências verificáveis quando pertinentes, perguntas frequentes e avisos de limites das especificações. Sem duplicar HTML anterior, sem transferir imagem de anúncio, preço ou link afiliado de outro blog.

| Origem Blogger (post ID) | URL origem | WordPress Radar Tech (DRAFT ID) | Título WordPress | Categoria |
|---|---|---:|---|---|
| `1105804294944604726` | https://ar-condicionado-sem-duvidas.blogspot.com/2026/11/antes-de-instalar-ar-condicionado-split.html | **353** | Instalação de ar-condicionado split: checklist técnico antes da compra | 20 |
| `8208866544157240159` | https://ar-condicionado-sem-duvidas.blogspot.com/2026/11/midea-lite-conectado-inverter-9000-btus.html | **354** | Ar-condicionado conectado de 9.000 BTUs: Wi-Fi, app e ficha técnica | 20 |
| `8847875310080419457` | https://ar-condicionado-sem-duvidas.blogspot.com/2026/11/midea-ai-ecomaster-inverter-12000-btus.html | **355** | Midea AI Ecomaster 12.000 BTUs: quais funções e dados técnicos conferir | 20 |
| `940950273343255024` | https://ar-condicionado-sem-duvidas.blogspot.com/2026/11/ar-condicionado-lg-dual-inverter.html | **356** | LG Dual Inverter Compact 12.000 BTUs: comparação técnica antes de comprar | 20 |

**Evidência WordPress após criação:** `wp_list_posts(status=draft,context=edit,raw_columns=true)` devolveu todos os quatro IDs, títulos, slugs, status `draft`, categoria `[20]` e corpos integrais com comprimentos exatos **5711 / 5624 / 5761 / 5992** caracteres, respectivamente. Cada corpo inclui 9 a 11 headings H2 e cerca de 718 a 796 palavras visíveis. Links para a origem Blogger: **0**; links afiliados antigos `s.shopee.com.br`: **0**; imagens transferidas de Shopee: **0**.

**Status LIVE:** Nenhum destes posts foi publicado; status DRAFT preservado por política V31. As URLs de prévia administrativas são `https://radartechbr.com.br/?p=353` a `?p=356`, não são permalinks públicos publicados e NÃO devem ser submetidos ao sitemap como se estivessem LIVE.

## Gates antes da exclusão manual da origem
1. Revisar os quatro rascunhos e fazer homologação editorial/comercial, especialmente especificações e itens exatos dos modelos; se forem adicionados anúncios Shopee, validar imagem+SKU+link da **campanha Radar Tech BR**, sem reutilizar `offerLink` do Blogger antigo.
2. Aprovar/publicar os posts de forma individual conforme política V31 e confirmar HTTP 200, slug/canonical e links internos.
3. Avaliar as **10 páginas Blogger** (BTUs, Inverter, consumo, instalação e políticas/Loja) que ainda têm links internos dos posts antigos, decidindo se devem ser absorvidas em novas peças ou mantidas em backup. O escopo deste ciclo foi os quatro POSTS solicitados.
4. Verificar GSC/backlinks da origem. Redirect permanente HTTP 301/308 entre Blogspot e WordPress não foi demonstrado e Blogger Custom Redirect é basicamente interno ao mesmo blog. Exclusão do Blogspot sem redirect pode perder acesso e sinais SEO das antigas URLs. Se o usuário aceitar esse risco, só então apagar manualmente.
5. Verificar/congelar fluxos antigos referentes à origem e reler o número de blogs após exclusão.

**Nenhum blog excluído, nenhuma migração LIVE, nenhum workflow/cron ou categoria alterado neste ciclo.** Os cinco Blogger escolhidos seguem intocados. Projeto Pinterest e Mercado Livre intocados.
