# C127 — Investigação de origem das imagens e links TikTok (ponto pré-mudanças)
**Data:** 23/11/2026, Recife. **Estado herdado:** C126, 7/10 revisões Radar Tech BR confirmadas, #29/#25/#24 preservados sem alterações. LIVE automático bloqueado.

## Descoberta factual crítica na retomada
Uma releitura integral dos backups C127, C128 e C129 revelou que a frase “sem link de afiliado” dos relatórios anteriores era limitada a URLs **Shopee**: **existem links externos já presentes** no HTML dos posts remanescentes:
- #29 Arctic: `https://vt.tiktok.com/ZS9UNndpjDsxQ-GACcI/`
- #25 Kapbom: `https://vt.tiktok.com/ZS9UNtSQoTWWq-a7gKh/`
- #24 Luz RGB: `https://vt.tiktok.com/ZS9UNGSAnRA9S-q3vFI/`

Eles aparecem em blocos `produto-principal-contextual`, acompanhados de aviso “link de afiliado”, mas **não foi verificado ainda se são válidos, se são links de produto/afiliado ou seu vendedor e variante**. Não são URLs Shopee e não devem ser rotulados como oferta Shopee; não houve descoberta de link Shopee específico dos três.

O projeto V31 usa Shopee para os blogs, de modo que esses CTAs TikTok precisam de auditoria antes de decidir preservação, substituição ou eventual retirada. A tentativa de resolver os links pelo Firecrawl falhou por domínio não suportado; web.open também indisponível. **Não significa que os links estão inválidos.**

## Plano de execução
- Investigar redirecionamentos dos três links em job Github Actions sem segredos, somente GET/HEAD, sem interações com contas, compras ou publicações.
- Gerar painel comparativo de imagens WP e anúncios atuais Shopee dos três artigos, inspecionar sem presumir que hash perceptual alto significa produto diferente (pode ser outra fotografia do mesmo produto). Registrar evidências visuais.
- Só publicar CTA Shopee se identidade/variante e rastreio de afiliado verificáveis, sem substituição silenciosa de link TikTok.
- Se a prova permanecer insuficiente, manter posts atuais e registrar alternativas editoriais PREVIEW sem sobrescrita.
- Guardar output, atualizar ponto permanente e preservar AUTO LIVE false. Nunca tocar D1/R2 ou outros sites.
**Código:** `V31-RADAR-C127-20261123-INVESTIGAR-TIKTOK-IMAGENS-NO-WRITES`.
