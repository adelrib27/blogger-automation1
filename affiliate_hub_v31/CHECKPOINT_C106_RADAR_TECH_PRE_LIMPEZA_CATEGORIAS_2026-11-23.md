# V31 C106 — RADAR TECH BR: limpeza de categorias fora do nicho — checkpoint ANTES DAS ALTERAÇÕES
**Data:** 23/11/2026. **URL:** https://radartechbr.com.br/ WordPress.
**Pedido expresso:** eliminar categorias que não combinam com o domínio e título do site, agora posicionado em tecnologia, eletrônicos, casa inteligente e guias práticos.

## Evidência e backup
- Leitura autenticada via WordPress: 6 categorias, **52 posts no total (37 publicados + 15 drafts)**, menu WordPress tradicional 0, tema em blocos sem sidebars clássicas.
- **Backup anterior a qualquer modificação:** `affiliate_hub_v31/backups/C106_RADAR_TECH_CATEGORY_INVENTORY_BEFORE_2026-11-23.json` (categorias originais, IDs, descrições, IDs/estados/URLs/tags/categorias dos 52 artigos; não é backup de HTML integral).
- Categoria default atual: `Guias de Compra` ID **1**, mantida para não atribuir falsamente artigos de moda/casa ao nicho de Tecnologia.
- Categoria `Tecnologia` ID **3** permanece.
- Exclusão requerida: `Casa & Decoração` ID **4**, `Cozinha & Utilidades` ID **5**, `Moda & Beleza` ID **6**, `Ferramentas & Automotivo` ID **7**. **Excluir categorias NÃO apaga os posts**, mas altera seus vínculos de taxonomia. Categoria deletada não possui lixeira; backup permite reconstruir nomes/slugs, não IDs originais.
- Ajustes de atribuição pertinentes: tecnologia com equivalência explícita, `Scanner OBD2 Bluetooth` ID **28**, `Lanterna tática P90` ID **27**, `Ventilador portátil com resfriamento e iluminação` ID **256** podem ser classificados em Tecnologia; `Ferro Elgin` ID **31**, `Mixer 2 em 1` ID **30**, `Kemei` ID **22** devem sair de Tecnologia e ir para Guias de Compra, pois não são gadgets do escopo técnico central. **Sem edição de texto, títulos, slugs ou status**.
- Artigos de casa, cozinha, moda e ferramentas que permanecerem LIVE serão temporariamente classificados sob Guias de Compra. **Isso ainda não resolve a incompatibilidade temática nas páginas/home; exige migração/retirada editorial posterior, individualizada e com URLs redirecionadas corretamente.** Não apagar posts apenas para parecer que o site é 100% tech.
- Validar GET de categorias, posts, total 37 publish / 15 draft, URLs intactas antes de declarar conclusão.
- Registro no GitHub antes, durante e após alterações. Não tocar nos outros WordPress, Blogger, lojas, Cloudflare, Pinterest, D1/R2 ou mecanismos V31 LIVE.
- Nenhuma automação LIVE deve ser ativada. Guard futuro: novos artigos Radar Tech devem ser estritamente do domínio de Tecnologia e categorias correspondentes, não instrumentos genéricos de casa/beleza/ferramentas.

## Estado de partida
- Backup confirmado no commit `d10c5714a5e71b5845d1213b69a1c160454842d0`. 
- Checklist de mutações pendentes: remover classificações incorretas, promover 3 posts técnicos, deletar quatro categorias com reatribuição default id1, reler dados, manter 52 posts íntegros.
