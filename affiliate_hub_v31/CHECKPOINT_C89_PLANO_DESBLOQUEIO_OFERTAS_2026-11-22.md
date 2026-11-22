# C89 — Diagnóstico da oferta editorial contínua (prévia, 22/11/2026)

**Objetivo:** eliminar a dependência de 2 SKU manuais por site no verificador automático C81, sem produzir textos não comprovados nem ampliar as cotas pagas ou LIVE.

## Causa observada no código
- autonomous_review_sources.json tem só dois offers por blog. Um SKU já foi USED em cada CMS.
- autonomous_review._selection() tenta offers estáticos; candidatos adicionais só entram por catalog_gtin(description) com GTIN válido e trusted_structured_hosts do site.
- O caminho usa preview_site_launch(max_items=24), condicionado por ranqueamento e lojas, e pode ignorar produtos aprovados fora dos top 24 mesmo com link da campanha.
- site_request_queue converte com base em intenção, mas não prioriza produtos comprováveis pelo verificador.
- [Cron #45044961421](https://github.com/adelrib27/blogger-automation1/actions/runs/45044961421) SUCCESS: choose-one Blogger correto, independent-verifier retornou NO_NEW_OFFER / no_new_offer_with_trusted_source, deliver-draft skipped, release skipped.
- D1 read-only: Blogger Móveis 1 USED; nenhum SEARCH/HTTP para 22/11 no momento da consulta.

## Plano técnico e gates
1. Medir via R2 somente leitura candidatos por rota/nicho, links da campanha, GTIN válido e perfil confiável, sem imprimir dados comerciais ou segredos.
2. Separar descoberta ampliada do catálogo da autorização factual de publicação. Jamais inferir GTIN, fabricante, material ou medida.
3. Priorizar conversões de SKUs elegíveis com fonte verificável dentro do teto global D1 3/dia UTC e sem copiar URLs entre campanhas.
4. Registrar motivo de indisponibilidade e evitar insistência em fonte insuficiente; preservar originalidade, assinatura, D1/R2/GET/replay.
5. Testar adversarialmente GTIN ausente/ambíguo, rota/campanha divergente, fonte 429, produto USED e quotas.
6. Abrir PR, CI, integrar somente após PASS e homologar SAFE; manter LIVE desligado e preservar a main concorrente de C88.

**Critério:** sem fontes confiáveis não inventar artigos. Uma solução sustentável repõe candidatos e não confunde ausência de prova com sucesso de criação.