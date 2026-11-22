# V31 C100 — Continuidade intermediária: R2 vs Busca Shopee — 22/11/2026

## Estado verificado (não confundir com loja publicada)
- Checkpoint C100 inicial já existe: `affiliate_hub_v31/CHECKPOINT_C100_EXPANSAO_LOJAS_PRE_EXECUCAO_2026-11-22.md`.
- Inventário completo: `affiliate_hub_v31/CHECKPOINT_C100_INVENTARIO_LOJAS_2026-11-22.md`. **19 Blogger Lojas vazias; 11 Blogger com ofertas; 3 WordPress com ofertas; 1 LAB e 1 blog não lançado excluídos.**
- 0 novas lojas foram publicadas até este registro.
- Workflow [C100 A #45078464648](https://github.com/adelrib27/blogger-automation1/actions/runs/45078464648) e sua revisão [#45078702998](https://github.com/adelrib27/blogger-automation1/actions/runs/45078702998) PASS no processamento, porém retornaram **apenas 9–10 ofertas válidas por blog**, incluindo erros Shopee `10000`; portanto NÃO publicar.
- C100 revisão adicionou ordenação por relevância e filtros contra produtos acessórios; `affiliate_hub_v31/c100_multi_store_readonly.py`.
- Consulta R2 READ ONLY [#45078854741](https://github.com/adelrib27/blogger-automation1/actions/runs/45078854741) SUCCESS, autenticada com o R2 oficial `v31-editorial-shopee`: todos os 19 nichos têm candidatos `products` moderados/ classificados. **Contagens são do catálogo, não ofertas afiliadas validadas atuais.**
- `liquidificadores`: 165 candidatos no R2
- `cozinha_sem_complicacao`: 1180 candidatos no R2
- `portal_radar_tech`: 1272 candidatos no R2
- `achadinhos_beleza`: 576 candidatos no R2
- `moda_ofertas`: 2490 candidatos no R2
- `vitrine_pratica`: 759 candidatos no R2
- `guia_achados`: 1832 candidatos no R2
- `achados_valem`: 662 candidatos no R2
- `escolha_certa`: 890 candidatos no R2
- `casa_em_ordem`: 759 candidatos no R2
- `estilo_dia`: 2748 candidatos no R2
- `conecta_achados`: 1664 candidatos no R2
- `limpeza`: 283 candidatos no R2
- `ventiladores`: 452 candidatos no R2
- `achados_casa`: 2088 candidatos no R2
- `eletroportateis`: 497 candidatos no R2
- `cabelos`: 258 candidatos no R2
- `air_fryers`: 247 candidatos no R2
- `moveis`: 594 candidatos no R2
- Código alternativo implantado: `affiliate_hub_v31/c100_r2_exact_readonly.py` lê R2 READ ONLY e consulta `productOfferV2(itemId)` em lotes GraphQL com conferência exata `shopId:itemId`, imagem, link afiliado, nota, vendas e comissão. Não converte shortlinks nem publica.
- O renderizador universal `affiliate_hub_v31/c100_shop_renderer.py` exige 24–36 produtos confirmados da API, exibe grade contínua e CTAs laranja `#D83F00`, com validações de anúncios.
- Primeiro workflow dessa estratégia: [C100 R2 EXACT Achados para Casa #45078972630](https://github.com/adelrib27/blogger-automation1/actions/runs/45078972630). **Na criação deste registro, consulta estava EM ANDAMENTO.** Confirmar conclusão, logs e `C100_EXACT_SITE` / `C100_EXACT_OFFER` antes de fazer qualquer atualização.
- A Loja a ser modificada, somente se >=24 ofertas realmente confirmadas: Achados para Casa blog ID `1426630233929943394`, página Loja ID `3841238517239710135`, URL https://achadosparacasa2026.blogspot.com/p/loja.html. **Fazer backup prévio desse HTML**, GET atual, e só atualizar a página existente quando válido. Sem criar página duplicada.
- NÃO tocar em Pinterest, artigos, D1/R2, temas, assinaturas ou `V31_AUTOLIVE_ACTIVE`.
- Próximas etapas se o chat expirar: 1) ler checkpoint e estado; 2) inspecionar run #45078972630; 3) se 24+ ofertas validas, gerar HTML e aplicar somente a página confirmada; 4) GET e validação pública; 5) registrar resultado; 6) continuar os outros 18 conforme perfil, consultando API e preservando lojas já preenchidas.

**Este arquivo não é uma ordem de execução automática. É uma evidência de continuidade idempotente e anti-alucinação.**
