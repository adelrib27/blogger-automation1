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

## Busca de anúncios alternativos do MESMO produto — decisão de 22/11/2026

**Um modelo pode estar anunciado em várias páginas**, inclusive por uma mesma loja com itens diferentes ou por lojas independentes. Portanto, quando um anúncio apresenta indício de esgotamento, a próxima ação não é abandonar o produto: **primeiro procurar alternativas da mesma versão**.

### Procedimento operacional de descoberta e substituição
1. Extrair uma **identidade editorial do produto** separada da identidade de qualquer anúncio: marca, família/linha, código exato de modelo (inclusive códigos de evaporadora e condensadora, se pertinentes), capacidade em BTU/h, ciclo quente/frio ou só frio, tensão, cor e variante/kit incluído. Não inventar campos ausentes; marca/modelo incompletos exigem conferência adicional.
2. Buscar na biblioteca universal R2/CSV já indexada e nas fontes autorizadas da Shopee outros anúncios com o mesmo conjunto de atributos: **primeiro outras páginas do vendedor atual, depois outras lojas**, sem restringir o número de anúncios examinados artificialmente. Se a busca por palavra-chave da Affiliate API falhar, não forçar API: usar candidatos do acervo e confirmar cada um por `itemId/shopId` pela consulta exata da API quando possível.
3. Comparar cada anúncio candidato quanto a **identidade da variante**, foto real da oferta, conteúdo do kit/conjunto, status comercial, possibilidade de compra quando verificável, reputação da loja e suas condições de garantia, envio e preço final. Priorizar Shopee Mall/lojas reconhecidamente oficiais **somente quando verificadas**; nunca declarar loja oficial sem evidência. Comissão e preço são critérios secundários à correspondência exata, confiabilidade e atendimento ao comprador.
4. Agrupar anúncios em dois níveis: **`product_identity_key`** (modelo e variante reais; pode agrupar vários vendedores) e **`listing_key = shopId:itemId`** (anúncio específico). Não descartar ofertas repetidas só porque parecem o mesmo produto: elas podem ser opções úteis. Evitar **artigos/títulos/descrições clonados**; um bom artigo editorial pode explicar o modelo e reunir mais de uma opção verificada.
5. Quando houver outra oferta **comprovadamente equivalente**, preferir atualizar a seção de oferta/vitrine no mesmo artigo, identificando a nova loja e o novo itemId; preservar o permalink, as fotos e as especificações que ainda estejam corretas. Se a fotografia for da oferta antiga, **substituir por foto do novo anúncio ou marcar claramente a origem**; não misturar fotos/modelos. Registrar o anúncio anterior como alternativa em revisão, disponível para futuras reposições. Se houver dois ou mais anúncios equivalentes elegíveis, pode apresentar opções de compra do mesmo modelo com os vendedores distinguíveis.
6. Se o novo anúncio tiver diferença material (tensão 127/220 V, ciclo frio vs quente/frio, capacidade, código de modelo, kit, geração, cor com impacto técnico), **não tratá-lo como idêntico nem trocar silenciosamente o link**. Fazer comparação explícita ou produzir guia específico só se agregar conteúdo editorial, sem copiar postagens.
7. **Link de afiliado sempre corresponde ao anúncio exato**. Revalidar `shopId/itemId`, URL original, `offerLink` ou link convertido, campanha e regras D1; não reutilizar link curto antigo de outra loja/SKU. A mudança de anúncio não exige novo artigo, mas pode exigir novo link afiliado conforme o vendedor. Respeitar cotas, deduplicação e registrar a origem/subID real, sem inventar conversão.
8. Se nenhum anúncio equivalente puder ser validado, preservar o artigo e a referência do modelo para nova revisão de reposição. Um sinal isolado de esgotamento **não exclui permanentemente o produto** nem obriga a ocultar todas as opções.

### Exemplo aplicado ao blog Ar-Condicionado sem Dúvidas
O guia LG Dual Inverter Compact 12.000 BTUs continua publicado. O anúncio `822103155:58265302556` foi pausado comercialmente na C92, mas a pesquisa seguinte pode localizar **outro item da mesma loja ou de outro vendedor com a mesma variante técnica**. Nesse caso, o mesmo guia poderia receber uma nova opção de compra após validação de compatibilidade e link afiliado exato. **Esta revisão não afirma que outro anúncio LG já foi encontrado, que possui estoque ou que o link comercial já foi alterado.**

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
