# V31 C108 — Radar Tech BR: seção de destaques renovada com imagens reais (23/11/2026)

**Site:** https://radartechbr.com.br/ — WordPress Twenty Twenty-Five. **Escopo pedido:** melhorar visualmente a seção de quatro cards "Achados em destaque" apontada em captura enviada pelo proprietário.
**Estado:** MODELO HOME ATUALIZADO E RELIDO DO WORDPRESS; HTML PÚBLICO VALIDADO EM DESKTOP E MOBILE.

## Problema original
- Card 1 mostrava imagem ilustrativa de tecnologia; os demais três tinham fundos coloridos e ícones pequenos, sem fotos dos artigos/produtos.
- A seção parecia desequilibrada, com espaços visuais vazios e pouco apelo editorial/comercial.
- A origem estava na personalização Full Site Editing `wp_template` **ID 42**, slug `home`, identificador `twentytwentyfive//home`, não em menu clássico nem artigos.

## Solução implantada (somente Home, nenhuma mudança global)
- Título alterado para **"Guias de tecnologia em destaque"**, atalho final **"Explorar tecnologia"** direcionado à categoria Tecnologia, que mantém exclusivamente os posts classificados no nicho.
- Quatro cards com layout e dimensões consistentes; card 1 mantém imagem de tecnologia `Radar-Tech-BR-Tecnologia.png`, e 3 cards passam a ter FOTOS REAIS do próprio acervo de mídia WordPress e links de artigos LIVE:
  1. **Tecnologia:** `/category/tecnologia/`, capa ilustrativa já existente.
  2. **Áudio e Bluetooth:** post `/caixa-som-kapbom-ka-8955-guia-antes-da-compra/`, imagem `/wp-content/uploads/2026/10/Caixa-de-som-Kapbom-KA-8955.jpg`, attachment WordPress ID69.
  3. **Smartwatches:** post `/como-escolher-um-relogio-inteligente-com-tela-infinita/`, imagem `/wp-content/uploads/2026/10/como-escolher-um-relogio-inteligente-com-tela-infinita.jpg`, attachment ID137.
  4. **Projetores e acessórios:** post `/controle-remoto-para-projetor-portatil/`, imagem `/wp-content/uploads/2026/11/controle-remoto-projetor-portatil-mini-hy300-hy320-infravermelho.jpg`, attachment ID279.
- Descrições e CTAs dos cards foram ajustados para linguagem prática, sem prometer testes ou vendas. Fotos usam `loading=lazy`, alt descritivo e `object-fit:contain`, mantidas dentro de área `height:222px` com fundos leves e bordas consistentes.
- **Importante sobre CSS:** a primeira prévia incluiu `<style>` embutido no bloco, que o WordPress **armazenou no banco porém removeu do HTML público**. Foi corrigido no mesmo ciclo: a versão final contém apenas estilos **inline aceitos no HTML público** para dimensionamento, cores, bordas e fotos. Responsividade estrutural da grade permanece responsabilidade do CSS existente no tema. NÃO afirmar que CSS embutido da primeira prévia estava ativo.

## Arquivos de segurança e previews
- Original completo HOME antes de editar: `affiliate_hub_v31/backups/C108_RADAR_TECH_HOME_BEFORE_FEATURED_CARDS_2026-11-23.html` — commit `e756f7604e6156aa9458ebf96ec2d84c6f625516`.
- Primeira versão em prévia (CSS embutido posteriormente removido do render): `affiliate_hub_v31/exports/C108_RADAR_TECH_HOME_FEATURED_REAL_IMAGES_PREVIEW_2026-11-23.html`, commit `ec2322c8c1e75010213864e096af38068d02e3f0`.
- **Versão final aplicada:** `affiliate_hub_v31/exports/C108_RADAR_TECH_HOME_FEATURED_INLINE_STYLES_FINAL_2026-11-23.html`, commit `0e29e7bef601ce503911d2cccb7fee0356dbe87d`.
- Em cada etapa, a API autenticada `wp_update_template(template_id=twentytwentyfive//home)` aplicou apenas o conteúdo da Home. A leitura posterior do DB via WPVibe mostrou correspondência **byte-a-byte** com o template esperado (17.053 chars primeira versão, **16.911 chars final**). Markup de blocos Gutenberg foi validado com pilha de abertura/fechamento, sem inconsistências.

## Homologação pública e limites de confirmação
- Firecrawl RAW HTML fresco: HTTP200 desktop e mobile, título correto, **4 anchors de card**, **3 tags img com as URLs exatas**, **4 elementos visuais com altura inline 222px**, 3 estilos `object-fit:contain` e misturas para fotos; links apontam para URLs de posts publicados; zero links para categorias removidas de moda, cozinha, casa e ferramentas.
- Screenshot de verificação foi capturado pelo serviço, porém sua análise visual manual da imagem renderizada NÃO foi concluída neste ciclo. A validação documentada comprova o HTML servido e sua estrutura, não o carregamento do JPG no navegador de cada visitante.
- A página principal preserva cabeçalho e rodapé C107, posts recentes, carrossel existente, Loja e links legais. **Nenhum conteúdo de artigos foi editado**; categorias C106 seguem as duas já homologadas.
- AUTO LIVE do V31 permanece OFF. Não alterar roteamento, automações, outros blogs, D1/R2, Cloudflare ou Pinterest.

## Restauração
Se o visual final causar problema, comparar primeiro o template atual do DB ID42 com o arquivo final aplicado; só se estiver idêntico restaurar o backup C108 original por `wp_update_template`, reler DB e conferir HTML público. Evitar rollback cego se um editor já alterou a home.
**C108 concluída para HTML / deploy.**
