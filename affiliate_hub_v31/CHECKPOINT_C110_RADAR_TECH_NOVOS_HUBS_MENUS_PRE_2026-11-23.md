# V31 C110 — Execução autorizada: menus especializados e novos eixos Radar Tech BR

**Data:** 23/11/2026. Pedido do usuário: aplicar a proposta de C109, ampliando para **Smartphones, Computação e TVs**.
**Estado:** pré-execução, backup realizado, ainda sem novas páginas.

## Fontes inspecionadas
- C109: `affiliate_hub_v31/CHECKPOINT_C109_PROPOSTA_NAVEGACAO_RADAR_TECH_BR_2026-11-23.md`.
- WordPress `list_posts`: 37 posts LIVE (14 Tecnologia, 23 Guias de Compra). Categorias Tecnologia ID3, Guias ID1, esta ainda mistura nichos.
- WordPress `list_pages(status=any)`: 8 páginas LIVE + 1 draft "Início", nenhum dos slugs dos novos hubs ocupa URL existente.
- Tema: Twenty Twenty-Five, templates FSE: header post ID66, home ID42. Backup completo antes de modificações: `affiliate_hub_v31/backups/C110_RADAR_TECH_PRE_NOVOS_MENUS_2026-11-23.json`.
- CSS adicional WordPress já existe: post tipo `custom_css` ID56, 26.631 caracteres, com regras legadas de overflow horizontal no menu mobile. Se usar dropdown na barra do cabeçalho, precisa retirar clipping e fornecer navegação móvel nativa acessível. Não alterar CSS sem backup antes.
- WordPress páginas legadas preservadas: Loja, Sobre, Contato, Política Editorial, Transparência e Afiliados, Termos, Privacidade, Cookies.

## Novo sistema editorial
1. Criar **8 páginas HUB com corpo útil não vazio**, incluindo **três verticais novas** para smartphones/computação/TVs: `audio-bluetooth`, `smartwatches`, `projetores-acessorios`, `gadgets-conectividade`, `smartphones`, `computacao`, `tvs`, `guias-tecnologia`.
2. Hubs existentes devem listar somente posts LIVE de seus temas via URLs reais verificadas. Nos novos hubs, escrever guias editoriais honestos de decisão de compra, sem prometer reviews, fotos de produtos ou avaliações inexistentes. Usar links complementares só quando verdadeiramente relacionados.
3. Navbar recomendada: **Início | Tecnologia ▾ (Áudio/Bluetooth, Smartwatches, Projetores, Gadgets) | Smartphones | Computação | TVs | Guias de Compra ▾ (Como escolher, Compatibilidade, Antes de comprar) | Loja**, mantendo Sobre/Contato utilitário, busca e páginas legais no rodapé.
4. Submenu Guias apontar ao **novo hub `/guias-tecnologia/`** (seções anchor), e não à categoria contaminada `/category/guias-de-compra/`.
5. Testar teclado, mobile, links internos, hover/tecla/click/touch de dropdown. Evitar menu clássico inexistente; editar only FSE header ID66. Uso de custom CSS pode ser necessário, com backup/restore e seletores prefixados.
6. Preservar 37 posts existentes, Loja, C107/C108, rotas GitHub com allowed_niches tech e `publish_enabled=false`. Não ativar V31 AUTO LIVE, não alterar R2/D1/Pinterest.
7. **Garantir checkpoint incremental com IDs das novas páginas e validação GET WordPress antes de alterar nav**. Se quota interromper a rodada, registrar estado e não publicar link para 404.

## Critérios de QA
- Homepage, mobile, páginas novas, link da Loja e páginas institucionais HTTP200;
- Nenhum link para categoria antiga /category/casa-decoracao etc;
- Hubs novos não apresentarem alegações não confirmadas sobre preços, especificações ou testes;
- Todos os 8 slugs existirem/publicados antes da mudança do cabeçalho;
- Backup de CSS, header e URLs e novo readback dos conteúdos aplicados.
