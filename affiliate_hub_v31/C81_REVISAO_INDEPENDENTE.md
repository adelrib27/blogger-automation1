# C81 — verificação factual autônoma

A aprovação editorial humana por artigo foi retirada do workflow DRAFT. A revisão é uma etapa independente que consulta o catálogo, a Shopee, fontes externas e o histórico de entrega antes de qualquer assinatura ou escrita no CMS.

## Caminho de trabalho

1. O gerador indica um produto em uma fila ou candidato privado. O verificador usa o SKU como sugestão. O texto, a indicação de fontes, as flags de aprovação e as alegações do gerador não são usados como prova.
2. O catálogo é restaurado do R2 oficial. A rota e a campanha vêm do cadastro do V31. O produto deve estar elegível com link cacheado da campanha. O verificador resolve o link para a mesma loja e SKU da Shopee e verifica o formato e os bytes da foto oficial.
3. O verificador consulta páginas permitidas e extrai afirmações com regras objetivas. Para produtos novos e com GTIN verificável no catálogo, ele procura fichas estruturadas de domínios confiáveis. Ausência, divergência ou ambiguidade de identidade/fatos bloqueiam a entrega.
4. O verificador reconstrói e audita o HTML. O texto segue a receita editorial confiável. Os fatos, SEO, links, imagem e hash do HTML são validados antes do recibo HMAC e da assinatura Ed25519.
5. O envelope oficial é escrito condicionalmente no R2 e validado na leitura. O D1 faz reserva da entrega atômica por blog e campanha. O publicador recebe somente a chave pública e releitura autenticada do CMS confirma DRAFT, título e HTML. O replay deve retornar o mesmo ID. Uma tentativa de CMS com resultado ambíguo é reconciliada por leitura.

## Operação e escopo

- O workflow [fila editorial DRAFT](../.github/workflows/v31_autonomous_draft_scheduler.yml) seleciona um blog ativo. O cron depende da variável protegida `V31_AUTODRAFT_ACTIVE`. O modo permanente exige a chave privada e o HMAC exclusivos no estágio do verificador e a chave pública correspondente. A configuração é técnica, feita uma vez. O canário usa um par isolado e efêmero.
- A prova inicial usa dois perfis explícitos, um por plataforma. Novos produtos podem ser cobertos por regras confiáveis ou metadados com GTIN. Produtos sem identidade verificável permanecem na fila sem publicação.
- As tentativas Firecrawl consomem cotas D1 por blog, campanha, dia UTC e tipo. 429 pausa a classe de pesquisa. O limite diário de DRAFT é aplicado no mesmo SQL que reivindica o envio ao CMS.
- Veja a [política LIVE proposta](C81_POLITICA_LIVE_AUTONOMA.md). O fluxo autônomo em homologação só chega a DRAFT. A política LIVE individual segue vigente.
