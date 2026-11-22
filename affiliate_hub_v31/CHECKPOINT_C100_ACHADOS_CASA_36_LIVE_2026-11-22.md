# V31 C100 — Primeiro blog replicado: ACHADOS PARA CASA

**Data:** 22/11/2026 (America/Recife)
**Site:** https://achadosparacasa2026.blogspot.com/p/loja.html
**Blog ID:** `1426630233929943394`
**Page ID existente:** `3841238517239710135`
**Status:** **LIVE**, 36 ofertas na página existente, sem nova página.

## Fontes e curadoria
- R2 READ ONLY: [inventário #45078854741](https://github.com/adelrib27/blogger-automation1/actions/runs/45078854741) — 2.088 produtos moderados/ classificados nos nichos do blog.
- API Shopee de anúncio EXATO: [#45078972630](https://github.com/adelrib27/blogger-automation1/actions/runs/45078972630), job `137382539823`. **80 candidatos R2**, **78 correspondências exatas shopId:itemId** na Affiliate API, **46 ofertas elegíveis** depois de filtros, **36 selecionadas**, **35 vendedores**, **22 com comissão adicional do vendedor >=3% no instantâneo**, consulta real, rating>=4 e vendas>=10; nenhuma mutation de shortlink, nenhuma escrita no R2/D1. `offerLink` é da conta e não garante SubID específico do blog; estoque não confirmado.
- Geração C100 de HTML com grade única C98, imagem do anúncio correspondente ao itemId, links de CTA com `rel="nofollow sponsored noopener noreferrer"`, cores laranja-avermelhadas `#D83F00` e brilho C99, atalhos para 8 grupos e **6 links internos reais** para artigos deste blog.

## Operações concretas
- Backup antes de editar: `affiliate_hub_v31/backups/C100_ACHADOS_PARA_CASA_LOJA_BEFORE_LIVE_2026-11-22.html` (**686 caracteres**, 0 produtos/0 fotos).
- HTML validado e salvo antes do update: `affiliate_hub_v31/exports/C100_ACHADOS_PARA_CASA_LOJA_36_REAIS_2026-11-22.html` (**67.464 caracteres**, 36 cards, 36 imgs, 36 URLs Shopee únicas, 36 botões laranja, 8 categorias e 6 guias).
- Único UPDATE na página existente Blogger, request_id `v31-c100-achados-casa-36-shopee-20261122-01`, `updated_at=2026-11-22T19:41:53-03:00`.
- GET posterior API: `status=live`, permalink antigo preservado, HTML idêntico ao export, **36 cards, 36 imagens, 36 offerLinks distintos** (duas ocorrências por item: foto e CTA), 36 CTA laranja, 8 atalhos, 6 links de artigos.

## QA público e ressalva do tema
- Firecrawl GET público `maxAge=0` confirmou o conteúdo e URLs da Loja, mas retornou **72 elementos no HTML renderizado** em vez de 36. Browser visual remoto identificou a causa: o tema conserva **duas instâncias da seção Loja**, sendo **uma totalmente oculta por `display:none`**. **Somente 36 cartões ficam visíveis ao visitante**, comprovado pelo navegador. Portanto não foram criadas 72 ofertas nem duas páginas; é duplicação técnica do DOM pelo tema. Não alterar o tema apenas por essa cópia oculta sem auditoria e backup específicos.
- Verificar em futuros temas se a cópia oculta traz impacto de SEO/performance antes de mudar; **não atribuir duas vitrines visíveis**.

## Protocolo de continuidade
- C100 restante: 18 páginas Blogger vazias por abastecer, conforme `CHECKPOINT_C100_INVENTARIO_LOJAS_2026-11-22.md`.
- Nunca repetir update deste blog se GET já confirmar `v31-c100-store` com 36 ofertas e links.
- Não modificar lojas já preenchidas, artigo C94, tema universal, D1/R2, campanhas, Pinterest, crons ou `V31_AUTOLIVE_ACTIVE=false`.
- O pipeline universal de discovery R2+Shopee pode ser reusado para os próximos blogs com `affiliate_hub_v31/c100_r2_exact_readonly.py`, renderização `c100_shop_renderer.py` e `c100_store_profiles.json`; **não executar publicação automática em lote sem a validação específica de cada página**.

**C100 — ACHADOS PARA CASA: CONCLUÍDO.**
