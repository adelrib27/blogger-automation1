# V31 C106 — RADAR TECH BR: LIMPEZA DE CATEGORIAS CONCLUÍDA

**Data:** 23/11/2026 • **Site:** https://radartechbr.com.br/ • **Plataforma:** WordPress (domínio próprio).
**Objetivo do proprietário:** eliminar categorias sem afinidade com o nome, domínio e posicionamento “Tecnologia, eletrônicos, casa inteligente e guias práticos”.

## Alterações EFETIVAMENTE executadas e verificadas
1. Foram excluídas **4 categorias WordPress**, via API `wp_delete_category` com `reassign=1`, nesta ordem:
   - ID **6**, **Moda & Beleza** (`moda-beleza`)
   - ID **5**, **Cozinha & Utilidades** (`cozinha-utilidades`)
   - ID **4**, **Casa & Decoração** (`casa-decoracao`)
   - ID **7**, **Ferramentas & Automotivo** (`ferramentas-automotivo`).
2. **2 categorias permanecem**: `Tecnologia` ID **3** e `Guias de Compra` ID **1**, esta última categoria default e agora local de transição dos artigos fora do foco. **Não existe categoria excluída com posts sem categoria**; WordPress reassociou os itens à categoria padrão.
3. Foram ajustadas manualmente as atribuições dos seguintes posts, com `wp_update_post(categories=[...])` e leitura posterior individual confirmando categoria, estado e URL sem mudanças:
   - Scanner OBD2 Bluetooth ID **28** → Tecnologia ID 3
   - Lanterna tática LED P90 ID **27** → Tecnologia ID 3
   - Ventilador portátil com resfriamento e iluminação ID **256** → Tecnologia ID 3
   - Ferro Elgin ID **31** → Guias de Compra ID 1
   - Mixer elétrico 2 em 1 ID **30** → Guias de Compra ID 1
   - Kemei PG-2600 ID **22** → Guias de Compra ID 1.
4. **Auditoria final API autenticada:** 52 posts intactos, **37 publicações + 15 drafts**; TODOS os 52 preservam ID, título, permalink, slug, estado `publish/draft` exatamente iguais aos dados originais. Distribuição:
   - `Tecnologia`: **14 posts LIVE + 1 draft**.
   - `Guias de Compra`: **23 posts LIVE + 14 drafts** (todos preservados, ainda alguns fora do foco temático).
   - Conteúdos e imagens de artigos não foram editados, páginas e Lojas não sofreram alterações.
5. Política de prevenção técnica: `affiliate_hub_v31/site_routes.json`, rota `wordpress_radartechbr` alterada **somente em `allowed_niches`**: ANTES 9 nichos `[tecnologia/gadgets,automotivo/acessorios,ferramentas/eletricas_manuais,casa/decoracao,casa/organizacao,cozinha/air_fryers,cozinha/liquidificadores,beleza/cabelos,moda/vestuario_calcados]`; AGORA **`["tecnologia/gadgets"]`**. `publish_enabled=false` preservado. As outras 19 rotas não foram modificadas. GET GitHub posterior confirmou valores exatos.
6. **Nenhum workflow LIVE foi ativado**; nenhum blog foi excluído e nenhum outro site WordPress/Blogger/Pinterest tocado.

## Segurança e backups
- Inventário integral de IDs/URLs/categorias e estados ANTES da modificação: `affiliate_hub_v31/backups/C106_RADAR_TECH_CATEGORY_INVENTORY_BEFORE_2026-11-23.json`. Commit backup `d10c5714a5e71b5845d1213b69a1c160454842d0`.
- `affiliate_hub_v31/CHECKPOINT_C106_RADAR_TECH_PRE_LIMPEZA_CATEGORIAS_2026-11-23.md`, checkpoint antes das operações. Commit `8bbbc9abf5310cef66a9154fefc6b62398f1b76f`.
- Backup completo do arquivo de rotas de **20 sites** antes do niche-lock: `affiliate_hub_v31/backups/C106_RADAR_TECH_ROUTES_BEFORE_NICHE_LOCK_2026-11-23.json`, commit `8a881a91351698bb6482d78a731f76b9a7ad5a6c`.
- Alteração de `site_routes.json`, commit `a146ac2df1eaeace9cfee59696d6bbcb051d6305`.
- As categorias excluídas são irreversíveis pelo CMS em seus IDs originais; é possível reconstruir nomes/slugs de categorias, mas não seus IDs ou qualquer classificação histórica exata sem mapear os posts com os dados preservados no backup.

## ALERTA — o que ainda falta para Radar Tech ser de fato exclusivamente tecnológico
**A limpeza pedida foi de CATEGORIAS, não de posts.** Os 23 artigos publicados e 14 rascunhos em `Guias de Compra` continuam existentes no Radar Tech, e vários pertencem a casa, moda, cozinha ou ferramentas. Assim, a home e URLs individuais podem permanecer fora do nicho até migração ou revisão apropriada. **Não enganar dizendo que todo conteúdo foi limpo.**
- Etapa posterior recomendada: inventariar URLs e desempenho GSC desses 23 LIVE, decidir para cada uma entre preservar/revisar tecnicamente, absorver com reescrita editorial no blog de nicho correto, colocar em draft/retirar com segurança e mapear redirecionamentos 301 conforme viabilidade. Os 14 drafts não precisam ser publicados. Evitar mover sem avaliar backlinks, campanhas afiliadas, canonical, indexação e redirecionamentos.
- A alteração de nichos é preventiva no nível de **configuração V31**; os workflows que ignorarem `site_routes.json` ou tiverem regras hardcoded exigem auditoria específica antes de reativar. Não afirmar impossibilidade absoluta de publicação indevida sem testar toda a arquitetura.
- A categoria `Guias de Compra` é temporária; poderá ser restrita a guias técnicos após destinação segura dos posts fora do nicho.
- Categoria excluída pode gerar 404 em URLs antigas `/category/...`; checar demanda GSC e configurar redirects específicos quando houver sinais de tráfego, sem redirecionar em massa para home.

**Status C106: 4 categorias excluídas, 6 posts reclassificados, 52 posts preservados, rota V31 restrita ao tech, AUTO LIVE OFF.**
