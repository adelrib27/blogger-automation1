# V31 — Política de estoque Shopee: cautela proporcional e retorno ao estoque

**Revisão de política em 22/11/2026 por orientação expressa do proprietário.**
Aplica-se ao Hub Editorial Shopee em blogs Blogger e WordPress; implantada primeiro no blog Ar-Condicionado sem Dúvidas (`2228849984262880811`).

## Princípio de decisão
**“Esgotado” não é banimento nem evidência de descontinuação.** Estoque é volátil e pode voltar; um snapshot isolado, uma página indexada, um erro do navegador ou um campo ausente na Affiliate API **não autorizam exclusão definitiva**. O objetivo é não induzir compras impossíveis e, ao mesmo tempo, preservar SEO, catálogo, histórico e potencial de conversão quando houver reposição.

**Estados editoriais sugeridos (não afirmar que existe monitoramento automático já implantado):**
1. `OFERTA_SEM_ALERTA`: API confirmou IDs, fotografia e link; não foi observado sinal recente de esgotamento. Produto e link podem permanecer na vitrine com aviso geral de que preço e estoque variam. **Não escrever “estoque confirmado”** sem verificação no checkout.
2. `SINAL_DE_ESGOTAMENTO`: apareceu uma vez a mensagem “esgotado”, ou os dados são contraditórios ou de fonte indexada. **Marcar para revisão, não excluir produto e não derrubar automaticamente o artigo ou todos os links.** Considerar uma nota editorial discreta; buscar confirmação no SKU/variante e outra observação independente quando acessível.
3. `PAUSA_COMERCIAL_TEMPORARIA`: indisponibilidade corroborada para a variante exata por observações atuais confiáveis, ou link realmente não oferece compra. É razoável **suspender temporariamente o CTA desse anúncio** ou substituí-lo por “verificar se voltou ao estoque”, mantendo o guia técnico, foto, SKU, link histórico e status no catálogo. Não transferir a oferta para outro SKU ou foto sem validação.
4. `RETORNO_AO_ESTOQUE`: nova verificação confiável indica oferta novamente comprável na variante correta. **Reativar o mesmo anúncio e link afiliado, se ainda válidos**, com o CTA adequado e sem recriar o post, sem perder SEO e sem repetir conversão já registrada. Se o link tiver expirado, tratar como nova elegibilidade com cota e deduplicação.
5. `INDETERMINADO`: não foi possível consultar a página por login/antibot, falha técnica ou ausência de estoque na API. **Não presumir esgotamento nem disponibilidade garantida.** Se há oferta exata com imagem+link validados pela API e nenhum outro sinal negativo, a publicação editorial pode seguir com a orientação “consulte a disponibilidade na Shopee”; se identidade/campanha/link são incertos, segurar somente a associação comercial até rechecagem.

## Evidência e proporcionalidade
- A API Shopee Affiliate `productOfferV2` valida a existência/elegibilidade de anúncio e link; preço positivo **não significa estoque físico confirmado**.
- Páginas públicas ou indexadas podem apresentar mensagens antigas. Registrar data, horário, SKU, loja, variante, URL, canal de verificação e se a página era acessível de fato. Se só há uma captura de “esgotado”, classificar como **sinal**, não como encerramento.
- Quando possível, validar o mesmo modelo/variante em uma segunda consulta ou no próprio seletor de compra. A falta de acesso por HTTP 403 não prova esgotamento.
- **Não impor descarte permanente, exclusão de SKU, remoção de artigo, reescrita de backlinks nem troca automática de produto por um único sinal.**
- É permitido manter um anúncio com disponibilidade incerta e alerta honesto, sem preço fixo nem prometer unidade disponível. Se o anúncio claramente não oferece compra e houve confirmação suficiente, preferir pausa do botão comercial até reposição.
- A estratégia deve permitir **revisitar produtos em pausa** na próxima revisão editorial; a cadência pode ser definida por workflow posteriormente. Este documento não cria monitoramento recorrente por si só e **não ativa publicação LIVE automática**.
- Se o usuário confirmar de forma explícita que o vendedor repôs o estoque, isso é motivo para **nova checagem rápida e reativação**, não exigir nova criação de artigo.

## Dedupe, conversão e rastreabilidade
- Conservar `shopId:itemId`, foto, oferta e texto editorial original. Nunca substituir SKU por uma variante diferente mantendo a descrição antiga.
- Reativar links já validados sem repetir a mutation da Shopee se o link ainda for válido. Respeitar limite global D1 3 conversões/dia UTC e o dedupe por campanha/produto.
- `offerLink` da API pode não conter SubID específico da campanha; mencionar essa limitação no relatório.
- `V31_AUTOLIVE_ACTIVE=false` permanece até autorização de política automática; qualquer reativação pública do CTA segue o gate aplicável.

## Histórico da C92 e interpretação correta
- 22/11/2026, anúncio LG `shopee:822103155:58265302556` teve uma indicação pública de “esgotado”. O artigo educativo `940950273343255024` foi **preservado**, mas o CTA e o cartão da Loja foram retirados pela decisão anterior C92. **Essa medida é reversível, não um banimento**. Reavaliar estoque/variante em nova oportunidade; ao comprovar retorno, restaurar os links históricos com o mesmo SKU.
- Outro anúncio Midea `shopee:1736335904:58212764417` apresentou sinal de esgotamento e não entrou na seleção C92. **Ele continua elegível a nova auditoria de reposição**, não foi proibido.
- Midea Lite 9.000 `shopee:1736335904:58267891881` e Midea AI Ecomaster 12.000 `shopee:889973435:18398298625` entraram na Loja pela identidade validada da Affiliate API; estoque de variantes não foi comprovado. **Não deve haver remoção automática por falta de campo stock.**
- Esta revisão altera a política para **futuras decisões**. Não afirma que o estoque desses itens mudou nem que um workflow de reposição já está rodando.

Fontes de referência: consulta autenticada Shopee Affiliate API C92 runs `45056107732`, `45056223307`; checkpoints anteriores preservam as evidências datadas. Para dados de eficiência: https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/condicionadores-de-ar/sistema-pbe-para-consulta-dos-produtos-etiquetados
