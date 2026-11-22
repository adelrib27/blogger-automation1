# C92 — Regra anti-esgotados de produtos Shopee no blog Ar-Condicionado sem Dúvidas
Válida para revisão editorial a partir de 22/11/2026. Blog `2228849984262880811`.

## Distinção obrigatória entre três estados
- `ESGOTADO_CONFIRMADO`: página Shopee do **SKU exato** mostra literalmente "esgotado" ou indica que não há unidade comprável. **Ação:** remover imediatamente CTA da Loja e do post; preservar conteúdo educacional, incluir aviso datado. Exemplo real: LG item `58265302556` shop `822103155`, auditado em 22/11.
- `SEM_ALERTA_ESGOTAMENTO_MAS_ESTOQUE_NAO_COMPROVADO`: a API Shopee confirma itemId+shopId, preço de referência positivo, período de oferta atual, imagem e `offerLink`, e a página pública acessível não exibe esgotado. **Ação:** não afirmar estoque, não prometer desconto/preço e alertar leitor para confirmar variante. Não é equivalência com disponibilidade garantida. Ex.: Midea 9.000 `1736335904:58267891881` e Midea 12.000 `889973435:18398298625`.
- `INDETERMINADO`: página sem dados de compra ou bloqueada pelo login/antibot, ou API falhou, ou item tem inconsistência de IDs/foto/título. **Ação:** falhar fechado para novas recomendações comerciais; somente artigo educativo, sem CTA de compra não verificável, até obter evidência alternativa.

## Fonte de verdade e limitação
- `productOfferV2` Shopee Affiliate API pode retornar oferta e preço **mesmo quando a página pública mostra esgotado**. Portanto não confundir link afiliado existente com estoque real.
- Shopee poderá bloquear consulta direta de unidades/variantes (HTTP 403 em `/api/v4/item/get` na auditoria C92). Nunca contornar autenticação, inferir unidades nem inventar números.
- A página pública pode estar indexada com atraso. Documentar data e tipo de evidência (live vs índice), nunca chamar estoque de "confirmado" a partir de índice antigo.
- Revalidar antes de cada nova publicação ou atualização da Loja e periodicamente quando houver monitoramento autorizado; ao constatar esgotamento, remover CTA comercial sem apagar os posts educacionais.
- Alteração de SKU exige imagem correspondente e link do mesmo itemId/shopId. Não trocar foto/identidade do modelo sem rechecagem.
- D1 global tem no máximo 3 slots de conversão UTC/dia; `offerLink` fornecido pela mesma conta API pode funcionar como afiliado sem consumir a mutation de shortlink, **mas pode não carregar SubID da campanha**. Documentar isso; não reutilizar shortlink de outro produto.
- `V31_AUTOLIVE_ACTIVE` segue desativado; nenhum job foi ativado para publicação automática neste blog.

## Evidência objetiva C92
- LG `822103155:58265302556`: página pública Shopee exibiu "esgotado" em consulta web 22/11/2026, apesar de `productOfferV2` elegível; CTA removido do post e da Loja.
- Midea `1736335904:58267891881` e `889973435:18398298625`: IDs+foto+offerLink confirmados pela API na Actions #45056223307; listagens públicas consultadas não exibiram "esgotado" no conteúdo disponível, mas não comprovaram unidades em estoque ao minuto.
- Referência oficial de eficiência energética por SKU: https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/condicionadores-de-ar/sistema-pbe-para-consulta-dos-produtos-etiquetados
