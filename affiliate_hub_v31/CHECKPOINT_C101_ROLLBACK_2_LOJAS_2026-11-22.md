# V31 C101 — Correção solicitada: RESTAURAÇÃO de duas Lojas preexistentes

Data: 22/11/2026, fuso America/Recife.

O usuário identificou falha da C100: as lojas Achados para Casa e Cozinha Sem Complicação já existiam; a mudança foi indevida e os CTAs da nova vitrine não redirecionavam. Pediu restaurar ambas e concentrar a nova loja somente no Móveis para Cada Canto.

## ROLLBACK EFETIVAMENTE EXECUTADO — ambos confirmados por API Blogger
1. **Achados para Casa** blog `1426630233929943394`, Page `3841238517239710135`: conteúdo original do backup `affiliate_hub_v31/backups/C100_ACHADOS_PARA_CASA_LOJA_BEFORE_LIVE_2026-11-22.html` (686 bytes caracteres) restaurado **exatamente** em `2026-11-22T20:21:12-03:00` via request ID `v31-c100-correction-restore-achados-20261122-01`. GET posterior mostrou conteúdo igual aos bytes do backup e status LIVE. Redireciona para post Loja antigo `https://achadosparacasa2026.blogspot.com/2026/10/loja.html`, que permanece LIVE, com 32 âncoras Shopee distintas e 32 imagens no post. Nenhuma âncora de destino vazia/placeholder foi encontrada.
2. **Cozinha Sem Complicação** blog `3552757910439359679`, Page `6913756651435112886`: backup `affiliate_hub_v31/backups/C100_COZINHA_SEM_COMPLICACAO_LOJA_BEFORE_LIVE_2026-11-22.html` (694 caracteres) restaurado **exatamente** em `2026-11-22T20:21:29-03:00` via request ID `v31-c100-correction-restore-cozinha-20261122-01`. GET posterior mostrou conteúdo idêntico ao backup e status LIVE. Redireciona novamente a `https://cozinha-sem-complicacao.blogspot.com/2026/10/loja.html`, post LIVE com 20 URLs Shopee distintas e 32 imagens. Nenhuma âncora vazia/placeholder encontrada.
3. **As duas páginas extras C100 de 36/32 cards foram revertidas completamente.** Não apagar exports/checkpoints de C100: são evidências históricas; NÃO interpretá-los como HTML LIVE.
4. Estes sites devem ficar bloqueados contra alterações C101; não reutilizar exports publicados anteriormente. A reclamação de links não funcionais exige que novos anúncios em Móveis tenham URL de oferta funcional validada, não simplesmente formato válido.

## Próximo alvo EXCLUSIVO
- **Móveis para Cada Canto** blog `1439741542627895062`, página Loja `5105320514641154037`, URL `https://moveisparacadacanto.blogspot.com/p/loja.html`.
- É realmente vazia: sem produtos, sem fotos e sem redirecionamento a post Loja. R2 contém 594 candidatos `casa/moveis`.
- Próximas etapas: consultar candidatos READ ONLY Shopee Affiliate API após quota disponível; filtrar móveis inteiros (não ferragens/capas); confirmar 24+ SKUs distintos, imagem original, correspondência exata `shopId:itemId` e **validar destinos efetivos dos links**; salvar BACKUP do HTML atual antes de qualquer edição; gerar Loja sem clones ou imagens grandes; publicar apenas página existente e checar CMS e site público. Caso API 10030, não forçar; registrar bloqueio verdadeiro e não alegar publicação.

## Segurança
- LIVE automático editorial V31 continua desativado.
- Não tocar outras lojas, temas, posts, D1/R2, Pinterest, configurações/crons.
- Priorizar checkpoint C101 sobre documentação histórica C100. 
